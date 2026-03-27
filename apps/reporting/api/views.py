from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Sum, Avg
from django.utils import timezone

from apps.finance.models import Invoice
from apps.housing.models import Lease
from apps.operations.models import WorkOrder
from apps.housing.models import Unit

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


class PortfolioKPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        active_org = getattr(request, 'active_organization', None)
        if not active_org:
            return Response({'detail': 'No active organization selected.'}, status=400)

        units = Unit.objects.filter(property__organization=active_org)
        total_units = units.count()
        occupied_units = units.filter(status='OCCUPIED').count()
        occupancy_rate = round((occupied_units / total_units) * 100, 2) if total_units else 0

        overdue_invoices = Invoice.objects.filter(
            organization=active_org,
            due_date__lt=timezone.now().date(),
            status__in=[Invoice.Status.SENT, Invoice.Status.PARTIALLY_PAID, Invoice.Status.OVERDUE],
        )
        overdue_balance = sum(invoice.balance_due for invoice in overdue_invoices)

        work_orders = WorkOrder.objects.filter(organization=active_org)
        maintenance = {
            'open_count': work_orders.filter(status__in=[WorkOrder.Status.OPEN, WorkOrder.Status.IN_PROGRESS]).count(),
            'closed_count': work_orders.filter(status__in=[WorkOrder.Status.RESOLVED, WorkOrder.Status.CLOSED]).count(),
            'avg_hours': float(work_orders.filter(actual_hours__isnull=False).aggregate(v=Avg('actual_hours'))['v'] or 0),
        }

        return Response({
            'occupancy': {
                'total_units': total_units,
                'occupied_units': occupied_units,
                'rate': occupancy_rate,
            },
            'receivables': {
                'overdue_invoice_count': overdue_invoices.count(),
                'overdue_balance': overdue_balance,
            },
            'maintenance': maintenance,
        })
