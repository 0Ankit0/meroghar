"""Maintenance management endpoints.

Implements maintenance request tracking and updates.
"""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...api.dependencies import (CommonQueryParams, get_current_user,
                                 require_role)
from ...core.database import get_async_db
from ...models.maintenance import (MaintenancePriority, MaintenanceRequest,
                                   MaintenanceStatus)
from ...models.property import Property, PropertyAssignment
from ...models.tenant import Tenant, TenantStatus
from ...models.user import User, UserRole
from ...schemas import (PaginatedResponse, SuccessResponse)
from ...schemas.maintenance import (MaintenanceRequestCreate,
                                   MaintenanceRequestResponse,
                                   MaintenanceRequestUpdate)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "",
    response_model=SuccessResponse[MaintenanceRequestResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create maintenance request",
    description="Submit a new maintenance request.",
)
async def create_maintenance_request(
    request: MaintenanceRequestCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_db)],
) -> SuccessResponse[MaintenanceRequestResponse]:
    """Create a new maintenance request.

    Tenants can create requests for their property.
    Owners/Intermediaries can create requests for properties they manage.
    """
    try:
        # Verify property access
        if current_user.role == UserRole.TENANT:
            # Check if tenant lives in property
            result = await session.execute(
                select(Tenant).where(
                    Tenant.user_id == current_user.id,
                    Tenant.property_id == request.property_id,
                    Tenant.status == TenantStatus.ACTIVE,
                )
            )
            tenant = result.scalar_one_or_none()
            if not tenant:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not a tenant of this property",
                )
        
        elif current_user.role == UserRole.INTERMEDIARY:
            # Check assignment
            result = await session.execute(
                select(PropertyAssignment).where(
                    PropertyAssignment.property_id == request.property_id,
                    PropertyAssignment.intermediary_id == current_user.id,
                    PropertyAssignment.is_active,
                )
            )
            if not result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not assigned to this property",
                )
                
        elif current_user.role == UserRole.OWNER:
             # Check ownership
            result = await session.execute(
                select(Property).where(
                    Property.id == request.property_id,
                    Property.owner_id == current_user.id,
                )
            )
            if not result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not own this property",
                )

        # Create request
        new_request = MaintenanceRequest(
            property_id=request.property_id,
            requested_by=current_user.id,
            title=request.title,
            description=request.description,
            priority=request.priority,
            images=request.images,
            status=MaintenanceStatus.OPEN,
        )

        session.add(new_request)
        await session.commit()
        await session.refresh(new_request)

        return SuccessResponse(
            success=True,
            message="Maintenance request submitted successfully",
            data=MaintenanceRequestResponse.model_validate(new_request),
        )

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error creating maintenance request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create maintenance request",
        )


@router.get(
    "",
    response_model=PaginatedResponse[MaintenanceRequestResponse],
    summary="List maintenance requests",
    description="List requests with filtering and RLS.",
)
async def list_maintenance_requests(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_db)],
    commons: Annotated[CommonQueryParams, Depends()],
    property_id: UUID | None = Query(None),
    status_filter: MaintenanceStatus | None = Query(None, alias="status"),
    priority_filter: MaintenancePriority | None = Query(None, alias="priority"),
) -> PaginatedResponse[MaintenanceRequestResponse]:
    try:
        query = select(MaintenanceRequest).options(
            selectinload(MaintenanceRequest.property),
            selectinload(MaintenanceRequest.requester),
            selectinload(MaintenanceRequest.assignee),
        )

        # RLS
        if current_user.role == UserRole.TENANT:
            query = query.where(MaintenanceRequest.requested_by == current_user.id)
        
        elif current_user.role == UserRole.INTERMEDIARY:
            # Managed properties only
            subquery = select(PropertyAssignment.property_id).where(
                PropertyAssignment.intermediary_id == current_user.id,
                PropertyAssignment.is_active,
            )
            query = query.where(MaintenanceRequest.property_id.in_(subquery))
            
        elif current_user.role == UserRole.OWNER:
            # Owned properties only
            subquery = select(Property.id).where(Property.owner_id == current_user.id)
            query = query.where(MaintenanceRequest.property_id.in_(subquery))

        # Filters
        if property_id:
            query = query.where(MaintenanceRequest.property_id == property_id)
        if status_filter:
            query = query.where(MaintenanceRequest.status == status_filter)
        if priority_filter:
            query = query.where(MaintenanceRequest.priority == priority_filter)

        # Pagination
        count_query = select(func.count()).select_from(query.subquery())
        total = (await session.execute(count_query)).scalar_one()

        query = query.order_by(MaintenanceRequest.created_at.desc())
        query = query.offset(commons.skip).limit(commons.limit)

        result = await session.execute(query)
        requests = result.scalars().all()

        # Enhance data
        response_data = []
        for req in requests:
            resp = MaintenanceRequestResponse.model_validate(req)
            if req.property:
                resp.property_name = req.property.name
            if req.requester:
                resp.requester_name = req.requester.full_name
            if req.assignee:
                resp.assignee_name = req.assignee.full_name
            response_data.append(resp)

        return PaginatedResponse(
            success=True,
            message=f"Found {len(response_data)} requests",
            data=response_data,
            total=total,
            skip=commons.skip,
            limit=commons.limit,
        )

    except Exception as e:
        logger.error(f"Error listing maintenance requests: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list maintenance requests",
        )


