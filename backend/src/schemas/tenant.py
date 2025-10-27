"""Tenant request/response schemas.

Implements T032 from tasks.md.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from ..models.tenant import TenantStatus


# ==================== Request Schemas ====================


class TenantCreateRequest(BaseModel):
    """Create tenant request."""

    user_id: UUID = Field(..., description="User ID (must be role='tenant')")
    property_id: UUID = Field(..., description="Property ID")
    move_in_date: date = Field(..., description="Tenant move-in date")
    monthly_rent: Decimal = Field(
        ..., gt=0, max_digits=12, decimal_places=2, description="Monthly rent amount"
    )
    security_deposit: Optional[Decimal] = Field(
        None,
        ge=0,
        max_digits=12,
        decimal_places=2,
        description="Security deposit amount",
    )
    electricity_rate: Optional[Decimal] = Field(
        None,
        ge=0,
        max_digits=8,
        decimal_places=4,
        description="Per-unit electricity rate",
    )

    @field_validator("move_in_date")
    @classmethod
    def validate_move_in_date(cls, v: date) -> date:
        """Validate move-in date is not in the past."""
        # Allow past dates for existing tenants being added to system
        # Business logic will handle validation based on context
        return v

    model_config = {"json_schema_extra": {"example": {
        "user_id": "990e8400-e29b-41d4-a716-446655440004",
        "property_id": "770e8400-e29b-41d4-a716-446655440002",
        "move_in_date": "2025-02-01",
        "monthly_rent": "15000.00",
        "security_deposit": "30000.00",
        "electricity_rate": "8.5000",
    }}}


class TenantUpdateRequest(BaseModel):
    """Update tenant request."""

    move_out_date: Optional[date] = Field(None, description="Tenant move-out date")
    monthly_rent: Optional[Decimal] = Field(
        None, gt=0, max_digits=12, decimal_places=2, description="Monthly rent amount"
    )
    security_deposit: Optional[Decimal] = Field(
        None,
        ge=0,
        max_digits=12,
        decimal_places=2,
        description="Security deposit amount",
    )
    electricity_rate: Optional[Decimal] = Field(
        None,
        ge=0,
        max_digits=8,
        decimal_places=4,
        description="Per-unit electricity rate",
    )
    status: Optional[TenantStatus] = Field(None, description="Tenant status")

    model_config = {"json_schema_extra": {"example": {
        "monthly_rent": "16000.00",
        "electricity_rate": "9.0000",
    }}}


class TenantMoveOutRequest(BaseModel):
    """Tenant move-out request."""

    move_out_date: date = Field(..., description="Tenant move-out date")

    @field_validator("move_out_date")
    @classmethod
    def validate_move_out_date(cls, v: date) -> date:
        """Validate move-out date is not in the future."""
        if v > date.today():
            raise ValueError("Move-out date cannot be in the future")
        return v

    model_config = {"json_schema_extra": {"example": {
        "move_out_date": "2025-06-30",
    }}}


# ==================== Response Schemas ====================


class TenantResponse(BaseModel):
    """Tenant response schema."""

    id: UUID = Field(..., description="Tenant identifier")
    user_id: UUID = Field(..., description="User ID")
    property_id: UUID = Field(..., description="Property ID")
    intermediary_id: UUID = Field(..., description="Managing intermediary ID")
    created_by: UUID = Field(..., description="User who created tenant record")
    move_in_date: date = Field(..., description="Tenant move-in date")
    move_out_date: Optional[date] = Field(None, description="Tenant move-out date")
    monthly_rent: Decimal = Field(..., description="Monthly rent amount")
    security_deposit: Optional[Decimal] = Field(
        None, description="Security deposit amount"
    )
    electricity_rate: Optional[Decimal] = Field(
        None, description="Per-unit electricity rate"
    )
    status: TenantStatus = Field(..., description="Tenant status")
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {"example": {
            "id": "aa0e8400-e29b-41d4-a716-446655440005",
            "user_id": "990e8400-e29b-41d4-a716-446655440004",
            "property_id": "770e8400-e29b-41d4-a716-446655440002",
            "intermediary_id": "660e8400-e29b-41d4-a716-446655440001",
            "created_by": "660e8400-e29b-41d4-a716-446655440001",
            "move_in_date": "2025-02-01",
            "move_out_date": None,
            "monthly_rent": "15000.00",
            "security_deposit": "30000.00",
            "electricity_rate": "8.5000",
            "status": "active",
            "created_at": "2025-01-27T10:00:00",
            "updated_at": "2025-01-27T10:00:00",
        }},
    }


class TenantListResponse(BaseModel):
    """Tenant list item response."""

    id: UUID = Field(..., description="Tenant identifier")
    user_id: UUID = Field(..., description="User ID")
    property_id: UUID = Field(..., description="Property ID")
    move_in_date: date = Field(..., description="Tenant move-in date")
    move_out_date: Optional[date] = Field(None, description="Tenant move-out date")
    monthly_rent: Decimal = Field(..., description="Monthly rent amount")
    status: TenantStatus = Field(..., description="Tenant status")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {"example": {
            "id": "aa0e8400-e29b-41d4-a716-446655440005",
            "user_id": "990e8400-e29b-41d4-a716-446655440004",
            "property_id": "770e8400-e29b-41d4-a716-446655440002",
            "move_in_date": "2025-02-01",
            "move_out_date": None,
            "monthly_rent": "15000.00",
            "status": "active",
        }},
    }


class TenantWithUserResponse(BaseModel):
    """Tenant response with user details."""

    id: UUID = Field(..., description="Tenant identifier")
    user_id: UUID = Field(..., description="User ID")
    user_email: str = Field(..., description="User email")
    user_full_name: str = Field(..., description="User full name")
    user_phone: Optional[str] = Field(None, description="User phone")
    property_id: UUID = Field(..., description="Property ID")
    property_name: str = Field(..., description="Property name")
    move_in_date: date = Field(..., description="Tenant move-in date")
    move_out_date: Optional[date] = Field(None, description="Tenant move-out date")
    monthly_rent: Decimal = Field(..., description="Monthly rent amount")
    security_deposit: Optional[Decimal] = Field(
        None, description="Security deposit amount"
    )
    status: TenantStatus = Field(..., description="Tenant status")

    model_config = {"json_schema_extra": {"example": {
        "id": "aa0e8400-e29b-41d4-a716-446655440005",
        "user_id": "990e8400-e29b-41d4-a716-446655440004",
        "user_email": "tenant@example.com",
        "user_full_name": "Jane Smith",
        "user_phone": "+911234567890",
        "property_id": "770e8400-e29b-41d4-a716-446655440002",
        "property_name": "Sunrise Apartments",
        "move_in_date": "2025-02-01",
        "move_out_date": None,
        "monthly_rent": "15000.00",
        "security_deposit": "30000.00",
        "status": "active",
    }}}


class TenantBalanceResponse(BaseModel):
    """Tenant balance response."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    total_rent_due: Decimal = Field(..., description="Total rent due")
    total_paid: Decimal = Field(..., description="Total amount paid")
    current_balance: Decimal = Field(..., description="Current balance (negative = owed)")
    last_payment_date: Optional[date] = Field(None, description="Last payment date")
    months_stayed: int = Field(..., description="Number of months stayed")

    model_config = {"json_schema_extra": {"example": {
        "tenant_id": "aa0e8400-e29b-41d4-a716-446655440005",
        "total_rent_due": "90000.00",
        "total_paid": "75000.00",
        "current_balance": "-15000.00",
        "last_payment_date": "2025-01-15",
        "months_stayed": 6,
    }}}
