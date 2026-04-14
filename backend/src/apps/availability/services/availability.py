from __future__ import annotations

import math
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from src.apps.availability.models.availability_block import AvailabilityBlock
from src.apps.listings.models.property import Property


async def get_property_blocks(db: AsyncSession, property_id: int) -> list[AvailabilityBlock]:
    result = await db.execute(
        select(AvailabilityBlock)
        .where(AvailabilityBlock.property_id == property_id)
        .order_by(col(AvailabilityBlock.start_at), col(AvailabilityBlock.end_at))
    )
    return list(result.scalars().all())


def blocks_overlap(start_at: datetime, end_at: datetime, block: AvailabilityBlock) -> bool:
    return start_at < block.end_at and block.start_at < end_at


def get_overlapping_blocks(
    blocks: list[AvailabilityBlock],
    start_at: datetime,
    end_at: datetime,
) -> list[AvailabilityBlock]:
    return [block for block in blocks if blocks_overlap(start_at, end_at, block)]


def calculate_duration_days(start_at: datetime, end_at: datetime) -> int:
    seconds = (end_at - start_at).total_seconds()
    return max(1, math.ceil(seconds / 86400))


def validate_booking_window(
    property_obj: Property,
    start_at: datetime,
    end_at: datetime,
    *,
    now: datetime | None = None,
) -> int:
    if end_at <= start_at:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end must be after start",
        )

    current_time = now or datetime.now()
    if property_obj.booking_lead_time_hours > 0:
        minimum_start = current_time + timedelta(hours=property_obj.booking_lead_time_hours)
        if start_at < minimum_start:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Requested start does not satisfy booking lead time",
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

    return duration_days


async def get_conflicting_blocks(
    db: AsyncSession,
    property_id: int,
    start_at: datetime,
    end_at: datetime,
) -> list[AvailabilityBlock]:
    blocks = await get_property_blocks(db, property_id)
    return get_overlapping_blocks(blocks, start_at, end_at)


def compute_next_available_start(
    blocks: list[AvailabilityBlock],
    start_at: datetime,
    end_at: datetime,
) -> datetime | None:
    conflicts = sorted(get_overlapping_blocks(blocks, start_at, end_at), key=lambda block: block.start_at)
    if not conflicts:
        return None

    candidate = max(end_at, conflicts[0].end_at)
    changed = True
    while changed:
        changed = False
        for block in blocks:
            if block.start_at <= candidate < block.end_at:
                if block.end_at > candidate:
                    candidate = block.end_at
                    changed = True
    return candidate


async def ensure_property_available(
    db: AsyncSession,
    property_obj: Property,
    start_at: datetime,
    end_at: datetime,
) -> list[AvailabilityBlock]:
    conflicts = await get_conflicting_blocks(db, property_obj.id, start_at, end_at)
    if conflicts:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "BOOKING_UNAVAILABLE",
                "message": "The property is not available for the selected dates.",
            },
        )
    return conflicts
