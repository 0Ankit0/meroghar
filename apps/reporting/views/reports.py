from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count
from django.utils import timezone
from apps.finance.models import Payment, Expense
from apps.housing.models import Lease, Unit, Property

class ReportListView(LoginRequiredMixin, TemplateView):
    template_name = "reporting/report_list.html"

class FinancialReportView(LoginRequiredMixin, TemplateView):
    template_name = "reporting/financial_report.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.request.user.organization
        now = timezone.now()
        
        # Filters
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        property_id = self.request.GET.get('property')
        
        # Base QuerySets
        payments = Payment.objects.filter(organization=org, status='SUCCESS')
        expenses = Expense.objects.filter(organization=org)
        
        if property_id:
            payments = payments.filter(lease__unit__property_id=property_id)
            expenses = expenses.filter(property_id=property_id)
            
        if start_date:
            payments = payments.filter(created_at__date__gte=start_date)
            expenses = expenses.filter(expense_date__gte=start_date)
            
        if end_date:
            payments = payments.filter(created_at__date__lte=end_date)
            expenses = expenses.filter(expense_date__lte=end_date)

        # Aggregates
        total_revenue = payments.aggregate(total=Sum('amount'))['total'] or 0
        total_expense = expenses.aggregate(total=Sum('amount'))['total'] or 0
        net_income = total_revenue - total_expense
        
        context['summary'] = {
            'revenue': total_revenue,
            'expense': total_expense,
            'net_income': net_income
        }
        
        # Chart Data (Monthly for last 6 months or selected range)
        # For simplicity, let's do a 6-month lookback if no date range, 
        # or grouped by month/day if range provided. 
        # Implementing a simple 6-month rolling view for the chart for now.
        
        labels = []
        revenue_data = []
        expense_data = []
        
        for i in range(5, -1, -1):
            month_start = now - timezone.timedelta(days=30*i) # Approx
            # Better month calculation needed for production, utilizing 'trunc' or proper date math
            # Using simple month extraction for MVP
            target_month = (now.month - i - 1) % 12 + 1
            target_year = now.year - ((now.month - i - 1) // 12 + 1)
            # Actually easier: use dateutil relativedelta but let's stick to stdlib
            # Python date math is tricky without external libs like dateutil or pandas
            # Let's simple-case it: Filter by month/year explicitly in loop
            
            # Logic to get year/month correctly
            y, m = now.year, now.month - i
            if m <= 0:
                m += 12
                y -= 1
            
            labels.append(f"{y}-{m:02d}")
            
            rev = payments.filter(created_at__year=y, created_at__month=m).aggregate(t=Sum('amount'))['t'] or 0
            exp = expenses.filter(expense_date__year=y, expense_date__month=m).aggregate(t=Sum('amount'))['t'] or 0
            
            revenue_data.append(float(rev))
            expense_data.append(float(exp))
            
        context['chart_data'] = {
            'labels': labels,
            'revenue': revenue_data,
            'expense': expense_data
        }
        
        context['properties'] = Property.objects.filter(organization=org)
        
        return context

class OccupancyReportView(LoginRequiredMixin, TemplateView):
    template_name = "reporting/occupancy_report.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.request.user.organization
        property_id = self.request.GET.get('property')
        
        # Base QuerySet
        units = Unit.objects.filter(property__organization=org)
        
        if property_id:
            units = units.filter(property_id=property_id)
            
        # Stats
        total_units = units.count()
        occupied = units.filter(status='OCCUPIED').count()
        vacant = units.filter(status='VACANT').count()
        maintenance = units.filter(status='MAINTENANCE').count()
        
        rate = 0
        if total_units > 0:
            rate = round((occupied / total_units) * 100, 1)
            
        context['occupancy'] = {
            'total': total_units,
            'occupied': occupied,
            'vacant': vacant,
            'maintenance': maintenance,
            'rate': rate
        }
        
        context['chart_data'] = {
            'labels': ['Occupied', 'Vacant', 'Maintenance'],
            'data': [occupied, vacant, maintenance]
        }
        
        context['properties'] = Property.objects.filter(organization=org)
        
        return context

class MaintenanceReportView(LoginRequiredMixin, TemplateView):
    template_name = "reporting/maintenance_report.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.request.user.organization
        property_id = self.request.GET.get('property')
        
        # Determine query path based on app structure 
        from apps.operations.models import WorkOrder
        
        wos = WorkOrder.objects.filter(organization=org)
        
        if property_id:
            wos = wos.filter(unit__property_id=property_id)
            
        # Stats
        total = wos.count()
        open_wo = wos.filter(status='OPEN').count()
        in_progress = wos.filter(status='IN_PROGRESS').count()
        resolved = wos.filter(status='RESOLVED').count()
        closed = wos.filter(status='CLOSED').count()
        
        # Priority Stats
        high_priority = wos.filter(priority__in=['HIGH', 'EMERGENCY']).count()
        
        context['stats'] = {
            'total': total,
            'open': open_wo,
            'in_progress': in_progress,
            'resolved': resolved,
            'closed': closed,
            'high_priority': high_priority
        }
        
        context['chart_data'] = {
            'labels': ['Open', 'In Progress', 'Resolved', 'Closed'],
            'data': [open_wo, in_progress, resolved, closed]
        }
        
        context['properties'] = Property.objects.filter(organization=org)
        
        return context
