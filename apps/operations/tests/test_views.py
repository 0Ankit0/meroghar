"""Requirement coverage: OPS-05."""

from django.test import TestCase, Client
from django.urls import reverse
from apps.iam.models import User, Organization, OrganizationMembership
from apps.operations.models import Vendor

class OperationsViewTest(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Ops Org", slug="ops-org")
        self.user = User.objects.create_user(username="manager", password="password", role="MANAGER")
        OrganizationMembership.objects.create(organization=self.organization, user=self.user, role='OWNER')
        self.client.login(username="manager", password="password")

    def test_vendor_list_view(self):
        Vendor.objects.create(
            organization=self.organization,
            company_name="Test Vendor",
            contact_person="Tester",
            email="test@vendor.com",
            phone="123",
            service_type='GENERAL'
        )
        response = self.client.get(reverse('operations:vendor_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Vendor")

    def test_create_vendor_view(self):
        response = self.client.post(reverse('operations:vendor_add'), {
            'company_name': 'New Vendor',
            'contact_person': 'New Contact',
            'email': 'new@vendor.com',
            'phone': '123456',
            'service_type': 'HVAC',
            'hourly_rate': '100.00'
        })
        if response.status_code != 302:
             print(f"Vendor Form Errors: {response.context['form'].errors}")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Vendor.objects.filter(company_name='New Vendor').exists())
