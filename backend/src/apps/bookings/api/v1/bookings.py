from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.bookings.models.booking import BookingStatus
from src.apps.bookings.schemas import (
    AgreementGenerateRequest,
    BookingCancelRequest,
    BookingCreate,
    BookingDeclineRequest,
    BookingEventRead,
    BookingListRead,
    BookingRead,
    BookingReturnRequest,
    BookingUpdate,
    RentalAgreementRead,
)
from src.apps.bookings.services.agreements import (
    countersign_booking_agreement,
    generate_booking_agreement,
    get_booking_agreement_or_404,
    send_booking_agreement,
)
from src.apps.bookings.services.bookings import (
    cancel_booking,
    confirm_booking,
    create_booking,
    decline_booking,
    get_booking_detail,
    get_booking_events,
    list_bookings,
    return_booking,
    update_booking,
)
from src.apps.iam.api.deps import get_current_user, get_db
from src.apps.iam.models.user import User
from src.apps.iam.utils.hashid import decode_id_or_404

router = APIRouter(prefix="/bookings")


@router.get("", response_model=BookingListRead)
async def list_bookings_endpoint(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=50),
    status_filter: BookingStatus | None = Query(default=None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BookingListRead:
    payload = await list_bookings(
        db,
        current_user,
        page=page,
        per_page=per_page,
        status_filter=status_filter,
    )
    return BookingListRead.model_validate(payload)


@router.post("", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
async def create_booking_endpoint(
    data: BookingCreate,
    response: Response,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BookingRead:
    payload, created = await create_booking(
        db,
        current_user,
        data,
        idempotency_key=idempotency_key,
    )
    if not created:
        response.status_code = status.HTTP_200_OK
    return BookingRead.model_validate(payload)


@router.get("/{booking_id}", response_model=BookingRead)
async def get_booking_endpoint(
    booking_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BookingRead:
    payload = await get_booking_detail(db, decode_id_or_404(booking_id), current_user)
    return BookingRead.model_validate(payload)


@router.put("/{booking_id}", response_model=BookingRead)
async def update_booking_endpoint(
    booking_id: str,
    data: BookingUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BookingRead:
    payload = await update_booking(db, decode_id_or_404(booking_id), current_user, data)
    return BookingRead.model_validate(payload)


@router.post("/{booking_id}/confirm", response_model=BookingRead)
async def confirm_booking_endpoint(
    booking_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BookingRead:
    payload = await confirm_booking(db, decode_id_or_404(booking_id), current_user)
    return BookingRead.model_validate(payload)


@router.post("/{booking_id}/decline", response_model=BookingRead)
async def decline_booking_endpoint(
    booking_id: str,
    data: BookingDeclineRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BookingRead:
    payload = await decline_booking(db, decode_id_or_404(booking_id), current_user, data.reason)
    return BookingRead.model_validate(payload)


@router.post("/{booking_id}/cancel", response_model=BookingRead)
async def cancel_booking_endpoint(
    booking_id: str,
    data: BookingCancelRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BookingRead:
    payload = await cancel_booking(db, decode_id_or_404(booking_id), current_user, data.reason)
    return BookingRead.model_validate(payload)


@router.post("/{booking_id}/return", response_model=BookingRead)
async def return_booking_endpoint(
    booking_id: str,
    data: BookingReturnRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BookingRead:
    payload = await return_booking(db, decode_id_or_404(booking_id), current_user, data)
    return BookingRead.model_validate(payload)


@router.get("/{booking_id}/events", response_model=list[BookingEventRead])
async def get_booking_events_endpoint(
    booking_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[BookingEventRead]:
    events = await get_booking_events(db, decode_id_or_404(booking_id), current_user)
    return [BookingEventRead.model_validate(event) for event in events]


@router.get("/{booking_id}/agreement", response_model=RentalAgreementRead)
async def get_booking_agreement_endpoint(
    booking_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RentalAgreementRead:
    payload = await get_booking_agreement_or_404(db, decode_id_or_404(booking_id), current_user)
    return RentalAgreementRead.model_validate(payload)


@router.post("/{booking_id}/agreement", response_model=RentalAgreementRead, status_code=status.HTTP_201_CREATED)
async def generate_booking_agreement_endpoint(
    booking_id: str,
    data: AgreementGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RentalAgreementRead:
    payload = await generate_booking_agreement(db, decode_id_or_404(booking_id), current_user, data)
    return RentalAgreementRead.model_validate(payload)


@router.post("/{booking_id}/agreement/send", response_model=RentalAgreementRead)
async def send_booking_agreement_endpoint(
    booking_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RentalAgreementRead:
    payload = await send_booking_agreement(db, decode_id_or_404(booking_id), current_user)
    return RentalAgreementRead.model_validate(payload)


@router.post("/{booking_id}/agreement/countersign", response_model=RentalAgreementRead)
async def countersign_booking_agreement_endpoint(
    booking_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RentalAgreementRead:
    request_ip = request.client.host if request.client is not None else None
    payload = await countersign_booking_agreement(
        db,
        decode_id_or_404(booking_id),
        current_user,
        request_ip=request_ip,
    )
    return RentalAgreementRead.model_validate(payload)
