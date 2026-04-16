from __future__ import annotations

from datetime import date, datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_serializer

from src.apps.finance.models.payment import PaymentProvider, PaymentStatus
from src.apps.iam.utils.hashid import encode_id
from src.apps.invoicing.models.invoice import (
    AdditionalChargeStatus,
    InvoiceReminderStatus,
    InvoiceReminderType,
    InvoiceStatus,
    InvoiceType,
    PaymentReferenceType,
)


class InvoiceLineItemRead(BaseModel):
    id: int
    invoice_id: int
    line_item_type: str
    description: str
    amount: float
    tax_rate: float
    tax_amount: float
    metadata_json: dict[str, object] | None = None

    model_config = {"from_attributes": True}

    @field_serializer("id", "invoice_id")
    def serialize_ids(self, value: int) -> str:
        return encode_id(value)


class InvoiceReminderRead(BaseModel):
    id: int
    invoice_id: int
    reminder_type: InvoiceReminderType
    scheduled_for: datetime
    sent_at: datetime | None = None
    status: InvoiceReminderStatus
    channel_status_json: dict[str, object] | None = None

    model_config = {"from_attributes": True}

    @field_serializer("id", "invoice_id")
    def serialize_ids(self, value: int) -> str:
        return encode_id(value)


class PaymentRead(BaseModel):
    id: int
    reference_type: PaymentReferenceType
    reference_id: int
    payer_user_id: int
    payment_method: PaymentProvider
    status: PaymentStatus
    amount: float
    currency: str
    gateway_ref: str
    gateway_response_json: dict[str, object] | None = None
    is_offline: bool
    created_at: datetime
    confirmed_at: datetime | None = None

    model_config = {"from_attributes": True}

    @field_serializer("id", "reference_id", "payer_user_id")
    def serialize_ids(self, value: int) -> str:
        return encode_id(value)


class InvoiceRead(BaseModel):
    id: int
    invoice_number: str
    booking_id: int | None = None
    tenant_user_id: int
    owner_user_id: int
    invoice_type: InvoiceType
    currency: str
    subtotal: float
    tax_amount: float
    total_amount: float
    paid_amount: float
    outstanding_amount: float
    status: InvoiceStatus
    due_date: date
    period_start: date | None = None
    period_end: date | None = None
    metadata_json: dict[str, object] | None = None
    line_items: list[InvoiceLineItemRead] = []
    reminders: list[InvoiceReminderRead] = []
    payments: list[PaymentRead] = []
    created_at: datetime
    paid_at: datetime | None = None

    @field_serializer("id", "tenant_user_id", "owner_user_id")
    def serialize_ids(self, value: int) -> str:
        return encode_id(value)

    @field_serializer("booking_id")
    def serialize_booking_id(self, value: int | None) -> str | None:
        if value is None:
            return None
        return encode_id(value)


class InvoiceListRead(BaseModel):
    items: list[InvoiceRead]
    total: int
    page: int
    per_page: int
    has_more: bool


class InvoicePaymentRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    provider: PaymentProvider
    amount: float | None = None
    return_url: str = Field(validation_alias=AliasChoices("return_url", "returnUrl"))
    website_url: str = Field(default="", validation_alias=AliasChoices("website_url", "websiteUrl"))
    customer_name: str | None = Field(default=None, validation_alias=AliasChoices("customer_name", "customerName"))
    customer_email: str | None = Field(default=None, validation_alias=AliasChoices("customer_email", "customerEmail"))
    customer_phone: str | None = Field(default=None, validation_alias=AliasChoices("customer_phone", "customerPhone"))


class AdditionalChargeRead(BaseModel):
    id: int
    booking_id: int
    invoice_id: int | None = None
    charge_type: str
    description: str
    amount: float
    resolved_amount: float | None = None
    evidence_url: str
    status: AdditionalChargeStatus
    dispute_reason: str
    resolution_notes: str
    created_at: datetime
    resolved_at: datetime | None = None

    @field_serializer("id", "booking_id", "invoice_id")
    def serialize_ids(self, value: int | None) -> str | None:
        if value is None:
            return None
        return encode_id(value)


class AdditionalChargeCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    charge_type: str = Field(default="damage", validation_alias=AliasChoices("charge_type", "chargeType"))
    description: str
    amount: float
    evidence_url: str = Field(default="", validation_alias=AliasChoices("evidence_url", "evidenceUrl"))


class AdditionalChargeDisputeRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    reason: str


class AdditionalChargeResolveRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    outcome: AdditionalChargeStatus
    resolved_amount: float | None = Field(default=None, validation_alias=AliasChoices("resolved_amount", "resolvedAmount"))
    resolution_notes: str = Field(default="", validation_alias=AliasChoices("resolution_notes", "resolutionNotes"))


class RentLedgerEntryRead(BaseModel):
    period_start: date
    period_end: date
    amount_due: float
    invoice_id: int | None = None
    invoice_status: InvoiceStatus | None = None
    due_date: date | None = None
    paid_amount: float = 0.0
    outstanding_amount: float = 0.0

    @field_serializer("invoice_id")
    def serialize_invoice_id(self, value: int | None) -> str | None:
        if value is None:
            return None
        return encode_id(value)


class RentLedgerRead(BaseModel):
    booking_id: int
    currency: str
    entries: list[RentLedgerEntryRead]
    additional_charges: list[AdditionalChargeRead] = []
    total_amount: float
    paid_amount: float
    outstanding_amount: float

    @field_serializer("booking_id")
    def serialize_booking_id(self, value: int) -> str:
        return encode_id(value)
