from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.iam.models import Organization, User, UserOnboardingEvent


class IamApiTest(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="IAM API Org", slug="iam-api-org")
        self.superuser = User.objects.create_superuser(
            username="super_iam",
            email="super@example.com",
            password="password",
        )
        self.owner = User.objects.create_user(
            username="owner_iam",
            password="password",
            role=User.Role.OWNER,
            is_staff=True,
            verification_status=User.VerificationStatus.VERIFIED,
        )
        self.owner.organizations.add(self.organization)

    def authenticate(self, user):
        self.client.force_authenticate(user=user)
        session = self.client.session
        session['active_org_id'] = str(self.organization.id)
        session.save()

    def test_user_api_access(self):
        self.authenticate(self.superuser)
        url = reverse('api-user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_owner_creates_pending_account(self):
        self.authenticate(self.owner)
        url = reverse('api-user-create-pending-account')
        payload = {
            'username': 'pending_member',
            'email': 'pending@example.com',
            'password': 'strong-password',
            'first_name': 'Pending',
            'last_name': 'Member',
        }
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = User.objects.get(username='pending_member')
        self.assertEqual(created.verification_status, User.VerificationStatus.PENDING)
        self.assertTrue(created.provisioned_by_owner)
        self.assertEqual(created.created_by, self.owner)
        self.assertEqual(created.organizations.first(), self.organization)
        self.assertTrue(
            UserOnboardingEvent.objects.filter(
                account=created,
                actor=self.owner,
                event_type=UserOnboardingEvent.EventType.CREATED,
            ).exists()
        )

    def test_superuser_verifies_account(self):
        member = User.objects.create_user(
            username='pending_verification',
            password='password',
            verification_status=User.VerificationStatus.PENDING,
            is_active=False,
        )
        self.authenticate(self.superuser)

        url = reverse('api-user-verify-account', kwargs={'pk': member.id})
        response = self.client.post(url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        member.refresh_from_db()
        self.assertEqual(member.verification_status, User.VerificationStatus.VERIFIED)
        self.assertTrue(member.verified_by_superuser)
        self.assertEqual(member.verified_by, self.superuser)
        self.assertIsNotNone(member.verified_at)

    def test_owner_delegates_member_role(self):
        member = User.objects.create_user(
            username='member_delegate',
            password='password',
            verification_status=User.VerificationStatus.VERIFIED,
            is_active=False,
        )
        self.authenticate(self.owner)

        url = reverse('api-user-activate-delegate-member-role', kwargs={'pk': member.id})
        response = self.client.post(url, {'role': User.Role.MANAGER}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        member.refresh_from_db()
        self.assertEqual(member.role, User.Role.MANAGER)
        self.assertEqual(member.delegated_by, self.owner)
        self.assertTrue(member.is_active)
        self.assertEqual(member.organizations.first(), self.organization)

    def test_superuser_assigns_owner_role(self):
        candidate = User.objects.create_user(username='owner_candidate', password='password')
        self.authenticate(self.superuser)

        url = reverse('api-user-assign-organization-owner-role', kwargs={'pk': candidate.id})
        response = self.client.post(url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        candidate.refresh_from_db()
        self.assertEqual(candidate.role, User.Role.OWNER)
        self.assertEqual(candidate.delegated_by, self.superuser)
