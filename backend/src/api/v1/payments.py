"""Payment management endpoints.

Implements T061-T062 from tasks.md.
"""
import logging
from datetime import date
from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...api.dependencies import CommonQueryParams, get_current_user, require_role
from ...core.database import get_async_db
from ...models.payment import Payment, PaymentStatus, PaymentType
from ...models.property import PropertyAssignment
from ...models.user import User, UserRole
from ...schemas.payment import (
    PaymentCreateRequest,
    PaymentListResponse,
    PaymentResponse,
)
from ...services.payment_service import PaymentService

# Configure logger for payment endpoints
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a new payment",
    description="Record a payment for a tenant. Requires intermediary role and property assignment.",
)
async def record_payment(
    request: PaymentCreateRequest,
    current_user: Annotated[User, Depends(require_role(UserRole.INTERMEDIARY))],
    session: Annotated[AsyncSession, Depends(get_async_db)],
) -> PaymentResponse:
    """Record a new payment.
    
    Only intermediaries can record payments for properties they manage.
    
    Args:
        request: Payment creation request
        current_user: Authenticated intermediary user
        session: Database session
        
    Returns:
        Created payment details
        
    Raises:
        403: If intermediary is not assigned to the property
        404: If tenant or property not found
        400: If validation fails (inactive tenant, invalid amounts, etc.)
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
                f"Intermediary {current_user.id} attempted to record payment "
                f"for unassigned property {request.property_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned to manage this property",
            )
        
        # Record the payment using service
        payment_service = PaymentService(session)
        payment = await payment_service.record_payment(
            request=request,
            recorded_by=current_user.id,
        )
        
        logger.info(
            f"Payment recorded: id={payment.id}, tenant_id={payment.tenant_id}, "
            f"amount={payment.amount}, recorded_by={current_user.id}"
        )
        
        return PaymentResponse.model_validate(payment)
        
    except ValueError as e:
        # Service validation errors (tenant not found, inactive, etc.)
        logger.error(f"Payment validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error recording payment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record payment",
        )


@router.get(
    "",
    response_model=PaymentListResponse,
    summary="List payments",
    description="Retrieve list of payments with optional filters. Results filtered by role permissions.",
)
async def list_payments(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_db)],
    commons: Annotated[CommonQueryParams, Depends()],
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant ID"),
    property_id: Optional[UUID] = Query(None, description="Filter by property ID"),
    payment_type: Optional[PaymentType] = Query(None, description="Filter by payment type"),
    payment_status: Optional[PaymentStatus] = Query(None, description="Filter by payment status"),
    date_from: Optional[date] = Query(None, description="Filter payments from this date"),
    date_to: Optional[date] = Query(None, description="Filter payments to this date"),
) -> PaymentListResponse:
    """List payments with filters.
    
    Filters applied based on user role:
    - OWNER: See all payments for properties they own
    - INTERMEDIARY: See payments for properties they manage
    - TENANT: See only their own payments
    
    Args:
        current_user: Authenticated user
        session: Database session
        commons: Common pagination params
        tenant_id: Optional tenant filter
        property_id: Optional property filter
        payment_type: Optional payment type filter
        payment_status: Optional payment status filter
        date_from: Optional date range start
        date_to: Optional date range end
        
    Returns:
        List of payments with pagination
        
    Raises:
        500: If database error occurs
    """
    try:
        # Build base query with eager loading
        query = select(Payment).options(
            selectinload(Payment.tenant),
            selectinload(Payment.property),
        )
        
        # Apply role-based filtering (will be enhanced with RLS in T072)
        if current_user.role == UserRole.TENANT:
            # Tenants can only see their own payments
            query = query.where(Payment.tenant_id == current_user.id)
        elif current_user.role == UserRole.INTERMEDIARY:
            # Intermediaries see payments for properties they manage
            result = await session.execute(
                select(PropertyAssignment.property_id).where(
                    PropertyAssignment.intermediary_id == current_user.id
                )
            )
            managed_property_ids = [row[0] for row in result.all()]
            query = query.where(Payment.property_id.in_(managed_property_ids))
        # OWNER sees all payments (no additional filter needed)
        
        # Apply optional filters
        if tenant_id:
            query = query.where(Payment.tenant_id == tenant_id)
        
        if property_id:
            query = query.where(Payment.property_id == property_id)
        
        if payment_type:
            query = query.where(Payment.payment_type == payment_type)
        
        if payment_status:
            query = query.where(Payment.status == payment_status)
        
        if date_from:
            query = query.where(Payment.payment_date >= date_from)
        
        if date_to:
            query = query.where(Payment.payment_date <= date_to)
        
        # Count total results
        count_query = select(Payment.id)
        for whereclause in query.whereclause:
            count_query = count_query.where(whereclause)
        
        result = await session.execute(count_query)
        total = len(result.all())
        
        # Apply pagination and ordering
        query = query.order_by(Payment.payment_date.desc())
        query = query.offset(commons.skip).limit(commons.limit)
        
        # Execute query
        result = await session.execute(query)
        payments = result.scalars().all()
        
        logger.info(
            f"Listed {len(payments)} payments for user {current_user.id} "
            f"(role={current_user.role.value}, total={total})"
        )
        
        return PaymentListResponse(
            payments=[PaymentResponse.model_validate(p) for p in payments],
            total=total,
            skip=commons.skip,
            limit=commons.limit,
        )
        
    except Exception as e:
        logger.error(f"Error listing payments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve payments",
        )


__all__ = ["router"]
