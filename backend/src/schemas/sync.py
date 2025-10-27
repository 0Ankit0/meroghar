"""
Sync request and response schemas.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SyncRecordRequest(BaseModel):
    """Single record sync request."""

    client_id: str | None = Field(
        None, description="Client-side temporary ID for tracking (useful for CREATE operations)"
    )
    model: str = Field(
        ..., description="Model name (e.g., 'property', 'tenant', 'payment', 'bill', 'expense')"
    )
    operation: str = Field(..., description="Operation type: 'create', 'update', or 'delete'")
    data: dict[str, Any] = Field(
        ..., description="Record data to sync (must include 'updated_at' for conflict resolution)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "client_id": "temp-123",
                "model": "expense",
                "operation": "create",
                "data": {
                    "property_id": 1,
                    "category": "maintenance",
                    "amount": 5000.00,
                    "description": "Plumbing repair",
                    "expense_date": "2025-01-26",
                    "updated_at": "2025-01-26T10:30:00Z",
                },
            }
        }


class SyncRequest(BaseModel):
    """Bulk sync request containing multiple records."""

    records: list[SyncRecordRequest] = Field(..., description="List of records to sync")

    class Config:
        json_schema_extra = {
            "example": {
                "records": [
                    {
                        "client_id": "temp-123",
                        "model": "expense",
                        "operation": "create",
                        "data": {
                            "property_id": 1,
                            "category": "maintenance",
                            "amount": 5000.00,
                            "description": "Plumbing repair",
                            "expense_date": "2025-01-26",
                            "updated_at": "2025-01-26T10:30:00Z",
                        },
                    },
                    {
                        "model": "payment",
                        "operation": "update",
                        "data": {
                            "id": 42,
                            "status": "completed",
                            "updated_at": "2025-01-26T11:00:00Z",
                        },
                    },
                ]
            }
        }


class SyncRecordResponse(BaseModel):
    """Single record sync result."""

    model: str = Field(..., description="Model name")
    operation: str = Field(..., description="Operation type")
    client_id: str | None = Field(None, description="Client-side temporary ID")
    status: str = Field(..., description="Result status: 'success', 'failed', or 'conflict'")
    message: str = Field(..., description="Human-readable result message")
    server_id: int | None = Field(None, description="Server-assigned ID (for CREATE operations)")
    conflict_details: dict[str, Any] | None = Field(
        None, description="Conflict details if status is 'conflict'"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "model": "expense",
                "operation": "create",
                "client_id": "temp-123",
                "status": "success",
                "message": "Created expense with ID 789",
                "server_id": 789,
            }
        }


class SyncResponse(BaseModel):
    """Bulk sync response with summary and detailed results."""

    sync_log_id: int = Field(..., description="Sync log ID for tracking")
    total_records: int = Field(..., description="Total records in request")
    successful: int = Field(..., description="Number of successfully synced records")
    failed: int = Field(..., description="Number of failed records")
    conflicts: int = Field(..., description="Number of conflicted records")
    results: list[SyncRecordResponse] = Field(..., description="Detailed results for each record")

    class Config:
        json_schema_extra = {
            "example": {
                "sync_log_id": 123,
                "total_records": 5,
                "successful": 3,
                "failed": 1,
                "conflicts": 1,
                "results": [
                    {
                        "model": "expense",
                        "operation": "create",
                        "client_id": "temp-123",
                        "status": "success",
                        "message": "Created expense with ID 789",
                        "server_id": 789,
                    }
                ],
            }
        }


class SyncStatusResponse(BaseModel):
    """Sync status summary for a user/device."""

    user_id: int = Field(..., description="User ID")
    device_id: str | None = Field(None, description="Device ID (if filtered)")
    total_syncs: int = Field(..., description="Total number of sync operations")
    pending: int = Field(..., description="Number of pending syncs")
    in_progress: int = Field(..., description="Number of in-progress syncs")
    success: int = Field(..., description="Number of successful syncs")
    failed: int = Field(..., description="Number of failed syncs")
    conflict: int = Field(..., description="Number of conflicted syncs")
    records_synced: int = Field(..., description="Total records successfully synced")
    records_failed: int = Field(..., description="Total records that failed")
    records_conflict: int = Field(..., description="Total records with conflicts")
    latest_sync_at: str | None = Field(None, description="Latest sync timestamp (ISO format)")
    latest_sync_status: str | None = Field(None, description="Latest sync status")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "device_id": "device-abc-123",
                "total_syncs": 50,
                "pending": 2,
                "in_progress": 0,
                "success": 45,
                "failed": 2,
                "conflict": 1,
                "records_synced": 523,
                "records_failed": 12,
                "records_conflict": 3,
                "latest_sync_at": "2025-01-26T12:00:00Z",
                "latest_sync_status": "success",
            }
        }


class ConflictResponse(BaseModel):
    """Conflict details for resolution UI."""

    sync_log_id: int = Field(..., description="Sync log ID")
    device_id: str = Field(..., description="Device that triggered the conflict")
    device_name: str | None = Field(None, description="Human-readable device name")
    started_at: datetime = Field(..., description="When the sync started")
    conflict_details: dict[str, Any] | None = Field(
        None, description="Structured conflict information (models, records, timestamps)"
    )
    records_conflict: int = Field(..., description="Number of conflicted records")

    class Config:
        json_schema_extra = {
            "example": {
                "sync_log_id": 456,
                "device_id": "device-abc-123",
                "device_name": "John's Phone",
                "started_at": "2025-01-26T12:00:00Z",
                "records_conflict": 1,
                "conflict_details": {
                    "conflicts": [
                        {
                            "model": "payment",
                            "record_id": 42,
                            "client_data": {
                                "status": "completed",
                                "updated_at": "2025-01-26T11:00:00Z",
                            },
                            "server_data": {"id": 42, "updated_at": "2025-01-26T11:30:00Z"},
                            "reason": "Server record is newer",
                        }
                    ]
                },
            }
        }
