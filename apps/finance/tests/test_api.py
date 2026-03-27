from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.finance.models import Expense, Invoice, Payment
from apps.housing.models import Lease, Property, Tenant, Unit
from apps.iam.models import Organization, OrganizationMembership, User


class FinanceApiTest(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Finance API Org", slug="fin-api-org")
        self.user = User.objects.create_user(username="api_fin", password="password", role='MANAGER')
        OrganizationMembership.objects.create(organization=self.organization, user=self.user, role='OWNER')
        self.client.login(username="api_fin", password="password")

        session = self.client.session
        session['active_org_id'] = str(self.organization.id)
        session.save()

        self.property = Property.objects.create(
            name="Fin Property",
            organization=self.organization,
            address="Street",
            city="Kathmandu",
        )

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


class PaymentVerificationApiTest(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Pay API Org", slug="pay-api-org")
        self.user = User.objects.create_user(username="api_payer", password="password", role='MANAGER')
        OrganizationMembership.objects.create(organization=self.organization, user=self.user, role='OWNER')
        self.client.login(username="api_payer", password="password")
        session = self.client.session
        session['active_org_id'] = str(self.organization.id)
        session.save()

        self.property = Property.objects.create(
            organization=self.organization,
            name="API Property",
            address="Street",
            city="Kathmandu",
        )
        self.unit = Unit.objects.create(property=self.property, unit_number="201")
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            first_name="Api",
            last_name="Tenant",
            email="api-tenant@example.com",
            phone="9800000001",
        )
        self.lease = Lease.objects.create(
            organization=self.organization,
            tenant=self.tenant,
            start_date=date.today() - timedelta(days=20),
            end_date=date.today() + timedelta(days=345),
            rent_amount=Decimal("1100.00"),
        )
        self.lease.units.add(self.unit)
        self.invoice = Invoice.objects.create(
            organization=self.organization,
            lease=self.lease,
            invoice_number="INV-API-001",
            invoice_date=date.today(),
            due_date=date.today() + timedelta(days=7),
            subtotal=Decimal("150.00"),
            tax=Decimal("0.00"),
            total_amount=Decimal("150.00"),
            status=Invoice.Status.SENT,
        )

    @patch('apps.finance.api.views.KhaltiService.verify_payment')
    def test_duplicate_verify_callback_returns_noop_success(self, mock_verify):
        Payment.objects.create(
            organization=self.organization,
            invoice=self.invoice,
            amount=Decimal("150.00"),
            provider=Payment.Provider.KHALTI,
            status=Payment.Status.INITIATED,
            transaction_id='pidx-api-1',
        )
        mock_verify.return_value = {'status': 'Completed', 'pidx': 'pidx-api-1'}
        url = reverse('api-payment-verify')

        first = self.client.post(url, {'pidx': 'pidx-api-1'}, format='json')
        second = self.client.post(url, {'pidx': 'pidx-api-1'}, format='json')

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertFalse(first.data['already_verified'])
        self.assertTrue(second.data['already_verified'])
        self.assertEqual(mock_verify.call_count, 1)
