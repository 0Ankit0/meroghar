from django.test import TestCase
from django.urls import reverse
from apps.iam.models import User, Organization
from apps.crm.models import Lead

class CrmViewTest(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Test Org", slug="test-org")
        self.user = User.objects.create_user(username="testuser", password="password", role="ADMIN")
        self.user.organizations.add(self.organization)
        self.client.login(username="testuser", password="password")

    def test_lead_list_view(self):
        Lead.objects.create(first_name="Lead", last_name="One", organization=self.organization)
        response = self.client.get(reverse('crm:lead_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Lead One")

    def test_lead_create_view(self):
        response = self.client.post(reverse('crm:lead_add'), {
            'first_name': 'New',
            'last_name': 'Lead',
            'email': 'new@example.com',
            'phone': '1234567890',
            'status': 'NEW',
            'source': 'WEBSITE'
        })
        if response.status_code != 302:
             print(f"Form Errors: {response.context['form'].errors}")
        self.assertEqual(response.status_code, 302) # Redirects on success
        self.assertTrue(Lead.objects.filter(email='new@example.com').exists())
