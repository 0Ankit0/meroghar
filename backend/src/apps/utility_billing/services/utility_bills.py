from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from src.apps.bookings.models.booking import Booking, BookingStatus
from src.apps.core.storage import save_media_bytes
from src.apps.iam.models.user import User
from src.apps.iam.utils.identity import require_user_id
from src.apps.invoicing.models.invoice import Invoice, InvoiceStatus, InvoiceType
from src.apps.invoicing.services.invoices import initiate_invoice_payment
from src.apps.listings.services.properties import get_property_or_404, require_property_owner
from src.apps.utility_billing.models.utility_bill import (
    UtilityBill,
    UtilityBillAttachment,
    UtilityBillDispute,
    UtilityBillDisputeStatus,
    UtilityBillSplit,
    UtilityBillSplitMethod,
    UtilityBillSplitStatus,
    UtilityBillStatus,
)


def _money(value: float) -> float:
    return round(float(value), 2)


async def _get_utility_bill_or_404(db: AsyncSession, bill_id: int) -> UtilityBill:
    bill = await db.get(UtilityBill, bill_id)
    if bill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utility bill not found")
    return bill


async def _list_bill_attachments(db: AsyncSession, bill_id: int) -> list[UtilityBillAttachment]:
    result = await db.execute(
        select(UtilityBillAttachment)
        .where(UtilityBillAttachment.utility_bill_id == bill_id)
        .order_by(col(UtilityBillAttachment.uploaded_at), col(UtilityBillAttachment.id))
    )
    return list(result.scalars().all())


async def _list_bill_splits(db: AsyncSession, bill_id: int) -> list[UtilityBillSplit]:
    result = await db.execute(
        select(UtilityBillSplit)
        .where(UtilityBillSplit.utility_bill_id == bill_id)
        .order_by(col(UtilityBillSplit.id))
    )
    return list(result.scalars().all())


async def _list_split_disputes(db: AsyncSession, split_id: int) -> list[UtilityBillDispute]:
    result = await db.execute(
        select(UtilityBillDispute)
        .where(UtilityBillDispute.utility_bill_split_id == split_id)
        .order_by(col(UtilityBillDispute.opened_at), col(UtilityBillDispute.id))
    )
    return list(result.scalars().all())


def _split_outstanding(split: UtilityBillSplit) -> float:
    if split.status == UtilityBillSplitStatus.WAIVED:
        return 0.0
    return _money(max(0.0, split.assigned_amount - split.paid_amount))


async def _sync_bill_status(db: AsyncSession, bill: UtilityBill) -> None:
    splits = await _list_bill_splits(db, bill.id)
    if not splits:
        bill.status = UtilityBillStatus.DRAFT
        db.add(bill)
        return

    if all(split.status in {UtilityBillSplitStatus.PAID, UtilityBillSplitStatus.WAIVED} for split in splits):
        bill.status = UtilityBillStatus.SETTLED
    elif any(split.paid_amount > 0 for split in splits):
        bill.status = UtilityBillStatus.PARTIALLY_PAID
    elif bill.published_at is not None:
        bill.status = UtilityBillStatus.PUBLISHED
    else:
        bill.status = UtilityBillStatus.DRAFT
    db.add(bill)


async def _build_bill_payload(db: AsyncSession, bill: UtilityBill) -> dict[str, object]:
    attachments = await _list_bill_attachments(db, bill.id)
    splits = await _list_bill_splits(db, bill.id)
    await _sync_bill_status(db, bill)
    return {
        "id": bill.id,
        "property_id": bill.property_id,
        "created_by_user_id": bill.created_by_user_id,
        "bill_type": bill.bill_type,
        "billing_period_label": bill.billing_period_label,
        "period_start": bill.period_start,
        "period_end": bill.period_end,
        "due_date": bill.due_date,
        "total_amount": _money(bill.total_amount),
        "owner_subsidy_amount": _money(bill.owner_subsidy_amount),
        "payable_amount": _money(max(0.0, bill.total_amount - bill.owner_subsidy_amount)),
        "status": bill.status,
        "notes": bill.notes,
        "attachments": [
            {
                "id": attachment.id,
                "utility_bill_id": attachment.utility_bill_id,
                "file_url": attachment.file_url,
                "file_type": attachment.file_type,
                "checksum": attachment.checksum,
                "uploaded_at": attachment.uploaded_at,
            }
            for attachment in attachments
        ],
        "splits": [
            {
                "id": split.id,
                "utility_bill_id": split.utility_bill_id,
                "tenant_user_id": split.tenant_user_id,
                "invoice_id": split.invoice_id,
                "split_method": split.split_method,
                "split_percent": split.split_percent,
                "assigned_amount": _money(split.assigned_amount),
                "paid_amount": _money(split.paid_amount),
                "outstanding_amount": _split_outstanding(split),
                "status": split.status,
                "due_at": split.due_at,
                "paid_at": split.paid_at,
            }
            for split in splits
        ],
        "created_at": bill.created_at,
        "published_at": bill.published_at,
    }


