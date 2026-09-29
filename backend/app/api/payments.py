
import hashlib
import hmac
import os
from datetime import datetime, timezone
from decimal import Decimal

import razorpay

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)

from sqlalchemy.orm import Session

from app.core.database import get_db

from app.models.user_model import User

from app.models.payment_model import Payment

from app.models.developer_model import (
    DeveloperProfile,
    DeveloperVerification,
)

from app.api.auth import get_current_user

from app.schemas.payment_schema import (
    DeveloperPaymentOrderRequest,
    DeveloperPaymentOrderResponse,
    PaymentVerifyRequest,
    PaymentVerifyResponse,
    PaymentOut,
    PaymentHistoryOut,
    DeveloperPaymentStatusOut,
)


# ============================================================
# Router
# ============================================================

router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


# ============================================================
# Configuration
# ============================================================

RAZORPAY_KEY_ID = os.getenv(
    "RAZORPAY_KEY_ID",
    "",
)

RAZORPAY_KEY_SECRET = os.getenv(
    "RAZORPAY_KEY_SECRET",
    "",
)

RAZORPAY_WEBHOOK_SECRET = os.getenv(
    "RAZORPAY_WEBHOOK_SECRET",
    "",
)


# ============================================================
# Developer Registration Pricing
# ============================================================

# One-time developer registration fee.
#
# Database:
#   major currency units
#
# Razorpay:
#   minor currency units
#
# INR 999.00 -> 99900 paise
DEVELOPER_REGISTRATION_FEE = Decimal("999.00")

DEVELOPER_PAYMENT_TYPE = (
    "developer_registration"
)

DEFAULT_CURRENCY = "INR"

# Currently only INR is enabled.
#
# International currencies can be added later without
# changing the database payment structure.
SUPPORTED_CURRENCIES = {
    "INR",
}


# ============================================================
# Razorpay Client
# ============================================================

razorpay_client = None

if (
    RAZORPAY_KEY_ID
    and RAZORPAY_KEY_SECRET
):
    razorpay_client = razorpay.Client(
        auth=(
            RAZORPAY_KEY_ID,
            RAZORPAY_KEY_SECRET,
        )
    )


# ============================================================
# Helper Functions
# ============================================================

def require_razorpay():
    """
    Ensure Razorpay credentials are configured.
    """

    if razorpay_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Payment gateway is not configured. "
                "Please configure RAZORPAY_KEY_ID and "
                "RAZORPAY_KEY_SECRET."
            ),
        )


def require_developer_application(
    db: Session,
    user: User,
):
    """
    Ensure that the logged-in user has a developer
    application before making registration payment.
    """

    profile = (
        db.query(DeveloperProfile)
        .filter(
            DeveloperProfile.user_id
            == user.id
        )
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Please submit your developer application "
                "before making the registration payment."
            ),
        )

    return profile


def amount_to_paise(
    amount: Decimal,
) -> int:
    """
    Convert major currency units to minor units.

    Example:
        999.00 INR -> 99900 paise
    """

    return int(
        (
            amount
            * Decimal("100")
        ).quantize(
            Decimal("1")
        )
    )


def normalize_currency(
    currency: str,
) -> str:
    """
    Normalize currency code.
    """

    return currency.strip().upper()


def get_latest_developer_payment(
    db: Session,
    user_id: int,
):
    """
    Get latest developer registration payment.
    """

    return (
        db.query(Payment)
        .filter(
            Payment.user_id == user_id,
            Payment.payment_type
            == DEVELOPER_PAYMENT_TYPE,
        )
        .order_by(
            Payment.created_at.desc()
        )
        .first()
    )


def payment_to_response(
    payment: Payment,
) -> PaymentOut:
    """
    Convert SQLAlchemy Payment object
    to API schema.
    """

    return PaymentOut.model_validate(
        payment
    )


def get_developer_verification_status(
    db: Session,
    user_id: int,
) -> str | None:
    """
    Return current developer verification status.

    Possible values:
        pending
        approved
        rejected
        None
    """

    profile = (
        db.query(DeveloperProfile)
        .filter(
            DeveloperProfile.user_id
            == user_id
        )
        .first()
    )

    if profile is None:
        return None

    verification = (
        db.query(DeveloperVerification)
        .filter(
            DeveloperVerification.developer_id
            == profile.id
        )
        .first()
    )

    if verification is None:
        return None

    return (
        verification.status
        or ""
    ).strip().lower()


