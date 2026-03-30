"""
Authentication tests for Event Management application.
"""
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, Mock
from .factories import UserFactory
from users.models import User


class UserRegistrationTest(APITestCase):
    """Test cases for user registration."""

    def test_register_user(self):
        """Test user registration with valid data."""
        url = reverse('users:register')
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'testpass123',
            'password_confirm': 'testpass123'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], 'newuser@example.com')

    def test_register_with_mismatched_passwords(self):
        """Test registration fails with mismatched passwords."""
        url = reverse('users:register')
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'testpass123',
            'password_confirm': 'differentpass'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_with_existing_email(self):
        """Test registration fails with existing email."""
        user = UserFactory()
        url = reverse('users:register')
        data = {
            'email': user.email,
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'testpass123',
            'password_confirm': 'testpass123'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_with_weak_password(self):
        """Test registration fails with weak password."""
        url = reverse('users:register')
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'password': '123',
            'password_confirm': '123'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class JWTAuthenticationTest(APITestCase):
    """Test cases for JWT authentication."""

    def setUp(self):
        self.user = UserFactory(password='testpass123')

    def test_obtain_token_pair(self):
        """Test obtaining JWT token pair with valid credentials."""
        url = reverse('users:login')
        data = {
            'email': self.user.email,
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)

    def test_obtain_token_with_wrong_password(self):
        """Test login fails with wrong password."""
        url = reverse('users:login')
        data = {
            'email': self.user.email,
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_obtain_token_with_nonexistent_user(self):
        """Test login fails with nonexistent user."""
        url = reverse('users:login')
        data = {
            'email': 'nonexistent@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token(self):
        """Test refreshing access token."""
        # First, login to get tokens
        login_url = reverse('users:login')
        login_data = {
            'email': self.user.email,
            'password': 'testpass123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        refresh_token = login_response.data['refresh']

        # Now refresh the token
        refresh_url = reverse('users:token-refresh')
        refresh_data = {'refresh': refresh_token}
        response = self.client.post(refresh_url, refresh_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_access_protected_endpoint(self):
        """Test accessing protected endpoint with valid token."""
        # Login to get token
        login_url = reverse('users:login')
        login_data = {
            'email': self.user.email,
            'password': 'testpass123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        access_token = login_response.data['access']

        # Access protected endpoint
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        url = reverse('users:profile')
        response = client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)

    def test_access_protected_endpoint_without_token(self):
        """Test accessing protected endpoint without token."""
        url = reverse('users:profile')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_blacklists_token(self):
        """Test logout blacklists refresh token."""
        # Login
        login_url = reverse('users:login')
        login_data = {
            'email': self.user.email,
            'password': 'testpass123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        refresh_token = login_response.data['refresh']
        access_token = login_response.data['access']

        # Logout
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        logout_url = reverse('users:logout')
        logout_response = client.post(logout_url, {'refresh': refresh_token}, format='json')

        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)

        # Try to refresh with blacklisted token
        refresh_url = reverse('users:token-refresh')
        response = self.client.post(refresh_url, {'refresh': refresh_token}, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class GoogleOAuthTest(APITestCase):
    """Test cases for Google OAuth authentication."""

    @patch('google.oauth2.id_token.verify_oauth2_token')
    def test_google_auth_new_user(self, mock_verify):
        """Test Google OAuth creates new user."""
        mock_verify.return_value = {
            'sub': 'google123',
            'email': 'googleuser@example.com',
            'given_name': 'Google',
            'family_name': 'User',
            'email_verified': True
        }

        url = reverse('users:google-auth')
        data = {'token': 'mock_google_token'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)

        # Check user was created
        user = User.objects.get(email='googleuser@example.com')
        self.assertEqual(user.google_id, 'google123')
        self.assertTrue(user.email_verified)

    @patch('google.oauth2.id_token.verify_oauth2_token')
    def test_google_auth_existing_user(self, mock_verify):
        """Test Google OAuth with existing user."""
        user = UserFactory(
            email='googleuser@example.com',
            google_id='google123'
        )

        mock_verify.return_value = {
            'sub': 'google123',
            'email': 'googleuser@example.com',
            'given_name': 'Google',
            'family_name': 'User',
            'email_verified': True
        }

        url = reverse('users:google-auth')
        data = {'token': 'mock_google_token'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['id'], user.id)

    @patch('google.oauth2.id_token.verify_oauth2_token')
    def test_google_auth_link_existing_account(self, mock_verify):
        """Test Google OAuth links to existing account by email."""
        user = UserFactory(email='googleuser@example.com', google_id='')

        mock_verify.return_value = {
            'sub': 'google123',
            'email': 'googleuser@example.com',
            'given_name': 'Google',
            'family_name': 'User',
            'email_verified': True
        }

        url = reverse('users:google-auth')
        data = {'token': 'mock_google_token'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check google_id was linked
        user.refresh_from_db()
        self.assertEqual(user.google_id, 'google123')

    @patch('google.oauth2.id_token.verify_oauth2_token')
    def test_google_auth_invalid_token(self, mock_verify):
        """Test Google OAuth with invalid token."""
        mock_verify.side_effect = ValueError('Invalid token')

        url = reverse('users:google-auth')
        data = {'token': 'invalid_token'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserProfileTest(APITestCase):
    """Test cases for user profile management."""

    def setUp(self):
        self.user = UserFactory(password='testpass123')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_get_profile(self):
        """Test retrieving user profile."""
        url = reverse('users:profile')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)
        self.assertEqual(response.data['username'], self.user.username)

    def test_update_profile(self):
        """Test updating user profile."""
        url = reverse('users:profile')
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'bio': 'Updated bio'
        }
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Updated')
        self.assertEqual(response.data['bio'], 'Updated bio')

    def test_change_password(self):
        """Test changing password."""
        url = reverse('users:change-password')
        data = {
            'old_password': 'testpass123',
            'new_password': 'newpass456'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Try logging in with new password
        self.client.force_authenticate(user=None)
        login_url = reverse('users:login')
        login_data = {
            'email': self.user.email,
            'password': 'newpass456'
        }
        login_response = self.client.post(login_url, login_data, format='json')

        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

    def test_change_password_wrong_old_password(self):
        """Test changing password with wrong old password."""
        url = reverse('users:change-password')
        data = {
            'old_password': 'wrongpass',
            'new_password': 'newpass456'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
