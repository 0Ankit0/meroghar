from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, BasePermission
from django.contrib.auth import get_user_model

from apps.iam.models import OrganizationMembership
from .serializers import UserSerializer

User = get_user_model()


class IsOrganizationAdmin(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        active_org = getattr(request, 'active_organization', None)
        return request.user.has_org_role(
            active_org,
            {OrganizationMembership.Role.OWNER, OrganizationMembership.Role.ADMIN},
        )


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsOrganizationAdmin]

    def get_queryset(self):
        active_org = getattr(self.request, 'active_organization', None)
        if not active_org:
            return User.objects.none()
        return User.objects.filter(
            organization_memberships__organization=active_org,
            organization_memberships__is_active=True,
        ).distinct().order_by('-date_joined')
