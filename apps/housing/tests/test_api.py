from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.iam.models import User, Organization, OrganizationMembership
from apps.housing.models import Property, Unit, PropertyInspection, InventoryItem, Tenant, Lease, LeaseRenewal
from datetime import date
from datetime import timedelta

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
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            first_name='Lease',
            last_name='Tenant',
            email='lease@test.com',
        )
        self.lease = Lease.objects.create(
            organization=self.organization,
            tenant=self.tenant,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            rent_amount=1000,
            status='ACTIVE',
        )
        self.lease.units.add(self.unit)

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

    def test_lease_renewal_approve_creates_renewal_lease(self):
        renewal = LeaseRenewal.objects.create(
            lease=self.lease,
            proposed_start_date=self.lease.end_date + timedelta(days=1),
            proposed_end_date=self.lease.end_date + timedelta(days=366),
            proposed_rent_amount=1100,
            status='REQUESTED',
        )
        url = reverse('api-lease-renewal-detail', kwargs={'pk': renewal.id})
        response = self.client.patch(url, {'status': 'APPROVED'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        renewal.refresh_from_db()
        self.assertEqual(renewal.status, 'APPROVED')
        self.assertIsNotNone(renewal.renewal_lease)
