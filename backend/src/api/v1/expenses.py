"""Expense management endpoints.

Implements T129-T132 from tasks.md.
"""

import logging
from datetime import date, datetime
from typing import Annotated
from uuid import UUID

from fastapi import (APIRouter, Depends, File, HTTPException, Query,
                     UploadFile, status)
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...api.dependencies import get_current_user, require_role
from ...core.database import get_async_db
from ...models.expense import Expense, ExpenseCategory, ExpenseStatus
from ...models.property import PropertyAssignment
from ...models.user import User, UserRole
from ...schemas.expense import (ExpenseApprovalRequest, ExpenseCreateRequest,
                                ExpenseListResponse,
                                ExpenseReimbursementRequest, ExpenseResponse)
from ...services.document_service import get_document_service

# Configure logger for expense endpoints
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "",
    response_model=ExpenseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a new expense",
    description="Record a maintenance or operational expense for a property. Requires intermediary role.",
)
async def record_expense(
    request: ExpenseCreateRequest,
    current_user: Annotated[User, Depends(require_role(UserRole.INTERMEDIARY))],
    session: Annotated[AsyncSession, Depends(get_async_db)],
) -> ExpenseResponse:
    """Record a new expense.

    Only intermediaries can record expenses for properties they manage.

    Args:
        request: Expense creation request
        current_user: Authenticated intermediary user
        session: Database session

    Returns:
        Created expense details

    Raises:
        403: If intermediary is not assigned to the property
        404: If property not found
        400: If validation fails
        500: If database error occurs
    """
    try:
        # Verify intermediary is assigned to the property
        result = await session.execute(
            select(PropertyAssignment).where(
                and_(
                    PropertyAssignment.property_id == request.property_id,
                    PropertyAssignment.intermediary_id == current_user.id,
                    PropertyAssignment.is_active,
                )
            )
        )
        assignment = result.scalar_one_or_none()

        if not assignment:
            logger.warning(
                f"Intermediary {current_user.id} attempted to record expense "
                f"for unassigned property {request.property_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned to manage this property",
            )

        # Create expense
        expense = Expense(
            property_id=request.property_id,
            amount=request.amount,
            category=request.category,
            expense_date=request.expense_date,
            description=request.description,
            vendor_name=request.vendor_name,
            invoice_number=request.invoice_number,
            paid_by=request.paid_by,
            is_reimbursable=request.is_reimbursable,
            recorded_by=current_user.id,
            status=ExpenseStatus.PENDING,
        )

        session.add(expense)
        await session.commit()
        await session.refresh(expense)

        logger.info(
            f"Expense recorded: id={expense.id}, property_id={expense.property_id}, "
            f"amount={expense.amount}, category={expense.category}, recorded_by={current_user.id}"
        )

        return ExpenseResponse.model_validate(expense)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording expense: {str(e)}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record expense: {str(e)}",
        )


@router.post(
    "/{expense_id}/receipt",
    response_model=ExpenseResponse,
    summary="Upload receipt for an expense",
    description="Upload a receipt image/document for an expense. Requires intermediary role.",
)
async def upload_receipt(
    expense_id: UUID,
    file: Annotated[UploadFile, File(description="Receipt image or PDF document")],
    current_user: Annotated[User, Depends(require_role(UserRole.INTERMEDIARY))],
    session: Annotated[AsyncSession, Depends(get_async_db)],
) -> ExpenseResponse:
    """Upload receipt for an expense.

    Args:
        expense_id: Expense ID
        file: Receipt file (image or PDF)
        current_user: Authenticated intermediary user
        session: Database session

    Returns:
        Updated expense with receipt URL

    Raises:
        403: If intermediary doesn't have access to the expense
        404: If expense not found
        400: If file validation fails
        500: If upload error occurs
    """
    try:
        # Fetch expense with property assignment check
        result = await session.execute(
            select(Expense).options(selectinload(Expense.property)).where(Expense.id == expense_id)
        )
        expense = result.scalar_one_or_none()

        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found",
            )

        # Verify intermediary has access
        assignment_result = await session.execute(
            select(PropertyAssignment).where(
                and_(
                    PropertyAssignment.property_id == expense.property_id,
                    PropertyAssignment.intermediary_id == current_user.id,
                    PropertyAssignment.is_active,
                )
            )
        )
        assignment = assignment_result.scalar_one_or_none()

        if not assignment:
            logger.warning(
                f"Intermediary {current_user.id} attempted to upload receipt "
                f"for expense {expense_id} on unassigned property {expense.property_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this expense",
            )

        # Validate file type
        content_type = file.content_type or ""
        allowed_types = [
            "image/jpeg",
            "image/png",
            "image/jpg",
            "application/pdf",
        ]

        if content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}",
            )

        # Upload receipt
        document_service = get_document_service()
        file_content = await file.read()

        receipt_url = await document_service.upload_receipt(
            file_content=file_content,
            filename=file.filename or "receipt",
            expense_id=str(expense_id),
            content_type=content_type,
        )

        # Update expense with receipt URL
        expense.receipt_url = receipt_url
        await session.commit()
        await session.refresh(expense)

        logger.info(f"Receipt uploaded for expense {expense_id}: {receipt_url}")

        return ExpenseResponse.model_validate(expense)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading receipt: {str(e)}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload receipt: {str(e)}",
        )


