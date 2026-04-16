from fastapi import APIRouter

from .invoices import router as invoices_router

router = APIRouter()
router.include_router(invoices_router, tags=["invoices"])
