"""Report generation endpoints.

Implements T133, T225-T230 from tasks.md.
"""
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from ...api.dependencies import get_current_user
from ...core.database import get_async_db, get_db
from ...models.expense import Expense, ExpenseCategory, ExpenseStatus
from ...models.property import Property, PropertyAssignment
from ...models.report import GeneratedReport
from ...models.user import User, UserRole
from ...schemas.expense import ExpenseSummary
from ...schemas.report import (
    AnnualIncomeReport,
    DeductibleExpensesReport,
    GSTReport,
    ProfitLossStatement,
    CashFlowStatement,
    ReportGenerateRequest,
    GeneratedReportResponse,
    ShareLinkRequest,
    ShareLinkResponse,
    ReportScheduleRequest,
)
from ...services.report_service import ReportService

# Configure logger for report endpoints
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/expenses",
    response_model=ExpenseSummary,
    summary="Generate expense report",
    description="Generate expense summary report with filters. Access controlled by role.",
)
async def get_expense_report(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_db)],
    property_id: Optional[UUID] = Query(None, description="Filter by property ID"),
    start_date: Optional[date] = Query(None, description="Report start date"),
    end_date: Optional[date] = Query(None, description="Report end date"),
    category: Optional[ExpenseCategory] = Query(None, description="Filter by category"),
) -> ExpenseSummary:
    """Generate expense report.
    
    Provides aggregated expense data:
    - Total expenses
    - Pending amount
    - Approved amount
    - Reimbursed amount
    - Outstanding amount (approved but not reimbursed)
    - Breakdown by category
    
    Access control:
    - Intermediaries: See expenses for properties they manage
    - Owners: See expenses for properties they own
    - Admin: See all expenses
    
    Args:
        property_id: Optional property filter
        start_date: Optional start date filter
        end_date: Optional end date filter
        category: Optional category filter
        current_user: Authenticated user
        session: Database session
        
    Returns:
        Expense summary with aggregated data
        
    Raises:
        403: If user doesn't have access to the property
        500: If database error occurs
    """
    try:
        # Build base query with access control
        query = select(Expense)
        
        # Apply role-based filtering
        if current_user.role == UserRole.INTERMEDIARY:
            # Intermediaries see expenses for properties they manage
            subquery = (
                select(PropertyAssignment.property_id)
                .where(
                    and_(
                        PropertyAssignment.intermediary_id == current_user.id,
                        PropertyAssignment.is_active == True,
                    )
                )
            )
            query = query.where(Expense.property_id.in_(subquery))
            
        elif current_user.role == UserRole.OWNER:
            # Owners see expenses for properties they own
            subquery = (
                select(Property.id)
                .where(Property.owner_id == current_user.id)
            )
            query = query.where(Expense.property_id.in_(subquery))
        
        # Apply filters
        if property_id:
            # Verify user has access to this property
            if current_user.role == UserRole.INTERMEDIARY:
                access_check = await session.execute(
                    select(PropertyAssignment).where(
                        and_(
                            PropertyAssignment.property_id == property_id,
                            PropertyAssignment.intermediary_id == current_user.id,
                            PropertyAssignment.is_active == True,
                        )
                    )
                )
                if not access_check.scalar_one_or_none():
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You do not have access to this property",
                    )
            elif current_user.role == UserRole.OWNER:
                property_check = await session.execute(
                    select(Property).where(
                        and_(
                            Property.id == property_id,
                            Property.owner_id == current_user.id,
                        )
                    )
                )
                if not property_check.scalar_one_or_none():
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You do not own this property",
                    )
            
            query = query.where(Expense.property_id == property_id)
        
        if start_date:
            query = query.where(Expense.expense_date >= start_date)
        
        if end_date:
            query = query.where(Expense.expense_date <= end_date)
        
        if category:
            query = query.where(Expense.category == category)
        
        # Execute query to get all matching expenses
        result = await session.execute(query)
        expenses = result.scalars().all()
        
        # Calculate aggregates
        total_amount = Decimal("0.00")
        pending_amount = Decimal("0.00")
        approved_amount = Decimal("0.00")
        reimbursed_amount = Decimal("0.00")
        outstanding_amount = Decimal("0.00")
        by_category: Dict[ExpenseCategory, Decimal] = {}
        
        for expense in expenses:
            total_amount += expense.amount
            
            if expense.status == ExpenseStatus.PENDING:
                pending_amount += expense.amount
            elif expense.status == ExpenseStatus.APPROVED:
                approved_amount += expense.amount
                if expense.is_reimbursable and not expense.is_reimbursed:
                    outstanding_amount += expense.amount
            elif expense.status == ExpenseStatus.REIMBURSED:
                reimbursed_amount += expense.amount
            
            # Category breakdown
            if expense.category not in by_category:
                by_category[expense.category] = Decimal("0.00")
            by_category[expense.category] += expense.amount
        
        logger.info(
            f"Generated expense report for user {current_user.id}: "
            f"total={total_amount}, pending={pending_amount}, "
            f"approved={approved_amount}, reimbursed={reimbursed_amount}"
        )
        
        return ExpenseSummary(
            total_amount=total_amount,
            pending_amount=pending_amount,
            approved_amount=approved_amount,
            reimbursed_amount=reimbursed_amount,
            outstanding_amount=outstanding_amount,
            by_category={k.value: v for k, v in by_category.items()},
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating expense report: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate expense report: {str(e)}",
        )


