"""
CORS middleware and error handlers for FastAPI application.
Implements T015 from tasks.md.
"""

import logging
import time
from typing import Any, Callable

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from jose import JWTError
from sqlalchemy.exc import SQLAlchemyError

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def setup_cors(app: FastAPI) -> None:
    """
    Configure CORS middleware for the FastAPI application.

    Args:
        app: FastAPI application instance
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_credentials,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
    )
    logger.info(f"CORS configured with origins: {settings.cors_origins}")


async def log_requests_middleware(request: Request, call_next: Callable) -> Any:
    """
    Middleware to log all incoming requests and their processing time.

    Args:
        request: Incoming request
        call_next: Next middleware/endpoint handler

    Returns:
        Response from the next handler
    """
    start_time = time.time()

    # Log request
    logger.info(
        f"Request: {request.method} {request.url.path} "
        f"from {request.client.host if request.client else 'unknown'}"
    )

    # Process request
    response = await call_next(request)

    # Calculate processing time
    process_time = time.time() - start_time

    # Log response
    logger.info(
        f"Response: {response.status_code} "
        f"processed in {process_time:.3f}s"
    )

    # Add processing time header
    response.headers["X-Process-Time"] = str(process_time)

    return response


async def rls_context_middleware(request: Request, call_next: Callable) -> Any:
    """
    Middleware to set Row-Level Security context from JWT token.
    This enables database-level access control by extracting user_id from JWT
    and storing it in request state. The actual PostgreSQL session variable
    will be set by the get_async_db dependency when a database connection is needed.

    Args:
        request: Incoming request
        call_next: Next middleware/endpoint handler

    Returns:
        Response from the next handler
    """
    # Extract user ID from JWT token if present
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            from .security import decode_token

            token = auth_header.split(" ")[1]
            payload = decode_token(token)
            user_id = payload.get("sub")

            # Store user ID in request state for RLS context
            # This will be used by get_async_db_with_rls dependency
            request.state.user_id = user_id
            logger.debug(f"RLS context: user_id={user_id}")

        except JWTError:
            logger.debug("Invalid JWT token, skipping RLS context")
        except Exception as e:
            logger.error(f"Error setting RLS context: {e}")

    return await call_next(request)


def setup_error_handlers(app: FastAPI) -> None:
    """
    Configure global error handlers for the FastAPI application.

    Args:
        app: FastAPI application instance
    """

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle validation errors with detailed error messages."""
        errors = []
        for error in exc.errors():
            errors.append(
                {
                    "loc": error["loc"],
                    "msg": error["msg"],
                    "type": error["type"],
                }
            )

        logger.warning(f"Validation error on {request.url.path}: {errors}")

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": "Validation Error",
                "details": errors,
            },
        )

    @app.exception_handler(JWTError)
    async def jwt_exception_handler(request: Request, exc: JWTError) -> JSONResponse:
        """Handle JWT authentication errors."""
        logger.warning(f"JWT error on {request.url.path}: {exc}")

        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "success": False,
                "error": "Authentication Failed",
                "detail": "Invalid or expired token",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(SQLAlchemyError)
    async def database_exception_handler(
        request: Request, exc: SQLAlchemyError
    ) -> JSONResponse:
        """Handle database errors."""
        logger.error(f"Database error on {request.url.path}: {exc}", exc_info=True)

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": "Database Error",
                "detail": "An error occurred while processing your request",
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle all other unhandled exceptions."""
        logger.error(
            f"Unhandled exception on {request.url.path}: {exc}", exc_info=True
        )

        # Don't expose internal errors in production
        detail = str(exc) if settings.debug else "An unexpected error occurred"

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": "Internal Server Error",
                "detail": detail,
            },
        )

    logger.info("Error handlers configured")


def setup_middleware(app: FastAPI) -> None:
    """
    Configure all middleware for the FastAPI application.

    Args:
        app: FastAPI application instance
    """
    # Setup CORS
    setup_cors(app)

    # Add custom middleware
    app.middleware("http")(log_requests_middleware)
    app.middleware("http")(rls_context_middleware)

    # Setup error handlers
    setup_error_handlers(app)

    logger.info("All middleware configured successfully")


__all__ = [
    "setup_cors",
    "setup_error_handlers",
    "setup_middleware",
    "log_requests_middleware",
    "rls_context_middleware",
]
