from __future__ import annotations

from enum import Enum

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class PropertyFeatureAttributeType(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    BOOLEAN = "boolean"
    SELECT = "select"
    MULTISELECT = "multiselect"


class PropertyType(SQLModel, table=True):
    __tablename__ = "property_types"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    parent_category_id: int | None = Field(default=None, foreign_key="property_types.id")
    name: str = Field(max_length=120, index=True)
    slug: str = Field(max_length=120, unique=True, index=True)
    description: str = Field(default="", max_length=1000)
    icon_url: str = Field(default="", max_length=500)
    is_active: bool = Field(default=True, index=True)
    display_order: int = Field(default=0, index=True)


class PropertyTypeFeature(SQLModel, table=True):
    __tablename__ = "property_type_features"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    property_type_id: int = Field(foreign_key="property_types.id", index=True)
    name: str = Field(max_length=120)
    slug: str = Field(max_length=120, index=True)
    attribute_type: PropertyFeatureAttributeType = Field(index=True)
    is_required: bool = Field(default=False)
    is_filterable: bool = Field(default=False)
    options_json: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    display_order: int = Field(default=0, index=True)
