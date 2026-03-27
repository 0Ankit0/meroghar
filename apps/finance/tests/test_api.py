"""Requirement coverage: FIN-05."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.iam.models import User, Organization, OrganizationMembership
from apps.housing.models import Property, Tenant, Lease, Unit
from apps.finance.models import Expense, Invoice
from django.utils import timezone
from datetime import timedelta
from datetime import date
from datetime import timedelta

class FinanceApiTest(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Finance API Org", slug="fin-api-org")
        self.user = User.objects.create_user(username="api_fin", password="password", role='MANAGER')
        OrganizationMembership.objects.create(organization=self.organization, user=self.user, role='OWNER')
        self.client.login(username="api_fin", password="password")

        session = self.client.session
        session['active_org_id'] = str(self.organization.id)
        session.save()
        
        self.property = Property.objects.create(name="Fin Property", organization=self.organization)
        self.other_org = Organization.objects.create(name="Finance Other Org", slug="finance-other-org")

    def test_expense_api_create(self):
        url = reverse('api-expense-list')
        data = {
            'property': self.property.id,
            'amount': '150.00',
            'expense_date': str(date.today()),
            'category': 'UTILITIES',
            'description': 'API Expense'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Expense.objects.count(), 1)
        self.assertEqual(float(Expense.objects.get().amount), 150.00)

    def test_invoice_detail_denies_cross_org_access(self):
        other_tenant_user = User.objects.create_user(username="other_tenant_fin", password="password", role="TENANT")
        OrganizationMembership.objects.create(organization=self.other_org, user=other_tenant_user, role='OWNER')
        other_property = Property.objects.create(name="Other Fin Property", organization=self.other_org)
        other_tenant = Tenant.objects.create(
            organization=self.other_org,
            first_name="Other",
            last_name="Tenant",
            email="other-fin@test.com",
            user=other_tenant_user,
        )
        other_lease = Lease.objects.create(
            organization=self.other_org,
            tenant=other_tenant,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=365),
            rent_amount=1200,
            status='ACTIVE',
        )
        other_unit = Unit.objects.create(property=other_property, unit_number="B1", market_rent=1200)
        other_lease.units.add(other_unit)
        other_invoice = Invoice.objects.create(
            organization=self.other_org,
            lease=other_lease,
            invoice_number="INV-OTHER-001",
            invoice_date=timezone.now().date(),
            due_date=timezone.now().date() + timedelta(days=7),
            total_amount=1200,
            status='SENT',
        )

        url = reverse('api-invoice-detail', args=[other_invoice.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
