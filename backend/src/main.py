"""
Main FastAPI application entry point.
Implements T017 from tasks.md.
"""

import logging
from datetime import datetime

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

from .core.config import get_settings, setup_logging
from .core.database import check_db_connection, close_db
from .core.middleware import setup_middleware
from .schemas import HealthCheckResponse

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Comprehensive house rental management system with mobile and API support",
    version=settings.api_version,
    docs_url=f"/api/{settings.api_version}/docs" if settings.debug else None,
    redoc_url=f"/api/{settings.api_version}/redoc" if settings.debug else None,
    openapi_url=f"/api/{settings.api_version}/openapi.json" if settings.debug else None,
)

# Setup middleware (CORS, logging, error handlers)
setup_middleware(app)


@app.on_event("startup")
async def startup_event() -> None:
    """
    Application startup event handler.
    Performs initialization tasks like database connection check.
    """
    logger.info(f"Starting {settings.app_name} - Environment: {settings.environment}")

    # Check database connection
    if check_db_connection():
        logger.info("Database connection: OK")
    else:
        logger.error("Database connection: FAILED")

    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """
    Application shutdown event handler.
    Performs cleanup tasks like closing database connections.
    """
    logger.info("Shutting down application...")

    # Close database connections
    close_db()

    logger.info("Application shutdown complete")


@app.get("/", status_code=status.HTTP_200_OK)
async def root() -> JSONResponse:
    """
    Root endpoint providing basic API information.

    Returns:
        JSON response with API information
    """
    return JSONResponse(
        content={
            "message": f"Welcome to {settings.app_name} API",
            "version": settings.api_version,
            "docs": f"/api/{settings.api_version}/docs",
            "status": "operational",
        }
    )


@app.get(
    f"/api/{settings.api_version}/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    tags=["Health"],
)
async def health_check() -> HealthCheckResponse:
    """
    Health check endpoint for monitoring and load balancers.

    Returns:
        Health check response with system status
    """
    db_status = "connected" if check_db_connection() else "disconnected"

    return HealthCheckResponse(
        status="healthy" if db_status == "connected" else "unhealthy",
        version=settings.api_version,
        timestamp=datetime.utcnow().isoformat() + "Z",
        database=db_status,
    )


# API Router setup
# Import and include API v1 routers
from .api.v1 import api_router

app.include_router(api_router, prefix="/api")

logger.info(f"FastAPI application configured with prefix: /api/{settings.api_version}")

