from rest_framework import viewsets
from apps.operations.models import Vendor, WorkOrder
from .serializers import VendorSerializer, WorkOrderSerializer
from apps.iam.api.permissions import IsOrgManager, IsOrgTenant

class VendorViewSet(viewsets.ModelViewSet):
    serializer_class = VendorSerializer
    permission_classes = [IsOrgManager]

    def get_queryset(self):
        if hasattr(self.request, 'active_organization'):
            return Vendor.objects.filter(organization=self.request.active_organization)
        return Vendor.objects.none()

    def perform_create(self, serializer):
        serializer.save(organization=self.request.active_organization)

class WorkOrderViewSet(viewsets.ModelViewSet):
    serializer_class = WorkOrderSerializer
    permission_classes = [IsOrgTenant]

    def get_queryset(self):
        user = self.request.user
        if hasattr(self.request, 'active_organization'):
            queryset = WorkOrder.objects.filter(organization=self.request.active_organization)
            
            if user.role == 'TENANT':
                queryset = queryset.filter(unit__leases__tenant__user=user, unit__leases__status='ACTIVE').distinct()
                # OR simpler: queryset.filter(requester__user=user)
                # But requester is optional. Best to link via unit they live in or explicitly if they requested it.
                # Let's check 'requester' field first. 
                # WorkOrder model has 'requester' (Tenant). So:
                queryset = queryset.filter(requester__user=user)
            
            return queryset
        return WorkOrder.objects.none()

    def perform_create(self, serializer):
        serializer.save(organization=self.request.active_organization)
