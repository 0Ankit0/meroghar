from __future__ import annotations

from datetime import datetime
from math import isclose

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from src.apps.availability.models.availability_block import AvailabilityBlock, AvailabilityBlockType
from src.apps.availability.services.availability import calculate_duration_days, get_property_blocks
from src.apps.bookings.models.agreement import AgreementStatus, RentalAgreement
from src.apps.bookings.models.booking import (
    Booking,
    BookingEvent,
    BookingStatus,
    CancellationPolicy,
    SecurityDeposit,
    SecurityDepositStatus,
)
from src.apps.bookings.schemas.booking import BookingCreate, BookingReturnRequest, BookingUpdate
from src.apps.iam.models.user import User
from src.apps.iam.utils.identity import require_user_id
from src.apps.listings.models.property import Property
from src.apps.listings.services.properties import get_property_or_404
from src.apps.pricing.services.quote import (
    QuoteBreakdown,
    build_quote_from_rules,
    get_property_pricing_rules,
    quote_property_period,
)

_DEFAULT_CANCELLATION_POLICY = {
    "name": "Standard cancellation policy",
    "free_cancellation_hours": 72,
    "partial_refund_hours": 24,
    "partial_refund_percent": 50.0,
}


def _money(value: float) -> float:
    return round(float(value), 2)


def get_effective_booking_status(
    booking: Booking,
    *,
    now: datetime | None = None,
) -> BookingStatus:
    current_time = now or datetime.now()
    if (
        booking.status == BookingStatus.CONFIRMED
        and booking.actual_return_at is None
        and booking.rental_start_at <= current_time
    ):
        return BookingStatus.ACTIVE
    return booking.status


async def _get_security_deposit(db: AsyncSession, booking_id: int) -> SecurityDeposit | None:
    result = await db.execute(
        select(SecurityDeposit).where(SecurityDeposit.booking_id == booking_id)
    )
    return result.scalars().first()


async def _get_latest_agreement(db: AsyncSession, booking_id: int) -> RentalAgreement | None:
    result = await db.execute(
        select(RentalAgreement)
        .where(RentalAgreement.booking_id == booking_id)
        .order_by(col(RentalAgreement.created_at).desc(), col(RentalAgreement.id).desc())
    )
    return result.scalars().first()


async def _get_cancellation_policy(db: AsyncSession, property_id: int) -> CancellationPolicy:
    result = await db.execute(
        select(CancellationPolicy).where(CancellationPolicy.property_id == property_id)
    )
    policy = result.scalars().first()
    if policy is not None:
        return policy
    return CancellationPolicy(property_id=property_id, **_DEFAULT_CANCELLATION_POLICY)


async def emit_booking_event(
    db: AsyncSession,
    booking_id: int,
    event_type: str,
    message: str,
    *,
    actor_user_id: int | None = None,
    metadata: dict[str, object] | None = None,
) -> BookingEvent:
    event = BookingEvent(
        booking_id=booking_id,
        event_type=event_type,
        message=message,
        actor_user_id=actor_user_id,
        metadata_json=metadata,
    )
    db.add(event)
    await db.flush()
    return event


async def get_accessible_booking_for_user(
    db: AsyncSession,
    booking_id: int,
    current_user: User,
) -> Booking:
    booking = await db.get(Booking, booking_id)
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    user_id = require_user_id(current_user.id)
    if current_user.is_superuser:
        return booking
    if booking.tenant_user_id == user_id or booking.owner_user_id == user_id:
        return booking
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to access this booking")


async def get_manageable_booking_for_user(
    db: AsyncSession,
    booking_id: int,
    current_user: User,
) -> Booking:
    booking = await db.get(Booking, booking_id)
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    user_id = require_user_id(current_user.id)
    if current_user.is_superuser or booking.owner_user_id == user_id:
        return booking
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to manage this booking")


