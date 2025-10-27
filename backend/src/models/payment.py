"""Payment model (stub for Phase 3, full implementation in Phase 4).

Minimal implementation to support User Story 1 relationships.
Full implementation in T056-T057.
"""
from datetime import date, datetime
from enum import Enum as PyEnum
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..core.database import Base


class PaymentMethod(str, PyEnum):
    """Payment method enumeration."""

    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    ONLINE = "online"
    UPI = "upi"
    CARD = "card"
    OTHER = "other"


class PaymentType(str, PyEnum):
    """Payment type enumeration."""

    RENT = "rent"
    SECURITY_DEPOSIT = "security_deposit"
    BILL_SHARE = "bill_share"
    PENALTY = "penalty"
    OTHER = "other"


class Payment(Base):
    """Payment model representing financial transactions."""

    __tablename__ = "payments"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
        comment="Payment identifier",
    )

    # Foreign Keys
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Paying tenant",
    )
    property_id = Column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Related property",
    )
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
        comment="User who recorded payment",
    )

    # Payment Details
    amount = Column(
        Numeric(12, 2),
        nullable=False,
        comment="Payment amount",
    )
    currency = Column(
        String(3),
        nullable=False,
        comment="ISO 4217 currency code",
    )
    payment_method = Column(
        Enum(PaymentMethod, name="payment_method"),
        nullable=False,
        comment="Payment method",
    )
    payment_type = Column(
        Enum(PaymentType, name="payment_type"),
        nullable=False,
        comment="Type of payment",
    )
    payment_date = Column(
        Date,
        nullable=False,
        index=True,
        comment="Date payment received",
    )

    # Additional Info
    reference_number = Column(
        String(100),
        nullable=True,
        comment="Transaction reference",
    )
    notes = Column(
        Text,
        nullable=True,
        comment="Additional notes",
    )
    receipt_url = Column(
        String(500),
        nullable=True,
        comment="S3 URL to receipt PDF",
    )
    device_id = Column(
        String(100),
        nullable=True,
        comment="Device that created record (for sync)",
    )

    # Void Support
    is_voided = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Payment voided flag",
    )
    voided_at = Column(
        DateTime,
        nullable=True,
        comment="Void timestamp",
    )
    voided_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who voided payment",
    )
    void_reason = Column(
        Text,
        nullable=True,
        comment="Reason for voiding",
    )

    # Timestamps
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Record creation timestamp",
    )

    # Relationships
    tenant = relationship(
        "Tenant",
        back_populates="payments",
        foreign_keys=[tenant_id],
    )
    property = relationship(
        "Property",
        back_populates="payments",
        foreign_keys=[property_id],
    )
    creator = relationship(
        "User",
        back_populates="created_payments",
        foreign_keys=[created_by],
    )
    voider = relationship(
        "User",
        foreign_keys=[voided_by],
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("amount > 0", name="check_amount_positive"),
        Index("idx_payments_date", "payment_date", postgresql_ops={"payment_date": "DESC"}),
    )

    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, tenant_id={self.tenant_id}, amount={self.amount})>"
