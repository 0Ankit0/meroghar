from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.bookings.schemas import EsignWebhookRequest, EsignWebhookResponse, RentalAgreementRead
from src.apps.bookings.services.agreements import process_esign_webhook
from src.apps.iam.api.deps import get_db

router = APIRouter(prefix="/webhooks")


@router.post("/esign", response_model=EsignWebhookResponse)
async def receive_esign_webhook(
    data: EsignWebhookRequest,
    db: AsyncSession = Depends(get_db),
) -> EsignWebhookResponse:
    payload = await process_esign_webhook(db, data)
    return EsignWebhookResponse(
        status="processed",
        agreement=RentalAgreementRead.model_validate(payload),
    )
