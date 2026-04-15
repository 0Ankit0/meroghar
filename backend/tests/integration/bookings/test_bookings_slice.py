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
from src.apps.iam.models.user import User
from src.apps.iam.utils.hashid import encode_id
from src.apps.listings.models.property import Property, PropertyStatus
from src.apps.listings.models.property_type import PropertyType
from src.apps.pricing.models.pricing_rule import PricingRateType, PricingRule
from src.apps.availability.models.availability_block import AvailabilityBlock
from src.apps.bookings.models.booking import Booking, SecurityDeposit
from src.apps.bookings.models.agreement import RentalAgreement


async def _make_user(db: AsyncSession, **kwargs) -> User:
    user = User(
        username=kwargs.get("username", "user"),
        email=kwargs.get("email", "user@example.com"),
        hashed_password=security.get_password_hash(kwargs.get("password", "TestPass123")),
        is_active=True,
        is_superuser=kwargs.get("is_superuser", False),
        is_confirmed=True,
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


async def _create_published_property(
    db: AsyncSession,
    *,
    owner_user_id: int,
    slug_suffix: str,
    instant_booking_enabled: bool = False,
    booking_lead_time_hours: int = 0,
) -> Property:
    property_type = PropertyType(
        name=f"Apartment {slug_suffix}",
        slug=f"apartment-{slug_suffix}",
        description="Urban apartment",
        icon_url="building",
        is_active=True,
        display_order=1,
    )
    db.add(property_type)
    await db.flush()

    property_obj = Property(
        owner_user_id=owner_user_id,
        property_type_id=property_type.id,
        name=f"Sunrise Heights {slug_suffix}",
        description="Bright apartment",
        status=PropertyStatus.PUBLISHED,
        is_published=True,
        location_address="Kathmandu, Nepal",
        deposit_amount=500.0,
        min_rental_duration_hours=24,
        max_rental_duration_days=120,
        booking_lead_time_hours=booking_lead_time_hours,
        instant_booking_enabled=instant_booking_enabled,
        average_rating=4.8,
        review_count=12,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(property_obj)
    await db.flush()

    daily_rule = PricingRule(
        property_id=property_obj.id,
        rate_type=PricingRateType.DAILY,
        rate_amount=100.0,
        currency="NPR",
        created_at=datetime.now(),
    )
    weekly_rule = PricingRule(
        property_id=property_obj.id,
        rate_type=PricingRateType.WEEKLY,
        rate_amount=650.0,
        currency="NPR",
        created_at=datetime.now(),
    )
    db.add(daily_rule)
    db.add(weekly_rule)
    await db.commit()
    await db.refresh(property_obj)
    return property_obj


async def _get_quote(
    client: AsyncClient,
    property_id: str,
    *,
    start_at: datetime,
    end_at: datetime,
) -> dict[str, object]:
    response = await client.get(
        f"/api/v1/properties/{property_id}/price",
        params={"start": start_at.isoformat(), "end": end_at.isoformat()},
    )
    assert response.status_code == 200, response.text
    return response.json()


async def _get_booking_by_number(db: AsyncSession, booking_number: str) -> Booking:
    result = await db.execute(select(Booking).where(Booking.booking_number == booking_number))
    return result.scalars().one()


@pytest.fixture(autouse=True)
def cleanup_agreement_media() -> None:
    yield
    agreements_dir = Path(settings.MEDIA_DIR) / "agreements"
    if agreements_dir.exists():
        shutil.rmtree(agreements_dir)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_booking_agreement_and_return_workflow(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    landlord = await _make_user(db_session, username="booklandlord", email="booklandlord@example.com")
    tenant = await _make_user(db_session, username="booktenant", email="booktenant@example.com")
    property_obj = await _create_published_property(
        db_session,
        owner_user_id=landlord.id,
        slug_suffix="workflow",
    )

    landlord_token = await _login(client, landlord.username)
    tenant_token = await _login(client, tenant.username)
    landlord_headers = {"Authorization": f"Bearer {landlord_token}"}
    tenant_headers = {"Authorization": f"Bearer {tenant_token}"}
    property_id = encode_id(property_obj.id)

    start_at = datetime.now() + timedelta(days=10)
    end_at = start_at + timedelta(days=4)
    initial_quote = await _get_quote(client, property_id, start_at=start_at, end_at=end_at)
    create_response = await client.post(
        "/api/v1/bookings",
        headers=tenant_headers,
        json={
            "property_id": property_id,
            "rental_start_at": start_at.isoformat(),
            "rental_end_at": end_at.isoformat(),
            "special_requests": "Need early check-in if possible.",
            "payment_method_id": "pm_booking_workflow",
            "quoted_total_fee": initial_quote["total_fee"],
            "quoted_deposit_amount": initial_quote["deposit_amount"],
            "quoted_currency": initial_quote["currency"],
        },
    )
    assert create_response.status_code == 201, create_response.text
    booking = create_response.json()
    booking_id = booking["id"]
    assert booking["status"] == "pending"
    assert booking["property"]["id"] == property_id
    assert booking["pricing"]["total_due_now"] == pytest.approx(
        booking["pricing"]["total_fee"] + booking["pricing"]["deposit_amount"]
    )

    detail_response = await client.get(f"/api/v1/bookings/{booking_id}", headers=tenant_headers)
    assert detail_response.status_code == 200, detail_response.text
    assert detail_response.json()["booking_number"].startswith("BKG-")

    list_response = await client.get(
        "/api/v1/bookings",
        headers=landlord_headers,
        params={"status": "pending"},
    )
    assert list_response.status_code == 200, list_response.text
    assert list_response.json()["total"] == 1
    assert list_response.json()["items"][0]["id"] == booking_id

    updated_end_at = end_at + timedelta(days=2)
    update_response = await client.put(
        f"/api/v1/bookings/{booking_id}",
        headers=tenant_headers,
        json={
            "rental_end_at": updated_end_at.isoformat(),
            "special_requests": "Please include move-in instructions.",
        },
    )
    assert update_response.status_code == 200, update_response.text
    updated_booking = update_response.json()
    assert updated_booking["rental_end_at"].startswith(updated_end_at.date().isoformat())
    assert updated_booking["special_requests"].startswith("Please include")
    assert updated_booking["pricing"]["total_fee"] > booking["pricing"]["total_fee"]

    confirm_response = await client.post(
        f"/api/v1/bookings/{booking_id}/confirm",
        headers=landlord_headers,
    )
    assert confirm_response.status_code == 200, confirm_response.text
    confirmed_booking = confirm_response.json()
    assert confirmed_booking["status"] == "confirmed"
    assert confirmed_booking["confirmed_at"] is not None

    generate_agreement_response = await client.post(
        f"/api/v1/bookings/{booking_id}/agreement",
        headers=landlord_headers,
        json={"custom_clauses": ["Tenant must share utility meter readings monthly."]},
    )
    assert generate_agreement_response.status_code == 201, generate_agreement_response.text
    agreement = generate_agreement_response.json()
    assert agreement["status"] == "draft"
    assert agreement["custom_clauses"] == ["Tenant must share utility meter readings monthly."]
    assert agreement["rendered_document_url"]

    send_response = await client.post(
        f"/api/v1/bookings/{booking_id}/agreement/send",
        headers=landlord_headers,
    )
    assert send_response.status_code == 200, send_response.text
    sent_agreement = send_response.json()
    assert sent_agreement["status"] == "pending_customer_signature"
    assert sent_agreement["esign_request_id"]

    webhook_response = await client.post(
        "/api/v1/webhooks/esign",
        json={
            "esign_request_id": sent_agreement["esign_request_id"],
            "event_type": "customer.signed",
            "signed_at": (datetime.now() + timedelta(minutes=5)).isoformat(),
            "ip_address": "203.0.113.10",
        },
    )
    assert webhook_response.status_code == 200, webhook_response.text
    webhook_agreement = webhook_response.json()["agreement"]
    assert webhook_agreement["status"] == "pending_owner_signature"
    assert webhook_agreement["customer_signature_ip"] == "203.0.113.10"

    countersign_response = await client.post(
        f"/api/v1/bookings/{booking_id}/agreement/countersign",
        headers=landlord_headers,
    )
    assert countersign_response.status_code == 200, countersign_response.text
    signed_agreement = countersign_response.json()
    assert signed_agreement["status"] == "signed"
    assert signed_agreement["signed_document_url"]

    agreement_get_response = await client.get(
        f"/api/v1/bookings/{booking_id}/agreement",
        headers=tenant_headers,
    )
    assert agreement_get_response.status_code == 200, agreement_get_response.text
    assert agreement_get_response.json()["status"] == "signed"

    booking_db = await _get_booking_by_number(db_session, confirmed_booking["booking_number"])
    booking_db.rental_start_at = datetime.now() - timedelta(days=3)
    booking_db.rental_end_at = datetime.now() + timedelta(days=2)
    block = (await db_session.execute(select(AvailabilityBlock).where(AvailabilityBlock.booking_id == booking_db.id))).scalars().first()
    block.start_at = booking_db.rental_start_at
    block.end_at = booking_db.rental_end_at
    db_session.add(booking_db)
    db_session.add(block)
    await db_session.commit()

    return_at = datetime.now() - timedelta(hours=1)
    tenant_return_response = await client.post(
        f"/api/v1/bookings/{booking_id}/return",
        headers=tenant_headers,
        json={
            "actual_return_at": return_at.isoformat(),
            "notes": "Tenant should not be able to close the booking.",
        },
    )
    assert tenant_return_response.status_code == 403, tenant_return_response.text

    return_response = await client.post(
        f"/api/v1/bookings/{booking_id}/return",
        headers=landlord_headers,
        json={
            "actual_return_at": return_at.isoformat(),
            "notes": "Keys returned to concierge desk.",
        },
    )
    assert return_response.status_code == 200, return_response.text
    returned_booking = return_response.json()
    assert returned_booking["status"] == "closed"
    assert returned_booking["actual_return_at"].startswith(return_at.date().isoformat())
    assert returned_booking["security_deposit"]["status"] == "fully_refunded"
    assert returned_booking["agreement_status"] == "terminated"

    events_response = await client.get(
        f"/api/v1/bookings/{booking_id}/events",
        headers=landlord_headers,
    )
    assert events_response.status_code == 200, events_response.text
    event_types = [event["event_type"] for event in events_response.json()]
    assert event_types == [
        "booking.created",
        "booking.updated",
        "booking.confirmed",
        "agreement.generated",
        "agreement.sent",
        "agreement.customer_signed",
        "agreement.signed",
        "agreement.terminated",
        "booking.returned",
    ]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_booking_idempotency_conflicts_and_cancel_refund(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    landlord = await _make_user(db_session, username="refundlandlord", email="refundlandlord@example.com")
    tenant = await _make_user(db_session, username="refundtenant", email="refundtenant@example.com")
    second_tenant = await _make_user(db_session, username="otherrefund", email="otherrefund@example.com")
    property_obj = await _create_published_property(
        db_session,
        owner_user_id=landlord.id,
        slug_suffix="refund",
    )

    tenant_token = await _login(client, tenant.username)
    second_tenant_token = await _login(client, second_tenant.username)
    tenant_headers = {"Authorization": f"Bearer {tenant_token}"}
    second_tenant_headers = {"Authorization": f"Bearer {second_tenant_token}"}
    property_id = encode_id(property_obj.id)

    start_at = datetime.now() + timedelta(hours=48)
    end_at = start_at + timedelta(days=3)
    quote = await _get_quote(client, property_id, start_at=start_at, end_at=end_at)
    request_headers = {
        **tenant_headers,
        "Idempotency-Key": "tenant-refund-booking-1",
    }
    payload = {
        "property_id": property_id,
        "rental_start_at": start_at.isoformat(),
        "rental_end_at": end_at.isoformat(),
        "special_requests": "Keep the parking slot available.",
        "payment_method_id": "pm_booking_refund",
        "quoted_total_fee": quote["total_fee"],
        "quoted_deposit_amount": quote["deposit_amount"],
        "quoted_currency": quote["currency"],
    }
    first_create_response = await client.post(
        "/api/v1/bookings",
        headers=request_headers,
        json=payload,
    )
    assert first_create_response.status_code == 201, first_create_response.text
    booking = first_create_response.json()

    second_create_response = await client.post(
        "/api/v1/bookings",
        headers=request_headers,
        json=payload,
    )
    assert second_create_response.status_code == 200, second_create_response.text
    assert second_create_response.json()["id"] == booking["id"]

    booking_count = (
        await db_session.execute(select(Booking).where(Booking.tenant_user_id == tenant.id))
    ).scalars().all()
    assert len(booking_count) == 1

    conflict_response = await client.post(
        "/api/v1/bookings",
        headers=second_tenant_headers,
        json={
            **payload,
            "payment_method_id": "pm_booking_conflict",
        },
    )
    assert conflict_response.status_code == 409, conflict_response.text
    assert conflict_response.json()["detail"]["code"] == "BOOKING_UNAVAILABLE"

    cancel_response = await client.post(
        f"/api/v1/bookings/{booking['id']}/cancel",
        headers=tenant_headers,
        json={"reason": "Travel plans changed."},
    )
    assert cancel_response.status_code == 200, cancel_response.text
    cancelled_booking = cancel_response.json()
    assert cancelled_booking["status"] == "cancelled"
    assert cancelled_booking["refund_amount"] == pytest.approx(quote["total_fee"] * 0.5)
    assert cancelled_booking["security_deposit"]["status"] == "fully_refunded"
    assert cancelled_booking["security_deposit"]["refund_amount"] == pytest.approx(quote["deposit_amount"])

    retry_response = await client.post(
        "/api/v1/bookings",
        headers=second_tenant_headers,
        json={
            **payload,
            "payment_method_id": "pm_booking_rebook",
        },
    )
    assert retry_response.status_code == 201, retry_response.text


@pytest.mark.integration
@pytest.mark.asyncio
async def test_landlord_decline_releases_booking_hold(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    landlord = await _make_user(db_session, username="declinelandlord", email="declinelandlord@example.com")
    tenant = await _make_user(db_session, username="declinetenant", email="declinetenant@example.com")
    second_tenant = await _make_user(db_session, username="declineother", email="declineother@example.com")
    property_obj = await _create_published_property(
        db_session,
        owner_user_id=landlord.id,
        slug_suffix="decline",
    )

    landlord_token = await _login(client, landlord.username)
    tenant_token = await _login(client, tenant.username)
    second_tenant_token = await _login(client, second_tenant.username)
    landlord_headers = {"Authorization": f"Bearer {landlord_token}"}
    tenant_headers = {"Authorization": f"Bearer {tenant_token}"}
    second_tenant_headers = {"Authorization": f"Bearer {second_tenant_token}"}
    property_id = encode_id(property_obj.id)

    start_at = datetime.now() + timedelta(days=7)
    end_at = start_at + timedelta(days=2)
    quote = await _get_quote(client, property_id, start_at=start_at, end_at=end_at)
    create_response = await client.post(
        "/api/v1/bookings",
        headers=tenant_headers,
        json={
            "property_id": property_id,
            "rental_start_at": start_at.isoformat(),
            "rental_end_at": end_at.isoformat(),
            "payment_method_id": "pm_booking_decline",
            "quoted_total_fee": quote["total_fee"],
            "quoted_deposit_amount": quote["deposit_amount"],
            "quoted_currency": quote["currency"],
        },
    )
    assert create_response.status_code == 201, create_response.text
    booking = create_response.json()

    decline_response = await client.post(
        f"/api/v1/bookings/{booking['id']}/decline",
        headers=landlord_headers,
        json={"reason": "Property maintenance is scheduled for those dates."},
    )
    assert decline_response.status_code == 200, decline_response.text
    declined_booking = decline_response.json()
    assert declined_booking["status"] == "declined"
    assert declined_booking["refund_amount"] == pytest.approx(quote["total_fee"])
    assert declined_booking["security_deposit"]["refund_amount"] == pytest.approx(quote["deposit_amount"])

    declined_booking_db = await _get_booking_by_number(db_session, declined_booking["booking_number"])
    block = (
        await db_session.execute(
            select(AvailabilityBlock).where(AvailabilityBlock.booking_id == declined_booking_db.id)
        )
    ).scalars().first()
    assert block is None

    replacement_response = await client.post(
        "/api/v1/bookings",
        headers=second_tenant_headers,
        json={
            "property_id": property_id,
            "rental_start_at": start_at.isoformat(),
            "rental_end_at": end_at.isoformat(),
            "payment_method_id": "pm_booking_replacement",
            "quoted_total_fee": quote["total_fee"],
            "quoted_deposit_amount": quote["deposit_amount"],
            "quoted_currency": quote["currency"],
        },
    )
    assert replacement_response.status_code == 201, replacement_response.text

    deposit_record = (
        await db_session.execute(select(SecurityDeposit).where(SecurityDeposit.booking_id.is_not(None)))
    ).scalars().all()
    assert any(item.status.value == "fully_refunded" for item in deposit_record)

    agreement_records = (await db_session.execute(select(RentalAgreement))).scalars().all()
    assert agreement_records == []
