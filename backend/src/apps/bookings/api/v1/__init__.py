from fastapi import APIRouter

from .bookings import router as bookings_router
from .webhooks import router as webhooks_router

router = APIRouter()
router.include_router(bookings_router, tags=["bookings"])
router.include_router(webhooks_router, tags=["bookings-webhooks"])
