

from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Text,
)

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    # =========================================================
    # BASIC ACCOUNT
    # =========================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    email = Column(
        String,
        unique=True,
        index=True,
        nullable=False,
    )

    hashed_password = Column(
        String,
        nullable=False,
    )

    # =========================================================
    # ACCOUNT FLAGS
    # =========================================================

    is_developer = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    is_admin = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    # =========================================================
    # DEVELOPER PLAN
    # =========================================================

    developer_active = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    developer_plan = Column(
        String,
        default="free",
        nullable=False,
    )

    payment_status = Column(
        String,
        default="unpaid",
        nullable=False,
    )

    activated_at = Column(
        DateTime,
        nullable=True,
    )

    # =========================================================
    # DEVELOPER PROFILE
    # =========================================================

    full_name = Column(
        String(150),
        nullable=True,
    )

    developer_type = Column(
        String(30),
        default="individual",
        nullable=False,
    )

    country = Column(
        String(100),
        nullable=True,
    )

    phone = Column(
        String(30),
        nullable=True,
    )

    address = Column(
        Text,
        nullable=True,
    )

    company_name = Column(
        String(150),
        nullable=True,
    )

    bio = Column(
        Text,
        nullable=True,
    )

    website = Column(
        String(500),
        nullable=True,
    )

    github = Column(
        String(500),
        nullable=True,
    )

