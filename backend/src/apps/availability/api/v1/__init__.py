from fastapi import APIRouter

from .availability import router as availability_router

router = APIRouter()
router.include_router(availability_router, tags=["availability"])
