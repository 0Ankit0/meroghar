from fastapi import APIRouter

from .v1 import router as v1_router

search_router = APIRouter()
search_router.include_router(v1_router)
