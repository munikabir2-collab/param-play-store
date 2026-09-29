
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


# ============================================================
# Developer Registration Payment
# ============================================================

class DeveloperPaymentOrderRequest(BaseModel):
    """
    Developer registration ke one-time payment ke liye
    payment order create karne ka request.
    """

    currency: str = Field(
        default="INR",
        min_length=3,
        max_length=3,
        description="3-letter ISO currency code, e.g. INR, USD, EUR",
    )


class DeveloperPaymentOrderResponse(BaseModel):
    """
    Payment gateway order create hone ke baad
    frontend ko return hone wala response.
    """

    payment_id: int

    order_id: str

    amount: Decimal

    currency: str

    payment_type: str

    gateway: str

    status: str


# ============================================================
# Payment Verification
# ============================================================

class PaymentVerifyRequest(BaseModel):
    """
    Successful payment ke baad frontend se backend ko
    payment verification ke liye bheja jayega.
    """

    order_id: str = Field(
        min_length=1,
        max_length=255,
    )

    payment_id: str = Field(
        min_length=1,
        max_length=255,
    )

    signature: Optional[str] = Field(
        default=None,
        max_length=1000,
    )


class PaymentVerifyResponse(BaseModel):
    """
    Payment verification ke baad backend response.
    """

    success: bool

    message: str

    payment_id: Optional[int] = None

    order_id: Optional[str] = None

    status: str

    payment_status: str

    developer_active: bool


# ============================================================
# Payment Details
# ============================================================

class PaymentOut(BaseModel):
    """
    Single payment transaction ka response.
    """

    id: int

    user_id: int

    payment_type: str

    amount: Decimal

    currency: str

    country: Optional[str] = None

    gateway: str

    order_id: Optional[str] = None

    payment_id: Optional[str] = None

    signature: Optional[str] = None

    status: str

    created_at: datetime

    paid_at: Optional[datetime] = None

    failure_reason: Optional[str] = None

    refund_reference: Optional[str] = None

    refunded_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================
# Payment History
# ============================================================

class PaymentHistoryOut(BaseModel):
    """
    Logged-in user ke payment history ka response.
    """

    payments: list[PaymentOut]


# ============================================================
# Developer Payment Status
# ============================================================

class DeveloperPaymentStatusOut(BaseModel):
    """
    Developer registration payment ka current status.
    """

    payment_required: bool

    payment_status: str

    payment_type: str

    amount: Decimal

    currency: str

    latest_payment_id: Optional[int] = None

    latest_order_id: Optional[str] = None

    paid_at: Optional[datetime] = None


# ============================================================
# Payment Failure
# ============================================================

class PaymentFailureRequest(BaseModel):
    """
    Payment fail hone par optional failure information.
    """

    order_id: Optional[str] = Field(
        default=None,
        max_length=255,
    )

    reason: Optional[str] = Field(
        default=None,
        max_length=2000,
    )


# ============================================================
# Payment Webhook
# ============================================================

class PaymentWebhookEvent(BaseModel):
    """
    Payment gateway webhook event ke liye generic schema.

    Gateway-specific fields ko baad mein gateway ke according
    extend kiya ja sakta hai.
    """

    event: str

    order_id: Optional[str] = None

    payment_id: Optional[str] = None

    status: Optional[str] = None

    signature: Optional[str] = None


# ============================================================
# Generic Payment Response
# ============================================================

class PaymentResponse(BaseModel):
    """
    Generic payment API response.
    """

    success: bool

    message: str

    payment_id: Optional[int] = None

    order_id: Optional[str] = None

    status: Optional[str] = None

