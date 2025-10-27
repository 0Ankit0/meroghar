"""Bill models for utility bill management and division.

Implements T075-T077 from tasks.md.
"""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Numeric,
    String,
    Text,
    Date,
    Integer,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.database import Base


class BillType(str, Enum):
    """Bill type options."""

    ELECTRICITY = "electricity"
    WATER = "water"
    GAS = "gas"
    INTERNET = "internet"
    MAINTENANCE = "maintenance"
    GARBAGE = "garbage"
    OTHER = "other"


class BillStatus(str, Enum):
    """Bill payment status."""

    PENDING = "pending"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    OVERDUE = "overdue"


class AllocationMethod(str, Enum):
    """Method for dividing bill among tenants."""

    EQUAL = "equal"
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"
    CUSTOM = "custom"


class RecurringFrequency(str, Enum):
    """Frequency for recurring bills."""

    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class Bill(Base):
    """Model for utility bills and other expenses.
    
    Implements T075 from tasks.md.
    """

    __tablename__ = "bills"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    property_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("properties.id"), nullable=False, index=True
    )
    bill_type: Mapped[BillType] = mapped_column(
        SQLEnum(BillType, name="bill_type"), nullable=False
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    status: Mapped[BillStatus] = mapped_column(
        SQLEnum(BillStatus, name="bill_status"), 
        nullable=False, 
        default=BillStatus.PENDING,
        index=True
    )
    allocation_method: Mapped[AllocationMethod] = mapped_column(
        SQLEnum(AllocationMethod, name="allocation_method"), 
        nullable=False,
        default=AllocationMethod.EQUAL
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    bill_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    paid_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    property: Mapped["Property"] = relationship("Property", back_populates="bills")
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])
    allocations: Mapped[list["BillAllocation"]] = relationship(
        "BillAllocation", back_populates="bill", cascade="all, delete-orphan"
    )


class BillAllocation(Base):
    """Model for bill allocation to individual tenants.
    
    Implements T076 from tasks.md.
    """

    __tablename__ = "bill_allocations"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    bill_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("bills.id"), nullable=False, index=True
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    allocated_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    percentage: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    is_paid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    paid_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    payment_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("payments.id"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    bill: Mapped["Bill"] = relationship("Bill", back_populates="allocations")
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="bill_allocations")
    payment: Mapped["Payment | None"] = relationship("Payment")


class RecurringBill(Base):
    """Model for recurring bill templates and schedules.
    
    Implements T077 from tasks.md.
    """

    __tablename__ = "recurring_bills"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    property_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("properties.id"), nullable=False, index=True
    )
    bill_type: Mapped[BillType] = mapped_column(
        SQLEnum(BillType, name="bill_type"), nullable=False
    )
    frequency: Mapped[RecurringFrequency] = mapped_column(
        SQLEnum(RecurringFrequency, name="recurring_frequency"), nullable=False
    )
    allocation_method: Mapped[AllocationMethod] = mapped_column(
        SQLEnum(AllocationMethod, name="allocation_method"), nullable=False
    )
    estimated_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    day_of_month: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_generated: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_generation: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    property: Mapped["Property"] = relationship("Property", back_populates="recurring_bills")
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])
