from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from sqlalchemy import Column, JSON, UniqueConstraint
from sqlmodel import Field, SQLModel

from src.apps.finance.models.payment import PaymentProvider, PaymentStatus


class InvoiceType(str, Enum):
    RENT = "rent"
    ADDITIONAL_CHARGE = "additional_charge"
    UTILITY_BILL_SHARE = "utility_bill_share"


class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    OVERDUE = "overdue"
    WAIVED = "waived"


class InvoiceReminderType(str, Enum):
    T_MINUS_7 = "t_minus_7"
    T_MINUS_3 = "t_minus_3"
    T_MINUS_1 = "t_minus_1"
    OVERDUE = "overdue"


class InvoiceReminderStatus(str, Enum):
    SCHEDULED = "scheduled"
    SENT = "sent"
    SKIPPED = "skipped"


class PaymentReferenceType(str, Enum):
    INVOICE = "invoice"
    SECURITY_DEPOSIT = "security_deposit"


class RefundStatus(str, Enum):
    INITIATED = "initiated"
    COMPLETED = "completed"
    FAILED = "failed"


class AdditionalChargeStatus(str, Enum):
    RAISED = "raised"
    ACCEPTED = "accepted"
    DISPUTED = "disputed"
    PARTIALLY_ACCEPTED = "partially_accepted"
    PAID = "paid"
    WAIVED = "waived"


class Invoice(SQLModel, table=True):
    __tablename__ = "invoices"  # type: ignore
    __table_args__ = (UniqueConstraint("invoice_number", name="uq_invoices_invoice_number"),)

    id: int | None = Field(default=None, primary_key=True)
    invoice_number: str = Field(default="", max_length=40, unique=True, index=True)
    booking_id: int | None = Field(default=None, foreign_key="bookings.id", index=True)
    tenant_user_id: int = Field(foreign_key="user.id", index=True)
    owner_user_id: int = Field(foreign_key="user.id", index=True)
    invoice_type: InvoiceType = Field(default=InvoiceType.RENT, index=True)
    currency: str = Field(default="NPR", max_length=3)
    subtotal: float = Field(default=0.0)
    tax_amount: float = Field(default=0.0)
    total_amount: float = Field(default=0.0)
    paid_amount: float = Field(default=0.0)
    status: InvoiceStatus = Field(default=InvoiceStatus.DRAFT, index=True)
    due_date: date = Field(index=True)
    period_start: date | None = Field(default=None)
    period_end: date | None = Field(default=None)
    metadata_json: dict[str, object] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    created_at: datetime = Field(default_factory=datetime.now, index=True)
    paid_at: datetime | None = Field(default=None)


class InvoiceLineItem(SQLModel, table=True):
    __tablename__ = "invoice_line_items"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    invoice_id: int = Field(foreign_key="invoices.id", index=True)
    line_item_type: str = Field(default="rent", max_length=80)
    description: str = Field(default="", max_length=500)
    amount: float = Field(default=0.0)
    tax_rate: float = Field(default=0.0)
    tax_amount: float = Field(default=0.0)
    metadata_json: dict[str, object] | None = Field(default=None, sa_column=Column(JSON, nullable=True))


class InvoiceReminder(SQLModel, table=True):
    __tablename__ = "invoice_reminders"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    invoice_id: int = Field(foreign_key="invoices.id", index=True)
    reminder_type: InvoiceReminderType = Field(default=InvoiceReminderType.T_MINUS_7, index=True)
    scheduled_for: datetime = Field(index=True)
    sent_at: datetime | None = Field(default=None)
    status: InvoiceReminderStatus = Field(default=InvoiceReminderStatus.SCHEDULED, index=True)
    channel_status_json: dict[str, object] | None = Field(default=None, sa_column=Column(JSON, nullable=True))


class Payment(SQLModel, table=True):
    __tablename__ = "payments"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    reference_type: PaymentReferenceType = Field(default=PaymentReferenceType.INVOICE, index=True)
    reference_id: int = Field(index=True)
    payer_user_id: int = Field(foreign_key="user.id", index=True)
    payment_method: PaymentProvider = Field(default=PaymentProvider.KHALTI, index=True)
    status: PaymentStatus = Field(default=PaymentStatus.PENDING, index=True)
    amount: float = Field(default=0.0)
    currency: str = Field(default="NPR", max_length=3)
    gateway_ref: str = Field(default="", max_length=255, index=True)
    gateway_response_json: dict[str, object] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    is_offline: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now, index=True)
    confirmed_at: datetime | None = Field(default=None)


class Refund(SQLModel, table=True):
    __tablename__ = "refunds"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    payment_id: int = Field(foreign_key="payments.id", index=True)
    gateway_ref: str = Field(default="", max_length=255)
    amount: float = Field(default=0.0)
    status: RefundStatus = Field(default=RefundStatus.INITIATED, index=True)
    reason: str = Field(default="", max_length=500)
    initiated_at: datetime = Field(default_factory=datetime.now, index=True)
    completed_at: datetime | None = Field(default=None)


class AdditionalCharge(SQLModel, table=True):
    __tablename__ = "additional_charges"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    booking_id: int = Field(foreign_key="bookings.id", index=True)
    invoice_id: int | None = Field(default=None, foreign_key="invoices.id", unique=True, index=True)
    charge_type: str = Field(default="damage", max_length=80)
    description: str = Field(default="", max_length=500)
    amount: float = Field(default=0.0)
    resolved_amount: float | None = Field(default=None)
    evidence_url: str = Field(default="", max_length=500)
    status: AdditionalChargeStatus = Field(default=AdditionalChargeStatus.RAISED, index=True)
    dispute_reason: str = Field(default="", max_length=1000)
    resolution_notes: str = Field(default="", max_length=1000)
    created_at: datetime = Field(default_factory=datetime.now, index=True)
    resolved_at: datetime | None = Field(default=None)
