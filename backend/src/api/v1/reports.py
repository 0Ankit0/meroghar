"""Report generation endpoints.

Implements T133 from tasks.md.
"""
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.dependencies import get_current_user
from ...core.database import get_async_db
from ...models.expense import Expense, ExpenseCategory, ExpenseStatus
from ...models.property import Property, PropertyAssignment
from ...models.user import User, UserRole
from ...schemas.expense import ExpenseSummary

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
