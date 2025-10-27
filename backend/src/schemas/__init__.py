"""
Base Pydantic schemas for API requests and responses.
Implements T018 from tasks.md.
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

# Generic type for data in responses
T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    """
    Standard success response wrapper.

    Attributes:
        success: Always True for success responses
        data: Response data of generic type T
        message: Optional success message
    """

    success: bool = Field(default=True, description="Indicates successful operation")
    data: T = Field(..., description="Response data")
    message: Optional[str] = Field(default=None, description="Optional success message")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"id": "123", "name": "Example"},
                "message": "Operation completed successfully",
            }
        }


class ErrorResponse(BaseModel):
    """
    Standard error response wrapper.

    Attributes:
        success: Always False for error responses
        error: Error type or category
        detail: Detailed error message
        details: Optional list of validation errors or additional info
    """

    success: bool = Field(default=False, description="Indicates failed operation")
    error: str = Field(..., description="Error type or category")
    detail: str = Field(..., description="Detailed error message")
    details: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Additional error details"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Validation Error",
                "detail": "Invalid input data",
                "details": [
                    {"loc": ["body", "email"], "msg": "Invalid email format", "type": "value_error"}
                ],
            }
        }


class PaginationParams(BaseModel):
    """
    Pagination parameters for list endpoints.

    Attributes:
        page: Page number (1-indexed)
        page_size: Number of items per page
        skip: Number of items to skip (calculated)
    """

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(
        default=20, ge=1, le=100, description="Number of items per page"
    )

    @property
    def skip(self) -> int:
        """Calculate number of items to skip based on page and page_size."""
        return (self.page - 1) * self.page_size

    class Config:
        json_schema_extra = {"example": {"page": 1, "page_size": 20}}


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Paginated response wrapper.

    Attributes:
        success: Always True for success responses
        data: List of items of generic type T
        pagination: Pagination metadata
    """

    success: bool = Field(default=True, description="Indicates successful operation")
    data: List[T] = Field(..., description="List of items")
    pagination: "PaginationMeta" = Field(..., description="Pagination metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": [{"id": "1", "name": "Item 1"}, {"id": "2", "name": "Item 2"}],
                "pagination": {
                    "page": 1,
                    "page_size": 20,
                    "total_items": 50,
                    "total_pages": 3,
                    "has_next": True,
                    "has_prev": False,
                },
            }
        }


class PaginationMeta(BaseModel):
    """
    Pagination metadata.

    Attributes:
        page: Current page number
        page_size: Items per page
        total_items: Total number of items
        total_pages: Total number of pages
        has_next: Whether there is a next page
        has_prev: Whether there is a previous page
    """

    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_items: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")


class HealthCheckResponse(BaseModel):
    """
    Health check response.

    Attributes:
        status: Health status (healthy/unhealthy)
        version: API version
        timestamp: Current timestamp
    """

    status: str = Field(..., description="Health status")
    version: str = Field(..., description="API version")
    timestamp: str = Field(..., description="Current timestamp")
    database: str = Field(..., description="Database connection status")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "v1",
                "timestamp": "2025-10-27T07:00:00Z",
                "database": "connected",
            }
        }


__all__ = [
    # Base schemas (T018)
    "SuccessResponse",
    "ErrorResponse",
    "PaginationParams",
    "PaginatedResponse",
    "PaginationMeta",
    "HealthCheckResponse",
    # Auth schemas (T029)
    "RegisterRequest",
    "LoginRequest",
    "RefreshTokenRequest",
    "TokenPair",
    "AuthResponse",
    "LogoutResponse",
    # User schemas (T030)
    "UserCreateRequest",
    "UserUpdateRequest",
    "PasswordChangeRequest",
    "UserResponse",
    "UserListResponse",
    "UserProfileResponse",
    # Property schemas (T031)
    "PropertyCreateRequest",
    "PropertyUpdateRequest",
    "PropertyAssignIntermediaryRequest",
    "PropertyRemoveIntermediaryRequest",
    "PropertyResponse",
    "PropertyListResponse",
    "PropertyAssignmentResponse",
    # Tenant schemas (T032)
    "TenantCreateRequest",
    "TenantUpdateRequest",
    "TenantMoveOutRequest",
    "TenantResponse",
    "TenantListResponse",
    "TenantWithUserResponse",
    "TenantBalanceResponse",
]

# Import schemas for convenient access
from .auth import (
    AuthResponse,
    LoginRequest,
    LogoutResponse,
    RefreshTokenRequest,
    RegisterRequest,
    TokenPair,
)
from .property import (
    PropertyAssignIntermediaryRequest,
    PropertyAssignmentResponse,
    PropertyCreateRequest,
    PropertyListResponse,
    PropertyRemoveIntermediaryRequest,
    PropertyResponse,
    PropertyUpdateRequest,
)
from .tenant import (
    TenantBalanceResponse,
    TenantCreateRequest,
    TenantListResponse,
    TenantMoveOutRequest,
    TenantResponse,
    TenantUpdateRequest,
    TenantWithUserResponse,
)
from .user import (
    PasswordChangeRequest,
    UserCreateRequest,
    UserListResponse,
    UserProfileResponse,
    UserResponse,
    UserUpdateRequest,
)