async def list_property_utility_bills(
    db: AsyncSession,
    property_id: int,
    current_user: User,
    *,
    page: int,
    per_page: int,
) -> dict[str, object]:
    user_id = require_user_id(current_user.id)
    property_obj = await require_property_owner(db, property_id, user_id) if not current_user.is_superuser else await get_property_or_404(db, property_id)
    result = await db.execute(
        select(UtilityBill)
        .where(UtilityBill.property_id == property_obj.id)
        .order_by(col(UtilityBill.period_start).desc(), col(UtilityBill.id).desc())
    )
    bills = list(result.scalars().all())
    total = len(bills)
    start_index = (page - 1) * per_page
    page_items = bills[start_index : start_index + per_page]
    return {
        "items": [await _build_bill_payload(db, bill) for bill in page_items],
        "total": total,
        "page": page,
        "per_page": per_page,
        "has_more": start_index + len(page_items) < total,
    }


async def create_utility_bill(
    db: AsyncSession,
    property_id: int,
    current_user: User,
    *,
    bill_type,
    billing_period_label: str,
    period_start,
    period_end,
    due_date,
    total_amount: float,
    owner_subsidy_amount: float,
    notes: str,
) -> dict[str, object]:
    user_id = require_user_id(current_user.id)
    property_obj = await require_property_owner(db, property_id, user_id) if not current_user.is_superuser else await get_property_or_404(db, property_id)
    if period_end < period_start:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="period_end must be on or after period_start")
    if due_date < period_end:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="due_date must be on or after period_end")
    if total_amount <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="total_amount must be positive")
    if owner_subsidy_amount < 0 or owner_subsidy_amount > total_amount:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="owner_subsidy_amount must be between 0 and total_amount",
        )

    bill = UtilityBill(
        property_id=property_obj.id,
        created_by_user_id=user_id,
        bill_type=bill_type,
        billing_period_label=billing_period_label.strip(),
        period_start=period_start,
        period_end=period_end,
        due_date=due_date,
        total_amount=_money(total_amount),
        owner_subsidy_amount=_money(owner_subsidy_amount),
        status=UtilityBillStatus.DRAFT,
        notes=notes.strip(),
    )
    db.add(bill)
    await db.commit()
    await db.refresh(bill)
    return await _build_bill_payload(db, bill)


async def upload_utility_bill_attachment(
    db: AsyncSession,
    bill_id: int,
    current_user: User,
    file: UploadFile,
) -> dict[str, object]:
    user_id = require_user_id(current_user.id)
    bill = await _get_utility_bill_or_404(db, bill_id)
    if not current_user.is_superuser:
        await require_property_owner(db, bill.property_id, user_id)

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Attachment file must not be empty")
    checksum = hashlib.sha256(file_bytes).hexdigest()
    filename = Path(file.filename or f"bill-{bill.id}-attachment").name
    relative_path = f"utility-bills/{bill.id}/{checksum[:12]}-{filename}"
    file_url = save_media_bytes(relative_path, file_bytes, content_type=file.content_type or "application/octet-stream")
    attachment = UtilityBillAttachment(
        utility_bill_id=bill.id,
        file_url=file_url,
        file_type=file.content_type or "application/octet-stream",
        checksum=checksum,
    )
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)
    return {
        "id": attachment.id,
        "utility_bill_id": attachment.utility_bill_id,
        "file_url": attachment.file_url,
        "file_type": attachment.file_type,
        "checksum": attachment.checksum,
        "uploaded_at": attachment.uploaded_at,
    }


async def _property_tenants_for_period(
    db: AsyncSession,
    property_id: int,
    *,
    period_start,
    period_end,
) -> list[int]:
    result = await db.execute(
        select(Booking)
        .where(
            Booking.property_id == property_id,
            Booking.status.in_(
                [
                    BookingStatus.CONFIRMED,
                    BookingStatus.ACTIVE,
                    BookingStatus.PENDING_CLOSURE,
                    BookingStatus.CLOSED,
                ]
            ),
            Booking.rental_start_at < datetime.combine(period_end, datetime.max.time()),
            Booking.rental_end_at > datetime.combine(period_start, datetime.min.time()),
        )
        .order_by(col(Booking.tenant_user_id))
    )
    bookings = list(result.scalars().all())
    return sorted({booking.tenant_user_id for booking in bookings})