async def build_booking_payload(db: AsyncSession, booking: Booking) -> dict[str, object]:
    property_obj = await get_property_or_404(db, booking.property_id)
    security_deposit = await _get_security_deposit(db, booking.id)
    cancellation_policy = await _get_cancellation_policy(db, booking.property_id)
    latest_agreement = await _get_latest_agreement(db, booking.id)
    security_deposit_payload = None
    if security_deposit is not None:
        security_deposit_payload = {
            "id": security_deposit.id,
            "booking_id": security_deposit.booking_id,
            "amount": _money(security_deposit.amount),
            "status": security_deposit.status,
            "gateway_ref": security_deposit.gateway_ref,
            "deduction_total": _money(security_deposit.deduction_total),
            "refund_amount": _money(security_deposit.refund_amount),
            "collected_at": security_deposit.collected_at,
            "settled_at": security_deposit.settled_at,
        }

    return {
        "id": booking.id,
        "booking_number": booking.booking_number,
        "status": get_effective_booking_status(booking),
        "property": {
            "id": property_obj.id,
            "name": property_obj.name,
            "location_address": property_obj.location_address,
        },
        "tenant_user_id": booking.tenant_user_id,
        "owner_user_id": booking.owner_user_id,
        "rental_start_at": booking.rental_start_at,
        "rental_end_at": booking.rental_end_at,
        "actual_return_at": booking.actual_return_at,
        "special_requests": booking.special_requests,
        "pricing": {
            "currency": booking.currency,
            "base_fee": _money(booking.base_fee),
            "peak_surcharge": _money(booking.peak_surcharge),
            "tax_amount": _money(booking.tax_amount),
            "total_fee": _money(booking.total_fee),
            "deposit_amount": _money(booking.deposit_amount),
            "total_due_now": _money(booking.total_fee + booking.deposit_amount),
        },
        "security_deposit": security_deposit_payload,
        "cancellation_policy": {
            "name": cancellation_policy.name,
            "free_cancellation_hours": cancellation_policy.free_cancellation_hours,
            "partial_refund_hours": cancellation_policy.partial_refund_hours,
            "partial_refund_percent": _money(cancellation_policy.partial_refund_percent),
        },
        "decline_reason": booking.decline_reason,
        "cancellation_reason": booking.cancellation_reason,
        "cancelled_at": booking.cancelled_at,
        "confirmed_at": booking.confirmed_at,
        "declined_at": booking.declined_at,
        "refund_amount": _money(booking.refund_amount),
        "agreement_status": latest_agreement.status if latest_agreement is not None else None,
        "created_at": booking.created_at,
        "updated_at": booking.updated_at,
    }


def _assert_quote_matches(
    data: BookingCreate | BookingUpdate,
    quote: QuoteBreakdown,
) -> None:
    actual_currency = quote.currency
    actual_total_fee = _money(float(quote.total_fee))
    actual_deposit_amount = _money(float(quote.deposit_amount))

    stale = False
    quoted_currency = getattr(data, "quoted_currency", None)
    if quoted_currency and quoted_currency.strip().upper() != actual_currency:
        stale = True
    quoted_total_fee = getattr(data, "quoted_total_fee", None)
    if quoted_total_fee is not None and not isclose(quoted_total_fee, actual_total_fee, abs_tol=0.01):
        stale = True
    quoted_deposit_amount = getattr(data, "quoted_deposit_amount", None)
    if quoted_deposit_amount is not None and not isclose(quoted_deposit_amount, actual_deposit_amount, abs_tol=0.01):
        stale = True

    if stale:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "STALE_BOOKING_QUOTE",
                "message": "Quoted pricing is out of date. Refresh pricing and try again.",
                "actual": {
                    "currency": actual_currency,
                    "total_fee": actual_total_fee,
                    "deposit_amount": actual_deposit_amount,
                    "total_due_now": _money(actual_total_fee + actual_deposit_amount),
                },
            },
        )


