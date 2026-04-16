from __future__ import annotations

import json
import shutil
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.apps.core.config import settings
from src.apps.iam.utils.hashid import encode_id
from src.apps.availability.models.availability_block import AvailabilityBlock
from src.apps.invoicing.models.invoice import AdditionalCharge, AdditionalChargeStatus
from src.apps.utility_billing.models.utility_bill import UtilityBill, UtilityBillSplit, UtilityBillSplitStatus
from tests.integration.bookings.test_bookings_slice import (
    _create_published_property,
    _get_booking_by_number,
    _get_quote,
    _login,
    _make_user,
)


def _mock_khalti_gateway():
    initiated_amounts: dict[str, int] = {}

    async def _post(url: str, *, json: dict[str, object], **_: object) -> MagicMock:
        response = MagicMock(spec=Response)
        if url.endswith("epayment/initiate/"):
            purchase_order_id = str(json["purchase_order_id"])
            pidx = f"test-pidx-{purchase_order_id}"
            initiated_amounts[pidx] = int(json["amount"])
            payload = {
                "pidx": pidx,
                "payment_url": f"https://test-pay.khalti.com/?pidx={pidx}",
                "expires_at": "2026-12-31T23:59:59",
                "expires_in": 1800,
            }
            response.status_code = 200
            response.json.return_value = payload
            response.text = json_module.dumps(payload)
            return response

        if url.endswith("epayment/lookup/"):
            pidx = str(json["pidx"])
            payload = {
                "pidx": pidx,
                "total_amount": initiated_amounts[pidx],
                "status": "Completed",
                "transaction_id": f"KHALTI-{pidx}",
                "fee": 0,
                "refunded": False,
            }
            response.status_code = 200
            response.json.return_value = payload
            response.text = json_module.dumps(payload)
            return response

        raise AssertionError(f"Unexpected Khalti URL: {url}")

    json_module = json
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(side_effect=_post)
    return patch("src.apps.finance.services.khalti.httpx.AsyncClient", return_value=mock_client)


async def _create_confirmed_booking(
    client: AsyncClient,
    db_session: AsyncSession,
    *,
    landlord_username: str,
    tenant_username: str,
    slug_suffix: str,
    start_at: datetime,
    end_at: datetime,
) -> tuple[dict[str, str], dict[str, str], str, str, str]:
    landlord = await _make_user(
        db_session,
        username=landlord_username,
        email=f"{landlord_username}@example.com",
    )
    tenant = await _make_user(
        db_session,
        username=tenant_username,
        email=f"{tenant_username}@example.com",
    )
    property_obj = await _create_published_property(
        db_session,
        owner_user_id=landlord.id,
        slug_suffix=slug_suffix,
    )

    landlord_token = await _login(client, landlord.username)
    tenant_token = await _login(client, tenant.username)
    landlord_headers = {"Authorization": f"Bearer {landlord_token}"}
    tenant_headers = {"Authorization": f"Bearer {tenant_token}"}
    property_id = encode_id(property_obj.id)

    quote = await _get_quote(client, property_id, start_at=start_at, end_at=end_at)
    create_response = await client.post(
        "/api/v1/bookings",
        headers=tenant_headers,
        json={
            "property_id": property_id,
            "rental_start_at": start_at.isoformat(),
            "rental_end_at": end_at.isoformat(),
            "special_requests": "Billing slice integration scenario.",
            "payment_method_id": f"pm-{slug_suffix}",
            "quoted_total_fee": quote["total_fee"],
            "quoted_deposit_amount": quote["deposit_amount"],
            "quoted_currency": quote["currency"],
        },
    )
    assert create_response.status_code == 201, create_response.text
    booking = create_response.json()

    confirm_response = await client.post(
        f"/api/v1/bookings/{booking['id']}/confirm",
        headers=landlord_headers,
    )
    assert confirm_response.status_code == 200, confirm_response.text

    return landlord_headers, tenant_headers, property_id, booking["id"], booking["booking_number"]


