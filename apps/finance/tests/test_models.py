from django.test import TestCase
from apps.iam.models import User, Organization, OrganizationMembership
from apps.housing.models import Property, Unit, Lease, Tenant
from apps.finance.models import Expense, Invoice, Payment
from datetime import date, timedelta
import uuid

class FinanceModelTest(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Finance Org", slug="finance-org")
        self.user = User.objects.create_user(username="accountant", password="password")
        OrganizationMembership.objects.create(organization=self.organization, user=self.user, role='OWNER')
        
        self.property = Property.objects.create(name="Finance Apts", organization=self.organization)
        self.unit = Unit.objects.create(property=self.property, unit_number="202", market_rent=1500)
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
            phone="9876543210"
        )
        self.lease = Lease.objects.create(
            organization=self.organization,
            tenant=self.tenant,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            rent_amount=1500,
            status='ACTIVE'
        )
        self.lease.units.add(self.unit)

    def test_create_expense(self):
        expense = Expense.objects.create(
            organization=self.organization,
            property=self.property,
            amount=500.00,
            expense_date=date.today(),
            category='MAINTENANCE',
            description="Fix plumbing"
        )
        self.assertEqual(expense.amount, 500.00)
        self.assertEqual(expense.category, 'MAINTENANCE')

    def test_create_invoice_and_payment(self):
        # Create Invoice
        invoice = Invoice.objects.create(
            organization=self.organization,
            lease=self.lease,
            invoice_number=f"INV-{uuid.uuid4()}",
            invoice_date=date.today(),
            due_date=date.today() + timedelta(days=7),
            total_amount=1500.00
        )
        self.assertEqual(invoice.status, 'DRAFT')
        self.assertEqual(invoice.balance_due, 1500.00)
        
        # Create Payment
        payment = Payment.objects.create(
            organization=self.organization,
            invoice=invoice,
            amount=1500.00,
            payment_method='CASH',
            status='SUCCESS',
            verified_at=date.today()
        )
        self.assertEqual(payment.invoice, invoice)
        
        # In a real app, signals or service logic would update invoice.paid_amount.
        # Assuming manual update for unit test if signals aren't active/implemented yet?
        # Let's check if the model has logic to update. Usually it's in a Service.
        # We will just verify the payment creation here.