async def _ensure_booking_window_available(
    db: AsyncSession,
    property_id: int,
    start_at: datetime,
    end_at: datetime,
    *,
    ignore_booking_id: int | None = None,
) -> None:
    blocks = await get_property_blocks(db, property_id)
    conflicts = [
        block
        for block in blocks
        if start_at < block.end_at
        and block.start_at < end_at
        and not (ignore_booking_id is not None and block.booking_id == ignore_booking_id)
    ]
    if conflicts:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "BOOKING_UNAVAILABLE",
                "message": "The property is not available for the selected dates.",
            },
        )


async def _get_booking_hold_block(db: AsyncSession, booking_id: int) -> AvailabilityBlock | None:
    result = await db.execute(
        select(AvailabilityBlock)
        .where(
            AvailabilityBlock.booking_id == booking_id,
            AvailabilityBlock.block_type == AvailabilityBlockType.BOOKING,
        )
        .order_by(col(AvailabilityBlock.id).desc())
    )
    return result.scalars().first()


async def _upsert_booking_hold_block(db: AsyncSession, booking: Booking) -> AvailabilityBlock:
    block = await _get_booking_hold_block(db, booking.id)
    if block is None:
        block = AvailabilityBlock(
            property_id=booking.property_id,
            booking_id=booking.id,
            block_type=AvailabilityBlockType.BOOKING,
            start_at=booking.rental_start_at,
            end_at=booking.rental_end_at,
            reason=f"Booking hold for {booking.booking_number or booking.id}",
        )
    else:
        block.start_at = booking.rental_start_at
        block.end_at = booking.rental_end_at
        block.reason = f"Booking hold for {booking.booking_number or booking.id}"
    db.add(block)
    await db.flush()
    return block


async def _release_booking_hold(
    db: AsyncSession,
    booking: Booking,
    *,
    actual_end_at: datetime | None = None,
) -> None:
    block = await _get_booking_hold_block(db, booking.id)
    if block is None:
        return
    if actual_end_at is None or actual_end_at <= block.start_at:
        await db.delete(block)
        return
    block.end_at = actual_end_at
    db.add(block)


async def _upsert_security_deposit(
    db: AsyncSession,
    booking: Booking,
    *,
    collected_at: datetime | None = None,
) -> SecurityDeposit:
    deposit = await _get_security_deposit(db, booking.id)
    if deposit is None:
        deposit = SecurityDeposit(
            booking_id=booking.id,
            amount=_money(booking.deposit_amount),
            status=SecurityDepositStatus.HELD,
            gateway_ref=booking.payment_method_id,
            deduction_total=0.0,
            refund_amount=0.0,
            collected_at=collected_at if booking.deposit_amount > 0 else None,
        )
    else:
        deposit.amount = _money(booking.deposit_amount)
        deposit.gateway_ref = booking.payment_method_id
        if deposit.status == SecurityDepositStatus.HELD and deposit.amount > 0 and deposit.collected_at is None:
            deposit.collected_at = collected_at or datetime.now()
    db.add(deposit)
    await db.flush()
    return deposit


async def _refund_security_deposit_full(
    db: AsyncSession,
    booking: Booking,
    *,
    settled_at: datetime,
) -> None:
    deposit = await _get_security_deposit(db, booking.id)
    if deposit is None:
        return
    deposit.status = SecurityDepositStatus.FULLY_REFUNDED
    deposit.refund_amount = _money(deposit.amount)
    deposit.settled_at = settled_at
    db.add(deposit)


async def _terminate_latest_agreement(
    db: AsyncSession,
    booking: Booking,
    *,
    actor_user_id: int | None,
    message: str,
) -> None:
    agreement = await _get_latest_agreement(db, booking.id)
    if agreement is None or agreement.status == AgreementStatus.TERMINATED:
        return
    previous_status = agreement.status
    agreement.status = AgreementStatus.TERMINATED
    db.add(agreement)
    await emit_booking_event(
        db,
        booking.id,
        "agreement.terminated",
        message,
        actor_user_id=actor_user_id,
        metadata={
            "agreement_id": agreement.id,
            "previous_status": previous_status.value,
        },
    )


