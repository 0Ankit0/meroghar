from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count
from django.utils import timezone
from apps.housing.models import Unit
from apps.finance.models import Payment
from apps.housing.models import Lease

class ReportListView(LoginRequiredMixin, TemplateView):
    template_name = "reporting/report_list.html"

class FinancialReportView(LoginRequiredMixin, TemplateView):
    template_name = "reporting/financial_report.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.request.user.organization
        now = timezone.now()
        
        # Monthly Revenue (Last 6 months)
        # Simplified for MVP: Just getting this month vs last month
        this_month_revenue = Payment.objects.filter(
            organization=org, 
            status='SUCCESS',
            created_at__month=now.month,
            created_at__year=now.year
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        last_month = now.month - 1 if now.month > 1 else 12
        last_month_year = now.year if now.month > 1 else now.year - 1
        
        last_month_revenue = Payment.objects.filter(
            organization=org, 
            status='SUCCESS',
            created_at__month=last_month,
            created_at__year=last_month_year
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        context['financials'] = {
            'this_month': this_month_revenue,
            'last_month': last_month_revenue,
            'growth': this_month_revenue - last_month_revenue
        }
        return context

class OccupancyReportView(LoginRequiredMixin, TemplateView):
    template_name = "reporting/occupancy_report.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.request.user.organization
        
        # Unit lookup via property
        total_units = Unit.objects.filter(property__organization=org).count()
        occupied = Unit.objects.filter(property__organization=org, status='OCCUPIED').count()
        vacant = total_units - occupied
        
        rate = 0
        if total_units > 0:
            rate = round((occupied / total_units) * 100, 1)
            
        context['occupancy'] = {
            'total': total_units,
            'occupied': occupied,
            'vacant': vacant,
            'rate': rate
        }
        return context
