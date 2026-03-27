"""Requirement coverage: IAM-02, IAM-03."""

from django.test import TestCase

from apps.iam.models import Organization, User


class IamModelTest(TestCase):
    def test_create_organization(self):
        org = Organization.objects.create(name="Test Org", slug="test-org")
        self.assertEqual(org.name, "Test Org")
        self.assertEqual(org.slug, "test-org")

    def test_create_user(self):
        user = User.objects.create_user(username="testuser", password="password", role="MANAGER")
        self.assertTrue(user.check_password("password"))
        self.assertEqual(user.role, "MANAGER")

    def test_user_organization_relationship(self):
        org = Organization.objects.create(name="Test Org", slug="test-org")
        user = User.objects.create_user(username="testuser", password="password")
        user.organizations.add(org)
        self.assertIn(org, user.organizations.all())

    def test_can_access_platform_depends_on_verification(self):
        user = User.objects.create_user(
            username='pending_user',
            password='password',
            verification_status=User.VerificationStatus.PENDING,
            is_active=True,
        )
        self.assertFalse(user.can_access_platform())

        user.verification_status = User.VerificationStatus.VERIFIED
        self.assertTrue(user.can_access_platform())
