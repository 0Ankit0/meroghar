from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_serializer, model_validator

from src.apps.iam.utils.hashid import encode_id
from src.apps.availability.models.availability_block import AvailabilityBlockType


class AvailabilityBlockBase(BaseModel):
    block_type: AvailabilityBlockType = AvailabilityBlockType.MANUAL
    start_at: datetime
    end_at: datetime
    reason: str = ""

    @model_validator(mode="after")
    def validate_window(self) -> "AvailabilityBlockBase":
        if self.end_at <= self.start_at:
            raise ValueError("end_at must be after start_at")
        return self


class AvailabilityBlockCreate(AvailabilityBlockBase):
    pass


class AvailabilityBlockUpdate(BaseModel):
    block_type: Optional[AvailabilityBlockType] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    reason: Optional[str] = None

    @model_validator(mode="after")
    def validate_window(self) -> "AvailabilityBlockUpdate":
        if self.start_at is not None and self.end_at is not None and self.end_at <= self.start_at:
            raise ValueError("end_at must be after start_at")
        return self


class AvailabilityBlockRead(AvailabilityBlockBase):
    id: int
    property_id: int
    booking_id: int | None = None
    maintenance_request_id: int | None = None

    model_config = {"from_attributes": True}

    @field_serializer("id", "property_id")
    def serialize_ids(self, value: int) -> str:
        return encode_id(value)


class AvailabilityQueryRead(BaseModel):
    property_id: int
    start_at: datetime
    end_at: datetime
    is_available: bool
    next_available_start: datetime | None = None
    conflicts: list[AvailabilityBlockRead] = []

    @field_serializer("property_id")
    def serialize_property_id(self, value: int) -> str:
        return encode_id(value)
