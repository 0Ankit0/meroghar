"""Payment service for recording payments and calculating balances.

Implements T060 from tasks.md.
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.cache import invalidate_cache
from ..models.payment import Payment, PaymentStatus, PaymentType
from ..models.tenant import Tenant, TenantStatus
from ..schemas.payment import PaymentCreateRequest, TenantBalanceResponse

logger = logging.getLogger(__name__)


class PaymentService:
    """Service for payment-related operations."""

    def __init__(self, session: AsyncSession):
        """Initialize payment service with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def record_payment(
        self,
        request: PaymentCreateRequest,
        recorded_by: UUID,
    ) -> Payment:
        """Record a new payment.

        Args:
            request: Payment creation request
            recorded_by: User ID of the person recording the payment

        Returns:
            Created payment record

        Raises:
            ValueError: If tenant not found or validation fails
        """
        # Verify tenant exists and is active
        result = await self.session.execute(
            select(Tenant).where(
                Tenant.id == request.tenant_id,
                Tenant.property_id == request.property_id,
            )
        )
        tenant = result.scalar_one_or_none()

        if not tenant:
            raise ValueError(
                f"Tenant {request.tenant_id} not found for property {request.property_id}"
            )

        if tenant.status != TenantStatus.ACTIVE:
            raise ValueError(f"Cannot record payment for inactive tenant {request.tenant_id}")

        # T074: Validate payment date is not in the future
        from datetime import date as date_class

        if request.payment_date > date_class.today():
            raise ValueError("Payment date cannot be in the future")

        # T074: Validate period dates if provided
        if request.payment_period_start and request.payment_period_end:
            if request.payment_period_end <= request.payment_period_start:
                raise ValueError("Payment period end must be after start date")

        # T074: Check for duplicate payments (same period for rent)
        if (
            request.payment_type == PaymentType.RENT
            and request.payment_period_start
            and request.payment_period_end
        ):
            result = await self.session.execute(
                select(Payment).where(
                    Payment.tenant_id == request.tenant_id,
                    Payment.property_id == request.property_id,
                    Payment.payment_type == PaymentType.RENT,
                    Payment.payment_period_start == request.payment_period_start,
                    Payment.payment_period_end == request.payment_period_end,
                    Payment.status.in_([PaymentStatus.COMPLETED, PaymentStatus.PENDING]),
                )
            )
            existing_payment = result.scalar_one_or_none()

            if existing_payment:
                raise ValueError(
                    f"Payment already exists for period {request.payment_period_start} to {request.payment_period_end}"
                )

        # T074: Validate payment amount for rent type
        if request.payment_type == PaymentType.RENT:
            # Allow some flexibility (e.g., 120% of monthly rent for security)
            max_rent_amount = tenant.monthly_rent * Decimal("1.20")
            if request.amount > max_rent_amount:
                raise ValueError(
                    f"Payment amount {request.amount} exceeds maximum allowed rent {max_rent_amount} "
                    f"(monthly rent: {tenant.monthly_rent})"
                )

        # Create payment record
        payment = Payment(
            tenant_id=request.tenant_id,
            property_id=request.property_id,
            recorded_by=recorded_by,
            amount=request.amount,
            currency=request.currency,
            payment_method=request.payment_method,
            payment_type=request.payment_type,
            status=PaymentStatus.COMPLETED,
            payment_date=request.payment_date,
            payment_period_start=request.payment_period_start,
            payment_period_end=request.payment_period_end,
            transaction_reference=request.transaction_reference,
            notes=request.notes,
        )

        self.session.add(payment)
        await self.session.commit()
        await self.session.refresh(payment)

        # Invalidate analytics caches
        invalidate_cache("cache:analytics:*")

        logger.info(
            f"Payment recorded: payment_id={payment.id}, tenant_id={request.tenant_id}, "
            f"amount={request.amount}, type={request.payment_type.value}, "
            f"recorded_by={recorded_by}"
        )

        return payment

    async def create_pending_payment(
        self,
        tenant_id: UUID,
        property_id: UUID,
        amount: Decimal,
        payment_type: PaymentType,
        transaction_reference: str | None,
        gateway: str,
    ) -> Payment:
        """Create a pending payment record for online payment tracking.

        This creates a payment record in PENDING status for tracking
        online payment gateway transactions.

        Args:
            tenant_id: Tenant making the payment
            property_id: Property for the payment
            amount: Payment amount
            payment_type: Type of payment (rent, security deposit, etc.)
            transaction_reference: Gateway transaction reference/ID
            gateway: Payment gateway name

        Returns:
            Created pending payment record

        Raises:
            ValueError: If tenant not found or validation fails
        """
        # Verify tenant exists
        result = await self.session.execute(
            select(Tenant).where(
                Tenant.id == tenant_id,
                Tenant.property_id == property_id,
            )
        )
        tenant = result.scalar_one_or_none()

        if not tenant:
            raise ValueError(
                f"Tenant {tenant_id} not found for property {property_id}"
            )

        # Create pending payment record
        from ..models.payment import PaymentMethod
        
        payment = Payment(
            tenant_id=tenant_id,
            property_id=property_id,
            recorded_by=tenant.user_id,  # User who initiated the payment
            amount=amount,
            currency=tenant.property.base_currency if hasattr(tenant, 'property') else 'NPR',
            payment_method=PaymentMethod.ONLINE,
            payment_type=payment_type,
            status=PaymentStatus.PENDING,
            payment_date=date.today(),
            transaction_reference=transaction_reference,
            notes=f"Online payment via {gateway}",
            metadata={
                "gateway": gateway,
                "initiated_at": datetime.utcnow().isoformat(),
                "status": "pending",
            },
        )

        self.session.add(payment)
        await self.session.commit()
        await self.session.refresh(payment)

        logger.info(
            f"Pending payment created: payment_id={payment.id}, tenant_id={tenant_id}, "
            f"amount={amount}, gateway={gateway}, transaction_ref={transaction_reference}"
        )

        return payment

    async def calculate_balance(
        self,
        tenant_id: UUID,
        property_id: UUID,
    ) -> TenantBalanceResponse:
        """Calculate tenant's payment balance.

        Calculates total paid, total due, and outstanding balance for a tenant.

        Args:
            tenant_id: Tenant ID
            property_id: Property ID

        Returns:
            Balance calculation response

        Raises:
            ValueError: If tenant not found
        """
        # Get tenant details
        result = await self.session.execute(
            select(Tenant).where(
                Tenant.id == tenant_id,
                Tenant.property_id == property_id,
            )
        )
        tenant = result.scalar_one_or_none()

        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found for property {property_id}")

        # Calculate total paid (completed payments only)
        result = await self.session.execute(
            select(func.sum(Payment.amount)).where(
                Payment.tenant_id == tenant_id,
                Payment.property_id == property_id,
                Payment.status == PaymentStatus.COMPLETED,
            )
        )
        total_paid = result.scalar() or Decimal("0.00")

        # Get last payment details
        result = await self.session.execute(
            select(Payment)
            .where(
                Payment.tenant_id == tenant_id,
                Payment.property_id == property_id,
                Payment.status == PaymentStatus.COMPLETED,
            )
            .order_by(Payment.payment_date.desc())
            .limit(1)
        )
        last_payment = result.scalar_one_or_none()

        last_payment_date = last_payment.payment_date if last_payment else None
        last_payment_amount = last_payment.amount if last_payment else None

        # Calculate months since move-in
        move_in_date = tenant.move_in_date
        today = date.today()

        # Calculate total due based on monthly rent
        months_since_move_in = self._calculate_months_between(move_in_date, today)

        # If tenant has moved out, calculate up to move-out date
        if tenant.move_out_date:
            months_since_move_in = self._calculate_months_between(
                move_in_date, tenant.move_out_date
            )

        # Total due = monthly rent * months since move-in + security deposit
        total_due = (
            tenant.monthly_rent * Decimal(str(months_since_move_in))
        ) + tenant.security_deposit

        # Calculate outstanding balance
        outstanding_balance = total_due - total_paid

        # Calculate months behind (for rent only)
        months_behind = 0
        if last_payment_date:
            months_since_last_payment = self._calculate_months_between(last_payment_date, today)
            # Subtract 1 because payment in current month means not behind
            months_behind = max(0, months_since_last_payment - 1)
        else:
            # No payments made, calculate from move-in date
            months_behind = months_since_move_in

        return TenantBalanceResponse(
            tenant_id=tenant_id,
            property_id=property_id,
            total_paid=total_paid,
            total_due=total_due,
            outstanding_balance=outstanding_balance,
            last_payment_date=last_payment_date,
            last_payment_amount=last_payment_amount,
            months_behind=months_behind,
        )

    async def calculate_prorated_rent(
        self,
        monthly_rent: Decimal,
        move_in_date: date,
        period_start: date,
        period_end: date,
    ) -> Decimal:
        """Calculate pro-rated rent for partial month.

        Used when tenant moves in mid-month.

        Args:
            monthly_rent: Monthly rent amount
            move_in_date: Date tenant moved in
            period_start: Start of rent period
            period_end: End of rent period

        Returns:
            Pro-rated rent amount
        """
        # If move-in is before or on period start, charge full rent
        if move_in_date <= period_start:
            return monthly_rent

        # If move-in is after period end, charge nothing for this period
        if move_in_date > period_end:
            return Decimal("0.00")

        # Calculate days in period
        total_days = (period_end - period_start).days + 1

        # Calculate days tenant will occupy
        occupied_days = (period_end - move_in_date).days + 1

        # Calculate pro-rated amount
        daily_rate = monthly_rent / Decimal(str(total_days))
        prorated_amount = daily_rate * Decimal(str(occupied_days))

        # Round to 2 decimal places
        return prorated_amount.quantize(Decimal("0.01"))

    async def generate_receipt(
        self,
        payment_id: UUID,
        output_path: str,
    ) -> str:
        """Generate PDF receipt for a payment.

        Args:
            payment_id: Payment ID to generate receipt for
            output_path: Path to save the PDF file

        Returns:
            Path to generated PDF file

        Raises:
            ValueError: If payment not found
        """
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer,
                                        Table, TableStyle)

        # Get payment with related data
        result = await self.session.execute(select(Payment).where(Payment.id == payment_id))
        payment = result.scalar_one_or_none()

        if not payment:
            raise ValueError(f"Payment {payment_id} not found")

        # Get tenant and property details
        result = await self.session.execute(select(Tenant).where(Tenant.id == payment.tenant_id))
        tenant = result.scalar_one_or_none()

        from ..models.property import Property

        result = await self.session.execute(
            select(Property).where(Property.id == payment.property_id)
        )
        property_obj = result.scalar_one_or_none()

        # Create PDF
        pdf = SimpleDocTemplate(output_path, pagesize=A4)

        # Get styles
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#2C3E50"),
            spaceAfter=30,
            alignment=TA_CENTER,
        )

        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=14,
            textColor=colors.HexColor("#34495E"),
            spaceAfter=12,
            alignment=TA_LEFT,
        )

        normal_style = ParagraphStyle(
            "CustomNormal",
            parent=styles["Normal"],
            fontSize=11,
            alignment=TA_LEFT,
        )

        # Build content
        content = []

        # Title
        content.append(Paragraph("PAYMENT RECEIPT", title_style))
        content.append(Spacer(1, 20))

        # Receipt details
        receipt_data = [
            ["Receipt #:", str(payment.id)[:8].upper()],
            ["Date:", payment.payment_date.strftime("%B %d, %Y")],
            ["Status:", payment.status.value.upper()],
        ]

        receipt_table = Table(receipt_data, colWidths=[80 * mm, 80 * mm])
        receipt_table.setStyle(
            TableStyle(
                [
                    ("FONT", (0, 0), (-1, -1), "Helvetica", 10),
                    ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 10),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#2C3E50")),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )

        content.append(receipt_table)
        content.append(Spacer(1, 20))

        # Property Details
        content.append(Paragraph("Property Details", heading_style))

        property_data = [
            ["Property:", property_obj.name if property_obj else "N/A"],
            ["Address:", property_obj.address if property_obj else "N/A"],
        ]

        property_table = Table(property_data, colWidths=[80 * mm, 80 * mm])
        property_table.setStyle(
            TableStyle(
                [
                    ("FONT", (0, 0), (-1, -1), "Helvetica", 10),
                    ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 10),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#2C3E50")),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )

        content.append(property_table)
        content.append(Spacer(1, 20))

        # Tenant Details
        content.append(Paragraph("Tenant Details", heading_style))

        tenant_data = [
            ["Name:", tenant.full_name if tenant else "N/A"],
            ["Phone:", tenant.phone_number if tenant else "N/A"],
            ["Email:", tenant.email_address if tenant else "N/A"],
        ]

        tenant_table = Table(tenant_data, colWidths=[80 * mm, 80 * mm])
        tenant_table.setStyle(
            TableStyle(
                [
                    ("FONT", (0, 0), (-1, -1), "Helvetica", 10),
                    ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 10),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#2C3E50")),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )

        content.append(tenant_table)
        content.append(Spacer(1, 20))

        # Payment Details
        content.append(Paragraph("Payment Details", heading_style))

        payment_details_data = [
            ["Payment Type:", payment.payment_type.value.replace("_", " ").title()],
            ["Payment Method:", payment.payment_method.value.replace("_", " ").title()],
            ["Transaction Ref:", payment.transaction_reference or "N/A"],
        ]

        if payment.payment_period_start and payment.payment_period_end:
            payment_details_data.append(
                [
                    "Period:",
                    f"{payment.payment_period_start.strftime('%b %d, %Y')} - {payment.payment_period_end.strftime('%b %d, %Y')}",
                ]
            )

        payment_details_table = Table(payment_details_data, colWidths=[80 * mm, 80 * mm])
        payment_details_table.setStyle(
            TableStyle(
                [
                    ("FONT", (0, 0), (-1, -1), "Helvetica", 10),
                    ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 10),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#2C3E50")),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )

        content.append(payment_details_table)
        content.append(Spacer(1, 20))

        # Amount Summary
        content.append(Paragraph("Amount Summary", heading_style))

        amount_data = [
            ["Description", "Amount"],
            [
                payment.payment_type.value.replace("_", " ").title(),
                f"{payment.currency} {payment.amount:,.2f}",
            ],
            ["", ""],
            ["Total Amount Paid", f"{payment.currency} {payment.amount:,.2f}"],
        ]

        amount_table = Table(amount_data, colWidths=[120 * mm, 40 * mm])
        amount_table.setStyle(
            TableStyle(
                [
                    ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 11),
                    ("FONT", (0, 1), (-1, -2), "Helvetica", 10),
                    ("FONT", (0, -1), (-1, -1), "Helvetica-Bold", 12),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495E")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#ECF0F1")),
                    ("TEXTCOLOR", (0, -1), (-1, -1), colors.HexColor("#2C3E50")),
                    ("ALIGN", (0, 0), (0, -1), "LEFT"),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -2), 0.5, colors.grey),
                    ("BOX", (0, 0), (-1, -1), 1, colors.black),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )

        content.append(amount_table)
        content.append(Spacer(1, 30))

        # Notes
        if payment.notes:
            content.append(Paragraph("Notes", heading_style))
            content.append(Paragraph(payment.notes, normal_style))
            content.append(Spacer(1, 20))

        # Footer
        footer_style = ParagraphStyle(
            "Footer",
            parent=styles["Normal"],
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER,
        )

        content.append(Spacer(1, 30))
        content.append(
            Paragraph(
                f"This is a computer-generated receipt and does not require a signature.<br/>"
                f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
                footer_style,
            )
        )

        # Build PDF
        pdf.build(content)

        logger.info(f"Receipt generated for payment {payment_id} at {output_path}")

        return output_path

    async def auto_generate_receipt(
        self,
        payment_id: UUID,
    ) -> str | None:
        """Automatically generate receipt after successful gateway payment.

        Implements T121 from tasks.md.

        This method is called automatically when a payment gateway callback
        confirms payment completion. It generates a PDF receipt and stores
        the path in payment metadata.

        Args:
            payment_id: Payment ID to generate receipt for

        Returns:
            Path to generated PDF file, or None if generation failed
        """
        import os
        import tempfile
        from datetime import datetime

        logger.info(f"Auto-generating receipt for payment {payment_id}")

        try:
            # Get payment record
            result = await self.session.execute(select(Payment).where(Payment.id == payment_id))
            payment = result.scalar_one_or_none()

            if not payment:
                logger.error(f"Payment {payment_id} not found for receipt generation")
                return None

            # Only generate receipts for completed payments
            if payment.status != PaymentStatus.COMPLETED:
                logger.warning(
                    f"Skipping receipt generation for payment {payment_id} "
                    f"with status {payment.status.value}"
                )
                return None

            # Create temp directory for receipts if it doesn't exist
            receipts_dir = os.path.join(tempfile.gettempdir(), "meroghar_receipts")
            os.makedirs(receipts_dir, exist_ok=True)

            # Generate unique filename: receipt_{payment_id}_{timestamp}.pdf
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"receipt_{str(payment_id)[:8]}_{timestamp}.pdf"
            output_path = os.path.join(receipts_dir, filename)

            # Generate receipt PDF
            await self.generate_receipt(payment_id, output_path)

            # Update payment metadata with receipt path
            if not payment.metadata:
                payment.metadata = {}

            payment.metadata["receipt_generated"] = True
            payment.metadata["receipt_path"] = output_path
            payment.metadata["receipt_generated_at"] = timestamp
            payment.metadata["receipt_filename"] = filename

            # Commit metadata update
            await self.session.commit()
            await self.session.refresh(payment)

            logger.info(f"Receipt auto-generated for payment {payment_id}: {output_path}")

            return output_path

        except Exception as e:
            logger.exception(f"Failed to auto-generate receipt for payment {payment_id}: {e}")
            # Don't fail the payment if receipt generation fails
            return None

    def _calculate_months_between(self, start_date: date, end_date: date) -> int:
        """Calculate number of months between two dates.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Number of months (rounded up)
        """
        if end_date < start_date:
            return 0

        # Calculate difference in months
        months = (end_date.year - start_date.year) * 12
        months += end_date.month - start_date.month

        # If we're past the start day in the end month, add 1
        if end_date.day >= start_date.day:
            months += 1

        return max(0, months)


__all__ = ["PaymentService"]
