from fastapi import APIRouter

from .utility_bills import router as utility_bills_router

router = APIRouter()
router.include_router(utility_bills_router, tags=["utility-bills"])
