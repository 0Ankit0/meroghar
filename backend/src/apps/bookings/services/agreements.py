from __future__ import annotations

import hashlib
import uuid
from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from src.apps.bookings.models.agreement import AgreementStatus, AgreementTemplate, RentalAgreement
from src.apps.bookings.models.booking import BookingStatus
from src.apps.bookings.schemas.agreement import AgreementGenerateRequest, EsignWebhookRequest
from src.apps.bookings.services.bookings import (
    emit_booking_event,
    get_accessible_booking_for_user,
    get_effective_booking_status,
    get_manageable_booking_for_user,
)
from src.apps.core.storage import save_media_bytes
from src.apps.iam.models.user import User
from src.apps.iam.utils.identity import require_user_id
from src.apps.listings.models.property import Property
from src.apps.listings.services.properties import get_property_or_404

_DEFAULT_AGREEMENT_TEMPLATE = """MEROGHAR RENTAL AGREEMENT\n\nBooking number: {{booking_number}}\nProperty: {{property_name}}\nProperty address: {{property_address}}\n\nTenant: {{tenant_name}}\nOwner: {{owner_name}}\n\nStay window: {{rental_start_at}} to {{rental_end_at}}\nCurrency: {{currency}}\nTotal fee: {{total_fee}}\nSecurity deposit: {{deposit_amount}}\n\nSpecial requests:\n{{special_requests}}\n\nCustom clauses:\n{{custom_clauses}}\n"""


def _document_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


async def _get_latest_agreement(db: AsyncSession, booking_id: int) -> RentalAgreement | None:
    result = await db.execute(
        select(RentalAgreement)
        .where(RentalAgreement.booking_id == booking_id)
        .order_by(col(RentalAgreement.created_at).desc(), col(RentalAgreement.id).desc())
    )
    return result.scalars().first()


async def _get_template(db: AsyncSession, template_id: int) -> AgreementTemplate | None:
    return await db.get(AgreementTemplate, template_id)


async def _resolve_template(
    db: AsyncSession,
    property_obj: Property,
    *,
    actor_user_id: int,
    template_id: int | None,
) -> AgreementTemplate:
    if template_id is not None:
        template = await _get_template(db, template_id)
        if template is None or not template.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agreement template not found")
        if template.property_type_id != property_obj.property_type_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agreement template does not match the property's category",
            )
        return template

    result = await db.execute(
        select(AgreementTemplate)
        .where(
            AgreementTemplate.property_type_id == property_obj.property_type_id,
            AgreementTemplate.is_active,
        )
        .order_by(col(AgreementTemplate.version).desc(), col(AgreementTemplate.id).desc())
    )
    template = result.scalars().first()
    if template is not None:
        return template

    template = AgreementTemplate(
        created_by_admin_id=actor_user_id,
        property_type_id=property_obj.property_type_id,
        name=f"{property_obj.name} standard lease",
        template_content=_DEFAULT_AGREEMENT_TEMPLATE,
        is_active=True,
        version=1,
        created_at=datetime.now(),
    )
    db.add(template)
    await db.flush()
    return template


