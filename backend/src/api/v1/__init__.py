"""API v1 routes package."""

from fastapi import APIRouter

from .auth import router as auth_router
from .users import router as users_router
from .properties import router as properties_router
from .tenants import router as tenants_router

# Create API v1 router
api_router = APIRouter(prefix="/v1")

# Include all routers
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users_router, prefix="/users", tags=["Users"])
api_router.include_router(properties_router, prefix="/properties", tags=["Properties"])
api_router.include_router(tenants_router, prefix="/tenants", tags=["Tenants"])

__all__ = ["api_router"]
