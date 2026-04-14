from fastapi import APIRouter

from .assets import router as assets_router
from .categories import router as categories_router
from .properties import router as properties_router

router = APIRouter()
router.include_router(categories_router, tags=["categories"])
router.include_router(assets_router, tags=["assets"])
router.include_router(properties_router, tags=["properties"])