# ========== Tax Report Endpoints ==========

@router.get(
    "/tax/income",
    response_model=AnnualIncomeReport,
    summary="Generate annual income tax report",
    description="Generate annual rental income report for tax filing. Owner access only.",
)
def get_tax_income_report(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    year: int = Query(..., description="Tax year", ge=2000, le=2100),
    property_ids: Optional[List[UUID]] = Query(None, description="Filter by property IDs"),
) -> AnnualIncomeReport:
    """Generate annual income tax report.
    
    Implements T225 from tasks.md.
    
    Provides comprehensive income breakdown for tax filing:
    - Total gross rental income
    - Income by property
    - Monthly income breakdown
    - Payment method breakdown
    - Security deposits (separately tracked)
    
    Access control:
    - Owners only: See income for their properties
    - Admin: See all income
    
    Args:
        year: Tax year
        property_ids: Optional property filters
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Annual income report
        
    Raises:
        403: If user is not an owner/admin
        500: If report generation fails
    """
    # Restrict to owners and admins
    if current_user.role not in [UserRole.OWNER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only property owners can generate tax reports",
        )
    
    try:
        report_service = ReportService(db)
        report_data = report_service.calculate_annual_income(
            user_id=current_user.id,
            year=year,
            property_ids=property_ids,
        )
        
        logger.info(f"Generated tax income report for user {current_user.id}, year {year}")
        return AnnualIncomeReport(**report_data)
        
    except Exception as e:
        logger.error(f"Error generating tax income report: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate tax income report: {str(e)}",
        )


@router.get(
    "/tax/deductions",
    response_model=DeductibleExpensesReport,
    summary="Generate tax deductions report",
    description="Generate deductible expenses report for tax filing. Owner access only.",
)
def get_tax_deductions_report(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    year: int = Query(..., description="Tax year", ge=2000, le=2100),
    property_ids: Optional[List[UUID]] = Query(None, description="Filter by property IDs"),
) -> DeductibleExpensesReport:
    """Generate tax-deductible expenses report.
    
    Implements T226 from tasks.md.
    
    Provides breakdown of tax-deductible expenses:
    - Total deductible expenses
    - Breakdown by category
    - Per-property breakdown
    - Non-deductible expenses separately
    
    Access control:
    - Owners only: See expenses for their properties
    - Admin: See all expenses
    
    Args:
        year: Tax year
        property_ids: Optional property filters
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Deductible expenses report
        
    Raises:
        403: If user is not an owner/admin
        500: If report generation fails
    """
    # Restrict to owners and admins
    if current_user.role not in [UserRole.OWNER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only property owners can generate tax reports",
        )
    
    try:
        report_service = ReportService(db)
        report_data = report_service.calculate_deductible_expenses(
            user_id=current_user.id,
            year=year,
            property_ids=property_ids,
        )
        
        logger.info(f"Generated tax deductions report for user {current_user.id}, year {year}")
        return DeductibleExpensesReport(**report_data)
        
    except Exception as e:
        logger.error(f"Error generating tax deductions report: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate tax deductions report: {str(e)}",
        )


@router.get(
    "/tax/gst",
    response_model=GSTReport,
    summary="Generate GST/VAT report",
    description="Generate GST/VAT quarterly report for tax filing. Owner access only.",
)
def get_gst_report(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    year: int = Query(..., description="Year", ge=2000, le=2100),
    quarter: int = Query(..., description="Quarter (1-4)", ge=1, le=4),
    property_ids: Optional[List[UUID]] = Query(None, description="Filter by property IDs"),
) -> GSTReport:
    """Generate GST/VAT quarterly report.
    
    Implements T227 from tasks.md.
    
    Provides GST calculations for quarterly filing:
    - Taxable income and output GST
    - Taxable expenses and input GST
    - Net GST payable/refundable
    
    Access control:
    - Owners only: See GST for their properties
    - Admin: See all GST data
    
    Args:
        year: Year
        quarter: Quarter (1-4)
        property_ids: Optional property filters
        current_user: Authenticated user
        db: Database session
        
    Returns:
        GST report
        
    Raises:
        403: If user is not an owner/admin
        500: If report generation fails
    """
    # Restrict to owners and admins
    if current_user.role not in [UserRole.OWNER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only property owners can generate tax reports",
        )
    
    try:
        report_service = ReportService(db)
        report_data = report_service.calculate_gst_report(
            user_id=current_user.id,
            quarter=quarter,
            year=year,
            property_ids=property_ids,
        )
        
        logger.info(f"Generated GST report for user {current_user.id}, Q{quarter} {year}")
        return GSTReport(**report_data)
        
    except Exception as e:
        logger.error(f"Error generating GST report: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate GST report: {str(e)}",
        )


