"""
Database models package.

This module imports all models to ensure they are registered with SQLAlchemy
and can be discovered by Alembic for migration generation.

All model files should be imported here.
"""

# Phase 3 - User Story 1 Models
from .user import User, UserRole
from .property import Property, PropertyAssignment
from .tenant import Tenant, TenantStatus
from .payment import Payment, PaymentMethod, PaymentType
from .bill import BillAllocation

__all__ = [
    # User
    "User",
    "UserRole",
    # Property
    "Property",
    "PropertyAssignment",
    # Tenant
    "Tenant",
    "TenantStatus",
    # Payment (stub for relationships)
    "Payment",
    "PaymentMethod",
    "PaymentType",
    # Bill (stub for relationships)
    "BillAllocation",
]

