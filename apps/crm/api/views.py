from rest_framework import viewsets
from ..models import Lead, Showing, RentalApplication
from .serializers import LeadSerializer, ShowingSerializer, RentalApplicationSerializer
from apps.iam.api.permissions import IsOrgManager

class LeadViewSet(viewsets.ModelViewSet):
    serializer_class = LeadSerializer
    permission_classes = [IsOrgManager]

    def get_queryset(self):
        if hasattr(self.request, 'active_organization'):
            return Lead.objects.filter(organization=self.request.active_organization)
        return Lead.objects.none()

    def perform_create(self, serializer):
        serializer.save(organization=self.request.active_organization)

class ShowingViewSet(viewsets.ModelViewSet):
    serializer_class = ShowingSerializer
    permission_classes = [IsOrgManager]

    def get_queryset(self):
        if hasattr(self.request, 'active_organization'):
            return Showing.objects.filter(lead__organization=self.request.active_organization)
        return Showing.objects.none()

class RentalApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = RentalApplicationSerializer
    permission_classes = [IsOrgManager]

    def get_queryset(self):
        if hasattr(self.request, 'active_organization'):
            return RentalApplication.objects.filter(lead__organization=self.request.active_organization)
        return RentalApplication.objects.none()
