from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.iam.models import User, Organization, OrganizationMembership

class IamApiTest(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="IAM API Org", slug="iam-api-org")
        self.user = User.objects.create_user(username="api_iam", password="password", role="ADMIN", is_staff=True)
        OrganizationMembership.objects.create(organization=self.organization, user=self.user, role='OWNER')
        self.client.login(username="api_iam", password="password")
        
        session = self.client.session
        session['active_org_id'] = str(self.organization.id)
        session.save()

    def test_user_api_access(self):
        # Assuming only admins can list users via API or similar policy
        url = reverse('api-user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should contain at least self
        self.assertGreaterEqual(len(response.data), 1)
