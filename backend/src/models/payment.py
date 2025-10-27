"""Payment models for rent and other payment tracking.

Implements T056-T057 from tasks.md.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.database import Base


class PaymentMethod(str, Enum):
    """Payment method options."""

    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    UPI = "upi"
    CHEQUE = "cheque"
    CARD = "card"
    ONLINE = "online"


class PaymentStatus(str, Enum):
    """Payment status options."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentType(str, Enum):
    """Payment type options."""

    RENT = "rent"
    SECURITY_DEPOSIT = "security_deposit"
    UTILITY = "utility"
    MAINTENANCE = "maintenance"
    OTHER = "other"


class Payment(Base):
    """Payment records for rent and other charges.

    Tracks all payments made by tenants including rent, deposits, and utilities.
    """

    __tablename__ = "payments"

    # Primary key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign keys
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    property_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("properties.id", ondelete="CASCADE"), nullable=False
    )
    recorded_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Payment details
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    payment_method: Mapped[PaymentMethod] = mapped_column(
        SQLEnum(PaymentMethod, name="payment_method", create_type=False),
        nullable=False,
        default=PaymentMethod.CASH,
    )
    payment_type: Mapped[PaymentType] = mapped_column(
        SQLEnum(PaymentType, name="payment_type", create_type=False),
        nullable=False,
        default=PaymentType.RENT,
    )
    status: Mapped[PaymentStatus] = mapped_column(
        SQLEnum(PaymentStatus, name="payment_status", create_type=False),
        nullable=False,
        default=PaymentStatus.COMPLETED,
    )

    # Payment period (for rent payments)
    payment_period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    payment_period_end: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Transaction reference
    transaction_reference: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )

    # Gateway transaction ID (from payment gateway)
    gateway_transaction_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )

    # T124: Gateway fee tracking for online payments
    gateway_fee: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=10, scale=2), nullable=True, default=Decimal("0.00")
    )

    # Metadata for storing gateway-specific information (pidx, verification status, etc.)
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Receipt
    receipt_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Timestamps
    payment_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="payments")
    property: Mapped["Property"] = relationship("Property", back_populates="payments")
    recorder: Mapped["User"] = relationship(
        "User", foreign_keys=[recorded_by], back_populates="created_payments"
    )
    transaction: Mapped["Transaction"] = relationship(
        "Transaction", back_populates="payment", uselist=False
    )

    def __repr__(self) -> str:
        return (
            f"<Payment(id={self.id}, tenant_id={self.tenant_id}, "
            f"amount={self.amount}, method={self.payment_method.value}, "
            f"type={self.payment_type.value}, status={self.status.value})>"
        )


class TransactionStatus(str, Enum):
    """Transaction status for payment gateway records."""

    INITIATED = "initiated"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Transaction(Base):
    """Transaction records for payment gateway integration.

    Stores raw transaction data from payment gateways (Razorpay, Stripe, etc.)
    for audit trail and reconciliation.
    """

    __tablename__ = "transactions"

    # Primary key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign key to payment
    payment_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("payments.id", ondelete="SET NULL"), nullable=True
    )

    # Gateway details
    gateway_name: Mapped[str] = mapped_column(String(50), nullable=False)
    gateway_transaction_id: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    gateway_order_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    # Transaction details
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    status: Mapped[TransactionStatus] = mapped_column(
        SQLEnum(TransactionStatus, name="transaction_status", create_type=False),
        nullable=False,
        default=TransactionStatus.INITIATED,
    )

    # Gateway response (JSON)
    gateway_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    initiated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Relationship
    payment: Mapped["Payment"] = relationship("Payment", back_populates="transaction")

    def __repr__(self) -> str:
        return (
            f"<Transaction(id={self.id}, gateway={self.gateway_name}, "
            f"transaction_id={self.gateway_transaction_id}, "
            f"amount={self.amount}, status={self.status.value})>"
        )
