"""Bill request/response schemas.

Implements T079 from tasks.md.
"""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from ..models.bill import (AllocationMethod, BillStatus, BillType,
                           RecurringFrequency)

# ==================== Request Schemas ====================


class BillCreateRequest(BaseModel):
    """Request schema for creating a bill."""

    property_id: UUID = Field(..., description="Property for which bill is created")
    bill_type: BillType = Field(..., description="Type of bill")
    total_amount: Decimal = Field(..., gt=0, description="Total bill amount")
    currency: str = Field(default="INR", max_length=3, description="Currency code (ISO 4217)")
    period_start: date = Field(..., description="Bill period start date")
    period_end: date = Field(..., description="Bill period end date")
    due_date: date = Field(..., description="Payment due date")
    allocation_method: AllocationMethod = Field(
        default=AllocationMethod.EQUAL, description="Method to allocate bill among tenants"
    )
    description: str | None = Field(None, max_length=500, description="Bill description")
    bill_number: str | None = Field(None, max_length=100, description="Bill/invoice number")

    @field_validator("total_amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Validate bill amount is positive."""
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v

    @field_validator("period_end")
    @classmethod
    def validate_period_dates(cls, v: date, info) -> date:
        """Validate period end date is after start date."""
        if "period_start" in info.data and v <= info.data["period_start"]:
            raise ValueError("Period end must be after period start")
        return v

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, v: date, info) -> date:
        """Validate due date is after period start."""
        if "period_start" in info.data and v < info.data["period_start"]:
            raise ValueError("Due date cannot be before period start")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "property_id": "123e4567-e89b-12d3-a456-426614174001",
                "bill_type": "electricity",
                "total_amount": 5000.00,
                "currency": "INR",
                "period_start": "2025-10-01",
                "period_end": "2025-10-31",
                "due_date": "2025-11-10",
                "allocation_method": "equal",
                "description": "October 2025 electricity bill",
                "bill_number": "ELEC-2025-10-001",
            }
        }


class BillUpdateRequest(BaseModel):
    """Request schema for updating a bill."""

    status: BillStatus | None = Field(None, description="Bill status")
    total_amount: Decimal | None = Field(None, gt=0, description="Updated total amount")
    due_date: date | None = Field(None, description="Updated due date")
    description: str | None = Field(None, max_length=500, description="Updated description")
    bill_number: str | None = Field(None, max_length=100, description="Updated bill number")

    @field_validator("total_amount")
    @classmethod
    def validate_amount(cls, v: Decimal | None) -> Decimal | None:
        """Validate bill amount is positive."""
        if v is not None and v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "status": "paid",
                "total_amount": 5200.00,
                "due_date": "2025-11-15",
                "description": "October 2025 electricity bill (revised)",
                "bill_number": "ELEC-2025-10-001-REV",
            }
        }


class BillAllocationCreateRequest(BaseModel):
    """Request schema for creating a bill allocation."""

    tenant_id: UUID = Field(..., description="Tenant to allocate bill to")
    allocated_amount: Decimal = Field(..., gt=0, description="Amount allocated to tenant")
    percentage: Decimal | None = Field(
        None, ge=0, le=100, description="Percentage of total bill (0-100)"
    )
    notes: str | None = Field(None, description="Allocation notes")

    @field_validator("allocated_amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Validate allocated amount is positive."""
        if v <= 0:
            raise ValueError("Allocated amount must be greater than 0")
        return v

    @field_validator("percentage")
    @classmethod
    def validate_percentage(cls, v: Decimal | None) -> Decimal | None:
        """Validate percentage is between 0 and 100."""
        if v is not None and (v < 0 or v > 100):
            raise ValueError("Percentage must be between 0 and 100")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
                "allocated_amount": 2500.00,
                "percentage": 50.00,
                "notes": "50% share as per agreement",
            }
        }


