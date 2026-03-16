from rest_framework import viewsets, permissions
from apps.operations.models import Vendor, WorkOrder
from .serializers import VendorSerializer, WorkOrderSerializer

class VendorViewSet(viewsets.ModelViewSet):
    serializer_class = VendorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if hasattr(self.request, 'active_organization'):
            return Vendor.objects.filter(organization=self.request.active_organization)
        return Vendor.objects.none()

    def perform_create(self, serializer):
        serializer.save(organization=self.request.active_organization)

class WorkOrderViewSet(viewsets.ModelViewSet):
    serializer_class = WorkOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        active_org = getattr(self.request, 'active_organization', None)
        if not active_org:
            return WorkOrder.objects.none()

        queryset = WorkOrder.objects.filter(organization=active_org)

        if user.role == 'TENANT':
            queryset = queryset.filter(requester__user=user)

        return queryset

    def perform_create(self, serializer):
        serializer.save(organization=self.request.active_organization)
