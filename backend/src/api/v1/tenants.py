"""Tenant management endpoints.

Implements T038-T039 from tasks.md.
"""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...api.dependencies import (CommonQueryParams, get_current_user,
                                 require_role)
from ...core.database import get_async_db
from ...models.property import Property, PropertyAssignment
from ...models.tenant import Tenant, TenantStatus
from ...models.user import User, UserRole
from ...schemas import (PaginatedResponse, SuccessResponse,
                        TenantCreateRequest, TenantListResponse,
                        TenantResponse)

# Configure logger for tenant endpoints
logger = logging.getLogger(__name__)

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
        # ==================== Enhanced Validation (T054) ====================

        # Validate move_out_date is after move_in_date
        if request.move_out_date and request.move_out_date <= request.move_in_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Move out date must be after move in date",
            )

        # Validate financial fields are positive
        if request.monthly_rent <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Monthly rent must be greater than 0",
            )

        if request.security_deposit < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Security deposit must be 0 or greater",
            )

        if request.electricity_rate <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Electricity rate must be greater than 0",
            )

        # Validate move_in_date is not in the distant past (more than 5 years)
        from datetime import datetime, timedelta

        five_years_ago = datetime.now().date() - timedelta(days=5 * 365)
        if request.move_in_date < five_years_ago:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Move in date cannot be more than 5 years in the past",
            )

        # ==================== Existing Validation ====================

        # Verify property exists
        result = await session.execute(select(Property).where(Property.id == request.property_id))
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
                PropertyAssignment.is_active,
            )
        )
        assignment = result.scalar_one_or_none()

        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned to manage this property",
            )

        # Verify user exists and is a tenant
        result = await session.execute(select(User).where(User.id == request.user_id))
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

        # Validate property capacity (total_units)
        result = await session.execute(
            select(Tenant).where(
                Tenant.property_id == request.property_id,
                Tenant.status == TenantStatus.ACTIVE,
            )
        )
        active_tenants_count = len(result.scalars().all())

        if active_tenants_count >= property_obj.total_units:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Property has reached maximum capacity ({property_obj.total_units} units)",
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

        # Log successful tenant creation (T055)
        logger.info(
            f"Tenant created: tenant_id={new_tenant.id}, user_id={request.user_id}, "
            f"property_id={request.property_id}, intermediary_id={current_user.id}, "
            f"monthly_rent={request.monthly_rent}, status=ACTIVE"
        )

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
    property_id: UUID | None = Query(None, description="Filter by property ID"),
    status_filter: TenantStatus | None = Query(
        None, alias="status", description="Filter by tenant status"
    ),
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
                    PropertyAssignment.is_active,
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
        count_result = await session.execute(select(func.count()).select_from(query.subquery()))
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


@router.get(
    "/{tenant_id}/balance",
    response_model=SuccessResponse,
    summary="Get tenant payment balance",
    description="Calculate and retrieve tenant's payment balance including outstanding amounts.",
)
async def get_tenant_balance(
    tenant_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_db)],
) -> SuccessResponse:
    """Get tenant payment balance.

    Calculates total paid, total due, and outstanding balance for a tenant.

    Authorization:
    - OWNER: Can view balance for any tenant
    - INTERMEDIARY: Can view balance for tenants in managed properties
    - TENANT: Can view only their own balance

    Args:
        tenant_id: Tenant ID to get balance for
        current_user: Authenticated user
        session: Database session

    Returns:
        Balance calculation details

    Raises:
        403: If user doesn't have permission to view balance
        404: If tenant not found
        500: If database error occurs
    """
    try:
        from ...services.payment_service import PaymentService

        # Get tenant to verify existence and get property_id
        result = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()

        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant {tenant_id} not found",
            )

        # Authorization check based on role
        if current_user.role == UserRole.TENANT:
            # Tenants can only view their own balance
            if current_user.id != tenant_id:
                logger.warning(
                    f"Tenant {current_user.id} attempted to view balance " f"for tenant {tenant_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only view your own balance",
                )
        elif current_user.role == UserRole.INTERMEDIARY:
            # Intermediaries can view balance for tenants in managed properties
            result = await session.execute(
                select(PropertyAssignment).where(
                    and_(
                        PropertyAssignment.property_id == tenant.property_id,
                        PropertyAssignment.intermediary_id == current_user.id,
                    )
                )
            )
            assignment = result.scalar_one_or_none()

            if not assignment:
                logger.warning(
                    f"Intermediary {current_user.id} attempted to view balance "
                    f"for tenant {tenant_id} in unassigned property {tenant.property_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not assigned to manage this tenant's property",
                )
        # OWNER can view any balance (no additional check needed)

        # Calculate balance using service
        payment_service = PaymentService(session)
        balance = await payment_service.calculate_balance(
            tenant_id=tenant_id,
            property_id=tenant.property_id,
        )

        logger.info(
            f"Balance retrieved for tenant {tenant_id} by user {current_user.id}: "
            f"outstanding={balance.outstanding_balance}"
        )

        return SuccessResponse(
            success=True,
            message="Balance calculated successfully",
            data=balance,
        )

    except HTTPException:
        raise
    except ValueError as e:
        # Service validation errors
        logger.error(f"Balance calculation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error getting tenant balance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate tenant balance",
        )


