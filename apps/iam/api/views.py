from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from apps.iam.models import UserOnboardingEvent
from .serializers import UserSerializer

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    def get_permissions(self):
        if self.action in {
            'create_pending_account',
            'activate_delegate_member_role',
            'verify_account',
            'assign_organization_owner_role',
        }:
            return [IsAuthenticated()]
        return [permission() for permission in self.permission_classes]

    def _create_event(self, account, actor, event_type, metadata=None, notes=''):
        UserOnboardingEvent.objects.create(
            account=account,
            actor=actor,
            event_type=event_type,
            metadata=metadata or {},
            notes=notes,
        )

    @action(detail=False, methods=['post'], url_path='create-pending-account')
    def create_pending_account(self, request):
        if not request.user.role == User.Role.OWNER and not request.user.is_superuser:
            return Response({'detail': 'Only organization owners can create pending accounts.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        account = serializer.save(
            is_active=False,
            verification_status=User.VerificationStatus.PENDING,
            provisioned_by_owner=True,
            created_by=request.user,
        )

        if hasattr(request, 'active_organization') and request.active_organization:
            account.organizations.add(request.active_organization)

        self._create_event(
            account=account,
            actor=request.user,
            event_type=UserOnboardingEvent.EventType.CREATED,
            metadata={'provisioned_by_owner': True},
            notes='Pending account created by owner.',
        )
        return Response(self.get_serializer(account).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='verify-account')
    def verify_account(self, request, pk=None):
        if not request.user.is_superuser:
            return Response({'detail': 'Only superusers can verify accounts.'}, status=status.HTTP_403_FORBIDDEN)

        account = self.get_object()
        account.verification_status = User.VerificationStatus.VERIFIED
        account.verified_by_superuser = True
        account.verified_at = timezone.now()
        account.verified_by = request.user
        account.is_active = True
        account.save(update_fields=['verification_status', 'verified_by_superuser', 'verified_at', 'verified_by', 'is_active'])

        self._create_event(
            account=account,
            actor=request.user,
            event_type=UserOnboardingEvent.EventType.VERIFIED,
            metadata={'verified_by_superuser': True},
            notes='Account verified by superuser.',
        )
        return Response(self.get_serializer(account).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='assign-organization-owner-role')
    def assign_organization_owner_role(self, request, pk=None):
        if not request.user.is_superuser:
            return Response({'detail': 'Only superusers can assign organization owner role.'}, status=status.HTTP_403_FORBIDDEN)

        account = self.get_object()
        account.role = User.Role.OWNER
        account.delegated_by = request.user
        account.delegated_at = timezone.now()
        account.save(update_fields=['role', 'delegated_by', 'delegated_at'])

        self._create_event(
            account=account,
            actor=request.user,
            event_type=UserOnboardingEvent.EventType.OWNER_ASSIGNED,
            metadata={'role': User.Role.OWNER},
            notes='Superuser assigned organization owner role.',
        )
        return Response(self.get_serializer(account).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='activate-delegate-member-role')
    def activate_delegate_member_role(self, request, pk=None):
        if not request.user.role == User.Role.OWNER and not request.user.is_superuser:
            return Response({'detail': 'Only organization owners can activate/delegate members.'}, status=status.HTTP_403_FORBIDDEN)

        account = self.get_object()
        target_role = request.data.get('role', User.Role.MEMBER)
        allowed_roles = {User.Role.MEMBER, User.Role.MANAGER, User.Role.STAFF, User.Role.TENANT, User.Role.VENDOR}
        if target_role not in allowed_roles:
            return Response({'detail': 'Invalid member role for delegation.'}, status=status.HTTP_400_BAD_REQUEST)

        account.role = target_role
        account.is_active = True
        account.delegated_by = request.user
        account.delegated_at = timezone.now()

        if account.verification_status == User.VerificationStatus.PENDING and request.user.is_superuser:
            account.verification_status = User.VerificationStatus.VERIFIED
            account.verified_by_superuser = True
            account.verified_at = timezone.now()
            account.verified_by = request.user

        account.save()

        if hasattr(request, 'active_organization') and request.active_organization:
            account.organizations.add(request.active_organization)

        self._create_event(
            account=account,
            actor=request.user,
            event_type=UserOnboardingEvent.EventType.MEMBER_DELEGATED,
            metadata={'role': target_role, 'is_active': True},
            notes='Owner activated/delegated member role.',
        )
        return Response(self.get_serializer(account).data, status=status.HTTP_200_OK)