@router.get(
    "",
    response_model=ExpenseListResponse,
    summary="List expenses with filters",
    description="Get paginated list of expenses with optional filters. Access controlled by role.",
)
async def list_expenses(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_db)],
    property_id: UUID | None = Query(None, description="Filter by property ID"),
    category: ExpenseCategory | None = Query(None, description="Filter by category"),
    status: ExpenseStatus | None = Query(None, description="Filter by status"),
    start_date: date | None = Query(None, description="Filter expenses from this date"),
    end_date: date | None = Query(None, description="Filter expenses until this date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
) -> ExpenseListResponse:
    """List expenses with filters.

    - Intermediaries: See expenses for properties they manage
    - Owners: See expenses for properties they own
    - Admin: See all expenses

    Args:
        property_id: Optional property filter
        category: Optional category filter
        status: Optional status filter
        start_date: Optional start date filter
        end_date: Optional end date filter
        page: Page number
        page_size: Items per page
        current_user: Authenticated user
        session: Database session

    Returns:
        Paginated list of expenses
    """
    try:
        # Build base query with access control
        query = select(Expense).options(
            selectinload(Expense.property),
            selectinload(Expense.recorder),
            selectinload(Expense.approver),
        )

        # Apply role-based filtering
        if current_user.role == UserRole.INTERMEDIARY:
            # Intermediaries see expenses for properties they manage
            subquery = select(PropertyAssignment.property_id).where(
                and_(
                    PropertyAssignment.intermediary_id == current_user.id,
                    PropertyAssignment.is_active,
                )
            )
            query = query.where(Expense.property_id.in_(subquery))

        elif current_user.role == UserRole.OWNER:
            # Owners see expenses for properties they own
            from ...models.property import Property

            subquery = select(Property.id).where(Property.owner_id == current_user.id)
            query = query.where(Expense.property_id.in_(subquery))

        # Apply filters
        if property_id:
            query = query.where(Expense.property_id == property_id)

        if category:
            query = query.where(Expense.category == category)

        if status:
            query = query.where(Expense.status == status)

        if start_date:
            query = query.where(Expense.expense_date >= start_date)

        if end_date:
            query = query.where(Expense.expense_date <= end_date)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(Expense.expense_date.desc()).offset(offset).limit(page_size)

        # Execute query
        result = await session.execute(query)
        expenses = result.scalars().all()

        logger.info(
            f"Listed {len(expenses)} expenses for user {current_user.id} "
            f"(page {page}, total {total})"
        )

        return ExpenseListResponse(
            expenses=[ExpenseResponse.model_validate(e) for e in expenses],
            total=total,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        logger.error(f"Error listing expenses: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list expenses: {str(e)}",
        )


@router.patch(
    "/{expense_id}/approve",
    response_model=ExpenseResponse,
    summary="Approve or reject an expense",
    description="Approve or reject an expense. Requires owner role.",
)
async def approve_expense(
    expense_id: UUID,
    request: ExpenseApprovalRequest,
    current_user: Annotated[User, Depends(require_role(UserRole.OWNER))],
    session: Annotated[AsyncSession, Depends(get_async_db)],
) -> ExpenseResponse:
    """Approve or reject an expense.

    Only property owners can approve/reject expenses for their properties.

    Args:
        expense_id: Expense ID
        request: Approval request with status and optional rejection reason
        current_user: Authenticated owner user
        session: Database session

    Returns:
        Updated expense

    Raises:
        403: If owner doesn't own the property
        404: If expense not found
        400: If expense is not in pending status
        500: If database error occurs
    """
    try:
        # Fetch expense with property
        result = await session.execute(
            select(Expense).options(selectinload(Expense.property)).where(Expense.id == expense_id)
        )
        expense = result.scalar_one_or_none()

        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found",
            )

        # Verify owner owns the property
        if expense.property.owner_id != current_user.id:
            logger.warning(
                f"Owner {current_user.id} attempted to approve expense {expense_id} "
                f"for property owned by {expense.property.owner_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not own the property for this expense",
            )

        # Verify expense is in pending status
        if expense.status != ExpenseStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Expense is not pending (current status: {expense.status})",
            )

        # Update expense
        expense.status = request.status
        expense.approved_by = current_user.id
        expense.approved_date = datetime.utcnow()

        if request.status == ExpenseStatus.REJECTED and request.rejection_reason:
            expense.rejection_reason = request.rejection_reason

        await session.commit()
        await session.refresh(expense)

        logger.info(f"Expense {expense_id} {request.status} by owner {current_user.id}")

        return ExpenseResponse.model_validate(expense)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving expense: {str(e)}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve expense: {str(e)}",
        )