async def _build_agreement_payload(db: AsyncSession, agreement: RentalAgreement) -> dict[str, Any]:
    template = await _get_template(db, agreement.template_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agreement template not found")

    return {
        "id": agreement.id,
        "booking_id": agreement.booking_id,
        "template": {
            "id": template.id,
            "property_type_id": template.property_type_id,
            "name": template.name,
            "version": template.version,
        },
        "status": agreement.status,
        "rendered_content": agreement.rendered_content,
        "custom_clauses": list(agreement.custom_clauses_json),
        "rendered_document_url": agreement.rendered_document_url,
        "rendered_document_sha256": agreement.rendered_document_sha256,
        "esign_request_id": agreement.esign_request_id,
        "signed_document_url": agreement.signed_document_url,
        "signed_document_sha256": agreement.signed_document_sha256,
        "sent_at": agreement.sent_at,
        "customer_signed_at": agreement.customer_signed_at,
        "customer_signature_ip": agreement.customer_signature_ip,
        "owner_signed_at": agreement.owner_signed_at,
        "owner_signature_ip": agreement.owner_signature_ip,
        "version": agreement.version,
        "created_at": agreement.created_at,
    }


def _display_name(user: User | None, fallback: str) -> str:
    if user is None:
        return fallback
    return user.username or user.email or fallback


async def _render_agreement_content(
    db: AsyncSession,
    template: AgreementTemplate,
    booking,
    property_obj: Property,
    custom_clauses: list[str],
) -> str:
    tenant = await db.get(User, booking.tenant_user_id)
    owner = await db.get(User, booking.owner_user_id)
    custom_clause_text = "\n".join(f"- {clause}" for clause in custom_clauses) if custom_clauses else "- None"
    rendered = template.template_content
    replacements = {
        "{{booking_number}}": booking.booking_number,
        "{{property_name}}": property_obj.name,
        "{{property_address}}": property_obj.location_address,
        "{{tenant_name}}": _display_name(tenant, f"Tenant #{booking.tenant_user_id}"),
        "{{owner_name}}": _display_name(owner, f"Owner #{booking.owner_user_id}"),
        "{{rental_start_at}}": booking.rental_start_at.isoformat(),
        "{{rental_end_at}}": booking.rental_end_at.isoformat(),
        "{{currency}}": booking.currency,
        "{{total_fee}}": f"{booking.total_fee:.2f}",
        "{{deposit_amount}}": f"{booking.deposit_amount:.2f}",
        "{{special_requests}}": booking.special_requests or "None",
        "{{custom_clauses}}": custom_clause_text,
    }
    for token, value in replacements.items():
        rendered = rendered.replace(token, value)
    return rendered


def _save_document(relative_path: str, content: str) -> tuple[str, str]:
    digest = _document_hash(content)
    url = save_media_bytes(
        relative_path,
        content.encode("utf-8"),
        content_type="text/plain; charset=utf-8",
    )
    return url, digest


async def get_booking_agreement_or_404(
    db: AsyncSession,
    booking_id: int,
    current_user: User,
) -> dict[str, Any]:
    booking = await get_accessible_booking_for_user(db, booking_id, current_user)
    agreement = await _get_latest_agreement(db, booking.id)
    if agreement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agreement not found")
    return await _build_agreement_payload(db, agreement)


async def generate_booking_agreement(
    db: AsyncSession,
    booking_id: int,
    current_user: User,
    data: AgreementGenerateRequest,
) -> dict[str, Any]:
    booking = await get_manageable_booking_for_user(db, booking_id, current_user)
    effective_status = get_effective_booking_status(booking)
    if effective_status not in {
        BookingStatus.CONFIRMED,
        BookingStatus.ACTIVE,
        BookingStatus.PENDING_CLOSURE,
        BookingStatus.CLOSED,
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agreements can only be generated for confirmed or completed bookings",
        )

    actor_user_id = require_user_id(current_user.id)
    property_obj = await get_property_or_404(db, booking.property_id)
    template = await _resolve_template(
        db,
        property_obj,
        actor_user_id=actor_user_id,
        template_id=data.template_id,
    )
    existing_agreement = await _get_latest_agreement(db, booking.id)
    if existing_agreement is not None and existing_agreement.status != AgreementStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An agreement already exists for this booking",
        )

    version = 1 if existing_agreement is None else existing_agreement.version + 1
    rendered_content = await _render_agreement_content(
        db,
        template,
        booking,
        property_obj,
        data.custom_clauses,
    )
    rendered_document_url, rendered_document_sha256 = _save_document(
        f"agreements/{booking.id}/draft-v{version}.txt",
        rendered_content,
    )

    if existing_agreement is None:
        agreement = RentalAgreement(
            booking_id=booking.id,
            template_id=template.id,
            status=AgreementStatus.DRAFT,
            rendered_content=rendered_content,
            custom_clauses_json=list(data.custom_clauses),
            rendered_document_url=rendered_document_url,
            rendered_document_sha256=rendered_document_sha256,
            version=version,
            created_at=datetime.now(),
        )
    else:
        agreement = existing_agreement
        agreement.template_id = template.id
        agreement.status = AgreementStatus.DRAFT
        agreement.rendered_content = rendered_content
        agreement.custom_clauses_json = list(data.custom_clauses)
        agreement.rendered_document_url = rendered_document_url
        agreement.rendered_document_sha256 = rendered_document_sha256
        agreement.esign_request_id = None
        agreement.signed_document_url = None
        agreement.signed_document_sha256 = None
        agreement.sent_at = None
        agreement.customer_signed_at = None
        agreement.customer_signature_ip = None
        agreement.owner_signed_at = None
        agreement.owner_signature_ip = None
        agreement.version = version
    db.add(agreement)
    await db.flush()

    await emit_booking_event(
        db,
        booking.id,
        "agreement.generated",
        "Draft rental agreement generated.",
        actor_user_id=actor_user_id,
        metadata={
            "agreement_id": agreement.id,
            "template_id": template.id,
            "version": agreement.version,
        },
    )
    await db.commit()
    await db.refresh(agreement)
    return await _build_agreement_payload(db, agreement)


