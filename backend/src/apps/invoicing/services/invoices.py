from __future__ import annotations

import json
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from src.apps.availability.services.availability import calculate_duration_days
from src.apps.bookings.models.booking import Booking, BookingStatus, SecurityDeposit, SecurityDepositStatus
from src.apps.finance.api.v1 import payment as payment_api
from src.apps.finance.models.payment import PaymentProvider, PaymentStatus, PaymentTransaction
from src.apps.finance.schemas.payment import InitiatePaymentRequest, InitiatePaymentResponse
from src.apps.iam.models.user import User
from src.apps.iam.utils.identity import require_user_id
from src.apps.invoicing.models.invoice import (
    AdditionalCharge,
    AdditionalChargeStatus,
    Invoice,
    InvoiceLineItem,
    InvoiceReminder,
    InvoiceReminderStatus,
    InvoiceReminderType,
    InvoiceStatus,
    InvoiceType,
    Payment,
    PaymentReferenceType,
)


def _money(value: float) -> float:
    return round(float(value), 2)


def _invoice_outstanding(invoice: Invoice) -> float:
    if invoice.status == InvoiceStatus.WAIVED:
        return 0.0
    return _money(max(0.0, invoice.total_amount - invoice.paid_amount))


def _effective_invoice_status(invoice: Invoice, *, now: datetime | None = None) -> InvoiceStatus:
    current_time = now or datetime.now()
    if invoice.status == InvoiceStatus.WAIVED:
        return InvoiceStatus.WAIVED
    if invoice.paid_amount >= invoice.total_amount - 0.01:
        return InvoiceStatus.PAID
    if invoice.paid_amount > 0:
        if invoice.due_date < current_time.date():
            return InvoiceStatus.OVERDUE
        return InvoiceStatus.PARTIALLY_PAID
    if invoice.due_date < current_time.date():
        return InvoiceStatus.OVERDUE
    if invoice.status == InvoiceStatus.DRAFT:
        return InvoiceStatus.DRAFT
    return InvoiceStatus.SENT


def _parse_json(value: str | None) -> dict[str, object] | None:
    if value is None or not value.strip():
        return None
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {"raw": value}
    if isinstance(parsed, dict):
        return parsed
    return {"data": parsed}


def _build_reminder_schedule(due_date: datetime) -> list[tuple[InvoiceReminderType, datetime]]:
    return [
        (InvoiceReminderType.T_MINUS_7, due_date - timedelta(days=7)),
        (InvoiceReminderType.T_MINUS_3, due_date - timedelta(days=3)),
        (InvoiceReminderType.T_MINUS_1, due_date - timedelta(days=1)),
        (InvoiceReminderType.OVERDUE, due_date + timedelta(days=1)),
    ]


async def _get_security_deposit(db: AsyncSession, booking_id: int) -> SecurityDeposit | None:
    result = await db.execute(select(SecurityDeposit).where(SecurityDeposit.booking_id == booking_id))
    return result.scalars().first()