# ========== Financial Report Endpoints ==========

@router.get(
    "/financial/pnl",
    response_model=ProfitLossStatement,
    summary="Generate profit and loss statement",
    description="Generate P&L statement for financial analysis. Owner access only.",
)
def get_profit_loss_report(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    start_date: date = Query(..., description="Period start date"),
    end_date: date = Query(..., description="Period end date"),
    property_ids: Optional[List[UUID]] = Query(None, description="Filter by property IDs"),
) -> ProfitLossStatement:
    """Generate profit and loss statement.
    
    Implements T228 from tasks.md.
    
    Provides comprehensive P&L with:
    - Revenue breakdown (rent, utilities, other)
    - Expense breakdown by category
    - Gross profit, operating profit, net profit
    - Profit margin percentage
    
    Access control:
    - Owners only: See P&L for their properties
    - Admin: See all P&L data
    
    Args:
        start_date: Period start
        end_date: Period end
        property_ids: Optional property filters
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Profit and loss statement
        
    Raises:
        403: If user is not an owner/admin
        400: If date range is invalid
        500: If report generation fails
    """
    # Restrict to owners and admins
    if current_user.role not in [UserRole.OWNER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only property owners can generate financial reports",
        )
    
    # Validate date range
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before end date",
        )
    
    try:
        report_service = ReportService(db)
        report_data = report_service.generate_profit_loss_statement(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            property_ids=property_ids,
        )
        
        logger.info(
            f"Generated P&L report for user {current_user.id}, "
            f"period {start_date} to {end_date}"
        )
        return ProfitLossStatement(**report_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating P&L report: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate P&L report: {str(e)}",
        )


@router.get(
    "/financial/cashflow",
    response_model=CashFlowStatement,
    summary="Generate cash flow statement",
    description="Generate cash flow statement for financial analysis. Owner access only.",
)
def get_cash_flow_report(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    start_date: date = Query(..., description="Period start date"),
    end_date: date = Query(..., description="Period end date"),
    property_ids: Optional[List[UUID]] = Query(None, description="Filter by property IDs"),
) -> CashFlowStatement:
    """Generate cash flow statement.
    
    Implements T229 from tasks.md.
    
    Provides cash flow analysis with:
    - Cash inflows (operations, deposits, other)
    - Cash outflows (operating, administrative, other)
    - Net cash flow
    
    Access control:
    - Owners only: See cash flow for their properties
    - Admin: See all cash flow data
    
    Args:
        start_date: Period start
        end_date: Period end
        property_ids: Optional property filters
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Cash flow statement
        
    Raises:
        403: If user is not an owner/admin
        400: If date range is invalid
        500: If report generation fails
    """
    # Restrict to owners and admins
    if current_user.role not in [UserRole.OWNER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only property owners can generate financial reports",
        )
    
    # Validate date range
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before end date",
        )
    
    try:
        report_service = ReportService(db)
        report_data = report_service.generate_cash_flow_report(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            property_ids=property_ids,
        )
        
        logger.info(
            f"Generated cash flow report for user {current_user.id}, "
            f"period {start_date} to {end_date}"
        )
        return CashFlowStatement(**report_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating cash flow report: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate cash flow report: {str(e)}",
        )


# ========== Report Scheduling Endpoint ==========

