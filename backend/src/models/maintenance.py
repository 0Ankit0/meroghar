"""Maintenance request model.

Implements maintenance tracking features.
"""

from datetime import datetime
from enum import Enum as PyEnum
from uuid import uuid4

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import relationship

from ..core.database import Base


class MaintenanceStatus(str, PyEnum):
    """Maintenance request status."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class MaintenancePriority(str, PyEnum):
    """Maintenance request priority."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class MaintenanceRequest(Base):
    """Maintenance request model.
    
    Tracks maintenance issues reported by tenants or identified by intermediaries.
    """

    __tablename__ = "maintenance_requests"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
        comment="Request identifier",
    )

    # Foreign Keys
    property_id = Column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Associated property",
    )
    requested_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
        comment="User who submitted the request",
    )
    assigned_to = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User assigned to handle the request",
    )

    # Details
    title = Column(
        String(200),
        nullable=False,
        comment="Issue title",
    )
    description = Column(
        Text,
        nullable=False,
        comment="Detailed description of the issue",
    )
    priority = Column(
        Enum(MaintenancePriority, name="maintenance_priority"),
        default=MaintenancePriority.MEDIUM,
        nullable=False,
        index=True,
        comment="Urgency level",
    )
    status = Column(
        Enum(MaintenanceStatus, name="maintenance_status"),
        default=MaintenanceStatus.OPEN,
        nullable=False,
        index=True,
        comment="Current status",
    )

    # Media
    images = Column(
        JSON,
        default=list,
        nullable=True,
        comment="List of image URLs demonstrating the issue",
    )

    # Resolution
    resolution_notes = Column(
        Text,
        nullable=True,
        comment="Notes on how the issue was resolved",
    )
    scheduled_date = Column(
        DateTime,
        nullable=True,
        comment="Scheduled date for maintenance work",
    )
    resolved_at = Column(
        DateTime,
        nullable=True,
        comment="Completion timestamp",
    )

    # Timestamps
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Creation timestamp",
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Last update timestamp",
    )

    # Relationships
    property = relationship(
        "Property",
        back_populates="maintenance_requests",
    )
    requester = relationship(
        "User",
        foreign_keys=[requested_by],
    )
    assignee = relationship(
        "User",
        foreign_keys=[assigned_to],
    )

    def __repr__(self) -> str:
        return f"<MaintenanceRequest(id={self.id}, title={self.title}, status={self.status})>"