@router.put(
    "/{tenant_id}/rent-policy",
    response_model=SuccessResponse[TenantResponse],
    summary="Set rent increment policy",
    description="Configure automatic rent increment policy for a tenant (T195)",
)
async def set_rent_policy(
    tenant_id: UUID,
    current_user: Annotated[User, Depends(require_role(UserRole.OWNER))],
    session: Annotated[AsyncSession, Depends(get_async_db)],
    increment_type: str = Query(..., description="Type: 'percentage' or 'fixed'"),
    increment_value: float = Query(
        ..., description="Increment value (e.g., 5 for 5% or fixed amount)"
    ),
    interval_years: int = Query(..., description="Years between increments"),
) -> SuccessResponse[TenantResponse]:
    """Set or update rent increment policy for a tenant.

    Only property owners can set rent policies.
    Implements T195 from tasks.md.
    """
    from ...services.rent_increment_service import RentIncrementService

    try:
        # Get tenant with property relationship
        result = await session.execute(
            select(Tenant)
            .options(selectinload(Tenant.property), selectinload(Tenant.user))
            .where(Tenant.id == tenant_id)
        )
        tenant = result.scalar_one_or_none()

        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found",
            )

        # Verify ownership
        if tenant.property.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only property owner can set rent policy",
            )

        # Validate increment type
        if increment_type not in ["percentage", "fixed"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Increment type must be 'percentage' or 'fixed'",
            )

        # Set policy using service
        service = RentIncrementService(session)
        tenant = service.set_rent_policy(
            tenant=tenant,
            increment_type=increment_type,
            increment_value=increment_value,
            interval_years=interval_years,
        )

        await session.commit()
        await session.refresh(tenant)

        logger.info(f"Rent policy set for tenant {tenant_id} by user {current_user.id}")

        return SuccessResponse(
            success=True,
            message="Rent increment policy set successfully",
            data=TenantResponse.from_orm(tenant),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting rent policy: {str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set rent policy",
        )


@router.post(
    "/{tenant_id}/rent-override",
    response_model=SuccessResponse[TenantResponse],
    summary="Manual rent override",
    description="Manually override tenant rent amount (T196)",
)
async def manual_rent_override(
    tenant_id: UUID,
    current_user: Annotated[User, Depends(require_role(UserRole.OWNER))],
    session: Annotated[AsyncSession, Depends(get_async_db)],
    new_rent: float = Query(..., description="New rent amount"),
    reason: str = Query(..., description="Reason for override"),
) -> SuccessResponse[TenantResponse]:
    """Manually override tenant rent.

    Only property owners can override rent.
    Implements T196 from tasks.md.
    """
    from decimal import Decimal

    from ...services.rent_increment_service import RentIncrementService

    try:
        # Get tenant
        result = await session.execute(
            select(Tenant)
            .options(selectinload(Tenant.property), selectinload(Tenant.user))
            .where(Tenant.id == tenant_id)
        )
        tenant = result.scalar_one_or_none()

        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found",
            )

        # Verify ownership
        if tenant.property.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only property owner can override rent",
            )

        # Validate new rent
        if new_rent <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rent must be positive",
            )

        # Apply override
        service = RentIncrementService(session)
        tenant = service.apply_manual_override(
            tenant=tenant,
            new_rent=Decimal(str(new_rent)),
            applied_by=current_user.id,
            reason=reason,
        )

        await session.commit()
        await session.refresh(tenant)

        logger.info(f"Rent overridden for tenant {tenant_id} by user {current_user.id}")

        return SuccessResponse(
            success=True,
            message="Rent overridden successfully",
            data=TenantResponse.from_orm(tenant),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error overriding rent: {str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to override rent",
        )


@router.get(
    "/{tenant_id}/rent-history",
    response_model=SuccessResponse[list[dict]],
    summary="Get rent history",
    description="Get historical rent changes for a tenant (T197)",
)
async def get_rent_history(
    tenant_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_db)],
) -> SuccessResponse[list[dict]]:
    """Get rent change history for a tenant.

    Accessible by owner, intermediary, or the tenant themselves.
    Implements T197 from tasks.md.
    """
    from ...services.rent_increment_service import RentIncrementService

    try:
        # Get tenant
        result = await session.execute(
            select(Tenant).options(selectinload(Tenant.property)).where(Tenant.id == tenant_id)
        )
        tenant = result.scalar_one_or_none()

        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found",
            )

        # Check access
        has_access = (
            (current_user.role == UserRole.OWNER and tenant.property.owner_id == current_user.id)
            or (
                current_user.role == UserRole.INTERMEDIARY
                and tenant.intermediary_id == current_user.id
            )
            or (current_user.role == UserRole.TENANT and tenant.user_id == current_user.id)
        )

        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view rent history",
            )

        # Get history
        service = RentIncrementService(session)
        history = service.get_rent_history(tenant)

        logger.info(f"Rent history retrieved for tenant {tenant_id} by user {current_user.id}")

        return SuccessResponse(
            success=True,
            message="Rent history retrieved successfully",
            data=history,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting rent history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve rent history",
        )
