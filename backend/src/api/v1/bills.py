"""Bill management endpoints.

Implements T081-T086 from tasks.md.
"""
import logging
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...api.dependencies import CommonQueryParams, get_current_user, require_role
from ...core.database import get_async_db
from ...models.bill import (
    Bill,
    BillAllocation,
    BillStatus,
    BillType,
    RecurringBill,
)
from ...models.property import PropertyAssignment
from ...models.user import User, UserRole
from ...schemas.bill import (
    BillAllocationCreateRequest,
    BillAllocationResponse,
    BillAllocationUpdateRequest,
    BillCreateRequest,
    BillListResponse,
    BillResponse,
    BillUpdateRequest,
    RecurringBillCreateRequest,
    RecurringBillListResponse,
    RecurringBillResponse,
    RecurringBillUpdateRequest,
)
from ...services.bill_service import BillService

# Configure logger for bill endpoints
logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== Bill Endpoints (T081-T082) ====================


@router.post(
    "",
    response_model=BillResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new bill",
    description="Create a bill for a property with automatic allocation. Requires intermediary role.",
)
async def create_bill(
    request: BillCreateRequest,
    current_user: Annotated[User, Depends(require_role(UserRole.INTERMEDIARY))],
    session: Annotated[AsyncSession, Depends(get_async_db)],
    allocations: Optional[list[BillAllocationCreateRequest]] = None,
) -> BillResponse:
    """Create a new bill (T081).
    
    Only intermediaries can create bills for properties they manage.
    
    Args:
        request: Bill creation request
        current_user: Authenticated intermediary user
        session: Database session
        allocations: Optional custom allocations (for CUSTOM method)
        
    Returns:
        Created bill with allocations
        
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
                )
            )
        )
        assignment = result.scalar_one_or_none()
        
        if not assignment:
            logger.warning(
                f"Intermediary {current_user.id} attempted to create bill "
                f"for unassigned property {request.property_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned to manage this property",
            )
        
        # Create bill using service
        bill_service = BillService(session)
        bill = await bill_service.create_bill(
            request=request,
            created_by=current_user.id,
            allocations=allocations,
        )
        
        logger.info(
            f"Bill created: id={bill.id}, property_id={request.property_id}, "
            f"type={request.bill_type.value}, amount={request.total_amount}, "
            f"created_by={current_user.id}"
        )
        
        return BillResponse.model_validate(bill)
        
    except ValueError as e:
        logger.error(f"Bill validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error creating bill: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create bill",
        )


@router.get(
    "",
    response_model=BillListResponse,
    summary="List bills",
    description="Retrieve list of bills with optional filters. Results filtered by role permissions.",
)
async def list_bills(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_db)],
    commons: Annotated[CommonQueryParams, Depends()],
    property_id: Optional[UUID] = Query(None, description="Filter by property ID"),
    bill_type: Optional[BillType] = Query(None, description="Filter by bill type"),
    status: Optional[BillStatus] = Query(None, description="Filter by bill status"),
) -> BillListResponse:
    """List bills with filters (T082).
    
    Filters applied based on user role:
    - OWNER: See all bills for properties they own
    - INTERMEDIARY: See bills for properties they manage
    - TENANT: See only bills allocated to them
    
    Args:
        current_user: Authenticated user
        session: Database session
        commons: Common pagination params
        property_id: Optional property filter
        bill_type: Optional bill type filter
        status: Optional status filter
        
    Returns:
        List of bills with pagination info
        
    Raises:
        500: If database error occurs
    """
    try:
        query = select(Bill).options(selectinload(Bill.allocations))
        
        # Apply role-based filtering
        if current_user.role == UserRole.TENANT:
            # Tenants see only bills allocated to them
            query = query.join(BillAllocation).where(
                BillAllocation.tenant_id == current_user.tenant_id
            )
        elif current_user.role == UserRole.INTERMEDIARY:
            # Intermediaries see bills for properties they manage
            query = query.join(PropertyAssignment).where(
                PropertyAssignment.intermediary_id == current_user.id
            )
        elif current_user.role == UserRole.OWNER:
            # Owners see bills for properties they own
            from ...models.property import Property
            query = query.join(Property).where(Property.owner_id == current_user.id)
        
        # Apply filters
        if property_id:
            query = query.where(Bill.property_id == property_id)
        if bill_type:
            query = query.where(Bill.bill_type == bill_type)
        if status:
            query = query.where(Bill.status == status)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar_one()
        
        # Apply pagination
        query = query.offset(commons.skip).limit(commons.limit)
        query = query.order_by(Bill.created_at.desc())
        
        result = await session.execute(query)
        bills = result.scalars().all()
        
        logger.info(
            f"Bills listed: user_id={current_user.id}, role={current_user.role.value}, "
            f"count={len(bills)}, total={total}"
        )
        
        return BillListResponse(
            bills=[BillResponse.model_validate(bill) for bill in bills],
            total=total,
            skip=commons.skip,
            limit=commons.limit,
        )
        
    except Exception as e:
        logger.error(f"Error listing bills: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve bills",
        )


@router.get(
    "/{bill_id}",
    response_model=BillResponse,
    summary="Get bill details",
    description="Retrieve detailed information about a specific bill.",
)
async def get_bill(
    bill_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_db)],
) -> BillResponse:
    """Get bill details (T082).
    
    Args:
        bill_id: Bill ID
        current_user: Authenticated user
        session: Database session
        
    Returns:
        Bill details with allocations
        
    Raises:
        403: If user doesn't have access to this bill
        404: If bill not found
        500: If database error occurs
    """
    try:
        result = await session.execute(
            select(Bill)
            .options(selectinload(Bill.allocations))
            .where(Bill.id == bill_id)
        )
        bill = result.scalar_one_or_none()
        
        if not bill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bill {bill_id} not found",
            )
        
        # Verify access permissions
        if current_user.role == UserRole.TENANT:
            # Check if bill is allocated to this tenant
            if not any(alloc.tenant_id == current_user.tenant_id for alloc in bill.allocations):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this bill",
                )
        elif current_user.role == UserRole.INTERMEDIARY:
            # Check if intermediary manages this property
            result = await session.execute(
                select(PropertyAssignment).where(
                    and_(
                        PropertyAssignment.property_id == bill.property_id,
                        PropertyAssignment.intermediary_id == current_user.id,
                    )
                )
            )
            if not result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this bill",
                )
        elif current_user.role == UserRole.OWNER:
            # Check if owner owns this property
            from ...models.property import Property
            result = await session.execute(
                select(Property).where(
                    and_(
                        Property.id == bill.property_id,
                        Property.owner_id == current_user.id,
                    )
                )
            )
            if not result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this bill",
                )
        
        logger.info(f"Bill retrieved: bill_id={bill_id}, user_id={current_user.id}")
        
        return BillResponse.model_validate(bill)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving bill: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve bill",
        )


@router.patch(
    "/{bill_id}",
    response_model=BillResponse,
    summary="Update bill",
    description="Update bill details. Requires intermediary role.",
)
async def update_bill(
    bill_id: UUID,
    request: BillUpdateRequest,
    current_user: Annotated[User, Depends(require_role(UserRole.INTERMEDIARY))],
    session: Annotated[AsyncSession, Depends(get_async_db)],
) -> BillResponse:
    """Update bill (T081).
    
    Args:
        bill_id: Bill ID
        request: Bill update request
        current_user: Authenticated intermediary user
        session: Database session
        
    Returns:
        Updated bill
        
    Raises:
        403: If intermediary doesn't manage this property
        404: If bill not found
        400: If validation fails
        500: If database error occurs
    """
    try:
        result = await session.execute(
            select(Bill)
            .options(selectinload(Bill.allocations))
            .where(Bill.id == bill_id)
        )
        bill = result.scalar_one_or_none()
        
        if not bill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bill {bill_id} not found",
            )
        
        # Verify intermediary manages this property
        result = await session.execute(
            select(PropertyAssignment).where(
                and_(
                    PropertyAssignment.property_id == bill.property_id,
                    PropertyAssignment.intermediary_id == current_user.id,
                )
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to update this bill",
            )
        
        # Update fields
        if request.status is not None:
            bill_service = BillService(session)
            bill = await bill_service.update_bill_status(bill_id, request.status)
        
        if request.total_amount is not None:
            bill.total_amount = request.total_amount
        if request.due_date is not None:
            bill.due_date = request.due_date
        if request.description is not None:
            bill.description = request.description
        if request.bill_number is not None:
            bill.bill_number = request.bill_number
        
        await session.commit()
        await session.refresh(bill)
        
        logger.info(f"Bill updated: bill_id={bill_id}, user_id={current_user.id}")
        
        return BillResponse.model_validate(bill)
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Bill update validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error updating bill: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update bill",
        )


# ==================== Bill Allocation Endpoints (T083) ====================


@router.patch(
    "/{bill_id}/allocations/{allocation_id}",
    response_model=BillAllocationResponse,
    summary="Update bill allocation",
    description="Update a bill allocation (e.g., mark as paid). Requires intermediary role.",
)
async def update_bill_allocation(
    bill_id: UUID,
    allocation_id: UUID,
    request: BillAllocationUpdateRequest,
    current_user: Annotated[User, Depends(require_role(UserRole.INTERMEDIARY))],
    session: Annotated[AsyncSession, Depends(get_async_db)],
) -> BillAllocationResponse:
    """Update bill allocation (T083).
    
    Args:
        bill_id: Bill ID
        allocation_id: Allocation ID
        request: Allocation update request
        current_user: Authenticated intermediary user
        session: Database session
        
    Returns:
        Updated allocation
        
    Raises:
        403: If intermediary doesn't manage this property
        404: If bill or allocation not found
        400: If validation fails
        500: If database error occurs
    """
    try:
        result = await session.execute(
            select(BillAllocation)
            .join(Bill)
            .where(
                and_(
                    BillAllocation.id == allocation_id,
                    BillAllocation.bill_id == bill_id,
                )
            )
        )
        allocation = result.scalar_one_or_none()
        
        if not allocation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Allocation {allocation_id} not found for bill {bill_id}",
            )
        
        # Get bill for property check
        result = await session.execute(
            select(Bill).where(Bill.id == bill_id)
        )
        bill = result.scalar_one()
        
        # Verify intermediary manages this property
        result = await session.execute(
            select(PropertyAssignment).where(
                and_(
                    PropertyAssignment.property_id == bill.property_id,
                    PropertyAssignment.intermediary_id == current_user.id,
                )
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to update this allocation",
            )
        
        # Update fields
        if request.allocated_amount is not None:
            allocation.allocated_amount = request.allocated_amount
        if request.percentage is not None:
            allocation.percentage = request.percentage
        if request.is_paid is not None:
            bill_service = BillService(session)
            if request.is_paid:
                allocation = await bill_service.mark_allocation_paid(
                    allocation_id, request.payment_id
                )
            else:
                allocation.is_paid = False
                allocation.paid_date = None
                allocation.payment_id = None
        if request.notes is not None:
            allocation.notes = request.notes
        
        await session.commit()
        await session.refresh(allocation)
        
        logger.info(
            f"Allocation updated: allocation_id={allocation_id}, "
            f"bill_id={bill_id}, user_id={current_user.id}"
        )
        
        return BillAllocationResponse.model_validate(allocation)
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Allocation update validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error updating allocation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update allocation",
        )


# ==================== Recurring Bill Endpoints (T084-T086) ====================


@router.post(
    "/recurring",
    response_model=RecurringBillResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create recurring bill template",
    description="Create a recurring bill template for automatic bill generation. Requires intermediary role.",
)
async def create_recurring_bill(
    request: RecurringBillCreateRequest,
    current_user: Annotated[User, Depends(require_role(UserRole.INTERMEDIARY))],
    session: Annotated[AsyncSession, Depends(get_async_db)],
) -> RecurringBillResponse:
    """Create recurring bill template (T084).
    
    Args:
        request: Recurring bill creation request
        current_user: Authenticated intermediary user
        session: Database session
        
    Returns:
        Created recurring bill template
        
    Raises:
        403: If intermediary doesn't manage this property
        404: If property not found
        400: If validation fails
        500: If database error occurs
    """
    try:
        # Verify intermediary manages this property
        result = await session.execute(
            select(PropertyAssignment).where(
                and_(
                    PropertyAssignment.property_id == request.property_id,
                    PropertyAssignment.intermediary_id == current_user.id,
                )
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to create recurring bills for this property",
            )
        
        # Create recurring bill
        bill_service = BillService(session)
        recurring_bill = await bill_service.create_recurring_bill(
            request=request,
            created_by=current_user.id,
        )
        
        logger.info(
            f"Recurring bill created: id={recurring_bill.id}, "
            f"property_id={request.property_id}, created_by={current_user.id}"
        )
        
        return RecurringBillResponse.model_validate(recurring_bill)
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Recurring bill validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error creating recurring bill: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create recurring bill",
        )


@router.get(
    "/recurring",
    response_model=RecurringBillListResponse,
    summary="List recurring bill templates",
    description="Retrieve list of recurring bill templates.",
)
async def list_recurring_bills(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_db)],
    commons: Annotated[CommonQueryParams, Depends()],
    property_id: Optional[UUID] = Query(None, description="Filter by property ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
) -> RecurringBillListResponse:
    """List recurring bill templates (T085).
    
    Args:
        current_user: Authenticated user
        session: Database session
        commons: Common pagination params
        property_id: Optional property filter
        is_active: Optional active status filter
        
    Returns:
        List of recurring bill templates
        
    Raises:
        500: If database error occurs
    """
    try:
        query = select(RecurringBill)
        
        # Apply role-based filtering
        if current_user.role == UserRole.INTERMEDIARY:
            query = query.join(PropertyAssignment).where(
                PropertyAssignment.intermediary_id == current_user.id
            )
        elif current_user.role == UserRole.OWNER:
            from ...models.property import Property
            query = query.join(Property).where(Property.owner_id == current_user.id)
        elif current_user.role == UserRole.TENANT:
            # Tenants can't see recurring bill templates
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenants cannot access recurring bill templates",
            )
        
        # Apply filters
        if property_id:
            query = query.where(RecurringBill.property_id == property_id)
        if is_active is not None:
            query = query.where(RecurringBill.is_active == is_active)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar_one()
        
        # Apply pagination
        query = query.offset(commons.skip).limit(commons.limit)
        query = query.order_by(RecurringBill.created_at.desc())
        
        result = await session.execute(query)
        recurring_bills = result.scalars().all()
        
        logger.info(
            f"Recurring bills listed: user_id={current_user.id}, "
            f"count={len(recurring_bills)}, total={total}"
        )
        
        return RecurringBillListResponse(
            recurring_bills=[
                RecurringBillResponse.model_validate(rb) for rb in recurring_bills
            ],
            total=total,
            skip=commons.skip,
            limit=commons.limit,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing recurring bills: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recurring bills",
        )


@router.patch(
    "/recurring/{recurring_bill_id}",
    response_model=RecurringBillResponse,
    summary="Update recurring bill template",
    description="Update a recurring bill template. Requires intermediary role.",
)
async def update_recurring_bill(
    recurring_bill_id: UUID,
    request: RecurringBillUpdateRequest,
    current_user: Annotated[User, Depends(require_role(UserRole.INTERMEDIARY))],
    session: Annotated[AsyncSession, Depends(get_async_db)],
) -> RecurringBillResponse:
    """Update recurring bill template (T086).
    
    Args:
        recurring_bill_id: Recurring bill ID
        request: Recurring bill update request
        current_user: Authenticated intermediary user
        session: Database session
        
    Returns:
        Updated recurring bill template
        
    Raises:
        403: If intermediary doesn't manage this property
        404: If recurring bill not found
        400: If validation fails
        500: If database error occurs
    """
    try:
        result = await session.execute(
            select(RecurringBill).where(RecurringBill.id == recurring_bill_id)
        )
        recurring_bill = result.scalar_one_or_none()
        
        if not recurring_bill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recurring bill {recurring_bill_id} not found",
            )
        
        # Verify intermediary manages this property
        result = await session.execute(
            select(PropertyAssignment).where(
                and_(
                    PropertyAssignment.property_id == recurring_bill.property_id,
                    PropertyAssignment.intermediary_id == current_user.id,
                )
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to update this recurring bill",
            )
        
        # Update fields
        if request.estimated_amount is not None:
            recurring_bill.estimated_amount = request.estimated_amount
        if request.day_of_month is not None:
            recurring_bill.day_of_month = request.day_of_month
        if request.description is not None:
            recurring_bill.description = request.description
        if request.is_active is not None:
            recurring_bill.is_active = request.is_active
        
        await session.commit()
        await session.refresh(recurring_bill)
        
        logger.info(
            f"Recurring bill updated: id={recurring_bill_id}, user_id={current_user.id}"
        )
        
        return RecurringBillResponse.model_validate(recurring_bill)
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Recurring bill update validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error updating recurring bill: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update recurring bill",
        )


@router.post(
    "/recurring/generate",
    response_model=BillListResponse,
    summary="Generate bills from recurring templates",
    description="Manually trigger bill generation from recurring templates. Requires intermediary role.",
)
async def generate_recurring_bills(
    current_user: Annotated[User, Depends(require_role(UserRole.INTERMEDIARY))],
    session: Annotated[AsyncSession, Depends(get_async_db)],
    recurring_bill_id: Optional[UUID] = Query(None, description="Optional specific recurring bill ID"),
) -> BillListResponse:
    """Generate bills from recurring templates (T086).
    
    Args:
        current_user: Authenticated intermediary user
        session: Database session
        recurring_bill_id: Optional specific recurring bill ID to generate from
        
    Returns:
        List of generated bills
        
    Raises:
        403: If intermediary doesn't manage the property (for specific recurring bill)
        500: If database error occurs
    """
    try:
        # If specific recurring bill, verify permission
        if recurring_bill_id:
            result = await session.execute(
                select(RecurringBill).where(RecurringBill.id == recurring_bill_id)
            )
            recurring_bill = result.scalar_one_or_none()
            
            if not recurring_bill:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Recurring bill {recurring_bill_id} not found",
                )
            
            # Verify intermediary manages this property
            result = await session.execute(
                select(PropertyAssignment).where(
                    and_(
                        PropertyAssignment.property_id == recurring_bill.property_id,
                        PropertyAssignment.intermediary_id == current_user.id,
                    )
                )
            )
            if not result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to generate bills from this template",
                )
        
        # Generate bills
        bill_service = BillService(session)
        bills = await bill_service.generate_bills_from_recurring(recurring_bill_id)
        
        logger.info(
            f"Bills generated from recurring templates: count={len(bills)}, "
            f"user_id={current_user.id}, recurring_bill_id={recurring_bill_id}"
        )
        
        return BillListResponse(
            bills=[BillResponse.model_validate(bill) for bill in bills],
            total=len(bills),
            skip=0,
            limit=len(bills),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating recurring bills: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate recurring bills",
        )


__all__ = ["router"]
