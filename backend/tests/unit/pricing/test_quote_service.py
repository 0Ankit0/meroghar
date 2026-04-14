from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException

from src.apps.listings.models.property import Property
from src.apps.pricing.models.pricing_rule import PricingRateType, PricingRule
from src.apps.pricing.services.quote import build_quote_from_rules, quote_breakdown_to_payload


@pytest.mark.unit
class TestQuoteService:
    def test_quote_uses_cheapest_mix_and_peak_surcharge(self) -> None:
        start_at = datetime(2026, 5, 1)
        end_at = start_at + timedelta(days=45)
        property_obj = Property(id=1, owner_user_id=1, property_type_id=1, name="Unit", deposit_amount=500)
        rules = [
            PricingRule(property_id=1, rate_type=PricingRateType.DAILY, rate_amount=50, currency="NPR"),
            PricingRule(property_id=1, rate_type=PricingRateType.WEEKLY, rate_amount=280, currency="NPR"),
            PricingRule(property_id=1, rate_type=PricingRateType.MONTHLY, rate_amount=1000, currency="NPR"),
            PricingRule(
                property_id=1,
                rate_type=PricingRateType.DAILY,
                rate_amount=10,
                currency="NPR",
                is_peak_rate=True,
                peak_start_date=(start_at + timedelta(days=3)).date(),
                peak_end_date=(start_at + timedelta(days=4)).date(),
            ),
        ]

        quote = build_quote_from_rules(property_obj, rules, start_at, end_at)
        payload = quote_breakdown_to_payload(quote)

        assert quote.duration_days == 45
        assert payload["base_fee"] == 1610.0
        assert payload["peak_surcharge"] == 20.0
        assert payload["total_fee"] == 1630.0
        assert payload["total_due_now"] == 2130.0
        assert [item["rate_type"] for item in payload["applied_rates"]] == [
            PricingRateType.MONTHLY,
            PricingRateType.WEEKLY,
            PricingRateType.DAILY,
        ]

    def test_quote_requires_base_pricing_rules(self) -> None:
        property_obj = Property(id=1, owner_user_id=1, property_type_id=1, name="Unit", deposit_amount=0)
        with pytest.raises(HTTPException) as exc_info:
            build_quote_from_rules(property_obj, [], datetime(2026, 5, 1), datetime(2026, 5, 3))
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Property has no pricing rules configured"
