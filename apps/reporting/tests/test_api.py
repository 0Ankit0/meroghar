"""Requirement coverage: RPT-02, TEN-03, FIN-01."""

from django.test import TestCase
from rest_framework.test import APIClient
from apps.iam.models import User, Organization, OrganizationMembership
from apps.housing.models import Tenant, Lease, Unit, Property
from apps.finance.models import Invoice
from apps.operations.models import WorkOrder
from django.utils import timezone
from datetime import timedelta

class MobileDashboardApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.organization = Organization.objects.create(name="Test Org", slug="test-org")
        self.other_org = Organization.objects.create(name="Other Test Org", slug="other-test-org")
        
        # Create Tenant User
        self.user = User.objects.create_user(username='tenant', email='tenant@test.com', password='password', role='TENANT')
        OrganizationMembership.objects.create(organization=self.organization, user=self.user, role='OWNER')
        
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

        # Cross-org records for the same user should not leak into dashboard totals
        other_property = Property.objects.create(name="Other Prop", organization=self.other_org)
        other_unit = Unit.objects.create(property=other_property, unit_number="202")
        other_tenant = Tenant.objects.create(
            organization=self.other_org,
            first_name="John",
            last_name="Doe",
            email="tenant@test.com",
            user=self.user,
        )
        other_lease = Lease.objects.create(
            organization=self.other_org,
            tenant=other_tenant,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=365),
            rent_amount=2000,
            status='ACTIVE',
        )
        other_lease.units.add(other_unit)
        Invoice.objects.create(
            organization=self.other_org,
            lease=other_lease,
            invoice_number="INV-OTHER-001",
            invoice_date=timezone.now().date(),
            due_date=timezone.now().date() + timedelta(days=3),
            total_amount=2000,
            status='SENT',
        )
        WorkOrder.objects.create(
            organization=self.other_org,
            unit=other_unit,
            requester=other_tenant,
            title="Other Org WO",
            description="Should not be counted",
            status='OPEN',
        )

    def test_dashboard_stats(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/dashboard/mobile/')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['balance_due'], 1000)
        self.assertEqual(response.data['lease_status'], 'ACTIVE')
        self.assertEqual(response.data['open_requests'], 0)

    def test_reporting_kpis_endpoint(self):
        self.client.force_authenticate(user=self.user)
        session = self.client.session
        session['active_org_id'] = str(self.organization.id)
        session.save()
        WorkOrder.objects.create(
            organization=self.organization,
            unit=self.unit,
            requester=self.tenant,
            title='Fix faucet',
            description='Leak',
            status='OPEN',
        )
        response = self.client.get('/api/reporting/kpis/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('occupancy', response.data)
        self.assertIn('receivables', response.data)
        self.assertIn('maintenance', response.data)
