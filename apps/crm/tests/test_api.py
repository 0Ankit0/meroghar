"""Requirement coverage: CRM-01."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.iam.models import User, Organization, OrganizationMembership
from apps.crm.models import Lead, Showing
from apps.housing.models import Property, Unit
from django.utils import timezone
from datetime import timedelta

class CrmApiTest(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Test API Org", slug="test-api-org")
        self.user = User.objects.create_user(username="api_user", password="password", role="ADMIN")
        OrganizationMembership.objects.create(organization=self.organization, user=self.user, role='OWNER')
        self.client.login(username="api_user", password="password")
        
        # Set active organization in session for middleware
        session = self.client.session
        session['active_org_id'] = str(self.organization.id)
        session.save()
        self.property = Property.objects.create(name="CRM Property", organization=self.organization)
        self.unit = Unit.objects.create(property=self.property, unit_number="C-1")
        
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

    def test_follow_up_api_create(self):
        lead = Lead.objects.create(first_name="A", last_name="Lead", organization=self.organization, email='a@a.com', phone='1')
        url = reverse('api-follow-up-list')
        response = self.client.post(url, {
            'lead': str(lead.id),
            'channel': 'EMAIL',
            'scheduled_at': (timezone.now() + timedelta(days=1)).isoformat(),
            'status': 'PENDING',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_showing_completion_sets_completed_at(self):
        lead = Lead.objects.create(first_name="B", last_name="Lead", organization=self.organization, email='b@b.com', phone='2')
        showing = Showing.objects.create(
            lead=lead,
            unit=self.unit,
            showing_agent=self.user,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=1),
            status='SCHEDULED',
        )
        url = reverse('api-showing-detail', kwargs={'pk': showing.id})
        response = self.client.patch(url, {'status': 'COMPLETED'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        showing.refresh_from_db()
        self.assertIsNotNone(showing.completed_at)
