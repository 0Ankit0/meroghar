from rest_framework import viewsets
from django.contrib.auth import get_user_model
from .serializers import UserSerializer
from .permissions import IsOrgOwner

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [IsOrgOwner]

    def get_queryset(self):
        if hasattr(self.request, 'active_organization'):
            return User.objects.filter(organizations=self.request.active_organization).order_by('-date_joined')
        return User.objects.none()
