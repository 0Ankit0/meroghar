from rest_framework import viewsets
from apps.finance.models import Expense, Invoice, Payment
from .serializers import ExpenseSerializer, InvoiceSerializer, PaymentSerializer
from apps.iam.api.permissions import IsOrgManager, IsOrgTenant

class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [IsOrgManager]

    def get_queryset(self):
        if hasattr(self.request, 'active_organization'):
            return Expense.objects.filter(organization=self.request.active_organization)
        return Expense.objects.none()

    def perform_create(self, serializer):
        serializer.save(organization=self.request.active_organization)

class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = [IsOrgTenant]

    def get_queryset(self):
        user = self.request.user
        queryset = Invoice.objects.none()
        
        if hasattr(self.request, 'active_organization'):
            queryset = Invoice.objects.filter(organization=self.request.active_organization)
            
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
        
        if hasattr(self.request, 'active_organization'):
            queryset = Payment.objects.filter(organization=self.request.active_organization)
            
        # Tenant Restriction - View their own payments
        if user.role == 'TENANT':
            queryset = queryset.filter(invoice__lease__tenant__user=user)
            
        return queryset

    def perform_create(self, serializer):
        # Tenants might create payments? Usually initiated via mobile app.
        # We need validation to ensure they pay THEIR invoice.
        # Use serializer validation or check here.
        serializer.save(organization=self.request.active_organization)
