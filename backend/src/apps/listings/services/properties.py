from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from src.apps.availability.models.availability_block import AvailabilityBlock
from src.apps.availability.services.availability import get_property_blocks
from src.apps.listings.models.property import Property, PropertyFeatureValue, PropertyPhoto, PropertyStatus
from src.apps.listings.models.property_type import PropertyType, PropertyTypeFeature
from src.apps.pricing.models.pricing_rule import PricingRule


async def get_property_type_or_404(db: AsyncSession, property_type_id: int) -> PropertyType:
    property_type = await db.get(PropertyType, property_type_id)
    if property_type is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property category not found")
    return property_type


async def get_property_type_feature_or_404(db: AsyncSession, attribute_id: int) -> PropertyTypeFeature:
    attribute = await db.get(PropertyTypeFeature, attribute_id)
    if attribute is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property attribute not found")
    return attribute


async def get_property_or_404(
    db: AsyncSession,
    property_id: int,
    *,
    published_only: bool = False,
) -> Property:
    property_obj = await db.get(Property, property_id)
    if property_obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    if published_only and (not property_obj.is_published or property_obj.status != PropertyStatus.PUBLISHED):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    return property_obj


async def require_property_owner(
    db: AsyncSession,
    property_id: int,
    owner_user_id: int,
) -> Property:
    property_obj = await get_property_or_404(db, property_id)
    if property_obj.owner_user_id != owner_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to manage this property")
    return property_obj


async def list_property_type_features(db: AsyncSession, property_type_id: int) -> list[PropertyTypeFeature]:
    result = await db.execute(
        select(PropertyTypeFeature)
        .where(PropertyTypeFeature.property_type_id == property_type_id)
        .order_by(col(PropertyTypeFeature.display_order), col(PropertyTypeFeature.id))
    )
    return list(result.scalars().all())


async def list_property_feature_values(db: AsyncSession, property_id: int) -> list[PropertyFeatureValue]:
    result = await db.execute(
        select(PropertyFeatureValue)
        .where(PropertyFeatureValue.property_id == property_id)
        .order_by(col(PropertyFeatureValue.id))
    )
    return list(result.scalars().all())


async def list_property_photos(db: AsyncSession, property_id: int) -> list[PropertyPhoto]:
    result = await db.execute(
        select(PropertyPhoto)
        .where(PropertyPhoto.property_id == property_id)
        .order_by(col(PropertyPhoto.is_cover).desc(), col(PropertyPhoto.position), col(PropertyPhoto.id))
    )
    return list(result.scalars().all())


async def list_property_pricing_rules(db: AsyncSession, property_id: int) -> list[PricingRule]:
    result = await db.execute(
        select(PricingRule)
        .where(PricingRule.property_id == property_id)
        .order_by(col(PricingRule.is_peak_rate), col(PricingRule.rate_type), col(PricingRule.created_at))
    )
    return list(result.scalars().all())


async def list_property_availability_blocks(db: AsyncSession, property_id: int) -> list[AvailabilityBlock]:
    return await get_property_blocks(db, property_id)


async def sync_property_feature_values(
    db: AsyncSession,
    property_obj: Property,
    feature_values: list[dict[str, Any]] | list[Any],
) -> None:
    if not feature_values:
        return

    attributes = await list_property_type_features(db, property_obj.property_type_id)
    attributes_by_id = {attribute.id: attribute for attribute in attributes}
    seen_attribute_ids: set[int] = set()

    existing_values = {
        feature_value.attribute_id: feature_value
        for feature_value in await list_property_feature_values(db, property_obj.id)
    }

    for item in feature_values:
        attribute_id = item["attribute_id"] if isinstance(item, dict) else item.attribute_id
        raw_value = item["value"] if isinstance(item, dict) else item.value
        if attribute_id in seen_attribute_ids:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Duplicate property attribute supplied")
        seen_attribute_ids.add(attribute_id)

        attribute = attributes_by_id.get(attribute_id)
        if attribute is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Property attribute does not belong to the selected category",
            )

        serialized_value = serialize_feature_value(raw_value)
        if attribute_id in existing_values:
            existing_values[attribute_id].value = serialized_value
            db.add(existing_values[attribute_id])
        else:
            db.add(
                PropertyFeatureValue(
                    property_id=property_obj.id,
                    attribute_id=attribute_id,
                    value=serialized_value,
                )
            )


def serialize_feature_value(value: Any) -> str:
    if isinstance(value, bool):
        return json.dumps(value)
    if isinstance(value, (int, float)):
        return json.dumps(value)
    if isinstance(value, list):
        return json.dumps(value)
    return str(value)


def deserialize_feature_value(value: str) -> Any:
    if value == "":
        return ""
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _blocks_overlap(
    left_start: datetime,
    left_end: datetime,
    right_start: datetime,
    right_end: datetime,
) -> bool:
    return left_start < right_end and right_start < left_end


