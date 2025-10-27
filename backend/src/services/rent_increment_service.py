"""Rent increment service for automatic rent calculations.

Implements T194 from tasks.md.
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from ..models.tenant import Tenant


class RentIncrementService:
    """Service for managing automatic rent increments.
    
    Features:
    - Calculate rent increments based on policy (percentage or fixed amount)
    - Apply rent increments with history tracking
    - Check for due increments
    - Preview upcoming increments
    - Support manual overrides
    """

    def __init__(self, db: Session):
        self.db = db

    def calculate_increment(
        self,
        current_rent: Decimal,
        policy: Dict,
    ) -> Decimal:
        """Calculate new rent amount based on increment policy.
        
        Args:
            current_rent: Current monthly rent amount
            policy: Increment policy dict with 'type' and 'value'
                   type: 'percentage' or 'fixed'
                   value: increment amount (5 for 5%, or fixed amount)
        
        Returns:
            New rent amount rounded to 2 decimal places
        """
        increment_type = policy.get("type", "percentage")
        increment_value = Decimal(str(policy.get("value", 0)))

        if increment_type == "percentage":
            # Calculate percentage increase
            increment_amount = current_rent * (increment_value / Decimal("100"))
            new_rent = current_rent + increment_amount
        elif increment_type == "fixed":
            # Fixed amount increase
            new_rent = current_rent + increment_value
        else:
            raise ValueError(f"Invalid increment type: {increment_type}")

        return new_rent.quantize(Decimal("0.01"))

    def calculate_next_increment_date(
        self,
        move_in_date: date,
        interval_years: int,
        last_increment_date: Optional[date] = None,
    ) -> date:
        """Calculate the next increment date based on interval.
        
        Args:
            move_in_date: Tenant's move-in date
            interval_years: Years between increments
            last_increment_date: Date of last increment (if any)
        
        Returns:
            Next increment date
        """
        reference_date = last_increment_date or move_in_date
        
        # Add interval years to reference date
        next_date = date(
            reference_date.year + interval_years,
            reference_date.month,
            reference_date.day,
        )
        
        return next_date

    def set_rent_policy(
        self,
        tenant: Tenant,
        increment_type: str,
        increment_value: float,
        interval_years: int,
    ) -> Tenant:
        """Set or update rent increment policy for a tenant.
        
        Args:
            tenant: Tenant object
            increment_type: 'percentage' or 'fixed'
            increment_value: Increment amount
            interval_years: Years between increments
        
        Returns:
            Updated tenant object
        """
        # Calculate next increment date based on move-in date
        next_increment_date = self.calculate_next_increment_date(
            tenant.move_in_date,
            interval_years,
        )

        policy = {
            "type": increment_type,
            "value": increment_value,
            "interval_years": interval_years,
            "next_increment_date": next_increment_date.isoformat(),
        }

        tenant.rent_increment_policy = policy
        
        # Initialize rent history if empty
        if not tenant.rent_history:
            tenant.rent_history = [
                {
                    "effective_date": tenant.move_in_date.isoformat(),
                    "amount": float(tenant.monthly_rent),
                    "reason": "Initial rent",
                    "applied_by": None,
                }
            ]

        self.db.commit()
        self.db.refresh(tenant)
        return tenant

    def apply_rent_increment(
        self,
        tenant: Tenant,
        applied_by: UUID,
        reason: str = "Automatic increment",
        effective_date: Optional[date] = None,
    ) -> Tenant:
        """Apply rent increment to tenant based on policy.
        
        Args:
            tenant: Tenant object
            applied_by: UUID of user applying increment
            reason: Reason for increment
            effective_date: Date increment takes effect (default: today)
        
        Returns:
            Updated tenant with new rent
        """
        if not tenant.rent_increment_policy:
            raise ValueError("No rent increment policy set for tenant")

        policy = tenant.rent_increment_policy
        new_rent = self.calculate_increment(tenant.monthly_rent, policy)
        
        if effective_date is None:
            effective_date = date.today()

        # Update rent
        old_rent = tenant.monthly_rent
        tenant.monthly_rent = new_rent

        # Add to history
        if not tenant.rent_history:
            tenant.rent_history = []
        
        tenant.rent_history.append({
            "effective_date": effective_date.isoformat(),
            "amount": float(new_rent),
            "old_amount": float(old_rent),
            "reason": reason,
            "applied_by": str(applied_by),
        })

        # Update next increment date
        interval_years = policy.get("interval_years", 1)
        next_date = self.calculate_next_increment_date(
            tenant.move_in_date,
            interval_years,
            effective_date,
        )
        tenant.rent_increment_policy["next_increment_date"] = next_date.isoformat()

        self.db.commit()
        self.db.refresh(tenant)
        return tenant

    def apply_manual_override(
        self,
        tenant: Tenant,
        new_rent: Decimal,
        applied_by: UUID,
        reason: str,
        effective_date: Optional[date] = None,
    ) -> Tenant:
        """Manually override rent amount.
        
        Args:
            tenant: Tenant object
            new_rent: New rent amount
            applied_by: UUID of user applying override
            reason: Reason for override
            effective_date: Date override takes effect
        
        Returns:
            Updated tenant
        """
        if effective_date is None:
            effective_date = date.today()

        old_rent = tenant.monthly_rent
        tenant.monthly_rent = new_rent

        # Add to history
        if not tenant.rent_history:
            tenant.rent_history = []

        tenant.rent_history.append({
            "effective_date": effective_date.isoformat(),
            "amount": float(new_rent),
            "old_amount": float(old_rent),
            "reason": f"Manual override: {reason}",
            "applied_by": str(applied_by),
        })

        self.db.commit()
        self.db.refresh(tenant)
        return tenant

    def get_tenants_due_for_increment(self) -> List[Tenant]:
        """Get all tenants whose rent is due for increment.
        
        Returns:
            List of tenants with due increments
        """
        from ..models.tenant import TenantStatus
        
        tenants = self.db.query(Tenant).filter(
            Tenant.status == TenantStatus.ACTIVE,
            Tenant.rent_increment_policy.isnot(None),
        ).all()

        due_tenants = []
        today = date.today()

        for tenant in tenants:
            policy = tenant.rent_increment_policy
            if not policy:
                continue

            next_increment_str = policy.get("next_increment_date")
            if not next_increment_str:
                continue

            next_increment = date.fromisoformat(next_increment_str)
            if next_increment <= today:
                due_tenants.append(tenant)

        return due_tenants

    def get_upcoming_increments(
        self,
        days_ahead: int = 30,
    ) -> List[Dict]:
        """Get upcoming rent increments within specified days.
        
        Args:
            days_ahead: Number of days to look ahead
        
        Returns:
            List of dicts with tenant info and increment details
        """
        from ..models.tenant import TenantStatus
        
        tenants = self.db.query(Tenant).filter(
            Tenant.status == TenantStatus.ACTIVE,
            Tenant.rent_increment_policy.isnot(None),
        ).all()

        upcoming = []
        today = date.today()
        future_date = today + timedelta(days=days_ahead)

        for tenant in tenants:
            policy = tenant.rent_increment_policy
            if not policy:
                continue

            next_increment_str = policy.get("next_increment_date")
            if not next_increment_str:
                continue

            next_increment = date.fromisoformat(next_increment_str)
            
            if today <= next_increment <= future_date:
                new_rent = self.calculate_increment(tenant.monthly_rent, policy)
                upcoming.append({
                    "tenant_id": tenant.id,
                    "tenant_name": tenant.user.full_name if tenant.user else "Unknown",
                    "property_id": tenant.property_id,
                    "current_rent": float(tenant.monthly_rent),
                    "new_rent": float(new_rent),
                    "increment_date": next_increment_str,
                    "days_until": (next_increment - today).days,
                })

        return sorted(upcoming, key=lambda x: x["days_until"])

    def get_rent_history(self, tenant: Tenant) -> List[Dict]:
        """Get formatted rent history for a tenant.
        
        Args:
            tenant: Tenant object
        
        Returns:
            List of rent change records
        """
        if not tenant.rent_history:
            return []

        return tenant.rent_history
