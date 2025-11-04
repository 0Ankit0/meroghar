"""
Application-wide constants for Meroghar Backend API

This module contains all constants used throughout the backend application
for easy maintenance and configuration management.
"""

from enum import Enum


# ==================== User Roles ====================
class UserRole(str, Enum):
    """User role types."""
    OWNER = "OWNER"
    INTERMEDIARY = "INTERMEDIARY"
    TENANT = "TENANT"


# ==================== Payment Methods ====================
class PaymentMethod(str, Enum):
    """Payment method types."""
    CASH = "CASH"
    BANK_TRANSFER = "BANK_TRANSFER"
    UPI = "UPI"
    CARD = "CARD"
    KHALTI = "KHALTI"
    ESEWA = "ESEWA"
    IMEPAY = "IMEPAY"
    ONLINE = "ONLINE"


# ==================== Payment Status ====================
class PaymentStatus(str, Enum):
    """Payment status types."""
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
    PROCESSING = "PROCESSING"


# ==================== Bill Types ====================
class BillType(str, Enum):
    """Bill category types."""
    ELECTRICITY = "ELECTRICITY"
    WATER = "WATER"
    GAS = "GAS"
    INTERNET = "INTERNET"
    MAINTENANCE = "MAINTENANCE"
    OTHER = "OTHER"


# ==================== Bill Allocation Method ====================
class BillAllocationMethod(str, Enum):
    """Methods for dividing bills among tenants."""
    PERCENTAGE = "PERCENTAGE"
    FIXED_AMOUNT = "FIXED_AMOUNT"
    EQUAL = "EQUAL"


# ==================== Expense Categories ====================
class ExpenseCategory(str, Enum):
    """Expense category types."""
    MAINTENANCE = "MAINTENANCE"
    REPAIR = "REPAIR"
    CLEANING = "CLEANING"
    UTILITIES = "UTILITIES"
    TAX = "TAX"
    INSURANCE = "INSURANCE"
    LEGAL = "LEGAL"
    MARKETING = "MARKETING"
    OTHER = "OTHER"


# ==================== Expense Status ====================
class ExpenseStatus(str, Enum):
    """Expense approval status."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


# ==================== Document Types ====================
class DocumentType(str, Enum):
    """Document category types."""
    LEASE = "LEASE"
    ID_PROOF = "ID_PROOF"
    ADDRESS_PROOF = "ADDRESS_PROOF"
    NOC = "NOC"
    RECEIPT = "RECEIPT"
    AGREEMENT = "AGREEMENT"
    INVOICE = "INVOICE"
    OTHER = "OTHER"


# ==================== Notification Types ====================
class NotificationType(str, Enum):
    """Notification category types."""
    PAYMENT = "PAYMENT"
    BILL = "BILL"
    MESSAGE = "MESSAGE"
    REMINDER = "REMINDER"
    ANNOUNCEMENT = "ANNOUNCEMENT"
    ALERT = "ALERT"
    SYSTEM = "SYSTEM"


# ==================== Message Types ====================
class MessageType(str, Enum):
    """Message delivery types."""
    SMS = "SMS"
    EMAIL = "EMAIL"
    WHATSAPP = "WHATSAPP"
    PUSH = "PUSH"
    IN_APP = "IN_APP"


# ==================== Message Status ====================
class MessageStatus(str, Enum):
    """Message delivery status."""
    PENDING = "PENDING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    READ = "READ"


# ==================== Sync Status ====================
class SyncStatus(str, Enum):
    """Data synchronization status."""
    SYNCED = "SYNCED"
    PENDING = "PENDING"
    FAILED = "FAILED"
    CONFLICT = "CONFLICT"


# ==================== Report Types ====================
class ReportType(str, Enum):
    """Report category types."""
    PAYMENT = "PAYMENT"
    EXPENSE = "EXPENSE"
    INCOME = "INCOME"
    TAX = "TAX"
    OCCUPANCY = "OCCUPANCY"
    FINANCIAL = "FINANCIAL"
    ANALYTICS = "ANALYTICS"


# ==================== Export Formats ====================
class ExportFormat(str, Enum):
    """Export file formats."""
    PDF = "PDF"
    EXCEL = "EXCEL"
    CSV = "CSV"
    JSON = "JSON"


# ==================== Rent Increment Types ====================
class RentIncrementType(str, Enum):
    """Rent increment calculation method."""
    PERCENTAGE = "PERCENTAGE"
    FIXED_AMOUNT = "FIXED_AMOUNT"


# ==================== Property Status ====================
class PropertyStatus(str, Enum):
    """Property operational status."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"


