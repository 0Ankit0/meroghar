"""Tenant model.

Implements T027 from tasks.md.
"""

from datetime import date, datetime
from enum import Enum as PyEnum
from uuid import uuid4

from sqlalchemy import (CheckConstraint, Column, Date, DateTime, Enum,
                        ForeignKey, Numeric)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import relationship

from ..core.database import Base


class TenantStatus(str, PyEnum):
    """Tenant status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING_MOVE_OUT = "pending_move_out"


class Tenant(Base):
    """Tenant model representing a property renter.

    Tenants are users with role='tenant' who live in a property.
    Each tenant has an associated User account for login.

    Features:
    - Move-in/move-out date tracking
    - Monthly rent and security deposit
    - Electricity rate tracking for bill splitting
    - Status tracking (active, pending move out, inactive)
    - Managed by assigned intermediary

    Financial Tracking:
    - Monthly rent amount
    - Security deposit
    - Per-unit electricity rate (optional)
    - Current balance calculated from payments and allocations

    Access Control:
    - Tenants see only themselves via RLS
    - Intermediaries see tenants in their assigned properties
    - Owners see all tenants in their properties
    """

    __tablename__ = "tenants"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
        comment="Tenant identifier",
    )

    # Foreign Keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        comment="Associated user account (must be role='tenant')",
    )
    property_id = Column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Rented property",
    )
    intermediary_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Managing intermediary",
    )
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
        comment="User who created tenant record",
    )

    # Rental Period
    move_in_date = Column(
        Date,
        nullable=False,
        comment="Tenant move-in date",
    )
    move_out_date = Column(
        Date,
        nullable=True,
        comment="Tenant move-out date",
    )

    # Financial
    monthly_rent = Column(
        Numeric(12, 2),
        nullable=False,
        comment="Monthly rent amount",
    )
    security_deposit = Column(
        Numeric(12, 2),
        nullable=True,
        comment="Security deposit amount",
    )
    electricity_rate = Column(
        Numeric(8, 4),
        nullable=True,
        comment="Per-unit electricity rate (for bill splitting)",
    )

    # Rent Increment Policy (T191, T192)
    rent_increment_policy = Column(
        JSON,
        nullable=True,
        comment="Rent increment policy: {type: 'percentage'|'fixed', value: number, interval_years: number, next_increment_date: ISO date}",
    )
    rent_history = Column(
        JSON,
        nullable=True,
        default=list,
        comment="Historical rent changes: [{effective_date: ISO, amount: Decimal, reason: str, applied_by: UUID}]",
    )

    # Status
    status = Column(
        Enum(TenantStatus, name="tenant_status"),
        default=TenantStatus.ACTIVE,
        nullable=False,
        index=True,
        comment="Tenant status",
    )

    # Timestamps
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Record creation timestamp",
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Last update timestamp",
    )

    # Relationships
    user = relationship(
        "User",
        back_populates="tenant_profile",
        foreign_keys=[user_id],
    )
    property = relationship(
        "Property",
        back_populates="tenants",
        foreign_keys=[property_id],
    )
    intermediary = relationship(
        "User",
        foreign_keys=[intermediary_id],
    )
    creator = relationship(
        "User",
        back_populates="created_tenants",
        foreign_keys=[created_by],
    )
    payments = relationship(
        "Payment",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )
    bill_allocations = relationship(
        "BillAllocation",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )
    messages = relationship(
        "Message",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )
    documents = relationship(
        "Document",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("monthly_rent > 0", name="check_monthly_rent_positive"),
        CheckConstraint(
            "move_out_date IS NULL OR move_out_date > move_in_date",
            name="check_move_out_after_move_in",
        ),
    )

    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, user_id={self.user_id}, property_id={self.property_id})>"

    @property
    def is_active(self) -> bool:
        """Check if tenant is currently active."""
        return self.status == TenantStatus.ACTIVE

    @property
    def days_stayed(self) -> int:
        """Calculate days stayed (up to move-out date or today)."""
        end_date = self.move_out_date or date.today()
        return (end_date - self.move_in_date).days