async def _get_invoice_or_404(db: AsyncSession, invoice_id: int) -> Invoice:
    invoice = await db.get(Invoice, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return invoice


async def _list_invoice_line_items(db: AsyncSession, invoice_id: int) -> list[InvoiceLineItem]:
    result = await db.execute(
        select(InvoiceLineItem)
        .where(InvoiceLineItem.invoice_id == invoice_id)
        .order_by(col(InvoiceLineItem.id))
    )
    return list(result.scalars().all())


async def _list_invoice_reminders(db: AsyncSession, invoice_id: int) -> list[InvoiceReminder]:
    result = await db.execute(
        select(InvoiceReminder)
        .where(InvoiceReminder.invoice_id == invoice_id)
        .order_by(col(InvoiceReminder.scheduled_for), col(InvoiceReminder.id))
    )
    return list(result.scalars().all())


async def _list_invoice_payments(db: AsyncSession, invoice_id: int) -> list[Payment]:
    result = await db.execute(
        select(Payment)
        .where(
            Payment.reference_type == PaymentReferenceType.INVOICE,
            Payment.reference_id == invoice_id,
        )
        .order_by(col(Payment.created_at), col(Payment.id))
    )
    return list(result.scalars().all())


async def _list_booking_invoices(
    db: AsyncSession,
    booking_id: int,
    *,
    invoice_type: InvoiceType | None = None,
) -> list[Invoice]:
    query = (
        select(Invoice)
        .where(Invoice.booking_id == booking_id)
        .order_by(col(Invoice.period_start), col(Invoice.created_at), col(Invoice.id))
    )
    if invoice_type is not None:
        query = query.where(Invoice.invoice_type == invoice_type)
    result = await db.execute(query)
    return list(result.scalars().all())


async def _list_booking_additional_charges(db: AsyncSession, booking_id: int) -> list[AdditionalCharge]:
    result = await db.execute(
        select(AdditionalCharge)
        .where(AdditionalCharge.booking_id == booking_id)
        .order_by(col(AdditionalCharge.created_at), col(AdditionalCharge.id))
    )
    return list(result.scalars().all())


async def _ensure_invoice_reminders(db: AsyncSession, invoice: Invoice) -> None:
    existing = await _list_invoice_reminders(db, invoice.id)
    if existing:
        return
    due_at = datetime.combine(invoice.due_date, datetime.min.time())
    for reminder_type, scheduled_for in _build_reminder_schedule(due_at):
        db.add(
            InvoiceReminder(
                invoice_id=invoice.id,
                reminder_type=reminder_type,
                scheduled_for=scheduled_for,
                status=InvoiceReminderStatus.SCHEDULED,
            )
        )


async def build_invoice_payload(db: AsyncSession, invoice: Invoice) -> dict[str, object]:
    line_items = await _list_invoice_line_items(db, invoice.id)
    reminders = await _list_invoice_reminders(db, invoice.id)
    payments = await _list_invoice_payments(db, invoice.id)
    effective_status = _effective_invoice_status(invoice)
    return {
        "id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "booking_id": invoice.booking_id,
        "tenant_user_id": invoice.tenant_user_id,
        "owner_user_id": invoice.owner_user_id,
        "invoice_type": invoice.invoice_type,
        "currency": invoice.currency,
        "subtotal": _money(invoice.subtotal),
        "tax_amount": _money(invoice.tax_amount),
        "total_amount": _money(invoice.total_amount),
        "paid_amount": _money(invoice.paid_amount),
        "outstanding_amount": _invoice_outstanding(invoice),
        "status": effective_status,
        "due_date": invoice.due_date,
        "period_start": invoice.period_start,
        "period_end": invoice.period_end,
        "metadata_json": invoice.metadata_json,
        "line_items": [
            {
                "id": item.id,
                "invoice_id": item.invoice_id,
                "line_item_type": item.line_item_type,
                "description": item.description,
                "amount": _money(item.amount),
                "tax_rate": _money(item.tax_rate),
                "tax_amount": _money(item.tax_amount),
                "metadata_json": item.metadata_json,
            }
            for item in line_items
        ],
        "reminders": [
            {
                "id": reminder.id,
                "invoice_id": reminder.invoice_id,
                "reminder_type": reminder.reminder_type,
                "scheduled_for": reminder.scheduled_for,
                "sent_at": reminder.sent_at,
                "status": reminder.status,
                "channel_status_json": reminder.channel_status_json,
            }
            for reminder in reminders
        ],
        "payments": [
            {
                "id": payment.id,
                "reference_type": payment.reference_type,
                "reference_id": payment.reference_id,
                "payer_user_id": payment.payer_user_id,
                "payment_method": payment.payment_method,
                "status": payment.status,
                "amount": _money(payment.amount),
                "currency": payment.currency,
                "gateway_ref": payment.gateway_ref,
                "gateway_response_json": payment.gateway_response_json,
                "is_offline": payment.is_offline,
                "created_at": payment.created_at,
                "confirmed_at": payment.confirmed_at,
            }
            for payment in payments
        ],
        "created_at": invoice.created_at,
        "paid_at": invoice.paid_at,
    }


def _user_can_access_invoice(current_user: User, invoice: Invoice) -> bool:
    user_id = require_user_id(current_user.id)
    if current_user.is_superuser:
        return True
    return invoice.tenant_user_id == user_id or invoice.owner_user_id == user_id


def _user_can_manage_invoice(current_user: User, invoice: Invoice) -> bool:
    user_id = require_user_id(current_user.id)
    return current_user.is_superuser or invoice.owner_user_id == user_id


async def get_accessible_invoice_or_404(db: AsyncSession, invoice_id: int, current_user: User) -> Invoice:
    invoice = await _get_invoice_or_404(db, invoice_id)
    if not _user_can_access_invoice(current_user, invoice):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to access this invoice")
    return invoice


async def list_invoices(
    db: AsyncSession,
    current_user: User,
    *,
    page: int,
    per_page: int,
    status_filter: InvoiceStatus | None = None,
) -> dict[str, object]:
    user_id = require_user_id(current_user.id)
    query = select(Invoice).order_by(col(Invoice.due_date).desc(), col(Invoice.id).desc())
    if not current_user.is_superuser:
        query = query.where(
            or_(Invoice.tenant_user_id == user_id, Invoice.owner_user_id == user_id)
        )
    result = await db.execute(query)
    invoices = list(result.scalars().all())
    if status_filter is not None:
        invoices = [
            invoice
            for invoice in invoices
            if _effective_invoice_status(invoice) == status_filter
        ]
    total = len(invoices)
    start_index = (page - 1) * per_page
    page_items = invoices[start_index : start_index + per_page]
    return {
        "items": [await build_invoice_payload(db, invoice) for invoice in page_items],
        "total": total,
        "page": page,
        "per_page": per_page,
        "has_more": start_index + len(page_items) < total,
    }


async def get_invoice_detail(db: AsyncSession, invoice_id: int, current_user: User) -> dict[str, object]:
    invoice = await get_accessible_invoice_or_404(db, invoice_id, current_user)
    return await build_invoice_payload(db, invoice)


async def _ensure_invoice_line_item(
    db: AsyncSession,
    invoice: Invoice,
    *,
    line_item_type: str,
    description: str,
    amount: float,
) -> None:
    items = await _list_invoice_line_items(db, invoice.id)
    if items:
        primary_item = items[0]
        primary_item.line_item_type = line_item_type
        primary_item.description = description
        primary_item.amount = _money(amount)
        primary_item.tax_rate = 0.0
        primary_item.tax_amount = 0.0
        db.add(primary_item)
        return
    db.add(
        InvoiceLineItem(
            invoice_id=invoice.id,
            line_item_type=line_item_type,
            description=description,
            amount=_money(amount),
            tax_rate=0.0,
            tax_amount=0.0,
        )
    )


async def ensure_booking_rent_schedule(db: AsyncSession, booking: Booking) -> list[Invoice]:
    if booking.status in {BookingStatus.PENDING, BookingStatus.DECLINED, BookingStatus.CANCELLED}:
        return []

    existing = {
        invoice.invoice_number: invoice
        for invoice in await _list_booking_invoices(db, booking.id, invoice_type=InvoiceType.RENT)
    }
    invoices: list[Invoice] = list(existing.values())
    duration_days = max(1, calculate_duration_days(booking.rental_start_at, booking.rental_end_at))
    per_day_fee = booking.total_fee / duration_days
    cursor = booking.rental_start_at
    remaining_total = _money(booking.total_fee)
    period_index = 1

    while cursor < booking.rental_end_at:
        period_end = min(cursor + timedelta(days=30), booking.rental_end_at)
        period_days = max(1, calculate_duration_days(cursor, period_end))
        amount = remaining_total if period_end == booking.rental_end_at else _money(per_day_fee * period_days)
        remaining_total = _money(remaining_total - amount)
        invoice_number = f"INV-{booking.id:05d}-{period_index:02d}"
        invoice = existing.get(invoice_number)
        if invoice is None:
            invoice = Invoice(
                invoice_number=invoice_number,
                booking_id=booking.id,
                tenant_user_id=booking.tenant_user_id,
                owner_user_id=booking.owner_user_id,
                invoice_type=InvoiceType.RENT,
                currency=booking.currency,
                subtotal=amount,
                tax_amount=0.0,
                total_amount=amount,
                paid_amount=0.0,
                status=InvoiceStatus.SENT,
                due_date=cursor.date(),
                period_start=cursor.date(),
                period_end=period_end.date(),
                metadata_json={"period_index": period_index},
            )
            db.add(invoice)
            await db.flush()
            existing[invoice_number] = invoice
            invoices.append(invoice)
        else:
            invoice.subtotal = _money(amount)
            invoice.total_amount = _money(amount)
            invoice.period_start = cursor.date()
            invoice.period_end = period_end.date()
            invoice.due_date = cursor.date()
            invoice.status = _effective_invoice_status(invoice)
            db.add(invoice)

        await _ensure_invoice_line_item(
            db,
            invoice,
            line_item_type="rent",
            description=f"Rent for {invoice.period_start.isoformat()} to {invoice.period_end.isoformat()}",
            amount=amount,
        )
        await _ensure_invoice_reminders(db, invoice)
        cursor = period_end
        period_index += 1

    await db.flush()
    return sorted(invoices, key=lambda item: (item.period_start or item.due_date, item.id or 0))


async def get_rent_ledger(db: AsyncSession, booking_id: int, current_user: User) -> dict[str, object]:
    from src.apps.bookings.services.bookings import get_accessible_booking_for_user

    booking = await get_accessible_booking_for_user(db, booking_id, current_user)
    invoices = await ensure_booking_rent_schedule(db, booking)
    charges = await _list_booking_additional_charges(db, booking.id)
    entries = []
    total_amount = 0.0
    paid_amount = 0.0
    for invoice in invoices:
        effective_status = _effective_invoice_status(invoice)
        outstanding_amount = _invoice_outstanding(invoice)
        total_amount += invoice.total_amount
        paid_amount += invoice.paid_amount
        entries.append(
            {
                "period_start": invoice.period_start or invoice.due_date,
                "period_end": invoice.period_end or invoice.due_date,
                "amount_due": _money(invoice.total_amount),
                "invoice_id": invoice.id,
                "invoice_status": effective_status,
                "due_date": invoice.due_date,
                "paid_amount": _money(invoice.paid_amount),
                "outstanding_amount": outstanding_amount,
            }
        )

    await db.commit()
    return {
        "booking_id": booking.id,
        "currency": booking.currency,
        "entries": entries,
        "additional_charges": [
            {
                "id": charge.id,
                "booking_id": charge.booking_id,
                "invoice_id": charge.invoice_id,
                "charge_type": charge.charge_type,
                "description": charge.description,
                "amount": _money(charge.amount),
                "resolved_amount": _money(charge.resolved_amount) if charge.resolved_amount is not None else None,
                "evidence_url": charge.evidence_url,
                "status": charge.status,
                "dispute_reason": charge.dispute_reason,
                "resolution_notes": charge.resolution_notes,
                "created_at": charge.created_at,
                "resolved_at": charge.resolved_at,
            }
            for charge in charges
        ],
        "total_amount": _money(total_amount),
        "paid_amount": _money(paid_amount),
        "outstanding_amount": _money(total_amount - paid_amount),
    }


async def _get_additional_charge_or_404(db: AsyncSession, charge_id: int) -> AdditionalCharge:
    charge = await db.get(AdditionalCharge, charge_id)
    if charge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Additional charge not found")
    return charge


def _final_charge_amount(charge: AdditionalCharge) -> float:
    if charge.resolved_amount is not None:
        return _money(charge.resolved_amount)
    return _money(charge.amount)


async def sync_booking_closeout(db: AsyncSession, booking: Booking) -> None:
    if booking.actual_return_at is None:
        return

    now = datetime.now()
    charges = await _list_booking_additional_charges(db, booking.id)
    deposit = await _get_security_deposit(db, booking.id)
    if any(charge.status == AdditionalChargeStatus.DISPUTED for charge in charges):
        if deposit is not None and deposit.status != SecurityDepositStatus.DISPUTED:
            deposit.status = SecurityDepositStatus.DISPUTED
            deposit.settled_at = None
            db.add(deposit)
        booking.status = BookingStatus.PENDING_CLOSURE
        db.add(booking)
        return

    accepted_charges = [
        charge
        for charge in charges
        if charge.status in {AdditionalChargeStatus.ACCEPTED, AdditionalChargeStatus.PARTIALLY_ACCEPTED}
    ]
    deposit_budget = _money(deposit.amount) if deposit is not None else 0.0
    remaining_deduction = deposit_budget
    for charge in accepted_charges:
        if charge.invoice_id is None or remaining_deduction <= 0:
            continue
        invoice = await _get_invoice_or_404(db, charge.invoice_id)
        outstanding = _invoice_outstanding(invoice)
        if outstanding <= 0:
            continue
        applied_amount = min(remaining_deduction, outstanding)
        invoice.paid_amount = _money(invoice.paid_amount + applied_amount)
        remaining_deduction = _money(remaining_deduction - applied_amount)
        if _invoice_outstanding(invoice) <= 0.01:
            invoice.status = InvoiceStatus.PAID
            invoice.paid_at = now
            charge.status = AdditionalChargeStatus.PAID
            charge.resolved_at = charge.resolved_at or now
            db.add(charge)
        else:
            invoice.status = InvoiceStatus.PARTIALLY_PAID
        db.add(invoice)

    if deposit is not None:
        accepted_total = _money(sum(_final_charge_amount(charge) for charge in accepted_charges))
        deduction_total = min(_money(deposit.amount), accepted_total)
        refund_amount = _money(max(0.0, deposit.amount - deduction_total))
        deposit.deduction_total = _money(deduction_total)
        deposit.refund_amount = refund_amount
        deposit.settled_at = now
        if deduction_total <= 0.01:
            deposit.status = SecurityDepositStatus.FULLY_REFUNDED
        elif refund_amount <= 0.01:
            deposit.status = SecurityDepositStatus.FULLY_DEDUCTED
        else:
            deposit.status = SecurityDepositStatus.PARTIALLY_REFUNDED
        db.add(deposit)

    remaining_invoices = [
        invoice
        for invoice in await _list_booking_invoices(db, booking.id)
        if _effective_invoice_status(invoice, now=now) not in {InvoiceStatus.PAID, InvoiceStatus.WAIVED}
    ]
    previous_status = booking.status
    if remaining_invoices:
        booking.status = BookingStatus.PENDING_CLOSURE
    else:
        booking.status = BookingStatus.CLOSED
        if deposit is not None:
            booking.refund_amount = _money(deposit.refund_amount)
    booking.updated_at = now
    db.add(booking)

    if previous_status != BookingStatus.CLOSED and booking.status == BookingStatus.CLOSED:
        from src.apps.bookings.services.bookings import emit_booking_event

        await emit_booking_event(
            db,
            booking.id,
            "booking.closed",
            "Booking closeout completed and the final balance was settled.",
            actor_user_id=None,
            metadata={"actual_return_at": booking.actual_return_at.isoformat()},
        )


async def create_additional_charge(
    db: AsyncSession,
    booking_id: int,
    current_user: User,
    *,
    charge_type: str,
    description: str,
    amount: float,
    evidence_url: str,
) -> dict[str, object]:
    from src.apps.bookings.services.bookings import emit_booking_event, get_manageable_booking_for_user

    booking = await get_manageable_booking_for_user(db, booking_id, current_user)
    if booking.actual_return_at is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Additional charges can only be raised after the return is recorded",
        )
    if amount <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="amount must be positive")

    now = datetime.now()
    invoice = Invoice(
        invoice_number="",
        booking_id=booking.id,
        tenant_user_id=booking.tenant_user_id,
        owner_user_id=booking.owner_user_id,
        invoice_type=InvoiceType.ADDITIONAL_CHARGE,
        currency=booking.currency,
        subtotal=_money(amount),
        tax_amount=0.0,
        total_amount=_money(amount),
        paid_amount=0.0,
        status=InvoiceStatus.SENT,
        due_date=(now + timedelta(days=7)).date(),
        metadata_json={"charge_type": charge_type},
    )
    db.add(invoice)
    await db.flush()
    invoice.invoice_number = f"CHR-{booking.id:05d}-{invoice.id:03d}"
    db.add(invoice)
    await _ensure_invoice_line_item(
        db,
        invoice,
        line_item_type=charge_type,
        description=description,
        amount=amount,
    )
    await _ensure_invoice_reminders(db, invoice)

    charge = AdditionalCharge(
        booking_id=booking.id,
        invoice_id=invoice.id,
        charge_type=charge_type.strip() or "damage",
        description=description.strip(),
        amount=_money(amount),
        evidence_url=evidence_url.strip(),
        status=AdditionalChargeStatus.RAISED,
    )
    db.add(charge)
    booking.status = BookingStatus.PENDING_CLOSURE
    booking.updated_at = now
    db.add(booking)
    await emit_booking_event(
        db,
        booking.id,
        "charge.raised",
        f"Additional charge raised: {description.strip()}",
        actor_user_id=require_user_id(current_user.id),
        metadata={"amount": _money(amount), "invoice_number": invoice.invoice_number},
    )
    await db.commit()
    await db.refresh(charge)
    return {
        "id": charge.id,
        "booking_id": charge.booking_id,
        "invoice_id": charge.invoice_id,
        "charge_type": charge.charge_type,
        "description": charge.description,
        "amount": _money(charge.amount),
        "resolved_amount": charge.resolved_amount,
        "evidence_url": charge.evidence_url,
        "status": charge.status,
        "dispute_reason": charge.dispute_reason,
        "resolution_notes": charge.resolution_notes,
        "created_at": charge.created_at,
        "resolved_at": charge.resolved_at,
    }


