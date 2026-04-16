from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from sqlmodel import Field, SQLModel


class UtilityBillType(str, Enum):
    ELECTRICITY = "electricity"
    WATER = "water"
    INTERNET = "internet"
    GAS = "gas"
    OTHER = "other"


class UtilityBillStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    PARTIALLY_PAID = "partially_paid"
    SETTLED = "settled"


class UtilityBillSplitMethod(str, Enum):
    SINGLE = "single"
    EQUAL = "equal"
    PERCENTAGE = "percentage"
    FIXED = "fixed"


class UtilityBillSplitStatus(str, Enum):
    PENDING = "pending"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    DISPUTED = "disputed"
    WAIVED = "waived"


class UtilityBillDisputeStatus(str, Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    REJECTED = "rejected"
    WAIVED = "waived"


class UtilityBill(SQLModel, table=True):
    __tablename__ = "utility_bills"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    property_id: int = Field(foreign_key="properties.id", index=True)
    created_by_user_id: int = Field(foreign_key="user.id", index=True)
    bill_type: UtilityBillType = Field(default=UtilityBillType.ELECTRICITY, index=True)
    billing_period_label: str = Field(default="", max_length=120)
    period_start: date
    period_end: date
    due_date: date
    total_amount: float = Field(default=0.0)
    owner_subsidy_amount: float = Field(default=0.0)
    status: UtilityBillStatus = Field(default=UtilityBillStatus.DRAFT, index=True)
    notes: str = Field(default="", max_length=2000)
    created_at: datetime = Field(default_factory=datetime.now, index=True)
    published_at: datetime | None = Field(default=None)


class UtilityBillAttachment(SQLModel, table=True):
    __tablename__ = "utility_bill_attachments"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    utility_bill_id: int = Field(foreign_key="utility_bills.id", index=True)
    file_url: str = Field(default="", max_length=500)
    file_type: str = Field(default="", max_length=120)
    checksum: str = Field(default="", max_length=64)
    uploaded_at: datetime = Field(default_factory=datetime.now, index=True)


class UtilityBillSplit(SQLModel, table=True):
    __tablename__ = "utility_bill_splits"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    utility_bill_id: int = Field(foreign_key="utility_bills.id", index=True)
    tenant_user_id: int = Field(foreign_key="user.id", index=True)
    invoice_id: int | None = Field(default=None, foreign_key="invoices.id", unique=True, index=True)
    split_method: UtilityBillSplitMethod = Field(default=UtilityBillSplitMethod.EQUAL, index=True)
    split_percent: float | None = Field(default=None)
    assigned_amount: float = Field(default=0.0)
    paid_amount: float = Field(default=0.0)
    status: UtilityBillSplitStatus = Field(default=UtilityBillSplitStatus.PENDING, index=True)
    due_at: datetime | None = Field(default=None)
    paid_at: datetime | None = Field(default=None)


class UtilityBillDispute(SQLModel, table=True):
    __tablename__ = "utility_bill_disputes"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    utility_bill_split_id: int = Field(foreign_key="utility_bill_splits.id", index=True)
    opened_by_user_id: int = Field(foreign_key="user.id", index=True)
    status: UtilityBillDisputeStatus = Field(default=UtilityBillDisputeStatus.OPEN, index=True)
    reason: str = Field(default="", max_length=1000)
    resolution_notes: str = Field(default="", max_length=1000)
    opened_at: datetime = Field(default_factory=datetime.now, index=True)
    resolved_at: datetime | None = Field(default=None)
