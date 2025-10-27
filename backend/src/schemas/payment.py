"""Payment request/response schemas.

Implements T059 from tasks.md.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from ..models.payment import PaymentMethod, PaymentStatus, PaymentType, TransactionStatus


# ==================== Request Schemas ====================


class PaymentCreateRequest(BaseModel):
    """Request schema for creating a payment."""

    tenant_id: UUID = Field(..., description="Tenant who made the payment")
    property_id: UUID = Field(..., description="Property for which payment was made")
    amount: Decimal = Field(..., gt=0, description="Payment amount")
    currency: str = Field(default="INR", max_length=3, description="Currency code (ISO 4217)")
    payment_method: PaymentMethod = Field(..., description="Payment method used")
    payment_type: PaymentType = Field(default=PaymentType.RENT, description="Type of payment")
    payment_date: date = Field(default_factory=date.today, description="Date payment was received")
    payment_period_start: Optional[date] = Field(None, description="Start of payment period (for rent)")
    payment_period_end: Optional[date] = Field(None, description="End of payment period (for rent)")
    transaction_reference: Optional[str] = Field(None, max_length=255, description="Transaction reference number")
    notes: Optional[str] = Field(None, description="Additional notes")

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Validate payment amount is positive."""
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v

    @field_validator('payment_period_end')
    @classmethod
    def validate_period_dates(cls, v: Optional[date], info) -> Optional[date]:
        """Validate period end date is after start date."""
        if v is not None and info.data.get('payment_period_start') is not None:
            if v <= info.data['payment_period_start']:
                raise ValueError('Payment period end must be after start date')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
                "property_id": "123e4567-e89b-12d3-a456-426614174001",
                "amount": 25000.00,
                "currency": "INR",
                "payment_method": "upi",
                "payment_type": "rent",
                "payment_date": "2025-10-27",
                "payment_period_start": "2025-10-01",
                "payment_period_end": "2025-10-31",
                "transaction_reference": "UPI-123456789",
                "notes": "Monthly rent for October 2025"
            }
        }


class PaymentUpdateRequest(BaseModel):
    """Request schema for updating a payment."""

    status: Optional[PaymentStatus] = Field(None, description="Payment status")
    notes: Optional[str] = Field(None, description="Additional notes")
    receipt_url: Optional[str] = Field(None, max_length=500, description="Receipt URL")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "completed",
                "notes": "Payment confirmed",
                "receipt_url": "https://storage.example.com/receipts/receipt-123.pdf"
            }
        }


# ==================== Response Schemas ====================


class PaymentResponse(BaseModel):
    """Response schema for payment details."""

    id: UUID
    tenant_id: UUID
    property_id: UUID
    recorded_by: Optional[UUID]
    amount: Decimal
    currency: str
    payment_method: PaymentMethod
    payment_type: PaymentType
    status: PaymentStatus
    payment_period_start: Optional[date]
    payment_period_end: Optional[date]
    transaction_reference: Optional[str]
    notes: Optional[str]
    receipt_url: Optional[str]
    payment_date: date
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174002",
                "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
                "property_id": "123e4567-e89b-12d3-a456-426614174001",
                "recorded_by": "123e4567-e89b-12d3-a456-426614174003",
                "amount": 25000.00,
                "currency": "INR",
                "payment_method": "upi",
                "payment_type": "rent",
                "status": "completed",
                "payment_period_start": "2025-10-01",
                "payment_period_end": "2025-10-31",
                "transaction_reference": "UPI-123456789",
                "notes": "Monthly rent for October 2025",
                "receipt_url": "https://storage.example.com/receipts/receipt-123.pdf",
                "payment_date": "2025-10-27",
                "created_at": "2025-10-27T09:00:00Z",
                "updated_at": "2025-10-27T09:00:00Z"
            }
        }


class PaymentListResponse(BaseModel):
    """Response schema for payment list."""

    payments: list[PaymentResponse]
    total: int
    skip: int
    limit: int

    class Config:
        json_schema_extra = {
            "example": {
                "payments": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174002",
                        "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
                        "amount": 25000.00,
                        "payment_method": "upi",
                        "payment_type": "rent",
                        "status": "completed",
                        "payment_date": "2025-10-27"
                    }
                ],
                "total": 1,
                "skip": 0,
                "limit": 50
            }
        }


class TenantBalanceResponse(BaseModel):
    """Response schema for tenant balance calculation."""

    tenant_id: UUID
    property_id: UUID
    total_paid: Decimal = Field(default=Decimal("0.00"), description="Total amount paid")
    total_due: Decimal = Field(default=Decimal("0.00"), description="Total amount due")
    outstanding_balance: Decimal = Field(default=Decimal("0.00"), description="Outstanding balance")
    last_payment_date: Optional[date] = Field(None, description="Date of last payment")
    last_payment_amount: Optional[Decimal] = Field(None, description="Amount of last payment")
    months_behind: int = Field(default=0, description="Number of months behind on rent")

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
                "property_id": "123e4567-e89b-12d3-a456-426614174001",
                "total_paid": 75000.00,
                "total_due": 100000.00,
                "outstanding_balance": 25000.00,
                "last_payment_date": "2025-09-27",
                "last_payment_amount": 25000.00,
                "months_behind": 1
            }
        }


class TransactionResponse(BaseModel):
    """Response schema for transaction details."""

    id: UUID
    payment_id: Optional[UUID]
    gateway_name: str
    gateway_transaction_id: str
    gateway_order_id: Optional[str]
    amount: Decimal
    currency: str
    status: TransactionStatus
    gateway_response: Optional[str]
    error_message: Optional[str]
    initiated_at: datetime
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174004",
                "payment_id": "123e4567-e89b-12d3-a456-426614174002",
                "gateway_name": "razorpay",
                "gateway_transaction_id": "pay_ABC123XYZ",
                "gateway_order_id": "order_XYZ789",
                "amount": 25000.00,
                "currency": "INR",
                "status": "success",
                "gateway_response": '{"id": "pay_ABC123XYZ", "status": "captured"}',
                "error_message": None,
                "initiated_at": "2025-10-27T09:00:00Z",
                "completed_at": "2025-10-27T09:00:10Z",
                "created_at": "2025-10-27T09:00:00Z",
                "updated_at": "2025-10-27T09:00:10Z"
            }
        }


# ==================== Export Schemas ====================

__all__ = [
    "PaymentCreateRequest",
    "PaymentUpdateRequest",
    "PaymentResponse",
    "PaymentListResponse",
    "TenantBalanceResponse",
    "TransactionResponse",
]
