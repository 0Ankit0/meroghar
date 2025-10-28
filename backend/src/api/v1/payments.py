"""Payment management endpoints.

Implements T061-T064, T114, T118 from tasks.md.
"""

import logging
import tempfile
from datetime import date
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...api.dependencies import (CommonQueryParams, get_current_user,
                                 require_role)
from ...core.config import get_settings
from ...core.database import get_async_db
from ...models.payment import Payment, PaymentStatus, PaymentType
from ...models.property import PropertyAssignment
from ...models.tenant import Tenant
from ...models.user import User, UserRole
from ...schemas.payment import (PaymentCreateRequest, PaymentListResponse,
                                PaymentResponse)
from ...services.payment_gateway import PaymentGateway, PaymentGatewayFactory
from ...services.payment_service import PaymentService

# Configure logger for payment endpoints
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a new payment",
    description="Record a payment for a tenant. Requires intermediary role and property assignment.",
)
async def record_payment(
    request: PaymentCreateRequest,
    current_user: Annotated[User, Depends(require_role(UserRole.INTERMEDIARY))],
    session: Annotated[AsyncSession, Depends(get_async_db)],
) -> PaymentResponse:
    """Record a new payment.

    Only intermediaries can record payments for properties they manage.

    Args:
        request: Payment creation request
        current_user: Authenticated intermediary user
        session: Database session

    Returns:
        Created payment details

    Raises:
        403: If intermediary is not assigned to the property
        404: If tenant or property not found
        400: If validation fails (inactive tenant, invalid amounts, etc.)
        500: If database error occurs
    """
    try:
        # Verify intermediary is assigned to the property
        result = await session.execute(
            select(PropertyAssignment).where(
                and_(
                    PropertyAssignment.property_id == request.property_id,
                    PropertyAssignment.intermediary_id == current_user.id,
                )
            )
        )
        assignment = result.scalar_one_or_none()

        if not assignment:
            logger.warning(
                f"Intermediary {current_user.id} attempted to record payment "
                f"for unassigned property {request.property_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned to manage this property",
            )

        # Record the payment using service
        payment_service = PaymentService(session)
        payment = await payment_service.record_payment(
            request=request,
            recorded_by=current_user.id,
        )

        logger.info(
            f"Payment recorded: id={payment.id}, tenant_id={payment.tenant_id}, "
            f"amount={payment.amount}, recorded_by={current_user.id}"
        )

        return PaymentResponse.model_validate(payment)

    except ValueError as e:
        # Service validation errors (tenant not found, inactive, etc.)
        logger.error(f"Payment validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error recording payment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record payment",
        )


