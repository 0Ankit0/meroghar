"""User management endpoints.

Implements T035 from tasks.md.
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ...core.database import get_async_db
from ...core.security import hash_password
from ...models.user import User, UserRole
from ...schemas import (
    SuccessResponse,
    UserCreateRequest,
    UserResponse,
)
from ...api.dependencies import get_current_user, require_role

router = APIRouter()


@router.post(
    "",
    response_model=SuccessResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Create a new user account (tenant user by intermediary). Requires intermediary role.",
)
async def create_user(
    request: UserCreateRequest,
    current_user: Annotated[User, Depends(require_role(UserRole.INTERMEDIARY))],
    session: Annotated[AsyncSession, Depends(get_async_db)],
) -> SuccessResponse[UserResponse]:
    """Create a new user (tenant).
    
    Only intermediaries can create tenant users for properties they manage.
    
    Args:
        request: User creation request
        current_user: Authenticated intermediary user
        session: Database session
        
    Returns:
        Created user details
        
    Raises:
        400: If email already exists
        403: If user is not an intermediary
        500: If database error occurs
    """
    try:
        # ==================== Enhanced Validation (T054) ====================
        
        # Validate email format (basic check - Pydantic also validates)
        if not request.email or "@" not in request.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format",
            )
        
        # Validate password strength (minimum 8 characters)
        if len(request.password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long",
            )
        
        # Validate full name is not empty
        if not request.full_name or not request.full_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Full name is required",
            )
        
        # Validate phone format if provided (basic check)
        if request.phone:
            # Remove common separators
            phone_digits = ''.join(c for c in request.phone if c.isdigit() or c == '+')
            if len(phone_digits) < 10:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Phone number must contain at least 10 digits",
                )
        
        # Validate role is tenant or intermediary (not owner)
        if request.role == UserRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create owner accounts through this endpoint",
            )
        
        # ==================== Existing Validation ====================
        
        # Check if email already exists
        result = await session.execute(
            select(User).where(User.email == request.email)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email {request.email} is already registered",
            )
        
        # Create new user
        new_user = User(
            email=request.email,
            password_hash=hash_password(request.password),
            full_name=request.full_name,
            phone=request.phone,
            role=request.role,
            is_active=True,
        )
        
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        
        return SuccessResponse(
            success=True,
            message="User created successfully",
            data=UserResponse.model_validate(new_user),
        )
        
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create user: {str(e)}",
        )
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating user: {str(e)}",
        )
