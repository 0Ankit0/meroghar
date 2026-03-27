from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Sum

from apps.finance.models import Invoice
from apps.housing.models import Lease
from apps.operations.models import WorkOrder

class MobileDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        active_org = getattr(request, 'active_organization', None)
        data = {
            'balance_due': 0,
            'open_requests': 0,
            'lease_status': 'None',
            'next_due_date': None
        }
        
        if user.role == 'TENANT' and active_org:
            # Balance Linked to Tenant User
            invoices = Invoice.objects.filter(
                organization=active_org,
                lease__tenant__user=user,
                status__in=['SENT', 'PARTIALLY_PAID', 'OVERDUE'],
            )
            total_due = sum(inv.balance_due for inv in invoices)
            
            # Next Due Date (Earliest unpaid invoice)
            next_invoice = invoices.order_by('due_date').first()
            
            # Open Requests
            open_requests = WorkOrder.objects.filter(
                organization=active_org,
                requester__user=user,
                status__in=['OPEN', 'IN_PROGRESS'],
            ).count()
            
            # Lease Status
            lease = Lease.objects.filter(
                organization=active_org,
                tenant__user=user,
                status='ACTIVE',
            ).first()
            
            data.update({
                'balance_due': total_due,
                'next_due_date': next_invoice.due_date if next_invoice else None,
                'open_requests': open_requests,
                'lease_status': lease.status if lease else 'No Active Lease'
            })
            
        return Response(data)
