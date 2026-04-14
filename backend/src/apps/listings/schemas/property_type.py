from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel, field_serializer, field_validator, model_validator

from src.apps.iam.utils.hashid import decode_id, encode_id
from src.apps.listings.models.property_type import PropertyFeatureAttributeType

_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _validate_slug(value: str) -> str:
    if not _SLUG_PATTERN.match(value):
        raise ValueError("Slug must be lowercase alphanumeric with hyphens only")
    return value


class PropertyTypeFeatureBase(BaseModel):
    name: str
    slug: str
    attribute_type: PropertyFeatureAttributeType
    is_required: bool = False
    is_filterable: bool = False
    options_json: list[str] = []
    display_order: int = 0

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str) -> str:
        return _validate_slug(value)

    @model_validator(mode="after")
    def validate_options(self) -> "PropertyTypeFeatureBase":
        if self.attribute_type in {
            PropertyFeatureAttributeType.SELECT,
            PropertyFeatureAttributeType.MULTISELECT,
        } and not self.options_json:
            raise ValueError("Selectable attributes must define options_json")
        return self


class PropertyTypeFeatureCreate(PropertyTypeFeatureBase):
    pass


class PropertyTypeFeatureRead(PropertyTypeFeatureBase):
    id: int
    property_type_id: int

    model_config = {"from_attributes": True}

    @field_serializer("id", "property_type_id")
    def serialize_ids(self, value: int) -> str:
        return encode_id(value)


class PropertyTypeBase(BaseModel):
    name: str
    slug: str
    description: str = ""
    icon_url: str = ""
    is_active: bool = True
    display_order: int = 0
    parent_category_id: int | None = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str) -> str:
        return _validate_slug(value)

    @field_validator("parent_category_id", mode="before")
    @classmethod
    def decode_parent_category_id(cls, value: int | str | None) -> int | None:
        if isinstance(value, str):
            decoded = decode_id(value)
            if decoded is None:
                raise ValueError("Invalid parent_category_id")
            return decoded
        return value


class PropertyTypeCreate(PropertyTypeBase):
    pass


class PropertyTypeUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    icon_url: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None
    parent_category_id: int | None = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return _validate_slug(value)

    @field_validator("parent_category_id", mode="before")
    @classmethod
    def decode_parent_category_id(cls, value: int | str | None) -> int | None:
        if isinstance(value, str):
            decoded = decode_id(value)
            if decoded is None:
                raise ValueError("Invalid parent_category_id")
            return decoded
        return value


class PropertyTypeRead(BaseModel):
    id: int
    name: str
    slug: str
    description: str
    icon_url: str
    is_active: bool
    display_order: int
    parent_category_id: int | None

    model_config = {"from_attributes": True}

    @field_serializer("id")
    def serialize_id(self, value: int) -> str:
        return encode_id(value)

    @field_serializer("parent_category_id")
    def serialize_parent_category_id(self, value: int | None) -> str | None:
        return encode_id(value) if value is not None else None


class PropertyTypeDetailRead(PropertyTypeRead):
    attributes: list[PropertyTypeFeatureRead] = []
