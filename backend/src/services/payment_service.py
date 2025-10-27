"""Payment service for recording payments and calculating balances.

Implements T060 from tasks.md.
"""
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.payment import Payment, PaymentStatus, PaymentType
from ..models.tenant import Tenant, TenantStatus
from ..schemas.payment import (
    PaymentCreateRequest,
    PaymentResponse,
    TenantBalanceResponse,
)

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
            raise ValueError(
                f"Cannot record payment for inactive tenant {request.tenant_id}"
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
        
        logger.info(
            f"Payment recorded: payment_id={payment.id}, tenant_id={request.tenant_id}, "
            f"amount={request.amount}, type={request.payment_type.value}, "
            f"recorded_by={recorded_by}"
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
            raise ValueError(
                f"Tenant {tenant_id} not found for property {property_id}"
            )
        
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
        total_due = (tenant.monthly_rent * Decimal(str(months_since_move_in))) + tenant.security_deposit
        
        # Calculate outstanding balance
        outstanding_balance = total_due - total_paid
        
        # Calculate months behind (for rent only)
        months_behind = 0
        if last_payment_date:
            months_since_last_payment = self._calculate_months_between(
                last_payment_date, today
            )
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
