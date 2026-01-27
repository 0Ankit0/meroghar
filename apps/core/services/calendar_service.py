from datetime import datetime, timedelta
from apps.housing.models import Lease
from apps.operations.models import WorkOrder
from apps.crm.models import Showing

class CalendarService:
    def __init__(self, organization):
        self.organization = organization

    def get_events(self, start_date=None, end_date=None):
        """
        Fetch all calendar events within a date range.
        Events: Lease Start, Lease End, Work Order Due (?), Showing
        """
        if not start_date:
            start_date = datetime.now()
        if not end_date:
            end_date = start_date + timedelta(days=30)

        events = []

        # 1. Lease Events
        leases = Lease.objects.filter(
            organization=self.organization,
            start_date__gte=start_date,
            start_date__lte=end_date
        )
        for lease in leases:
            events.append({
                'title': f"Lease Start: {lease.tenant}",
                'start': lease.start_date,
                'type': 'lease_start',
                'id': lease.id
            })
            
        # Lease Endings (Checking end_date in range)
        expiring_leases = Lease.objects.filter(
            organization=self.organization,
            end_date__gte=start_date,
            end_date__lte=end_date
        )
        for lease in expiring_leases:
            events.append({
                'title': f"Lease Expiring: {lease.tenant}",
                'start': lease.end_date,
                'type': 'lease_end',
                'id': lease.id,
                'className': 'bg-red-500' # detailed logic in serializes
            })

        # 2. Showings
        showings = Showing.objects.filter(
            lead__organization=self.organization,
            start_time__gte=start_date,
            start_time__lte=end_date
        )
        for showing in showings:
             events.append({
                'title': f"Showing: {showing.unit.unit_number}",
                'start': showing.start_time,
                'end': showing.end_time,
                'type': 'showing',
                'id': showing.id
            })

        # 3. Work Orders (Using created_at or if we add due_date later)
        # Assuming we just list active ones or those created recently? 
        # Ideally WO has a 'scheduled_date'. Let's skip for now if no date field suitable.
        
        return events
