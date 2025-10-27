"""User request/response schemas.

Implements T030 from tasks.md.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from ..models.user import UserRole


# ==================== Request Schemas ====================


class UserCreateRequest(BaseModel):
    """Create user request (for intermediaries creating tenants)."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Password (min 8 characters)",
    )
    full_name: str = Field(
        ..., min_length=1, max_length=255, description="User's full name"
    )
    phone: Optional[str] = Field(
        None, max_length=20, description="Contact phone number (E.164 format)"
    )
    role: UserRole = Field(..., description="User role (tenant for intermediaries)")

    model_config = {"json_schema_extra": {"example": {
        "email": "tenant@example.com",
        "password": "SecurePass123",
        "full_name": "Jane Smith",
        "phone": "+911234567890",
        "role": "tenant",
    }}}


class UserUpdateRequest(BaseModel):
    """Update user request."""

    full_name: Optional[str] = Field(
        None, min_length=1, max_length=255, description="User's full name"
    )
    phone: Optional[str] = Field(
        None, max_length=20, description="Contact phone number (E.164 format)"
    )

    model_config = {"json_schema_extra": {"example": {
        "full_name": "Jane Doe",
        "phone": "+919876543210",
    }}}


class PasswordChangeRequest(BaseModel):
    """Change password request."""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="New password (min 8 characters)",
    )

    model_config = {"json_schema_extra": {"example": {
        "current_password": "OldPass123",
        "new_password": "NewSecurePass456",
    }}}


# ==================== Response Schemas ====================


class UserResponse(BaseModel):
    """User response schema."""

    id: UUID = Field(..., description="User unique identifier")
    email: str = Field(..., description="User email address")
    phone: Optional[str] = Field(None, description="Contact phone number")
    full_name: str = Field(..., description="User's full name")
    role: UserRole = Field(..., description="User role")
    is_active: bool = Field(..., description="Account active status")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_login_at: Optional[datetime] = Field(
        None, description="Last login timestamp"
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {"example": {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "owner@example.com",
            "phone": "+911234567890",
            "full_name": "John Doe",
            "role": "owner",
            "is_active": True,
            "created_at": "2025-01-27T10:00:00",
            "updated_at": "2025-01-27T10:00:00",
            "last_login_at": "2025-01-27T12:30:00",
        }},
    }


class UserListResponse(BaseModel):
    """User list item response."""

    id: UUID = Field(..., description="User unique identifier")
    email: str = Field(..., description="User email address")
    full_name: str = Field(..., description="User's full name")
    role: UserRole = Field(..., description="User role")
    is_active: bool = Field(..., description="Account active status")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {"example": {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "owner@example.com",
            "full_name": "John Doe",
            "role": "owner",
            "is_active": True,
        }},
    }


class UserProfileResponse(BaseModel):
    """User profile response (extended info)."""

    id: UUID = Field(..., description="User unique identifier")
    email: str = Field(..., description="User email address")
    phone: Optional[str] = Field(None, description="Contact phone number")
    full_name: str = Field(..., description="User's full name")
    role: UserRole = Field(..., description="User role")
    is_active: bool = Field(..., description="Account active status")
    created_at: datetime = Field(..., description="Account creation timestamp")
    last_login_at: Optional[datetime] = Field(
        None, description="Last login timestamp"
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {"example": {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "owner@example.com",
            "phone": "+911234567890",
            "full_name": "John Doe",
            "role": "owner",
            "is_active": True,
            "created_at": "2025-01-27T10:00:00",
            "last_login_at": "2025-01-27T12:30:00",
        }},
    }
