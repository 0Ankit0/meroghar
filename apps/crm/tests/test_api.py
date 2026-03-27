from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.iam.models import User, Organization, OrganizationMembership
from apps.crm.models import Lead

class CrmApiTest(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Test API Org", slug="test-api-org")
        self.other_org = Organization.objects.create(name="CRM Other Org", slug="crm-other-org")
        self.user = User.objects.create_user(username="api_user", password="password", role="ADMIN")
        OrganizationMembership.objects.create(organization=self.organization, user=self.user, role='OWNER')
        self.client.login(username="api_user", password="password")
        
        # Set active organization in session for middleware
        session = self.client.session
        session['active_org_id'] = str(self.organization.id)
        session.save()
        
    def test_lead_api_list(self):
        Lead.objects.create(first_name="API", last_name="Lead", organization=self.organization)
        url = reverse('api-lead-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['first_name'], "API")

    def test_lead_api_create(self):
        url = reverse('api-lead-list')
        data = {
            'first_name': 'New API',
            'last_name': 'Lead',
            'email': 'api@example.com',
            'phone': '9876543210',
            'status': 'NEW',
            'source': 'WEBSITE'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Lead.objects.count(), 1)
        self.assertEqual(Lead.objects.get().email, 'api@example.com')

    def test_lead_detail_denies_cross_org_access(self):
        other_lead = Lead.objects.create(
            first_name="Other",
            last_name="Lead",
            organization=self.other_org,
        )
        url = reverse('api-lead-detail', args=[other_lead.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