async def configure_utility_bill_splits(
    db: AsyncSession,
    bill_id: int,
    current_user: User,
    *,
    default_method,
    splits,
) -> dict[str, object]:
    user_id = require_user_id(current_user.id)
    bill = await _get_utility_bill_or_404(db, bill_id)
    if not current_user.is_superuser:
        await require_property_owner(db, bill.property_id, user_id)
    if bill.published_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Published bills cannot be reconfigured")

    payable_total = _money(max(0.0, bill.total_amount - bill.owner_subsidy_amount))
    computed_splits: list[dict[str, object]] = []
    overlapping_tenant_ids = set(
        await _property_tenants_for_period(
            db,
            bill.property_id,
            period_start=bill.period_start,
            period_end=bill.period_end,
        )
    )
    if splits:
        seen_tenant_ids: set[int] = set()
        equal_items: list[dict[str, object]] = []
        fixed_or_percentage_total = 0.0
        single_count = 0
        for split in splits:
            if split.tenant_user_id in seen_tenant_ids:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Duplicate tenant bill-share entries are not allowed")
            seen_tenant_ids.add(split.tenant_user_id)
            if split.tenant_user_id not in overlapping_tenant_ids:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Each bill share must be assigned to a tenant with a booking in the billing period",
                )
            assigned_amount = split.assigned_amount
            if split.split_method == UtilityBillSplitMethod.PERCENTAGE:
                if split.split_percent is None or split.split_percent <= 0:
                    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Percentage splits require split_percent")
                assigned_amount = _money(payable_total * (split.split_percent / 100))
                fixed_or_percentage_total = _money(fixed_or_percentage_total + assigned_amount)
            elif split.split_method == UtilityBillSplitMethod.SINGLE:
                single_count += 1
                assigned_amount = payable_total
            elif split.split_method == UtilityBillSplitMethod.FIXED:
                if assigned_amount is None or assigned_amount <= 0:
                    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Fixed splits require assigned_amount")
                fixed_or_percentage_total = _money(fixed_or_percentage_total + assigned_amount)
            elif split.split_method == UtilityBillSplitMethod.EQUAL:
                assigned_amount = None
            computed_splits.append(
                {
                    "tenant_user_id": split.tenant_user_id,
                    "split_method": split.split_method,
                    "split_percent": split.split_percent,
                    "assigned_amount": assigned_amount,
                }
            )
            if split.split_method == UtilityBillSplitMethod.EQUAL:
                equal_items.append(computed_splits[-1])
        if single_count:
            if len(computed_splits) != 1:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Single bill splits cannot be combined with any other split entries",
                )
        elif fixed_or_percentage_total > payable_total + 0.05:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Configured fixed and percentage shares exceed the payable utility amount",
            )
        remaining = _money(payable_total - fixed_or_percentage_total)
        if equal_items:
            equal_amount = _money(remaining / len(equal_items))
            for index, item in enumerate(equal_items, start=1):
                amount = remaining if index == len(equal_items) else equal_amount
                item["assigned_amount"] = _money(amount)
                remaining = _money(remaining - amount)
        elif abs(remaining) > 0.05:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Configured bill-share totals must equal the payable utility amount",
            )
    else:
        tenant_ids = sorted(overlapping_tenant_ids)
        if not tenant_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No tenant bookings overlap the billing period",
            )
        method = default_method or UtilityBillSplitMethod.EQUAL
        if method not in {UtilityBillSplitMethod.EQUAL, UtilityBillSplitMethod.SINGLE}:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="default_method only supports equal or single auto-generated bill shares",
            )
        if method == UtilityBillSplitMethod.SINGLE and len(tenant_ids) != 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Single splits require exactly one tenant for the billing period",
            )
        if method == UtilityBillSplitMethod.SINGLE:
            computed_splits = [
                {
                    "tenant_user_id": tenant_ids[0],
                    "split_method": method,
                    "split_percent": None,
                    "assigned_amount": payable_total,
                }
            ]
        else:
            equal_amount = _money(payable_total / len(tenant_ids))
            remaining = payable_total
            for index, tenant_user_id in enumerate(tenant_ids, start=1):
                amount = remaining if index == len(tenant_ids) else equal_amount
                computed_splits.append(
                    {
                        "tenant_user_id": tenant_user_id,
                        "split_method": method,
                        "split_percent": None,
                        "assigned_amount": _money(amount),
                    }
                )
                remaining = _money(remaining - amount)

    total_assigned = _money(sum(float(item["assigned_amount"]) for item in computed_splits))
    if abs(total_assigned - payable_total) > 0.05:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Configured bill-share totals must equal the payable utility amount",
        )

    await db.execute(delete(UtilityBillSplit).where(UtilityBillSplit.utility_bill_id == bill.id))
    due_at = datetime.combine(bill.due_date, datetime.min.time())
    for item in computed_splits:
        db.add(
            UtilityBillSplit(
                utility_bill_id=bill.id,
                tenant_user_id=int(item["tenant_user_id"]),
                split_method=item["split_method"],
                split_percent=item["split_percent"],
                assigned_amount=_money(float(item["assigned_amount"])),
                paid_amount=0.0,
                status=UtilityBillSplitStatus.PENDING,
                due_at=due_at,
            )
        )
    await db.commit()
    await db.refresh(bill)
    return await _build_bill_payload(db, bill)