@router.get(
    "",
    response_model=PaymentListResponse,
    summary="List payments",
    description="Retrieve list of payments with optional filters. Results filtered by role permissions.",
)
async def list_payments(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_db)],
    commons: Annotated[CommonQueryParams, Depends()],
    tenant_id: UUID | None = Query(None, description="Filter by tenant ID"),
    property_id: UUID | None = Query(None, description="Filter by property ID"),
    payment_type: PaymentType | None = Query(None, description="Filter by payment type"),
    payment_status: PaymentStatus | None = Query(None, description="Filter by payment status"),
    date_from: date | None = Query(None, description="Filter payments from this date"),
    date_to: date | None = Query(None, description="Filter payments to this date"),
) -> PaymentListResponse:
    """List payments with filters.

    Filters applied based on user role:
    - OWNER: See all payments for properties they own
    - INTERMEDIARY: See payments for properties they manage
    - TENANT: See only their own payments

    Args:
        current_user: Authenticated user
        session: Database session
        commons: Common pagination params
        tenant_id: Optional tenant filter
        property_id: Optional property filter
        payment_type: Optional payment type filter
        payment_status: Optional payment status filter
        date_from: Optional date range start
        date_to: Optional date range end

    Returns:
        List of payments with pagination

    Raises:
        500: If database error occurs
    """
    try:
        # Build base query with eager loading
        query = select(Payment).options(
            selectinload(Payment.tenant),
            selectinload(Payment.property),
        )

        # Apply role-based filtering (will be enhanced with RLS in T072)
        if current_user.role == UserRole.TENANT:
            # Tenants can only see their own payments
            query = query.where(Payment.tenant_id == current_user.id)
        elif current_user.role == UserRole.INTERMEDIARY:
            # Intermediaries see payments for properties they manage
            result = await session.execute(
                select(PropertyAssignment.property_id).where(
                    PropertyAssignment.intermediary_id == current_user.id
                )
            )
            managed_property_ids = [row[0] for row in result.all()]
            query = query.where(Payment.property_id.in_(managed_property_ids))
        # OWNER sees all payments (no additional filter needed)

        # Apply optional filters
        if tenant_id:
            query = query.where(Payment.tenant_id == tenant_id)

        if property_id:
            query = query.where(Payment.property_id == property_id)

        if payment_type:
            query = query.where(Payment.payment_type == payment_type)

        if payment_status:
            query = query.where(Payment.status == payment_status)

        if date_from:
            query = query.where(Payment.payment_date >= date_from)

        if date_to:
            query = query.where(Payment.payment_date <= date_to)

        # Count total results
        from sqlalchemy import func

        count_query = select(func.count(Payment.id))
        for whereclause in query.whereclause:
            count_query = count_query.where(whereclause)

        result = await session.execute(count_query)
        total = result.scalar() or 0

        # Apply pagination and ordering
        query = query.order_by(Payment.payment_date.desc())
        query = query.offset(commons.skip).limit(commons.limit)

        # Execute query
        result = await session.execute(query)
        payments = result.scalars().all()

        logger.info(
            f"Listed {len(payments)} payments for user {current_user.id} "
            f"(role={current_user.role.value}, total={total})"
        )

        return PaymentListResponse(
            payments=[PaymentResponse.model_validate(p) for p in payments],
            total=total,
            skip=commons.skip,
            limit=commons.limit,
        )

    except Exception as e:
        logger.error(f"Error listing payments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve payments",
        )


@router.get(
    "/{payment_id}/receipt",
    response_class=FileResponse,
    summary="Generate and download payment receipt",
    description="Generate a PDF receipt for a payment and download it.",
)
async def get_payment_receipt(
    payment_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_db)],
) -> FileResponse:
    """Generate and download payment receipt as PDF.

    Authorization:
    - OWNER: Can generate receipt for any payment
    - INTERMEDIARY: Can generate receipt for payments in managed properties
    - TENANT: Can generate receipt for their own payments

    Args:
        payment_id: Payment ID to generate receipt for
        current_user: Authenticated user
        session: Database session

    Returns:
        PDF file as download

    Raises:
        403: If user doesn't have permission to view payment
        404: If payment not found
        500: If PDF generation fails
    """
    try:
        # Get payment to verify existence and authorization
        result = await session.execute(select(Payment).where(Payment.id == payment_id))
        payment = result.scalar_one_or_none()

        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment {payment_id} not found",
            )

        # Authorization check based on role
        if current_user.role == UserRole.TENANT:
            # Tenants can only view their own payment receipts
            if current_user.id != payment.tenant_id:
                logger.warning(
                    f"Tenant {current_user.id} attempted to view receipt "
                    f"for payment {payment_id} (tenant={payment.tenant_id})"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only view receipts for your own payments",
                )
        elif current_user.role == UserRole.INTERMEDIARY:
            # Intermediaries can view receipts for payments in managed properties
            result = await session.execute(
                select(PropertyAssignment).where(
                    and_(
                        PropertyAssignment.property_id == payment.property_id,
                        PropertyAssignment.intermediary_id == current_user.id,
                    )
                )
            )
            assignment = result.scalar_one_or_none()

            if not assignment:
                logger.warning(
                    f"Intermediary {current_user.id} attempted to view receipt "
                    f"for payment {payment_id} in unassigned property {payment.property_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not assigned to manage this payment's property",
                )
        # OWNER can view any receipt (no additional check needed)

        # Generate receipt using service
        payment_service = PaymentService(session)

        # Create temporary file for PDF
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, suffix=".pdf", prefix=f"receipt_{payment_id}_"
        )
        temp_path = temp_file.name
        temp_file.close()

        # Generate PDF
        await payment_service.generate_receipt(
            payment_id=payment_id,
            output_path=temp_path,
        )

        logger.info(f"Receipt generated for payment {payment_id} by user {current_user.id}")

        # Return file as download
        return FileResponse(
            path=temp_path,
            media_type="application/pdf",
            filename=f"receipt_{str(payment_id)[:8]}.pdf",
            background=None,  # File will be deleted after response
        )

    except HTTPException:
        raise
    except ValueError as e:
        # Service validation errors
        logger.error(f"Receipt generation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error generating receipt: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate receipt",
        )


