"""Requirement coverage: HOU-01, HOU-02."""

from django.test import TestCase
from django.urls import reverse
from apps.iam.models import User, Organization, OrganizationMembership
from apps.housing.models import Property, Unit

class HousingViewTest(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Housing Org", slug="housing-org")
        self.user = User.objects.create_user(username="manager", password="password", role="MANAGER")
        OrganizationMembership.objects.create(organization=self.organization, user=self.user, role='OWNER')
        self.client.login(username="manager", password="password")
        
        self.property = Property.objects.create(name="Sunset Apts", organization=self.organization)

    def test_property_list_view(self):
        response = self.client.get(reverse('housing:property_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sunset Apts")

    def test_property_create_view(self):
        response = self.client.post(reverse('housing:property_add'), {
            'name': 'New Condo',
            'address': '123 Main St',
            'city': 'TestCity',
            'state': 'TS',
            'zip_code': '12345',
            'property_type': 'APARTMENT'
        })
        if response.status_code != 302:
             print(f"Prop Form Errors: {response.context['form'].errors}")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Property.objects.filter(name='New Condo').exists())

    def test_unit_list_view(self):
        Unit.objects.create(property=self.property, unit_number="101", market_rent=1000)
        response = self.client.get(reverse('housing:unit_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "101")
