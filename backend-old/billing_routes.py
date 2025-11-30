#!/usr/bin/env python3
"""
LUMINA - AI-POWERED RECEIPT MANAGEMENT SYSTEM
Billing API Routes

Copyright (c) 2024 Jaideep Singh Rajpurohit. All rights reserved.
PROPRIETARY SOFTWARE - UNAUTHORIZED USE PROHIBITED
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from typing import Dict, Any

from auth import get_current_user, User
from billing_service import BillingService
from billing_models import (
    BillingInfo, CheckoutRequest, CheckoutResponse, PlanType, PLAN_CONFIG
)
from config import settings
from logging_config import get_logger
from rate_limiter import create_rate_limit_dependency

logger = get_logger("billing_routes")

# Billing router
billing_router = APIRouter(prefix="/api/billing", tags=["billing"])

# Billing service will be set by main server
billing_service: BillingService = None

def set_billing_service(service: BillingService):
    """Set billing service instance"""
    global billing_service
    billing_service = service

@billing_router.get("/info", response_model=BillingInfo)
async def get_billing_info(current_user: User = Depends(get_current_user)):
    """Get user's current billing information and plan details"""
    try:
        billing_info = await billing_service.get_user_billing_info(current_user)
        
        logger.info(
            f"Billing info retrieved for user {current_user.email}",
            extra={
                "user_id": current_user.id,
                "plan": billing_info.plan.value,
                "receipts_used": billing_info.receipts_used,
                "receipts_remaining": billing_info.receipts_remaining
            }
        )
        
        return billing_info
        
    except Exception as e:
        logger.error(f"Error getting billing info for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve billing information"
        )

@billing_router.get("/plans")
async def get_available_plans():
    """Get all available subscription plans"""
    try:
        plans = {}
        for plan_type, config in PLAN_CONFIG.items():
            plans[plan_type.value] = {
                "name": config["name"],
                "price": config["price"],
                "currency": config["currency"],
                "receipt_limit": config["receipt_limit"],
                "features": config["features"]
            }
        
        return {"plans": plans}
        
    except Exception as e:
        logger.error(f"Error getting available plans: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available plans"
        )

@billing_router.post("/create-checkout-session", response_model=CheckoutResponse)
async def create_checkout_session(
    request: Request,
    checkout_request: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    _rate_limit: None = Depends(
        create_rate_limit_dependency(
            endpoint="checkout",
            limit=5,  # 5 checkout attempts per minute
            window_minutes=1
        )
    )
):
    """Create Stripe checkout session for plan upgrade"""
    try:
        # Validate plan upgrade
        if checkout_request.plan_type == PlanType.FREE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create checkout session for free plan"
            )
        
        if current_user.plan == checkout_request.plan_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You already have the {checkout_request.plan_type.value} plan"
            )
        
        # Get host URL for webhook
        host_url = str(request.base_url).rstrip('/')
        
        # Create checkout session
        checkout_response = await billing_service.create_checkout_session(
            user=current_user,
            request=checkout_request,
            host_url=host_url
        )
        
        logger.info(
            f"Checkout session created for user {current_user.email}",
            extra={
                "user_id": current_user.id,
                "plan_type": checkout_request.plan_type.value,
                "session_id": checkout_response.session_id
            }
        )
        
        return checkout_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error creating checkout session for user {current_user.id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )

@billing_router.get("/checkout-status/{session_id}")
async def get_checkout_status(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get status of checkout session and process payment if completed"""
    try:
        # Get checkout status from Stripe
        status_response = await billing_service.get_checkout_status(session_id)
        
        logger.info(
            f"Checkout status retrieved for session {session_id}",
            extra={
                "user_id": current_user.id,
                "session_id": session_id,
                "status": status_response.status,
                "payment_status": status_response.payment_status
            }
        )
        
        return {
            "status": status_response.status,
            "payment_status": status_response.payment_status,
            "amount_total": status_response.amount_total,
            "currency": status_response.currency,
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(
            f"Error getting checkout status for session {session_id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve checkout status"
        )

@billing_router.post("/webhook")
async def handle_stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    try:
        # Get webhook data
        webhook_body = await request.body()
        stripe_signature = request.headers.get("Stripe-Signature")
        
        if not stripe_signature:
            logger.warning("Webhook received without Stripe signature")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing Stripe signature"
            )
        
        # Process webhook using Emergent Stripe integration
        host_url = str(request.base_url).rstrip('/')
        webhook_url = f"{host_url}/api/billing/webhook"
        stripe_checkout = billing_service.get_stripe_checkout(webhook_url)
        
        # Handle webhook
        webhook_response = await stripe_checkout.handle_webhook(
            webhook_body, 
            stripe_signature
        )
        
        # Process the webhook event
        webhook_data = {
            "event_type": webhook_response.event_type,
            "event_id": webhook_response.event_id,
            "session_id": webhook_response.session_id,
            "payment_status": webhook_response.payment_status,
            "metadata": webhook_response.metadata
        }
        
        # Handle the event
        success = await billing_service.handle_webhook_event(webhook_data)
        
        if success:
            logger.info(
                f"Webhook processed successfully: {webhook_response.event_type}",
                extra={
                    "event_type": webhook_response.event_type,
                    "event_id": webhook_response.event_id,
                    "session_id": webhook_response.session_id
                }
            )
            return {"status": "success"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process webhook event"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Stripe webhook: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook"
        )