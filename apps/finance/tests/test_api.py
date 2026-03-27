"""Requirement coverage: FIN-05."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.iam.models import User, Organization, OrganizationMembership
from apps.housing.models import Property, Unit, Tenant, Lease
from apps.finance.models import Expense, Invoice
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
        self.unit = Unit.objects.create(property=self.property, unit_number="F-1", market_rent=1000)
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            first_name='Fin',
            last_name='Tenant',
            email='tenant@fin.com',
        )
        self.lease = Lease.objects.create(
            organization=self.organization,
            tenant=self.tenant,
            start_date=date.today() - timedelta(days=60),
            end_date=date.today() + timedelta(days=300),
            rent_amount=1000,
            status='ACTIVE',
        )
        self.lease.units.add(self.unit)

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

    def test_invoice_list_applies_late_fee_to_overdue_invoice(self):
        invoice = Invoice.objects.create(
            organization=self.organization,
            lease=self.lease,
            invoice_number='INV-LATE-1',
            invoice_date=date.today() - timedelta(days=40),
            due_date=date.today() - timedelta(days=10),
            total_amount=1000,
            paid_amount=0,
            status='SENT',
        )
        response = self.client.get(reverse('api-invoice-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        invoice.refresh_from_db()
        self.assertEqual(float(invoice.late_fee_amount), 50.00)
