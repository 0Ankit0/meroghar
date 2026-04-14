from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class PricingRateType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class PricingRule(SQLModel, table=True):
    __tablename__ = "pricing_rules"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    property_id: int = Field(foreign_key="properties.id", index=True)
    rate_type: PricingRateType = Field(index=True)
    rate_amount: float = Field(default=0.0)
    currency: str = Field(default="NPR", max_length=3)
    is_peak_rate: bool = Field(default=False, index=True)
    peak_start_date: date | None = Field(default=None)
    peak_end_date: date | None = Field(default=None)
    peak_days_of_week_json: list[int] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    discount_percentage: float = Field(default=0.0)
    min_units_for_discount: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.now, index=True)