def _calculate_booking_refund(
    booking: Booking,
    policy: CancellationPolicy,
    *,
    current_time: datetime,
    effective_status: BookingStatus,
) -> float:
    if effective_status == BookingStatus.ACTIVE or current_time >= booking.rental_start_at:
        return 0.0

    hours_until_start = (booking.rental_start_at - current_time).total_seconds() / 3600
    if hours_until_start >= policy.free_cancellation_hours:
        return _money(booking.total_fee)
    if hours_until_start >= policy.partial_refund_hours:
        return _money(booking.total_fee * (policy.partial_refund_percent / 100))
    return 0.0


async def _quote_for_update(
    db: AsyncSession,
    property_obj: Property,
    booking: Booking,
    *,
    start_at: datetime,
    end_at: datetime,
    effective_status: BookingStatus,
) -> QuoteBreakdown:
    await _ensure_booking_window_available(
        db,
        property_obj.id,
        start_at,
        end_at,
        ignore_booking_id=booking.id,
    )
    if effective_status == BookingStatus.ACTIVE:
        if end_at <= start_at:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="end must be after start",
            )
        duration_hours = (end_at - start_at).total_seconds() / 3600
        if duration_hours < property_obj.min_rental_duration_hours:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Requested duration is shorter than the minimum rental duration",
            )
        duration_days = calculate_duration_days(start_at, end_at)
        if duration_days > property_obj.max_rental_duration_days:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Requested duration exceeds the maximum rental duration",
            )
        pricing_rules = await get_property_pricing_rules(db, property_obj.id)
        return build_quote_from_rules(property_obj, pricing_rules, start_at, end_at, duration_days)
    return await quote_property_period(
        db,
        property_obj,
        start_at,
        end_at,
        skip_availability_check=True,
    )


async def list_bookings(
    db: AsyncSession,
    current_user: User,
    *,
    page: int,
    per_page: int,
    status_filter: BookingStatus | None = None,
) -> dict[str, object]:
    user_id = require_user_id(current_user.id)
    query = select(Booking).order_by(col(Booking.updated_at).desc(), col(Booking.id).desc())
    if not current_user.is_superuser:
        query = query.where(
            or_(Booking.tenant_user_id == user_id, Booking.owner_user_id == user_id)
        )

    result = await db.execute(query)
    bookings = list(result.scalars().all())
    if status_filter is not None:
        bookings = [
            booking
            for booking in bookings
            if get_effective_booking_status(booking) == status_filter
        ]

    total = len(bookings)
    start_index = (page - 1) * per_page
    page_items = bookings[start_index : start_index + per_page]
    items = [await build_booking_payload(db, booking) for booking in page_items]
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "has_more": start_index + len(items) < total,
    }


async def get_booking_detail(
    db: AsyncSession,
    booking_id: int,
    current_user: User,
) -> dict[str, object]:
    booking = await get_accessible_booking_for_user(db, booking_id, current_user)
    return await build_booking_payload(db, booking)


async def get_booking_events(
    db: AsyncSession,
    booking_id: int,
    current_user: User,
) -> list[BookingEvent]:
    await get_accessible_booking_for_user(db, booking_id, current_user)
    result = await db.execute(
        select(BookingEvent)
        .where(BookingEvent.booking_id == booking_id)
        .order_by(col(BookingEvent.created_at), col(BookingEvent.id))
    )
    return list(result.scalars().all())


