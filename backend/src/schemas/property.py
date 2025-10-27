"""Property request/response schemas.

Implements T031 from tasks.md.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

# ==================== Request Schemas ====================


class PropertyCreateRequest(BaseModel):
    """Create property request."""

    name: str = Field(..., min_length=1, max_length=255, description="Property name/identifier")
    address_line1: str = Field(..., min_length=1, max_length=255, description="Street address")
    address_line2: str | None = Field(None, max_length=255, description="Apartment/unit number")
    city: str = Field(..., min_length=1, max_length=100, description="City")
    state: str = Field(..., min_length=1, max_length=100, description="State/province")
    postal_code: str = Field(..., min_length=1, max_length=20, description="Postal/ZIP code")
    country: str = Field(..., min_length=1, max_length=100, description="Country")
    total_units: int = Field(..., gt=0, description="Number of rental units")
    base_currency: str = Field(
        ..., min_length=3, max_length=3, description="ISO 4217 currency code"
    )

    @field_validator("base_currency")
    @classmethod
    def validate_currency_code(cls, v: str) -> str:
        """Validate ISO 4217 currency code."""
        # Common currency codes validation
        valid_codes = {
            "USD",
            "EUR",
            "GBP",
            "INR",
            "JPY",
            "CNY",
            "AUD",
            "CAD",
            "CHF",
            "SEK",
            "NZD",
            "SGD",
            "HKD",
            "NOK",
            "KRW",
            "TRY",
            "RUB",
            "BRL",
            "ZAR",
            "MXN",
        }
        v_upper = v.upper()
        if v_upper not in valid_codes:
            raise ValueError(f"Invalid currency code. Supported: {', '.join(sorted(valid_codes))}")
        return v_upper

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Sunrise Apartments",
                "address_line1": "123 Main Street",
                "address_line2": "Building A",
                "city": "Kathmandu",
                "state": "Bagmati",
                "postal_code": "44600",
                "country": "Nepal",
                "total_units": 10,
                "base_currency": "INR",
            }
        }
    }


class PropertyUpdateRequest(BaseModel):
    """Update property request."""

    name: str | None = Field(
        None, min_length=1, max_length=255, description="Property name/identifier"
    )
    address_line1: str | None = Field(
        None, min_length=1, max_length=255, description="Street address"
    )
    address_line2: str | None = Field(None, max_length=255, description="Apartment/unit number")
    city: str | None = Field(None, min_length=1, max_length=100, description="City")
    state: str | None = Field(None, min_length=1, max_length=100, description="State/province")
    postal_code: str | None = Field(
        None, min_length=1, max_length=20, description="Postal/ZIP code"
    )
    country: str | None = Field(None, min_length=1, max_length=100, description="Country")
    total_units: int | None = Field(None, gt=0, description="Number of rental units")
    # Note: base_currency is immutable and cannot be updated

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Sunrise Apartments - Renovated",
                "total_units": 12,
            }
        }
    }


class PropertyAssignIntermediaryRequest(BaseModel):
    """Assign intermediary to property request."""

    intermediary_id: UUID = Field(..., description="Intermediary user ID to assign")

    model_config = {
        "json_schema_extra": {
            "example": {
                "intermediary_id": "660e8400-e29b-41d4-a716-446655440001",
            }
        }
    }


class PropertyRemoveIntermediaryRequest(BaseModel):
    """Remove intermediary from property request."""

    intermediary_id: UUID = Field(..., description="Intermediary user ID to remove")

    model_config = {
        "json_schema_extra": {
            "example": {
                "intermediary_id": "660e8400-e29b-41d4-a716-446655440001",
            }
        }
    }


# ==================== Response Schemas ====================


class PropertyResponse(BaseModel):
    """Property response schema."""

    id: UUID = Field(..., description="Property unique identifier")
    owner_id: UUID = Field(..., description="Property owner ID")
    name: str = Field(..., description="Property name/identifier")
    address_line1: str = Field(..., description="Street address")
    address_line2: str | None = Field(None, description="Apartment/unit number")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State/province")
    postal_code: str = Field(..., description="Postal/ZIP code")
    country: str = Field(..., description="Country")
    total_units: int = Field(..., description="Number of rental units")
    base_currency: str = Field(..., description="ISO 4217 currency code")
    created_at: datetime = Field(..., description="Property creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "770e8400-e29b-41d4-a716-446655440002",
                "owner_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Sunrise Apartments",
                "address_line1": "123 Main Street",
                "address_line2": "Building A",
                "city": "Kathmandu",
                "state": "Bagmati",
                "postal_code": "44600",
                "country": "Nepal",
                "total_units": 10,
                "base_currency": "INR",
                "created_at": "2025-01-27T10:00:00",
                "updated_at": "2025-01-27T10:00:00",
            }
        },
    }


class PropertyListResponse(BaseModel):
    """Property list item response."""

    id: UUID = Field(..., description="Property unique identifier")
    name: str = Field(..., description="Property name/identifier")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State/province")
    total_units: int = Field(..., description="Number of rental units")
    base_currency: str = Field(..., description="ISO 4217 currency code")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "770e8400-e29b-41d4-a716-446655440002",
                "name": "Sunrise Apartments",
                "city": "Kathmandu",
                "state": "Bagmati",
                "total_units": 10,
                "base_currency": "INR",
            }
        },
    }


class PropertyAssignmentResponse(BaseModel):
    """Property assignment response."""

    id: UUID = Field(..., description="Assignment identifier")
    property_id: UUID = Field(..., description="Property ID")
    intermediary_id: UUID = Field(..., description="Intermediary user ID")
    assigned_by: UUID = Field(..., description="Owner who made assignment")
    is_active: bool = Field(..., description="Active assignment flag")
    assigned_at: datetime = Field(..., description="Assignment timestamp")
    removed_at: datetime | None = Field(None, description="Removal timestamp (soft delete)")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "880e8400-e29b-41d4-a716-446655440003",
                "property_id": "770e8400-e29b-41d4-a716-446655440002",
                "intermediary_id": "660e8400-e29b-41d4-a716-446655440001",
                "assigned_by": "550e8400-e29b-41d4-a716-446655440000",
                "is_active": True,
                "assigned_at": "2025-01-27T10:00:00",
                "removed_at": None,
            }
        },
    }
