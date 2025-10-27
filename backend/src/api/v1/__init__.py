"""API v1 routes package."""

from fastapi import APIRouter

from .auth import router as auth_router
from .users import router as users_router
from .properties import router as properties_router
from .tenants import router as tenants_router
from .payments import router as payments_router
from .bills import router as bills_router
from .analytics import router as analytics_router
from .webhooks import router as webhooks_router
from .expenses import router as expenses_router
from .reports import router as reports_router
from .sync import router as sync_router
from .messages import router as messages_router
from .documents import router as documents_router

# Create API v1 router
api_router = APIRouter(prefix="/v1")

# Include all routers
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users_router, prefix="/users", tags=["Users"])
api_router.include_router(properties_router, prefix="/properties", tags=["Properties"])
api_router.include_router(tenants_router, prefix="/tenants", tags=["Tenants"])
api_router.include_router(payments_router, prefix="/payments", tags=["Payments"])
api_router.include_router(bills_router, prefix="/bills", tags=["Bills"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(webhooks_router, prefix="/webhooks", tags=["Webhooks"])
api_router.include_router(expenses_router, prefix="/expenses", tags=["Expenses"])
api_router.include_router(reports_router, prefix="/reports", tags=["Reports"])
api_router.include_router(sync_router, prefix="/sync", tags=["Sync"])
api_router.include_router(messages_router, prefix="/messages", tags=["Messages"])
api_router.include_router(documents_router, prefix="/documents", tags=["Documents"])

__all__ = ["api_router"]
