from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlmodel import Field, SQLModel


class PropertyStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Property(SQLModel, table=True):
    __tablename__ = "properties"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    owner_user_id: int = Field(foreign_key="user.id", index=True)
    property_type_id: int = Field(foreign_key="property_types.id", index=True)
    name: str = Field(max_length=200, index=True)
    description: str = Field(default="", max_length=5000)
    status: PropertyStatus = Field(default=PropertyStatus.DRAFT, index=True)
    is_published: bool = Field(default=False, index=True)
    location_address: str = Field(default="", max_length=500, index=True)
    location_lat: float | None = Field(default=None)
    location_lng: float | None = Field(default=None)
    deposit_amount: float = Field(default=0.0)
    min_rental_duration_hours: int = Field(default=24)
    max_rental_duration_days: int = Field(default=365)
    booking_lead_time_hours: int = Field(default=24)
    instant_booking_enabled: bool = Field(default=False)
    average_rating: float = Field(default=0.0)
    review_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.now, index=True)
    updated_at: datetime = Field(default_factory=datetime.now)


class PropertyFeatureValue(SQLModel, table=True):
    __tablename__ = "property_feature_values"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    property_id: int = Field(foreign_key="properties.id", index=True)
    attribute_id: int = Field(foreign_key="property_type_features.id", index=True)
    value: str = Field(default="", max_length=2000)


class PropertyPhoto(SQLModel, table=True):
    __tablename__ = "property_photos"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    property_id: int = Field(foreign_key="properties.id", index=True)
    url: str = Field(max_length=500)
    thumbnail_url: str | None = Field(default=None, max_length=500)
    position: int = Field(default=0, index=True)
    is_cover: bool = Field(default=False, index=True)
    caption: str = Field(default="", max_length=255)
