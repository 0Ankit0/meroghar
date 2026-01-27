from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.iam.models import User, Organization
from apps.operations.models import Vendor

class OperationsApiTest(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Ops API Org", slug="ops-api-org")
        self.user = User.objects.create_user(username="api_ops", password="password")
        self.user.organizations.add(self.organization)
        self.client.login(username="api_ops", password="password")
        
        session = self.client.session
        session['active_org_id'] = str(self.organization.id)
        session.save()

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