def sync_developer_activation(
    db: Session,
    user: User,
) -> None:
    """
    Keep developer activation state synchronized.

    Developer becomes ACTIVE only when:

        payment_status == paid
        AND
        verification_status == approved

    Payment and verification remain separate.
    """

    verification_status = (
        get_developer_verification_status(
            db,
            user.id,
        )
    )

    payment_paid = (
        (user.payment_status or "")
        .strip()
        .lower()
        == "paid"
    )

    verification_approved = (
        verification_status
        == "approved"
    )

    # --------------------------------------------------------
    # Fully activated
    # --------------------------------------------------------

    if (
        payment_paid
        and verification_approved
    ):

        user.is_developer = True

        user.developer_active = True

        user.developer_plan = "verified"

        if user.activated_at is None:

            now = datetime.now(
                timezone.utc
            )

            user.activated_at = (
                now.replace(
                    tzinfo=None
                )
            )

        return

    # --------------------------------------------------------
    # Payment paid but verification pending/rejected
    # --------------------------------------------------------

    if payment_paid:

        # Payment remains paid.
        #
        # Developer privileges remain inactive until
        # verification is approved.

        user.is_developer = False

        user.developer_active = False

        user.developer_plan = "free"

        user.activated_at = None

        return

    # --------------------------------------------------------
    # Verification approved but payment not paid
    # --------------------------------------------------------

    if verification_approved:

        # Verification can be approved independently,
        # but account cannot become active until payment
        # is completed.

        user.is_developer = True

        user.developer_active = False

        user.developer_plan = "verified"

        user.activated_at = None

        return

    # --------------------------------------------------------
    # Not approved / not paid
    # --------------------------------------------------------

    user.is_developer = False

    user.developer_active = False

    user.developer_plan = "free"

    user.activated_at = None


# ============================================================
# Create Developer Registration Payment Order
# ============================================================

@router.post(
    "/developer/create-order",
    response_model=DeveloperPaymentOrderResponse,
)
def create_developer_payment_order(
    payload: DeveloperPaymentOrderRequest,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    """
    Create one-time developer registration
    payment order.
    """

    require_razorpay()

    # --------------------------------------------------------
    # Developer application required
    # --------------------------------------------------------

    require_developer_application(
        db,
        current_user,
    )

    # --------------------------------------------------------
    # Already active developer
    # --------------------------------------------------------

    if current_user.developer_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Developer account is already active. "
                "Registration payment is not required again."
            ),
        )

    # --------------------------------------------------------
    # Already paid
    # --------------------------------------------------------

    if (
        current_user.payment_status
        == "paid"
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Developer registration payment has "
                "already been completed."
            ),
        )

    # --------------------------------------------------------
    # Currency
    # --------------------------------------------------------

    currency = normalize_currency(
        payload.currency
    )

    if currency not in SUPPORTED_CURRENCIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Currency '{currency}' is not currently "
                f"supported for this payment configuration."
            ),
        )

    # --------------------------------------------------------
    # Existing payment
    # --------------------------------------------------------

    latest_payment = (
        get_latest_developer_payment(
            db,
            current_user.id,
        )
    )

    if latest_payment:

        # ----------------------------------------------------
        # Existing successful payment
        # ----------------------------------------------------

        if latest_payment.status == "paid":

            current_user.payment_status = "paid"

            sync_developer_activation(
                db,
                current_user,
            )

            db.commit()

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Developer registration payment "
                    "has already been completed."
                ),
            )

        # ----------------------------------------------------
        # Existing pending order
        # ----------------------------------------------------

        if (
            latest_payment.status
            == "pending"
            and latest_payment.order_id
        ):

            return DeveloperPaymentOrderResponse(
                payment_id=latest_payment.id,
                order_id=latest_payment.order_id,
                amount=latest_payment.amount,
                currency=latest_payment.currency,
                payment_type=(
                    latest_payment.payment_type
                ),
                gateway=latest_payment.gateway,
                status=latest_payment.status,
            )

    # --------------------------------------------------------
    # Server-controlled amount
    # --------------------------------------------------------

    amount = (
        DEVELOPER_REGISTRATION_FEE
    )

    amount_paise = amount_to_paise(
        amount
    )

    # --------------------------------------------------------
    # Create Razorpay order
    # --------------------------------------------------------

    try:

        razorpay_order = (
            razorpay_client.order.create(
                {
                    "amount": amount_paise,
                    "currency": currency,
                    "receipt": (
                        f"developer_"
                        f"{current_user.id}_"
                        f"{int(datetime.now().timestamp())}"
                    ),
                }
            )
        )

    except Exception as exc:

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Unable to create payment order. "
                "Please try again later."
            ),
        ) from exc

    razorpay_order_id = (
        razorpay_order.get("id")
    )

    if not razorpay_order_id:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Payment gateway did not return "
                "an order ID."
            ),
        )

    # --------------------------------------------------------
    # Save payment transaction
    # --------------------------------------------------------

    payment = Payment(
        user_id=current_user.id,
        payment_type=(
            DEVELOPER_PAYMENT_TYPE
        ),
        amount=amount,
        currency=currency,
        country=current_user.country,
        gateway="razorpay",
        order_id=razorpay_order_id,
        status="pending",
    )

    db.add(payment)

    current_user.payment_status = "pending"

    # Payment pending means developer cannot be active.
    sync_developer_activation(
        db,
        current_user,
    )

    db.commit()

    db.refresh(payment)

    return DeveloperPaymentOrderResponse(
        payment_id=payment.id,
        order_id=payment.order_id,
        amount=payment.amount,
        currency=payment.currency,
        payment_type=(
            payment.payment_type
        ),
        gateway=payment.gateway,
        status=payment.status,
    )


