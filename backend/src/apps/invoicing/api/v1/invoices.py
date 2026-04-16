from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.iam.api.deps import get_current_user, get_db
from src.apps.iam.models.user import User
from src.apps.iam.utils.hashid import decode_id_or_404
from src.apps.finance.schemas.payment import InitiatePaymentResponse
from src.apps.invoicing.models.invoice import InvoiceStatus
from src.apps.invoicing.schemas import (
    AdditionalChargeCreateRequest,
    AdditionalChargeDisputeRequest,
    AdditionalChargeRead,
    AdditionalChargeResolveRequest,
    InvoiceListRead,
    InvoicePaymentRequest,
    InvoiceRead,
    RentLedgerRead,
)
from src.apps.invoicing.services.invoices import (
    create_additional_charge,
    dispute_additional_charge,
    get_invoice_detail,
    get_invoice_receipt_text,
    get_rent_ledger,
    initiate_invoice_payment,
    list_invoices,
    resolve_additional_charge,
)

router = APIRouter()


@router.get("/invoices", response_model=InvoiceListRead)
async def list_invoices_endpoint(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=50),
    status_filter: InvoiceStatus | None = Query(default=None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InvoiceListRead:
    payload = await list_invoices(db, current_user, page=page, per_page=per_page, status_filter=status_filter)
    return InvoiceListRead.model_validate(payload)


@router.get("/invoices/{invoice_id}", response_model=InvoiceRead)
async def get_invoice_endpoint(
    invoice_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InvoiceRead:
    payload = await get_invoice_detail(db, decode_id_or_404(invoice_id), current_user)
    return InvoiceRead.model_validate(payload)


@router.post("/invoices/{invoice_id}/pay", response_model=InitiatePaymentResponse)
async def pay_invoice_endpoint(
    invoice_id: str,
    data: InvoicePaymentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InitiatePaymentResponse:
    response = await initiate_invoice_payment(
        db,
        decode_id_or_404(invoice_id),
        current_user,
        data,
        allow_partial=False,
    )
    return response


@router.post("/invoices/{invoice_id}/partial-pay", response_model=InitiatePaymentResponse)
async def partial_pay_invoice_endpoint(
    invoice_id: str,
    data: InvoicePaymentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InitiatePaymentResponse:
    response = await initiate_invoice_payment(
        db,
        decode_id_or_404(invoice_id),
        current_user,
        data,
        allow_partial=True,
    )
    return response


@router.get("/invoices/{invoice_id}/receipt")
async def get_invoice_receipt_endpoint(
    invoice_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    receipt = await get_invoice_receipt_text(db, decode_id_or_404(invoice_id), current_user)
    decoded_invoice_id = decode_id_or_404(invoice_id)
    return PlainTextResponse(
        content=receipt,
        headers={"Content-Disposition": f'attachment; filename="invoice-{decoded_invoice_id}-receipt.txt"'},
    )


@router.get("/bookings/{booking_id}/rent-ledger", response_model=RentLedgerRead)
async def get_rent_ledger_endpoint(
    booking_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RentLedgerRead:
    payload = await get_rent_ledger(db, decode_id_or_404(booking_id), current_user)
    return RentLedgerRead.model_validate(payload)


@router.post("/bookings/{booking_id}/additional-charges", response_model=AdditionalChargeRead, status_code=status.HTTP_201_CREATED)
async def create_additional_charge_endpoint(
    booking_id: str,
    data: AdditionalChargeCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AdditionalChargeRead:
    payload = await create_additional_charge(
        db,
        decode_id_or_404(booking_id),
        current_user,
        charge_type=data.charge_type,
        description=data.description,
        amount=data.amount,
        evidence_url=data.evidence_url,
    )
    return AdditionalChargeRead.model_validate(payload)


@router.post("/additional-charges/{charge_id}/dispute", response_model=AdditionalChargeRead)
async def dispute_additional_charge_endpoint(
    charge_id: str,
    data: AdditionalChargeDisputeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AdditionalChargeRead:
    payload = await dispute_additional_charge(
        db,
        decode_id_or_404(charge_id),
        current_user,
        reason=data.reason,
    )
    return AdditionalChargeRead.model_validate(payload)


@router.post("/additional-charges/{charge_id}/resolve", response_model=AdditionalChargeRead)
async def resolve_additional_charge_endpoint(
    charge_id: str,
    data: AdditionalChargeResolveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AdditionalChargeRead:
    payload = await resolve_additional_charge(
        db,
        decode_id_or_404(charge_id),
        current_user,
        outcome=data.outcome,
        resolved_amount=data.resolved_amount,
        resolution_notes=data.resolution_notes,
    )
    return AdditionalChargeRead.model_validate(payload)