async def create_booking(
    db: AsyncSession,
    current_user: User,
    data: BookingCreate,
    *,
    idempotency_key: str | None = None,
) -> tuple[dict[str, object], bool]:
    tenant_user_id = require_user_id(current_user.id)
    normalized_idempotency_key = idempotency_key.strip() if idempotency_key and idempotency_key.strip() else None

    if normalized_idempotency_key is not None:
        existing_result = await db.execute(
            select(Booking).where(
                Booking.tenant_user_id == tenant_user_id,
                Booking.idempotency_key == normalized_idempotency_key,
            )
        )
        existing_booking = existing_result.scalars().first()
        if existing_booking is not None:
            matches_existing_request = (
                existing_booking.property_id == data.property_id
                and existing_booking.rental_start_at == data.rental_start_at
                and existing_booking.rental_end_at == data.rental_end_at
                and existing_booking.payment_method_id == data.payment_method_id
                and existing_booking.special_requests == data.special_requests
            )
            if not matches_existing_request:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Idempotency key already used for a different booking request",
                )
            return await build_booking_payload(db, existing_booking), False

    property_obj = await get_property_or_404(db, data.property_id, published_only=True)
    if property_obj.owner_user_id == tenant_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot create a booking for your own property",
        )

    quote = await quote_property_period(db, property_obj, data.rental_start_at, data.rental_end_at)
    _assert_quote_matches(data, quote)

    current_time = datetime.now()
    booking_status = BookingStatus.CONFIRMED if property_obj.instant_booking_enabled else BookingStatus.PENDING
    booking = Booking(
        booking_number="",
        property_id=property_obj.id,
        tenant_user_id=tenant_user_id,
        owner_user_id=property_obj.owner_user_id,
        status=booking_status,
        rental_start_at=data.rental_start_at,
        rental_end_at=data.rental_end_at,
        special_requests=data.special_requests,
        payment_method_id=data.payment_method_id,
        currency=quote.currency,
        base_fee=_money(float(quote.base_fee)),
        peak_surcharge=_money(float(quote.peak_surcharge)),
        tax_amount=_money(float(quote.tax_amount)),
        total_fee=_money(float(quote.total_fee)),
        deposit_amount=_money(float(quote.deposit_amount)),
        confirmed_at=current_time if booking_status == BookingStatus.CONFIRMED else None,
        idempotency_key=normalized_idempotency_key,
        created_at=current_time,
        updated_at=current_time,
    )
    db.add(booking)
    await db.flush()

    booking.booking_number = f"BKG-{current_time.year}-{booking.id:05d}"
    db.add(booking)
    await _upsert_booking_hold_block(db, booking)
    await _upsert_security_deposit(db, booking, collected_at=current_time)
    await emit_booking_event(
        db,
        booking.id,
        "booking.created",
        f"Booking {booking.booking_number} submitted for review.",
        actor_user_id=tenant_user_id,
        metadata={"status": booking.status.value},
    )
    if booking.status == BookingStatus.CONFIRMED:
        await emit_booking_event(
            db,
            booking.id,
            "booking.confirmed",
            "Booking auto-confirmed because instant booking is enabled.",
            actor_user_id=tenant_user_id,
            metadata={"instant_booking": True},
        )

    await db.commit()
    await db.refresh(booking)
    return await build_booking_payload(db, booking), True


