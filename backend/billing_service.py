#!/usr/bin/env python3
"""
LUMINA - AI-POWERED RECEIPT MANAGEMENT SYSTEM
Billing Service for Stripe Integration

Copyright (c) 2024 Jaideep Singh Rajpurohit. All rights reserved.
PROPRIETARY SOFTWARE - UNAUTHORIZED USE PROHIBITED
"""

import os
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase

from billing_models import (
    PlanType, SubscriptionStatus, PaymentStatus, PaymentTransaction,
    BillingInfo, PLAN_CONFIG, CheckoutRequest, CheckoutResponse
)
from config import settings
from logging_config import get_logger
from auth import User

# Emergent Stripe integration
from emergentintegrations.payments.stripe.checkout import (
    StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, 
    CheckoutSessionRequest
)

logger = get_logger("billing")

class BillingService:
    """Comprehensive billing service with Stripe integration"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.stripe_api_key = os.getenv('STRIPE_API_KEY', 'sk_test_emergent')
        
    def get_stripe_checkout(self, webhook_url: str) -> StripeCheckout:
        """Get configured Stripe checkout instance"""
        return StripeCheckout(
            api_key=self.stripe_api_key,
            webhook_url=webhook_url
        )
    
    async def get_user_billing_info(self, user: User) -> BillingInfo:
        """Get comprehensive billing information for user"""
        try:
            # Get current plan configuration
            plan_config = PLAN_CONFIG[user.plan]
            
            # Count receipts used in current billing period
            receipts_used = await self._count_user_receipts_this_period(user.id)
            
            # Calculate remaining receipts
            receipt_limit = plan_config["receipt_limit"]
            receipts_remaining = max(0, receipt_limit - receipts_used)
            
            # Determine if user can upgrade
            can_upgrade = user.plan == PlanType.FREE
            
            # Get subscription dates
            billing_start = user.billing_period_start
            billing_end = user.billing_period_end
            next_billing = billing_end if billing_end and billing_end > datetime.now(timezone.utc) else None
            
            return BillingInfo(
                plan=user.plan,
                plan_name=plan_config["name"],
                receipt_limit=receipt_limit,
                receipts_used=receipts_used,
                receipts_remaining=receipts_remaining,
                subscription_status=user.stripe_subscription_status,
                billing_period_start=billing_start,
                billing_period_end=billing_end,
                next_billing_date=next_billing,
                can_upgrade=can_upgrade,
                features=plan_config["features"]
            )
            
        except Exception as e:
            logger.error(f"Error getting billing info for user {user.id}: {e}")
            raise
    
    async def _count_user_receipts_this_period(self, user_id: str) -> int:
        """Count receipts uploaded by user in current billing period"""
        try:
            # Get user to find billing period
            user_doc = await self.db.users.find_one({"_id": user_id})
            if not user_doc:
                return 0
            
            # Determine billing period start
            if user_doc.get('billing_period_start'):
                period_start = user_doc['billing_period_start']
            else:
                # Default to current month for free users
                now = datetime.now(timezone.utc)
                period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # Count receipts since period start
            count = await self.db.receipts.count_documents({
                "user_id": user_id,
                "upload_date": {"$gte": period_start}
            })
            
            return count
            
        except Exception as e:
            logger.error(f"Error counting receipts for user {user_id}: {e}")
            return 0
    
    async def check_receipt_limit(self, user: User) -> Tuple[bool, str]:
        """Check if user can upload more receipts"""
        try:
            billing_info = await self.get_user_billing_info(user)
            
            if billing_info.receipts_remaining > 0:
                return True, f"You have {billing_info.receipts_remaining} receipts remaining this month"
            else:
                plan_name = PLAN_CONFIG[user.plan]["name"]
                if user.plan == PlanType.FREE:
                    return False, f"You've reached your {plan_name} limit of {billing_info.receipt_limit} receipts per month. Upgrade to Pro for 500 receipts/month!"
                else:
                    return False, f"You've reached your {plan_name} limit of {billing_info.receipt_limit} receipts per month. Please wait for your next billing cycle."
        
        except Exception as e:
            logger.error(f"Error checking receipt limit for user {user.id}: {e}")
            return False, "Unable to verify receipt limit. Please try again."
    
    async def create_checkout_session(self, user: User, request: CheckoutRequest, host_url: str) -> CheckoutResponse:
        """Create Stripe checkout session for plan upgrade"""
        try:
            # Validate plan upgrade
            if user.plan == request.plan_type:
                raise ValueError(f"User already has {request.plan_type} plan")
            
            if request.plan_type == PlanType.FREE:
                raise ValueError("Cannot checkout for free plan")
            
            # Get plan configuration
            plan_config = PLAN_CONFIG[request.plan_type]
            
            # Create webhook URL
            webhook_url = f"{host_url.rstrip('/')}/api/billing/webhook"
            
            # Initialize Stripe checkout
            stripe_checkout = self.get_stripe_checkout(webhook_url)
            
            # Prepare checkout request
            success_url = f"{request.origin_url}/billing/success?session_id={{CHECKOUT_SESSION_ID}}"
            cancel_url = f"{request.origin_url}/billing"
            
            # Create metadata for tracking
            metadata = {
                "user_id": user.id,
                "email": user.email,
                "plan_type": request.plan_type.value,
                "current_plan": user.plan.value,
                "upgrade_type": "subscription"
            }
            
            # Create checkout session request
            checkout_request = CheckoutSessionRequest(
                amount=plan_config["price"],
                currency=plan_config["currency"],
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata
            )
            
            # Create checkout session
            session: CheckoutSessionResponse = await stripe_checkout.create_checkout_session(checkout_request)
            
            # Create payment transaction record
            transaction = PaymentTransaction(
                user_id=user.id,
                email=user.email,
                session_id=session.session_id,
                amount=plan_config["price"],
                currency=plan_config["currency"],
                plan_type=request.plan_type,
                payment_status=PaymentStatus.INITIATED,
                metadata=metadata
            )
            
            # Store transaction in database
            await self.db.payment_transactions.insert_one(transaction.dict())
            
            logger.info(
                f"Checkout session created for user {user.email}",
                extra={
                    "user_id": user.id,
                    "session_id": session.session_id,
                    "plan_type": request.plan_type.value,
                    "amount": plan_config["price"]
                }
            )
            
            return CheckoutResponse(
                checkout_url=session.url,
                session_id=session.session_id
            )
            
        except Exception as e:
            logger.error(
                f"Error creating checkout session for user {user.id}: {e}",
                exc_info=True
            )
            raise
    
    async def get_checkout_status(self, session_id: str) -> CheckoutStatusResponse:
        """Get checkout session status and update transaction"""
        try:
            # Get transaction record
            transaction = await self.db.payment_transactions.find_one({"session_id": session_id})
            if not transaction:
                raise ValueError(f"Transaction not found for session {session_id}")
            
            # Create webhook URL (dummy for status check)
            webhook_url = "https://api.example.com/webhook/stripe"
            stripe_checkout = self.get_stripe_checkout(webhook_url)
            
            # Get status from Stripe
            status_response = await stripe_checkout.get_checkout_status(session_id)
            
            # Update transaction status
            await self._update_transaction_status(session_id, status_response)
            
            # If payment is complete, upgrade user plan
            if status_response.payment_status == "paid":
                await self._process_successful_payment(transaction, status_response)
            
            return status_response
            
        except Exception as e:
            logger.error(f"Error getting checkout status for session {session_id}: {e}")
            raise
    
    async def _update_transaction_status(self, session_id: str, status_response: CheckoutStatusResponse):
        """Update payment transaction status"""
        try:
            # Map Stripe status to our payment status
            payment_status = PaymentStatus.PENDING
            if status_response.payment_status == "paid":
                payment_status = PaymentStatus.PAID
            elif status_response.status == "expired":
                payment_status = PaymentStatus.EXPIRED
            
            # Update transaction
            await self.db.payment_transactions.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "payment_status": payment_status.value,
                        "stripe_payment_intent_id": status_response.metadata.get("payment_intent_id"),
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"Error updating transaction status for session {session_id}: {e}")
            raise
    
    async def _process_successful_payment(self, transaction: dict, status_response: CheckoutStatusResponse):
        """Process successful payment and upgrade user plan"""
        try:
            user_id = transaction["user_id"]
            plan_type = PlanType(transaction["plan_type"])
            
            # Check if already processed to prevent double processing
            existing_upgrade = await self.db.users.find_one({
                "_id": user_id,
                "plan": plan_type.value
            })
            
            if existing_upgrade:
                logger.info(f"User {user_id} already upgraded to {plan_type.value}")
                return
            
            # Calculate billing period (monthly subscription)
            now = datetime.now(timezone.utc)
            period_start = now
            period_end = now + timedelta(days=30)  # 30-day subscription
            
            # Update user plan
            await self.db.users.update_one(
                {"_id": user_id},
                {
                    "$set": {
                        "plan": plan_type.value,
                        "stripe_subscription_status": SubscriptionStatus.ACTIVE.value,
                        "billing_period_start": period_start,
                        "billing_period_end": period_end,
                        "updated_at": now
                    }
                }
            )
            
            logger.info(
                f"Successfully upgraded user {user_id} to {plan_type.value}",
                extra={
                    "user_id": user_id,
                    "plan_type": plan_type.value,
                    "session_id": transaction["session_id"],
                    "amount": transaction["amount"]
                }
            )
            
        except Exception as e:
            logger.error(
                f"Error processing successful payment for user {transaction.get('user_id')}: {e}",
                exc_info=True
            )
            raise
    
    async def handle_webhook_event(self, webhook_data: dict) -> bool:
        """Handle Stripe webhook events"""
        try:
            event_type = webhook_data.get("event_type")
            session_id = webhook_data.get("session_id")
            
            logger.info(
                f"Processing webhook event: {event_type}",
                extra={
                    "event_type": event_type,
                    "session_id": session_id,
                    "event_id": webhook_data.get("event_id")
                }
            )
            
            if event_type == "checkout.session.completed":
                await self._handle_checkout_completed(webhook_data)
            elif event_type == "invoice.payment_succeeded":
                await self._handle_payment_succeeded(webhook_data)
            elif event_type == "customer.subscription.updated":
                await self._handle_subscription_updated(webhook_data)
            elif event_type == "customer.subscription.deleted":
                await self._handle_subscription_canceled(webhook_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling webhook event: {e}", exc_info=True)
            return False
    
    async def _handle_checkout_completed(self, webhook_data: dict):
        """Handle completed checkout session"""
        session_id = webhook_data.get("session_id")
        if session_id:
            # Update payment status and process upgrade
            status_response = await self.get_checkout_status(session_id)
    
    async def _handle_payment_succeeded(self, webhook_data: dict):
        """Handle successful payment"""
        # This is handled in checkout completion
        pass
    
    async def _handle_subscription_updated(self, webhook_data: dict):
        """Handle subscription updates"""
        # Handle subscription changes, renewals, etc.
        pass
    
    async def _handle_subscription_canceled(self, webhook_data: dict):
        """Handle subscription cancellation"""
        # Downgrade user to free plan
        pass