async def _move_booking_into_returnable_window(
    db_session: AsyncSession,
    booking_number: str,
) -> None:
    booking_db = await _get_booking_by_number(db_session, booking_number)
    booking_db.rental_start_at = datetime.now() - timedelta(days=4)
    booking_db.rental_end_at = datetime.now() + timedelta(days=1)
    block = (
        await db_session.execute(
            select(AvailabilityBlock).where(AvailabilityBlock.booking_id == booking_db.id)
        )
    ).scalars().first()
    assert block is not None
    block.start_at = booking_db.rental_start_at
    block.end_at = booking_db.rental_end_at
    db_session.add(booking_db)
    db_session.add(block)
    await db_session.commit()


@pytest.fixture(autouse=True)
def cleanup_billing_media() -> None:
    yield
    for folder_name in ("agreements", "utility-bills"):
        target = Path(settings.MEDIA_DIR) / folder_name
        if target.exists():
            shutil.rmtree(target)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rent_ledger_partial_payment_and_receipt_flow(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    start_at = datetime.now() + timedelta(days=14)
    end_at = start_at + timedelta(days=40)
    landlord_headers, tenant_headers, _, booking_id, _ = await _create_confirmed_booking(
        client,
        db_session,
        landlord_username="billinglandlord",
        tenant_username="billingtenant",
        slug_suffix="billing-rent",
        start_at=start_at,
        end_at=end_at,
    )

    ledger_response = await client.get(
        f"/api/v1/bookings/{booking_id}/rent-ledger",
        headers=tenant_headers,
    )
    assert ledger_response.status_code == 200, ledger_response.text
    ledger = ledger_response.json()
    assert len(ledger["entries"]) == 2
    assert ledger["entries"][0]["amount_due"] > 0
    assert ledger["entries"][1]["amount_due"] > 0
    assert ledger["total_amount"] == pytest.approx(
        ledger["entries"][0]["amount_due"] + ledger["entries"][1]["amount_due"]
    )

    invoice_list_response = await client.get("/api/v1/invoices", headers=tenant_headers)
    assert invoice_list_response.status_code == 200, invoice_list_response.text
    invoice_list = invoice_list_response.json()
    assert invoice_list["total"] == 2
    first_invoice = invoice_list["items"][0]
    invoice_id = first_invoice["id"]
    half_amount = round(first_invoice["total_amount"] / 2, 2)

    with _mock_khalti_gateway():
        partial_payment_response = await client.post(
            f"/api/v1/invoices/{invoice_id}/partial-pay",
            headers=tenant_headers,
            json={
                "provider": "khalti",
                "amount": half_amount,
                "return_url": "http://localhost:3000/payment-callback?provider=khalti",
                "website_url": "http://localhost:3000",
            },
        )
        assert partial_payment_response.status_code == 200, partial_payment_response.text
        first_pidx = partial_payment_response.json()["provider_pidx"]

        verify_partial_response = await client.post(
            "/api/v1/payments/verify/",
            json={"provider": "khalti", "pidx": first_pidx},
        )
        assert verify_partial_response.status_code == 200, verify_partial_response.text
        assert verify_partial_response.json()["status"] == "completed"

        partially_paid_invoice_response = await client.get(
            f"/api/v1/invoices/{invoice_id}",
            headers=tenant_headers,
        )
        assert partially_paid_invoice_response.status_code == 200, partially_paid_invoice_response.text
        partially_paid_invoice = partially_paid_invoice_response.json()
        assert partially_paid_invoice["status"] == "partially_paid"
        assert partially_paid_invoice["paid_amount"] == pytest.approx(half_amount)
        assert partially_paid_invoice["outstanding_amount"] == pytest.approx(
            round(first_invoice["total_amount"] - half_amount, 2)
        )

        settle_response = await client.post(
            f"/api/v1/invoices/{invoice_id}/pay",
            headers=tenant_headers,
            json={
                "provider": "khalti",
                "return_url": "http://localhost:3000/payment-callback?provider=khalti",
                "website_url": "http://localhost:3000",
            },
        )
        assert settle_response.status_code == 200, settle_response.text
        second_pidx = settle_response.json()["provider_pidx"]

        verify_settle_response = await client.post(
            "/api/v1/payments/verify/",
            json={"provider": "khalti", "pidx": second_pidx},
        )
        assert verify_settle_response.status_code == 200, verify_settle_response.text
        assert verify_settle_response.json()["status"] == "completed"

    paid_invoice_response = await client.get(
        f"/api/v1/invoices/{invoice_id}",
        headers=tenant_headers,
    )
    assert paid_invoice_response.status_code == 200, paid_invoice_response.text
    paid_invoice = paid_invoice_response.json()
    assert paid_invoice["status"] == "paid"
    assert paid_invoice["paid_amount"] == pytest.approx(first_invoice["total_amount"])
    assert paid_invoice["outstanding_amount"] == pytest.approx(0.0)

    paid_filter_response = await client.get(
        "/api/v1/invoices",
        headers=landlord_headers,
        params={"status": "paid"},
    )
    assert paid_filter_response.status_code == 200, paid_filter_response.text
    assert paid_filter_response.json()["total"] == 1

    receipt_response = await client.get(
        f"/api/v1/invoices/{invoice_id}/receipt",
        headers=tenant_headers,
    )
    assert receipt_response.status_code == 200, receipt_response.text
    assert "MEROGHAR PAYMENT RECEIPT" in receipt_response.text
    assert paid_invoice["invoice_number"] in receipt_response.text


@pytest.mark.integration
@pytest.mark.asyncio
async def test_additional_charge_dispute_and_closeout_workflow(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    start_at = datetime.now() + timedelta(days=7)
    end_at = start_at + timedelta(days=6)
    landlord_headers, tenant_headers, _, booking_id, booking_number = await _create_confirmed_booking(
        client,
        db_session,
        landlord_username="chargelandlord",
        tenant_username="chargetenant",
        slug_suffix="billing-charge",
        start_at=start_at,
        end_at=end_at,
    )

    await _move_booking_into_returnable_window(db_session, booking_number)

    return_response = await client.post(
        f"/api/v1/bookings/{booking_id}/return",
        headers=landlord_headers,
        json={
            "actual_return_at": (datetime.now() - timedelta(hours=2)).isoformat(),
            "notes": "Property returned for post-tenancy billing checks.",
        },
    )
    assert return_response.status_code == 200, return_response.text
    assert return_response.json()["status"] == "closed"

    charge_response = await client.post(
        f"/api/v1/bookings/{booking_id}/additional-charges",
        headers=landlord_headers,
        json={
            "charge_type": "damage",
            "description": "Living-room wall repair and lock replacement",
            "amount": 600,
            "evidence_url": "https://example.com/evidence/wall-repair.jpg",
        },
    )
    assert charge_response.status_code == 201, charge_response.text
    charge = charge_response.json()
    charge_id = charge["id"]
    charge_invoice_id = charge["invoice_id"]
    assert charge["status"] == "raised"

    dispute_response = await client.post(
        f"/api/v1/additional-charges/{charge_id}/dispute",
        headers=tenant_headers,
        json={"reason": "The damage existed before move-in."},
    )
    assert dispute_response.status_code == 200, dispute_response.text
    assert dispute_response.json()["status"] == "disputed"

    resolve_response = await client.post(
        f"/api/v1/additional-charges/{charge_id}/resolve",
        headers=landlord_headers,
        json={
            "outcome": "accepted",
            "resolution_notes": "Inspection photos confirm the damage occurred during tenancy.",
        },
    )
    assert resolve_response.status_code == 200, resolve_response.text
    assert resolve_response.json()["status"] == "accepted"

    charge_invoice_response = await client.get(
        f"/api/v1/invoices/{charge_invoice_id}",
        headers=tenant_headers,
    )
    assert charge_invoice_response.status_code == 200, charge_invoice_response.text
    charge_invoice = charge_invoice_response.json()
    assert charge_invoice["status"] == "partially_paid"
    assert charge_invoice["paid_amount"] == pytest.approx(500.0)
    assert charge_invoice["outstanding_amount"] == pytest.approx(100.0)

    booking_detail_response = await client.get(
        f"/api/v1/bookings/{booking_id}",
        headers=landlord_headers,
    )
    assert booking_detail_response.status_code == 200, booking_detail_response.text
    booking_detail = booking_detail_response.json()
    assert booking_detail["status"] == "pending_closure"
    assert booking_detail["security_deposit"]["status"] == "fully_deducted"
    assert booking_detail["security_deposit"]["deduction_total"] == pytest.approx(500.0)

    with _mock_khalti_gateway():
        settle_response = await client.post(
            f"/api/v1/invoices/{charge_invoice_id}/pay",
            headers=tenant_headers,
            json={
                "provider": "khalti",
                "return_url": "http://localhost:3000/payment-callback?provider=khalti",
                "website_url": "http://localhost:3000",
            },
        )
        assert settle_response.status_code == 200, settle_response.text
        verify_response = await client.post(
            "/api/v1/payments/verify/",
            json={"provider": "khalti", "pidx": settle_response.json()["provider_pidx"]},
        )
        assert verify_response.status_code == 200, verify_response.text
        assert verify_response.json()["status"] == "completed"

    final_booking_response = await client.get(
        f"/api/v1/bookings/{booking_id}",
        headers=landlord_headers,
    )
    assert final_booking_response.status_code == 200, final_booking_response.text
    assert final_booking_response.json()["status"] == "closed"

    resolved_charge = (
        await db_session.execute(
            select(AdditionalCharge).where(
                AdditionalCharge.invoice_id == _decode_hashid(charge_invoice_id)
            )
        )
    ).scalars().one()
    assert resolved_charge.status == AdditionalChargeStatus.PAID


def _decode_hashid(value: str) -> int:
    from src.apps.iam.utils.hashid import decode_id

    decoded = decode_id(value)
    assert decoded is not None
    return decoded


@pytest.mark.integration
@pytest.mark.asyncio
async def test_utility_bill_publication_dispute_and_settlement_workflow(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    start_at = datetime.now() + timedelta(days=10)
    end_at = start_at + timedelta(days=8)
    landlord_headers, tenant_headers, property_id, booking_id, booking_number = await _create_confirmed_booking(
        client,
        db_session,
        landlord_username="utilitylandlord",
        tenant_username="utilitytenant",
        slug_suffix="billing-utility",
        start_at=start_at,
        end_at=end_at,
    )

    await _move_booking_into_returnable_window(db_session, booking_number)
    return_response = await client.post(
        f"/api/v1/bookings/{booking_id}/return",
        headers=landlord_headers,
        json={
            "actual_return_at": (datetime.now() - timedelta(hours=3)).isoformat(),
            "notes": "Returned before utility settlement workflow.",
        },
    )
    assert return_response.status_code == 200, return_response.text

    bill_response = await client.post(
        f"/api/v1/properties/{property_id}/utility-bills",
        headers=landlord_headers,
        json={
            "bill_type": "electricity",
            "billing_period_label": "April electricity",
            "period_start": (date.today() - timedelta(days=3)).isoformat(),
            "period_end": date.today().isoformat(),
            "due_date": (date.today() + timedelta(days=7)).isoformat(),
            "total_amount": 300,
            "owner_subsidy_amount": 50,
            "notes": "Meter reading and common-area allocation included.",
        },
    )
    assert bill_response.status_code == 201, bill_response.text
    bill = bill_response.json()
    bill_id = bill["id"]
    assert bill["status"] == "draft"
    assert bill["payable_amount"] == pytest.approx(250.0)

    attachment_response = await client.post(
        f"/api/v1/utility-bills/{bill_id}/attachments",
        headers=landlord_headers,
        files={"file": ("electricity-bill.pdf", b"fake-pdf-content", "application/pdf")},
    )
    assert attachment_response.status_code == 200, attachment_response.text
    assert attachment_response.json()["file_type"] == "application/pdf"

    split_response = await client.post(
        f"/api/v1/utility-bills/{bill_id}/splits",
        headers=landlord_headers,
        json={"default_method": "single"},
    )
    assert split_response.status_code == 200, split_response.text
    split_bill = split_response.json()
    assert len(split_bill["splits"]) == 1
    assert split_bill["splits"][0]["assigned_amount"] == pytest.approx(250.0)

    publish_response = await client.post(
        f"/api/v1/utility-bills/{bill_id}/publish",
        headers=landlord_headers,
    )
    assert publish_response.status_code == 200, publish_response.text
    published_bill = publish_response.json()
    assert published_bill["status"] == "published"
    bill_share_id = published_bill["splits"][0]["id"]

    bill_shares_response = await client.get(
        "/api/v1/tenants/me/bill-shares",
        headers=tenant_headers,
    )
    assert bill_shares_response.status_code == 200, bill_shares_response.text
    bill_share = bill_shares_response.json()["items"][0]
    assert bill_share["split"]["id"] == bill_share_id
    assert bill_share["split"]["status"] == "pending"
    assert len(bill_share["bill"]["attachments"]) == 1

    dispute_response = await client.post(
        f"/api/v1/bill-shares/{bill_share_id}/dispute",
        headers=tenant_headers,
        json={"reason": "Please confirm the peak/off-peak split."},
    )
    assert dispute_response.status_code == 200, dispute_response.text
    assert dispute_response.json()["status"] == "open"

    resolve_dispute_response = await client.post(
        f"/api/v1/bill-shares/{bill_share_id}/resolve-dispute",
        headers=landlord_headers,
        json={
            "outcome": "rejected",
            "resolution_notes": "Meter statement and subsidy note were verified.",
        },
    )
    assert resolve_dispute_response.status_code == 200, resolve_dispute_response.text
    assert resolve_dispute_response.json()["status"] == "rejected"

    with _mock_khalti_gateway():
        pay_response = await client.post(
            f"/api/v1/bill-shares/{bill_share_id}/pay",
            headers=tenant_headers,
            json={
                "provider": "khalti",
                "return_url": "http://localhost:3000/payment-callback?provider=khalti",
                "website_url": "http://localhost:3000",
            },
        )
        assert pay_response.status_code == 200, pay_response.text
        verify_response = await client.post(
            "/api/v1/payments/verify/",
            json={"provider": "khalti", "pidx": pay_response.json()["provider_pidx"]},
        )
        assert verify_response.status_code == 200, verify_response.text
        assert verify_response.json()["status"] == "completed"

    settled_bill_shares_response = await client.get(
        "/api/v1/tenants/me/bill-shares",
        headers=tenant_headers,
    )
    assert settled_bill_shares_response.status_code == 200, settled_bill_shares_response.text
    settled_bill_share = settled_bill_shares_response.json()["items"][0]
    assert settled_bill_share["split"]["status"] == "paid"
    assert settled_bill_share["bill"]["status"] == "settled"
    assert settled_bill_share["split"]["outstanding_amount"] == pytest.approx(0.0)

    bill_history_response = await client.get(
        f"/api/v1/utility-bills/{bill_id}/history",
        headers=landlord_headers,
    )
    assert bill_history_response.status_code == 200, bill_history_response.text
    event_types = {entry["event_type"] for entry in bill_history_response.json()["entries"]}
    assert {
        "utility_bill.created",
        "utility_bill.attachment_uploaded",
        "utility_bill.split_configured",
        "utility_bill.published",
        "utility_bill.dispute",
        "utility_bill.dispute_resolved",
        "utility_bill.paid",
    }.issubset(event_types)

    bill_db = await db_session.get(UtilityBill, _decode_hashid(bill_id))
    split_db = await db_session.get(UtilityBillSplit, _decode_hashid(bill_share_id))
    assert bill_db is not None
    assert split_db is not None
    assert split_db.status == UtilityBillSplitStatus.PAID
