from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta
from apps.finance.models import Payment


class RevenueDataAPIView(LoginRequiredMixin, View):
    """API endpoint to fetch revenue data for different time periods."""

    def _resolve_organization(self, request):
        """Resolve organization from active context first, then user memberships."""
        active_org = getattr(request, 'active_organization', None)
        if active_org:
            return active_org

        user = request.user
        if not user.is_authenticated:
            return None

        return user.organizations.first()
    
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'labels': [], 'data': []})

        org = self._resolve_organization(request)
        if not org:
            return JsonResponse({'labels': [], 'data': []})

        months_param = request.GET.get('months', '6')
        
        try:
            months = int(months_param)
        except ValueError:
            months = 6
        
        now = timezone.now()
        
        # Determine time range
        if months == 0:
            # All time - get first payment date
            first_payment = Payment.objects.filter(
                organization=org, 
                status='SUCCESS'
            ).order_by('created_at').first()
            
            if first_payment:
                start_date = first_payment.created_at
            else:
                start_date = now - timedelta(days=180)  # Default to 6 months if no data
        else:
            start_date = now - timedelta(days=30 * months)
        
        # Fetch revenue data
        revenue_data = Payment.objects.filter(
            organization=org,
            status='SUCCESS',
            created_at__gte=start_date
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            total=Sum('amount')
        ).order_by('month')
        
        # Format for Chart.js
        labels = []
        data = []
        for entry in revenue_data:
            labels.append(entry['month'].strftime('%b %Y'))
            data.append(float(entry['total']))
        
        return JsonResponse({
            'labels': labels,
            'data': data
        })
