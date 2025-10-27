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
from .payment import Payment, PaymentMethod, PaymentType, PaymentStatus
from .bill import (
    Bill,
    BillAllocation,
    RecurringBill,
    BillType,
    BillStatus,
    AllocationMethod,
    RecurringFrequency,
)

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
    # Payment
    "Payment",
    "PaymentMethod",
    "PaymentType",
    "PaymentStatus",
    # Bill
    "Bill",
    "BillAllocation",
    "RecurringBill",
    "BillType",
    "BillStatus",
    "AllocationMethod",
    "RecurringFrequency",
]

