"""Tenant management endpoints.

Implements T038-T039 from tasks.md.
"""
from datetime import datetime
from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from ...core.database import get_async_db
from ...models.property import Property, PropertyAssignment
from ...models.tenant import Tenant, TenantStatus
from ...models.user import User, UserRole
from ...schemas import (
    PaginatedResponse,
    SuccessResponse,
    TenantCreateRequest,
    TenantListResponse,
    TenantResponse,
)
from ...api.dependencies import CommonQueryParams, get_current_user, require_role

router = APIRouter()


@router.post(
    "",
    response_model=SuccessResponse[TenantResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tenant",
    description="Create a new tenant record. Requires intermediary role and property assignment.",
)
async def create_tenant(
    request: TenantCreateRequest,
    current_user: Annotated[User, Depends(require_role(UserRole.INTERMEDIARY))],
    session: Annotated[AsyncSession, Depends(get_async_db)],
) -> SuccessResponse[TenantResponse]:
    """Create a new tenant.
    
    Only intermediaries can create tenant records for properties they manage.
    
    Args:
        request: Tenant creation request
        current_user: Authenticated intermediary user
        session: Database session
        
    Returns:
        Created tenant details
        
    Raises:
        403: If intermediary is not assigned to the property
        404: If user or property not found
        400: If user is not a tenant or already has active tenancy
        500: If database error occurs
    """
    try:
        # Verify property exists
        result = await session.execute(
            select(Property).where(Property.id == request.property_id)
        )
        property_obj = result.scalar_one_or_none()
        
        if not property_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Property {request.property_id} not found",
            )
        
        # Verify intermediary is assigned to this property
        result = await session.execute(
            select(PropertyAssignment).where(
                PropertyAssignment.property_id == request.property_id,
                PropertyAssignment.intermediary_id == current_user.id,
                PropertyAssignment.is_active == True,
            )
        )
        assignment = result.scalar_one_or_none()
        
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned to manage this property",
            )
        
        # Verify user exists and is a tenant
        result = await session.execute(
            select(User).where(User.id == request.user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {request.user_id} not found",
            )
        
        if user.role != UserRole.TENANT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User {user.email} is not a tenant",
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User {user.email} is not active",
            )
        
        # Check if user already has an active tenancy
        result = await session.execute(
            select(Tenant).where(
                Tenant.user_id == request.user_id,
                Tenant.status == TenantStatus.ACTIVE,
            )
        )
        existing_tenant = result.scalar_one_or_none()
        
        if existing_tenant:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User {user.email} already has an active tenancy",
            )
        
        # Create tenant record
        new_tenant = Tenant(
            user_id=request.user_id,
            property_id=request.property_id,
            move_in_date=request.move_in_date,
            move_out_date=request.move_out_date,
            monthly_rent=request.monthly_rent,
            security_deposit=request.security_deposit,
            electricity_rate=request.electricity_rate,
            status=TenantStatus.ACTIVE,
        )
        
        session.add(new_tenant)
        await session.commit()
        await session.refresh(new_tenant)
        
        return SuccessResponse(
            success=True,
            message="Tenant created successfully",
            data=TenantResponse.model_validate(new_tenant),
        )
        
    except HTTPException:
        raise
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create tenant: {str(e)}",
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating tenant: {str(e)}",
        )


@router.get(
    "",
    response_model=PaginatedResponse[TenantListResponse],
    status_code=status.HTTP_200_OK,
    summary="List tenants",
    description="List tenants with RLS filtering. Owners see all tenants for their properties, intermediaries see tenants for assigned properties, tenants see only themselves.",
)
async def list_tenants(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_db)],
    commons: Annotated[CommonQueryParams, Depends()],
    property_id: Optional[UUID] = Query(None, description="Filter by property ID"),
    status_filter: Optional[TenantStatus] = Query(None, alias="status", description="Filter by tenant status"),
) -> PaginatedResponse[TenantListResponse]:
    """List tenants with RLS filtering.
    
    Access rules:
    - Owners: See all tenants for properties they own
    - Intermediaries: See tenants for properties they manage
    - Tenants: See only their own record
    
    Args:
        current_user: Authenticated user
        session: Database session
        commons: Common query parameters (skip, limit)
        property_id: Optional property filter
        status_filter: Optional status filter
        
    Returns:
        Paginated list of tenants
        
    Raises:
        403: If user doesn't have access to requested data
        500: If database error occurs
    """
    try:
        # Build base query with eager loading
        query = select(Tenant).options(
            selectinload(Tenant.user),
            selectinload(Tenant.property),
        )
        
        # Apply RLS filtering based on user role
        if current_user.role == UserRole.TENANT:
            # Tenants can only see their own record
            query = query.where(Tenant.user_id == current_user.id)
            
        elif current_user.role == UserRole.INTERMEDIARY:
            # Intermediaries see tenants for properties they manage
            # Get property IDs where intermediary is assigned
            assignment_result = await session.execute(
                select(PropertyAssignment.property_id).where(
                    PropertyAssignment.intermediary_id == current_user.id,
                    PropertyAssignment.is_active == True,
                )
            )
            managed_property_ids = [row[0] for row in assignment_result.all()]
            
            if not managed_property_ids:
                # Intermediary has no properties assigned
                return PaginatedResponse(
                    success=True,
                    message="No tenants found",
                    data=[],
                    total=0,
                    skip=commons.skip,
                    limit=commons.limit,
                )
            
            query = query.where(Tenant.property_id.in_(managed_property_ids))
            
        elif current_user.role == UserRole.OWNER:
            # Owners see tenants for properties they own
            property_result = await session.execute(
                select(Property.id).where(Property.owner_id == current_user.id)
            )
            owned_property_ids = [row[0] for row in property_result.all()]
            
            if not owned_property_ids:
                # Owner has no properties
                return PaginatedResponse(
                    success=True,
                    message="No tenants found",
                    data=[],
                    total=0,
                    skip=commons.skip,
                    limit=commons.limit,
                )
            
            query = query.where(Tenant.property_id.in_(owned_property_ids))
        
        # Apply optional filters
        if property_id:
            query = query.where(Tenant.property_id == property_id)
        
        if status_filter:
            query = query.where(Tenant.status == status_filter)
        
        # Get total count
        count_result = await session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()
        
        # Apply pagination
        query = query.offset(commons.skip).limit(commons.limit)
        
        # Execute query
        result = await session.execute(query)
        tenants = result.scalars().all()
        
        # Convert to response models
        tenant_list = [TenantListResponse.model_validate(tenant) for tenant in tenants]
        
        return PaginatedResponse(
            success=True,
            message=f"Found {len(tenant_list)} tenant(s)",
            data=tenant_list,
            total=total,
            skip=commons.skip,
            limit=commons.limit,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while listing tenants: {str(e)}",
        )
