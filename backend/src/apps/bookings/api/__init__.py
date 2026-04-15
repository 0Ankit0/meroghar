from fastapi import APIRouter

from .v1 import router as v1_router

bookings_router = APIRouter()
bookings_router.include_router(v1_router)
