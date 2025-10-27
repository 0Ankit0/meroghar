"""API v1 routes package."""

from fastapi import APIRouter

from .auth import router as auth_router

# Create API v1 router
api_router = APIRouter(prefix="/v1")

# Include all routers
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])

__all__ = ["api_router"]
