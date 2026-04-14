from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from src.apps.availability.services.availability import (
    calculate_duration_days,
    ensure_property_available,
    validate_booking_window,
)
from src.apps.listings.models.property import Property
from src.apps.pricing.models.pricing_rule import PricingRateType, PricingRule

_DECIMAL_CENTS = Decimal("0.01")
_RATE_DAYS: dict[PricingRateType, int] = {
    PricingRateType.DAILY: 1,
    PricingRateType.WEEKLY: 7,
    PricingRateType.MONTHLY: 30,
}


@dataclass(slots=True)
class AppliedRate:
    rate_type: PricingRateType
    units: int
    unit_amount: Decimal
    subtotal: Decimal
    discount_percentage: Decimal
    discounted_subtotal: Decimal


@dataclass(slots=True)
class QuoteBreakdown:
    property_id: int
    currency: str
    start_at: datetime
    end_at: datetime
    duration_days: int
    base_fee: Decimal
    peak_surcharge: Decimal
    tax_amount: Decimal
    deposit_amount: Decimal
    total_fee: Decimal
    total_due_now: Decimal
    applied_rates: list[AppliedRate]


async def get_property_pricing_rules(db: AsyncSession, property_id: int) -> list[PricingRule]:
    result = await db.execute(
        select(PricingRule)
        .where(PricingRule.property_id == property_id)
        .order_by(col(PricingRule.is_peak_rate), col(PricingRule.rate_type), col(PricingRule.created_at))
    )
    return list(result.scalars().all())


async def get_property_base_daily_rate(db: AsyncSession, property_id: int) -> tuple[float | None, str | None]:
    rules = await get_property_pricing_rules(db, property_id)
    for rule in rules:
        if not rule.is_peak_rate and rule.rate_type == PricingRateType.DAILY:
            return rule.rate_amount, rule.currency
    non_peak_rules = [rule for rule in rules if not rule.is_peak_rate]
    if not non_peak_rules:
        return None, None
    cheapest = min(non_peak_rules, key=lambda item: item.rate_amount / _RATE_DAYS[item.rate_type])
    per_day = Decimal(str(cheapest.rate_amount)) / Decimal(_RATE_DAYS[cheapest.rate_type])
    return float(_quantize(per_day)), cheapest.currency


async def quote_property_period(
    db: AsyncSession,
    property_obj: Property,
    start_at: datetime,
    end_at: datetime,
    *,
    skip_availability_check: bool = False,
) -> QuoteBreakdown:
    duration_days = validate_booking_window(property_obj, start_at, end_at)
    if not skip_availability_check:
        await ensure_property_available(db, property_obj, start_at, end_at)
    pricing_rules = await get_property_pricing_rules(db, property_obj.id)
    return build_quote_from_rules(property_obj, pricing_rules, start_at, end_at, duration_days)


def build_quote_from_rules(
    property_obj: Property,
    pricing_rules: list[PricingRule],
    start_at: datetime,
    end_at: datetime,
    duration_days: int | None = None,
) -> QuoteBreakdown:
    computed_duration_days = duration_days or calculate_duration_days(start_at, end_at)
    base_rules = {rule.rate_type: rule for rule in pricing_rules if not rule.is_peak_rate}
    peak_rules = [rule for rule in pricing_rules if rule.is_peak_rate]

    if not base_rules:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Property has no pricing rules configured",
        )

    candidates: list[tuple[Decimal, list[AppliedRate], str]] = []
    max_months = computed_duration_days // _RATE_DAYS[PricingRateType.MONTHLY] if PricingRateType.MONTHLY in base_rules else 0

    for month_units in range(max_months + 1):
        remaining_after_months = computed_duration_days - month_units * _RATE_DAYS[PricingRateType.MONTHLY]
        max_weeks = remaining_after_months // _RATE_DAYS[PricingRateType.WEEKLY] if PricingRateType.WEEKLY in base_rules else 0
        for week_units in range(max_weeks + 1):
            remaining_days = remaining_after_months - week_units * _RATE_DAYS[PricingRateType.WEEKLY]
            if remaining_days < 0:
                continue
            if remaining_days > 0 and PricingRateType.DAILY not in base_rules:
                continue

            total = Decimal("0")
            applied_rates: list[AppliedRate] = []
            currency = None
            for rate_type, units in (
                (PricingRateType.MONTHLY, month_units),
                (PricingRateType.WEEKLY, week_units),
                (PricingRateType.DAILY, remaining_days),
            ):
                if units <= 0:
                    continue
                rule = base_rules[rate_type]
                currency = currency or rule.currency
                applied_rate = _applied_rate(rule, units)
                total += applied_rate.discounted_subtotal
                applied_rates.append(applied_rate)
            if currency:
                candidates.append((total, applied_rates, currency))

    if not candidates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pricing rules do not support the requested duration",
        )

    base_fee, applied_rates, currency = min(candidates, key=lambda candidate: candidate[0])
    peak_surcharge = _calculate_peak_surcharge(start_at, end_at, peak_rules)
    tax_amount = Decimal("0.00")
    deposit_amount = Decimal(str(property_obj.deposit_amount))
    total_fee = _quantize(base_fee + peak_surcharge + tax_amount)
    total_due_now = _quantize(total_fee + deposit_amount)

    return QuoteBreakdown(
        property_id=property_obj.id,
        currency=currency,
        start_at=start_at,
        end_at=end_at,
        duration_days=computed_duration_days,
        base_fee=_quantize(base_fee),
        peak_surcharge=_quantize(peak_surcharge),
        tax_amount=tax_amount,
        deposit_amount=_quantize(deposit_amount),
        total_fee=total_fee,
        total_due_now=total_due_now,
        applied_rates=applied_rates,
    )


