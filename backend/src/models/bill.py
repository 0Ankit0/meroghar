"""Bill and BillAllocation models (stub for Phase 3, full implementation in Phase 5).

Minimal implementation to support User Story 1 relationships.
Full implementation in T075-T077.
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..core.database import Base


class BillAllocation(Base):
    """BillAllocation model representing tenant's share of a bill (stub)."""

    __tablename__ = "bill_allocations"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
        comment="Allocation identifier",
    )

    # Foreign Keys
    bill_id = Column(
        UUID(as_uuid=True),
        ForeignKey("bills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Related bill",
    )
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Allocated tenant",
    )

    # Allocation Details
    amount = Column(
        Numeric(12, 2),
        nullable=False,
        comment="Allocated amount",
    )
    is_paid = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Payment status",
    )
    paid_at = Column(
        DateTime,
        nullable=True,
        comment="Payment timestamp",
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
    tenant = relationship(
        "Tenant",
        back_populates="bill_allocations",
        foreign_keys=[tenant_id],
    )

    def __repr__(self) -> str:
        return f"<BillAllocation(id={self.id}, tenant_id={self.tenant_id}, amount={self.amount})>"