@router.get(
    "/calculate-prorated",
    response_model=dict[str, Decimal],
    summary="Calculate pro-rated rent",
    description="Calculate pro-rated rent for a tenant based on move-in date and period",
)
async def calculate_prorated_rent(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_db)],
    tenant_id: UUID = Query(..., description="Tenant ID"),
    period_start: date = Query(..., description="Payment period start date"),
    period_end: date = Query(..., description="Payment period end date"),
) -> dict[str, Decimal]:
    """Calculate pro-rated rent for a tenant.

    This endpoint helps calculate the correct rent amount when a tenant
    moves in mid-month. The calculation is based on:
    - Monthly rent from tenant record
    - Tenant's move-in date
    - The payment period

    Only intermediaries can access this endpoint.

    Args:
        current_user: Authenticated intermediary user
        session: Database session
        tenant_id: Tenant to calculate rent for
        period_start: Start of payment period
        period_end: End of payment period

    Returns:
        Dict with monthly_rent and prorated_rent amounts

    Raises:
        403: If user is not an intermediary
        404: If tenant not found
        400: If period dates are invalid
        500: If database error occurs
    """
    try:
        # Only intermediaries can use this endpoint
        if current_user.role != UserRole.INTERMEDIARY:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only intermediaries can calculate pro-rated rent",
            )

        # Validate period dates
        if period_end <= period_start:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Period end must be after period start",
            )

        # Fetch tenant
        result = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()

        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found",
            )

        # Verify intermediary is assigned to the property
        result = await session.execute(
            select(PropertyAssignment).where(
                and_(
                    PropertyAssignment.property_id == tenant.property_id,
                    PropertyAssignment.intermediary_id == current_user.id,
                    PropertyAssignment.is_active,
                )
            )
        )
        assignment = result.scalar_one_or_none()

        if not assignment:
            logger.warning(
                f"Intermediary {current_user.id} attempted to calculate rent "
                f"for tenant {tenant_id} on unassigned property {tenant.property_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned to manage this tenant's property",
            )

        # Calculate pro-rated rent
        payment_service = PaymentService(session)
        prorated_amount = await payment_service.calculate_prorated_rent(
            monthly_rent=tenant.monthly_rent,
            move_in_date=tenant.move_in_date,
            period_start=period_start,
            period_end=period_end,
        )

        logger.info(
            f"Pro-rated rent calculated: tenant_id={tenant_id}, "
            f"monthly={tenant.monthly_rent}, prorated={prorated_amount}"
        )

        return {
            "monthly_rent": tenant.monthly_rent,
            "prorated_rent": prorated_amount,
            "move_in_date": tenant.move_in_date.isoformat(),
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating pro-rated rent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate pro-rated rent",
        )


# ==================== Online Payment Gateway Endpoints (T114, T118) ====================


