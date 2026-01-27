from decimal import Decimal
import calendar
from datetime import date

def calculate_prorated_rent(monthly_rent: Decimal, start_date: date, end_date: date) -> Decimal:
    """
    Calculate prorated rent for a partial month.
    Logic: (Monthly Rent / Days in Month) * Remaining Days
    """
    if start_date.month == end_date.month and start_date.year == end_date.year:
        # Same month
        days_in_month = calendar.monthrange(start_date.year, start_date.month)[1]
        days_occupied = (end_date - start_date).days + 1 # inclusive
        
        daily_rate = monthly_rent / Decimal(days_in_month)
        return round(daily_rate * Decimal(days_occupied), 2)
    else:
        # Multi-month logic is complex, usually we just prorate the first and last month separately.
        # For this utility we assume it's called for a specific billing period (usually 1 month).
        # If the period spans multiple months, we should probably calculate per month.
        # But per requirements edge case, let's strictly handle the specific month of the start_date.
        
        days_in_month = calendar.monthrange(start_date.year, start_date.month)[1]
        # Valid days in this month
        days_occupied = days_in_month - start_date.day + 1
        
        daily_rate = monthly_rent / Decimal(days_in_month)
        return round(daily_rate * Decimal(days_occupied), 2)