def quote_breakdown_to_payload(quote: QuoteBreakdown) -> dict[str, object]:
    return {
        "property_id": quote.property_id,
        "currency": quote.currency,
        "start_at": quote.start_at,
        "end_at": quote.end_at,
        "duration_days": quote.duration_days,
        "base_fee": float(quote.base_fee),
        "peak_surcharge": float(quote.peak_surcharge),
        "tax_amount": float(quote.tax_amount),
        "deposit_amount": float(quote.deposit_amount),
        "total_fee": float(quote.total_fee),
        "total_due_now": float(quote.total_due_now),
        "applied_rates": [
            {
                "rate_type": applied.rate_type,
                "units": applied.units,
                "unit_amount": float(applied.unit_amount),
                "subtotal": float(applied.subtotal),
                "discount_percentage": float(applied.discount_percentage),
                "discounted_subtotal": float(applied.discounted_subtotal),
            }
            for applied in quote.applied_rates
        ],
    }


def _applied_rate(rule: PricingRule, units: int) -> AppliedRate:
    unit_amount = Decimal(str(rule.rate_amount))
    subtotal = unit_amount * Decimal(units)
    discount_percentage = Decimal(str(rule.discount_percentage or 0))
    if rule.min_units_for_discount and units >= rule.min_units_for_discount and discount_percentage > 0:
        discounted_subtotal = subtotal * (Decimal("1") - (discount_percentage / Decimal("100")))
    else:
        discounted_subtotal = subtotal
    return AppliedRate(
        rate_type=rule.rate_type,
        units=units,
        unit_amount=_quantize(unit_amount),
        subtotal=_quantize(subtotal),
        discount_percentage=_quantize(discount_percentage),
        discounted_subtotal=_quantize(discounted_subtotal),
    )


def _calculate_peak_surcharge(start_at: datetime, end_at: datetime, peak_rules: list[PricingRule]) -> Decimal:
    surcharge = Decimal("0.00")
    for rule in peak_rules:
        matched_days = _count_peak_days(start_at.date(), end_at.date(), rule)
        if matched_days <= 0:
            continue
        units = (matched_days + _RATE_DAYS[rule.rate_type] - 1) // _RATE_DAYS[rule.rate_type]
        surcharge += _applied_rate(rule, units).discounted_subtotal
    return _quantize(surcharge)


def _count_peak_days(start_date: date, end_date: date, rule: PricingRule) -> int:
    if rule.peak_start_date is None or rule.peak_end_date is None:
        return 0

    count = 0
    cursor = start_date
    while cursor < end_date:
        if rule.peak_start_date <= cursor <= rule.peak_end_date:
            if not rule.peak_days_of_week_json or cursor.weekday() in rule.peak_days_of_week_json:
                count += 1
        cursor += timedelta(days=1)
    return count


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_DECIMAL_CENTS, rounding=ROUND_HALF_UP)