@router.post(
    "/initiate",
    response_model=dict[str, any],
    status_code=status.HTTP_200_OK,
    summary="Initiate online payment through gateway",
    description="Initiate payment through Khalti, eSewa, or IME Pay. Returns payment URL for user redirection.",
)
async def initiate_online_payment(
    tenant_id: UUID,
    amount: Decimal,
    payment_type: PaymentType,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_db)],
    gateway: PaymentGateway = PaymentGateway.KHALTI,
) -> dict[str, any]:
    """Initiate online payment through payment gateway (T114).

    This creates a payment intent and returns a payment URL where the user
    should be redirected to complete the payment.

    Args:
        tenant_id: Tenant making the payment
        amount: Payment amount in rupees
        payment_type: Type of payment (rent, bill_share, etc.)
        gateway: Payment gateway to use (khalti, esewa, imepay)
        current_user: Authenticated user
        session: Database session

    Returns:
        Dict containing:
            - payment_url: URL to redirect user for payment
            - transaction_id: Payment tracking ID
            - expires_at: Payment link expiration time
            - expires_in: Expiration time in seconds

    Raises:
        403: If user doesn't have permission
        404: If tenant not found
        400: If validation fails
        500: If gateway error occurs
    """
    try:
        # Get tenant details
        result = await session.execute(
            select(Tenant).where(Tenant.id == tenant_id).options(selectinload(Tenant.property))
        )
        tenant = result.scalar_one_or_none()

        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant {tenant_id} not found",
            )

        # Verify permission (tenant can pay for themselves, intermediary/owner can initiate for tenants)
        if current_user.role == UserRole.TENANT:
            # Tenant can only pay for themselves
            if tenant.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only initiate payment for yourself",
                )
        elif current_user.role == UserRole.INTERMEDIARY:
            # Intermediary must be assigned to the property
            result = await session.execute(
                select(PropertyAssignment).where(
                    and_(
                        PropertyAssignment.property_id == tenant.property_id,
                        PropertyAssignment.intermediary_id == current_user.id,
                    )
                )
            )
            if not result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not assigned to manage this property",
                )

        # Create payment gateway instance
        gateway_service = PaymentGatewayFactory.create_gateway(gateway)

        # Generate unique purchase order ID
        from datetime import datetime

        purchase_order_id = f"PAY-{tenant_id}-{int(datetime.utcnow().timestamp())}"

        # Get settings for configuration
        settings = get_settings()
        
        # Get property_id from tenant
        property_id = tenant.property_id
        
        # Initiate payment with gateway
        result = await gateway_service.initiate_payment(
            amount=amount,
            purchase_order_id=purchase_order_id,
            purchase_order_name=f"{payment_type.value.replace('_', ' ').title()} - Tenant {tenant_id}",
            return_url=f"{settings.website_url}/api/v1/webhooks/{gateway.value}",  # Webhook URL
            website_url=settings.website_url,
            customer_name=tenant.user.full_name if hasattr(tenant, "user") else None,
            customer_email=tenant.user.email if hasattr(tenant, "user") else None,
            customer_phone=tenant.user.phone if hasattr(tenant, "user") else None,
            merchant_tenant_id=str(tenant_id),
            merchant_payment_type=payment_type.value,
            merchant_user_id=str(current_user.id),
        )

        # Store payment intent in database (for tracking)
        payment_service = PaymentService(session)
        # Create pending payment record for tracking
        from ...schemas.payment import PaymentCreateRequest
        
        pending_payment = await payment_service.create_pending_payment(
            tenant_id=tenant_id,
            property_id=property_id,
            amount=amount,
            payment_type=payment_type,
            transaction_reference=result.get("pidx") or result.get("transaction_id"),
            gateway=gateway.value,
        )

        logger.info(
            f"Online payment initiated: tenant_id={tenant_id}, amount={amount}, "
            f"gateway={gateway}, order_id={purchase_order_id}"
        )

        return {
            "payment_url": result.get("payment_url"),
            "transaction_id": result.get("pidx") or result.get("transaction_id"),
            "expires_at": result.get("expires_at"),
            "expires_in": result.get("expires_in"),
            "gateway": gateway.value,
            "amount": float(amount),
            "purchase_order_id": purchase_order_id,
        }

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Payment initiation validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error initiating online payment: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate online payment",
        )


