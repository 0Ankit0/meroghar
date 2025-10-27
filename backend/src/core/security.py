"""
Security utilities for password hashing and JWT token management.
Implements T012 and T013 from tasks.md.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

import bcrypt
from jose import JWTError, jwt

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class PasswordHasher:
    """
    Password hashing utilities using bcrypt.
    Implements T012 from tasks.md.
    """

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt with configured cost factor.

        Args:
            password: Plain text password to hash

        Returns:
            Hashed password as string

        Raises:
            ValueError: If password is empty or invalid
        """
        if not password or not password.strip():
            raise ValueError("Password cannot be empty")

        # Convert password to bytes
        password_bytes = password.encode("utf-8")

        # Generate salt with configured cost factor
        salt = bcrypt.gensalt(rounds=settings.bcrypt_cost_factor)

        # Hash password
        hashed = bcrypt.hashpw(password_bytes, salt)

        # Return as string
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain text password against a hashed password.

        Args:
            plain_password: Plain text password to verify
            hashed_password: Hashed password to compare against

        Returns:
            True if passwords match, False otherwise
        """
        if not plain_password or not hashed_password:
            return False

        try:
            password_bytes = plain_password.encode("utf-8")
            hashed_bytes = hashed_password.encode("utf-8")
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False


class JWTManager:
    """
    JWT token generation and validation utilities.
    Implements T013 from tasks.md.
    """

    @staticmethod
    def create_access_token(
        data: dict[str, Any],
        expires_delta: timedelta | None = None,
    ) -> str:
        """
        Create a new JWT access token.

        Args:
            data: Payload data to encode in the token
            expires_delta: Optional custom expiration time

        Returns:
            Encoded JWT token as string
        """
        to_encode = data.copy()

        # Set expiration time
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)

        to_encode.update(
            {
                "exp": expire,
                "iat": datetime.utcnow(),
                "type": "access",
            }
        )

        # Encode token
        encoded_jwt = jwt.encode(
            to_encode,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

        logger.debug(f"Created access token for user: {data.get('sub')}")
        return encoded_jwt

    @staticmethod
    def create_refresh_token(
        data: dict[str, Any],
        expires_delta: timedelta | None = None,
    ) -> str:
        """
        Create a new JWT refresh token.

        Args:
            data: Payload data to encode in the token
            expires_delta: Optional custom expiration time

        Returns:
            Encoded JWT token as string
        """
        to_encode = data.copy()

        # Set expiration time
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days)

        to_encode.update(
            {
                "exp": expire,
                "iat": datetime.utcnow(),
                "type": "refresh",
            }
        )

        # Encode token
        encoded_jwt = jwt.encode(
            to_encode,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

        logger.debug(f"Created refresh token for user: {data.get('sub')}")
        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> dict[str, Any]:
        """
        Decode and validate a JWT token.

        Args:
            token: JWT token to decode

        Returns:
            Decoded token payload

        Raises:
            JWTError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
            )
            return payload
        except JWTError as e:
            logger.warning(f"JWT decode error: {e}")
            raise

    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> dict[str, Any] | None:
        """
        Verify a JWT token and check its type.

        Args:
            token: JWT token to verify
            token_type: Expected token type ('access' or 'refresh')

        Returns:
            Decoded payload if valid, None otherwise
        """
        try:
            payload = JWTManager.decode_token(token)

            # Verify token type
            if payload.get("type") != token_type:
                logger.warning(
                    f"Token type mismatch: expected {token_type}, got {payload.get('type')}"
                )
                return None

            return payload

        except JWTError as e:
            logger.warning(f"Token verification failed: {e}")
            return None

    @staticmethod
    def create_token_pair(
        user_id: str, additional_data: dict[str, Any] | None = None
    ) -> dict[str, str]:
        """
        Create both access and refresh tokens for a user.

        Args:
            user_id: User identifier to encode in tokens
            additional_data: Optional additional data to include in payload

        Returns:
            Dictionary with 'access_token' and 'refresh_token' keys
        """
        data = {"sub": user_id}
        if additional_data:
            data.update(additional_data)

        access_token = JWTManager.create_access_token(data)
        refresh_token = JWTManager.create_refresh_token({"sub": user_id})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }


# Export convenience functions
def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return PasswordHasher.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return PasswordHasher.verify_password(plain_password, hashed_password)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    return JWTManager.create_access_token(data, expires_delta)


def create_refresh_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a JWT refresh token."""
    return JWTManager.create_refresh_token(data, expires_delta)


def decode_token(token: str) -> dict[str, Any]:
    """Decode a JWT token."""
    return JWTManager.decode_token(token)


def verify_token(token: str, token_type: str = "access") -> dict[str, Any] | None:
    """Verify a JWT token."""
    return JWTManager.verify_token(token, token_type)


def create_token_pair(
    user_id: str, additional_data: dict[str, Any] | None = None
) -> dict[str, str]:
    """Create access and refresh token pair."""
    return JWTManager.create_token_pair(user_id, additional_data)


__all__ = [
    "PasswordHasher",
    "JWTManager",
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "verify_token",
    "create_token_pair",
]