class BillAllocationUpdateRequest(BaseModel):
    """Request schema for updating a bill allocation."""

    allocated_amount: Decimal | None = Field(None, gt=0, description="Updated allocated amount")
    percentage: Decimal | None = Field(None, ge=0, le=100, description="Updated percentage")
    is_paid: bool | None = Field(None, description="Payment status")
    payment_id: UUID | None = Field(None, description="Associated payment ID")
    notes: str | None = Field(None, description="Updated notes")

    @field_validator("allocated_amount")
    @classmethod
    def validate_amount(cls, v: Decimal | None) -> Decimal | None:
        """Validate allocated amount is positive."""
        if v is not None and v <= 0:
            raise ValueError("Allocated amount must be greater than 0")
        return v

    @field_validator("percentage")
    @classmethod
    def validate_percentage(cls, v: Decimal | None) -> Decimal | None:
        """Validate percentage is between 0 and 100."""
        if v is not None and (v < 0 or v > 100):
            raise ValueError("Percentage must be between 0 and 100")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "allocated_amount": 2600.00,
                "percentage": 52.00,
                "is_paid": True,
                "payment_id": "123e4567-e89b-12d3-a456-426614174002",
                "notes": "Paid via UPI",
            }
        }


class RecurringBillCreateRequest(BaseModel):
    """Request schema for creating a recurring bill template."""

    property_id: UUID = Field(..., description="Property for recurring bill")
    bill_type: BillType = Field(..., description="Type of bill")
    frequency: RecurringFrequency = Field(..., description="Bill recurrence frequency")
    allocation_method: AllocationMethod = Field(
        default=AllocationMethod.EQUAL, description="Method to allocate bill among tenants"
    )
    estimated_amount: Decimal = Field(..., gt=0, description="Estimated bill amount")
    currency: str = Field(default="INR", max_length=3, description="Currency code")
    day_of_month: int = Field(..., ge=1, le=31, description="Day of month to generate bill (1-31)")
    description: str | None = Field(None, max_length=500, description="Template description")
    is_active: bool = Field(default=True, description="Whether template is active")

    @field_validator("estimated_amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Validate estimated amount is positive."""
        if v <= 0:
            raise ValueError("Estimated amount must be greater than 0")
        return v

    @field_validator("day_of_month")
    @classmethod
    def validate_day(cls, v: int) -> int:
        """Validate day of month."""
        if v < 1 or v > 31:
            raise ValueError("Day of month must be between 1 and 31")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "property_id": "123e4567-e89b-12d3-a456-426614174001",
                "bill_type": "electricity",
                "frequency": "monthly",
                "allocation_method": "equal",
                "estimated_amount": 5000.00,
                "currency": "INR",
                "day_of_month": 1,
                "description": "Monthly electricity bill template",
                "is_active": True,
            }
        }


class RecurringBillUpdateRequest(BaseModel):
    """Request schema for updating a recurring bill template."""

    estimated_amount: Decimal | None = Field(None, gt=0, description="Updated estimated amount")
    day_of_month: int | None = Field(None, ge=1, le=31, description="Updated day of month")
    description: str | None = Field(None, max_length=500, description="Updated description")
    is_active: bool | None = Field(None, description="Active status")

    @field_validator("estimated_amount")
    @classmethod
    def validate_amount(cls, v: Decimal | None) -> Decimal | None:
        """Validate estimated amount is positive."""
        if v is not None and v <= 0:
            raise ValueError("Estimated amount must be greater than 0")
        return v

    @field_validator("day_of_month")
    @classmethod
    def validate_day(cls, v: int | None) -> int | None:
        """Validate day of month."""
        if v is not None and (v < 1 or v > 31):
            raise ValueError("Day of month must be between 1 and 31")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "estimated_amount": 5500.00,
                "day_of_month": 5,
                "description": "Monthly electricity bill template (revised estimate)",
                "is_active": True,
            }
        }


# ==================== Response Schemas ====================


class BillAllocationResponse(BaseModel):
    """Response schema for bill allocation details."""

    id: UUID
    bill_id: UUID
    tenant_id: UUID
    allocated_amount: Decimal
    percentage: Decimal | None
    is_paid: bool
    paid_date: date | None
    payment_id: UUID | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174005",
                "bill_id": "123e4567-e89b-12d3-a456-426614174003",
                "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
                "allocated_amount": 2500.00,
                "percentage": 50.00,
                "is_paid": True,
                "paid_date": "2025-11-08",
                "payment_id": "123e4567-e89b-12d3-a456-426614174002",
                "notes": "50% share as per agreement",
                "created_at": "2025-11-01T09:00:00Z",
                "updated_at": "2025-11-08T10:30:00Z",
            }
        }


