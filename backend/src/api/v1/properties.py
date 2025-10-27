"""Property management endpoints.

Implements T036-T037 from tasks.md.
"""
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ...core.database import get_async_db
from ...models.property import Property, PropertyAssignment
from ...models.user import User, UserRole
from ...schemas import (
    PropertyAssignIntermediaryRequest,
    PropertyAssignmentResponse,
    PropertyCreateRequest,
    PropertyResponse,
    SuccessResponse,
)
from ...api.dependencies import get_current_user, require_role

router = APIRouter()


@router.post(
    "",
    response_model=SuccessResponse[PropertyResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new property",
    description="Create a new property. Requires owner role.",
)
async def create_property(
    request: PropertyCreateRequest,
    current_user: Annotated[User, Depends(require_role(UserRole.OWNER))],
    session: Annotated[AsyncSession, Depends(get_async_db)],
) -> SuccessResponse[PropertyResponse]:
    """Create a new property.
    
    Only owners can create properties.
    
    Args:
        request: Property creation request
        current_user: Authenticated owner user
        session: Database session
        
    Returns:
        Created property details
        
    Raises:
        403: If user is not an owner
        500: If database error occurs
    """
    try:
        # ==================== Enhanced Validation (T054) ====================
        
        # Validate total_units is positive
        if request.total_units <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Total units must be greater than 0",
            )
        
        # Validate postal code format (basic validation)
        if request.postal_code and len(request.postal_code.strip()) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Postal code must be at least 3 characters",
            )
        
        # Validate required address fields are not empty
        if not request.address_line1.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Address line 1 is required",
            )
        
        if not request.city.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="City is required",
            )
        
        if not request.state.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="State is required",
            )
        
        if not request.country.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Country is required",
            )
        
        # ==================== Create Property ====================
        
        # Create new property
        new_property = Property(
            owner_id=current_user.id,
            name=request.name,
            address_line1=request.address_line1,
            address_line2=request.address_line2,
            city=request.city,
            state=request.state,
            postal_code=request.postal_code,
            country=request.country,
            total_units=request.total_units,
            base_currency=request.base_currency,
        )
        
        session.add(new_property)
        await session.commit()
        await session.refresh(new_property)
        
        return SuccessResponse(
            success=True,
            message="Property created successfully",
            data=PropertyResponse.model_validate(new_property),
        )
        
    except HTTPException:
        raise
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create property: {str(e)}",
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating property: {str(e)}",
        )


@router.post(
    "/{property_id}/assign",
    response_model=SuccessResponse[PropertyAssignmentResponse],
    status_code=status.HTTP_200_OK,
    summary="Assign intermediary to property",
    description="Assign an intermediary to manage a property. Requires owner role and property ownership.",
)
async def assign_intermediary(
    property_id: UUID,
    request: PropertyAssignIntermediaryRequest,
    current_user: Annotated[User, Depends(require_role(UserRole.OWNER))],
    session: Annotated[AsyncSession, Depends(get_async_db)],
) -> SuccessResponse[PropertyAssignmentResponse]:
    """Assign intermediary to property.
    
    Only the property owner can assign intermediaries.
    
    Args:
        property_id: Property ID
        request: Intermediary assignment request
        current_user: Authenticated owner user
        session: Database session
        
    Returns:
        Assignment details
        
    Raises:
        403: If user is not the property owner
        404: If property or intermediary not found
        400: If intermediary already assigned or invalid role
        500: If database error occurs
    """
    try:
        # Get property and verify ownership
        result = await session.execute(
            select(Property).where(Property.id == property_id)
        )
        property_obj = result.scalar_one_or_none()
        
        if not property_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Property {property_id} not found",
            )
        
        if property_obj.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only assign intermediaries to your own properties",
            )
        
        # Get intermediary user and verify role
        result = await session.execute(
            select(User).where(User.id == request.intermediary_id)
        )
        intermediary = result.scalar_one_or_none()
        
        if not intermediary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Intermediary {request.intermediary_id} not found",
            )
        
        if intermediary.role != UserRole.INTERMEDIARY:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User {intermediary.email} is not an intermediary",
            )
        
        if not intermediary.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Intermediary {intermediary.email} is not active",
            )
        
        # Check if assignment already exists
        result = await session.execute(
            select(PropertyAssignment).where(
                PropertyAssignment.property_id == property_id,
                PropertyAssignment.intermediary_id == request.intermediary_id,
                PropertyAssignment.is_active == True,
            )
        )
        existing_assignment = result.scalar_one_or_none()
        
        if existing_assignment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Intermediary {intermediary.email} is already assigned to this property",
            )
        
        # Create assignment
        assignment = PropertyAssignment(
            property_id=property_id,
            intermediary_id=request.intermediary_id,
            assigned_by=current_user.id,
            assigned_at=datetime.utcnow(),
            is_active=True,
        )
        
        session.add(assignment)
        await session.commit()
        await session.refresh(assignment)
        
        return SuccessResponse(
            success=True,
            message="Intermediary assigned successfully",
            data=PropertyAssignmentResponse.model_validate(assignment),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while assigning intermediary: {str(e)}",
        )