async def dispute_additional_charge(
    db: AsyncSession,
    charge_id: int,
    current_user: User,
    *,
    reason: str,
) -> dict[str, object]:
    from src.apps.bookings.services.bookings import emit_booking_event, get_accessible_booking_for_user

    charge = await _get_additional_charge_or_404(db, charge_id)
    booking = await get_accessible_booking_for_user(db, charge.booking_id, current_user)
    user_id = require_user_id(current_user.id)
    if not current_user.is_superuser and booking.tenant_user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the tenant can dispute this charge")
    if charge.status in {AdditionalChargeStatus.PAID, AdditionalChargeStatus.WAIVED}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This charge can no longer be disputed",
        )

    charge.status = AdditionalChargeStatus.DISPUTED
    charge.dispute_reason = reason.strip()
    db.add(charge)
    deposit = await _get_security_deposit(db, booking.id)
    if deposit is not None:
        deposit.status = SecurityDepositStatus.DISPUTED
        deposit.settled_at = None
        db.add(deposit)
    booking.status = BookingStatus.PENDING_CLOSURE
    db.add(booking)
    await emit_booking_event(
        db,
        booking.id,
        "charge.disputed",
        "Tenant disputed an additional charge.",
        actor_user_id=user_id,
        metadata={"charge_id": charge.id},
    )
    await db.commit()
    return {
        "id": charge.id,
        "booking_id": charge.booking_id,
        "invoice_id": charge.invoice_id,
        "charge_type": charge.charge_type,
        "description": charge.description,
        "amount": _money(charge.amount),
        "resolved_amount": charge.resolved_amount,
        "evidence_url": charge.evidence_url,
        "status": charge.status,
        "dispute_reason": charge.dispute_reason,
        "resolution_notes": charge.resolution_notes,
        "created_at": charge.created_at,
        "resolved_at": charge.resolved_at,
    }


