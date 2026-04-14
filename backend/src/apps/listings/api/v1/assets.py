from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.iam.api.deps import get_current_user, get_db
from src.apps.iam.models.user import User
from src.apps.listings.models.property import Property, PropertyStatus
from src.apps.listings.schemas.property import PropertyCreate, PropertyManageRead
from src.apps.listings.services.properties import (
    build_property_payload,
    get_property_type_or_404,
    sync_property_availability_blocks,
    sync_property_feature_values,
)

router = APIRouter(prefix="/assets")


@router.post("/", response_model=PropertyManageRead, status_code=status.HTTP_201_CREATED)
async def create_asset(
    data: PropertyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PropertyManageRead:
    if current_user.id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current user is invalid")

    await get_property_type_or_404(db, data.property_type_id)
    property_obj = Property(
        owner_user_id=current_user.id,
        property_type_id=data.property_type_id,
        name=data.name,
        description=data.description,
        status=PropertyStatus.DRAFT,
        is_published=False,
        location_address=data.location_address,
        location_lat=data.location_lat,
        location_lng=data.location_lng,
        deposit_amount=data.deposit_amount,
        min_rental_duration_hours=data.min_rental_duration_hours,
        max_rental_duration_days=data.max_rental_duration_days,
        booking_lead_time_hours=data.booking_lead_time_hours,
        instant_booking_enabled=data.instant_booking_enabled,
    )
    db.add(property_obj)
    await db.flush()
    await sync_property_feature_values(db, property_obj, data.feature_values)
    await sync_property_availability_blocks(db, property_obj, data.availability_blocks)
    await db.commit()
    await db.refresh(property_obj)
    return PropertyManageRead.model_validate(await build_property_payload(db, property_obj))
