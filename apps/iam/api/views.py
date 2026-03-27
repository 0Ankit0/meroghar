from django.contrib.auth import get_user_model, login, logout
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.organization import resolve_active_organization
from apps.iam.models import Organization, OrganizationInvitation, OrganizationMembership
from .serializers import (
    AuthProfileSerializer,
    LoginSerializer,
    MembershipSerializer,
    SwitchOrganizationSerializer,
    OrganizationInvitationSerializer,
    UserSerializer,
)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


class OrganizationInvitationViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationInvitationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        active_org = getattr(self.request, 'active_organization', None)
        if not active_org:
            return OrganizationInvitation.objects.none()
        return OrganizationInvitation.objects.filter(organization=active_org).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(
            organization=self.request.active_organization,
            invited_by=self.request.user,
        )


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


class AcceptInvitationApiView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, token):
        invitation = OrganizationInvitation.objects.filter(token=token).first()
        if not invitation:
            return Response({'detail': 'Invitation not found.'}, status=status.HTTP_404_NOT_FOUND)
        if invitation.status != OrganizationInvitation.Status.PENDING:
            return Response({'detail': 'Invitation is no longer valid.'}, status=status.HTTP_400_BAD_REQUEST)
        if invitation.expires_at <= timezone.now():
            invitation.status = OrganizationInvitation.Status.EXPIRED
            invitation.save(update_fields=['status', 'updated_at'])
            return Response({'detail': 'Invitation expired.'}, status=status.HTTP_400_BAD_REQUEST)
        if invitation.email.lower() != request.user.email.lower():
            return Response({'detail': 'Invitation email does not match logged in user.'}, status=status.HTTP_403_FORBIDDEN)

        OrganizationMembership.objects.update_or_create(
            organization=invitation.organization,
            user=request.user,
            defaults={
                'role': invitation.role,
                'invited_by': invitation.invited_by,
                'is_active': True,
            },
        )
        request.user.organizations.add(invitation.organization)
        invitation.mark_accepted(request.user)
        return Response({'detail': 'Invitation accepted.'}, status=status.HTTP_200_OK)