async def resolve_additional_charge(
    db: AsyncSession,
    charge_id: int,
    current_user: User,
    *,
    outcome: AdditionalChargeStatus,
    resolved_amount: float | None,
    resolution_notes: str,
) -> dict[str, object]:
    from src.apps.bookings.services.bookings import emit_booking_event, get_manageable_booking_for_user

    charge = await _get_additional_charge_or_404(db, charge_id)
    booking = await get_manageable_booking_for_user(db, charge.booking_id, current_user)
    if outcome not in {
        AdditionalChargeStatus.ACCEPTED,
        AdditionalChargeStatus.PARTIALLY_ACCEPTED,
        AdditionalChargeStatus.WAIVED,
    }:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported charge outcome")
    invoice = await _get_invoice_or_404(db, charge.invoice_id) if charge.invoice_id is not None else None
    now = datetime.now()

    charge.resolution_notes = resolution_notes.strip()
    charge.resolved_at = now
    if outcome == AdditionalChargeStatus.WAIVED:
        charge.status = AdditionalChargeStatus.WAIVED
        charge.resolved_amount = 0.0
        if invoice is not None:
            invoice.status = InvoiceStatus.WAIVED
            invoice.paid_at = now
            db.add(invoice)
    elif outcome == AdditionalChargeStatus.ACCEPTED:
        charge.status = AdditionalChargeStatus.ACCEPTED
        charge.resolved_amount = _money(charge.amount)
        if invoice is not None and invoice.status == InvoiceStatus.DRAFT:
            invoice.status = InvoiceStatus.SENT
            db.add(invoice)
    else:
        if resolved_amount is None or resolved_amount <= 0 or resolved_amount > charge.amount:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="resolved_amount must be between 0 and the original charge amount",
            )
        charge.status = AdditionalChargeStatus.PARTIALLY_ACCEPTED
        charge.resolved_amount = _money(resolved_amount)
        if invoice is not None:
            invoice.subtotal = _money(resolved_amount)
            invoice.total_amount = _money(resolved_amount)
            invoice.status = _effective_invoice_status(invoice, now=now)
            db.add(invoice)

    db.add(charge)
    await sync_booking_closeout(db, booking)
    await emit_booking_event(
        db,
        booking.id,
        "charge.resolved",
        f"Additional charge resolved as {charge.status.value}.",
        actor_user_id=require_user_id(current_user.id),
        metadata={"charge_id": charge.id, "resolved_amount": charge.resolved_amount},
    )
    await db.commit()
    await db.refresh(charge)
    return {
        "id": charge.id,
        "booking_id": charge.booking_id,
        "invoice_id": charge.invoice_id,
        "charge_type": charge.charge_type,
        "description": charge.description,
        "amount": _money(charge.amount),
        "resolved_amount": _money(charge.resolved_amount) if charge.resolved_amount is not None else None,
        "evidence_url": charge.evidence_url,
        "status": charge.status,
        "dispute_reason": charge.dispute_reason,
        "resolution_notes": charge.resolution_notes,
        "created_at": charge.created_at,
        "resolved_at": charge.resolved_at,
    }