# ============================================================
# Verify Developer Registration Payment
# ============================================================

@router.post(
    "/developer/verify",
    response_model=PaymentVerifyResponse,
)
def verify_developer_payment(
    payload: PaymentVerifyRequest,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    """
    Verify Razorpay payment signature.

    Successful payment:
        payment.status = paid
        user.payment_status = paid

    Developer activation:
        only when verification is also approved.
    """

    require_razorpay()

    # --------------------------------------------------------
    # Find payment belonging to logged-in user
    # --------------------------------------------------------

    payment = (
        db.query(Payment)
        .filter(
            Payment.user_id
            == current_user.id,
            Payment.payment_type
            == DEVELOPER_PAYMENT_TYPE,
            Payment.order_id
            == payload.order_id,
        )
        .first()
    )

    if not payment:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment order not found.",
        )

    # --------------------------------------------------------
    # Already paid
    # --------------------------------------------------------

    if payment.status == "paid":

        current_user.payment_status = "paid"

        sync_developer_activation(
            db,
            current_user,
        )

        db.commit()

        return PaymentVerifyResponse(
            success=True,
            message=(
                "Payment has already been verified."
            ),
            payment_id=payment.id,
            order_id=payment.order_id,
            status=payment.status,
            payment_status="paid",
            developer_active=(
                current_user.developer_active
            ),
        )

    # --------------------------------------------------------
    # Order ID verification
    # --------------------------------------------------------

    if payment.order_id != payload.order_id:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment order.",
        )

    # --------------------------------------------------------
    # Signature required
    # --------------------------------------------------------

    if not payload.signature:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Payment signature is required."
            ),
        )

    # --------------------------------------------------------
    # Razorpay signature verification
    # --------------------------------------------------------

    try:

        razorpay_client.utility.verify_payment_signature(
            {
                "razorpay_order_id": (
                    payload.order_id
                ),
                "razorpay_payment_id": (
                    payload.payment_id
                ),
                "razorpay_signature": (
                    payload.signature
                ),
            }
        )

    except Exception as exc:

        payment.status = "failed"

        payment.failure_reason = (
            "Payment signature verification failed."
        )

        # IMPORTANT:
        # Do not overwrite a previously paid user with
        # failed state here because this branch is only
        # reached for a payment record that is not paid.

        current_user.payment_status = "failed"

        sync_developer_activation(
            db,
            current_user,
        )

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Payment verification failed."
            ),
        ) from exc

    # --------------------------------------------------------
    # Store verified payment details
    # --------------------------------------------------------

    payment.payment_id = (
        payload.payment_id
    )

    payment.signature = (
        payload.signature
    )

    payment.status = "paid"

    payment.paid_at = (
        datetime.now(
            timezone.utc
        ).replace(
            tzinfo=None
        )
    )

    # --------------------------------------------------------
    # User payment state
    # --------------------------------------------------------

    current_user.payment_status = "paid"

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # Payment alone does not automatically activate
    # the developer.
    #
    # If verification is already approved, the helper
    # will activate the developer.
    # Otherwise developer remains inactive.
    # --------------------------------------------------------

    sync_developer_activation(
        db,
        current_user,
    )

    db.commit()

    db.refresh(payment)
    db.refresh(current_user)

    return PaymentVerifyResponse(
        success=True,
        message=(
            "Payment verified successfully. "
            "Developer verification status will "
            "determine account activation."
        ),
        payment_id=payment.id,
        order_id=payment.order_id,
        status=payment.status,
        payment_status=(
            current_user.payment_status
        ),
        developer_active=(
            current_user.developer_active
        ),
    )


