from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.apps.iam.api.deps import get_current_user, get_db
from src.apps.iam.models.user import User
from src.apps.iam.utils.hashid import decode_id_or_404
from src.apps.listings.services.properties import get_property_or_404, require_property_owner, touch_property
from src.apps.pricing.models.pricing_rule import PricingRule
from src.apps.pricing.schemas.pricing import PriceQuoteRead, PricingRuleCreate, PricingRuleRead, PricingRuleUpdate
from src.apps.pricing.services.quote import get_property_pricing_rules, quote_breakdown_to_payload, quote_property_period

router = APIRouter(prefix="/properties/{property_id}")


def _windows_overlap(
    left_start: date | None,
    left_end: date | None,
    right_start: date | None,
    right_end: date | None,
) -> bool:
    if left_start is None or left_end is None or right_start is None or right_end is None:
        return False
    return left_start <= right_end and right_start <= left_end


async def _validate_pricing_rule(
    db: AsyncSession,
    property_id: int,
    payload: PricingRuleCreate | PricingRuleUpdate,
    *,
    existing_rule: PricingRule | None = None,
) -> None:
    rate_type = payload.rate_type if payload.rate_type is not None else existing_rule.rate_type
    is_peak_rate = payload.is_peak_rate if payload.is_peak_rate is not None else existing_rule.is_peak_rate
    peak_start_date = (
        payload.peak_start_date
        if payload.peak_start_date is not None
        else (existing_rule.peak_start_date if existing_rule is not None else None)
    )
    peak_end_date = (
        payload.peak_end_date
        if payload.peak_end_date is not None
        else (existing_rule.peak_end_date if existing_rule is not None else None)
    )

    if is_peak_rate:
        if peak_start_date is None or peak_end_date is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Peak pricing rules require peak_start_date and peak_end_date",
            )
        if peak_end_date < peak_start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="peak_end_date must be on or after peak_start_date",
            )

    rules = await get_property_pricing_rules(db, property_id)
    for rule in rules:
        if existing_rule is not None and rule.id == existing_rule.id:
            continue
        if rule.rate_type != rate_type or rule.is_peak_rate != is_peak_rate:
            continue
        if not is_peak_rate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A base pricing rule already exists for this rate_type",
            )
        if _windows_overlap(rule.peak_start_date, rule.peak_end_date, peak_start_date, peak_end_date):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Overlapping peak pricing rules are not allowed for the same rate_type",
            )


@router.get("/pricing-rules", response_model=list[PricingRuleRead])
async def list_pricing_rules(
    property_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PricingRuleRead]:
    if current_user.id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current user is invalid")
    property_obj = await require_property_owner(db, decode_id_or_404(property_id), current_user.id)
    return [PricingRuleRead.model_validate(rule) for rule in await get_property_pricing_rules(db, property_obj.id)]


@router.post("/pricing-rules", response_model=PricingRuleRead, status_code=status.HTTP_201_CREATED)
async def create_pricing_rule(
    property_id: str,
    data: PricingRuleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PricingRuleRead:
    if current_user.id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current user is invalid")
    property_obj = await require_property_owner(db, decode_id_or_404(property_id), current_user.id)
    await _validate_pricing_rule(db, property_obj.id, data)

    payload = data.model_dump()
    if not payload["is_peak_rate"]:
        payload["peak_start_date"] = None
        payload["peak_end_date"] = None
        payload["peak_days_of_week_json"] = []
    rule = PricingRule(property_id=property_obj.id, **payload)
    db.add(rule)
    await touch_property(property_obj)
    db.add(property_obj)
    await db.commit()
    await db.refresh(rule)
    return PricingRuleRead.model_validate(rule)


@router.put("/pricing-rules/{rule_id}", response_model=PricingRuleRead)
async def update_pricing_rule(
    property_id: str,
    rule_id: str,
    data: PricingRuleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PricingRuleRead:
    if current_user.id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current user is invalid")
    property_obj = await require_property_owner(db, decode_id_or_404(property_id), current_user.id)
    rule = (
        await db.execute(
            select(PricingRule).where(
                PricingRule.id == decode_id_or_404(rule_id),
                PricingRule.property_id == property_obj.id,
            )
        )
    ).scalars().first()
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pricing rule not found")

    await _validate_pricing_rule(db, property_obj.id, data, existing_rule=rule)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    if not rule.is_peak_rate:
        rule.peak_start_date = None
        rule.peak_end_date = None
        rule.peak_days_of_week_json = []
    db.add(rule)
    await touch_property(property_obj)
    db.add(property_obj)
    await db.commit()
    await db.refresh(rule)
    return PricingRuleRead.model_validate(rule)


@router.delete("/pricing-rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pricing_rule(
    property_id: str,
    rule_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    if current_user.id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current user is invalid")
    property_obj = await require_property_owner(db, decode_id_or_404(property_id), current_user.id)
    rule = (
        await db.execute(
            select(PricingRule).where(
                PricingRule.id == decode_id_or_404(rule_id),
                PricingRule.property_id == property_obj.id,
            )
        )
    ).scalars().first()
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pricing rule not found")

    await db.delete(rule)
    await touch_property(property_obj)
    db.add(property_obj)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/price", response_model=PriceQuoteRead)
async def get_price_quote(
    property_id: str,
    start: datetime = Query(..., alias="start"),
    end: datetime = Query(..., alias="end"),
    db: AsyncSession = Depends(get_db),
) -> PriceQuoteRead:
    property_obj = await get_property_or_404(db, decode_id_or_404(property_id), published_only=True)
    quote = await quote_property_period(db, property_obj, start, end)
    return PriceQuoteRead.model_validate(quote_breakdown_to_payload(quote))