def _provider_amount(provider: PaymentProvider, amount: float) -> int:
    normalized = _money(amount)
    if provider == PaymentProvider.KHALTI:
        return int(round(normalized * 100))
    return int(round(normalized))


async def initiate_invoice_payment(
    db: AsyncSession,
    invoice_id: int,
    current_user: User,
    data,
    *,
    allow_partial: bool,
) -> InitiatePaymentResponse:
    invoice = await get_accessible_invoice_or_404(db, invoice_id, current_user)
    user_id = require_user_id(current_user.id)
    if not current_user.is_superuser and invoice.tenant_user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the tenant can pay this invoice")

    outstanding_amount = _invoice_outstanding(invoice)
    if outstanding_amount <= 0.01 or _effective_invoice_status(invoice) in {InvoiceStatus.PAID, InvoiceStatus.WAIVED}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invoice is already settled")

    requested_amount = _money(data.amount if data.amount is not None else outstanding_amount)
    if requested_amount <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="amount must be positive")
    if requested_amount > outstanding_amount + 0.01:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="amount may not exceed the outstanding invoice balance",
        )
    if not allow_partial and requested_amount < outstanding_amount - 0.01:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Use the partial payment endpoint for partial settlements",
        )

    payment = Payment(
        reference_type=PaymentReferenceType.INVOICE,
        reference_id=invoice.id,
        payer_user_id=user_id,
        payment_method=data.provider,
        status=PaymentStatus.PENDING,
        amount=requested_amount,
        currency=invoice.currency,
        gateway_ref="",
        is_offline=False,
    )
    db.add(payment)
    await db.flush()
    purchase_order_id = f"INV-{invoice.invoice_number}-PAY-{payment.id}"
    provider_service = payment_api._get_provider(data.provider)
    response = await provider_service.initiate_payment(
        InitiatePaymentRequest(
            provider=data.provider,
            amount=_provider_amount(data.provider, requested_amount),
            purchase_order_id=purchase_order_id,
            purchase_order_name=f"Invoice {invoice.invoice_number}",
            return_url=data.return_url,
            website_url=data.website_url or data.return_url,
            customer_name=data.customer_name or current_user.username,
            customer_email=data.customer_email or current_user.email,
            customer_phone=data.customer_phone or None,
        ),
        db,
    )
    payment.status = PaymentStatus.INITIATED
    payment.gateway_ref = str(response.transaction_id)
    payment.gateway_response_json = {
        "purchase_order_id": purchase_order_id,
        "provider_pidx": response.provider_pidx,
        "payment_url": response.payment_url,
        "extra": response.extra,
    }
    db.add(payment)
    await db.commit()
    return response


