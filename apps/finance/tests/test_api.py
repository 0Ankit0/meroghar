"""Requirement coverage: FIN-05."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.iam.models import User, Organization, OrganizationMembership
from apps.housing.models import Property
from apps.finance.models import Expense
from datetime import date

class FinanceApiTest(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Finance API Org", slug="fin-api-org")
        self.user = User.objects.create_user(username="api_fin", password="password")
        OrganizationMembership.objects.create(organization=self.organization, user=self.user, role='OWNER')
        self.client.login(username="api_fin", password="password")
        
        session = self.client.session
        session['active_org_id'] = str(self.organization.id)
        session.save()
        
        self.property = Property.objects.create(name="Fin Property", organization=self.organization)

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
