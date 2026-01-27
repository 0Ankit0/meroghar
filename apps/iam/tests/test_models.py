from django.test import TestCase
from apps.iam.models import User, Organization

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
