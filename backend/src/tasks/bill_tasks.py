"""Celery tasks for bill management.

Implements T086 from tasks.md.
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import async_session_maker
from ..models.bill import Bill, RecurringBill, RecurringFrequency
from ..models.property import Property
from ..models.tenant import Tenant, TenantStatus
from ..schemas.bill import BillCreateRequest
from ..services.bill_service import BillService
from .celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="src.tasks.bill_tasks.generate_recurring_bills", bind=True)
def generate_recurring_bills(self):
    """Generate bills from recurring bill templates.

    This task runs monthly and creates bills for all active recurring bill templates
    that are due for generation.

    Returns:
        dict: Summary of bills generated
    """
    import asyncio

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(_generate_recurring_bills_async())
    return result


async def _generate_recurring_bills_async() -> dict:
    """Async implementation of recurring bill generation."""
    bills_generated = 0
    errors = []
    today = date.today()

    async with async_session_maker() as session:
        try:
            # Get all active recurring bills that need generation
            result = await session.execute(
                select(RecurringBill).where(
                    and_(
                        RecurringBill.is_active,
                        RecurringBill.next_generation <= today,
                    )
                )
            )
            recurring_bills = result.scalars().all()

            logger.info(f"Found {len(recurring_bills)} recurring bills to process")

            for recurring_bill in recurring_bills:
                try:
                    await _generate_bill_from_template(session, recurring_bill, today)
                    bills_generated += 1
                    logger.info(
                        f"Generated bill for recurring template {recurring_bill.id} "
                        f"(Property: {recurring_bill.property_id})"
                    )
                except Exception as e:
                    error_msg = (
                        f"Failed to generate bill from template {recurring_bill.id}: {str(e)}"
                    )
                    logger.error(error_msg, exc_info=True)
                    errors.append(error_msg)

            await session.commit()

            logger.info(
                f"Recurring bill generation complete. "
                f"Generated: {bills_generated}, Errors: {len(errors)}"
            )

            return {
                "status": "completed",
                "bills_generated": bills_generated,
                "errors": errors,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to generate recurring bills: {str(e)}", exc_info=True)
            await session.rollback()
            return {
                "status": "failed",
                "bills_generated": bills_generated,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }


async def _generate_bill_from_template(
    session: AsyncSession,
    recurring_bill: RecurringBill,
    generation_date: date,
) -> Bill:
    """Generate a bill from a recurring bill template.

    Args:
        session: Database session
        recurring_bill: Recurring bill template
        generation_date: Date to generate the bill for

    Returns:
        Generated bill

    Raises:
        ValueError: If bill generation fails
    """
    # Calculate billing period based on frequency
    period_start, period_end = _calculate_billing_period(recurring_bill.frequency, generation_date)

    # Calculate due date
    due_date = period_end + timedelta(days=10)  # 10 days after period ends

    # Get active tenants for the property
    result = await session.execute(
        select(Tenant).where(
            and_(
                Tenant.property_id == recurring_bill.property_id,
                Tenant.status == TenantStatus.ACTIVE,
            )
        )
    )
    active_tenants = result.scalars().all()

    if not active_tenants:
        logger.warning(
            f"No active tenants found for recurring bill {recurring_bill.id}. "
            f"Skipping generation."
        )
        raise ValueError(f"No active tenants for property {recurring_bill.property_id}")

    # Get property for currency
    result = await session.execute(
        select(Property).where(Property.id == recurring_bill.property_id)
    )
    property_obj = result.scalar_one()

    # Create bill request
    bill_request = BillCreateRequest(
        property_id=recurring_bill.property_id,
        bill_type=recurring_bill.bill_type,
        total_amount=recurring_bill.estimated_amount or Decimal("0.00"),
        currency=property_obj.base_currency,
        period_start=period_start,
        period_end=period_end,
        due_date=due_date,
        allocation_method=recurring_bill.allocation_method,
        description=f"Auto-generated from recurring template: {recurring_bill.description or recurring_bill.bill_type.value}",
    )

    # Use bill service to create the bill with allocations
    bill_service = BillService(session)
    bill = await bill_service.create_bill(
        request=bill_request,
        created_by=recurring_bill.created_by,
        allocations=None,  # Use automatic allocation
    )

    # Update recurring bill's next generation date
    recurring_bill.last_generated = generation_date
    recurring_bill.next_generation = _calculate_next_generation_date(
        recurring_bill.frequency, generation_date
    )

    session.add(recurring_bill)

    return bill


def _calculate_billing_period(
    frequency: RecurringFrequency, reference_date: date
) -> tuple[date, date]:
    """Calculate billing period start and end dates.

    Args:
        frequency: Billing frequency
        reference_date: Reference date for calculation

    Returns:
        Tuple of (period_start, period_end)
    """
    if frequency == RecurringFrequency.MONTHLY:
        # Previous month
        if reference_date.month == 1:
            period_start = date(reference_date.year - 1, 12, 1)
            period_end = date(reference_date.year - 1, 12, 31)
        else:
            period_start = date(reference_date.year, reference_date.month - 1, 1)
            # Last day of previous month
            period_end = date(reference_date.year, reference_date.month, 1) - timedelta(days=1)

    elif frequency == RecurringFrequency.QUARTERLY:
        # Previous quarter
        current_quarter = (reference_date.month - 1) // 3 + 1
        if current_quarter == 1:
            period_start = date(reference_date.year - 1, 10, 1)
            period_end = date(reference_date.year - 1, 12, 31)
        else:
            quarter_start_month = (current_quarter - 2) * 3 + 1
            period_start = date(reference_date.year, quarter_start_month, 1)
            quarter_end_month = quarter_start_month + 2
            period_end = date(reference_date.year, quarter_end_month + 1, 1) - timedelta(days=1)

    elif frequency == RecurringFrequency.YEARLY:
        # Previous year
        period_start = date(reference_date.year - 1, 1, 1)
        period_end = date(reference_date.year - 1, 12, 31)

    else:
        raise ValueError(f"Unsupported frequency: {frequency}")

    return period_start, period_end


def _calculate_next_generation_date(frequency: RecurringFrequency, current_date: date) -> date:
    """Calculate next bill generation date.

    Args:
        frequency: Billing frequency
        current_date: Current generation date

    Returns:
        Next generation date
    """
    if frequency == RecurringFrequency.MONTHLY:
        # First day of next month
        if current_date.month == 12:
            return date(current_date.year + 1, 1, 1)
        else:
            return date(current_date.year, current_date.month + 1, 1)

    elif frequency == RecurringFrequency.QUARTERLY:
        # First day of next quarter (3 months later)
        month = current_date.month + 3
        year = current_date.year
        if month > 12:
            month -= 12
            year += 1
        return date(year, month, 1)

    elif frequency == RecurringFrequency.YEARLY:
        # First day of next year
        return date(current_date.year + 1, 1, 1)

    else:
        raise ValueError(f"Unsupported frequency: {frequency}")


@celery_app.task(name="src.tasks.bill_tasks.check_overdue_bills", bind=True)
def check_overdue_bills(self):
    """Check for overdue bills and update their status.

    This task runs daily and marks bills as overdue if their due date has passed
    and they haven't been fully paid.

    Returns:
        dict: Summary of bills marked as overdue
    """
    import asyncio

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(_check_overdue_bills_async())
    return result


async def _check_overdue_bills_async() -> dict:
    """Async implementation of overdue bill check."""
    from ..models.bill import BillStatus

    bills_updated = 0
    today = date.today()

    async with async_session_maker() as session:
        try:
            # Get all pending or partially paid bills with due date in the past
            result = await session.execute(
                select(Bill).where(
                    and_(
                        Bill.due_date < today,
                        Bill.status.in_([BillStatus.PENDING, BillStatus.PARTIALLY_PAID]),
                    )
                )
            )
            overdue_bills = result.scalars().all()

            logger.info(f"Found {len(overdue_bills)} overdue bills to update")

            for bill in overdue_bills:
                bill.status = BillStatus.OVERDUE
                session.add(bill)
                bills_updated += 1

            await session.commit()

            logger.info(f"Updated {bills_updated} bills to overdue status")

            return {
                "status": "completed",
                "bills_updated": bills_updated,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to check overdue bills: {str(e)}", exc_info=True)
            await session.rollback()
            return {
                "status": "failed",
                "bills_updated": bills_updated,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }


__all__ = [
    "generate_recurring_bills",
    "check_overdue_bills",
]
