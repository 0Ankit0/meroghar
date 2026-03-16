from rest_framework import viewsets
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from apps.iam.models import UserOnboardingEvent
from .serializers import UserSerializer
from .permissions import IsOrgOwner

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsOrgOwner]

    def get_queryset(self):
        if hasattr(self.request, 'active_organization'):
            return User.objects.filter(organizations=self.request.active_organization).order_by('-date_joined')
        return User.objects.none()
