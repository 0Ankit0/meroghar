"""
Message model for SMS/WhatsApp reminders.

Implements T157 from tasks.md.
"""
from datetime import datetime
from typing import Optional
import enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Boolean,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from ..core.database import Base


class MessageChannel(str, enum.Enum):
    """Message delivery channel."""
    SMS = "sms"
    WHATSAPP = "whatsapp"
    EMAIL = "email"


class MessageStatus(str, enum.Enum):
    """Message delivery status."""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MessageTemplate(str, enum.Enum):
    """Predefined message templates."""
    PAYMENT_REMINDER = "payment_reminder"
    PAYMENT_OVERDUE = "payment_overdue"
    PAYMENT_RECEIVED = "payment_received"
    LEASE_EXPIRING = "lease_expiring"
    MAINTENANCE_NOTICE = "maintenance_notice"
    CUSTOM = "custom"


class Message(Base):
    """Message model for SMS/WhatsApp/Email communications.
    
    Features:
    - Multiple delivery channels (SMS, WhatsApp, Email)
    - Template-based messaging
    - Scheduled delivery
    - Delivery tracking and status updates
    - Bulk messaging support
    - Personalization with tenant data
    """
    
    __tablename__ = "messages"
    
    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    tenant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Recipient tenant"
    )
    sent_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
        index=True,
        comment="User who sent the message"
    )
    property_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("properties.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Related property (optional)"
    )
    
    # Message Content
    template: Mapped[MessageTemplate] = mapped_column(
        SQLEnum(MessageTemplate, name="message_template"),
        nullable=False,
        comment="Template used for message"
    )
    subject: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Message subject (for email)"
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Message body content"
    )
    
    # Delivery Configuration
    channel: Mapped[MessageChannel] = mapped_column(
        SQLEnum(MessageChannel, name="message_channel"),
        nullable=False,
        comment="Delivery channel"
    )
    recipient_phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Phone number for SMS/WhatsApp"
    )
    recipient_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Email address for email channel"
    )
    
    # Status and Tracking
    status: Mapped[MessageStatus] = mapped_column(
        SQLEnum(MessageStatus, name="message_status"),
        nullable=False,
        default=MessageStatus.PENDING,
        comment="Current message status"
    )
    
    # Scheduling
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Scheduled send time"
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Actual send time"
    )
    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Delivery confirmation time"
    )
    
    # Error Handling
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Error details if failed"
    )
    retry_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of retry attempts"
    )
    max_retries: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
        comment="Maximum retry attempts"
    )
    
    # External Provider Data
    provider_message_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="External provider's message ID (Twilio SID, etc.)"
    )
    provider_response: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Full provider response"
    )
    
    # Metadata
    metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional message metadata"
    )
    
    # Bulk Message Grouping
    bulk_message_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="ID for bulk message batch"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="Record creation timestamp"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Last update timestamp"
    )
    
    # Relationships
    tenant = relationship(
        "Tenant",
        back_populates="messages",
        foreign_keys=[tenant_id]
    )
    sender = relationship(
        "User",
        back_populates="sent_messages",
        foreign_keys=[sent_by]
    )
    property = relationship(
        "Property",
        back_populates="messages",
        foreign_keys=[property_id]
    )
    
    def __repr__(self) -> str:
        return f"<Message(id={self.id}, tenant_id={self.tenant_id}, channel={self.channel}, status={self.status})>"
    
    @property
    def is_pending(self) -> bool:
        """Check if message is pending delivery."""
        return self.status in (MessageStatus.PENDING, MessageStatus.SCHEDULED)
    
    @property
    def is_sent(self) -> bool:
        """Check if message has been sent."""
        return self.status in (MessageStatus.SENT, MessageStatus.DELIVERED)
    
    @property
    def has_failed(self) -> bool:
        """Check if message delivery failed."""
        return self.status == MessageStatus.FAILED
    
    @property
    def can_retry(self) -> bool:
        """Check if message can be retried."""
        return self.has_failed and self.retry_count < self.max_retries