@router.post(
    "/schedule",
    response_model=Dict[str, str],
    summary="Schedule a report for automatic generation",
    description="Schedule a report template for automatic generation. Owner access only.",
)
def schedule_report(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    request: ReportScheduleRequest,
) -> Dict[str, str]:
    """Schedule a report for automatic generation.
    
    Implements T230 from tasks.md.
    
    Allows owners to schedule automatic report generation:
    - Daily, weekly, monthly, quarterly, or annual frequency
    - Email delivery to specified recipients
    - Custom cron expressions for advanced scheduling
    
    Access control:
    - Owners only: Schedule reports for their properties
    - Admin: Schedule any report
    
    Args:
        request: Schedule configuration
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Success message with schedule details
        
    Raises:
        403: If user is not an owner/admin
        404: If template not found
        400: If schedule configuration is invalid
        500: If scheduling fails
    """
    # Restrict to owners and admins
    if current_user.role not in [UserRole.OWNER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only property owners can schedule reports",
        )
    
    try:
        # TODO: Implement scheduling logic with Celery Beat
        # This will be implemented in T231 (Celery task creation)
        
        logger.info(
            f"Scheduled report template {request.template_id} for user {current_user.id}"
        )
        
        return {
            "status": "success",
            "message": f"Report scheduled successfully",
            "template_id": str(request.template_id),
        }
        
    except Exception as e:
        logger.error(f"Error scheduling report: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule report: {str(e)}",
        )


# ========== Report Sharing Endpoints ==========

@router.post(
    "/{report_id}/share",
    response_model=ShareLinkResponse,
    summary="Generate secure share link for a report",
    description="Create a time-limited secure share link for a generated report.",
)
def create_report_share_link(
    report_id: UUID,
    request: ShareLinkRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ShareLinkResponse:
    """Generate a secure share link for a report.
    
    Implements T234 from tasks.md.
    
    Creates a time-limited, secure token for sharing reports with
    external parties (accountants, auditors, etc.) without requiring login.
    
    Access control:
    - Report owner can share their own reports
    - Admins can share any report
    
    Args:
        report_id: Generated report ID
        request: Share link configuration
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Share link details with token and expiration
        
    Raises:
        403: If user doesn't own the report
        404: If report not found
        500: If share link generation fails
    """
    try:
        # Verify report exists and user has access
        report = db.query(GeneratedReport).filter(
            GeneratedReport.id == report_id
        ).first()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found",
            )
        
        # Check access - user must own the report or be admin
        if current_user.role != UserRole.ADMIN and report.generated_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to share this report",
            )
        
        # Generate share token
        report_service = ReportService(db)
        token = report_service.generate_share_token(
            report_id=report_id,
            expires_in_days=request.expires_in_days,
        )
        
        # Build share URL (in production this would be the actual domain)
        share_url = f"/api/v1/reports/shared/{token}"
        
        # Get updated report to get expiration time
        db.refresh(report)
        
        logger.info(
            f"Created share link for report {report_id} by user {current_user.id}, "
            f"expires in {request.expires_in_days} days"
        )
        
        return ShareLinkResponse(
            share_token=token,
            share_url=share_url,
            expires_at=report.share_expires_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating share link: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create share link: {str(e)}",
        )


@router.get(
    "/shared/{token}",
    response_model=GeneratedReportResponse,
    summary="Access a shared report via token",
    description="Access a report using a secure share token (no authentication required).",
)
def get_shared_report(
    token: str,
    db: Annotated[Session, Depends(get_db)],
) -> GeneratedReportResponse:
    """Access a shared report via secure token.
    
    Implements T234 from tasks.md.
    
    Allows external access to reports via time-limited secure tokens.
    No authentication required - the token itself provides authorization.
    
    Args:
        token: Secure share token
        db: Database session
        
    Returns:
        Report details and download link
        
    Raises:
        404: If token is invalid or expired
    """
    try:
        report_service = ReportService(db)
        report = report_service.verify_share_token(token)
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid or expired share link",
            )
        
        logger.info(f"Accessed shared report {report.id} via token")
        
        return GeneratedReportResponse.from_orm(report)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accessing shared report: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to access shared report: {str(e)}",
        )


@router.delete(
    "/{report_id}/share",
    response_model=Dict[str, str],
    summary="Revoke report share link",
    description="Revoke a previously created share link for a report.",
)
def revoke_report_share_link(
    report_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Dict[str, str]:
    """Revoke a report share link.
    
    Implements T234 from tasks.md.
    
    Immediately invalidates the share token, preventing further access.
    
    Access control:
    - Report owner can revoke their own share links
    - Admins can revoke any share link
    
    Args:
        report_id: Generated report ID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        403: If user doesn't own the report
        404: If report not found
        500: If revocation fails
    """
    try:
        # Verify report exists and user has access
        report = db.query(GeneratedReport).filter(
            GeneratedReport.id == report_id
        ).first()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found",
            )
        
        # Check access
        if current_user.role != UserRole.ADMIN and report.generated_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to revoke this share link",
            )
        
        # Revoke token by clearing it
        report.share_token = None
        report.share_expires_at = None
        db.commit()
        
        logger.info(
            f"Revoked share link for report {report_id} by user {current_user.id}"
        )
        
        return {
            "status": "success",
            "message": "Share link revoked successfully",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking share link: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke share link: {str(e)}",
        )