class BillResponse(BaseModel):
    """Response schema for bill details."""

    id: UUID
    property_id: UUID
    bill_type: BillType
    total_amount: Decimal
    currency: str
    period_start: date
    period_end: date
    due_date: date
    status: BillStatus
    allocation_method: AllocationMethod
    description: str | None
    bill_number: str | None
    paid_date: date | None
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime
    allocations: list[BillAllocationResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174003",
                "property_id": "123e4567-e89b-12d3-a456-426614174001",
                "bill_type": "electricity",
                "total_amount": 5000.00,
                "currency": "INR",
                "period_start": "2025-10-01",
                "period_end": "2025-10-31",
                "due_date": "2025-11-10",
                "status": "paid",
                "allocation_method": "equal",
                "description": "October 2025 electricity bill",
                "bill_number": "ELEC-2025-10-001",
                "paid_date": "2025-11-08",
                "created_by": "123e4567-e89b-12d3-a456-426614174004",
                "created_at": "2025-11-01T09:00:00Z",
                "updated_at": "2025-11-08T10:30:00Z",
                "allocations": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174005",
                        "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
                        "allocated_amount": 2500.00,
                        "percentage": 50.00,
                        "is_paid": True,
                    }
                ],
            }
        }


class BillListResponse(BaseModel):
    """Response schema for bill list."""

    bills: list[BillResponse]
    total: int
    skip: int
    limit: int

    class Config:
        json_schema_extra = {
            "example": {
                "bills": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174003",
                        "property_id": "123e4567-e89b-12d3-a456-426614174001",
                        "bill_type": "electricity",
                        "total_amount": 5000.00,
                        "period_start": "2025-10-01",
                        "period_end": "2025-10-31",
                        "status": "paid",
                        "due_date": "2025-11-10",
                    }
                ],
                "total": 1,
                "skip": 0,
                "limit": 50,
            }
        }


class RecurringBillResponse(BaseModel):
    """Response schema for recurring bill template."""

    id: UUID
    property_id: UUID
    bill_type: BillType
    frequency: RecurringFrequency
    allocation_method: AllocationMethod
    estimated_amount: Decimal
    currency: str
    day_of_month: int
    description: str | None
    is_active: bool
    last_generated: date | None
    next_generation: date | None
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174006",
                "property_id": "123e4567-e89b-12d3-a456-426614174001",
                "bill_type": "electricity",
                "frequency": "monthly",
                "allocation_method": "equal",
                "estimated_amount": 5000.00,
                "currency": "INR",
                "day_of_month": 1,
                "description": "Monthly electricity bill template",
                "is_active": True,
                "last_generated": "2025-10-01",
                "next_generation": "2025-11-01",
                "created_by": "123e4567-e89b-12d3-a456-426614174004",
                "created_at": "2025-09-01T09:00:00Z",
                "updated_at": "2025-10-01T09:00:00Z",
            }
        }


class RecurringBillListResponse(BaseModel):
    """Response schema for recurring bill list."""

    recurring_bills: list[RecurringBillResponse]
    total: int
    skip: int
    limit: int

    class Config:
        json_schema_extra = {
            "example": {
                "recurring_bills": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174006",
                        "property_id": "123e4567-e89b-12d3-a456-426614174001",
                        "bill_type": "electricity",
                        "frequency": "monthly",
                        "is_active": True,
                    }
                ],
                "total": 1,
                "skip": 0,
                "limit": 50,
            }
        }


# ==================== Export Schemas ====================

__all__ = [
    "BillCreateRequest",
    "BillUpdateRequest",
    "BillAllocationCreateRequest",
    "BillAllocationUpdateRequest",
    "RecurringBillCreateRequest",
    "RecurringBillUpdateRequest",
    "BillResponse",
    "BillAllocationResponse",
    "BillListResponse",
    "RecurringBillResponse",
    "RecurringBillListResponse",
]
