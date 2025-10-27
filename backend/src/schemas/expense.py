"""Expense request/response schemas.

Implements T127 from tasks.md.
"""
from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from ..models.expense import ExpenseCategory, ExpenseStatus


class ExpenseCreateRequest(BaseModel):
    """Request schema for creating a new expense."""

    property_id: UUID = Field(..., description="Property ID where expense was incurred")
    amount: Decimal = Field(..., gt=0, description="Expense amount")
    currency: str = Field(default="NPR", max_length=3, description="Currency code")
    category: ExpenseCategory = Field(..., description="Expense category")
    description: str = Field(..., min_length=1, max_length=2000, description="Expense description")
    vendor_name: Optional[str] = Field(None, max_length=255, description="Vendor/service provider name")
    invoice_number: Optional[str] = Field(None, max_length=100, description="Invoice or receipt number")
    paid_by: str = Field(default="intermediary", max_length=100, description="Who paid for this expense")
    is_reimbursable: bool = Field(default=True, description="Whether expense is reimbursable")
    expense_date: date = Field(..., description="Date when expense was incurred")
    notes: Optional[str] = Field(None, max_length=2000, description="Additional notes")

    @field_validator('expense_date')
    @classmethod
    def validate_expense_date(cls, v: date) -> date:
        """Validate expense date is not in the future."""
        if v > date.today():
            raise ValueError("Expense date cannot be in the future")
        return v

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Validate amount has max 2 decimal places."""
        if v.as_tuple().exponent < -2:
            raise ValueError("Amount cannot have more than 2 decimal places")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "property_id": "123e4567-e89b-12d3-a456-426614174000",
                "amount": 5000.00,
                "currency": "NPR",
                "category": "maintenance",
                "description": "Plumbing repair for leaking pipe in bathroom",
                "vendor_name": "ABC Plumbing Services",
                "invoice_number": "INV-2024-001",
                "paid_by": "intermediary",
                "is_reimbursable": True,
                "expense_date": "2024-01-15",
                "notes": "Emergency repair required",
            }
        }
    }


class ExpenseUpdateRequest(BaseModel):
    """Request schema for updating an expense."""

    amount: Optional[Decimal] = Field(None, gt=0, description="Expense amount")
    category: Optional[ExpenseCategory] = Field(None, description="Expense category")
    description: Optional[str] = Field(None, min_length=1, max_length=2000)
    vendor_name: Optional[str] = Field(None, max_length=255)
    invoice_number: Optional[str] = Field(None, max_length=100)
    expense_date: Optional[date] = Field(None, description="Date when expense was incurred")
    notes: Optional[str] = Field(None, max_length=2000)

    @field_validator('expense_date')
    @classmethod
    def validate_expense_date(cls, v: Optional[date]) -> Optional[date]:
        """Validate expense date is not in the future."""
        if v and v > date.today():
            raise ValueError("Expense date cannot be in the future")
        return v


class ExpenseApprovalRequest(BaseModel):
    """Request schema for approving/rejecting an expense."""

    status: ExpenseStatus = Field(..., description="Approval status (approved/rejected)")
    rejection_reason: Optional[str] = Field(None, max_length=1000, description="Reason if rejected")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: ExpenseStatus) -> ExpenseStatus:
        """Validate status is either approved or rejected."""
        if v not in [ExpenseStatus.APPROVED, ExpenseStatus.REJECTED]:
            raise ValueError("Status must be either 'approved' or 'rejected'")
        return v

    @field_validator('rejection_reason')
    @classmethod
    def validate_rejection_reason(cls, v: Optional[str], info) -> Optional[str]:
        """Require rejection reason if status is rejected."""
        status = info.data.get('status')
        if status == ExpenseStatus.REJECTED and not v:
            raise ValueError("Rejection reason is required when rejecting an expense")
        return v


class ExpenseReimbursementRequest(BaseModel):
    """Request schema for marking expense as reimbursed."""

    reimbursed_date: date = Field(..., description="Date when reimbursement was made")

    @field_validator('reimbursed_date')
    @classmethod
    def validate_reimbursed_date(cls, v: date) -> date:
        """Validate reimbursed date is not in the future."""
        if v > date.today():
            raise ValueError("Reimbursed date cannot be in the future")
        return v


class ExpenseResponse(BaseModel):
    """Response schema for expense."""

    id: UUID
    property_id: UUID
    recorded_by: UUID
    approved_by: Optional[UUID]
    amount: Decimal
    currency: str
    category: ExpenseCategory
    status: ExpenseStatus
    description: str
    vendor_name: Optional[str]
    invoice_number: Optional[str]
    receipt_url: Optional[str]
    paid_by: str
    is_reimbursable: bool
    is_reimbursed: bool
    reimbursed_date: Optional[date]
    expense_date: date
    approved_date: Optional[date]
    created_at: str
    updated_at: str
    notes: Optional[str]
    rejection_reason: Optional[str]

    model_config = {"from_attributes": True}


class ExpenseListResponse(BaseModel):
    """Response schema for expense list with pagination."""

    total: int = Field(..., description="Total number of expenses")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    expenses: list[ExpenseResponse] = Field(..., description="List of expenses")


class ExpenseSummary(BaseModel):
    """Summary statistics for expenses."""

    total_expenses: int = Field(..., description="Total number of expenses")
    total_amount: Decimal = Field(..., description="Total expense amount")
    pending_amount: Decimal = Field(..., description="Amount pending approval")
    approved_amount: Decimal = Field(..., description="Amount approved")
    reimbursed_amount: Decimal = Field(..., description="Amount reimbursed")
    outstanding_amount: Decimal = Field(..., description="Amount approved but not reimbursed")
    by_category: dict[str, Decimal] = Field(..., description="Amount by category")


__all__ = [
    "ExpenseCreateRequest",
    "ExpenseUpdateRequest",
    "ExpenseApprovalRequest",
    "ExpenseReimbursementRequest",
    "ExpenseResponse",
    "ExpenseListResponse",
    "ExpenseSummary",
]
