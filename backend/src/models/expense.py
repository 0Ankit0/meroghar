"""Expense models for maintenance and operational expense tracking.

Implements T125 from tasks.md.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.database import Base


class ExpenseCategory(str, Enum):
    """Expense category options."""

    MAINTENANCE = "maintenance"
    REPAIR = "repair"
    CLEANING = "cleaning"
    LANDSCAPING = "landscaping"
    SECURITY = "security"
    UTILITIES = "utilities"
    INSURANCE = "insurance"
    TAXES = "taxes"
    LEGAL = "legal"
    ADMINISTRATIVE = "administrative"
    OTHER = "other"


class ExpenseStatus(str, Enum):
    """Expense approval status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REIMBURSED = "reimbursed"


class Expense(Base):
    """Maintenance and operational expense records.

    Tracks expenses incurred by intermediaries for property maintenance,
    repairs, and other operational costs requiring owner reimbursement.
    """

    __tablename__ = "expenses"

    # Primary key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign keys
    property_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("properties.id", ondelete="CASCADE"), nullable=False
    )
    recorded_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    approved_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Expense details
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="NPR")
    category: Mapped[ExpenseCategory] = mapped_column(
        SQLEnum(ExpenseCategory, name="expense_category", create_type=False),
        nullable=False,
    )
    status: Mapped[ExpenseStatus] = mapped_column(
        SQLEnum(ExpenseStatus, name="expense_status", create_type=False),
        nullable=False,
        default=ExpenseStatus.PENDING,
    )

    # Description and documentation
    description: Mapped[str] = mapped_column(Text, nullable=False)
    vendor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    invoice_number: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Receipt/document URLs (stored in S3 or local storage)
    receipt_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Who paid for this expense
    paid_by: Mapped[str] = mapped_column(
        String(100), nullable=False, default="intermediary"
    )  # "intermediary", "owner", "tenant", "property_account"

    # Reimbursement tracking
    is_reimbursable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_reimbursed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reimbursed_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Timestamps
    expense_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    approved_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    property: Mapped["Property"] = relationship("Property", back_populates="expenses")
    recorder: Mapped["User"] = relationship(
        "User", foreign_keys=[recorded_by], back_populates="recorded_expenses"
    )
    approver: Mapped["User"] = relationship(
        "User", foreign_keys=[approved_by], back_populates="approved_expenses"
    )

    def __repr__(self) -> str:
        return (
            f"<Expense(id={self.id}, property_id={self.property_id}, "
            f"amount={self.amount}, category={self.category.value}, "
            f"status={self.status.value})>"
        )
