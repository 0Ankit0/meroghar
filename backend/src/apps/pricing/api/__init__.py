from fastapi import APIRouter

from .v1 import router as v1_router

pricing_router = APIRouter()
pricing_router.include_router(v1_router)
