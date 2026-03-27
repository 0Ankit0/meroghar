from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from apps.iam.models import User, Organization, OrganizationMembership
from apps.housing.models import Property, Unit, Lease, Tenant
from apps.finance.models import Expense, Invoice, Payment
from datetime import date

class FinanceViewTest(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Finance Org", slug="finance-org")
        self.user = User.objects.create_user(username="accountant", password="password", role="MANAGER")
        OrganizationMembership.objects.create(organization=self.organization, user=self.user, role='OWNER')
        self.client.login(username="accountant", password="password")
        
        self.property = Property.objects.create(
            name="Finance Apts",
            organization=self.organization,
            address="Kathmandu 1",
            city="Kathmandu",
        )

    def test_expense_list_view(self):
        Expense.objects.create(
            organization=self.organization,
            property=self.property,
            amount=100.00,
            expense_date=date.today(),
            category='UTILITIES'
        )
        response = self.client.get(reverse('finance:expense_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "100.00")

    def test_create_expense_view(self):
        response = self.client.post(reverse('finance:expense_add'), {
            'property': self.property.id,
            'amount': '250.00',
            'expense_date': str(date.today()),
            'category': 'MAINTENANCE',
            'description': 'Test Expense'
        })
        if response.status_code != 302:
             print(f"Expense Form Errors: {response.context['form'].errors}")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Expense.objects.filter(amount=250.00).exists())

    @patch("apps.finance.views.payment.KhaltiService.initiate_payment")
    def test_initiate_payment_rejects_cross_org_invoice(self, mock_initiate_payment):
        other_org = Organization.objects.create(name="Other Org", slug="other-org")

        tenant = Tenant.objects.create(
            organization=other_org,
            first_name="Other",
            last_name="Tenant",
            email="other@example.com",
            phone="9800000000",
        )
        property_other = Property.objects.create(
            organization=other_org,
            name="Other Property",
            address="Pokhara 1",
            city="Pokhara",
        )
        unit = Unit.objects.create(
            property=property_other,
            unit_number="101",
            market_rent="10000.00",
        )
        lease = Lease.objects.create(
            organization=other_org,
            tenant=tenant,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            rent_amount="10000.00",
        )
        lease.units.add(unit)
        invoice = Invoice.objects.create(
            organization=other_org,
            lease=lease,
            invoice_number="INV-OTHER-1",
            invoice_date=date(2026, 1, 1),
            due_date=date(2026, 1, 5),
            total_amount="10000.00",
        )

        response = self.client.post(reverse("finance:initiate_payment", kwargs={"invoice_id": invoice.id}))

        self.assertEqual(response.status_code, 404)
        self.assertFalse(Payment.objects.filter(invoice=invoice).exists())
        mock_initiate_payment.assert_not_called()

    @patch("apps.finance.views.payment.KhaltiService.initiate_payment")
    def test_initiate_payment_uses_active_org_invoice(self, mock_initiate_payment):
        tenant = Tenant.objects.create(
            organization=self.organization,
            first_name="Finance",
            last_name="Tenant",
            email="tenant@example.com",
            phone="9800000001",
        )
        unit = Unit.objects.create(
            property=self.property,
            unit_number="201",
            market_rent="12000.00",
        )
        lease = Lease.objects.create(
            organization=self.organization,
            tenant=tenant,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            rent_amount="12000.00",
        )
        lease.units.add(unit)
        invoice = Invoice.objects.create(
            organization=self.organization,
            lease=lease,
            invoice_number="INV-FIN-1",
            invoice_date=date(2026, 1, 1),
            due_date=date(2026, 1, 5),
            total_amount="12000.00",
        )
        mock_initiate_payment.return_value = {
            "pidx": "test-pidx-123",
            "payment_url": "https://khalti.test/pay",
        }

        response = self.client.post(reverse("finance:initiate_payment", kwargs={"invoice_id": invoice.id}))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "https://khalti.test/pay")
        payment = Payment.objects.get(invoice=invoice)
        self.assertEqual(payment.organization, self.organization)
        self.assertEqual(payment.transaction_id, "test-pidx-123")
        mock_initiate_payment.assert_called_once()
