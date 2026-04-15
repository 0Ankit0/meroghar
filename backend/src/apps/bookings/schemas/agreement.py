from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_serializer, field_validator

from src.apps.bookings.models.agreement import AgreementStatus
from src.apps.iam.utils.hashid import decode_id, encode_id


class AgreementTemplateSummaryRead(BaseModel):
    id: int
    property_type_id: int
    name: str
    version: int

    @field_serializer("id", "property_type_id")
    def serialize_ids(self, value: int) -> str:
        return encode_id(value)


class RentalAgreementRead(BaseModel):
    id: int
    booking_id: int
    template: AgreementTemplateSummaryRead
    status: AgreementStatus
    rendered_content: str
    custom_clauses: list[str] = []
    rendered_document_url: str | None = None
    rendered_document_sha256: str | None = None
    esign_request_id: str | None = None
    signed_document_url: str | None = None
    signed_document_sha256: str | None = None
    sent_at: datetime | None = None
    customer_signed_at: datetime | None = None
    customer_signature_ip: str | None = None
    owner_signed_at: datetime | None = None
    owner_signature_ip: str | None = None
    version: int
    created_at: datetime

    @field_serializer("id", "booking_id")
    def serialize_ids(self, value: int) -> str:
        return encode_id(value)


class AgreementGenerateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    template_id: int | None = Field(default=None, validation_alias=AliasChoices("template_id", "templateId"))
    custom_clauses: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("custom_clauses", "customClauses"),
    )

    @field_validator("template_id", mode="before")
    @classmethod
    def decode_template_id(cls, value: int | str | None) -> int | None:
        if isinstance(value, str):
            decoded = decode_id(value)
            if decoded is None:
                raise ValueError("Invalid template_id")
            return decoded
        return value


class EsignWebhookEventType(str, Enum):
    CUSTOMER_SIGNED = "customer.signed"


class EsignWebhookRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    esign_request_id: str = Field(validation_alias=AliasChoices("esign_request_id", "esignRequestId"))
    event_type: EsignWebhookEventType = Field(validation_alias=AliasChoices("event_type", "eventType"))
    signed_at: datetime | None = Field(default=None, validation_alias=AliasChoices("signed_at", "signedAt"))
    ip_address: str | None = Field(default=None, validation_alias=AliasChoices("ip_address", "ipAddress"))


class EsignWebhookResponse(BaseModel):
    status: str
    agreement: RentalAgreementRead