# ==================== Tenant Status ====================
class TenantStatus(str, Enum):
    """Tenant occupancy status."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    PENDING = "PENDING"
    TERMINATED = "TERMINATED"


# ==================== Currency Codes ====================
class Currency(str, Enum):
    """Supported currency codes."""
    INR = "INR"  # Indian Rupee
    NPR = "NPR"  # Nepalese Rupee
    USD = "USD"  # US Dollar
    EUR = "EUR"  # Euro
    GBP = "GBP"  # British Pound


# ==================== Validation Constants ====================
class ValidationLimits:
    """Validation limits for various fields."""
    
    # Text field lengths
    NAME_MIN_LENGTH = 2
    NAME_MAX_LENGTH = 100
    EMAIL_MAX_LENGTH = 255
    PHONE_MIN_LENGTH = 10
    PHONE_MAX_LENGTH = 15
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_MAX_LENGTH = 128
    DESCRIPTION_MAX_LENGTH = 500
    
    # File sizes (in bytes)
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
    MAX_DOCUMENT_SIZE = 20 * 1024 * 1024  # 20 MB
    
    # Numeric limits
    MIN_AMOUNT = 0.01
    MAX_AMOUNT = 10000000.0
    MIN_PERCENTAGE = 0.0
    MAX_PERCENTAGE = 100.0
    
    # Pagination
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100


# ==================== Date Formats ====================
class DateFormats:
    """Date format strings."""
    API_DATE = "%Y-%m-%d"
    API_DATETIME = "%Y-%m-%dT%H:%M:%SZ"
    DISPLAY_DATE = "%d/%m/%Y"
    DISPLAY_DATETIME = "%d/%m/%Y %H:%M"


# ==================== API Response Messages ====================
class ResponseMessages:
    """Standard API response messages."""
    
    # Success messages
    SUCCESS = "Operation completed successfully"
    CREATED = "Resource created successfully"
    UPDATED = "Resource updated successfully"
    DELETED = "Resource deleted successfully"
    LOGIN_SUCCESS = "Login successful"
    LOGOUT_SUCCESS = "Logout successful"
    PAYMENT_SUCCESS = "Payment completed successfully"
    
    # Error messages
    NOT_FOUND = "Resource not found"
    UNAUTHORIZED = "Unauthorized access"
    FORBIDDEN = "Access forbidden"
    BAD_REQUEST = "Invalid request data"
    VALIDATION_ERROR = "Validation error"
    SERVER_ERROR = "Internal server error"
    DUPLICATE_ENTRY = "Resource already exists"
    
    # Authentication
    INVALID_CREDENTIALS = "Invalid email or password"
    TOKEN_EXPIRED = "Token has expired"
    TOKEN_INVALID = "Invalid token"
    
    # Payment
    PAYMENT_FAILED = "Payment processing failed"
    INSUFFICIENT_BALANCE = "Insufficient balance"
    
    # File upload
    FILE_TOO_LARGE = "File size exceeds maximum limit"
    INVALID_FILE_TYPE = "Invalid file type"


# ==================== Regex Patterns ====================
class RegexPatterns:
    """Regular expression patterns for validation."""
    EMAIL = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    PHONE = r'^\+?[\d\s-]{10,15}$'
    NUMBER = r'^\d+$'
    DECIMAL = r'^\d+\.?\d{0,2}$'


# ==================== Database Constants ====================
class DatabaseConstants:
    """Database-related constants."""
    
    # Table names
    USERS = "users"
    PROPERTIES = "properties"
    PROPERTY_ASSIGNMENTS = "property_assignments"
    TENANTS = "tenants"
    PAYMENTS = "payments"
    BILLS = "bills"
    BILL_ALLOCATIONS = "bill_allocations"
    EXPENSES = "expenses"
    DOCUMENTS = "documents"
    MESSAGES = "messages"
    NOTIFICATIONS = "notifications"
    REPORTS = "reports"
    SYNC_LOGS = "sync_logs"
    
    # Common field names
    ID = "id"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    DELETED_AT = "deleted_at"
    IS_ACTIVE = "is_active"


# ==================== Cache Keys ====================
class CacheKeys:
    """Redis cache key patterns."""
    USER_PREFIX = "user:"
    PROPERTY_PREFIX = "property:"
    TENANT_PREFIX = "tenant:"
    PAYMENT_PREFIX = "payment:"
    BILL_PREFIX = "bill:"
    SESSION_PREFIX = "session:"
    
    @staticmethod
    def user(user_id: str) -> str:
        """Generate cache key for user."""
        return f"{CacheKeys.USER_PREFIX}{user_id}"
    
    @staticmethod
    def property(property_id: str) -> str:
        """Generate cache key for property."""
        return f"{CacheKeys.PROPERTY_PREFIX}{property_id}"
    
    @staticmethod
    def tenant(tenant_id: str) -> str:
        """Generate cache key for tenant."""
        return f"{CacheKeys.TENANT_PREFIX}{tenant_id}"


# ==================== Celery Task Names ====================
class CeleryTasks:
    """Celery task identifiers."""
    SEND_EMAIL = "tasks.send_email"
    SEND_SMS = "tasks.send_sms"
    SEND_WHATSAPP = "tasks.send_whatsapp"
    SEND_NOTIFICATION = "tasks.send_notification"
    GENERATE_REPORT = "tasks.generate_report"
    PROCESS_PAYMENT = "tasks.process_payment"
    SYNC_DATA = "tasks.sync_data"
    CALCULATE_RENT_INCREMENT = "tasks.calculate_rent_increment"
    SEND_RENT_REMINDER = "tasks.send_rent_reminder"


# ==================== HTTP Status Codes ====================
class HTTPStatus:
    """Common HTTP status codes."""
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    INTERNAL_SERVER_ERROR = 500


# ==================== Supported Languages ====================
SUPPORTED_LANGUAGES = [
    {"code": "en", "name": "English", "native_name": "English"},
    {"code": "hi", "name": "Hindi", "native_name": "हिन्दी"},
    {"code": "ne", "name": "Nepali", "native_name": "नेपाली"},
    {"code": "es", "name": "Spanish", "native_name": "Español"},
]


# ==================== Supported Currencies ====================
SUPPORTED_CURRENCIES = [
    {"code": "INR", "symbol": "₹", "name": "Indian Rupee"},
    {"code": "NPR", "symbol": "रू", "name": "Nepalese Rupee"},
    {"code": "USD", "symbol": "$", "name": "US Dollar"},
    {"code": "EUR", "symbol": "€", "name": "Euro"},
    {"code": "GBP", "symbol": "£", "name": "British Pound"},
]


# ==================== Payment Gateway URLs ====================
class PaymentGatewayURLs:
    """Payment gateway API endpoints."""
    
    # Khalti (Nepal)
    KHALTI_SANDBOX = "https://a.khalti.com/api/v2"
    KHALTI_PRODUCTION = "https://khalti.com/api/v2"
    
    # eSewa (Nepal)
    ESEWA_SANDBOX = "https://uat.esewa.com.np/epay"
    ESEWA_PRODUCTION = "https://esewa.com.np/epay"
    
    # IME Pay (Nepal)
    IMEPAY_SANDBOX = "https://stg.imepay.com.np:7979/api"
    IMEPAY_PRODUCTION = "https://payment.imepay.com.np/api"


# ==================== File Upload Settings ====================
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"]
ALLOWED_DOCUMENT_TYPES = ["application/pdf", "image/jpeg", "image/png"]
ALLOWED_EXTENSIONS = {
    "images": [".jpg", ".jpeg", ".png", ".webp"],
    "documents": [".pdf", ".jpg", ".jpeg", ".png"],
}


# ==================== Default Values ====================
class Defaults:
    """Default values for various settings."""
    LANGUAGE = "en"
    CURRENCY = "INR"
    PAGE_SIZE = 20
    RENT_REMINDER_DAYS_BEFORE = [7, 3, 0]  # Days before due date
    SYNC_INTERVAL_MINUTES = 15
    TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7
