"""Report template model for financial and tax reports.

Implements T222 from tasks.md.

Provides customizable report templates for:
- Annual income statements
- Expense deduction reports
- GST/VAT reports
- Profit & Loss statements
- Cash flow reports
"""
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, Enum, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..core.database import Base


class ReportType(str, PyEnum):
    """Report type enumeration."""
    
    # Tax reports
    TAX_INCOME = "tax_income"  # Annual income statement for tax filing
    TAX_DEDUCTIONS = "tax_deductions"  # Expense deductions report
    TAX_GST = "tax_gst"  # GST/VAT report
    
    # Financial reports
    PROFIT_LOSS = "profit_loss"  # Profit & Loss statement
    CASH_FLOW = "cash_flow"  # Cash flow report
    BALANCE_SHEET = "balance_sheet"  # Balance sheet
    
    # Operational reports
    RENT_COLLECTION = "rent_collection"  # Rent collection summary
    EXPENSE_BREAKDOWN = "expense_breakdown"  # Expense category breakdown
    OCCUPANCY = "occupancy"  # Occupancy rate report
    
    # Custom
    CUSTOM = "custom"  # User-defined custom report


class ReportPeriod(str, PyEnum):
    """Report period enumeration."""
    
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    CUSTOM = "custom"


class ReportFormat(str, PyEnum):
    """Report output format enumeration."""
    
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"


class ReportTemplate(Base):
    """Report template model for customizable financial and tax reports.
    
    Templates define:
    - Report structure and layout
    - Data sources and calculations
    - Formatting rules
    - Schedule and recurrence
    
    Features:
    - Predefined templates for common reports
    - Custom templates with user-defined configuration
    - Scheduled report generation
    - Multi-format output (PDF, Excel, CSV)
    """
    
    __tablename__ = "report_templates"
    
    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
        comment="Unique report template identifier",
    )
    
    # Template Information
    name = Column(
        String(255),
        nullable=False,
        comment="Template name (e.g., 'Annual Tax Statement 2024')",
    )
    description = Column(
        Text,
        nullable=True,
        comment="Template description and purpose",
    )
    report_type = Column(
        Enum(ReportType, name="report_type"),
        nullable=False,
        index=True,
        comment="Type of report (tax, financial, operational, custom)",
    )
    
    # Configuration
    config = Column(
        JSON,
        nullable=False,
        default={},
        comment="Report configuration (data sources, calculations, formatting)",
    )
    """
    Example config structure:
    {
        "data_sources": ["payments", "expenses", "bills"],
        "calculations": {
            "total_income": "SUM(payments.amount)",
            "total_expenses": "SUM(expenses.amount)",
            "net_profit": "total_income - total_expenses"
        },
        "filters": {
            "date_range": {"start": "2024-01-01", "end": "2024-12-31"},
            "property_ids": ["uuid1", "uuid2"]
        },
        "grouping": ["month", "property"],
        "formatting": {
            "currency": "INR",
            "locale": "en_IN",
            "decimal_places": 2
        },
        "sections": [
            {"title": "Income Summary", "type": "table", "data": "income_by_month"},
            {"title": "Expense Breakdown", "type": "chart", "chart_type": "pie"}
        ]
    }
    """
    
    # Schedule
    is_scheduled = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether report is auto-generated on schedule",
    )
    schedule_config = Column(
        JSON,
        nullable=True,
        comment="Schedule configuration (cron expression, period, recipients)",
    )
    """
    Example schedule_config:
    {
        "period": "monthly",
        "cron": "0 0 1 * *",  # First day of each month at midnight
        "recipients": ["owner@example.com", "accountant@example.com"],
        "formats": ["pdf", "excel"],
        "enabled": true
    }
    """
    
    # Output
    default_format = Column(
        Enum(ReportFormat, name="report_format"),
        nullable=False,
        default=ReportFormat.PDF,
        comment="Default output format",
    )
    
    # Ownership
    created_by = Column(
        UUID(as_uuid=True),
        nullable=False,
        comment="User who created the template",
    )
    is_public = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether template is available to all users",
    )
    is_system = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether template is a system-provided template",
    )
    
    # Status
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether template is active",
    )
    
    # Timestamps
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Template creation timestamp",
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Last update timestamp",
    )
    last_generated_at = Column(
        DateTime,
        nullable=True,
        comment="Last time report was generated from this template",
    )
    
    def __repr__(self) -> str:
        return f"<ReportTemplate(id={self.id}, name={self.name}, type={self.report_type})>"
    
    @property
    def is_tax_report(self) -> bool:
        """Check if this is a tax-related report."""
        return self.report_type in [
            ReportType.TAX_INCOME,
            ReportType.TAX_DEDUCTIONS,
            ReportType.TAX_GST,
        ]
    
    @property
    def is_financial_report(self) -> bool:
        """Check if this is a financial report."""
        return self.report_type in [
            ReportType.PROFIT_LOSS,
            ReportType.CASH_FLOW,
            ReportType.BALANCE_SHEET,
        ]


class GeneratedReport(Base):
    """Generated report instance model.
    
    Stores metadata and file references for generated reports.
    Actual report files are stored in S3 or local storage.
    """
    
    __tablename__ = "generated_reports"
    
    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
        comment="Unique generated report identifier",
    )
    
    # Template Reference
    template_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Template used to generate report (null for ad-hoc reports)",
    )
    
    # Report Information
    name = Column(
        String(255),
        nullable=False,
        comment="Generated report name",
    )
    report_type = Column(
        Enum(ReportType, name="report_type"),
        nullable=False,
        index=True,
        comment="Type of report",
    )
    period_start = Column(
        DateTime,
        nullable=True,
        comment="Report period start date",
    )
    period_end = Column(
        DateTime,
        nullable=True,
        comment="Report period end date",
    )
    
    # File Information
    file_url = Column(
        String(500),
        nullable=False,
        comment="URL to generated report file (S3 or local path)",
    )
    file_format = Column(
        Enum(ReportFormat, name="report_format"),
        nullable=False,
        comment="Report file format",
    )
    file_size = Column(
        String(50),
        nullable=True,
        comment="File size (human-readable, e.g., '1.2 MB')",
    )
    
    # Metadata
    generated_by = Column(
        UUID(as_uuid=True),
        nullable=False,
        comment="User who generated the report",
    )
    parameters = Column(
        JSON,
        nullable=True,
        comment="Parameters used to generate report",
    )
    
    # Sharing
    share_token = Column(
        String(100),
        nullable=True,
        unique=True,
        comment="Secure token for sharing report via link",
    )
    share_expires_at = Column(
        DateTime,
        nullable=True,
        comment="Share link expiration timestamp",
    )
    
    # Timestamps
    generated_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
        comment="Report generation timestamp",
    )
    accessed_at = Column(
        DateTime,
        nullable=True,
        comment="Last access timestamp",
    )
    
    def __repr__(self) -> str:
        return f"<GeneratedReport(id={self.id}, name={self.name}, type={self.report_type})>"
    
    @property
    def is_shared(self) -> bool:
        """Check if report has an active share link."""
        if not self.share_token or not self.share_expires_at:
            return False
        return datetime.utcnow() < self.share_expires_at
