from __future__ import annotations

from datetime import datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_serializer, field_validator, model_validator

from src.apps.bookings.models.agreement import AgreementStatus
from src.apps.bookings.models.booking import BookingStatus, SecurityDepositStatus
from src.apps.iam.utils.hashid import decode_id, encode_id


class BookingPropertySummaryRead(BaseModel):
    id: int
    name: str
    location_address: str

    @field_serializer("id")
    def serialize_id(self, value: int) -> str:
        return encode_id(value)


class BookingPricingRead(BaseModel):
    currency: str
    base_fee: float
    peak_surcharge: float
    tax_amount: float
    total_fee: float
    deposit_amount: float
    total_due_now: float


class CancellationPolicyRead(BaseModel):
    name: str
    free_cancellation_hours: int
    partial_refund_hours: int
    partial_refund_percent: float


class SecurityDepositRead(BaseModel):
    id: int
    booking_id: int
    amount: float
    status: SecurityDepositStatus
    gateway_ref: str
    deduction_total: float
    refund_amount: float
    collected_at: datetime | None
    settled_at: datetime | None

    @field_serializer("id", "booking_id")
    def serialize_ids(self, value: int) -> str:
        return encode_id(value)


class BookingRead(BaseModel):
    id: int
    booking_number: str
    status: BookingStatus
    property: BookingPropertySummaryRead
    tenant_user_id: int
    owner_user_id: int
    rental_start_at: datetime
    rental_end_at: datetime
    actual_return_at: datetime | None = None
    special_requests: str
    pricing: BookingPricingRead
    security_deposit: SecurityDepositRead | None = None
    cancellation_policy: CancellationPolicyRead
    decline_reason: str
    cancellation_reason: str
    cancelled_at: datetime | None = None
    confirmed_at: datetime | None = None
    declined_at: datetime | None = None
    refund_amount: float
    agreement_status: AgreementStatus | None = None
    created_at: datetime
    updated_at: datetime

    @field_serializer("id", "tenant_user_id", "owner_user_id")
    def serialize_ids(self, value: int) -> str:
        return encode_id(value)


class BookingListRead(BaseModel):
    items: list[BookingRead]
    total: int
    page: int
    per_page: int
    has_more: bool


class BookingEventRead(BaseModel):
    id: int
    booking_id: int
    event_type: str
    message: str
    actor_user_id: int | None = None
    metadata_json: dict[str, object] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("id", "booking_id", "actor_user_id")
    def serialize_ids(self, value: int | None) -> str | None:
        if value is None:
            return None
        return encode_id(value)


class BookingCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    property_id: int = Field(validation_alias=AliasChoices("property_id", "propertyId"))
    rental_start_at: datetime = Field(validation_alias=AliasChoices("rental_start_at", "rentalStartAt"))
    rental_end_at: datetime = Field(validation_alias=AliasChoices("rental_end_at", "rentalEndAt"))
    special_requests: str = Field(default="", validation_alias=AliasChoices("special_requests", "specialRequests"))
    payment_method_id: str = Field(
        min_length=1,
        validation_alias=AliasChoices("payment_method_id", "paymentMethodId"),
    )
    quoted_total_fee: float | None = Field(
        default=None,
        validation_alias=AliasChoices("quoted_total_fee", "quotedTotalFee"),
    )
    quoted_deposit_amount: float | None = Field(
        default=None,
        validation_alias=AliasChoices("quoted_deposit_amount", "quotedDepositAmount"),
    )
    quoted_currency: str | None = Field(
        default=None,
        validation_alias=AliasChoices("quoted_currency", "quotedCurrency"),
    )

    @field_validator("property_id", mode="before")
    @classmethod
    def decode_property_id(cls, value: int | str) -> int:
        if isinstance(value, str):
            decoded = decode_id(value)
            if decoded is None:
                raise ValueError("Invalid property_id")
            return decoded
        return value

    @model_validator(mode="after")
    def validate_window(self) -> "BookingCreate":
        if self.rental_end_at <= self.rental_start_at:
            raise ValueError("rental_end_at must be after rental_start_at")
        return self


class BookingUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    rental_start_at: datetime | None = Field(
        default=None,
        validation_alias=AliasChoices("rental_start_at", "rentalStartAt"),
    )
    rental_end_at: datetime | None = Field(
        default=None,
        validation_alias=AliasChoices("rental_end_at", "rentalEndAt"),
    )
    special_requests: str | None = Field(
        default=None,
        validation_alias=AliasChoices("special_requests", "specialRequests"),
    )
    quoted_total_fee: float | None = Field(
        default=None,
        validation_alias=AliasChoices("quoted_total_fee", "quotedTotalFee"),
    )
    quoted_deposit_amount: float | None = Field(
        default=None,
        validation_alias=AliasChoices("quoted_deposit_amount", "quotedDepositAmount"),
    )
    quoted_currency: str | None = Field(
        default=None,
        validation_alias=AliasChoices("quoted_currency", "quotedCurrency"),
    )

    @model_validator(mode="after")
    def validate_window(self) -> "BookingUpdate":
        if self.rental_start_at is not None and self.rental_end_at is not None:
            if self.rental_end_at <= self.rental_start_at:
                raise ValueError("rental_end_at must be after rental_start_at")
        return self


class BookingDeclineRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    reason: str = Field(min_length=1)


class BookingCancelRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    reason: str = Field(min_length=1)


class BookingReturnRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    actual_return_at: datetime | None = Field(
        default=None,
        validation_alias=AliasChoices("actual_return_at", "actualReturnAt"),
    )
    notes: str = ""
