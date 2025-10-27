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