@router.get(
    "/{payment_id}/status",
    response_model=dict[str, any],
    summary="Get payment status",
    description="Poll payment status for real-time updates. Used by mobile app to check payment completion.",
)
async def get_payment_status(
    payment_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_db)],
) -> dict[str, any]:
    """Get current payment status (T118).

    Used by mobile apps to poll payment status while user completes payment.

    Args:
        payment_id: Payment ID to check
        current_user: Authenticated user
        session: Database session

    Returns:
        Dict containing:
            - status: Payment status
            - amount: Payment amount
            - payment_date: Date payment was completed (if completed)
            - transaction_id: Gateway transaction ID (if completed)

    Raises:
        404: If payment not found
        403: If user doesn't have permission to view payment
    """
    try:
        # Get payment details
        result = await session.execute(
            select(Payment)
            .where(Payment.id == payment_id)
            .options(
                selectinload(Payment.tenant),
                selectinload(Payment.property),
            )
        )
        payment = result.scalar_one_or_none()

        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment {payment_id} not found",
            )

        # Verify permission
        if current_user.role == UserRole.TENANT:
            if payment.tenant.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only view your own payments",
                )
        elif current_user.role == UserRole.INTERMEDIARY:
            # Check property assignment
            result = await session.execute(
                select(PropertyAssignment).where(
                    and_(
                        PropertyAssignment.property_id == payment.property_id,
                        PropertyAssignment.intermediary_id == current_user.id,
                    )
                )
            )
            if not result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to view this payment",
                )

        # Return payment status
        response = {
            "id": str(payment.id),
            "status": payment.status.value if payment.status else "pending",
            "amount": float(payment.amount),
            "currency": payment.currency,
            "payment_type": payment.payment_type.value,
            "payment_method": payment.payment_method.value,
            "payment_date": payment.payment_date.isoformat() if payment.payment_date else None,
            "reference_number": payment.reference_number,
            "is_voided": payment.is_voided,
        }

        # Add transaction details if available
        if hasattr(payment, "transaction") and payment.transaction:
            response["transaction"] = {
                "id": str(payment.transaction.id),
                "gateway": payment.transaction.gateway.value,
                "gateway_transaction_id": payment.transaction.gateway_transaction_id,
                "status": payment.transaction.status.value,
                "gateway_fee": (
                    float(payment.transaction.gateway_fee)
                    if payment.transaction.gateway_fee
                    else None
                ),
            }

        logger.info(f"Payment status retrieved: payment_id={payment_id}, status={payment.status}")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving payment status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve payment status",
        )


@router.post(
    "/export",
    summary="Export payment history",
    description="Export payment history to Excel or PDF format (T205-T207)",
)
async def export_payment_history(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_db)],
    tenant_id: UUID | None = Query(
        None, description="Tenant ID (defaults to current user if tenant)"
    ),
    start_date: date | None = Query(None, description="Start date for filtering"),
    end_date: date | None = Query(None, description="End date for filtering"),
    format: str = Query("excel", description="Export format: 'excel' or 'pdf'"),
) -> FileResponse:
    """Export payment history for a tenant.

    Tenants can export their own history.
    Owners/Intermediaries can export any tenant's history in their properties.

    Implements T205-T207 from tasks.md.
    """
    from ...services.export_service import ExportService

    try:
        # Determine tenant_id
        if current_user.role == UserRole.TENANT:
            # Tenant can only export their own history
            result = await session.execute(select(Tenant).where(Tenant.user_id == current_user.id))
            tenant = result.scalar_one_or_none()
            if not tenant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Tenant profile not found",
                )
            target_tenant_id = tenant.id
        elif tenant_id:
            # Owner/Intermediary accessing specific tenant
            result = await session.execute(
                select(Tenant).options(selectinload(Tenant.property)).where(Tenant.id == tenant_id)
            )
            tenant = result.scalar_one_or_none()
            if not tenant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Tenant not found",
                )

            # Verify access
            if current_user.role == UserRole.OWNER:
                if tenant.property.owner_id != current_user.id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Not authorized to export this tenant's history",
                    )
            elif current_user.role == UserRole.INTERMEDIARY:
                if tenant.intermediary_id != current_user.id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Not authorized to export this tenant's history",
                    )

            target_tenant_id = tenant_id
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="tenant_id required for non-tenant users",
            )

        # Validate format
        if format not in ["excel", "pdf"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Format must be 'excel' or 'pdf'",
            )

        # Generate export using synchronous session
        # Note: In production, convert ExportService to async or use run_in_executor
        export_service = ExportService(session.sync_session)

        if format == "excel":
            buffer = export_service.export_payment_history_excel(
                tenant_id=target_tenant_id,
                start_date=start_date,
                end_date=end_date,
            )
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"payment_history_{target_tenant_id}_{date.today().isoformat()}.xlsx"
        else:  # pdf
            buffer = export_service.export_payment_history_pdf(
                tenant_id=target_tenant_id,
                start_date=start_date,
                end_date=end_date,
            )
            media_type = "application/pdf"
            filename = f"payment_history_{target_tenant_id}_{date.today().isoformat()}.pdf"

        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{format}") as tmp:
            tmp.write(buffer.read())
            tmp_path = tmp.name

        logger.info(
            f"Payment history exported: tenant_id={target_tenant_id}, format={format}, user={current_user.id}"
        )

        return FileResponse(
            path=tmp_path,
            media_type=media_type,
            filename=filename,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting payment history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export payment history: {str(e)}",
        )


__all__ = ["router"]
