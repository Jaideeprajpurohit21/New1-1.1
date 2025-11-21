#!/usr/bin/env python3
"""
LUMINA - AI-POWERED RECEIPT MANAGEMENT SYSTEM
Billing and Subscription Models

Copyright (c) 2024 Jaideep Singh Rajpurohit. All rights reserved.
PROPRIETARY SOFTWARE - UNAUTHORIZED USE PROHIBITED
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class PlanType(str, Enum):
    """Available subscription plans"""
    FREE = "free"
    PRO = "pro"

class SubscriptionStatus(str, Enum):
    """Stripe subscription status"""
    ACTIVE = "active"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    PAST_DUE = "past_due"
    PAUSED = "paused"
    TRIALING = "trialing"
    UNPAID = "unpaid"

class PaymentStatus(str, Enum):
    """Payment transaction status"""
    INITIATED = "initiated"
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELED = "canceled"

# Plan configuration
PLAN_CONFIG = {
    PlanType.FREE: {
        "name": "Free Plan",
        "price": 0.0,
        "currency": "usd",
        "receipt_limit": 50,
        "features": [
            "50 receipts per month",
            "Basic OCR processing",
            "Manual categorization",
            "CSV export"
        ],
        "stripe_price_id": None
    },
    PlanType.PRO: {
        "name": "Pro Plan",
        "price": 9.99,
        "currency": "usd",
        "receipt_limit": 500,
        "features": [
            "500 receipts per month",
            "Advanced OCR processing",
            "AI-powered categorization",
            "Advanced search & filtering",
            "CSV export",
            "Priority support"
        ],
        "stripe_price_id": "price_pro_monthly"  # Will be set in production
    }
}

class PaymentTransaction(BaseModel):
    """Payment transaction record"""
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    user_id: Optional[str] = None
    email: Optional[str] = None
    session_id: str
    amount: float
    currency: str
    plan_type: PlanType
    payment_status: PaymentStatus = PaymentStatus.INITIATED
    stripe_payment_intent_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BillingInfo(BaseModel):
    """User billing information response"""
    plan: PlanType
    plan_name: str
    receipt_limit: int
    receipts_used: int
    receipts_remaining: int
    subscription_status: Optional[SubscriptionStatus] = None
    billing_period_start: Optional[datetime] = None
    billing_period_end: Optional[datetime] = None
    next_billing_date: Optional[datetime] = None
    can_upgrade: bool
    features: list[str]

class CheckoutRequest(BaseModel):
    """Request to create checkout session"""
    plan_type: PlanType
    origin_url: str = Field(..., description="Frontend origin URL for success/cancel redirects")

class CheckoutResponse(BaseModel):
    """Response from checkout session creation"""
    checkout_url: str
    session_id: str

class WebhookEvent(BaseModel):
    """Stripe webhook event data"""
    event_type: str
    event_id: str
    session_id: Optional[str] = None
    subscription_id: Optional[str] = None
    customer_id: Optional[str] = None
    payment_status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None