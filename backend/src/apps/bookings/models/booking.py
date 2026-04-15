from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import Column, JSON, UniqueConstraint
from sqlmodel import Field, SQLModel


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    DECLINED = "declined"
    CANCELLED = "cancelled"
    ACTIVE = "active"
    PENDING_CLOSURE = "pending_closure"
    CLOSED = "closed"


class SecurityDepositStatus(str, Enum):
    HELD = "held"
    FULLY_REFUNDED = "fully_refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    FULLY_DEDUCTED = "fully_deducted"
    DISPUTED = "disputed"


class Booking(SQLModel, table=True):
    __tablename__ = "bookings"  # type: ignore
    __table_args__ = (
        UniqueConstraint("booking_number", name="uq_bookings_booking_number"),
        UniqueConstraint("tenant_user_id", "idempotency_key", name="uq_bookings_tenant_idempotency_key"),
    )

    id: int | None = Field(default=None, primary_key=True)
    booking_number: str = Field(default="", max_length=32, unique=True, index=True)
    property_id: int = Field(foreign_key="properties.id", index=True)
    tenant_user_id: int = Field(foreign_key="user.id", index=True)
    owner_user_id: int = Field(foreign_key="user.id", index=True)
    status: BookingStatus = Field(default=BookingStatus.PENDING, index=True)
    rental_start_at: datetime = Field(index=True)
    rental_end_at: datetime = Field(index=True)
    actual_return_at: datetime | None = Field(default=None)
    special_requests: str = Field(default="", max_length=2000)
    payment_method_id: str = Field(default="", max_length=255)
    currency: str = Field(default="NPR", max_length=3)
    base_fee: float = Field(default=0.0)
    peak_surcharge: float = Field(default=0.0)
    tax_amount: float = Field(default=0.0)
    total_fee: float = Field(default=0.0)
    deposit_amount: float = Field(default=0.0)
    decline_reason: str = Field(default="", max_length=500)
    cancellation_reason: str = Field(default="", max_length=500)
    cancelled_at: datetime | None = Field(default=None)
    confirmed_at: datetime | None = Field(default=None)
    declined_at: datetime | None = Field(default=None)
    refund_amount: float = Field(default=0.0)
    idempotency_key: str | None = Field(default=None, max_length=255, index=True)
    created_at: datetime = Field(default_factory=datetime.now, index=True)
    updated_at: datetime = Field(default_factory=datetime.now)


class BookingEvent(SQLModel, table=True):
    __tablename__ = "booking_events"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    booking_id: int = Field(foreign_key="bookings.id", index=True)
    event_type: str = Field(max_length=100, index=True)
    message: str = Field(default="", max_length=2000)
    actor_user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    metadata_json: dict[str, object] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    created_at: datetime = Field(default_factory=datetime.now, index=True)


class CancellationPolicy(SQLModel, table=True):
    __tablename__ = "cancellation_policies"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    property_id: int = Field(foreign_key="properties.id", unique=True, index=True)
    name: str = Field(max_length=120)
    free_cancellation_hours: int = Field(default=72)
    partial_refund_hours: int = Field(default=24)
    partial_refund_percent: float = Field(default=50.0)


class SecurityDeposit(SQLModel, table=True):
    __tablename__ = "security_deposits"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    booking_id: int = Field(foreign_key="bookings.id", unique=True, index=True)
    amount: float = Field(default=0.0)
    status: SecurityDepositStatus = Field(default=SecurityDepositStatus.HELD, index=True)
    gateway_ref: str = Field(default="", max_length=255)
    deduction_total: float = Field(default=0.0)
    refund_amount: float = Field(default=0.0)
    collected_at: datetime | None = Field(default=None)
    settled_at: datetime | None = Field(default=None)
