from __future__ import annotations

import math
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from src.apps.availability.services.availability import get_conflicting_blocks, validate_booking_window
from src.apps.listings.models.property import Property, PropertyStatus
from src.apps.listings.models.property_type import PropertyType
from src.apps.listings.services.properties import list_property_photos
from src.apps.pricing.services.quote import get_property_base_daily_rate, quote_breakdown_to_payload, quote_property_period


def _parse_location_coordinates(location: str | None) -> tuple[float, float] | None:
    if not location:
        return None
    if "," not in location:
        return None
    left, right = [item.strip() for item in location.split(",", 1)]
    try:
        return float(left), float(right)
    except ValueError:
        return None


def _distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    earth_radius_km = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lng / 2) ** 2
    )
    return 2 * earth_radius_km * math.asin(math.sqrt(a))


async def search_assets(
    db: AsyncSession,
    *,
    category: str | None,
    start_at: datetime | None,
    end_at: datetime | None,
    location: str | None,
    radius_km: float | None,
    min_price: float | None,
    max_price: float | None,
    page: int,
    per_page: int,
) -> dict[str, object]:
    query = select(Property).where(
        Property.is_published == True,
        Property.status == PropertyStatus.PUBLISHED,
    )

    property_type_ids: set[int] | None = None
    if category:
        type_result = await db.execute(
            select(PropertyType).where(PropertyType.slug == category, PropertyType.is_active == True)
        )
        property_types = type_result.scalars().all()
        property_type_ids = {property_type.id for property_type in property_types}
        if not property_type_ids:
            return {"items": [], "total": 0, "page": page, "per_page": per_page, "has_more": False}
        query = query.where(Property.property_type_id.in_(property_type_ids))

    coordinates = _parse_location_coordinates(location)
    if location and coordinates is None:
        query = query.where(col(Property.location_address).ilike(f"%{location}%"))

    result = await db.execute(query.order_by(col(Property.created_at).desc()))
    properties = list(result.scalars().all())

    items: list[dict[str, object]] = []
    for property_obj in properties:
        if coordinates and radius_km is not None:
            if property_obj.location_lat is None or property_obj.location_lng is None:
                continue
            if _distance_km(coordinates[0], coordinates[1], property_obj.location_lat, property_obj.location_lng) > radius_km:
                continue

        property_type = await db.get(PropertyType, property_obj.property_type_id)
        if property_type is None:
            continue

        cover_photo = next((photo for photo in await list_property_photos(db, property_obj.id) if photo.is_cover), None)
        quote_preview = None
        starting_price = None
        currency = None

        if start_at and end_at:
            try:
                validate_booking_window(property_obj, start_at, end_at)
            except HTTPException:
                continue
            conflicts = await get_conflicting_blocks(db, property_obj.id, start_at, end_at)
            if conflicts:
                continue
            try:
                quote = await quote_property_period(
                    db,
                    property_obj,
                    start_at,
                    end_at,
                    skip_availability_check=True,
                )
            except HTTPException:
                continue
            payload = quote_breakdown_to_payload(quote)
            quote_preview = {
                "currency": payload["currency"],
                "base_fee": payload["base_fee"],
                "peak_surcharge": payload["peak_surcharge"],
                "total_fee": payload["total_fee"],
                "deposit_amount": payload["deposit_amount"],
                "total_due_now": payload["total_due_now"],
            }
            starting_price = payload["total_fee"]
            currency = payload["currency"]
        else:
            starting_price, currency = await get_property_base_daily_rate(db, property_obj.id)

        if min_price is not None and (starting_price is None or starting_price < min_price):
            continue
        if max_price is not None and (starting_price is None or starting_price > max_price):
            continue

        items.append(
            {
                "id": property_obj.id,
                "property_type_id": property_type.id,
                "property_type_name": property_type.name,
                "property_type_slug": property_type.slug,
                "name": property_obj.name,
                "description": property_obj.description,
                "status": property_obj.status.value,
                "is_published": property_obj.is_published,
                "location_address": property_obj.location_address,
                "instant_booking_enabled": property_obj.instant_booking_enabled,
                "cover_photo_url": cover_photo.url if cover_photo else None,
                "starting_price": starting_price,
                "currency": currency,
                "deposit_amount": property_obj.deposit_amount,
                "min_rental_duration_hours": property_obj.min_rental_duration_hours,
                "max_rental_duration_days": property_obj.max_rental_duration_days,
                "average_rating": property_obj.average_rating,
                "review_count": property_obj.review_count,
                "quote": quote_preview,
            }
        )

    total = len(items)
    start_index = (page - 1) * per_page
    paginated_items = items[start_index : start_index + per_page]
    return {
        "items": paginated_items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "has_more": start_index + len(paginated_items) < total,
    }
