from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, field_serializer, field_validator, model_validator

from src.apps.iam.utils.hashid import encode_id
from src.apps.pricing.models.pricing_rule import PricingRateType


class PricingRuleBase(BaseModel):
    rate_type: PricingRateType
    rate_amount: float
    currency: str = "NPR"
    is_peak_rate: bool = False
    peak_start_date: date | None = None
    peak_end_date: date | None = None
    peak_days_of_week_json: list[int] = []
    discount_percentage: float = 0.0
    min_units_for_discount: int = 0

    @field_validator("rate_amount")
    @classmethod
    def validate_rate_amount(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("rate_amount must be positive")
        return value

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        normalized = value.strip().upper()
        if len(normalized) != 3:
            raise ValueError("currency must be a 3-letter ISO code")
        return normalized

    @field_validator("discount_percentage")
    @classmethod
    def validate_discount_percentage(cls, value: float) -> float:
        if value < 0 or value > 100:
            raise ValueError("discount_percentage must be between 0 and 100")
        return value

    @field_validator("peak_days_of_week_json")
    @classmethod
    def validate_peak_days(cls, value: list[int]) -> list[int]:
        for day in value:
            if day < 0 or day > 6:
                raise ValueError("peak_days_of_week_json entries must be between 0 and 6")
        return sorted(set(value))

    @model_validator(mode="after")
    def validate_peak_window(self) -> "PricingRuleBase":
        if self.is_peak_rate:
            if self.peak_start_date is None or self.peak_end_date is None:
                raise ValueError("Peak pricing rules require peak_start_date and peak_end_date")
            if self.peak_end_date < self.peak_start_date:
                raise ValueError("peak_end_date must be on or after peak_start_date")
        return self


class PricingRuleCreate(PricingRuleBase):
    pass


class PricingRuleUpdate(BaseModel):
    rate_type: Optional[PricingRateType] = None
    rate_amount: Optional[float] = None
    currency: Optional[str] = None
    is_peak_rate: Optional[bool] = None
    peak_start_date: Optional[date] = None
    peak_end_date: Optional[date] = None
    peak_days_of_week_json: Optional[list[int]] = None
    discount_percentage: Optional[float] = None
    min_units_for_discount: Optional[int] = None

    @field_validator("rate_amount")
    @classmethod
    def validate_rate_amount(cls, value: float | None) -> float | None:
        if value is not None and value <= 0:
            raise ValueError("rate_amount must be positive")
        return value

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip().upper()
        if len(normalized) != 3:
            raise ValueError("currency must be a 3-letter ISO code")
        return normalized

    @field_validator("discount_percentage")
    @classmethod
    def validate_discount_percentage(cls, value: float | None) -> float | None:
        if value is not None and (value < 0 or value > 100):
            raise ValueError("discount_percentage must be between 0 and 100")
        return value

    @field_validator("peak_days_of_week_json")
    @classmethod
    def validate_peak_days(cls, value: list[int] | None) -> list[int] | None:
        if value is None:
            return value
        for day in value:
            if day < 0 or day > 6:
                raise ValueError("peak_days_of_week_json entries must be between 0 and 6")
        return sorted(set(value))


class PricingRuleRead(PricingRuleBase):
    id: int
    property_id: int
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("id", "property_id")
    def serialize_ids(self, value: int) -> str:
        return encode_id(value)


class AppliedRateRead(BaseModel):
    rate_type: PricingRateType
    units: int
    unit_amount: float
    subtotal: float
    discount_percentage: float
    discounted_subtotal: float


class PriceQuoteRead(BaseModel):
    property_id: int
    currency: str
    start_at: datetime
    end_at: datetime
    duration_days: int
    base_fee: float
    peak_surcharge: float
    tax_amount: float
    deposit_amount: float
    total_fee: float
    total_due_now: float
    applied_rates: list[AppliedRateRead]

    @field_serializer("property_id")
    def serialize_property_id(self, value: int) -> str:
        return encode_id(value)
