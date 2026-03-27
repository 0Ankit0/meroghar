from rest_framework import viewsets
from apps.operations.models import Vendor, WorkOrder
from .serializers import VendorSerializer, WorkOrderSerializer
from apps.iam.api.permissions import IsOrgManager, IsOrgTenant

class VendorViewSet(viewsets.ModelViewSet):
    serializer_class = VendorSerializer
    permission_classes = [IsOrgManager]

    def get_queryset(self):
        active_org = getattr(self.request, 'active_organization', None)
        if active_org:
            return Vendor.objects.filter(organization=active_org)
        return Vendor.objects.none()

    def perform_create(self, serializer):
        serializer.save(organization=self.request.active_organization)

class WorkOrderViewSet(viewsets.ModelViewSet):
    serializer_class = WorkOrderSerializer
    permission_classes = [IsOrgTenant]

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