async def update_booking(
    db: AsyncSession,
    booking_id: int,
    current_user: User,
    data: BookingUpdate,
) -> dict[str, object]:
    booking = await get_accessible_booking_for_user(db, booking_id, current_user)
    user_id = require_user_id(current_user.id)
    is_manager = current_user.is_superuser or booking.owner_user_id == user_id
    is_tenant = booking.tenant_user_id == user_id
    effective_status = get_effective_booking_status(booking)
    if effective_status in {
        BookingStatus.CANCELLED,
        BookingStatus.CLOSED,
        BookingStatus.DECLINED,
        BookingStatus.PENDING_CLOSURE,
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This booking can no longer be updated",
        )

    current_time = datetime.now()
    if is_tenant and current_time >= booking.rental_start_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenants can only update bookings before the stay starts",
        )
    if effective_status == BookingStatus.ACTIVE and not is_manager:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the property owner can update an active booking",
        )

    if effective_status == BookingStatus.ACTIVE and data.rental_start_at is not None and data.rental_start_at != booking.rental_start_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Active bookings may only extend or shorten the end date",
        )

    next_start_at = data.rental_start_at or booking.rental_start_at
    next_end_at = data.rental_end_at or booking.rental_end_at
    if next_end_at <= next_start_at:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end must be after start",
        )

    property_obj = await get_property_or_404(db, booking.property_id)
    quote = await _quote_for_update(
        db,
        property_obj,
        booking,
        start_at=next_start_at,
        end_at=next_end_at,
        effective_status=effective_status,
    )
    _assert_quote_matches(data, quote)

    previous_window = {
        "rental_start_at": booking.rental_start_at.isoformat(),
        "rental_end_at": booking.rental_end_at.isoformat(),
    }
    booking.rental_start_at = next_start_at
    booking.rental_end_at = next_end_at
    if data.special_requests is not None:
        booking.special_requests = data.special_requests
    booking.currency = quote.currency
    booking.base_fee = _money(float(quote.base_fee))
    booking.peak_surcharge = _money(float(quote.peak_surcharge))
    booking.tax_amount = _money(float(quote.tax_amount))
    booking.total_fee = _money(float(quote.total_fee))
    booking.deposit_amount = _money(float(quote.deposit_amount))
    booking.updated_at = current_time
    db.add(booking)

    await _upsert_booking_hold_block(db, booking)
    await _upsert_security_deposit(db, booking)
    await emit_booking_event(
        db,
        booking.id,
        "booking.updated",
        "Booking details were updated.",
        actor_user_id=user_id,
        metadata={
            **previous_window,
            "updated_rental_start_at": booking.rental_start_at.isoformat(),
            "updated_rental_end_at": booking.rental_end_at.isoformat(),
        },
    )

    await db.commit()
    await db.refresh(booking)
    return await build_booking_payload(db, booking)


async def confirm_booking(
    db: AsyncSession,
    booking_id: int,
    current_user: User,
) -> dict[str, object]:
    booking = await get_manageable_booking_for_user(db, booking_id, current_user)
    if booking.status == BookingStatus.CONFIRMED and booking.confirmed_at is not None:
        return await build_booking_payload(db, booking)
    if booking.status != BookingStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending bookings can be confirmed",
        )

    current_time = datetime.now()
    actor_user_id = require_user_id(current_user.id)
    booking.status = BookingStatus.CONFIRMED
    booking.confirmed_at = current_time
    booking.updated_at = current_time
    db.add(booking)
    await _upsert_security_deposit(db, booking, collected_at=current_time)
    await emit_booking_event(
        db,
        booking.id,
        "booking.confirmed",
        "Booking confirmed and moved into the active workflow.",
        actor_user_id=actor_user_id,
        metadata={"status": booking.status.value},
    )
    await db.commit()
    await db.refresh(booking)
    return await build_booking_payload(db, booking)


async def decline_booking(
    db: AsyncSession,
    booking_id: int,
    current_user: User,
    reason: str,
) -> dict[str, object]:
    booking = await get_manageable_booking_for_user(db, booking_id, current_user)
    if booking.status == BookingStatus.DECLINED and booking.declined_at is not None:
        return await build_booking_payload(db, booking)
    if booking.status != BookingStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending bookings can be declined",
        )

    current_time = datetime.now()
    actor_user_id = require_user_id(current_user.id)
    booking.status = BookingStatus.DECLINED
    booking.decline_reason = reason.strip()
    booking.declined_at = current_time
    booking.refund_amount = _money(booking.total_fee)
    booking.updated_at = current_time
    db.add(booking)

    await _release_booking_hold(db, booking)
    await _refund_security_deposit_full(db, booking, settled_at=current_time)
    await _terminate_latest_agreement(
        db,
        booking,
        actor_user_id=actor_user_id,
        message="Agreement terminated because the booking was declined.",
    )
    await emit_booking_event(
        db,
        booking.id,
        "booking.declined",
        booking.decline_reason or "Booking request was declined.",
        actor_user_id=actor_user_id,
        metadata={"refund_amount": booking.refund_amount},
    )

    await db.commit()
    await db.refresh(booking)
    return await build_booking_payload(db, booking)


