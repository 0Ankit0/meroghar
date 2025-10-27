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
from .expense import Expense, ExpenseCategory, ExpenseStatus
from .sync import SyncLog, SyncStatus, SyncOperation
from .message import Message, MessageChannel, MessageStatus, MessageTemplate
from .document import Document, DocumentType, DocumentStatus

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
    # Expense
    "Expense",
    "ExpenseCategory",
    "ExpenseStatus",
    # Sync
    "SyncLog",
    "SyncStatus",
    "SyncOperation",
    # Message
    "Message",
    "MessageChannel",
    "MessageStatus",
    "MessageTemplate",
    # Document
    "Document",
    "DocumentType",
    "DocumentStatus",
]

