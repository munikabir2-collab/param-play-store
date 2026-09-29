
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    DateTime,
    Text,
)

from sqlalchemy.sql import func

from app.core.database import Base


class App(Base):
    __tablename__ = "apps"

    # =====================================================
    # PRIMARY KEY
    # =====================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    # =====================================================
    # DEVELOPER
    # =====================================================

    developer_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    # =====================================================
    # BASIC APP INFORMATION
    # =====================================================

    app_name = Column(
        String(100),
        nullable=False,
        index=True,
    )

    package_name = Column(
        String(255),
        nullable=True,
        index=True,
    )

    version = Column(
        String(50),
        nullable=False,
    )

    # =====================================================
    # FILE INFORMATION
    # =====================================================

    file_type = Column(
        String(10),
        nullable=False,
    )

    file_path = Column(
        String,
        nullable=False,
    )

    size_mb = Column(
        Float,
        nullable=True,
    )

    # =====================================================
    # APP CONTENT
    # =====================================================

    description = Column(
        Text,
        nullable=False,
        default="",
    )

    category = Column(
        String(50),
        nullable=False,
        default="Other",
        index=True,
    )

    changelog = Column(
        Text,
        nullable=False,
        default="",
    )

    # =====================================================
    # ICON
    # =====================================================

    icon_path = Column(
        String,
        nullable=True,
    )

    # =====================================================
    # MARKETPLACE STATUS
    #
    # pending  = waiting for publication
    # published = visible in marketplace
    # hidden   = developer/admin temporarily hides it
    # rejected = rejected by admin
    # =====================================================

    status = Column(
        String(20),
        nullable=False,
        default="published",
        index=True,
    )

    # =====================================================
    # MARKETPLACE STATISTICS
    # =====================================================

    download_count = Column(
        Integer,
        nullable=False,
        default=0,
    )

    view_count = Column(
        Integer,
        nullable=False,
        default=0,
    )

    rating = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    review_count = Column(
        Integer,
        nullable=False,
        default=0,
    )

    # =====================================================
    # TIMESTAMPS
    # =====================================================

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