async def publish_utility_bill(db: AsyncSession, bill_id: int, current_user: User) -> dict[str, object]:
    user_id = require_user_id(current_user.id)
    bill = await _get_utility_bill_or_404(db, bill_id)
    property_obj = await get_property_or_404(db, bill.property_id)
    if not current_user.is_superuser:
        await require_property_owner(db, bill.property_id, user_id)
    splits = await _list_bill_splits(db, bill.id)
    if not splits:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Configure bill shares before publishing")

    for split in splits:
        if split.invoice_id is not None:
            continue
        invoice = Invoice(
            invoice_number="",
            booking_id=None,
            tenant_user_id=split.tenant_user_id,
            owner_user_id=property_obj.owner_user_id,
            invoice_type=InvoiceType.UTILITY_BILL_SHARE,
            currency="NPR",
            subtotal=_money(split.assigned_amount),
            tax_amount=0.0,
            total_amount=_money(split.assigned_amount),
            paid_amount=0.0,
            status=InvoiceStatus.SENT,
            due_date=bill.due_date,
            period_start=bill.period_start,
            period_end=bill.period_end,
            metadata_json={"utility_bill_id": bill.id, "utility_bill_split_id": split.id},
        )
        db.add(invoice)
        await db.flush()
        invoice.invoice_number = f"UB-{bill.id:05d}-{split.id:03d}"
        db.add(invoice)
        from src.apps.invoicing.services.invoices import _ensure_invoice_line_item, _ensure_invoice_reminders

        await _ensure_invoice_line_item(
            db,
            invoice,
            line_item_type="utility_bill_share",
            description=f"{bill.bill_type.value.title()} bill share for {bill.billing_period_label}",
            amount=split.assigned_amount,
        )
        await _ensure_invoice_reminders(db, invoice)
        split.invoice_id = invoice.id
        split.status = UtilityBillSplitStatus.PENDING
        db.add(split)

    bill.published_at = datetime.now()
    bill.status = UtilityBillStatus.PUBLISHED
    db.add(bill)
    await db.commit()
    await db.refresh(bill)
    return await _build_bill_payload(db, bill)


async def list_tenant_bill_shares(db: AsyncSession, current_user: User) -> dict[str, object]:
    user_id = require_user_id(current_user.id)
    result = await db.execute(
        select(UtilityBillSplit)
        .where(UtilityBillSplit.tenant_user_id == user_id)
        .order_by(col(UtilityBillSplit.id).desc())
    )
    splits = list(result.scalars().all())
    items = []
    for split in splits:
        bill = await _get_utility_bill_or_404(db, split.utility_bill_id)
        disputes = await _list_split_disputes(db, split.id)
        items.append(
            {
                "split": {
                    "id": split.id,
                    "utility_bill_id": split.utility_bill_id,
                    "tenant_user_id": split.tenant_user_id,
                    "invoice_id": split.invoice_id,
                    "split_method": split.split_method,
                    "split_percent": split.split_percent,
                    "assigned_amount": _money(split.assigned_amount),
                    "paid_amount": _money(split.paid_amount),
                    "outstanding_amount": _split_outstanding(split),
                    "status": split.status,
                    "due_at": split.due_at,
                    "paid_at": split.paid_at,
                },
                "bill": await _build_bill_payload(db, bill),
                "disputes": [
                    {
                        "id": dispute.id,
                        "utility_bill_split_id": dispute.utility_bill_split_id,
                        "opened_by_user_id": dispute.opened_by_user_id,
                        "status": dispute.status,
                        "reason": dispute.reason,
                        "resolution_notes": dispute.resolution_notes,
                        "opened_at": dispute.opened_at,
                        "resolved_at": dispute.resolved_at,
                    }
                    for dispute in disputes
                ],
            }
        )
    return {"items": items, "total": len(items)}


