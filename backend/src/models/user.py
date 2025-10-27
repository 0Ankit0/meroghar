"""User model with role-based access control.

Implements T024 from tasks.md.
"""
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, Enum, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..core.database import Base


class UserRole(str, PyEnum):
    """User role enumeration."""

    OWNER = "owner"
    INTERMEDIARY = "intermediary"
    TENANT = "tenant"


class User(Base):
    """User model representing all system users.
    
    Roles:
    - owner: Property owner who can manage properties and assign intermediaries
    - intermediary: Property manager who handles day-to-day tenant operations
    - tenant: Renter living in a property
    
    Authentication:
    - Email-based login
    - bcrypt password hashing with cost factor 12+
    - JWT token-based authentication
    
    Security:
    - RLS policies ensure users can only access their own data
    - Role is immutable after creation
    - Password must meet strength requirements
    """

    __tablename__ = "users"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
        comment="Unique user identifier",
    )

    # Authentication
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="User email address (unique login)",
    )
    phone = Column(
        String(20),
        nullable=True,
        comment="Contact phone number (E.164 format)",
    )
    password_hash = Column(
        String(255),
        nullable=False,
        comment="bcrypt hashed password",
    )

    # Profile
    full_name = Column(
        String(255),
        nullable=False,
        comment="User's full name",
    )
    role = Column(
        Enum(UserRole, name="user_role"),
        nullable=False,
        index=True,
        comment="User role (immutable after creation)",
    )

    # Status
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Account active status",
    )

    # Timestamps
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Account creation timestamp",
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Last update timestamp",
    )
    last_login_at = Column(
        DateTime,
        nullable=True,
        comment="Last login timestamp",
    )

    # Relationships
    owned_properties = relationship(
        "Property",
        back_populates="owner",
        foreign_keys="Property.owner_id",
        cascade="all, delete-orphan",
    )
    property_assignments = relationship(
        "PropertyAssignment",
        back_populates="intermediary",
        foreign_keys="PropertyAssignment.intermediary_id",
        cascade="all, delete-orphan",
    )
    tenant_profile = relationship(
        "Tenant",
        back_populates="user",
        foreign_keys="Tenant.user_id",
        uselist=False,
        cascade="all, delete-orphan",
    )
    created_tenants = relationship(
        "Tenant",
        back_populates="creator",
        foreign_keys="Tenant.created_by",
    )
    created_payments = relationship(
        "Payment",
        back_populates="recorder",
        foreign_keys="Payment.recorded_by",
    )
    recorded_expenses = relationship(
        "Expense",
        back_populates="recorder",
        foreign_keys="Expense.recorded_by",
    )
    approved_expenses = relationship(
        "Expense",
        back_populates="approver",
        foreign_keys="Expense.approved_by",
    )
    sync_logs = relationship(
        "SyncLog",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    sent_messages = relationship(
        "Message",
        back_populates="sender",
        foreign_keys="Message.sent_by",
    )
    uploaded_documents = relationship(
        "Document",
        back_populates="uploader",
        foreign_keys="Document.uploaded_by",
    )

    # Indexes
    __table_args__ = (
        Index("idx_users_active", "is_active", postgresql_where=(is_active == True)),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"

    @property
    def is_owner(self) -> bool:
        """Check if user is an owner."""
        return self.role == UserRole.OWNER

    @property
    def is_intermediary(self) -> bool:
        """Check if user is an intermediary."""
        return self.role == UserRole.INTERMEDIARY

    @property
    def is_tenant(self) -> bool:
        """Check if user is a tenant."""
        return self.role == UserRole.TENANT