@router.patch(
    "/{expense_id}/reimburse",
    response_model=ExpenseResponse,
    summary="Mark expense as reimbursed",
    description="Mark an approved expense as reimbursed. Requires owner role.",
)
async def reimburse_expense(
    expense_id: UUID,
    request: ExpenseReimbursementRequest,
    current_user: Annotated[User, Depends(require_role(UserRole.OWNER))],
    session: Annotated[AsyncSession, Depends(get_async_db)],
) -> ExpenseResponse:
    """Mark expense as reimbursed.

    Args:
        expense_id: Expense ID
        request: Reimbursement request
        current_user: Authenticated owner user
        session: Database session

    Returns:
        Updated expense

    Raises:
        403: If owner doesn't own the property
        404: If expense not found
        400: If expense is not approved or not reimbursable
        500: If database error occurs
    """
    try:
        # Fetch expense with property
        result = await session.execute(
            select(Expense).options(selectinload(Expense.property)).where(Expense.id == expense_id)
        )
        expense = result.scalar_one_or_none()

        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found",
            )

        # Verify owner owns the property
        if expense.property.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not own the property for this expense",
            )

        # Verify expense is approved
        if expense.status != ExpenseStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Expense must be approved before reimbursement (current status: {expense.status})",
            )

        # Verify expense is reimbursable
        if not expense.is_reimbursable:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Expense is not marked as reimbursable",
            )

        # Update reimbursement status
        expense.status = ExpenseStatus.REIMBURSED
        expense.is_reimbursed = True
        expense.reimbursed_date = request.reimbursed_date or datetime.utcnow()

        await session.commit()
        await session.refresh(expense)

        logger.info(f"Expense {expense_id} marked as reimbursed by owner {current_user.id}")

        return ExpenseResponse.model_validate(expense)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking expense as reimbursed: {str(e)}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark expense as reimbursed: {str(e)}",
        )


@router.get(
    "/{expense_id}",
    response_model=ExpenseResponse,
    summary="Get expense details",
    description="Get detailed information about a specific expense.",
)
async def get_expense(
    expense_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_db)],
) -> ExpenseResponse:
    """Get expense details.

    Args:
        expense_id: Expense ID
        current_user: Authenticated user
        session: Database session

    Returns:
        Expense details

    Raises:
        403: If user doesn't have access
        404: If expense not found
    """
    try:
        # Fetch expense
        result = await session.execute(
            select(Expense)
            .options(
                selectinload(Expense.property),
                selectinload(Expense.recorder),
                selectinload(Expense.approver),
            )
            .where(Expense.id == expense_id)
        )
        expense = result.scalar_one_or_none()

        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found",
            )

        # Verify access
        has_access = False

        if current_user.role == UserRole.INTERMEDIARY:
            # Check if intermediary manages the property
            assignment_result = await session.execute(
                select(PropertyAssignment).where(
                    and_(
                        PropertyAssignment.property_id == expense.property_id,
                        PropertyAssignment.intermediary_id == current_user.id,
                        PropertyAssignment.is_active,
                    )
                )
            )
            has_access = assignment_result.scalar_one_or_none() is not None

        elif current_user.role == UserRole.OWNER:
            # Check if owner owns the property
            has_access = expense.property.owner_id == current_user.id

        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this expense",
            )

        return ExpenseResponse.model_validate(expense)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching expense: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch expense: {str(e)}",
        )