async def send_booking_agreement(
    db: AsyncSession,
    booking_id: int,
    current_user: User,
) -> dict[str, Any]:
    booking = await get_manageable_booking_for_user(db, booking_id, current_user)
    agreement = await _get_latest_agreement(db, booking.id)
    if agreement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agreement not found")
    if agreement.status == AgreementStatus.PENDING_CUSTOMER_SIGNATURE:
        return await _build_agreement_payload(db, agreement)
    if agreement.status != AgreementStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft agreements can be sent for signature",
        )

    actor_user_id = require_user_id(current_user.id)
    agreement.status = AgreementStatus.PENDING_CUSTOMER_SIGNATURE
    agreement.sent_at = datetime.now()
    agreement.esign_request_id = uuid.uuid4().hex
    db.add(agreement)
    await emit_booking_event(
        db,
        booking.id,
        "agreement.sent",
        "Agreement sent to tenant for signature.",
        actor_user_id=actor_user_id,
        metadata={
            "agreement_id": agreement.id,
            "esign_request_id": agreement.esign_request_id,
        },
    )
    await db.commit()
    await db.refresh(agreement)
    return await _build_agreement_payload(db, agreement)


async def process_esign_webhook(
    db: AsyncSession,
    data: EsignWebhookRequest,
) -> dict[str, Any]:
    result = await db.execute(
        select(RentalAgreement).where(RentalAgreement.esign_request_id == data.esign_request_id)
    )
    agreement = result.scalars().first()
    if agreement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agreement not found")

    if agreement.status == AgreementStatus.PENDING_OWNER_SIGNATURE:
        return await _build_agreement_payload(db, agreement)
    if agreement.status == AgreementStatus.SIGNED:
        return await _build_agreement_payload(db, agreement)
    if agreement.status != AgreementStatus.PENDING_CUSTOMER_SIGNATURE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agreement is not waiting for customer signature",
        )

    signed_at = data.signed_at or datetime.now()
    agreement.status = AgreementStatus.PENDING_OWNER_SIGNATURE
    agreement.customer_signed_at = signed_at
    agreement.customer_signature_ip = data.ip_address
    db.add(agreement)

    await emit_booking_event(
        db,
        agreement.booking_id,
        "agreement.customer_signed",
        "Tenant completed the e-signature step.",
        metadata={
            "agreement_id": agreement.id,
            "signed_at": signed_at.isoformat(),
        },
    )
    await db.commit()
    await db.refresh(agreement)
    return await _build_agreement_payload(db, agreement)


async def countersign_booking_agreement(
    db: AsyncSession,
    booking_id: int,
    current_user: User,
    *,
    request_ip: str | None,
) -> dict[str, Any]:
    booking = await get_manageable_booking_for_user(db, booking_id, current_user)
    agreement = await _get_latest_agreement(db, booking.id)
    if agreement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agreement not found")
    if agreement.status == AgreementStatus.SIGNED:
        return await _build_agreement_payload(db, agreement)
    if agreement.status != AgreementStatus.PENDING_OWNER_SIGNATURE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only tenant-signed agreements can be countersigned",
        )

    actor_user_id = require_user_id(current_user.id)
    signed_content = (
        f"{agreement.rendered_content}\n\n"
        f"Countersigned by owner at {datetime.now().isoformat()}"
    )
    signed_document_url, signed_document_sha256 = _save_document(
        f"agreements/{booking.id}/signed-v{agreement.version}.txt",
        signed_content,
    )

    agreement.status = AgreementStatus.SIGNED
    agreement.owner_signed_at = datetime.now()
    agreement.owner_signature_ip = request_ip
    agreement.signed_document_url = signed_document_url
    agreement.signed_document_sha256 = signed_document_sha256
    db.add(agreement)
    await emit_booking_event(
        db,
        booking.id,
        "agreement.signed",
        "Agreement countersigned by the owner.",
        actor_user_id=actor_user_id,
        metadata={"agreement_id": agreement.id},
    )
    await db.commit()
    await db.refresh(agreement)
    return await _build_agreement_payload(db, agreement)
