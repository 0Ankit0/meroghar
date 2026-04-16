from __future__ import annotations

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.finance.schemas.payment import InitiatePaymentResponse
from src.apps.iam.api.deps import get_current_user, get_db
from src.apps.iam.models.user import User
from src.apps.iam.utils.hashid import decode_id_or_404
from src.apps.invoicing.schemas import InvoicePaymentRequest
from src.apps.utility_billing.schemas import (
    UtilityBillAttachmentRead,
    UtilityBillCreateRequest,
    UtilityBillDisputeRead,
    UtilityBillDisputeRequest,
    UtilityBillDisputeResolveRequest,
    UtilityBillHistoryRead,
    UtilityBillListRead,
    UtilityBillRead,
    UtilityBillShareListRead,
    UtilityBillSplitConfigureRequest,
)
from src.apps.utility_billing.services.utility_bills import (
    configure_utility_bill_splits,
    create_utility_bill,
    dispute_bill_share,
    get_utility_bill_history,
    list_property_utility_bills,
    list_tenant_bill_shares,
    pay_bill_share,
    publish_utility_bill,
    resolve_bill_share_dispute,
    upload_utility_bill_attachment,
)

router = APIRouter()


@router.get("/properties/{property_id}/utility-bills", response_model=UtilityBillListRead)
async def list_property_utility_bills_endpoint(
    property_id: str,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UtilityBillListRead:
    payload = await list_property_utility_bills(
        db,
        decode_id_or_404(property_id),
        current_user,
        page=page,
        per_page=per_page,
    )
    return UtilityBillListRead.model_validate(payload)


@router.post("/properties/{property_id}/utility-bills", response_model=UtilityBillRead, status_code=status.HTTP_201_CREATED)
async def create_utility_bill_endpoint(
    property_id: str,
    data: UtilityBillCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UtilityBillRead:
    payload = await create_utility_bill(
        db,
        decode_id_or_404(property_id),
        current_user,
        bill_type=data.bill_type,
        billing_period_label=data.billing_period_label,
        period_start=data.period_start,
        period_end=data.period_end,
        due_date=data.due_date,
        total_amount=data.total_amount,
        owner_subsidy_amount=data.owner_subsidy_amount,
        notes=data.notes,
    )
    return UtilityBillRead.model_validate(payload)


@router.post("/utility-bills/{bill_id}/attachments", response_model=UtilityBillAttachmentRead)
async def upload_utility_bill_attachment_endpoint(
    bill_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UtilityBillAttachmentRead:
    payload = await upload_utility_bill_attachment(db, decode_id_or_404(bill_id), current_user, file)
    return UtilityBillAttachmentRead.model_validate(payload)


@router.post("/utility-bills/{bill_id}/splits", response_model=UtilityBillRead)
async def configure_utility_bill_splits_endpoint(
    bill_id: str,
    data: UtilityBillSplitConfigureRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UtilityBillRead:
    payload = await configure_utility_bill_splits(
        db,
        decode_id_or_404(bill_id),
        current_user,
        default_method=data.default_method,
        splits=data.splits,
    )
    return UtilityBillRead.model_validate(payload)


@router.post("/utility-bills/{bill_id}/publish", response_model=UtilityBillRead)
async def publish_utility_bill_endpoint(
    bill_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UtilityBillRead:
    payload = await publish_utility_bill(db, decode_id_or_404(bill_id), current_user)
    return UtilityBillRead.model_validate(payload)


@router.get("/tenants/me/bill-shares", response_model=UtilityBillShareListRead)
async def list_tenant_bill_shares_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UtilityBillShareListRead:
    payload = await list_tenant_bill_shares(db, current_user)
    return UtilityBillShareListRead.model_validate(payload)


@router.post("/bill-shares/{bill_share_id}/pay", response_model=InitiatePaymentResponse)
async def pay_bill_share_endpoint(
    bill_share_id: str,
    data: InvoicePaymentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InitiatePaymentResponse:
    return await pay_bill_share(
        db,
        decode_id_or_404(bill_share_id),
        current_user,
        data,
        allow_partial=False,
    )


@router.post("/bill-shares/{bill_share_id}/dispute", response_model=UtilityBillDisputeRead)
async def dispute_bill_share_endpoint(
    bill_share_id: str,
    data: UtilityBillDisputeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UtilityBillDisputeRead:
    payload = await dispute_bill_share(
        db,
        decode_id_or_404(bill_share_id),
        current_user,
        reason=data.reason,
    )
    return UtilityBillDisputeRead.model_validate(payload)


@router.post("/bill-shares/{bill_share_id}/resolve-dispute", response_model=UtilityBillDisputeRead)
async def resolve_bill_share_dispute_endpoint(
    bill_share_id: str,
    data: UtilityBillDisputeResolveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UtilityBillDisputeRead:
    payload = await resolve_bill_share_dispute(
        db,
        decode_id_or_404(bill_share_id),
        current_user,
        outcome=data.outcome,
        resolution_notes=data.resolution_notes,
    )
    return UtilityBillDisputeRead.model_validate(payload)


@router.get("/utility-bills/{bill_id}/history", response_model=UtilityBillHistoryRead)
async def get_utility_bill_history_endpoint(
    bill_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UtilityBillHistoryRead:
    payload = await get_utility_bill_history(db, decode_id_or_404(bill_id), current_user)
    return UtilityBillHistoryRead.model_validate(payload)
