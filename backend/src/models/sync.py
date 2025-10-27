"""SyncLog model for tracking offline synchronization.

Implements T141 from tasks.md.
"""
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from ..core.database import Base


class SyncStatus(str, PyEnum):
    """Sync operation status."""
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    CONFLICT = "conflict"


class SyncOperation(str, PyEnum):
    """Type of sync operation."""
    
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    BULK = "bulk"


class SyncLog(Base):
    """SyncLog model for tracking offline synchronization operations.
    
    Records all sync attempts including:
    - Timestamp of sync operation
    - Status (pending, success, failed, conflict)
    - Number of records synced
    - Device information
    - Conflict details for resolution
    
    Features:
    - Tracks sync operations per user and device
    - Records success/failure with error messages
    - Stores conflict information for manual resolution
    - Maintains sync history for audit trail
    """

    __tablename__ = "sync_logs"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
        comment="Unique sync log identifier",
    )

    # User and Device
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who initiated sync",
    )
    device_id = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Device identifier (UUID or platform-specific ID)",
    )
    device_name = Column(
        String(255),
        nullable=True,
        comment="Human-readable device name",
    )

    # Sync Operation
    operation = Column(
        Enum(SyncOperation, name="sync_operation"),
        nullable=False,
        comment="Type of sync operation",
    )
    status = Column(
        Enum(SyncStatus, name="sync_status"),
        nullable=False,
        default=SyncStatus.PENDING,
        index=True,
        comment="Current status of sync",
    )

    # Records
    records_synced = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of records successfully synced",
    )
    records_failed = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of records that failed to sync",
    )
    records_conflict = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of records with conflicts",
    )

    # Timestamps
    started_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Sync start timestamp",
    )
    completed_at = Column(
        DateTime,
        nullable=True,
        comment="Sync completion timestamp",
    )

    # Details
    error_message = Column(
        Text,
        nullable=True,
        comment="Error message if sync failed",
    )
    conflict_details = Column(
        JSONB,
        nullable=True,
        comment="Details of conflicts for resolution (JSON)",
    )
    sync_metadata = Column(
        JSONB,
        nullable=True,
        comment="Additional sync metadata (versions, checksums, etc.)",
    )

    # Retry tracking
    retry_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of retry attempts",
    )
    next_retry_at = Column(
        DateTime,
        nullable=True,
        comment="Next scheduled retry time",
    )

    # Relationships
    user = relationship(
        "User",
        back_populates="sync_logs",
        foreign_keys=[user_id],
    )

    # Constraints
    __table_args__ = (
        Index("idx_sync_logs_user_device", "user_id", "device_id"),
        Index("idx_sync_logs_status_retry", "status", "next_retry_at"),
        Index("idx_sync_logs_started_at", "started_at"),
    )

    def __repr__(self) -> str:
        return f"<SyncLog(id={self.id}, user_id={self.user_id}, status={self.status}, records={self.records_synced})>"

    @property
    def is_completed(self) -> bool:
        """Check if sync is completed (success or failed)."""
        return self.status in [SyncStatus.SUCCESS, SyncStatus.FAILED]

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate sync duration in seconds."""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def total_records(self) -> int:
        """Total number of records processed."""
        return self.records_synced + self.records_failed + self.records_conflict
