"""Bill service for managing bills, allocations, and recurring bills.

Implements T080 from tasks.md.
"""
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.bill import (
    AllocationMethod,
    Bill,
    BillAllocation,
    BillStatus,
    BillType,
    RecurringBill,
    RecurringFrequency,
)
from ..models.notification import NotificationPriority, NotificationType
from ..models.property import Property
from ..models.tenant import Tenant, TenantStatus
from ..schemas.bill import (
    BillAllocationCreateRequest,
    BillCreateRequest,
    RecurringBillCreateRequest,
)
from .notification_service import NotificationService

logger = logging.getLogger(__name__)


class BillService:
    """Service for bill-related operations."""

    def __init__(self, session: AsyncSession):
        """Initialize bill service with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def create_bill(
        self,
        request: BillCreateRequest,
        created_by: UUID,
        allocations: Optional[list[BillAllocationCreateRequest]] = None,
    ) -> Bill:
        """Create a new bill with automatic or custom allocations.
        
        Args:
            request: Bill creation request
            created_by: User ID of the person creating the bill
            allocations: Optional list of custom allocations (for custom method)
            
        Returns:
            Created bill with allocations
            
        Raises:
            ValueError: If validation fails
        """
        # Verify property exists
        result = await self.session.execute(
            select(Property).where(Property.id == request.property_id)
        )
        property_obj = result.scalar_one_or_none()
        
        if not property_obj:
            raise ValueError(f"Property {request.property_id} not found")
        
        # Validate dates
        if request.period_end <= request.period_start:
            raise ValueError("Period end must be after period start")
        
        if request.due_date < request.period_start:
            raise ValueError("Due date cannot be before period start")
        
        # Get active tenants for the property
        result = await self.session.execute(
            select(Tenant).where(
                Tenant.property_id == request.property_id,
                Tenant.status == TenantStatus.ACTIVE,
            )
        )
        active_tenants = result.scalars().all()
        
        if not active_tenants:
            raise ValueError(
                f"No active tenants found for property {request.property_id}"
            )
        
        # Create bill
        bill = Bill(
            property_id=request.property_id,
            bill_type=request.bill_type,
            total_amount=request.total_amount,
            currency=request.currency,
            period_start=request.period_start,
            period_end=request.period_end,
            due_date=request.due_date,
            status=BillStatus.PENDING,
            allocation_method=request.allocation_method,
            description=request.description,
            bill_number=request.bill_number,
            created_by=created_by,
        )
        
        self.session.add(bill)
        await self.session.flush()  # Get bill ID
        
        # Create allocations based on method
        if request.allocation_method == AllocationMethod.CUSTOM:
            if not allocations:
                raise ValueError("Custom allocation method requires allocations list")
            
            # Validate custom allocations
            await self._validate_custom_allocations(
                allocations, active_tenants, request.total_amount
            )
            
            # Create custom allocations
            for alloc_request in allocations:
                allocation = BillAllocation(
                    bill_id=bill.id,
                    tenant_id=alloc_request.tenant_id,
                    allocated_amount=alloc_request.allocated_amount,
                    percentage=alloc_request.percentage,
                    notes=alloc_request.notes,
                )
                self.session.add(allocation)
        else:
            # Automatic allocation
            await self._create_automatic_allocations(
                bill, active_tenants, request.allocation_method, allocations
            )
        
        await self.session.commit()
        
        # Reload bill with allocations
        result = await self.session.execute(
            select(Bill)
            .options(selectinload(Bill.allocations))
            .where(Bill.id == bill.id)
        )
        bill = result.scalar_one()
        
        logger.info(
            f"Bill created: bill_id={bill.id}, property_id={request.property_id}, "
            f"type={request.bill_type.value}, amount={request.total_amount}, "
            f"method={request.allocation_method.value}, allocations={len(bill.allocations)}, "
            f"created_by={created_by}"
        )
        
        # T243: Send bill creation notifications to affected tenants
        try:
            for allocation in bill.allocations:
                await NotificationService.create_notification(
                    db=self.session,
                    user_id=allocation.tenant.user_id,
                    title="New Bill Created",
                    body=(
                        f"A new {bill.bill_type.value} bill of "
                        f"{bill.currency} {allocation.allocated_amount} has been created. "
                        f"Due date: {bill.due_date.strftime('%Y-%m-%d')}"
                    ),
                    notification_type=NotificationType.BILL_CREATED,
                    priority=NotificationPriority.NORMAL,
                    deep_link=f"meroghar://bills/{bill.id}",
                    metadata={
                        "bill_id": str(bill.id),
                        "allocation_id": str(allocation.id),
                        "allocated_amount": float(allocation.allocated_amount),
                        "due_date": bill.due_date.isoformat(),
                    },
                    send_push=True,
                )
            logger.info(f"Bill notifications sent for bill {bill.id}")
        except Exception as e:
            # Don't fail bill creation if notification fails
            logger.error(f"Failed to send bill notifications: {e}")
        
        return bill

    async def _validate_custom_allocations(
        self,
        allocations: list[BillAllocationCreateRequest],
        active_tenants: list[Tenant],
        total_amount: Decimal,
    ) -> None:
        """Validate custom allocations.
        
        Args:
            allocations: List of allocation requests
            active_tenants: List of active tenants
            total_amount: Total bill amount
            
        Raises:
            ValueError: If validation fails
        """
        tenant_ids = {tenant.id for tenant in active_tenants}
        
        # Check all tenants in allocations are active
        for alloc in allocations:
            if alloc.tenant_id not in tenant_ids:
                raise ValueError(
                    f"Tenant {alloc.tenant_id} is not an active tenant for this property"
                )
        
        # Check sum of allocations equals total amount (within 0.01 tolerance)
        total_allocated = sum(alloc.allocated_amount for alloc in allocations)
        difference = abs(total_allocated - total_amount)
        
        if difference > Decimal("0.01"):
            raise ValueError(
                f"Sum of allocations ({total_allocated}) does not equal total amount ({total_amount})"
            )
        
        # If percentages provided, check they sum to 100 (within 0.01 tolerance)
        if any(alloc.percentage is not None for alloc in allocations):
            percentages_provided = [
                alloc.percentage for alloc in allocations if alloc.percentage is not None
            ]
            
            if len(percentages_provided) != len(allocations):
                raise ValueError("If using percentages, all allocations must have percentages")
            
            total_percentage = sum(percentages_provided)
            percentage_diff = abs(total_percentage - Decimal("100"))
            
            if percentage_diff > Decimal("0.01"):
                raise ValueError(
                    f"Sum of percentages ({total_percentage}) does not equal 100%"
                )

    async def _create_automatic_allocations(
        self,
        bill: Bill,
        active_tenants: list[Tenant],
        method: AllocationMethod,
        custom_percentages: Optional[list[BillAllocationCreateRequest]] = None,
    ) -> None:
        """Create automatic allocations based on method.
        
        Args:
            bill: Bill to create allocations for
            active_tenants: List of active tenants
            method: Allocation method
            custom_percentages: Optional custom percentages for PERCENTAGE method
        """
        tenant_count = len(active_tenants)
        
        if method == AllocationMethod.EQUAL:
            # T080: Equal division with proper rounding
            # Divide equally, round each share to 2 decimals
            equal_share = (bill.total_amount / tenant_count).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            
            # Calculate total allocated and remainder
            total_allocated = equal_share * tenant_count
            remainder = bill.total_amount - total_allocated
            
            # Allocate equal shares
            for i, tenant in enumerate(active_tenants):
                # Add remainder to last tenant to ensure exact total
                allocated_amount = equal_share
                if i == tenant_count - 1:
                    allocated_amount += remainder
                
                percentage = (allocated_amount / bill.total_amount * 100).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                
                allocation = BillAllocation(
                    bill_id=bill.id,
                    tenant_id=tenant.id,
                    allocated_amount=allocated_amount,
                    percentage=percentage,
                    notes=f"Equal share ({tenant_count} tenants)",
                )
                self.session.add(allocation)
        
        elif method == AllocationMethod.PERCENTAGE:
            # T080: Percentage-based division
            if not custom_percentages:
                raise ValueError("Percentage method requires custom percentages")
            
            # Create percentage map
            percentage_map = {
                alloc.tenant_id: alloc.percentage
                for alloc in custom_percentages
            }
            
            # Validate all tenants have percentages
            for tenant in active_tenants:
                if tenant.id not in percentage_map:
                    raise ValueError(
                        f"Missing percentage for tenant {tenant.id}"
                    )
            
            # Validate percentages sum to 100
            total_percentage = sum(percentage_map.values())
            if abs(total_percentage - Decimal("100")) > Decimal("0.01"):
                raise ValueError(
                    f"Percentages must sum to 100%, got {total_percentage}%"
                )
            
            # Calculate amounts with proper rounding
            allocated_amounts = []
            for tenant in active_tenants:
                percentage = percentage_map[tenant.id]
                amount = (bill.total_amount * percentage / 100).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                allocated_amounts.append((tenant, percentage, amount))
            
            # Adjust last allocation for rounding errors
            total_allocated = sum(amount for _, _, amount in allocated_amounts)
            remainder = bill.total_amount - total_allocated
            
            if remainder != 0:
                # Add remainder to largest allocation
                tenant, percentage, amount = allocated_amounts[-1]
                allocated_amounts[-1] = (tenant, percentage, amount + remainder)
            
            # Create allocations
            for tenant, percentage, amount in allocated_amounts:
                allocation = BillAllocation(
                    bill_id=bill.id,
                    tenant_id=tenant.id,
                    allocated_amount=amount,
                    percentage=percentage,
                    notes=f"{percentage}% of total",
                )
                self.session.add(allocation)
        
        elif method == AllocationMethod.FIXED_AMOUNT:
            # T080: Fixed amount per tenant (equal division)
            # This is similar to EQUAL but explicitly states it's a fixed amount
            equal_share = (bill.total_amount / tenant_count).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            
            total_allocated = equal_share * tenant_count
            remainder = bill.total_amount - total_allocated
            
            for i, tenant in enumerate(active_tenants):
                allocated_amount = equal_share
                if i == tenant_count - 1:
                    allocated_amount += remainder
                
                percentage = (allocated_amount / bill.total_amount * 100).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                
                allocation = BillAllocation(
                    bill_id=bill.id,
                    tenant_id=tenant.id,
                    allocated_amount=allocated_amount,
                    percentage=percentage,
                    notes=f"Fixed amount: ₹{allocated_amount}",
                )
                self.session.add(allocation)

    async def update_bill_status(
        self,
        bill_id: UUID,
        status: BillStatus,
    ) -> Bill:
        """Update bill status based on allocation payments.
        
        Args:
            bill_id: Bill ID
            status: New status
            
        Returns:
            Updated bill
            
        Raises:
            ValueError: If bill not found
        """
        result = await self.session.execute(
            select(Bill)
            .options(selectinload(Bill.allocations))
            .where(Bill.id == bill_id)
        )
        bill = result.scalar_one_or_none()
        
        if not bill:
            raise ValueError(f"Bill {bill_id} not found")
        
        # Auto-calculate status based on allocations if not explicitly set
        if status == BillStatus.PENDING:
            paid_count = sum(1 for alloc in bill.allocations if alloc.is_paid)
            
            if paid_count == 0:
                bill.status = BillStatus.PENDING
            elif paid_count == len(bill.allocations):
                bill.status = BillStatus.PAID
                bill.paid_date = date.today()
            else:
                bill.status = BillStatus.PARTIALLY_PAID
        else:
            bill.status = status
            if status == BillStatus.PAID:
                bill.paid_date = date.today()
        
        await self.session.commit()
        await self.session.refresh(bill)
        
        logger.info(f"Bill status updated: bill_id={bill_id}, status={bill.status.value}")
        
        return bill

    async def mark_allocation_paid(
        self,
        allocation_id: UUID,
        payment_id: Optional[UUID] = None,
    ) -> BillAllocation:
        """Mark a bill allocation as paid.
        
        Args:
            allocation_id: Allocation ID
            payment_id: Optional payment ID
            
        Returns:
            Updated allocation
            
        Raises:
            ValueError: If allocation not found
        """
        result = await self.session.execute(
            select(BillAllocation).where(BillAllocation.id == allocation_id)
        )
        allocation = result.scalar_one_or_none()
        
        if not allocation:
            raise ValueError(f"Allocation {allocation_id} not found")
        
        allocation.is_paid = True
        allocation.paid_date = date.today()
        allocation.payment_id = payment_id
        
        await self.session.commit()
        await self.session.refresh(allocation)
        
        # Update bill status
        await self.update_bill_status(allocation.bill_id, BillStatus.PENDING)
        
        logger.info(
            f"Allocation marked paid: allocation_id={allocation_id}, "
            f"payment_id={payment_id}"
        )
        
        return allocation

    async def create_recurring_bill(
        self,
        request: RecurringBillCreateRequest,
        created_by: UUID,
    ) -> RecurringBill:
        """Create a recurring bill template.
        
        Args:
            request: Recurring bill creation request
            created_by: User ID of the person creating the template
            
        Returns:
            Created recurring bill template
            
        Raises:
            ValueError: If property not found
        """
        # Verify property exists
        result = await self.session.execute(
            select(Property).where(Property.id == request.property_id)
        )
        property_obj = result.scalar_one_or_none()
        
        if not property_obj:
            raise ValueError(f"Property {request.property_id} not found")
        
        # Calculate next generation date
        next_generation = self._calculate_next_generation_date(
            request.frequency, request.day_of_month
        )
        
        # Create recurring bill
        recurring_bill = RecurringBill(
            property_id=request.property_id,
            bill_type=request.bill_type,
            frequency=request.frequency,
            allocation_method=request.allocation_method,
            estimated_amount=request.estimated_amount,
            currency=request.currency,
            day_of_month=request.day_of_month,
            description=request.description,
            is_active=request.is_active,
            next_generation=next_generation,
            created_by=created_by,
        )
        
        self.session.add(recurring_bill)
        await self.session.commit()
        await self.session.refresh(recurring_bill)
        
        logger.info(
            f"Recurring bill created: id={recurring_bill.id}, "
            f"property_id={request.property_id}, type={request.bill_type.value}, "
            f"frequency={request.frequency.value}, next_generation={next_generation}"
        )
        
        return recurring_bill

    def _calculate_next_generation_date(
        self,
        frequency: RecurringFrequency,
        day_of_month: int,
    ) -> date:
        """Calculate next bill generation date.
        
        Args:
            frequency: Bill frequency
            day_of_month: Day of month to generate (1-31)
            
        Returns:
            Next generation date
        """
        today = date.today()
        current_month = today.month
        current_year = today.year
        
        # Try current month first
        try:
            next_date = date(current_year, current_month, min(day_of_month, 28))
        except ValueError:
            # Invalid day for this month, use last day of month
            if current_month == 12:
                next_date = date(current_year, 12, 31)
            else:
                next_date = date(current_year, current_month + 1, 1) - timedelta(days=1)
        
        # If date has passed, move to next period
        if next_date <= today:
            if frequency == RecurringFrequency.MONTHLY:
                # Move to next month
                if current_month == 12:
                    next_date = date(current_year + 1, 1, min(day_of_month, 28))
                else:
                    next_date = date(current_year, current_month + 1, min(day_of_month, 28))
            
            elif frequency == RecurringFrequency.QUARTERLY:
                # Move to next quarter
                next_month = current_month + 3
                next_year = current_year
                if next_month > 12:
                    next_month -= 12
                    next_year += 1
                next_date = date(next_year, next_month, min(day_of_month, 28))
            
            elif frequency == RecurringFrequency.YEARLY:
                # Move to next year
                next_date = date(current_year + 1, current_month, min(day_of_month, 28))
        
        return next_date

    async def generate_bills_from_recurring(
        self,
        recurring_bill_id: Optional[UUID] = None,
    ) -> list[Bill]:
        """Generate bills from recurring bill templates.
        
        Args:
            recurring_bill_id: Optional specific recurring bill ID, or None for all due
            
        Returns:
            List of generated bills
        """
        # Get recurring bills due for generation
        query = select(RecurringBill).where(
            RecurringBill.is_active == True,
            RecurringBill.next_generation <= date.today(),
        )
        
        if recurring_bill_id:
            query = query.where(RecurringBill.id == recurring_bill_id)
        
        result = await self.session.execute(query)
        recurring_bills = result.scalars().all()
        
        generated_bills = []
        
        for recurring in recurring_bills:
            # Calculate period dates
            period_start = recurring.next_generation.replace(day=1)
            
            if recurring.frequency == RecurringFrequency.MONTHLY:
                # Last day of month
                if period_start.month == 12:
                    period_end = date(period_start.year + 1, 1, 1) - timedelta(days=1)
                else:
                    period_end = date(period_start.year, period_start.month + 1, 1) - timedelta(days=1)
            
            elif recurring.frequency == RecurringFrequency.QUARTERLY:
                # 3 months
                month = period_start.month + 3
                year = period_start.year
                if month > 12:
                    month -= 12
                    year += 1
                period_end = date(year, month, 1) - timedelta(days=1)
            
            elif recurring.frequency == RecurringFrequency.YEARLY:
                # 1 year
                period_end = date(period_start.year + 1, 1, 1) - timedelta(days=1)
            
            # Due date is 10 days after period end
            due_date = period_end + timedelta(days=10)
            
            # Create bill request
            bill_request = BillCreateRequest(
                property_id=recurring.property_id,
                bill_type=recurring.bill_type,
                total_amount=recurring.estimated_amount,
                currency=recurring.currency,
                period_start=period_start,
                period_end=period_end,
                due_date=due_date,
                allocation_method=recurring.allocation_method,
                description=f"{recurring.description} (Auto-generated from recurring template)",
            )
            
            # Create bill
            try:
                bill = await self.create_bill(
                    bill_request,
                    created_by=recurring.created_by,
                )
                
                generated_bills.append(bill)
                
                # Update recurring bill
                recurring.last_generated = date.today()
                recurring.next_generation = self._calculate_next_generation_date(
                    recurring.frequency, recurring.day_of_month
                )
                
            except Exception as e:
                logger.error(
                    f"Failed to generate bill from recurring {recurring.id}: {str(e)}"
                )
        
        await self.session.commit()
        
        logger.info(f"Generated {len(generated_bills)} bills from recurring templates")
        
        return generated_bills


__all__ = ["BillService"]
