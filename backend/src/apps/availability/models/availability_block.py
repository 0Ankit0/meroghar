from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlmodel import Field, SQLModel


class AvailabilityBlockType(str, Enum):
    MANUAL = "manual"
    BOOKING = "booking"
    MAINTENANCE = "maintenance"


class AvailabilityBlock(SQLModel, table=True):
    __tablename__ = "availability_blocks"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    property_id: int = Field(foreign_key="properties.id", index=True)
    block_type: AvailabilityBlockType = Field(default=AvailabilityBlockType.MANUAL, index=True)
    start_at: datetime = Field(index=True)
    end_at: datetime = Field(index=True)
    reason: str = Field(default="", max_length=500)
    booking_id: int | None = Field(default=None, foreign_key="bookings.id", index=True)
    maintenance_request_id: int | None = Field(default=None)
