from django.test import TestCase
from django.utils import timezone
from apps.crm.models import Lead, Showing, RentalApplication
from apps.iam.models import User, Organization, OrganizationMembership
from apps.housing.models import Property, Unit

class CrmModelTest(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Test Org", slug="test-org")
        self.user = User.objects.create_user(username="agent", password="password")
        OrganizationMembership.objects.create(organization=self.organization, user=self.user, role='OWNER')
        self.property = Property.objects.create(name="Test Property", organization=self.organization)
        self.unit = Unit.objects.create(property=self.property, unit_number="101", market_rent=1000)

    def test_create_lead(self):
        lead = Lead.objects.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            organization=self.organization,
            status="NEW"
        )
        self.assertEqual(lead.full_name, "John Doe")
        self.assertEqual(lead.status, "NEW")

    def test_create_showing(self):
        lead = Lead.objects.create(
            first_name="Jane",
            last_name="Doe",
            organization=self.organization
        )
        showing = Showing.objects.create(
            lead=lead,
            unit=self.unit,
            showing_agent=self.user,
            start_time=timezone.now(),
            end_time=timezone.now() + timezone.timedelta(hours=1),
            status="SCHEDULED"
        )
        self.assertEqual(showing.lead, lead)
        self.assertEqual(showing.unit, self.unit)

    def test_create_application(self):
        lead = Lead.objects.create(
            first_name="Alice",
            last_name="Smith",
            organization=self.organization
        )
        application = RentalApplication.objects.create(
            lead=lead,
            unit=self.unit,
            status="PENDING",
            annual_income=50000
        )
        self.assertEqual(application.status, "PENDING")
        self.assertEqual(application.unit, self.unit)
