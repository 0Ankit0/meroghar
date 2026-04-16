from __future__ import annotations

from datetime import date, datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_serializer, field_validator

from src.apps.iam.utils.hashid import decode_id, encode_id
from src.apps.utility_billing.models.utility_bill import (
    UtilityBillDisputeStatus,
    UtilityBillSplitMethod,
    UtilityBillSplitStatus,
    UtilityBillStatus,
    UtilityBillType,
)


class UtilityBillAttachmentRead(BaseModel):
    id: int
    utility_bill_id: int
    file_url: str
    file_type: str
    checksum: str
    uploaded_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("id", "utility_bill_id")
    def serialize_ids(self, value: int) -> str:
        return encode_id(value)


class UtilityBillSplitRead(BaseModel):
    id: int
    utility_bill_id: int
    tenant_user_id: int
    invoice_id: int | None = None
    split_method: UtilityBillSplitMethod
    split_percent: float | None = None
    assigned_amount: float
    paid_amount: float
    outstanding_amount: float
    status: UtilityBillSplitStatus
    due_at: datetime | None = None
    paid_at: datetime | None = None

    model_config = {"from_attributes": True}

    @field_serializer("id", "utility_bill_id", "tenant_user_id", "invoice_id")
    def serialize_ids(self, value: int | None) -> str | None:
        if value is None:
            return None
        return encode_id(value)


class UtilityBillDisputeRead(BaseModel):
    id: int
    utility_bill_split_id: int
    opened_by_user_id: int
    status: UtilityBillDisputeStatus
    reason: str
    resolution_notes: str
    opened_at: datetime
    resolved_at: datetime | None = None

    model_config = {"from_attributes": True}

    @field_serializer("id", "utility_bill_split_id", "opened_by_user_id")
    def serialize_ids(self, value: int) -> str:
        return encode_id(value)


class UtilityBillRead(BaseModel):
    id: int
    property_id: int
    created_by_user_id: int
    bill_type: UtilityBillType
    billing_period_label: str
    period_start: date
    period_end: date
    due_date: date
    total_amount: float
    owner_subsidy_amount: float
    payable_amount: float
    status: UtilityBillStatus
    notes: str
    attachments: list[UtilityBillAttachmentRead] = []
    splits: list[UtilityBillSplitRead] = []
    created_at: datetime
    published_at: datetime | None = None

    @field_serializer("id", "property_id", "created_by_user_id")
    def serialize_ids(self, value: int) -> str:
        return encode_id(value)


class UtilityBillListRead(BaseModel):
    items: list[UtilityBillRead]
    total: int
    page: int
    per_page: int
    has_more: bool


class UtilityBillShareRead(BaseModel):
    split: UtilityBillSplitRead
    bill: UtilityBillRead
    disputes: list[UtilityBillDisputeRead] = []


class UtilityBillShareListRead(BaseModel):
    items: list[UtilityBillShareRead]
    total: int


class UtilityBillCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    bill_type: UtilityBillType = Field(validation_alias=AliasChoices("bill_type", "billType"))
    billing_period_label: str = Field(validation_alias=AliasChoices("billing_period_label", "billingPeriodLabel"))
    period_start: date = Field(validation_alias=AliasChoices("period_start", "periodStart"))
    period_end: date = Field(validation_alias=AliasChoices("period_end", "periodEnd"))
    due_date: date = Field(validation_alias=AliasChoices("due_date", "dueDate"))
    total_amount: float = Field(validation_alias=AliasChoices("total_amount", "totalAmount"))
    owner_subsidy_amount: float = Field(
        default=0.0,
        validation_alias=AliasChoices("owner_subsidy_amount", "ownerSubsidyAmount"),
    )
    notes: str = ""


class UtilityBillSplitInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    tenant_user_id: int = Field(validation_alias=AliasChoices("tenant_user_id", "tenantUserId"))
    split_method: UtilityBillSplitMethod = Field(validation_alias=AliasChoices("split_method", "splitMethod"))
    split_percent: float | None = Field(default=None, validation_alias=AliasChoices("split_percent", "splitPercent"))
    assigned_amount: float | None = Field(default=None, validation_alias=AliasChoices("assigned_amount", "assignedAmount"))

    @field_validator("tenant_user_id", mode="before")
    @classmethod
    def decode_tenant_user_id(cls, value: int | str) -> int:
        if isinstance(value, str):
            decoded = decode_id(value)
            if decoded is None:
                raise ValueError("Invalid tenant_user_id")
            return decoded
        return value


class UtilityBillSplitConfigureRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    default_method: UtilityBillSplitMethod | None = Field(
        default=None,
        validation_alias=AliasChoices("default_method", "defaultMethod"),
    )
    splits: list[UtilityBillSplitInput] = Field(default_factory=list)


class UtilityBillDisputeRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    reason: str


class UtilityBillDisputeResolveRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    outcome: UtilityBillDisputeStatus
    resolution_notes: str = Field(default="", validation_alias=AliasChoices("resolution_notes", "resolutionNotes"))


class UtilityBillHistoryEntryRead(BaseModel):
    event_type: str
    message: str
    occurred_at: datetime
    metadata_json: dict[str, object] | None = None


class UtilityBillHistoryRead(BaseModel):
    bill_id: int
    entries: list[UtilityBillHistoryEntryRead]

    @field_serializer("bill_id")
    def serialize_bill_id(self, value: int) -> str:
        return encode_id(value)
