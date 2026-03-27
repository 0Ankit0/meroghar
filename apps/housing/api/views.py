from rest_framework import viewsets
from apps.housing.models import PropertyInspection, InventoryItem, Property, Unit, Tenant, Lease, LeaseRenewal
from .serializers import PropertyInspectionSerializer, InventoryItemSerializer, PropertySerializer, UnitSerializer, TenantSerializer, LeaseSerializer, LeaseRenewalSerializer
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


class LeaseRenewalViewSet(viewsets.ModelViewSet):
    serializer_class = LeaseRenewalSerializer
    permission_classes = [IsOrgTenant]

    def get_queryset(self):
        active_org = getattr(self.request, 'active_organization', None)
        if not active_org:
            return LeaseRenewal.objects.none()
        return LeaseRenewal.objects.filter(lease__organization=active_org)

    def perform_update(self, serializer):
        instance = serializer.save()
        status_value = serializer.validated_data.get('status')
        if status_value == LeaseRenewal.Status.APPROVED:
            instance.approve(self.request.user)
        elif status_value == LeaseRenewal.Status.REJECTED:
            instance.reject(self.request.user)
