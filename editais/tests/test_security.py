"""
Security tests: CSRF protection, XSS prevention, SQL injection, authentication/authorization.
"""

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from django.utils.html import escape

from ..models import Edital


class CSRFProtectionTest(TestCase):
    """Tests for CSRF protection"""
    
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=True
        )
        self.edital = Edital.objects.create(
            titulo='Test Edital',
            url='https://example.com',
            status='aberto'
        )
    
    def test_csrf_protection_on_login(self):
        """Test that login form requires CSRF token"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        }, follow=False)
        # Should return 403 Forbidden without CSRF token
        self.assertEqual(response.status_code, 403)
    
    def test_csrf_protection_on_register(self):
        """Test that registration form requires CSRF token"""
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        }, follow=False)
        # Should return 403 Forbidden without CSRF token
        self.assertEqual(response.status_code, 403)
    
    def test_csrf_token_in_login_form(self):
        """Test that login form includes CSRF token"""
        response = self.client.get(reverse('login'))
        self.assertContains(response, 'csrfmiddlewaretoken')
    
    def test_csrf_token_in_register_form(self):
        """Test that register form includes CSRF token"""
        response = self.client.get(reverse('register'))
        self.assertContains(response, 'csrfmiddlewaretoken')


class XSSPreventionTest(TestCase):
    """Tests for XSS prevention"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=True
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_xss_in_edital_title(self):
        """Test that XSS attempts in edital title are escaped"""
        xss_payload = '<script>alert("XSS")</script>'
        edital = Edital.objects.create(
            titulo=xss_payload,
            url='https://example.com',
            status='aberto'
        )
        response = self.client.get(reverse('editais_index'))
        # The script tag should be escaped, not executed
        self.assertContains(response, escape(xss_payload))
        self.assertNotContains(response, '<script>')
    
    def test_xss_in_search_query(self):
        """Test that XSS attempts in search query are handled safely"""
        xss_payload = '<script>alert("XSS")</script>'
        response = self.client.get(reverse('editais_index'), {
            'search': xss_payload
        })
        # Should not crash and should escape the payload
        self.assertEqual(response.status_code, 200)
        # The script tag should not appear in the response
        self.assertNotContains(response, '<script>alert("XSS")</script>')


class SQLInjectionTest(TestCase):
    """Tests for SQL injection prevention"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=True
        )
        self.client.login(username='testuser', password='testpass123')
        Edital.objects.create(
            titulo='Normal Edital',
            url='https://example.com',
            status='aberto'
        )
    
    def test_sql_injection_in_search(self):
        """Test that SQL injection attempts in search are prevented"""
        sql_injection = "'; DROP TABLE editais_edital; --"
        response = self.client.get(reverse('editais_index'), {
            'search': sql_injection
        })
        # Should not crash and should handle the query safely
        self.assertEqual(response.status_code, 200)
        # Table should still exist
        self.assertTrue(Edital.objects.exists())
    
    def test_sql_injection_in_filter(self):
        """Test that SQL injection attempts in filters are prevented"""
        sql_injection = "'; DELETE FROM editais_edital; --"
        response = self.client.get(reverse('editais_index'), {
            'status': sql_injection
        })
        # Should not crash
        self.assertEqual(response.status_code, 200)
        # Table should still exist
        self.assertTrue(Edital.objects.exists())


class AuthenticationAuthorizationTest(TestCase):
    """Tests for authentication and authorization"""
    
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staff',
            password='testpass123',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='regular',
            password='testpass123',
            is_staff=False
        )
    
    def test_unauthenticated_access_to_dashboard(self):
        """Test that unauthenticated users cannot access dashboard"""
        response = self.client.get(reverse('dashboard_home'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard_home')}")
    
    def test_authenticated_access_to_dashboard(self):
        """Test that authenticated users can access dashboard"""
        self.client.login(username='regular', password='testpass123')
        response = self.client.get(reverse('dashboard_home'))
        self.assertEqual(response.status_code, 200)
    
    def test_staff_only_views_require_staff(self):
        """Test that staff-only views require staff permission"""
        staff_only_views = [
            'dashboard_editais',
            'dashboard_usuarios',
            'dashboard_relatorios',
            'dashboard_novo_edital',
        ]
        
        self.client.login(username='regular', password='testpass123')
        for view_name in staff_only_views:
            response = self.client.get(reverse(view_name))
            self.assertEqual(response.status_code, 403, f"{view_name} should require staff")
    
    def test_staff_can_access_staff_views(self):
        """Test that staff users can access staff-only views"""
        staff_only_views = [
            'dashboard_editais',
            'dashboard_usuarios',
            'dashboard_relatorios',
            'dashboard_novo_edital',
        ]
        
        self.client.login(username='staff', password='testpass123')
        for view_name in staff_only_views:
            response = self.client.get(reverse(view_name))
            self.assertEqual(response.status_code, 200, f"{view_name} should be accessible to staff")
    
    def test_public_views_accessible_without_auth(self):
        """Test that public views are accessible without authentication"""
        public_views = [
            'home',
            'ambientes_inovacao',
            'projetos_aprovados',
            'editais_index',
        ]
        
        for view_name in public_views:
            response = self.client.get(reverse(view_name))
            self.assertEqual(response.status_code, 200, f"{view_name} should be publicly accessible")