@router.patch(
    "/{request_id}",
    response_model=SuccessResponse[MaintenanceRequestResponse],
    summary="Update maintenance request",
)
async def update_maintenance_request(
    request_id: UUID,
    update_data: MaintenanceRequestUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_db)],
) -> SuccessResponse[MaintenanceRequestResponse]:
    """Update maintenance request details or status.
    
    Tenants can only update description/images if status is OPEN.
    Owners/Intermediaries can update status, priority, assignment, notes.
    """
    try:
        result = await session.execute(
            select(MaintenanceRequest)
            .options(selectinload(MaintenanceRequest.property))
            .where(MaintenanceRequest.id == request_id)
        )
        req = result.scalar_one_or_none()

        if not req:
            raise HTTPException(status_code=404, detail="Request not found")

        # Authorization
        is_owner = req.property.owner_id == current_user.id
        is_intermediary = False # TODO: Check assignment properly or trust RLS logic logic if simplified
        is_requester = req.requested_by == current_user.id

        # Simplistic auth for brevity - Owner/Intermediary check is complex without property loading context
        # But we loaded property.
        if not is_owner:
             # Check assignment
             res = await session.execute(
                 select(PropertyAssignment).where(
                     PropertyAssignment.property_id == req.property_id,
                     PropertyAssignment.intermediary_id == current_user.id,
                     PropertyAssignment.is_active
                 )
             )
             if res.scalar_one_or_none():
                 is_intermediary = True

        if not (is_owner or is_intermediary or is_requester):
            raise HTTPException(status_code=403, detail="Not authorized")

        # Update Logic
        from datetime import datetime
        
        if is_requester and not (is_owner or is_intermediary):
            # Tenant can only update if OPEN
            if req.status != MaintenanceStatus.OPEN:
                raise HTTPException(status_code=400, detail="Cannot edit request in progress")
            # Can only update description/title/images
            if update_data.description: req.description = update_data.description
            if update_data.title: req.title = update_data.title
            if update_data.images: req.images = update_data.images
            
        else:
            # Management: can update everything
            if update_data.status: 
                req.status = update_data.status
                if update_data.status == MaintenanceStatus.RESOLVED and not req.resolved_at:
                    req.resolved_at = datetime.utcnow()
            
            if update_data.priority: req.priority = update_data.priority
            if update_data.assigned_to: req.assigned_to = update_data.assigned_to
            if update_data.resolution_notes: req.resolution_notes = update_data.resolution_notes
            if update_data.scheduled_date: req.scheduled_date = update_data.scheduled_date
            
            # Allow common fields execution too
            if update_data.description: req.description = update_data.description
            if update_data.title: req.title = update_data.title

        await session.commit()
        await session.refresh(req)

        return SuccessResponse(
            success=True,
            message="Request updated successfully",
            data=MaintenanceRequestResponse.model_validate(req),
        )

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error updating request: {e}")
        raise HTTPException(status_code=500, detail="Failed to update request")
