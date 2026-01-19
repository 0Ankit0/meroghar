from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "core/dashboard.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if not user.is_authenticated or not hasattr(user, 'organization') or not user.organization:
            context['stats'] = {
                'properties': 0,
                'tenants': 0,
                'occupancy_rate': 0,
                'open_requests': 0,
                'revenue_month': 0
            }
            return context

        org = user.organization
        
        # Imports here to avoid circular dependencies if any, or just for cleanliness
        from apps.housing.models import Property, Unit
        from apps.housing.models import Tenant
        from apps.operations.models import WorkOrder
        from apps.finance.models import Payment
        from django.db.models import Sum, Q
        from django.utils import timezone
        
        # 1. Property Stats
        total_properties = Property.objects.filter(organization=org).count()
        total_units = Unit.objects.filter(property__organization=org).count()
        occupied_units = Unit.objects.filter(property__organization=org, status='OCCUPIED').count()
        
        occupancy_rate = 0
        if total_units > 0:
            occupancy_rate = round((occupied_units / total_units) * 100, 1)

        # 2. Tenant Stats
        total_tenants = Tenant.objects.filter(organization=org).count()
        
        # 3. Maintenance Stats
        open_requests = WorkOrder.objects.filter(
            organization=org, 
            status__in=['OPEN', 'IN_PROGRESS', 'EMERGENCY'] # Adjusted based on choices usually available
        ).count()
        
        # 4. Financial Stats (This Month)
        now = timezone.now()
        current_year = now.year
        current_month = now.month
        
        revenue_month = Payment.objects.filter(
            organization=org,
            status='SUCCESS', 
            created_at__year=current_year,
            created_at__month=current_month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        context['stats'] = {
            'properties': total_properties,
            'tenants': total_tenants,
            'occupancy_rate': occupancy_rate,
            'open_requests': open_requests,
            'revenue_month': revenue_month
        }

        # --- Chart Data Aggregation ---

        # A) Revenue Trend (Last 6 Months)
        from django.db.models.functions import TruncMonth
        from datetime import timedelta
        
        six_months_ago = now - timedelta(days=30*6)
        revenue_data = Payment.objects.filter(
            organization=org,
            status='SUCCESS',
            created_at__gte=six_months_ago
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            total=Sum('amount')
        ).order_by('month')
        
        # Format for Chart.js
        months = []
        revenues = []
        for entry in revenue_data:
            months.append(entry['month'].strftime('%b %Y'))
            revenues.append(float(entry['total']))
            
        context['chart_revenue_labels'] = months
        context['chart_revenue_data'] = revenues

        # B) Work Order Status Distribution
        from django.db.models import Count
        wo_status_data = WorkOrder.objects.filter(organization=org).values('status').annotate(count=Count('id'))
        
        wo_labels = []
        wo_counts = []
        for entry in wo_status_data:
            label = dict(WorkOrder.Status.choices).get(entry['status'], entry['status'])
            wo_labels.append(label)
            wo_counts.append(entry['count'])
            
        context['chart_wo_labels'] = wo_labels
        context['chart_wo_data'] = wo_counts

        # C) Invoice Status Distribution
        from apps.finance.models import Invoice
        inv_status_data = Invoice.objects.filter(organization=org).values('status').annotate(count=Count('id'))
        
        inv_labels = []
        inv_counts = []
        for entry in inv_status_data:
            label = dict(Invoice.Status.choices).get(entry['status'], entry['status'])
            inv_labels.append(label)
            inv_counts.append(entry['count'])
            
        context['chart_inv_labels'] = inv_labels
        context['chart_inv_data'] = inv_counts
        
        # Recent Activity (Hybrid feed)
        recent_requests = WorkOrder.objects.filter(organization=org).order_by('-created_at')[:5]
        context['recent_requests'] = recent_requests
        
        return context
