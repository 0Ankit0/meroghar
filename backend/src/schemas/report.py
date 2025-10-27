"""Report schemas for API requests and responses.

Implements report-related schemas for T225-T230 from tasks.md.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ..models.report import ReportFormat, ReportType

# ========== Tax Report Schemas ==========


class AnnualIncomeReport(BaseModel):
    """Annual income report for tax purposes."""

    year: int = Field(..., description="Tax year")
    total_gross_income: Decimal = Field(..., description="Total gross income")
    total_rent_income: Decimal = Field(..., description="Rent income only")
    total_utility_income: Decimal = Field(..., description="Utility income")
    total_other_income: Decimal = Field(..., description="Other income")
    security_deposits_received: Decimal = Field(..., description="Security deposits (not taxable)")
    income_by_property: dict[str, dict[str, Any]] = Field(..., description="Per-property breakdown")
    income_by_month: dict[int, Decimal] = Field(..., description="Monthly breakdown")
    payment_method_breakdown: dict[str, Decimal] = Field(..., description="By payment method")
    currency: str = Field(default="NPR", description="Currency code")

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class DeductibleExpensesReport(BaseModel):
    """Tax-deductible expenses report."""

    year: int = Field(..., description="Tax year")
    total_deductible: Decimal = Field(..., description="Total deductible expenses")
    total_non_deductible: Decimal = Field(..., description="Non-deductible expenses")
    by_category: dict[str, Decimal] = Field(..., description="Breakdown by category")
    by_property: dict[str, dict[str, Any]] = Field(..., description="Per-property breakdown")
    deductible_categories: list[str] = Field(..., description="List of deductible categories")
    currency: str = Field(default="NPR", description="Currency code")

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class GSTReport(BaseModel):
    """GST/VAT quarterly report."""

    year: int = Field(..., description="Year")
    quarter: int = Field(..., ge=1, le=4, description="Quarter (1-4)")
    period_start: str = Field(..., description="Period start date")
    period_end: str = Field(..., description="Period end date")
    gst_rate: Decimal = Field(..., description="GST rate applied")
    taxable_income: Decimal = Field(..., description="Income subject to GST")
    output_gst_collected: Decimal = Field(..., description="GST collected on income")
    taxable_expenses: Decimal = Field(..., description="Expenses with GST")
    input_gst_paid: Decimal = Field(..., description="GST paid on expenses")
    net_gst_payable: Decimal = Field(..., description="Net GST to pay (or refund if negative)")
    currency: str = Field(default="NPR", description="Currency code")

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


# ========== Financial Report Schemas ==========


class ProfitLossStatement(BaseModel):
    """Profit and loss statement."""

    period_start: str = Field(..., description="Period start date")
    period_end: str = Field(..., description="Period end date")
    revenue: dict[str, Decimal] = Field(..., description="Revenue breakdown")
    expenses: dict[str, Any] = Field(..., description="Expense breakdown")
    profit: dict[str, Decimal] = Field(..., description="Profit calculations")
    profit_margin: Decimal = Field(..., description="Net profit margin percentage")
    currency: str = Field(default="NPR", description="Currency code")

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class CashFlowStatement(BaseModel):
    """Cash flow statement."""

    period_start: str = Field(..., description="Period start date")
    period_end: str = Field(..., description="Period end date")
    cash_inflows: dict[str, Decimal] = Field(..., description="Cash inflows")
    cash_outflows: dict[str, Decimal] = Field(..., description="Cash outflows")
    net_cash_flow: Decimal = Field(..., description="Net cash flow")
    currency: str = Field(default="NPR", description="Currency code")

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


# ========== Report Template Schemas ==========


class ReportTemplateBase(BaseModel):
    """Base schema for report templates."""

    name: str = Field(..., min_length=1, max_length=255, description="Template name")
    description: str | None = Field(None, description="Template description")
    report_type: ReportType = Field(..., description="Type of report")
    config: dict[str, Any] = Field(default_factory=dict, description="Template configuration")
    is_scheduled: bool = Field(default=False, description="Auto-generate on schedule")
    schedule_config: dict[str, Any] | None = Field(None, description="Schedule configuration")
    default_format: ReportFormat = Field(
        default=ReportFormat.PDF, description="Default output format"
    )


class ReportTemplateCreate(ReportTemplateBase):
    """Schema for creating a report template."""

    pass


class ReportTemplateUpdate(BaseModel):
    """Schema for updating a report template."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    config: dict[str, Any] | None = None
    is_scheduled: bool | None = None
    schedule_config: dict[str, Any] | None = None
    default_format: ReportFormat | None = None
    is_active: bool | None = None


