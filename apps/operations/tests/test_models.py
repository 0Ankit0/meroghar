"""Requirement coverage: OPS-01, OPS-05."""

from django.test import TestCase
from apps.iam.models import User, Organization, OrganizationMembership
from apps.housing.models import Property, Unit, Tenant
from apps.operations.models import Vendor, WorkOrder
from datetime import date

class OperationsModelTest(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Ops Org", slug="ops-org")
        self.user = User.objects.create_user(username="manager", password="password")
        OrganizationMembership.objects.create(organization=self.organization, user=self.user, role='OWNER')
        
        self.property = Property.objects.create(name="Ops Apts", organization=self.organization)
        self.unit = Unit.objects.create(property=self.property, unit_number="303", market_rent=1400)
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            first_name="Bob",
            last_name="Tenant",
            email="bob@example.com",
            phone="1112223333"
        )

    def test_create_vendor(self):
        vendor = Vendor.objects.create(
            organization=self.organization,
            company_name="Bob's Plumbing",
            contact_person="Bob Plumber",
            email="bob@plumbing.com",
            phone="9998887777",
            service_type='PLUMBING',
            hourly_rate=80.00
        )
        self.assertEqual(vendor.company_name, "Bob's Plumbing")
        self.assertEqual(vendor.service_type, 'PLUMBING')

    def test_create_work_order(self):
        vendor = Vendor.objects.create(
            organization=self.organization,
            company_name="Bob's Plumbing",
            contact_person="Bob Plumber",
            email="bob@plumbing.com",
            phone="9998887777",
            service_type='PLUMBING'
        )
        wo = WorkOrder.objects.create(
            organization=self.organization,
            unit=self.unit,
            requester=self.tenant,
            title="Leaky Faucet",
            description="Faucet in kitchen leaking",
            priority='MEDIUM',
            status='OPEN',
            assigned_vendor=vendor
        )
        self.assertEqual(wo.title, "Leaky Faucet")
        self.assertEqual(wo.assigned_vendor, vendor)