async def cancel_booking(
    db: AsyncSession,
    booking_id: int,
    current_user: User,
    reason: str,
) -> dict[str, object]:
    booking = await get_accessible_booking_for_user(db, booking_id, current_user)
    user_id = require_user_id(current_user.id)
    effective_status = get_effective_booking_status(booking)
    if booking.status == BookingStatus.CANCELLED and booking.cancelled_at is not None:
        return await build_booking_payload(db, booking)
    if booking.status in {BookingStatus.CLOSED, BookingStatus.DECLINED}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This booking can no longer be cancelled",
        )

    current_time = datetime.now()
    policy = await _get_cancellation_policy(db, booking.property_id)
    booking.status = BookingStatus.CANCELLED
    booking.cancellation_reason = reason.strip()
    booking.cancelled_at = current_time
    booking.refund_amount = _calculate_booking_refund(
        booking,
        policy,
        current_time=current_time,
        effective_status=effective_status,
    )
    if effective_status == BookingStatus.ACTIVE:
        booking.actual_return_at = current_time
        await _release_booking_hold(db, booking, actual_end_at=current_time)
    else:
        await _release_booking_hold(db, booking)
    booking.updated_at = current_time
    db.add(booking)

    await _refund_security_deposit_full(db, booking, settled_at=current_time)
    await _terminate_latest_agreement(
        db,
        booking,
        actor_user_id=user_id,
        message="Agreement terminated because the booking was cancelled.",
    )
    await emit_booking_event(
        db,
        booking.id,
        "booking.cancelled",
        booking.cancellation_reason or "Booking cancelled.",
        actor_user_id=user_id,
        metadata={
            "refund_amount": booking.refund_amount,
            "status": effective_status.value,
        },
    )

    await db.commit()
    await db.refresh(booking)
    return await build_booking_payload(db, booking)


async def return_booking(
    db: AsyncSession,
    booking_id: int,
    current_user: User,
    data: BookingReturnRequest,
) -> dict[str, object]:
    booking = await get_manageable_booking_for_user(db, booking_id, current_user)
    user_id = require_user_id(current_user.id)
    effective_status = get_effective_booking_status(booking)
    if booking.status == BookingStatus.CLOSED and booking.actual_return_at is not None:
        return await build_booking_payload(db, booking)
    if effective_status not in {
        BookingStatus.CONFIRMED,
        BookingStatus.ACTIVE,
        BookingStatus.PENDING_CLOSURE,
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only confirmed or active bookings can be returned",
        )

    current_time = datetime.now()
    actual_return_at = data.actual_return_at or current_time
    if actual_return_at < booking.rental_start_at:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="actual_return_at must be on or after rental_start_at",
        )

    booking.actual_return_at = actual_return_at
    booking.status = BookingStatus.CLOSED
    booking.updated_at = current_time
    db.add(booking)

    await _release_booking_hold(db, booking, actual_end_at=actual_return_at)
    await _refund_security_deposit_full(db, booking, settled_at=current_time)
    await _terminate_latest_agreement(
        db,
        booking,
        actor_user_id=user_id,
        message="Agreement terminated because the booking closed.",
    )
    await emit_booking_event(
        db,
        booking.id,
        "booking.returned",
        data.notes.strip() or "Return recorded and booking closed.",
        actor_user_id=user_id,
        metadata={
            "actual_return_at": actual_return_at.isoformat(),
            "notes": data.notes or None,
        },
    )

    await db.commit()
    await db.refresh(booking)
    return await build_booking_payload(db, booking)
