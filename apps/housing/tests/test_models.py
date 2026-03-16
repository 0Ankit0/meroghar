from django.test import TestCase
from apps.iam.models import User, Organization, OrganizationMembership
from apps.housing.models import Property, Unit, Lease, PropertyInspection, InventoryItem, Tenant
from django.core.exceptions import ValidationError
from datetime import date, timedelta

class HousingModelTest(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Housing Org", slug="housing-org")
        self.user = User.objects.create_user(username="manager", password="password")
        OrganizationMembership.objects.create(organization=self.organization, user=self.user, role='OWNER')
        self.property = Property.objects.create(name="Sunset Apts", organization=self.organization)
        self.unit = Unit.objects.create(property=self.property, unit_number="101", market_rent=1200)
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="1234567890"
        )

    def test_create_property_unit(self):
        self.assertEqual(self.property.name, "Sunset Apts")
        self.assertEqual(self.unit.market_rent, 1200)

    def test_lease_creation_and_overlap(self):
        # Create initial lease
        lease1 = Lease.objects.create(
            organization=self.organization,
            tenant=self.tenant,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            rent_amount=1200,
            status='ACTIVE'
        )
        lease1.units.add(self.unit)
        self.assertEqual(str(lease1), f"Lease: {self.tenant} - 1 Units")

        # Create overlapping lease (should fail validation)
        lease2 = Lease.objects.create(
            organization=self.organization,
            tenant=self.tenant,
            start_date=date(2023, 6, 1), # Overlaps
            end_date=date(2024, 6, 1),
            rent_amount=1300
        )
        lease2.units.add(self.unit)
        
        with self.assertRaises(ValidationError):
            lease2.full_clean()

    def test_create_inspection(self):
        inspection = PropertyInspection.objects.create(
            organization=self.organization,
            unit=self.unit,
            inspector=self.user,
            inspection_date=date.today(),
            status='COMPLETED',
            condition_rating=5
        )
        self.assertEqual(inspection.status, 'COMPLETED')

    def test_create_inventory(self):
        item = InventoryItem.objects.create(
            organization=self.organization,
            unit=self.unit,
            name="Refrigerator",
            purchase_date=date(2022, 1, 1),
            condition='GOOD',
            category='APPLIANCE'
        )
        self.assertEqual(item.name, "Refrigerator")
