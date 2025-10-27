"""Property and PropertyAssignment models.

Implements T025 and T026 from tasks.md.
"""
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..core.database import Base


class Property(Base):
    """Property model representing a rental property.
    
    Properties are owned by users with role='owner' and managed by
    intermediaries through PropertyAssignment junction table.
    
    Features:
    - Multi-unit support (apartments, condos, etc.)
    - Immutable base currency for financial consistency
    - Full address tracking
    - Owner and intermediary access control via RLS
    """

    __tablename__ = "properties"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
        comment="Unique property identifier",
    )

    # Ownership
    owner_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Property owner (must be role='owner')",
    )

    # Basic Info
    name = Column(
        String(255),
        nullable=False,
        comment="Property name/identifier",
    )

    # Address
    address_line1 = Column(
        String(255),
        nullable=False,
        comment="Street address",
    )
    address_line2 = Column(
        String(255),
        nullable=True,
        comment="Apartment/unit number",
    )
    city = Column(
        String(100),
        nullable=False,
        comment="City",
    )
    state = Column(
        String(100),
        nullable=False,
        comment="State/province",
    )
    postal_code = Column(
        String(20),
        nullable=False,
        comment="Postal/ZIP code",
    )
    country = Column(
        String(100),
        nullable=False,
        comment="Country",
    )

    # Property Details
    total_units = Column(
        Integer,
        nullable=False,
        comment="Number of rental units",
    )
    base_currency = Column(
        String(3),
        nullable=False,
        comment="ISO 4217 currency code (immutable after creation)",
    )

    # Timestamps
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Property creation timestamp",
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Last update timestamp",
    )

    # Relationships
    owner = relationship(
        "User",
        back_populates="owned_properties",
        foreign_keys=[owner_id],
    )
    assignments = relationship(
        "PropertyAssignment",
        back_populates="property",
        cascade="all, delete-orphan",
    )
    tenants = relationship(
        "Tenant",
        back_populates="property",
        cascade="all, delete-orphan",
    )
    payments = relationship(
        "Payment",
        back_populates="property",
        cascade="all, delete-orphan",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("total_units > 0", name="check_total_units_positive"),
        Index("idx_properties_city", "city", "state"),
    )

    def __repr__(self) -> str:
        return f"<Property(id={self.id}, name={self.name}, owner_id={self.owner_id})>"

    @property
    def full_address(self) -> str:
        """Get formatted full address."""
        parts = [
            self.address_line1,
            self.address_line2,
            self.city,
            self.state,
            self.postal_code,
            self.country,
        ]
        return ", ".join(filter(None, parts))


class PropertyAssignment(Base):
    """PropertyAssignment junction table for intermediary assignments.
    
    Manages many-to-many relationship between intermediaries and properties.
    Allows owners to assign multiple intermediaries to a property and
    intermediaries to manage multiple properties.
    
    Features:
    - Soft delete (removed_at) for assignment history
    - Unique constraint on active assignments
    - Audit trail (assigned_by, assigned_at, removed_at)
    """

    __tablename__ = "property_assignments"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
        comment="Assignment identifier",
    )

    # Foreign Keys
    property_id = Column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Assigned property",
    )
    intermediary_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Assigned intermediary (must be role='intermediary')",
    )
    assigned_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
        comment="Owner who made assignment",
    )

    # Status
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Active assignment flag",
    )

    # Timestamps
    assigned_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Assignment timestamp",
    )
    removed_at = Column(
        DateTime,
        nullable=True,
        comment="Removal timestamp (soft delete)",
    )

    # Relationships
    property = relationship(
        "Property",
        back_populates="assignments",
        foreign_keys=[property_id],
    )
    intermediary = relationship(
        "User",
        back_populates="property_assignments",
        foreign_keys=[intermediary_id],
    )
    assigner = relationship(
        "User",
        foreign_keys=[assigned_by],
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "property_id",
            "intermediary_id",
            "is_active",
            name="uq_property_intermediary_active",
            postgresql_where=(is_active == True),
        ),
        Index("idx_pa_active", "is_active", postgresql_where=(is_active == True)),
    )

    def __repr__(self) -> str:
        return f"<PropertyAssignment(id={self.id}, property_id={self.property_id}, intermediary_id={self.intermediary_id})>"
