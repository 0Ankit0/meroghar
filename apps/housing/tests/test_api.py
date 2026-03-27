"""Requirement coverage: HOU-04, HOU-05."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.iam.models import User, Organization, OrganizationMembership
from apps.housing.models import Property, Unit, PropertyInspection, InventoryItem
from datetime import date

class HousingApiTest(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Housing API Org", slug="housing-api-org")
        self.user = User.objects.create_user(username="api_housing", password="password", role="MANAGER")
        OrganizationMembership.objects.create(organization=self.organization, user=self.user, role='OWNER')
        self.client.login(username="api_housing", password="password")
        
        session = self.client.session
        session['active_org_id'] = str(self.organization.id)
        session.save()
        
        self.property = Property.objects.create(name="API Property", organization=self.organization)
        self.unit = Unit.objects.create(property=self.property, unit_number="A1", market_rent=1000)

    def test_inspection_api_list(self):
        PropertyInspection.objects.create(
            organization=self.organization,
            unit=self.unit,
            inspector=self.user,
            inspection_date=date.today(),
            status='COMPLETED'
        )
        url = reverse('api-inspection-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_inventory_api_create(self):
        url = reverse('api-inventory-list')
        data = {
            'unit': self.unit.id,
            'name': 'API Microwave',
            'category': 'APPLIANCE',
            'condition': 'NEW'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(InventoryItem.objects.count(), 1)
        self.assertEqual(InventoryItem.objects.get().name, 'API Microwave')
