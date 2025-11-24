"""
Tests for public views (home, ambientes_inovacao, projetos_aprovados, login, register).
"""

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class HomeViewTest(TestCase):
    """Tests for home page view"""
    
    def setUp(self):
        self.client = Client()
    
    def test_home_page_loads(self):
        """Test that home page loads without authentication"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        # Verify content is present (template is being rendered)
        self.assertContains(response, 'AgroHub', status_code=200)
    
    def test_home_page_contains_branding(self):
        """Test that home page contains AgroHub branding"""
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'AgroHub', status_code=200)


class AmbientesInovacaoViewTest(TestCase):
    """Tests for ambientes de inovação page view"""
    
    def setUp(self):
        self.client = Client()
    
    def test_ambientes_inovacao_page_loads(self):
        """Test that ambientes de inovação page loads without authentication"""
        response = self.client.get(reverse('ambientes_inovacao'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ambientes_inovacao.html')


class ProjetosAprovadosViewTest(TestCase):
    """Tests for projetos aprovados page view"""
    
    def setUp(self):
        self.client = Client()
    
    def test_projetos_aprovados_page_loads(self):
        """Test that projetos aprovados page loads without authentication"""
        response = self.client.get(reverse('projetos_aprovados'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'projetos_aprovados.html')


class LoginViewTest(TestCase):
    """Tests for login view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
    
    def test_login_page_loads(self):
        """Test that login page loads without authentication"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')
    
    def test_login_page_redirects_authenticated_user(self):
        """Test that authenticated users are redirected to dashboard"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('login'))
        self.assertRedirects(response, reverse('dashboard_home'))
    
    def test_login_with_valid_credentials(self):
        """Test login with valid credentials"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertRedirects(response, reverse('dashboard_home'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)
    
    def test_login_with_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertContains(response, 'form')
    
    def test_login_redirects_to_next_url(self):
        """Test that login redirects to next URL if provided"""
        next_url = '/editais/'
        response = self.client.post(
            reverse('login') + f'?next={next_url}',
            {
                'username': 'testuser',
                'password': 'testpass123'
            }
        )
        self.assertRedirects(response, next_url)
    
    def test_login_page_has_csrf_token(self):
        """Test that login page includes CSRF token"""
        response = self.client.get(reverse('login'))
        self.assertContains(response, 'csrfmiddlewaretoken')


class RegisterViewTest(TestCase):
    """Tests for user registration view"""
    
    def setUp(self):
        self.client = Client()
    
    def test_register_page_loads(self):
        """Test that register page loads without authentication"""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/register.html')
    
    def test_register_page_redirects_authenticated_user(self):
        """Test that authenticated users are redirected to dashboard"""
        user = User.objects.create_user(
            username='existinguser',
            password='testpass123'
        )
        self.client.login(username='existinguser', password='testpass123')
        response = self.client.get(reverse('register'))
        self.assertRedirects(response, reverse('dashboard_home'))
    
    def test_register_with_valid_data(self):
        """Test user registration with valid data"""
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        })
        self.assertRedirects(response, reverse('dashboard_home'))
        self.assertTrue(User.objects.filter(username='newuser').exists())
        # User should be automatically logged in
        self.assertTrue(response.wsgi_request.user.is_authenticated)
    
    def test_register_with_invalid_data(self):
        """Test user registration with invalid data"""
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'invalid-email',
            'password1': 'short',
            'password2': 'short',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='newuser').exists())
        self.assertContains(response, 'form')
    
    def test_register_with_duplicate_email(self):
        """Test that registration fails with duplicate email"""
        User.objects.create_user(
            username='existing',
            email='existing@example.com',
            password='testpass123'
        )
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'existing@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='newuser').exists())
    
    def test_register_page_has_csrf_token(self):
        """Test that register page includes CSRF token"""
        response = self.client.get(reverse('register'))
        self.assertContains(response, 'csrfmiddlewaretoken')

