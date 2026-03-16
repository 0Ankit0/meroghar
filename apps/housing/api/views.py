from rest_framework import viewsets
from apps.housing.models import PropertyInspection, InventoryItem, Property, Unit, Tenant, Lease
from .serializers import PropertyInspectionSerializer, InventoryItemSerializer, PropertySerializer, UnitSerializer, TenantSerializer, LeaseSerializer
from apps.iam.api.permissions import IsOrgManager, IsOrgTenant

class PropertyInspectionViewSet(viewsets.ModelViewSet):
    serializer_class = PropertyInspectionSerializer
    permission_classes = [IsOrgManager]

    def get_queryset(self):
        if hasattr(self.request, 'active_organization'):
            return PropertyInspection.objects.filter(unit__property__organization=self.request.active_organization)
        return PropertyInspection.objects.none()

class InventoryItemViewSet(viewsets.ModelViewSet):
    serializer_class = InventoryItemSerializer
    permission_classes = [IsOrgManager]

    def get_queryset(self):
        if hasattr(self.request, 'active_organization'):
            return InventoryItem.objects.filter(unit__property__organization=self.request.active_organization)
        return InventoryItem.objects.none()

    def perform_create(self, serializer):
        serializer.save(organization=self.request.active_organization)

class PropertyViewSet(viewsets.ModelViewSet):
    serializer_class = PropertySerializer
    permission_classes = [IsOrgManager]

    def get_queryset(self):
        if hasattr(self.request, 'active_organization'):
            return Property.objects.filter(organization=self.request.active_organization)
        return Property.objects.none()

    def perform_create(self, serializer):
        serializer.save(organization=self.request.active_organization)

class UnitViewSet(viewsets.ModelViewSet):
    serializer_class = UnitSerializer
    permission_classes = [IsOrgManager]

    def get_queryset(self):
        if hasattr(self.request, 'active_organization'):
            return Unit.objects.filter(property__organization=self.request.active_organization)
        return Unit.objects.none()

class TenantViewSet(viewsets.ModelViewSet):
    serializer_class = TenantSerializer
    permission_classes = [IsOrgTenant]

    def get_queryset(self):
        if hasattr(self.request, 'active_organization'):
            return Tenant.objects.filter(organization=self.request.active_organization)
        return Tenant.objects.none()

    def perform_create(self, serializer):
        serializer.save(organization=self.request.active_organization)

class LeaseViewSet(viewsets.ModelViewSet):
    serializer_class = LeaseSerializer
    permission_classes = [IsOrgTenant]

    def get_queryset(self):
        user = self.request.user
        active_org = getattr(self.request, 'active_organization', None)
        if not active_org:
            return Lease.objects.none()

        queryset = Lease.objects.filter(units__property__organization=active_org).distinct()

        if user.role == 'TENANT':
            queryset = queryset.filter(tenant__user=user)

        return queryset

