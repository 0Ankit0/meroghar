from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class AgreementStatus(str, Enum):
    DRAFT = "draft"
    PENDING_CUSTOMER_SIGNATURE = "pending_customer_signature"
    PENDING_OWNER_SIGNATURE = "pending_owner_signature"
    SIGNED = "signed"
    AMENDED = "amended"
    TERMINATED = "terminated"


class AgreementTemplate(SQLModel, table=True):
    __tablename__ = "agreement_templates"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    created_by_admin_id: int = Field(foreign_key="user.id", index=True)
    property_type_id: int = Field(foreign_key="property_types.id", index=True)
    name: str = Field(max_length=150)
    template_content: str = Field(default="", max_length=20000)
    is_active: bool = Field(default=True, index=True)
    version: int = Field(default=1)
    created_at: datetime = Field(default_factory=datetime.now, index=True)


class RentalAgreement(SQLModel, table=True):
    __tablename__ = "rental_agreements"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    booking_id: int = Field(foreign_key="bookings.id", index=True)
    template_id: int = Field(foreign_key="agreement_templates.id", index=True)
    status: AgreementStatus = Field(default=AgreementStatus.DRAFT, index=True)
    rendered_content: str = Field(default="", max_length=50000)
    custom_clauses_json: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    rendered_document_url: str | None = Field(default=None, max_length=500)
    rendered_document_sha256: str | None = Field(default=None, max_length=64)
    esign_request_id: str | None = Field(default=None, unique=True, index=True, max_length=120)
    signed_document_url: str | None = Field(default=None, max_length=500)
    signed_document_sha256: str | None = Field(default=None, max_length=64)
    sent_at: datetime | None = Field(default=None)
    customer_signed_at: datetime | None = Field(default=None)
    customer_signature_ip: str | None = Field(default=None, max_length=45)
    owner_signed_at: datetime | None = Field(default=None)
    owner_signature_ip: str | None = Field(default=None, max_length=45)
    version: int = Field(default=1)
    created_at: datetime = Field(default_factory=datetime.now, index=True)


class AgreementAmendment(SQLModel, table=True):
    __tablename__ = "agreement_amendments"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    agreement_id: int = Field(foreign_key="rental_agreements.id", index=True)
    amendment_number: int = Field(default=1)
    reason: str = Field(default="", max_length=1000)
    signed_document_url: str | None = Field(default=None, max_length=500)
    status: str = Field(default="draft", max_length=50)
    created_at: datetime = Field(default_factory=datetime.now, index=True)
    signed_at: datetime | None = Field(default=None)
