"""
FastAPI dependencies for authentication and database sessions.
Implements T014 from tasks.md - Updated for async support.
"""

import logging
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_async_db
from ..core.security import decode_token
from ..models.user import User, UserRole

logger = logging.getLogger(__name__)

# Security scheme for JWT tokens
security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UUID:
    """
    Extract and validate current user ID from JWT token.

    Args:
        credentials: HTTP Bearer token credentials

    Returns:
        User ID from token

    Raises:
        HTTPException: If token is invalid or missing
    """
    token = credentials.credentials

    try:
        # Verify and decode token
        payload = decode_token(token)

        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify token type
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Expected access token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )

        logger.debug(f"Authenticated user: {user_id}")
        return UUID(user_id)

    except ValueError as e:
        logger.warning(f"JWT validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.warning(f"Unexpected error validating JWT: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
) -> UUID | None:
    """
    Extract current user ID from JWT token if present (optional authentication).

    Args:
        credentials: HTTP Bearer token credentials (optional)

    Returns:
        User ID from token or None if not authenticated
    """
    if credentials is None:
        return None

    try:
        token = credentials.credentials
        payload = decode_token(token)

        if payload is None or payload.get("type") != "access":
            return None

        user_id = payload.get("sub")
        if user_id:
            logger.debug(f"Optional auth - authenticated user: {user_id}")
            return UUID(user_id)
        return None

    except Exception as e:
        logger.debug(f"Optional auth failed: {e}")
        return None


async def get_current_user(
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_async_db),
) -> User:
    """
    Get current authenticated user from database.

    Args:
        user_id: Current user ID from token
        session: Database session

    Returns:
        User object

    Raises:
        HTTPException: If user not found or inactive
    """
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


def require_role(*allowed_roles: UserRole):
    """
    Dependency factory to require specific user role(s).

    Args:
        allowed_roles: One or more allowed roles

    Returns:
        Dependency function that checks user role

    Example:
        @app.get("/admin")
        async def admin_only(user: User = Depends(require_role(UserRole.OWNER))):
            return {"message": "Admin access granted"}
    """

    async def check_role(
        user: User = Depends(get_current_user),
    ) -> User:
        if user.role not in allowed_roles:
            role_names = ", ".join(role.value for role in allowed_roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of: {role_names}",
            )

        logger.debug(f"Role check passed: {user.role.value}")
        return user

    return check_role


class CommonQueryParams:
    """
    Common query parameters for list endpoints.

    Attributes:
        skip: Number of records to skip
        limit: Maximum number of records to return
    """

    def __init__(
        self,
        skip: int = 0,
        limit: int = 20,
    ):
        self.skip = skip
        self.limit = min(limit, 100)  # Cap at 100 items


__all__ = [
    "get_current_user_id",
    "get_optional_current_user_id",
    "get_current_user",
    "require_role",
    "CommonQueryParams",
    "security",
]
