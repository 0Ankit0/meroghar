from __future__ import annotations

from pydantic import BaseModel, field_serializer

from src.apps.iam.utils.hashid import encode_id


class AssetSearchQuotePreview(BaseModel):
    currency: str
    base_fee: float
    peak_surcharge: float
    total_fee: float
    deposit_amount: float
    total_due_now: float


class AssetSearchItem(BaseModel):
    id: int
    property_type_id: int
    property_type_name: str
    property_type_slug: str
    name: str
    description: str
    status: str
    is_published: bool
    location_address: str
    instant_booking_enabled: bool
    cover_photo_url: str | None = None
    starting_price: float | None = None
    currency: str | None = None
    deposit_amount: float | None = None
    min_rental_duration_hours: int | None = None
    max_rental_duration_days: int | None = None
    average_rating: float | None = None
    review_count: int | None = None
    quote: AssetSearchQuotePreview | None = None

    @field_serializer("id", "property_type_id")
    def serialize_ids(self, value: int) -> str:
        return encode_id(value)


class AssetSearchResponse(BaseModel):
    items: list[AssetSearchItem]
    total: int
    page: int
    per_page: int
    has_more: bool
