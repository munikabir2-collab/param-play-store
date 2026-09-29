
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
)

from sqlalchemy.sql import func

from app.core.database import Base


class DeveloperProfile(Base):
    __tablename__ = "developer_profiles"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
        index=True,
    )

    full_name = Column(
        String(150),
        nullable=False,
    )

    developer_type = Column(
        String(30),
        nullable=False,
        default="individual",
    )

    country = Column(
        String(100),
        nullable=False,
    )

    phone = Column(
        String(30),
        nullable=False,
    )

    address = Column(
        Text,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class DeveloperVerification(Base):
    __tablename__ = "developer_verifications"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    developer_id = Column(
        Integer,
        ForeignKey("developer_profiles.id"),
        unique=True,
        nullable=False,
        index=True,
    )

    status = Column(
        String(30),
        nullable=False,
        default="pending",
    )

    verification_method = Column(
        String(50),
        nullable=True,
    )

    verification_reference = Column(
        String(255),
        nullable=True,
    )

    rejection_reason = Column(
        Text,
        nullable=True,
    )

    submitted_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    verified_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    reviewed_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
    )

