from rest_framework import viewsets
from apps.finance.models import Expense, Invoice, Payment
from .serializers import ExpenseSerializer, InvoiceSerializer, PaymentSerializer
from apps.iam.api.permissions import IsOrgManager, IsOrgTenant

class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [IsOrgManager]

    def get_queryset(self):
        active_org = getattr(self.request, 'active_organization', None)
        if active_org:
            return Expense.objects.filter(organization=active_org)
        return Expense.objects.none()

    def perform_create(self, serializer):
        serializer.save(organization=self.request.active_organization)

class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = [IsOrgTenant]

    def get_queryset(self):
        user = self.request.user
        queryset = Invoice.objects.none()
        active_org = getattr(self.request, 'active_organization', None)
        
        if active_org:
            queryset = Invoice.objects.filter(organization=active_org)
            
        # Tenant Restriction
        if user.role == 'TENANT':
            # Assuming Tenant profile is linked
            queryset = queryset.filter(lease__tenant__user=user)
            
        return queryset

class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsOrgTenant]

    def get_queryset(self):
        user = self.request.user
        queryset = Payment.objects.none()
        active_org = getattr(self.request, 'active_organization', None)
        
        if active_org:
            queryset = Payment.objects.filter(organization=active_org)
            
        # Tenant Restriction - View their own payments
        if user.role == 'TENANT':
            queryset = queryset.filter(invoice__lease__tenant__user=user)
            
        return queryset

    def perform_create(self, serializer):
        # Tenants might create payments? Usually initiated via mobile app.
        # We need validation to ensure they pay THEIR invoice.
        # Use serializer validation or check here.
        serializer.save(organization=self.request.active_organization)
