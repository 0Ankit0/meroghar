"""
Database models package.

This module imports all models to ensure they are registered with SQLAlchemy
and can be discovered by Alembic for migration generation.

All model files should be imported here.
"""

# Phase 3 - User Story 1 Models
from .bill import (AllocationMethod, Bill, BillAllocation, BillStatus,
                   BillType, RecurringBill, RecurringFrequency)
from .document import Document, DocumentStatus, DocumentType
from .expense import Expense, ExpenseCategory, ExpenseStatus
from .message import Message, MessageChannel, MessageStatus, MessageTemplate
from .notification import Notification, NotificationPriority, NotificationType
from .payment import Payment, PaymentMethod, PaymentStatus, PaymentType
from .property import Property, PropertyAssignment
from .sync import SyncLog, SyncOperation, SyncStatus
from .tenant import Tenant, TenantStatus
from .user import User, UserRole

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
    # Notification
    "Notification",
    "NotificationType",
    "NotificationPriority",
]