class ReportTemplateResponse(ReportTemplateBase):
    """Schema for report template response."""

    id: UUID = Field(..., description="Template ID")
    created_by: UUID = Field(..., description="Creator user ID")
    is_public: bool = Field(..., description="Available to all users")
    is_system: bool = Field(..., description="System-provided template")
    is_active: bool = Field(..., description="Template is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_generated_at: datetime | None = Field(None, description="Last generation time")

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


# ========== Generated Report Schemas ==========


class ReportGenerateRequest(BaseModel):
    """Request schema for generating a report."""

    template_id: UUID | None = Field(None, description="Report template ID (optional)")
    report_type: ReportType | None = Field(None, description="Report type (if no template)")
    period_start: date | None = Field(None, description="Period start date")
    period_end: date | None = Field(None, description="Period end date")
    year: int | None = Field(None, description="Year for annual reports")
    quarter: int | None = Field(None, ge=1, le=4, description="Quarter for GST reports")
    property_ids: list[UUID] | None = Field(None, description="Filter by properties")
    format: ReportFormat = Field(default=ReportFormat.PDF, description="Output format")
    parameters: dict[str, Any] | None = Field(None, description="Additional parameters")


class GeneratedReportResponse(BaseModel):
    """Schema for generated report response."""

    id: UUID = Field(..., description="Report ID")
    template_id: UUID | None = Field(None, description="Template used")
    name: str = Field(..., description="Report name")
    report_type: ReportType = Field(..., description="Report type")
    period_start: date | None = Field(None, description="Period start")
    period_end: date | None = Field(None, description="Period end")
    file_url: str = Field(..., description="File download URL")
    file_format: ReportFormat = Field(..., description="File format")
    file_size: str | None = Field(None, description="File size")
    generated_by: UUID = Field(..., description="Generator user ID")
    parameters: dict[str, Any] | None = Field(None, description="Generation parameters")
    share_token: str | None = Field(None, description="Share token")
    share_expires_at: datetime | None = Field(None, description="Share expiration")
    generated_at: datetime = Field(..., description="Generation timestamp")
    accessed_at: datetime | None = Field(None, description="Last access timestamp")

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class ShareLinkRequest(BaseModel):
    """Request schema for creating a share link."""

    expires_in_days: int = Field(default=7, ge=1, le=90, description="Token validity in days")


class ShareLinkResponse(BaseModel):
    """Response schema for share link."""

    share_token: str = Field(..., description="Share token")
    share_url: str = Field(..., description="Full share URL")
    expires_at: datetime = Field(..., description="Expiration timestamp")


# ========== Report Scheduling Schemas ==========


class ReportScheduleRequest(BaseModel):
    """Request schema for scheduling a report."""

    template_id: UUID = Field(..., description="Report template to schedule")
    schedule_config: dict[str, Any] = Field(
        ..., description="Schedule configuration (cron, frequency, recipients)"
    )
    is_active: bool = Field(default=True, description="Schedule is active")


class ReportScheduleResponse(BaseModel):
    """Response schema for scheduled report."""

    template_id: UUID = Field(..., description="Template ID")
    schedule_config: dict[str, Any] = Field(..., description="Schedule configuration")
    is_scheduled: bool = Field(..., description="Scheduling enabled")
    last_generated_at: datetime | None = Field(None, description="Last generation")
    next_run_at: datetime | None = Field(None, description="Next scheduled run")

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
