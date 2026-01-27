from django.test import TestCase
from rest_framework.test import APIClient
from apps.iam.models import User, Organization
from apps.housing.models import Tenant, Lease, Unit, Property
from apps.finance.models import Invoice
from django.utils import timezone
from datetime import timedelta

class MobileDashboardApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.organization = Organization.objects.create(name="Test Org", slug="test-org")
        
        # Create Tenant User
        self.user = User.objects.create_user(username='tenant', email='tenant@test.com', password='password', role='TENANT')
        self.user.organizations.add(self.organization)
        
        # Property/Unit/Tenant
        self.property = Property.objects.create(name="Test Prop", organization=self.organization)
        self.unit = Unit.objects.create(property=self.property, unit_number="101")
        self.tenant = Tenant.objects.create(
            organization=self.organization, 
            first_name="John", 
            last_name="Doe", 
            email="tenant@test.com",
            user=self.user
        )
        self.lease = Lease.objects.create(
            organization=self.organization, # Added organization to Lease
            tenant=self.tenant, 
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=365),
            rent_amount=1000,
            status='ACTIVE'
        )
        self.lease.units.add(self.unit)
        
        # Invoice
        Invoice.objects.create(
            organization=self.organization,
            lease=self.lease,
            invoice_number="INV-001",
            invoice_date=timezone.now().date(),
            due_date=timezone.now().date() + timedelta(days=5),
            total_amount=1000,
            status='SENT'
        )

    def test_dashboard_stats(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/dashboard/mobile/')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['balance_due'], 1000)
        self.assertEqual(response.data['lease_status'], 'ACTIVE')
        self.assertEqual(response.data['open_requests'], 0)