async def sync_property_availability_blocks(
    db: AsyncSession,
    property_obj: Property,
    availability_blocks: list[dict[str, Any]] | list[Any],
) -> None:
    existing_blocks = await list_property_availability_blocks(db, property_obj.id)
    protected_blocks = [
        block
        for block in existing_blocks
        if block.booking_id is not None or block.maintenance_request_id is not None
    ]

    candidate_blocks: list[AvailabilityBlock] = []
    for item in availability_blocks:
        payload = item if isinstance(item, dict) else item.model_dump()
        block = AvailabilityBlock(property_id=property_obj.id, **payload)

        for existing in [*protected_blocks, *candidate_blocks]:
            if _blocks_overlap(block.start_at, block.end_at, existing.start_at, existing.end_at):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Availability blocks may not overlap",
                )

        candidate_blocks.append(block)

    await delete_property_availability_blocks(db, property_obj.id)
    for block in candidate_blocks:
        db.add(block)


async def ensure_property_publishable(db: AsyncSession, property_obj: Property) -> None:
    missing_parts: list[str] = []

    if not property_obj.description.strip():
        missing_parts.append("description")
    if not property_obj.location_address.strip():
        missing_parts.append("location_address")

    photos = await list_property_photos(db, property_obj.id)
    if not photos:
        missing_parts.append("photos")

    pricing_rules = await list_property_pricing_rules(db, property_obj.id)
    if not any(not rule.is_peak_rate for rule in pricing_rules):
        missing_parts.append("pricing_rules")

    attributes = await list_property_type_features(db, property_obj.property_type_id)
    required_attributes = {attribute.id: attribute.slug for attribute in attributes if attribute.is_required}
    feature_values = await list_property_feature_values(db, property_obj.id)
    present_attribute_ids = {feature_value.attribute_id for feature_value in feature_values}
    missing_required_attributes = [
        slug for attribute_id, slug in required_attributes.items() if attribute_id not in present_attribute_ids
    ]
    if missing_required_attributes:
        missing_parts.append(f"required_attributes:{','.join(missing_required_attributes)}")

    if missing_parts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Property is not ready to publish",
                "missing": missing_parts,
            },
        )


async def unset_cover_photo(db: AsyncSession, property_id: int) -> None:
    photos = await list_property_photos(db, property_id)
    for photo in photos:
        if photo.is_cover:
            photo.is_cover = False
            db.add(photo)


async def set_fallback_cover_photo(db: AsyncSession, property_id: int) -> None:
    photos = await list_property_photos(db, property_id)
    if photos and not any(photo.is_cover for photo in photos):
        photos[0].is_cover = True
        db.add(photos[0])


async def build_property_payload(db: AsyncSession, property_obj: Property) -> dict[str, Any]:
    property_type = await get_property_type_or_404(db, property_obj.property_type_id)
    attributes = await list_property_type_features(db, property_obj.property_type_id)
    attributes_by_id = {attribute.id: attribute for attribute in attributes}
    feature_values = await list_property_feature_values(db, property_obj.id)
    photos = await list_property_photos(db, property_obj.id)
    pricing_rules = await list_property_pricing_rules(db, property_obj.id)
    availability_blocks = await list_property_availability_blocks(db, property_obj.id)

    return {
        "id": property_obj.id,
        "owner_user_id": property_obj.owner_user_id,
        "property_type_id": property_obj.property_type_id,
        "property_type": property_type,
        "name": property_obj.name,
        "description": property_obj.description,
        "status": property_obj.status,
        "is_published": property_obj.is_published,
        "location_address": property_obj.location_address,
        "location_lat": property_obj.location_lat,
        "location_lng": property_obj.location_lng,
        "deposit_amount": property_obj.deposit_amount,
        "min_rental_duration_hours": property_obj.min_rental_duration_hours,
        "max_rental_duration_days": property_obj.max_rental_duration_days,
        "booking_lead_time_hours": property_obj.booking_lead_time_hours,
        "instant_booking_enabled": property_obj.instant_booking_enabled,
        "average_rating": property_obj.average_rating,
        "review_count": property_obj.review_count,
        "created_at": property_obj.created_at,
        "updated_at": property_obj.updated_at,
        "feature_values": [
            {
                "id": feature_value.id,
                "property_id": property_obj.id,
                "attribute_id": feature_value.attribute_id,
                "attribute_name": attributes_by_id[feature_value.attribute_id].name,
                "attribute_slug": attributes_by_id[feature_value.attribute_id].slug,
                "attribute_type": attributes_by_id[feature_value.attribute_id].attribute_type.value,
                "value": deserialize_feature_value(feature_value.value),
            }
            for feature_value in feature_values
            if feature_value.attribute_id in attributes_by_id
        ],
        "photos": photos,
        "pricing_rules": pricing_rules,
        "availability_blocks": availability_blocks,
    }


async def delete_property_feature_values(db: AsyncSession, property_id: int) -> None:
    await db.execute(delete(PropertyFeatureValue).where(PropertyFeatureValue.property_id == property_id))


async def delete_property_availability_blocks(db: AsyncSession, property_id: int) -> None:
    await db.execute(
        delete(AvailabilityBlock).where(
            AvailabilityBlock.property_id == property_id,
            AvailabilityBlock.booking_id.is_(None),
            AvailabilityBlock.maintenance_request_id.is_(None),
        )
    )


async def touch_property(property_obj: Property) -> None:
    property_obj.updated_at = datetime.now()