async def reconcile_payment_transaction(db: AsyncSession, transaction_id: int) -> None:
    tx = await db.get(PaymentTransaction, transaction_id)
    if tx is None:
        return

    result = await db.execute(select(Payment).where(Payment.gateway_ref == str(transaction_id)))
    payment = result.scalars().first()
    if payment is None:
        return

    previous_status = payment.status
    payment.status = tx.status
    payment.gateway_response_json = _parse_json(tx.extra_data)
    if tx.status in {PaymentStatus.COMPLETED, PaymentStatus.REFUNDED}:
        payment.confirmed_at = datetime.now()
    db.add(payment)

    if payment.reference_type != PaymentReferenceType.INVOICE:
        await db.commit()
        return

    invoice = await _get_invoice_or_404(db, payment.reference_id)
    now = datetime.now()
    if tx.status == PaymentStatus.COMPLETED and previous_status != PaymentStatus.COMPLETED:
        invoice.paid_amount = _money(min(invoice.total_amount, invoice.paid_amount + payment.amount))
        if _invoice_outstanding(invoice) <= 0.01:
            invoice.status = InvoiceStatus.PAID
            invoice.paid_at = now
        else:
            invoice.status = InvoiceStatus.PARTIALLY_PAID
        db.add(invoice)
    elif tx.status == PaymentStatus.REFUNDED and previous_status != PaymentStatus.REFUNDED:
        invoice.paid_amount = _money(max(0.0, invoice.paid_amount - payment.amount))
        invoice.status = _effective_invoice_status(invoice, now=now)
        invoice.paid_at = None if invoice.paid_amount < invoice.total_amount else invoice.paid_at
        db.add(invoice)

    if invoice.invoice_type == InvoiceType.ADDITIONAL_CHARGE:
        result = await db.execute(select(AdditionalCharge).where(AdditionalCharge.invoice_id == invoice.id))
        charge = result.scalars().first()
        if charge is not None and invoice.status == InvoiceStatus.PAID:
            charge.status = AdditionalChargeStatus.PAID
            charge.resolved_at = charge.resolved_at or now
            db.add(charge)

    if invoice.invoice_type == InvoiceType.UTILITY_BILL_SHARE:
        from src.apps.utility_billing.services.utility_bills import sync_split_from_invoice

        await sync_split_from_invoice(db, invoice)

    if invoice.booking_id is not None:
        booking = await db.get(Booking, invoice.booking_id)
        if booking is not None and booking.actual_return_at is not None:
            await sync_booking_closeout(db, booking)
    await db.commit()


async def get_invoice_receipt_text(db: AsyncSession, invoice_id: int, current_user: User) -> str:
    invoice = await get_accessible_invoice_or_404(db, invoice_id, current_user)
    payments = await _list_invoice_payments(db, invoice.id)
    lines = await _list_invoice_line_items(db, invoice.id)
    content = [
        "MEROGHAR PAYMENT RECEIPT",
        "",
        f"Invoice number: {invoice.invoice_number}",
        f"Invoice type: {invoice.invoice_type.value}",
        f"Currency: {invoice.currency}",
        f"Status: {_effective_invoice_status(invoice).value}",
        f"Due date: {invoice.due_date.isoformat()}",
        f"Total amount: {invoice.total_amount:.2f}",
        f"Paid amount: {invoice.paid_amount:.2f}",
        "",
        "Line items:",
    ]
    for item in lines:
        content.append(f"- {item.description}: {item.amount:.2f}")
    content.extend(["", "Payments:"])
    if payments:
        for payment in payments:
            content.append(
                f"- {payment.created_at.isoformat()} | {payment.payment_method.value} | "
                f"{payment.amount:.2f} {payment.currency} | {payment.status.value}"
            )
    else:
        content.append("- No completed payments recorded yet.")
    return "\n".join(content)
