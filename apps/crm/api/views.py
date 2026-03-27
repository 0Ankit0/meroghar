from rest_framework import viewsets
from ..models import Lead, Showing, RentalApplication, LeadFollowUp
from .serializers import LeadSerializer, ShowingSerializer, RentalApplicationSerializer, LeadFollowUpSerializer
from apps.iam.api.permissions import IsOrgManager

class LeadViewSet(viewsets.ModelViewSet):
    serializer_class = LeadSerializer
    permission_classes = [IsOrgManager]

    def get_queryset(self):
        active_org = getattr(self.request, 'active_organization', None)
        if active_org:
            return Lead.objects.filter(organization=active_org)
        return Lead.objects.none()

    def perform_create(self, serializer):
        serializer.save(organization=self.request.active_organization)

class ShowingViewSet(viewsets.ModelViewSet):
    serializer_class = ShowingSerializer
    permission_classes = [IsOrgManager]

    def get_queryset(self):
        active_org = getattr(self.request, 'active_organization', None)
        if active_org:
            return Showing.objects.filter(lead__organization=active_org)
        return Showing.objects.none()

class RentalApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = RentalApplicationSerializer
    permission_classes = [IsOrgManager]

    def get_queryset(self):
        active_org = getattr(self.request, 'active_organization', None)
        if active_org:
            return RentalApplication.objects.filter(lead__organization=active_org)
        return RentalApplication.objects.none()


class LeadFollowUpViewSet(viewsets.ModelViewSet):
    serializer_class = LeadFollowUpSerializer
    permission_classes = [IsOrgManager]

    def get_queryset(self):
        if hasattr(self.request, 'active_organization'):
            return LeadFollowUp.objects.filter(lead__organization=self.request.active_organization)
        return LeadFollowUp.objects.none()
