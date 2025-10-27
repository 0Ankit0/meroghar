"""
FastAPI dependencies for authentication and database sessions.
Implements T014 from tasks.md.
"""

import logging
from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from ..core.database import get_db, set_rls_context
from ..core.security import verify_token

logger = logging.getLogger(__name__)

# Security scheme for JWT tokens
security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
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
        payload = verify_token(token, token_type="access")

        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
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
        return user_id

    except JWTError as e:
        logger.warning(f"JWT validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
) -> Optional[str]:
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
        payload = verify_token(token, token_type="access")

        if payload is None:
            return None

        user_id = payload.get("sub")
        logger.debug(f"Optional auth - authenticated user: {user_id}")
        return user_id

    except Exception as e:
        logger.debug(f"Optional auth failed: {e}")
        return None


def get_db_with_rls(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> Generator[Session, None, None]:
    """
    Get database session with Row-Level Security context set.

    Args:
        db: Database session
        user_id: Current authenticated user ID

    Yields:
        Database session with RLS context

    Example:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db_with_rls)):
            # RLS policies will automatically filter results
            return db.query(User).all()
    """
    # Set RLS context for this session
    set_rls_context(db, user_id)
    yield db


async def require_role(required_role: str):
    """
    Dependency factory to require specific user role.

    Args:
        required_role: Required role (owner, intermediary, tenant)

    Returns:
        Dependency function that checks user role

    Example:
        @app.get("/admin")
        def admin_only(user = Depends(require_role("owner"))):
            return {"message": "Admin access granted"}
    """

    async def check_role(
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ) -> dict:
        token = credentials.credentials

        try:
            payload = verify_token(token, token_type="access")

            if payload is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token",
                )

            user_role = payload.get("role")
            if user_role != required_role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Requires {required_role} role",
                )

            logger.debug(f"Role check passed: {user_role}")
            return payload

        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

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
    "get_db_with_rls",
    "require_role",
    "CommonQueryParams",
    "security",
]
