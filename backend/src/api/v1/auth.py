"""Authentication endpoints.

Implements T034 from tasks.md.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_async_db
from ...schemas import (
    AuthResponse,
    LoginRequest,
    LogoutResponse,
    RefreshTokenRequest,
    RegisterRequest,
    SuccessResponse,
    TokenPair,
)
from ...services.auth_service import AuthService

router = APIRouter()


def get_auth_service(
    session: Annotated[AsyncSession, Depends(get_async_db)]
) -> AuthService:
    """Get auth service instance.
    
    Args:
        session: Database session from dependency
        
    Returns:
        AuthService instance
    """
    return AuthService(session)


@router.post(
    "/register",
    response_model=SuccessResponse[AuthResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Register a new user account with email, password, and role. Returns JWT tokens for immediate login.",
)
async def register(
    request: RegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> SuccessResponse[AuthResponse]:
    """Register a new user.
    
    Args:
        request: Registration request with user details
        auth_service: Auth service instance
        
    Returns:
        Success response with user details and JWT tokens
        
    Raises:
        HTTPException 400: If email already exists or validation fails
        HTTPException 500: If server error occurs
    """
    try:
        auth_response = await auth_service.register(request)
        return SuccessResponse(
            data=auth_response,
            message="User registered successfully",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}",
        )


@router.post(
    "/login",
    response_model=SuccessResponse[AuthResponse],
    status_code=status.HTTP_200_OK,
    summary="User login",
    description="Authenticate user with email and password. Returns JWT tokens for API access.",
)
async def login(
    request: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> SuccessResponse[AuthResponse]:
    """User login.
    
    Args:
        request: Login request with email and password
        auth_service: Auth service instance
        
    Returns:
        Success response with user details and JWT tokens
        
    Raises:
        HTTPException 401: If credentials invalid
        HTTPException 403: If account inactive
        HTTPException 500: If server error occurs
    """
    try:
        auth_response = await auth_service.login(request)
        return SuccessResponse(
            data=auth_response,
            message="Login successful",
        )
    except ValueError as e:
        error_msg = str(e).lower()
        if "invalid" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
            )
        elif "inactive" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}",
        )


@router.post(
    "/refresh",
    response_model=SuccessResponse[TokenPair],
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Refresh expired access token using refresh token. Returns new access and refresh tokens.",
)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> SuccessResponse[TokenPair]:
    """Refresh access token.
    
    Args:
        request: Refresh token request
        auth_service: Auth service instance
        
    Returns:
        Success response with new token pair
        
    Raises:
        HTTPException 401: If refresh token invalid or expired
        HTTPException 403: If account inactive
        HTTPException 500: If server error occurs
    """
    try:
        token_pair = await auth_service.refresh_tokens(request.refresh_token)
        return SuccessResponse(
            data=token_pair,
            message="Token refreshed successfully",
        )
    except ValueError as e:
        error_msg = str(e).lower()
        if "inactive" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}",
        )


@router.post(
    "/logout",
    response_model=SuccessResponse[LogoutResponse],
    status_code=status.HTTP_200_OK,
    summary="User logout",
    description="Logout user. Note: Token invalidation must be handled client-side by deleting tokens.",
)
async def logout() -> SuccessResponse[LogoutResponse]:
    """User logout.
    
    Note: JWT tokens are stateless, so logout is handled client-side
    by deleting the stored tokens. This endpoint exists for consistency
    and to allow future server-side token blacklisting if needed.
    
    Returns:
        Success response with logout message
    """
    return SuccessResponse(
        data=LogoutResponse(message="Successfully logged out"),
        message="Logout successful. Please delete tokens on client side.",
    )