async def pay_bill_share(
    db: AsyncSession,
    split_id: int,
    current_user: User,
    data,
    *,
    allow_partial: bool,
):
    split = await db.get(UtilityBillSplit, split_id)
    if split is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill share not found")
    user_id = require_user_id(current_user.id)
    if not current_user.is_superuser and split.tenant_user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to pay this bill share")
    if split.invoice_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bill share has not been published yet")
    return await initiate_invoice_payment(db, split.invoice_id, current_user, data, allow_partial=allow_partial)


async def dispute_bill_share(
    db: AsyncSession,
    split_id: int,
    current_user: User,
    *,
    reason: str,
) -> dict[str, object]:
    split = await db.get(UtilityBillSplit, split_id)
    if split is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill share not found")
    user_id = require_user_id(current_user.id)
    if not current_user.is_superuser and split.tenant_user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to dispute this bill share")
    if split.status in {UtilityBillSplitStatus.PAID, UtilityBillSplitStatus.WAIVED}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This bill share can no longer be disputed")
    existing_disputes = await _list_split_disputes(db, split.id)
    if any(dispute.status == UtilityBillDisputeStatus.OPEN for dispute in existing_disputes):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An open dispute already exists for this bill share")
    dispute = UtilityBillDispute(
        utility_bill_split_id=split.id,
        opened_by_user_id=user_id,
        status=UtilityBillDisputeStatus.OPEN,
        reason=reason.strip(),
    )
    split.status = UtilityBillSplitStatus.DISPUTED
    db.add(dispute)
    db.add(split)
    bill = await _get_utility_bill_or_404(db, split.utility_bill_id)
    await _sync_bill_status(db, bill)
    await db.commit()
    await db.refresh(dispute)
    return {
        "id": dispute.id,
        "utility_bill_split_id": dispute.utility_bill_split_id,
        "opened_by_user_id": dispute.opened_by_user_id,
        "status": dispute.status,
        "reason": dispute.reason,
        "resolution_notes": dispute.resolution_notes,
        "opened_at": dispute.opened_at,
        "resolved_at": dispute.resolved_at,
    }


async def resolve_bill_share_dispute(
    db: AsyncSession,
    split_id: int,
    current_user: User,
    *,
    outcome,
    resolution_notes: str,
) -> dict[str, object]:
    split = await db.get(UtilityBillSplit, split_id)
    if split is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill share not found")
    bill = await _get_utility_bill_or_404(db, split.utility_bill_id)
    user_id = require_user_id(current_user.id)
    if not current_user.is_superuser:
        await require_property_owner(db, bill.property_id, user_id)

    disputes = await _list_split_disputes(db, split.id)
    if not disputes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No dispute exists for this bill share")
    dispute = disputes[-1]
    if dispute.status != UtilityBillDisputeStatus.OPEN:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The latest dispute has already been resolved")
    now = datetime.now()
    dispute.status = outcome
    dispute.resolution_notes = resolution_notes.strip()
    dispute.resolved_at = now
    db.add(dispute)

    if split.invoice_id is not None:
        invoice = await db.get(Invoice, split.invoice_id)
    else:
        invoice = None
    if outcome == UtilityBillDisputeStatus.WAIVED:
        split.status = UtilityBillSplitStatus.WAIVED
        split.paid_at = None
        if invoice is not None:
            invoice.status = InvoiceStatus.WAIVED
            invoice.paid_at = now
            db.add(invoice)
    else:
        if invoice is not None and invoice.status == InvoiceStatus.PAID:
            split.status = UtilityBillSplitStatus.PAID
            split.paid_at = invoice.paid_at or now
        elif invoice is not None and invoice.paid_amount > 0:
            split.status = UtilityBillSplitStatus.PARTIALLY_PAID
            split.paid_at = None
        else:
            split.status = UtilityBillSplitStatus.PENDING
            split.paid_at = None
    db.add(split)
    await _sync_bill_status(db, bill)
    await db.commit()
    await db.refresh(dispute)
    return {
        "id": dispute.id,
        "utility_bill_split_id": dispute.utility_bill_split_id,
        "opened_by_user_id": dispute.opened_by_user_id,
        "status": dispute.status,
        "reason": dispute.reason,
        "resolution_notes": dispute.resolution_notes,
        "opened_at": dispute.opened_at,
        "resolved_at": dispute.resolved_at,
    }


