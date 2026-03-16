from django.contrib.auth import get_user_model, login, logout
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.organization import resolve_active_organization
from apps.iam.models import Organization
from .serializers import (
    AuthProfileSerializer,
    LoginSerializer,
    MembershipSerializer,
    SwitchOrganizationSerializer,
    UserSerializer,
)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


@extend_schema(request=LoginSerializer)
class AuthLoginApiView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        login(request, user)

        token, _ = Token.objects.get_or_create(user=user)
        active_organization = resolve_active_organization(request._request, user)
        profile = AuthProfileSerializer(user, context={'active_organization': active_organization})
        return Response(
            {
                'token': token.key,
                'user': profile.data,
            },
            status=status.HTTP_200_OK,
        )


class AuthRefreshTokenApiView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        token = Token.objects.create(user=request.user)
        return Response({'token': token.key}, status=status.HTTP_200_OK)


class AuthLogoutApiView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AuthProfileApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        active_organization = resolve_active_organization(request._request, request.user)
        profile = AuthProfileSerializer(request.user, context={'active_organization': active_organization})
        return Response(profile.data, status=status.HTTP_200_OK)


class MembershipListApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        active_organization = resolve_active_organization(request._request, request.user)
        memberships = MembershipSerializer(
            request.user.organizations.order_by('name'),
            many=True,
            context={'active_organization': active_organization},
        )
        return Response(memberships.data, status=status.HTTP_200_OK)


@extend_schema(request=SwitchOrganizationSerializer)
class SwitchOrganizationApiView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SwitchOrganizationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        organization_id = serializer.validated_data['organization_id']
        try:
            organization = request.user.organizations.get(id=organization_id)
        except Organization.DoesNotExist:
            return Response(
                {'detail': 'You are not a member of this organization.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        request.session['active_org_id'] = str(organization.id)
        request.active_organization = organization
        membership = MembershipSerializer(
            organization,
            context={'active_organization': organization},
        )
        return Response({'active_organization': membership.data}, status=status.HTTP_200_OK)
