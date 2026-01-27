from django.test import TestCase, Client
from django.urls import reverse
from apps.iam.models import User, Organization
from apps.housing.models import Property, Unit, Lease, Tenant
from apps.finance.models import Expense
from datetime import date

class FinanceViewTest(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Finance Org", slug="finance-org")
        self.user = User.objects.create_user(username="accountant", password="password", role="MANAGER")
        self.user.organizations.add(self.organization)
        self.client.login(username="accountant", password="password")
        
        self.property = Property.objects.create(name="Finance Apts", organization=self.organization)

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
