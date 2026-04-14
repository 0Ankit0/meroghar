from __future__ import annotations

import shutil
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.apps.core import security
from src.apps.core.config import settings
from src.apps.core.storage import extract_relative_media_path
from src.apps.iam.models.user import User
from src.apps.listings.models.property import Property, PropertyStatus


async def _make_user(db: AsyncSession, **kwargs) -> User:
    user = User(
        username=kwargs.get("username", "user"),
        email=kwargs.get("email", "user@example.com"),
        hashed_password=security.get_password_hash(kwargs.get("password", "TestPass123")),
        is_active=kwargs.get("is_active", True),
        is_superuser=kwargs.get("is_superuser", False),
        is_confirmed=kwargs.get("is_confirmed", True),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _login(client: AsyncClient, username: str, password: str = "TestPass123") -> str:
    response = await client.post(
        "/api/v1/auth/login/?set_cookie=false",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access"]


@pytest.fixture(autouse=True)
def cleanup_property_photos() -> None:
    yield
    photos_dir = Path(settings.MEDIA_DIR) / "property-photos"
    if photos_dir.exists():
        shutil.rmtree(photos_dir)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_listings_search_pricing_and_availability_slice(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    admin = await _make_user(
        db_session,
        username="sliceadmin",
        email="sliceadmin@example.com",
        is_superuser=True,
    )
    landlord = await _make_user(
        db_session,
        username="landlordslice",
        email="landlordslice@example.com",
    )
    admin_token = await _login(client, admin.username)
    landlord_token = await _login(client, landlord.username)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    landlord_headers = {"Authorization": f"Bearer {landlord_token}"}

    category_response = await client.post(
        "/api/v1/categories/",
        headers=admin_headers,
        json={
            "name": "Apartment",
            "slug": "apartment",
            "description": "Urban rentals",
            "icon_url": "building",
            "display_order": 1,
        },
    )
    assert category_response.status_code == 201, category_response.text
    category_id = category_response.json()["id"]

    category_update_response = await client.put(
        f"/api/v1/categories/{category_id}",
        headers=admin_headers,
        json={"description": "City apartments"},
    )
    assert category_update_response.status_code == 200, category_update_response.text
    assert category_update_response.json()["description"] == "City apartments"

    bedrooms_response = await client.post(
        f"/api/v1/categories/{category_id}/attributes",
        headers=admin_headers,
        json={
            "name": "Bedrooms",
            "slug": "bedrooms",
            "attribute_type": "number",
            "is_required": True,
            "is_filterable": True,
            "display_order": 1,
        },
    )
    assert bedrooms_response.status_code == 201, bedrooms_response.text
    bedrooms_id = bedrooms_response.json()["id"]

    parking_response = await client.post(
        f"/api/v1/categories/{category_id}/attributes",
        headers=admin_headers,
        json={
            "name": "Parking",
            "slug": "parking",
            "attribute_type": "boolean",
            "is_required": False,
            "is_filterable": True,
            "display_order": 2,
        },
    )
    assert parking_response.status_code == 201, parking_response.text
    parking_id = parking_response.json()["id"]

    categories_response = await client.get("/api/v1/categories/")
    assert categories_response.status_code == 200, categories_response.text
    assert categories_response.json()[0]["slug"] == "apartment"

    create_property_response = await client.post(
        "/api/v1/assets/",
        headers=landlord_headers,
        json={
            "property_type_id": category_id,
            "name": "Sunrise Heights",
            "description": "",
            "location_address": "Kathmandu, Nepal",
            "deposit_amount": 500,
            "min_rental_duration_hours": 24,
            "max_rental_duration_days": 120,
            "booking_lead_time_hours": 24,
            "instant_booking_enabled": True,
            "feature_values": [
                {"attribute_id": bedrooms_id, "value": 2},
                {"attribute_id": parking_id, "value": True},
            ],
        },
    )
    assert create_property_response.status_code == 201, create_property_response.text
    property_data = create_property_response.json()
    property_id = property_data["id"]
    assert property_data["status"] == "draft"
    assert property_data["is_published"] is False

    public_unpublished_detail_response = await client.get(f"/api/v1/properties/{property_id}")
    assert public_unpublished_detail_response.status_code == 404, public_unpublished_detail_response.text

    owner_unpublished_detail_response = await client.get(
        f"/api/v1/properties/{property_id}",
        headers=landlord_headers,
    )
    assert owner_unpublished_detail_response.status_code == 200, owner_unpublished_detail_response.text
    assert owner_unpublished_detail_response.json()["status"] == "draft"

    my_properties_response = await client.get(
        "/api/v1/properties/mine",
        headers=landlord_headers,
    )
    assert my_properties_response.status_code == 200, my_properties_response.text
    assert my_properties_response.json()["total"] == 1
    assert my_properties_response.json()["items"][0]["id"] == property_id

    unpublished_search_response = await client.get("/api/v1/assets/?category=apartment")
    assert unpublished_search_response.status_code == 200, unpublished_search_response.text
    assert unpublished_search_response.json()["total"] == 0

    update_property_response = await client.put(
        f"/api/v1/properties/{property_id}",
        headers=landlord_headers,
        json={
            "description": "Bright apartment with balcony and parking.",
            "location_address": "Boudha, Kathmandu",
        },
    )
    assert update_property_response.status_code == 200, update_property_response.text
    assert update_property_response.json()["description"].startswith("Bright apartment")

    publish_before_ready_response = await client.post(
        f"/api/v1/properties/{property_id}/publish",
        headers=landlord_headers,
    )
    assert publish_before_ready_response.status_code == 400, publish_before_ready_response.text
    assert "photos" in publish_before_ready_response.json()["detail"]["missing"]
    assert "pricing_rules" in publish_before_ready_response.json()["detail"]["missing"]

    upload_photo_response = await client.post(
        f"/api/v1/properties/{property_id}/photos",
        headers=landlord_headers,
        files={"file": ("cover.png", b"fake-image-bytes", "image/png")},
        data={"caption": "Front elevation", "position": "0", "is_cover": "true"},
    )
    assert upload_photo_response.status_code == 201, upload_photo_response.text
    photo_data = upload_photo_response.json()
    photo_id = photo_data["id"]
    photo_path = Path(settings.MEDIA_DIR) / extract_relative_media_path(photo_data["url"])
    assert photo_path.exists()

    daily_rule_response = await client.post(
        f"/api/v1/properties/{property_id}/pricing-rules",
        headers=landlord_headers,
        json={"rate_type": "daily", "rate_amount": 50, "currency": "NPR"},
    )
    assert daily_rule_response.status_code == 201, daily_rule_response.text

    weekly_rule_response = await client.post(
        f"/api/v1/properties/{property_id}/pricing-rules",
        headers=landlord_headers,
        json={"rate_type": "weekly", "rate_amount": 300, "currency": "NPR"},
    )
    assert weekly_rule_response.status_code == 201, weekly_rule_response.text
    weekly_rule_id = weekly_rule_response.json()["id"]

    monthly_rule_response = await client.post(
        f"/api/v1/properties/{property_id}/pricing-rules",
        headers=landlord_headers,
        json={"rate_type": "monthly", "rate_amount": 1000, "currency": "NPR"},
    )
    assert monthly_rule_response.status_code == 201, monthly_rule_response.text

    quote_start = (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=20))
    quote_end = quote_start + timedelta(days=45)
    peak_start = (quote_start + timedelta(days=3)).date().isoformat()
    peak_end = (quote_start + timedelta(days=4)).date().isoformat()

    peak_rule_response = await client.post(
        f"/api/v1/properties/{property_id}/pricing-rules",
        headers=landlord_headers,
        json={
            "rate_type": "daily",
            "rate_amount": 10,
            "currency": "NPR",
            "is_peak_rate": True,
            "peak_start_date": peak_start,
            "peak_end_date": peak_end,
        },
    )
    assert peak_rule_response.status_code == 201, peak_rule_response.text

    weekly_update_response = await client.put(
        f"/api/v1/properties/{property_id}/pricing-rules/{weekly_rule_id}",
        headers=landlord_headers,
        json={"rate_amount": 280},
    )
    assert weekly_update_response.status_code == 200, weekly_update_response.text
    assert weekly_update_response.json()["rate_amount"] == 280

    pricing_rules_response = await client.get(
        f"/api/v1/properties/{property_id}/pricing-rules",
        headers=landlord_headers,
    )
    assert pricing_rules_response.status_code == 200, pricing_rules_response.text
    assert len(pricing_rules_response.json()) == 4

    blocked_start = quote_start - timedelta(days=10)
    blocked_end = blocked_start + timedelta(days=2)
    block_response = await client.post(
        f"/api/v1/properties/{property_id}/availability-blocks",
        headers=landlord_headers,
        json={
            "block_type": "manual",
            "start_at": blocked_start.isoformat(),
            "end_at": blocked_end.isoformat(),
            "reason": "Owner stay",
        },
    )
    assert block_response.status_code == 201, block_response.text
    block_id = block_response.json()["id"]

    block_update_response = await client.put(
        f"/api/v1/properties/{property_id}/availability-blocks/{block_id}",
        headers=landlord_headers,
        json={"reason": "Family stay"},
    )
    assert block_update_response.status_code == 200, block_update_response.text
    assert block_update_response.json()["reason"] == "Family stay"

    sync_blocks_response = await client.put(
        f"/api/v1/properties/{property_id}",
        headers=landlord_headers,
        json={
            "availability_blocks": [
                {
                    "block_type": "maintenance",
                    "start_at": blocked_start.isoformat(),
                    "end_at": blocked_end.isoformat(),
                    "reason": "Scheduled repainting",
                }
            ]
        },
    )
    assert sync_blocks_response.status_code == 200, sync_blocks_response.text
    assert len(sync_blocks_response.json()["availability_blocks"]) == 1
    assert sync_blocks_response.json()["availability_blocks"][0]["reason"] == "Scheduled repainting"
    synced_block_id = sync_blocks_response.json()["availability_blocks"][0]["id"]

    blocks_list_response = await client.get(
        f"/api/v1/properties/{property_id}/availability-blocks",
        headers=landlord_headers,
    )
    assert blocks_list_response.status_code == 200, blocks_list_response.text
    assert len(blocks_list_response.json()) == 1
    assert blocks_list_response.json()[0]["reason"] == "Scheduled repainting"

    publish_response = await client.post(
        f"/api/v1/properties/{property_id}/publish",
        headers=landlord_headers,
    )
    assert publish_response.status_code == 200, publish_response.text
    assert publish_response.json()["status"] == "published"
    assert publish_response.json()["is_published"] is True

    blocked_availability_response = await client.get(
        f"/api/v1/properties/{property_id}/availability",
        params={"start": blocked_start.isoformat(), "end": blocked_end.isoformat()},
    )
    assert blocked_availability_response.status_code == 200, blocked_availability_response.text
    blocked_availability = blocked_availability_response.json()
    assert blocked_availability["is_available"] is False
    assert blocked_availability["next_available_start"].startswith(blocked_end.isoformat()[:19])
    assert len(blocked_availability["conflicts"]) == 1

    property_detail_response = await client.get(f"/api/v1/properties/{property_id}")
    assert property_detail_response.status_code == 200, property_detail_response.text
    property_detail = property_detail_response.json()
    assert property_detail["property_type"]["slug"] == "apartment"
    assert len(property_detail["photos"]) == 1
    assert len(property_detail["pricing_rules"]) == 4
    assert len(property_detail["availability_blocks"]) == 1

    quote_response = await client.get(
        f"/api/v1/properties/{property_id}/price",
        params={"start": quote_start.isoformat(), "end": quote_end.isoformat()},
    )
    assert quote_response.status_code == 200, quote_response.text
    quote_data = quote_response.json()
    assert quote_data["duration_days"] == 45
    assert quote_data["base_fee"] == 1610.0
    assert quote_data["peak_surcharge"] == 20.0
    assert quote_data["deposit_amount"] == 500.0
    assert quote_data["total_fee"] == 1630.0
    assert quote_data["total_due_now"] == 2130.0
    assert [item["units"] for item in quote_data["applied_rates"]] == [1, 2, 1]

    blocked_search_response = await client.get(
        "/api/v1/assets/",
        params={
            "category": "apartment",
            "start": blocked_start.isoformat(),
            "end": blocked_end.isoformat(),
            "location": "Kathmandu",
        },
    )
    assert blocked_search_response.status_code == 200, blocked_search_response.text
    assert blocked_search_response.json()["total"] == 0

    search_response = await client.get(
        "/api/v1/assets/",
        params={
            "category": "apartment",
            "start": quote_start.isoformat(),
            "end": quote_end.isoformat(),
            "location": "Boudha",
            "min_price": 1600,
            "max_price": 1700,
        },
    )
    assert search_response.status_code == 200, search_response.text
    search_payload = search_response.json()
    assert search_payload["total"] == 1
    assert search_payload["items"][0]["quote"]["total_fee"] == 1630.0
    assert search_payload["items"][0]["cover_photo_url"] == photo_data["url"]

    no_match_search_response = await client.get(
        "/api/v1/assets/",
        params={
            "category": "apartment",
            "start": quote_start.isoformat(),
            "end": quote_end.isoformat(),
            "max_price": 1000,
        },
    )
    assert no_match_search_response.status_code == 200, no_match_search_response.text
    assert no_match_search_response.json()["total"] == 0

    delete_block_response = await client.delete(
        f"/api/v1/properties/{property_id}/availability-blocks/{synced_block_id}",
        headers=landlord_headers,
    )
    assert delete_block_response.status_code == 204, delete_block_response.text

    archive_property_response = await client.delete(
        f"/api/v1/properties/{property_id}",
        headers=landlord_headers,
    )
    assert archive_property_response.status_code == 204, archive_property_response.text

    archived_search_response = await client.get("/api/v1/assets/?category=apartment")
    assert archived_search_response.status_code == 200, archived_search_response.text
    assert archived_search_response.json()["total"] == 0

    delete_photo_response = await client.delete(
        f"/api/v1/properties/{property_id}/photos/{photo_id}",
        headers=landlord_headers,
    )
    assert delete_photo_response.status_code == 204, delete_photo_response.text
    assert not photo_path.exists()

    property_result = await db_session.execute(select(Property).where(Property.id == decode_property_id(property_id)))
    property_obj = property_result.scalars().one()
    assert property_obj.status == PropertyStatus.ARCHIVED
    assert property_obj.is_published is False


def decode_property_id(hashid: str) -> int:
    from src.apps.iam.utils.hashid import decode_id

    decoded = decode_id(hashid)
    assert decoded is not None
    return decoded
