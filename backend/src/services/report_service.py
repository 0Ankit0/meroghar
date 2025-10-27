"""Report service for generating financial and tax reports.

Implements T224, T234 from tasks.md.

Provides comprehensive tax and financial reporting capabilities including:
- Income statements (rental income aggregation)
- Expense deductions (categorized expenses)
- GST/VAT reports
- Profit & Loss statements
- Cash flow analysis
- Balance sheets
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from io import BytesIO
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID, uuid4
import secrets

from sqlalchemy import func, and_, or_, extract
from sqlalchemy.orm import Session

from ..models.payment import Payment, PaymentStatus, PaymentType
from ..models.expense import Expense, ExpenseStatus, ExpenseCategory
from ..models.bill import Bill, BillStatus
from ..models.property import Property
from ..models.tenant import Tenant
from ..models.user import User
from ..models.report import (
    ReportTemplate,
    GeneratedReport,
    ReportType,
    ReportPeriod,
    ReportFormat,
)


class ReportService:
    """Service for generating financial and tax reports."""

    # Tax-deductible expense categories
    TAX_DEDUCTIBLE_CATEGORIES = {
        ExpenseCategory.MAINTENANCE,
        ExpenseCategory.REPAIR,
        ExpenseCategory.INSURANCE,
        ExpenseCategory.TAXES,
        ExpenseCategory.LEGAL,
        ExpenseCategory.ADMINISTRATIVE,
    }

    def __init__(self, db: Session):
        self.db = db

    # ========== Tax Report Methods ==========

    def calculate_annual_income(
        self,
        user_id: UUID,
        year: int,
        property_ids: Optional[List[UUID]] = None,
    ) -> Dict[str, Any]:
        """Calculate total rental income for tax reporting.
        
        Implements T225 requirement from tasks.md.
        
        Args:
            user_id: Property owner user ID
            year: Tax year (e.g., 2024)
            property_ids: Optional list of property IDs to filter
            
        Returns:
            Dict with income breakdown including:
            - total_gross_income: Total rent received
            - income_by_property: Per-property breakdown
            - income_by_month: Monthly breakdown
            - security_deposits: Separate tracking
            - payment_method_breakdown: Cash vs electronic
        """
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)

        # Base query for payments
        query = (
            self.db.query(Payment)
            .join(Property, Payment.property_id == Property.id)
            .filter(
                Property.owner_id == user_id,
                Payment.status == PaymentStatus.COMPLETED,
                Payment.payment_date >= start_date,
                Payment.payment_date <= end_date,
            )
        )

        if property_ids:
            query = query.filter(Payment.property_id.in_(property_ids))

        payments = query.all()

        # Calculate totals
        total_rent = Decimal('0.00')
        total_security_deposits = Decimal('0.00')
        total_utilities = Decimal('0.00')
        total_other = Decimal('0.00')

        income_by_property: Dict[str, Dict[str, Any]] = {}
        income_by_month: Dict[int, Decimal] = {m: Decimal('0.00') for m in range(1, 13)}
        payment_method_breakdown: Dict[str, Decimal] = {}

        for payment in payments:
            amount = payment.amount

            # Categorize by payment type
            if payment.payment_type == PaymentType.RENT:
                total_rent += amount
            elif payment.payment_type == PaymentType.SECURITY_DEPOSIT:
                total_security_deposits += amount
            elif payment.payment_type == PaymentType.UTILITY:
                total_utilities += amount
            else:
                total_other += amount

            # By property
            prop_id = str(payment.property_id)
            if prop_id not in income_by_property:
                income_by_property[prop_id] = {
                    'property_name': payment.property.name if payment.property else 'Unknown',
                    'property_address': payment.property.address if payment.property else '',
                    'total_income': Decimal('0.00'),
                    'rent_income': Decimal('0.00'),
                    'utility_income': Decimal('0.00'),
                    'other_income': Decimal('0.00'),
                }
            
            income_by_property[prop_id]['total_income'] += amount
            if payment.payment_type == PaymentType.RENT:
                income_by_property[prop_id]['rent_income'] += amount
            elif payment.payment_type == PaymentType.UTILITY:
                income_by_property[prop_id]['utility_income'] += amount
            else:
                income_by_property[prop_id]['other_income'] += amount

            # By month
            if payment.payment_date:
                month = payment.payment_date.month
                income_by_month[month] += amount

            # By payment method
            method = payment.payment_method.value if payment.payment_method else 'unknown'
            payment_method_breakdown[method] = payment_method_breakdown.get(method, Decimal('0.00')) + amount

        total_gross_income = total_rent + total_utilities + total_other

        return {
            'year': year,
            'total_gross_income': float(total_gross_income),
            'total_rent_income': float(total_rent),
            'total_utility_income': float(total_utilities),
            'total_other_income': float(total_other),
            'security_deposits_received': float(total_security_deposits),
            'income_by_property': {
                k: {**v, 'total_income': float(v['total_income']), 
                    'rent_income': float(v['rent_income']),
                    'utility_income': float(v['utility_income']),
                    'other_income': float(v['other_income'])}
                for k, v in income_by_property.items()
            },
            'income_by_month': {k: float(v) for k, v in income_by_month.items()},
            'payment_method_breakdown': {k: float(v) for k, v in payment_method_breakdown.items()},
            'currency': 'NPR',  # Nepal Rupees
        }

    def calculate_deductible_expenses(
        self,
        user_id: UUID,
        year: int,
        property_ids: Optional[List[UUID]] = None,
    ) -> Dict[str, Any]:
        """Calculate tax-deductible expenses.
        
        Implements T226 requirement from tasks.md.
        
        Args:
            user_id: Property owner user ID
            year: Tax year
            property_ids: Optional property filter
            
        Returns:
            Dict with deductible expenses breakdown including:
            - total_deductible: Total deductible amount
            - by_category: Breakdown by expense category
            - by_property: Per-property breakdown
            - non_deductible_total: Non-deductible expenses
        """
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)

        # Query approved and reimbursed expenses
        query = (
            self.db.query(Expense)
            .join(Property, Expense.property_id == Property.id)
            .filter(
                Property.owner_id == user_id,
                Expense.status.in_([ExpenseStatus.APPROVED, ExpenseStatus.REIMBURSED]),
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date,
            )
        )

        if property_ids:
            query = query.filter(Expense.property_id.in_(property_ids))

        expenses = query.all()

        # Calculate totals
        total_deductible = Decimal('0.00')
        total_non_deductible = Decimal('0.00')
        by_category: Dict[str, Decimal] = {}
        by_property: Dict[str, Dict[str, Any]] = {}

        for expense in expenses:
            amount = expense.amount
            category = expense.category.value if expense.category else 'other'

            # Check if tax-deductible
            is_deductible = expense.category in self.TAX_DEDUCTIBLE_CATEGORIES

            if is_deductible:
                total_deductible += amount
                by_category[category] = by_category.get(category, Decimal('0.00')) + amount
            else:
                total_non_deductible += amount

            # By property
            prop_id = str(expense.property_id)
            if prop_id not in by_property:
                by_property[prop_id] = {
                    'property_name': expense.property.name if expense.property else 'Unknown',
                    'property_address': expense.property.address if expense.property else '',
                    'total_expenses': Decimal('0.00'),
                    'deductible_expenses': Decimal('0.00'),
                    'non_deductible_expenses': Decimal('0.00'),
                }
            
            by_property[prop_id]['total_expenses'] += amount
            if is_deductible:
                by_property[prop_id]['deductible_expenses'] += amount
            else:
                by_property[prop_id]['non_deductible_expenses'] += amount

        return {
            'year': year,
            'total_deductible': float(total_deductible),
            'total_non_deductible': float(total_non_deductible),
            'by_category': {k: float(v) for k, v in by_category.items()},
            'by_property': {
                k: {**v, 'total_expenses': float(v['total_expenses']),
                    'deductible_expenses': float(v['deductible_expenses']),
                    'non_deductible_expenses': float(v['non_deductible_expenses'])}
                for k, v in by_property.items()
            },
            'deductible_categories': [cat.value for cat in self.TAX_DEDUCTIBLE_CATEGORIES],
            'currency': 'NPR',
        }

    def calculate_gst_report(
        self,
        user_id: UUID,
        quarter: int,
        year: int,
        property_ids: Optional[List[UUID]] = None,
    ) -> Dict[str, Any]:
        """Calculate GST/VAT report for quarterly filing.
        
        Implements T227 requirement from tasks.md.
        
        Args:
            user_id: Property owner user ID
            quarter: Quarter number (1-4)
            year: Year
            property_ids: Optional property filter
            
        Returns:
            Dict with GST calculations including:
            - taxable_income: Income subject to GST
            - output_gst: GST collected on income
            - input_gst: GST paid on expenses
            - net_gst_payable: Amount to pay/refund
        """
        # Determine quarter date range
        quarter_starts = {1: 1, 2: 4, 3: 7, 4: 10}
        quarter_ends = {1: 3, 2: 6, 3: 9, 4: 12}
        
        start_month = quarter_starts[quarter]
        end_month = quarter_ends[quarter]
        
        start_date = date(year, start_month, 1)
        if end_month == 12:
            end_date = date(year, 12, 31)
        else:
            end_date = date(year, end_month + 1, 1) - timedelta(days=1)

        # GST rate for rental income in Nepal (13% as of 2024)
        GST_RATE = Decimal('0.13')

        # Calculate income (GST output)
        income_data = self.calculate_annual_income(user_id, year, property_ids)
        
        # Filter payments for this quarter
        query = (
            self.db.query(Payment)
            .join(Property, Payment.property_id == Property.id)
            .filter(
                Property.owner_id == user_id,
                Payment.status == PaymentStatus.COMPLETED,
                Payment.payment_date >= start_date,
                Payment.payment_date <= end_date,
                Payment.payment_type == PaymentType.RENT,  # GST typically on rent only
            )
        )

        if property_ids:
            query = query.filter(Payment.property_id.in_(property_ids))

        payments = query.all()
        taxable_income = sum(p.amount for p in payments)
        output_gst = taxable_income * GST_RATE

        # Calculate expenses (GST input)
        expense_query = (
            self.db.query(Expense)
            .join(Property, Expense.property_id == Property.id)
            .filter(
                Property.owner_id == user_id,
                Expense.status.in_([ExpenseStatus.APPROVED, ExpenseStatus.REIMBURSED]),
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date,
            )
        )

        if property_ids:
            expense_query = expense_query.filter(Expense.property_id.in_(property_ids))

        expenses = expense_query.all()
        taxable_expenses = sum(e.amount for e in expenses if e.gst_applicable)
        input_gst = taxable_expenses * GST_RATE

        net_gst = output_gst - input_gst

        return {
            'year': year,
            'quarter': quarter,
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat(),
            'gst_rate': float(GST_RATE),
            'taxable_income': float(taxable_income),
            'output_gst_collected': float(output_gst),
            'taxable_expenses': float(taxable_expenses),
            'input_gst_paid': float(input_gst),
            'net_gst_payable': float(net_gst),
            'currency': 'NPR',
        }

    # ========== Financial Report Methods ==========

    def generate_profit_loss_statement(
        self,
        user_id: UUID,
        start_date: date,
        end_date: date,
        property_ids: Optional[List[UUID]] = None,
    ) -> Dict[str, Any]:
        """Generate profit and loss statement.
        
        Implements T228 requirement from tasks.md.
        
        Args:
            user_id: Property owner user ID
            start_date: Period start
            end_date: Period end
            property_ids: Optional property filter
            
        Returns:
            P&L statement with revenue, expenses, and net profit
        """
        # Revenue
        payment_query = (
            self.db.query(Payment)
            .join(Property, Payment.property_id == Property.id)
            .filter(
                Property.owner_id == user_id,
                Payment.status == PaymentStatus.COMPLETED,
                Payment.payment_date >= start_date,
                Payment.payment_date <= end_date,
            )
        )

        if property_ids:
            payment_query = payment_query.filter(Payment.property_id.in_(property_ids))

        payments = payment_query.all()

        # Categorize revenue
        rental_income = sum(
            p.amount for p in payments if p.payment_type == PaymentType.RENT
        )
        utility_income = sum(
            p.amount for p in payments if p.payment_type == PaymentType.UTILITY
        )
        other_income = sum(
            p.amount for p in payments 
            if p.payment_type not in [PaymentType.RENT, PaymentType.UTILITY, PaymentType.SECURITY_DEPOSIT]
        )

        total_revenue = rental_income + utility_income + other_income

        # Expenses
        expense_query = (
            self.db.query(Expense)
            .join(Property, Expense.property_id == Property.id)
            .filter(
                Property.owner_id == user_id,
                Expense.status.in_([ExpenseStatus.APPROVED, ExpenseStatus.REIMBURSED]),
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date,
            )
        )

        if property_ids:
            expense_query = expense_query.filter(Expense.property_id.in_(property_ids))

        expenses = expense_query.all()

        # Categorize expenses
        expense_by_category: Dict[str, Decimal] = {}
        for expense in expenses:
            category = expense.category.value if expense.category else 'other'
            expense_by_category[category] = expense_by_category.get(category, Decimal('0.00')) + expense.amount

        total_expenses = sum(e.amount for e in expenses)

        # Calculate profit
        gross_profit = total_revenue
        operating_profit = total_revenue - total_expenses
        net_profit = operating_profit  # Can add tax deductions here

        return {
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat(),
            'revenue': {
                'rental_income': float(rental_income),
                'utility_income': float(utility_income),
                'other_income': float(other_income),
                'total_revenue': float(total_revenue),
            },
            'expenses': {
                'by_category': {k: float(v) for k, v in expense_by_category.items()},
                'total_expenses': float(total_expenses),
            },
            'profit': {
                'gross_profit': float(gross_profit),
                'operating_profit': float(operating_profit),
                'net_profit': float(net_profit),
            },
            'profit_margin': float((net_profit / total_revenue * 100) if total_revenue > 0 else 0),
            'currency': 'NPR',
        }

    def generate_cash_flow_report(
        self,
        user_id: UUID,
        start_date: date,
        end_date: date,
        property_ids: Optional[List[UUID]] = None,
    ) -> Dict[str, Any]:
        """Generate cash flow statement.
        
        Implements T229 requirement from tasks.md.
        
        Args:
            user_id: Property owner user ID
            start_date: Period start
            end_date: Period end
            property_ids: Optional property filter
            
        Returns:
            Cash flow statement with inflows, outflows, and net cash
        """
        # Cash inflows (payments received)
        payment_query = (
            self.db.query(Payment)
            .join(Property, Payment.property_id == Property.id)
            .filter(
                Property.owner_id == user_id,
                Payment.status == PaymentStatus.COMPLETED,
                Payment.payment_date >= start_date,
                Payment.payment_date <= end_date,
            )
        )

        if property_ids:
            payment_query = payment_query.filter(Payment.property_id.in_(property_ids))

        payments = payment_query.all()

        # Categorize cash inflows
        cash_from_operations = sum(
            p.amount for p in payments if p.payment_type in [PaymentType.RENT, PaymentType.UTILITY]
        )
        cash_from_deposits = sum(
            p.amount for p in payments if p.payment_type == PaymentType.SECURITY_DEPOSIT
        )
        other_cash_inflows = sum(
            p.amount for p in payments 
            if p.payment_type not in [PaymentType.RENT, PaymentType.UTILITY, PaymentType.SECURITY_DEPOSIT]
        )

        total_cash_inflow = cash_from_operations + cash_from_deposits + other_cash_inflows

        # Cash outflows (expenses paid)
        expense_query = (
            self.db.query(Expense)
            .join(Property, Expense.property_id == Property.id)
            .filter(
                Property.owner_id == user_id,
                Expense.status == ExpenseStatus.REIMBURSED,  # Only paid expenses
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date,
            )
        )

        if property_ids:
            expense_query = expense_query.filter(Expense.property_id.in_(property_ids))

        expenses = expense_query.all()

        # Categorize cash outflows
        operating_expenses = sum(
            e.amount for e in expenses 
            if e.category in [ExpenseCategory.MAINTENANCE, ExpenseCategory.REPAIR, 
                             ExpenseCategory.CLEANING, ExpenseCategory.UTILITIES]
        )
        administrative_expenses = sum(
            e.amount for e in expenses
            if e.category in [ExpenseCategory.ADMINISTRATIVE, ExpenseCategory.LEGAL]
        )
        other_expenses = sum(
            e.amount for e in expenses
            if e.category not in [ExpenseCategory.MAINTENANCE, ExpenseCategory.REPAIR,
                                 ExpenseCategory.CLEANING, ExpenseCategory.UTILITIES,
                                 ExpenseCategory.ADMINISTRATIVE, ExpenseCategory.LEGAL]
        )

        total_cash_outflow = operating_expenses + administrative_expenses + other_expenses

        # Net cash flow
        net_cash_flow = total_cash_inflow - total_cash_outflow

        return {
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat(),
            'cash_inflows': {
                'from_operations': float(cash_from_operations),
                'from_deposits': float(cash_from_deposits),
                'other_inflows': float(other_cash_inflows),
                'total_inflows': float(total_cash_inflow),
            },
            'cash_outflows': {
                'operating_expenses': float(operating_expenses),
                'administrative_expenses': float(administrative_expenses),
                'other_expenses': float(other_expenses),
                'total_outflows': float(total_cash_outflow),
            },
            'net_cash_flow': float(net_cash_flow),
            'currency': 'NPR',
        }

    # ========== Report Generation and Sharing ==========

    def create_report_template(
        self,
        name: str,
        description: str,
        report_type: ReportType,
        config: Dict[str, Any],
        created_by: UUID,
        is_scheduled: bool = False,
        schedule_config: Optional[Dict[str, Any]] = None,
        default_format: ReportFormat = ReportFormat.PDF,
    ) -> ReportTemplate:
        """Create a new report template.
        
        Args:
            name: Template name
            description: Template description
            report_type: Type of report
            config: Template configuration (fields, filters, formatting)
            created_by: User ID who created the template
            is_scheduled: Whether to auto-generate on schedule
            schedule_config: Schedule configuration (cron, recipients)
            default_format: Default output format
            
        Returns:
            Created ReportTemplate instance
        """
        template = ReportTemplate(
            id=uuid4(),
            name=name,
            description=description,
            report_type=report_type,
            config=config,
            is_scheduled=is_scheduled,
            schedule_config=schedule_config,
            default_format=default_format,
            created_by=created_by,
            is_system=False,
            is_active=True,
        )
        
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        
        return template

    def generate_report(
        self,
        template_id: UUID,
        generated_by: UUID,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> GeneratedReport:
        """Generate a report from a template.
        
        Implements T230 requirement from tasks.md.
        
        Args:
            template_id: Report template ID
            generated_by: User ID generating the report
            parameters: Report parameters (date ranges, filters, etc.)
            
        Returns:
            GeneratedReport instance with file URL
        """
        template = self.db.query(ReportTemplate).filter(
            ReportTemplate.id == template_id
        ).first()
        
        if not template:
            raise ValueError("Report template not found")

        # Extract parameters
        params = parameters or {}
        period_start = params.get('period_start')
        period_end = params.get('period_end')
        file_format = params.get('format', template.default_format)

        # Generate report data based on type
        if template.report_type == ReportType.TAX_INCOME:
            year = params.get('year', datetime.now().year)
            report_data = self.calculate_annual_income(generated_by, year)
        elif template.report_type == ReportType.TAX_DEDUCTIONS:
            year = params.get('year', datetime.now().year)
            report_data = self.calculate_deductible_expenses(generated_by, year)
        elif template.report_type == ReportType.TAX_GST:
            year = params.get('year', datetime.now().year)
            quarter = params.get('quarter', 1)
            report_data = self.calculate_gst_report(generated_by, quarter, year)
        elif template.report_type == ReportType.PROFIT_LOSS:
            report_data = self.generate_profit_loss_statement(
                generated_by, period_start, period_end
            )
        elif template.report_type == ReportType.CASH_FLOW:
            report_data = self.generate_cash_flow_report(
                generated_by, period_start, period_end
            )
        else:
            raise ValueError(f"Unsupported report type: {template.report_type}")

        # Generate file (placeholder - actual implementation would use export service)
        file_url = f"/reports/{uuid4()}.{file_format.value}"
        file_size = "1.2 MB"  # Placeholder

        # Create generated report record
        generated_report = GeneratedReport(
            id=uuid4(),
            template_id=template_id,
            name=f"{template.name} - {datetime.now().strftime('%Y-%m-%d')}",
            report_type=template.report_type,
            period_start=period_start,
            period_end=period_end,
            file_url=file_url,
            file_format=file_format,
            file_size=file_size,
            generated_by=generated_by,
            parameters=parameters,
        )

        self.db.add(generated_report)
        
        # Update template's last_generated_at
        template.last_generated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(generated_report)

        return generated_report

    def generate_share_token(
        self,
        report_id: UUID,
        expires_in_days: int = 7,
    ) -> str:
        """Generate a secure share link token for a report.
        
        Implements T234 requirement from tasks.md.
        
        Args:
            report_id: Generated report ID
            expires_in_days: Token validity in days
            
        Returns:
            Secure share token
        """
        report = self.db.query(GeneratedReport).filter(
            GeneratedReport.id == report_id
        ).first()

        if not report:
            raise ValueError("Report not found")

        # Generate secure token
        token = secrets.token_urlsafe(32)
        
        # Set expiration
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        # Update report
        report.share_token = token
        report.share_expires_at = expires_at

        self.db.commit()

        return token

    def verify_share_token(self, token: str) -> Optional[GeneratedReport]:
        """Verify a share token and return the report if valid.
        
        Args:
            token: Share token to verify
            
        Returns:
            GeneratedReport if valid, None otherwise
        """
        report = self.db.query(GeneratedReport).filter(
            GeneratedReport.share_token == token
        ).first()

        if not report:
            return None

        # Check expiration
        if report.share_expires_at and report.share_expires_at < datetime.utcnow():
            return None

        # Update accessed_at
        report.accessed_at = datetime.utcnow()
        self.db.commit()

        return report
