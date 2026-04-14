from fastapi import APIRouter

from .pricing_rules import router as pricing_router

router = APIRouter()
router.include_router(pricing_router, tags=["pricing"])
