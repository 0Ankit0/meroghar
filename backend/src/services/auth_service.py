"""Authentication service.

Implements T033 from tasks.md.
"""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import (JWTManager, PasswordHasher, create_access_token,
                             create_refresh_token, decode_token, hash_password,
                             verify_password)
from ..models.user import User
from ..schemas.auth import (AuthResponse, LoginRequest, RegisterRequest,
                            TokenPair)

# Configure logger for auth service
logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service for user registration, login, and token management."""

    def __init__(self, session: AsyncSession):
        """Initialize auth service with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session
        self.password_hasher = PasswordHasher()
        self.jwt_manager = JWTManager()

    async def register(self, request: RegisterRequest) -> AuthResponse:
        """Register a new user.

        Args:
            request: Registration request with email, password, full_name, role

        Returns:
            AuthResponse with user details and JWT tokens

        Raises:
            ValueError: If email already exists or validation fails
            IntegrityError: If database constraint violated
        """
        logger.info(f"Registration attempt for email: {request.email}, role: {request.role.value}")

        # Check if email already exists
        existing_user = await self._get_user_by_email(request.email)
        if existing_user:
            logger.warning(f"Registration failed: Email {request.email} already exists")
            raise ValueError(f"Email {request.email} is already registered")

        # Hash password
        password_hash = hash_password(request.password)

        # Create user
        user = User(
            email=request.email,
            password_hash=password_hash,
            full_name=request.full_name,
            phone=request.phone,
            role=request.role,
            is_active=True,
        )

        try:
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
            logger.info(
                f"User registered successfully: {user.id} ({user.email}, role: {user.role.value})"
            )
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Registration failed for {request.email}: {str(e)}")
            raise ValueError(f"Failed to create user: {str(e)}")

        # Generate tokens
        access_token = create_access_token(user_id=user.id, role=user.role.value)
        refresh_token = create_refresh_token(user_id=user.id)

        return AuthResponse(
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    async def login(self, request: LoginRequest) -> AuthResponse:
        """Authenticate user and return tokens.

        Args:
            request: Login request with email and password

        Returns:
            AuthResponse with user details and JWT tokens

        Raises:
            ValueError: If credentials invalid or user inactive
        """
        # Get user by email
        user = await self._get_user_by_email(request.email)
        if not user:
            raise ValueError("Invalid email or password")

        # Verify password
        if not verify_password(request.password, user.password_hash):
            raise ValueError("Invalid email or password")

        # Check if user is active
        if not user.is_active:
            raise ValueError("Account is inactive. Please contact support.")

        # Update last login timestamp
        user.last_login_at = datetime.utcnow()
        await self.session.commit()

        # Generate tokens
        access_token = create_access_token(user_id=user.id, role=user.role.value)
        refresh_token = create_refresh_token(user_id=user.id)

        return AuthResponse(
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    async def refresh_tokens(self, refresh_token: str) -> TokenPair:
        """Refresh access token using refresh token.

        Args:
            refresh_token: JWT refresh token

        Returns:
            TokenPair with new access and refresh tokens

        Raises:
            ValueError: If token invalid, expired, or user not found
        """
        # Decode and verify refresh token
        try:
            payload = decode_token(refresh_token)
        except Exception as e:
            raise ValueError(f"Invalid refresh token: {str(e)}")

        # Verify token type
        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type. Expected refresh token.")

        # Get user
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Invalid token payload: missing user ID")

        user = await self._get_user_by_id(UUID(user_id))
        if not user:
            raise ValueError("User not found")

        # Check if user is active
        if not user.is_active:
            raise ValueError("Account is inactive. Please contact support.")

        # Generate new tokens
        access_token = create_access_token(user_id=user.id, role=user.role.value)
        new_refresh_token = create_refresh_token(user_id=user.id)

        return TokenPair(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
        )

    async def verify_access_token(self, access_token: str) -> User | None:
        """Verify access token and return user.

        Args:
            access_token: JWT access token

        Returns:
            User if token valid, None otherwise
        """
        try:
            payload = decode_token(access_token)
        except Exception:
            return None

        # Verify token type
        if payload.get("type") != "access":
            return None

        # Get user
        user_id = payload.get("sub")
        if not user_id:
            return None

        user = await self._get_user_by_id(UUID(user_id))
        if not user or not user.is_active:
            return None

        return user

    async def change_password(
        self, user_id: UUID, current_password: str, new_password: str
    ) -> bool:
        """Change user password.

        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password

        Returns:
            True if password changed successfully

        Raises:
            ValueError: If current password incorrect or user not found
        """
        user = await self._get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        # Verify current password
        if not verify_password(current_password, user.password_hash):
            raise ValueError("Current password is incorrect")

        # Hash and update new password
        user.password_hash = hash_password(new_password)
        user.updated_at = datetime.utcnow()
        await self.session.commit()

        return True

    async def deactivate_user(self, user_id: UUID) -> bool:
        """Deactivate user account.

        Args:
            user_id: User ID to deactivate

        Returns:
            True if user deactivated

        Raises:
            ValueError: If user not found
        """
        user = await self._get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        user.is_active = False
        user.updated_at = datetime.utcnow()
        await self.session.commit()

        return True

    # ==================== Private Helper Methods ====================

    async def _get_user_by_email(self, email: str) -> User | None:
        """Get user by email.

        Args:
            email: User email

        Returns:
            User if found, None otherwise
        """
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def _get_user_by_id(self, user_id: UUID) -> User | None:
        """Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User if found, None otherwise
        """
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
