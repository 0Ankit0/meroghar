"""Maintenance request schemas.

Implements maintenance request validation and serialization.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from ..models.maintenance import MaintenancePriority, MaintenanceStatus


class MaintenanceRequestBase(BaseModel):
    """Base schema for maintenance requests."""

    title: str = Field(..., min_length=3, max_length=200, example="Leaking faucet")
    description: str = Field(..., min_length=10, example="Kitchen sink tap is leaking continuously.")
    priority: MaintenancePriority = Field(default=MaintenancePriority.MEDIUM)
    images: list[str] = Field(default_factory=list, description="List of image URLs")


class MaintenanceRequestCreate(MaintenanceRequestBase):
    """Schema for creating a maintenance request."""

    property_id: UUID


class MaintenanceRequestUpdate(BaseModel):
    """Schema for updating a maintenance request."""

    title: str | None = Field(None, min_length=3, max_length=200)
    description: str | None = Field(None, min_length=10)
    priority: MaintenancePriority | None = None
    status: MaintenanceStatus | None = None
    assigned_to: UUID | None = Field(None, description="Assign to user (Intermediary/Owner)")
    resolution_notes: str | None = None
    scheduled_date: datetime | None = None
    images: list[str] | None = None


class MaintenanceRequestResponse(MaintenanceRequestBase):
    """Schema for maintenance request response."""

    id: UUID
    property_id: UUID
    requested_by: UUID
    assigned_to: UUID | None = None
    status: MaintenanceStatus
    resolution_notes: str | None = None
    scheduled_date: datetime | None = None
    resolved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    
    # Flattened/Related data (optional)
    property_name: str | None = None
    requester_name: str | None = None
    assignee_name: str | None = None

    class Config:
        from_attributes = True


class MaintenanceListResponse(BaseModel):
    """Schema for maintenance list item."""
    
    id: UUID
    title: str
    status: MaintenanceStatus
    priority: MaintenancePriority
    created_at: datetime
    property_name: str
    
    class Config:
        from_attributes = True