# ============================================================
# Developer Payment Status
# ============================================================

@router.get(
    "/developer/status",
    response_model=DeveloperPaymentStatusOut,
)
def get_developer_payment_status(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    """
    Get current developer registration payment status.
    """

    latest_payment = (
        get_latest_developer_payment(
            db,
            current_user.id,
        )
    )

    # --------------------------------------------------------
    # No payment yet
    # --------------------------------------------------------

    if not latest_payment:

        return DeveloperPaymentStatusOut(
            payment_required=(
                not current_user.developer_active
            ),
            payment_status=(
                current_user.payment_status
            ),
            payment_type=(
                DEVELOPER_PAYMENT_TYPE
            ),
            amount=(
                DEVELOPER_REGISTRATION_FEE
            ),
            currency=DEFAULT_CURRENCY,
            latest_payment_id=None,
            latest_order_id=None,
            paid_at=None,
        )

    # --------------------------------------------------------
    # Existing payment
    # --------------------------------------------------------

    return DeveloperPaymentStatusOut(
        payment_required=(
            latest_payment.status != "paid"
            and not current_user.developer_active
        ),
        payment_status=(
            latest_payment.status
        ),
        payment_type=(
            latest_payment.payment_type
        ),
        amount=latest_payment.amount,
        currency=latest_payment.currency,
        latest_payment_id=(
            latest_payment.id
        ),
        latest_order_id=(
            latest_payment.order_id
        ),
        paid_at=latest_payment.paid_at,
    )


# ============================================================
# My Payment History
# ============================================================

@router.get(
    "/my",
    response_model=PaymentHistoryOut,
)
def get_my_payments(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    """
    Return logged-in user's complete payment history.
    """

    payments = (
        db.query(Payment)
        .filter(
            Payment.user_id
            == current_user.id
        )
        .order_by(
            Payment.created_at.desc()
        )
        .all()
    )

    return PaymentHistoryOut(
        payments=[
            payment_to_response(
                payment
            )
            for payment in payments
        ]
    )


# ============================================================
# Get Single Payment
# ============================================================

@router.get(
    "/{payment_id}",
    response_model=PaymentOut,
)
def get_payment(
    payment_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    """
    Return one payment belonging to the
    logged-in user.
    """

    payment = (
        db.query(Payment)
        .filter(
            Payment.id == payment_id,
            Payment.user_id
            == current_user.id,
        )
        .first()
    )

    if not payment:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found.",
        )

    return payment_to_response(
        payment
    )


# ============================================================
# Razorpay Webhook
# ============================================================

@router.post(
    "/webhook",
)
async def razorpay_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Razorpay webhook endpoint.

    Webhook signature is verified against
    the raw request body.
    """

    if not RAZORPAY_WEBHOOK_SECRET:

        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "Payment webhook is not configured."
            ),
        )

    body = await request.body()

    webhook_signature = (
        request.headers.get(
            "X-Razorpay-Signature"
        )
    )

    if not webhook_signature:

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "Webhook signature missing."
            ),
        )

    # --------------------------------------------------------
    # Verify webhook signature
    # --------------------------------------------------------

    expected_signature = hmac.new(
        RAZORPAY_WEBHOOK_SECRET.encode(
            "utf-8"
        ),
        body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(
        expected_signature,
        webhook_signature,
    ):

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "Invalid webhook signature."
            ),
        )

    # --------------------------------------------------------
    # Parse JSON
    # --------------------------------------------------------

    try:

        payload = await request.json()

    except Exception as exc:

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail="Invalid webhook JSON.",
        ) from exc

    event = payload.get(
        "event",
        "",
    )

    payment_entity = (
        payload
        .get("payload", {})
        .get("payment", {})
        .get("entity", {})
    )

    order_id = payment_entity.get(
        "order_id"
    )

    payment_id = payment_entity.get(
        "id"
    )

    # --------------------------------------------------------
    # Ignore events without order ID
    # --------------------------------------------------------

    if not order_id:

        return {
            "success": True,
            "message": "Webhook received.",
            "event": event,
        }

    # --------------------------------------------------------
    # Find payment
    # --------------------------------------------------------

    payment = (
        db.query(Payment)
        .filter(
            Payment.order_id
            == order_id
        )
        .first()
    )

    if not payment:

        # Never create arbitrary payment records
        # from unknown gateway orders.

        return {
            "success": True,
            "message": "Unknown order ignored.",
            "event": event,
        }

    # --------------------------------------------------------
    # Payment captured / order paid
    # --------------------------------------------------------

    if event in {
        "payment.captured",
        "order.paid",
    }:

        # ----------------------------------------------------
        # Idempotent success handling
        # ----------------------------------------------------

        payment.status = "paid"

        if payment_id:
            payment.payment_id = (
                payment_id
            )

        if payment.paid_at is None:

            payment.paid_at = (
                datetime.now(
                    timezone.utc
                ).replace(
                    tzinfo=None
                )
            )

        user = (
            db.query(User)
            .filter(
                User.id
                == payment.user_id
            )
            .first()
        )

        if user:

            user.payment_status = "paid"

            # Activation only happens when verification
            # is also approved.
            sync_developer_activation(
                db,
                user,
            )

        db.commit()

        return {
            "success": True,
            "message": (
                "Payment marked as paid."
            ),
            "event": event,
            "order_id": order_id,
        }

    # --------------------------------------------------------
    # Payment failed
    # --------------------------------------------------------

    if event == "payment.failed":

        # Do not overwrite an already-paid transaction.
        if payment.status == "paid":

            return {
                "success": True,
                "message": (
                    "Payment already marked as paid."
                ),
                "event": event,
                "order_id": order_id,
            }

        payment.status = "failed"

        error_description = (
            payment_entity.get(
                "error_description"
            )
        )

        if error_description:

            payment.failure_reason = (
                error_description
            )

        user = (
            db.query(User)
            .filter(
                User.id
                == payment.user_id
            )
            .first()
        )

        if user:

            # Only update payment state when there
            # is no already-paid state.
            if user.payment_status != "paid":

                user.payment_status = "failed"

                sync_developer_activation(
                    db,
                    user,
                )

        db.commit()

        return {
            "success": True,
            "message": (
                "Payment marked as failed."
            ),
            "event": event,
            "order_id": order_id,
        }

    # --------------------------------------------------------
    # Refund events
    # --------------------------------------------------------

    if event in {
        "refund.created",
        "refund.processed",
        "refund.failed",
    }:

        # Refund processing will be implemented separately
        # with explicit refund_reference / refunded_at
        # handling.
        #
        # We intentionally do not mark the original payment
        # refunded from an incomplete webhook structure.

        db.commit()

        return {
            "success": True,
            "message": (
                "Refund webhook received."
            ),
            "event": event,
            "order_id": order_id,
        }

    # --------------------------------------------------------
    # Other valid webhook events
    # --------------------------------------------------------

    return {
        "success": True,
        "message": "Webhook received.",
        "event": event,
        "order_id": order_id,
    }

