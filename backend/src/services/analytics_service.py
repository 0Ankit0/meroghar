"""Analytics service for aggregating financial data and generating insights.

Implements T095 from tasks.md.
"""

import logging
from datetime import date, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.cache import CACHE_TTL, cached
from ..models.bill import Bill
from ..models.payment import Payment, PaymentStatus, PaymentType
from ..models.property import Property
from ..models.tenant import Tenant

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for analytics and reporting operations."""

    def __init__(self, session: AsyncSession):
        """Initialize analytics service with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    @cached(ttl=CACHE_TTL["medium"], key_prefix="analytics:rent_trends")
    async def get_rent_collection_trends(
        self,
        user_id: UUID,
        property_id: UUID | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict[str, Any]]:
        """Get rent collection trends over time.

        Args:
            user_id: Owner/intermediary user ID
            property_id: Optional property filter
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            List of monthly rent collection data with totals
        """
        # Default to last 12 months if no date range specified
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=365)

        # Build query for payments grouped by month
        query = (
            select(
                func.date_trunc("month", Payment.payment_date).label("month"),
                func.sum(Payment.amount).label("total_collected"),
                func.count(Payment.id).label("payment_count"),
                func.sum(
                    case(
                        (Payment.payment_status == PaymentStatus.COMPLETED, Payment.amount), else_=0
                    )
                ).label("completed_amount"),
                func.sum(
                    case((Payment.payment_status == PaymentStatus.PENDING, Payment.amount), else_=0)
                ).label("pending_amount"),
            )
            .join(Tenant, Payment.tenant_id == Tenant.id)
            .join(Property, Tenant.property_id == Property.id)
            .where(
                and_(
                    Payment.payment_date >= start_date,
                    Payment.payment_date <= end_date,
                    Payment.payment_type == PaymentType.RENT,
                    or_(
                        Property.owner_id == user_id,
                        Property.id.in_(
                            select(Property.id)
                            .join_from(Property, Property.assignments)
                            .where(
                                Property.assignments.any(intermediary_id=user_id, is_active=True)
                            )
                        ),
                    ),
                )
            )
            .group_by(func.date_trunc("month", Payment.payment_date))
            .order_by(func.date_trunc("month", Payment.payment_date))
        )

        if property_id:
            query = query.where(Property.id == property_id)

        result = await self.session.execute(query)
        rows = result.all()

        return [
            {
                "month": row.month.isoformat() if row.month else None,
                "total_collected": float(row.total_collected or 0),
                "payment_count": row.payment_count or 0,
                "completed_amount": float(row.completed_amount or 0),
                "pending_amount": float(row.pending_amount or 0),
            }
            for row in rows
        ]

    @cached(ttl=CACHE_TTL["medium"], key_prefix="analytics:payment_status")
    async def get_payment_status_overview(
        self,
        user_id: UUID,
        property_id: UUID | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, Any]:
        """Get overview of payment status (completed, pending, overdue).

        Args:
            user_id: Owner/intermediary user ID
            property_id: Optional property filter
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            Dictionary with payment status breakdown
        """
        # Default to current month if no date range
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = date(end_date.year, end_date.month, 1)

        # Build base query
        base_conditions = [
            Payment.payment_date >= start_date,
            Payment.payment_date <= end_date,
            or_(
                Property.owner_id == user_id,
                Property.id.in_(
                    select(Property.id)
                    .join_from(Property, Property.assignments)
                    .where(Property.assignments.any(intermediary_id=user_id, is_active=True))
                ),
            ),
        ]

        if property_id:
            base_conditions.append(Property.id == property_id)

        # Query for payment status aggregation
        query = (
            select(
                Payment.payment_status,
                func.count(Payment.id).label("count"),
                func.sum(Payment.amount).label("total_amount"),
            )
            .join(Tenant, Payment.tenant_id == Tenant.id)
            .join(Property, Tenant.property_id == Property.id)
            .where(and_(*base_conditions))
            .group_by(Payment.payment_status)
        )

        result = await self.session.execute(query)
        rows = result.all()

        status_data = {
            "completed": {"count": 0, "amount": 0.0},
            "pending": {"count": 0, "amount": 0.0},
            "failed": {"count": 0, "amount": 0.0},
        }

        for row in rows:
            status_key = row.payment_status.value.lower()
            if status_key in status_data:
                status_data[status_key] = {
                    "count": row.count,
                    "amount": float(row.total_amount or 0),
                }

        # Calculate total
        total_count = sum(data["count"] for data in status_data.values())
        total_amount = sum(data["amount"] for data in status_data.values())

        return {
            "status_breakdown": status_data,
            "total_count": total_count,
            "total_amount": total_amount,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
        }

    @cached(ttl=CACHE_TTL["long"], key_prefix="analytics:expense_breakdown")
    async def get_expense_breakdown(
        self,
        user_id: UUID,
        property_id: UUID | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict[str, Any]]:
        """Get expense breakdown by bill type.

        Args:
            user_id: Owner/intermediary user ID
            property_id: Optional property filter
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            List of expense data grouped by bill type
        """
        # Default to current year if no date range
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = date(end_date.year, 1, 1)

        # Build base conditions
        base_conditions = [
            Bill.bill_date >= start_date,
            Bill.bill_date <= end_date,
            or_(
                Property.owner_id == user_id,
                Property.id.in_(
                    select(Property.id)
                    .join_from(Property, Property.assignments)
                    .where(Property.assignments.any(intermediary_id=user_id, is_active=True))
                ),
            ),
        ]

        if property_id:
            base_conditions.append(Property.id == property_id)

        # Query for expense breakdown by bill type
        query = (
            select(
                Bill.bill_type,
                func.count(Bill.id).label("bill_count"),
                func.sum(Bill.total_amount).label("total_amount"),
                func.avg(Bill.total_amount).label("average_amount"),
            )
            .join(Property, Bill.property_id == Property.id)
            .where(and_(*base_conditions))
            .group_by(Bill.bill_type)
            .order_by(func.sum(Bill.total_amount).desc())
        )

        result = await self.session.execute(query)
        rows = result.all()

        total = sum(float(row.total_amount or 0) for row in rows)

        return [
            {
                "bill_type": row.bill_type.value,
                "bill_count": row.bill_count,
                "total_amount": float(row.total_amount or 0),
                "average_amount": float(row.average_amount or 0),
                "percentage": (float(row.total_amount or 0) / total * 100) if total > 0 else 0,
            }
            for row in rows
        ]

    @cached(ttl=CACHE_TTL["long"], key_prefix="analytics:revenue_vs_expenses")
    async def get_revenue_vs_expenses(
        self,
        user_id: UUID,
        property_id: UUID | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, Any]:
        """Get revenue (rent collected) vs expenses (bills) comparison.

        Args:
            user_id: Owner/intermediary user ID
            property_id: Optional property filter
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            Dictionary with revenue, expenses, and net profit
        """
        # Default to current year if no date range
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = date(end_date.year, 1, 1)

        # Build base property filter
        property_filter = or_(
            Property.owner_id == user_id,
            Property.id.in_(
                select(Property.id)
                .join_from(Property, Property.assignments)
                .where(Property.assignments.any(intermediary_id=user_id, is_active=True))
            ),
        )

        # Query for revenue (completed rent payments)
        revenue_query = (
            select(
                func.sum(Payment.amount).label("total_revenue"),
                func.count(Payment.id).label("payment_count"),
            )
            .join(Tenant, Payment.tenant_id == Tenant.id)
            .join(Property, Tenant.property_id == Property.id)
            .where(
                and_(
                    Payment.payment_date >= start_date,
                    Payment.payment_date <= end_date,
                    Payment.payment_type == PaymentType.RENT,
                    Payment.payment_status == PaymentStatus.COMPLETED,
                    property_filter,
                    Property.id == property_id if property_id else True,
                )
            )
        )

        revenue_result = await self.session.execute(revenue_query)
        revenue_row = revenue_result.one()

        # Query for expenses (bills)
        expense_query = (
            select(
                func.sum(Bill.total_amount).label("total_expenses"),
                func.count(Bill.id).label("bill_count"),
            )
            .join(Property, Bill.property_id == Property.id)
            .where(
                and_(
                    Bill.bill_date >= start_date,
                    Bill.bill_date <= end_date,
                    property_filter,
                    Property.id == property_id if property_id else True,
                )
            )
        )

        expense_result = await self.session.execute(expense_query)
        expense_row = expense_result.one()

        total_revenue = float(revenue_row.total_revenue or 0)
        total_expenses = float(expense_row.total_expenses or 0)
        net_profit = total_revenue - total_expenses
        profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0

        return {
            "revenue": {
                "total": total_revenue,
                "payment_count": revenue_row.payment_count or 0,
            },
            "expenses": {
                "total": total_expenses,
                "bill_count": expense_row.bill_count or 0,
            },
            "net_profit": net_profit,
            "profit_margin": profit_margin,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
        }

    @cached(ttl=CACHE_TTL["long"], key_prefix="analytics:property_performance")
    async def get_property_performance(
        self,
        user_id: UUID,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict[str, Any]]:
        """Get performance comparison across all properties.

        Args:
            user_id: Owner/intermediary user ID
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            List of property performance data
        """
        # Default to current year if no date range
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = date(end_date.year, 1, 1)

        # Query for property performance
        query = (
            select(
                Property.id,
                Property.name,
                Property.address,
                func.count(func.distinct(Tenant.id)).label("tenant_count"),
                func.sum(
                    case(
                        (
                            and_(
                                Payment.payment_date >= start_date,
                                Payment.payment_date <= end_date,
                                Payment.payment_status == PaymentStatus.COMPLETED,
                            ),
                            Payment.amount,
                        ),
                        else_=0,
                    )
                ).label("total_revenue"),
                func.sum(
                    case(
                        (
                            and_(
                                Bill.bill_date >= start_date,
                                Bill.bill_date <= end_date,
                            ),
                            Bill.total_amount,
                        ),
                        else_=0,
                    )
                ).label("total_expenses"),
            )
            .outerjoin(Tenant, Property.id == Tenant.property_id)
            .outerjoin(Payment, Tenant.id == Payment.tenant_id)
            .outerjoin(Bill, Property.id == Bill.property_id)
            .where(
                or_(
                    Property.owner_id == user_id,
                    Property.id.in_(
                        select(Property.id)
                        .join_from(Property, Property.assignments)
                        .where(Property.assignments.any(intermediary_id=user_id, is_active=True))
                    ),
                )
            )
            .group_by(Property.id, Property.name, Property.address)
            .order_by(
                func.sum(
                    case(
                        (
                            and_(
                                Payment.payment_date >= start_date,
                                Payment.payment_date <= end_date,
                                Payment.payment_status == PaymentStatus.COMPLETED,
                            ),
                            Payment.amount,
                        ),
                        else_=0,
                    )
                ).desc()
            )
        )

        result = await self.session.execute(query)
        rows = result.all()

        return [
            {
                "property_id": str(row.id),
                "property_name": row.name,
                "property_address": row.address,
                "tenant_count": row.tenant_count or 0,
                "total_revenue": float(row.total_revenue or 0),
                "total_expenses": float(row.total_expenses or 0),
                "net_profit": float((row.total_revenue or 0) - (row.total_expenses or 0)),
                "occupancy_rate": 100.0,  # TODO: Calculate based on units when implemented
            }
            for row in rows
        ]
