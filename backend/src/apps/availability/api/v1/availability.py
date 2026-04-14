from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.apps.availability.models.availability_block import AvailabilityBlock
from src.apps.availability.schemas.availability import (
    AvailabilityBlockCreate,
    AvailabilityBlockRead,
    AvailabilityBlockUpdate,
    AvailabilityQueryRead,
)
from src.apps.availability.services.availability import (
    compute_next_available_start,
    get_overlapping_blocks,
    get_property_blocks,
)
from src.apps.iam.api.deps import get_current_user, get_db
from src.apps.iam.models.user import User
from src.apps.iam.utils.hashid import decode_id_or_404
from src.apps.listings.services.properties import get_property_or_404, require_property_owner, touch_property

router = APIRouter(prefix="/properties/{property_id}")


@router.get("/availability", response_model=AvailabilityQueryRead)
async def get_property_availability(
    property_id: str,
    start: datetime = Query(..., alias="start"),
    end: datetime = Query(..., alias="end"),
    db: AsyncSession = Depends(get_db),
) -> AvailabilityQueryRead:
    if end <= start:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="end must be after start")
    property_obj = await get_property_or_404(db, decode_id_or_404(property_id), published_only=True)
    blocks = await get_property_blocks(db, property_obj.id)
    conflicts = get_overlapping_blocks(blocks, start, end)
    return AvailabilityQueryRead.model_validate(
        {
            "property_id": property_obj.id,
            "start_at": start,
            "end_at": end,
            "is_available": not conflicts,
            "next_available_start": compute_next_available_start(blocks, start, end),
            "conflicts": conflicts,
        }
    )


def _validate_no_block_overlap(
    blocks: list[AvailabilityBlock],
    start_at: datetime,
    end_at: datetime,
    *,
    ignore_block_id: int | None = None,
) -> None:
    for block in blocks:
        if ignore_block_id is not None and block.id == ignore_block_id:
            continue
        if start_at < block.end_at and block.start_at < end_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Availability blocks may not overlap",
            )


@router.get("/availability-blocks", response_model=list[AvailabilityBlockRead])
async def list_availability_blocks(
    property_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AvailabilityBlockRead]:
    if current_user.id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current user is invalid")
    property_obj = await require_property_owner(db, decode_id_or_404(property_id), current_user.id)
    return [AvailabilityBlockRead.model_validate(block) for block in await get_property_blocks(db, property_obj.id)]


@router.post("/availability-blocks", response_model=AvailabilityBlockRead, status_code=status.HTTP_201_CREATED)
async def create_availability_block(
    property_id: str,
    data: AvailabilityBlockCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AvailabilityBlockRead:
    if current_user.id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current user is invalid")
    property_obj = await require_property_owner(db, decode_id_or_404(property_id), current_user.id)
    blocks = await get_property_blocks(db, property_obj.id)
    _validate_no_block_overlap(blocks, data.start_at, data.end_at)

    block = AvailabilityBlock(property_id=property_obj.id, **data.model_dump())
    db.add(block)
    await touch_property(property_obj)
    db.add(property_obj)
    await db.commit()
    await db.refresh(block)
    return AvailabilityBlockRead.model_validate(block)


@router.put("/availability-blocks/{block_id}", response_model=AvailabilityBlockRead)
async def update_availability_block(
    property_id: str,
    block_id: str,
    data: AvailabilityBlockUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AvailabilityBlockRead:
    if current_user.id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current user is invalid")
    property_obj = await require_property_owner(db, decode_id_or_404(property_id), current_user.id)
    block = (
        await db.execute(
            select(AvailabilityBlock).where(
                AvailabilityBlock.id == decode_id_or_404(block_id),
                AvailabilityBlock.property_id == property_obj.id,
            )
        )
    ).scalars().first()
    if block is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Availability block not found")

    update_fields = data.model_dump(exclude_unset=True)
    next_start_at = update_fields.get("start_at", block.start_at)
    next_end_at = update_fields.get("end_at", block.end_at)
    _validate_no_block_overlap(await get_property_blocks(db, property_obj.id), next_start_at, next_end_at, ignore_block_id=block.id)
    for field, value in update_fields.items():
        setattr(block, field, value)
    db.add(block)
    await touch_property(property_obj)
    db.add(property_obj)
    await db.commit()
    await db.refresh(block)
    return AvailabilityBlockRead.model_validate(block)


@router.delete("/availability-blocks/{block_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_availability_block(
    property_id: str,
    block_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    if current_user.id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current user is invalid")
    property_obj = await require_property_owner(db, decode_id_or_404(property_id), current_user.id)
    block = (
        await db.execute(
            select(AvailabilityBlock).where(
                AvailabilityBlock.id == decode_id_or_404(block_id),
                AvailabilityBlock.property_id == property_obj.id,
            )
        )
    ).scalars().first()
    if block is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Availability block not found")

    await db.delete(block)
    await touch_property(property_obj)
    db.add(property_obj)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
