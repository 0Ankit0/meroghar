from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, field_serializer, field_validator

from src.apps.availability.schemas.availability import AvailabilityBlockCreate, AvailabilityBlockRead
from src.apps.iam.utils.hashid import decode_id, encode_id
from src.apps.listings.models.property import PropertyStatus
from src.apps.listings.schemas.property_type import PropertyTypeRead
from src.apps.pricing.schemas.pricing import PricingRuleRead


class PropertyFeatureValueInput(BaseModel):
    attribute_id: int
    value: Any

    @field_validator("attribute_id", mode="before")
    @classmethod
    def decode_attribute_id(cls, value: int | str) -> int:
        if isinstance(value, str):
            decoded = decode_id(value)
            if decoded is None:
                raise ValueError("Invalid attribute_id")
            return decoded
        return value


class PropertyFeatureValueRead(BaseModel):
    id: int
    property_id: int
    attribute_id: int
    attribute_name: str
    attribute_slug: str
    attribute_type: str
    value: Any

    @field_serializer("id", "property_id", "attribute_id")
    def serialize_ids(self, value: int) -> str:
        return encode_id(value)


class PropertyPhotoRead(BaseModel):
    id: int
    property_id: int
    url: str
    thumbnail_url: str | None = None
    position: int
    is_cover: bool
    caption: str

    model_config = {"from_attributes": True}

    @field_serializer("id", "property_id")
    def serialize_ids(self, value: int) -> str:
        return encode_id(value)


class PropertyCreate(BaseModel):
    property_type_id: int
    name: str
    description: str = ""
    location_address: str = ""
    location_lat: float | None = None
    location_lng: float | None = None
    deposit_amount: float = 0.0
    min_rental_duration_hours: int = 24
    max_rental_duration_days: int = 365
    booking_lead_time_hours: int = 24
    instant_booking_enabled: bool = False
    feature_values: list[PropertyFeatureValueInput] = []
    availability_blocks: list[AvailabilityBlockCreate] = []

    @field_validator("property_type_id", mode="before")
    @classmethod
    def decode_property_type_id(cls, value: int | str) -> int:
        if isinstance(value, str):
            decoded = decode_id(value)
            if decoded is None:
                raise ValueError("Invalid property_type_id")
            return decoded
        return value

    @field_validator("deposit_amount")
    @classmethod
    def validate_deposit_amount(cls, value: float) -> float:
        if value < 0:
            raise ValueError("deposit_amount cannot be negative")
        return value


class PropertyUpdate(BaseModel):
    property_type_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    location_address: Optional[str] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    deposit_amount: Optional[float] = None
    min_rental_duration_hours: Optional[int] = None
    max_rental_duration_days: Optional[int] = None
    booking_lead_time_hours: Optional[int] = None
    instant_booking_enabled: Optional[bool] = None
    feature_values: Optional[list[PropertyFeatureValueInput]] = None
    availability_blocks: Optional[list[AvailabilityBlockCreate]] = None

    @field_validator("property_type_id", mode="before")
    @classmethod
    def decode_property_type_id(cls, value: int | str | None) -> int | None:
        if isinstance(value, str):
            decoded = decode_id(value)
            if decoded is None:
                raise ValueError("Invalid property_type_id")
            return decoded
        return value

    @field_validator("deposit_amount")
    @classmethod
    def validate_deposit_amount(cls, value: float | None) -> float | None:
        if value is not None and value < 0:
            raise ValueError("deposit_amount cannot be negative")
        return value


class PropertyBaseRead(BaseModel):
    id: int
    property_type_id: int
    property_type: PropertyTypeRead
    name: str
    description: str
    status: PropertyStatus
    is_published: bool
    location_address: str
    location_lat: float | None
    location_lng: float | None
    deposit_amount: float
    min_rental_duration_hours: int
    max_rental_duration_days: int
    booking_lead_time_hours: int
    instant_booking_enabled: bool
    average_rating: float
    review_count: int
    created_at: datetime
    updated_at: datetime
    feature_values: list[PropertyFeatureValueRead] = []
    photos: list[PropertyPhotoRead] = []
    availability_blocks: list[AvailabilityBlockRead] = []

    @field_serializer("id", "property_type_id")
    def serialize_ids(self, value: int) -> str:
        return encode_id(value)


class PropertyManageRead(PropertyBaseRead):
    owner_user_id: int
    pricing_rules: list[PricingRuleRead] = []

    @field_serializer("owner_user_id")
    def serialize_owner_user_id(self, value: int) -> str:
        return encode_id(value)


class PropertyDetailRead(PropertyBaseRead):
    pricing_rules: list[PricingRuleRead] = []


class PropertyListRead(BaseModel):
    items: list[PropertyManageRead]
    total: int
    page: int
    per_page: int
    has_more: bool