async def sync_split_from_invoice(db: AsyncSession, invoice: Invoice) -> None:
    result = await db.execute(select(UtilityBillSplit).where(UtilityBillSplit.invoice_id == invoice.id))
    split = result.scalars().first()
    if split is None:
        return

    disputes = await _list_split_disputes(db, split.id)
    split.paid_amount = _money(invoice.paid_amount)
    if invoice.status == InvoiceStatus.WAIVED:
        split.status = UtilityBillSplitStatus.WAIVED
        split.paid_at = None
    elif invoice.status == InvoiceStatus.PAID:
        split.status = UtilityBillSplitStatus.PAID
        split.paid_at = invoice.paid_at or datetime.now()
    elif any(dispute.status == UtilityBillDisputeStatus.OPEN for dispute in disputes):
        split.status = UtilityBillSplitStatus.DISPUTED
        split.paid_at = None
    elif invoice.paid_amount > 0:
        split.status = UtilityBillSplitStatus.PARTIALLY_PAID
        split.paid_at = None
    else:
        split.status = UtilityBillSplitStatus.PENDING
        split.paid_at = None
    db.add(split)

    bill = await _get_utility_bill_or_404(db, split.utility_bill_id)
    await _sync_bill_status(db, bill)
    db.add(bill)


async def get_utility_bill_history(db: AsyncSession, bill_id: int, current_user: User) -> dict[str, object]:
    bill = await _get_utility_bill_or_404(db, bill_id)
    user_id = require_user_id(current_user.id)
    if not current_user.is_superuser:
        tenant_result = await db.execute(
            select(UtilityBillSplit).where(
                UtilityBillSplit.utility_bill_id == bill.id,
                UtilityBillSplit.tenant_user_id == user_id,
            )
        )
        tenant_split = tenant_result.scalars().first()
        if tenant_split is None:
            await require_property_owner(db, bill.property_id, user_id)

    entries = [
        {
            "event_type": "utility_bill.created",
            "message": "Utility bill created.",
            "occurred_at": bill.created_at,
            "metadata_json": {"status": bill.status.value},
        }
    ]
    if bill.published_at is not None:
        entries.append(
            {
                "event_type": "utility_bill.published",
                "message": "Utility bill published to tenants.",
                "occurred_at": bill.published_at,
                "metadata_json": None,
            }
        )
    for attachment in await _list_bill_attachments(db, bill.id):
        entries.append(
            {
                "event_type": "utility_bill.attachment_uploaded",
                "message": f"Attachment uploaded ({attachment.file_type}).",
                "occurred_at": attachment.uploaded_at,
                "metadata_json": {"attachment_id": attachment.id},
            }
        )
    for split in await _list_bill_splits(db, bill.id):
        entries.append(
            {
                "event_type": "utility_bill.split_configured",
                "message": f"Tenant share configured for user {split.tenant_user_id}.",
                "occurred_at": split.due_at or bill.created_at,
                "metadata_json": {
                    "split_id": split.id,
                    "assigned_amount": _money(split.assigned_amount),
                    "status": split.status.value,
                },
            }
        )
        for dispute in await _list_split_disputes(db, split.id):
            entries.append(
                {
                    "event_type": "utility_bill.dispute",
                    "message": dispute.reason,
                    "occurred_at": dispute.opened_at,
                    "metadata_json": {"split_id": split.id, "status": dispute.status.value},
                }
            )
            if dispute.resolved_at is not None:
                entries.append(
                    {
                        "event_type": "utility_bill.dispute_resolved",
                        "message": dispute.resolution_notes or "Dispute resolved.",
                        "occurred_at": dispute.resolved_at,
                        "metadata_json": {"split_id": split.id, "status": dispute.status.value},
                    }
                )
        if split.paid_at is not None:
            entries.append(
                {
                    "event_type": "utility_bill.paid",
                    "message": "Tenant bill share settled.",
                    "occurred_at": split.paid_at,
                    "metadata_json": {"split_id": split.id, "paid_amount": _money(split.paid_amount)},
                }
            )
    entries.sort(key=lambda item: item["occurred_at"])
    return {"bill_id": bill.id, "entries": entries}
