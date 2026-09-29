from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    DateTime,
    ForeignKey,
    Text,
)

from sqlalchemy.sql import func

from app.core.database import Base


class Payment(Base):
    __tablename__ = "payments"

    # =========================================================
    # PRIMARY KEY
    # =========================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    # =========================================================
    # USER
    # =========================================================

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    # =========================================================
    # PAYMENT TYPE
    # =========================================================
    # Future-ready:
    # developer_registration
    # app_purchase
    # featured_listing
    # promotion

    payment_type = Column(
        String(50),
        nullable=False,
        index=True,
    )

    # =========================================================
    # AMOUNT
    # =========================================================

    amount = Column(
        Numeric(18, 2),
        nullable=False,
    )

    currency = Column(
        String(3),
        nullable=False,
        default="INR",
    )

    # =========================================================
    # COUNTRY
    # =========================================================

    country = Column(
        String(100),
        nullable=True,
    )

    # =========================================================
    # PAYMENT GATEWAY
    # =========================================================

    gateway = Column(
        String(50),
        nullable=False,
    )

    # =========================================================
    # GATEWAY REFERENCES
    # =========================================================

    order_id = Column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
    )

    payment_id = Column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
    )

    signature = Column(
        Text,
        nullable=True,
    )

    # =========================================================
    # STATUS
    # =========================================================

    status = Column(
        String(30),
        nullable=False,
        default="pending",
        index=True,
    )

    # =========================================================
    # TIMESTAMPS
    # =========================================================

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    paid_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    # =========================================================
    # FAILURE / REFUND INFORMATION
    # =========================================================

    failure_reason = Column(
        Text,
        nullable=True,
    )

    refund_reference = Column(
        String(255),
        nullable=True,
    )

    refunded_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )