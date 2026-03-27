"""Requirement coverage: OPS-05."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.iam.models import User, Organization, OrganizationMembership
from apps.operations.models import Vendor
from apps.housing.models import Property, Unit

class OperationsApiTest(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Ops API Org", slug="ops-api-org")
        self.other_org = Organization.objects.create(name="Ops Other Org", slug="ops-other-org")
        self.user = User.objects.create_user(username="api_ops", password="password")
        OrganizationMembership.objects.create(organization=self.organization, user=self.user, role='OWNER')
        self.client.login(username="api_ops", password="password")
        
        session = self.client.session
        session['active_org_id'] = str(self.organization.id)
        session.save()
        self.property = Property.objects.create(name="Ops Property", organization=self.organization)
        self.unit = Unit.objects.create(property=self.property, unit_number="OPS-1", market_rent=1200)

    def test_vendor_api_list(self):
        Vendor.objects.create(
            organization=self.organization,
            company_name="API Vendor",
            contact_person="Contact",
            email="vendor@api.com",
            phone="111",
            service_type='GENERAL'
        )
        url = reverse('api-vendor-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_vendor_api_create(self):
        url = reverse('api-vendor-list')
        data = {
            'company_name': 'New API Vendor',
            'contact_person': 'New Contact',
            'email': 'new_vendor@api.com',
            'phone': '222',
            'service_type': 'PLUMBING'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Vendor.objects.count(), 1)

    def test_vendor_detail_denies_cross_org_access(self):
        other_vendor = Vendor.objects.create(
            organization=self.other_org,
            company_name="Other Vendor",
            contact_person="Other Contact",
            email="other_vendor@api.com",
            phone="333",
            service_type='GENERAL',
        )
        url = reverse('api-vendor-detail', args=[other_vendor.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
