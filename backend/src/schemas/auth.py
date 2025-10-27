"""Authentication request/response schemas.

Implements T029 from tasks.md.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from ..models.user import UserRole


# ==================== Request Schemas ====================


class RegisterRequest(BaseModel):
    """User registration request."""

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
    role: UserRole = Field(..., description="User role (owner, intermediary, tenant)")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets strength requirements."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format (E.164)."""
        if v is None:
            return v
        # Basic E.164 validation: +[country code][number]
        if not v.startswith("+"):
            raise ValueError("Phone number must start with + (E.164 format)")
        if not v[1:].isdigit():
            raise ValueError("Phone number must contain only digits after +")
        if len(v) < 8 or len(v) > 20:
            raise ValueError("Phone number must be between 8 and 20 characters")
        return v

    model_config = {"json_schema_extra": {"example": {
        "email": "owner@example.com",
        "password": "SecurePass123",
        "full_name": "John Doe",
        "phone": "+911234567890",
        "role": "owner",
    }}}


class LoginRequest(BaseModel):
    """User login request."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

    model_config = {"json_schema_extra": {"example": {
        "email": "owner@example.com",
        "password": "SecurePass123",
    }}}


class RefreshTokenRequest(BaseModel):
    """Token refresh request."""

    refresh_token: str = Field(..., description="JWT refresh token")

    model_config = {"json_schema_extra": {"example": {
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    }}}


# ==================== Response Schemas ====================


class TokenPair(BaseModel):
    """JWT token pair."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")

    model_config = {"json_schema_extra": {"example": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
    }}}


class AuthResponse(BaseModel):
    """Authentication response with tokens and user info."""

    user_id: UUID = Field(..., description="User unique identifier")
    email: str = Field(..., description="User email address")
    full_name: str = Field(..., description="User's full name")
    role: UserRole = Field(..., description="User role")
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")

    model_config = {"json_schema_extra": {"example": {
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "owner@example.com",
        "full_name": "John Doe",
        "role": "owner",
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
    }}}


class LogoutResponse(BaseModel):
    """Logout response."""

    message: str = Field(default="Successfully logged out", description="Logout message")

    model_config = {"json_schema_extra": {"example": {
        "message": "Successfully logged out",
    }}}
