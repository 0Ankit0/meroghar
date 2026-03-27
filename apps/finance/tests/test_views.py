"""Requirement coverage: FIN-05."""

from django.test import TestCase, Client
from django.urls import reverse

from apps.finance.admin.payment import PaymentAdmin
from apps.finance.models import Expense, Invoice, Payment
from apps.housing.models import Lease, Property, Tenant, Unit
from apps.iam.models import Organization, OrganizationMembership, User


class FinanceViewTest(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Finance Org", slug="finance-org")
        self.user = User.objects.create_user(username="accountant", password="password", role="MANAGER")
        OrganizationMembership.objects.create(organization=self.organization, user=self.user, role='OWNER')
        self.client.login(username="accountant", password="password")

        session = self.client.session
        session['active_org_id'] = str(self.organization.id)
        session.save()

        self.property = Property.objects.create(
            name="Finance Apts",
            organization=self.organization,
            address="Kathmandu",
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
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Expense.objects.filter(amount=250.00).exists())


class PaymentFlowViewTest(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Pay Org", slug="pay-org")
        self.user = User.objects.create_user(username="payer", password="password", role="MANAGER")
        OrganizationMembership.objects.create(organization=self.organization, user=self.user, role='OWNER')
        self.client = Client()
        self.client.login(username="payer", password="password")
        session = self.client.session
        session['active_org_id'] = str(self.organization.id)
        session.save()

        self.property = Property.objects.create(
            organization=self.organization,
            name="Pay Property",
            address="Street",
            city="Kathmandu",
        )
        self.unit = Unit.objects.create(property=self.property, unit_number="101")
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            first_name="Test",
            last_name="Tenant",
            email="tenant@example.com",
            phone="9800000000",
        )
        self.lease = Lease.objects.create(
            organization=self.organization,
            tenant=self.tenant,
            start_date=date.today() - timedelta(days=10),
            end_date=date.today() + timedelta(days=355),
            rent_amount=Decimal("1000.00"),
        )
        self.lease.units.add(self.unit)
        self.invoice = Invoice.objects.create(
            organization=self.organization,
            lease=self.lease,
            invoice_number="INV-DOUBLE-001",
            invoice_date=date.today(),
            due_date=date.today() + timedelta(days=5),
            subtotal=Decimal("100.00"),
            tax=Decimal("0.00"),
            total_amount=Decimal("100.00"),
            status=Invoice.Status.SENT,
        )

    @patch('apps.finance.views.payment.KhaltiService.initiate_payment')
    def test_double_click_initiate_creates_single_pending_record(self, mock_initiate):
        mock_initiate.return_value = {'pidx': 'pidx-123', 'payment_url': 'https://khalti.test/pay'}
        url = reverse('finance:initiate_payment', kwargs={'invoice_id': self.invoice.id})

        first = self.client.post(url)
        second = self.client.post(url)

        self.assertEqual(first.status_code, 302)
        self.assertEqual(second.status_code, 302)
        self.assertEqual(mock_initiate.call_count, 2)
        self.assertEqual(
            Payment.objects.filter(
                invoice=self.invoice,
                provider=Payment.Provider.KHALTI,
                transaction_id='pidx-123',
            ).count(),
            1,
        )

    @patch('apps.finance.views.payment.KhaltiService.verify_payment')
    def test_duplicate_callback_is_idempotent_success(self, mock_verify):
        payment = Payment.objects.create(
            organization=self.organization,
            invoice=self.invoice,
            amount=Decimal("100.00"),
            provider=Payment.Provider.KHALTI,
            status=Payment.Status.INITIATED,
            transaction_id='pidx-cb-1',
        )
        mock_verify.return_value = {'status': 'Completed', 'pidx': 'pidx-cb-1'}
        url = reverse('finance:verify_payment')

        first = self.client.get(f'{url}?pidx=pidx-cb-1')
        second = self.client.get(f'{url}?pidx=pidx-cb-1')

        self.assertEqual(first.status_code, 302)
        self.assertEqual(second.status_code, 302)
        payment.refresh_from_db()
        self.invoice.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.SUCCESS)
        self.assertEqual(self.invoice.paid_amount, Decimal("100.00"))
        self.assertEqual(mock_verify.call_count, 1)

    def test_admin_reversal_transitions_invoice_and_payment(self):
        payment = Payment.objects.create(
            organization=self.organization,
            invoice=self.invoice,
            amount=Decimal("100.00"),
            provider=Payment.Provider.KHALTI,
            status=Payment.Status.SUCCESS,
            transaction_id='pidx-admin-1',
        )
        self.invoice.paid_amount = Decimal("100.00")
        self.invoice.status = Invoice.Status.PAID
        self.invoice.save(update_fields=['paid_amount', 'status', 'updated_at'])

        model_admin = PaymentAdmin(Payment, AdminSite())
        request = RequestFactory().post('/admin/finance/payment/')
        request.user = self.user
        model_admin.mark_refunded(request, Payment.objects.filter(pk=payment.pk))

        payment.refresh_from_db()
        self.invoice.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.REFUNDED)
        self.assertEqual(self.invoice.paid_amount, Decimal("0"))
        self.assertEqual(self.invoice.status, Invoice.Status.SENT)
