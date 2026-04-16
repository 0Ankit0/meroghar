from fastapi import APIRouter

from .v1 import router as v1_router

utility_billing_router = APIRouter()
utility_billing_router.include_router(v1_router)
