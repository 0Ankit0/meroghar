from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.iam.models import Organization, User


class IamApiTest(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="IAM API Org", slug="iam-api-org")
        self.organization_2 = Organization.objects.create(name="IAM API Org 2", slug="iam-api-org-2")
        self.other_org = Organization.objects.create(name="Other Org", slug="other-org")

        self.user = User.objects.create_user(
            username="api_iam",
            password="password",
            role="ADMIN",
            is_staff=True,
        )
        self.user.organizations.add(self.organization, self.organization_2)

        self.client.login(username="api_iam", password="password")
        session = self.client.session
        session['active_org_id'] = str(self.organization.id)
        session.save()

    def test_user_api_access(self):
        url = reverse('api-user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_login_returns_token_and_profile(self):
        self.client.logout()
        url = reverse('api-iam-login')

        response = self.client.post(
            url,
            {'username': 'api_iam', 'password': 'password'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['username'], self.user.username)
        self.assertEqual(response.data['user']['active_organization']['id'], str(self.organization.id))

    def test_profile_with_token_auth(self):
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        url = reverse('api-iam-profile')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.user.username)
        self.assertEqual(response.data['active_organization']['id'], str(self.organization.id))

    def test_memberships_and_switch_organization(self):
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        memberships_url = reverse('api-iam-memberships')
        memberships_response = self.client.get(memberships_url)
        self.assertEqual(memberships_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(memberships_response.data), 2)

        switch_url = reverse('api-iam-switch-organization')
        switch_response = self.client.post(
            switch_url,
            {'organization_id': str(self.organization_2.id)},
            format='json',
        )

        self.assertEqual(switch_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            switch_response.data['active_organization']['id'],
            str(self.organization_2.id),
        )

    def test_switch_organization_requires_membership(self):
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        switch_url = reverse('api-iam-switch-organization')
        response = self.client.post(
            switch_url,
            {'organization_id': str(self.other_org.id)},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_x_organization_id_header_changes_context(self):
        token = Token.objects.create(user=self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {token.key}',
            HTTP_X_ORGANIZATION_ID=str(self.organization_2.id),
        )

        url = reverse('api-iam-profile')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['active_organization']['id'], str(self.organization_2.id))

    def test_x_organization_id_header_forbidden_for_non_member(self):
        token = Token.objects.create(user=self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {token.key}',
            HTTP_X_ORGANIZATION_ID=str(self.other_org.id),
        )

        url = reverse('api-iam-profile')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data['detail'],
            'You are not a member of the organization provided in X-Organization-ID.',
        )

    def test_refresh_rotates_token(self):
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        url = reverse('api-iam-refresh')
        response = self.client.post(url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertNotEqual(response.data['token'], token.key)

    def test_logout_revokes_token(self):
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        url = reverse('api-iam-logout')
        response = self.client.post(url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Token.objects.filter(key=token.key).exists())
