"""Notification model for push notifications.

Implements T235 from tasks.md.
"""
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import relationship

from ..core.database import Base


class NotificationType(str, PyEnum):
    """Notification type enumeration."""
    
    PAYMENT_RECEIVED = "payment_received"
    PAYMENT_OVERDUE = "payment_overdue"
    BILL_CREATED = "bill_created"
    BILL_ALLOCATED = "bill_allocated"
    DOCUMENT_UPLOADED = "document_uploaded"
    DOCUMENT_EXPIRING = "document_expiring"
    RENT_INCREMENT = "rent_increment"
    MESSAGE_RECEIVED = "message_received"
    EXPENSE_SUBMITTED = "expense_submitted"
    EXPENSE_APPROVED = "expense_approved"
    LEASE_EXPIRING = "lease_expiring"
    MAINTENANCE_SCHEDULED = "maintenance_scheduled"
    SYSTEM_ANNOUNCEMENT = "system_announcement"


class NotificationPriority(str, PyEnum):
    """Notification priority level."""
    
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Notification(Base):
    """Notification model for push notifications.
    
    Stores notification records for push notifications sent to users.
    Integrates with Firebase Cloud Messaging (FCM) for mobile push.
    
    Features:
    - Multiple notification types for different events
    - Priority levels for notification importance
    - Read/unread status tracking
    - Deep link support for navigation
    - Metadata for additional context
    - FCM message ID tracking
    
    Access Control via RLS:
    - Users see only their own notifications
    """

    __tablename__ = "notifications"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
        comment="Notification identifier",
    )

    # Foreign Keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Recipient user",
    )

    # Notification Content
    title = Column(
        String(200),
        nullable=False,
        comment="Notification title/heading",
    )
    body = Column(
        Text,
        nullable=False,
        comment="Notification message body",
    )
    notification_type = Column(
        Enum(NotificationType, name="notification_type"),
        nullable=False,
        index=True,
        comment="Type of notification",
    )
    priority = Column(
        Enum(NotificationPriority, name="notification_priority"),
        default=NotificationPriority.NORMAL,
        nullable=False,
        comment="Notification priority level",
    )

    # Navigation & Context
    deep_link = Column(
        String(500),
        nullable=True,
        comment="Deep link for in-app navigation (e.g., /payments/123)",
    )
    metadata = Column(
        JSON,
        nullable=True,
        comment="Additional context data as JSON",
    )

    # Status & Tracking
    is_read = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Read status",
    )
    read_at = Column(
        DateTime,
        nullable=True,
        comment="When notification was marked as read",
    )
    fcm_message_id = Column(
        String(200),
        nullable=True,
        comment="Firebase Cloud Messaging message ID",
    )
    sent_at = Column(
        DateTime,
        nullable=True,
        comment="When push notification was sent",
    )
    delivery_failed = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether delivery failed",
    )
    failure_reason = Column(
        Text,
        nullable=True,
        comment="Reason for delivery failure",
    )

    # Timestamps
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
        comment="Record creation timestamp",
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Last update timestamp",
    )

    # Relationships
    user = relationship(
        "User",
        back_populates="notifications",
        foreign_keys=[user_id],
    )

    # Indexes
    __table_args__ = (
        Index("ix_notifications_user_unread", "user_id", "is_read"),
        Index("ix_notifications_user_type", "user_id", "notification_type"),
        Index("ix_notifications_created_desc", "created_at", postgresql_using="btree", postgresql_ops={"created_at": "DESC"}),
    )

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, user_id={self.user_id}, type={self.notification_type}, is_read={self.is_read})>"

    @property
    def is_unread(self) -> bool:
        """Check if notification is unread."""
        return not self.is_read

    def mark_as_read(self) -> None:
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.utcnow()

    def mark_as_unread(self) -> None:
        """Mark notification as unread."""
        if self.is_read:
            self.is_read = False
            self.read_at = None
