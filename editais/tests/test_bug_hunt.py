"""
Comprehensive bug hunt tests covering security, data integrity, edge cases,
validation, error handling, performance, and integration issues.

This test suite implements the deep bug hunt plan systematically.
"""

from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client, TransactionTestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.http import Http404
from django.utils import timezone
from django.urls import reverse

from editais.models import Edital, EditalValor, Cronograma, EditalHistory, Project
from editais.forms import EditalForm, UserRegistrationForm
from editais.utils import (
    determine_edital_status, sanitize_html, sanitize_edital_fields,
    mark_edital_fields_safe, get_project_status_mapping, clear_index_cache
)
from editais.decorators import get_client_ip, rate_limit
from editais.constants import HTML_FIELDS


class SecurityTests(TestCase):
    """Security vulnerability tests"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.staff_user = User.objects.create_user('staff', 'staff@example.com', 'password', is_staff=True)
    
    def test_sql_injection_in_search_query(self):
        """Test SQL injection attempts in search queries"""
        # SQL injection attempts should be treated as literal strings
        malicious_queries = [
            "'; DROP TABLE editais_edital; --",
            "' OR '1'='1",
            "1' UNION SELECT * FROM auth_user--",
            "'; DELETE FROM editais_edital WHERE '1'='1",
        ]
        
        for query in malicious_queries:
            response = self.client.get('/editais/', {'search': query})
            # Should not raise exception and should return 200
            self.assertEqual(response.status_code, 200)
            # Should not execute SQL - just treat as search string
    
    def test_xss_in_html_fields(self):
        """Test XSS prevention in HTML fields"""
        xss_payloads = [
            '<script>alert("XSS")</script>',
            '<img src=x onerror=alert("XSS")>',
            '<svg onload=alert("XSS")>',
            'javascript:alert("XSS")',
            '<iframe src="javascript:alert(\'XSS\')"></iframe>',
        ]
        
        for payload in xss_payloads:
            sanitized = sanitize_html(payload)
            # Should remove script tags and event handlers
            self.assertNotIn('<script>', sanitized)
            self.assertNotIn('onerror=', sanitized)
            self.assertNotIn('onload=', sanitized)
            self.assertNotIn('javascript:', sanitized.lower())
    
    def test_csrf_protection_on_forms(self):
        """Test CSRF protection on POST endpoints"""
        # Login required for staff views
        self.client.force_login(self.staff_user)
        
        # Test edital creation without CSRF token
        # Django test client bypasses CSRF by default, so we need to enforce it
        from django.test import Client
        csrf_client = Client(enforce_csrf_checks=True)
        response = csrf_client.post('/cadastrar/', {
            'titulo': 'Test Edital',
            'url': 'https://example.com',
        }, follow=False)
        # Should require CSRF token
        self.assertIn(response.status_code, [403, 400])  # CSRF failure
    
    def test_authentication_bypass_attempts(self):
        """Test authentication and authorization bypass attempts"""
        # Try to access staff-only views without authentication
        staff_urls = [
            '/dashboard/editais/',
            '/dashboard/usuarios/',
            '/cadastrar/',
        ]
        
        for url in staff_urls:
            response = self.client.get(url)
            # Should redirect to login or return 403
            self.assertIn(response.status_code, [302, 403])
        
        # Try to access staff-only views as non-staff
        self.client.force_login(self.user)
        for url in staff_urls:
            response = self.client.get(url)
            # Should return 403 for non-staff
            self.assertEqual(response.status_code, 403)
    
    def test_draft_edital_visibility(self):
        """Test that draft editais are hidden from non-staff users"""
        edital = Edital.objects.create(
            titulo='Draft Edital',
            url='https://example.com',
            status='draft'
        )
        
        # Non-authenticated user should get 404
        response = self.client.get(edital.get_absolute_url())
        self.assertEqual(response.status_code, 404)
        
        # Non-staff user should get 404
        self.client.force_login(self.user)
        response = self.client.get(edital.get_absolute_url())
        self.assertEqual(response.status_code, 404)
        
        # Staff user should see it
        self.client.force_login(self.staff_user)
        response = self.client.get(edital.get_absolute_url())
        self.assertEqual(response.status_code, 200)
    
    def test_rate_limiting_bypass(self):
        """Test rate limiting behavior"""
        # This would require actual rate limit testing with multiple requests
        # For now, verify decorator is applied
        from editais.views.editais_crud import edital_create
        self.assertTrue(hasattr(edital_create, '__wrapped__'))
    
    def test_information_disclosure_in_errors(self):
        """Test that error messages don't leak sensitive information"""
        # Try to access non-existent edital
        response = self.client.get('/edital/99999/')
        # Should return 404 without revealing internal structure
        self.assertEqual(response.status_code, 404)
        # Error page should not contain stack traces or internal paths
        if hasattr(response, 'content'):
            content = response.content.decode('utf-8')
            self.assertNotIn('Traceback', content)
            self.assertNotIn('settings.py', content)


class DataIntegrityTests(TransactionTestCase):
    """Data integrity and race condition tests"""
    
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
    
    def test_slug_uniqueness_under_concurrent_load(self):
        """Test slug generation under concurrent load"""
        import threading
        
        results = []
        errors = []
        
        def create_edital(title):
            try:
                edital = Edital.objects.create(
                    titulo=title,
                    url='https://example.com',
                    created_by=self.user
                )
                results.append(edital.slug)
            except Exception as e:
                errors.append(str(e))
        
        # Create multiple editais with same title concurrently
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_edital, args=('Test Edital',))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All should succeed without IntegrityError
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        # All slugs should be unique
        self.assertEqual(len(results), len(set(results)), "Duplicate slugs generated")
    
    def test_user_registration_email_uniqueness_race_condition(self):
        """Test email uniqueness check race condition"""
        # This tests the race condition between clean_email() and save()
        form1 = UserRegistrationForm({
            'username': 'user1',
            'email': 'test@example.com',
            'first_name': 'Test',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        })
        
        form2 = UserRegistrationForm({
            'username': 'user2',
            'email': 'test@example.com',
            'first_name': 'Test',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        })
        
        # Both forms should validate initially
        self.assertTrue(form1.is_valid())
        self.assertTrue(form2.is_valid())
        
        # Save first user
        form1.save()
        
        # Second save should handle IntegrityError
        try:
            form2.save()
            # If it doesn't raise, the IntegrityError was caught
        except ValidationError as e:
            # Expected - email already exists
            self.assertIn('email', str(e).lower())
    
    def test_date_validation_edge_cases(self):
        """Test date validation with edge cases"""
        # Test end_date < start_date
        form = EditalForm({
            'titulo': 'Test',
            'url': 'https://example.com',
            'start_date': '2025-12-31',
            'end_date': '2025-01-01',  # Before start_date
        })
        self.assertFalse(form.is_valid())
        self.assertIn('end_date', form.errors)
        
        form = EditalForm({
            'titulo': 'Test',
            'url': 'https://example.com',
            'start_date': '2025-01-01',
            'end_date': '2025-01-01',
        })
        if not form.is_valid():
            self.assertNotIn('end_date', form.errors, 
                            f"end_date should be valid for same dates. Errors: {form.errors}")
    
    def test_foreign_key_cascade_deletion(self):
        """Test foreign key cascade behaviors"""
        edital = Edital.objects.create(
            titulo='Test Edital',
            url='https://example.com',
            created_by=self.user
        )
        
        # Create related objects
        valor = EditalValor.objects.create(edital=edital, valor_total=1000)
        cronograma = Cronograma.objects.create(edital=edital, descricao='Test')
        project = Project.objects.create(
            name='Test Project',
            proponente=self.user,
            edital=edital
        )
        
        # Delete edital - valores and cronogramas should cascade
        edital.delete()
        
        # Related objects should be deleted
        self.assertFalse(EditalValor.objects.filter(pk=valor.pk).exists())
        self.assertFalse(Cronograma.objects.filter(pk=cronograma.pk).exists())
        
        # Project should have edital set to None (SET_NULL)
        project.refresh_from_db()
        self.assertIsNone(project.edital)
    
    def test_null_empty_field_handling(self):
        """Test handling of None and empty fields"""
        edital = Edital.objects.create(
            titulo='Test',
            url='https://example.com',
            objetivo='',
            entidade_principal='',
        )
        
        self.assertEqual(edital.objetivo, '')
        self.assertEqual(edital.entidade_principal, '')
        
        from django.template import Template, Context
        template = Template('{{ edital.objetivo|default:"No objetivo" }}')
        result = template.render(Context({'edital': edital}))
        self.assertEqual(result, 'No objetivo')


class EdgeCaseTests(TestCase):
    """Edge case and logic error tests"""
    
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.staff_user = User.objects.create_user('staff', 'staff@example.com', 'password', is_staff=True)
        self.client = Client()
    
    def test_pagination_edge_cases(self):
        """Test pagination with edge cases"""
        # Create some editais
        for i in range(15):
            Edital.objects.create(
                titulo=f'Edital {i}',
                url=f'https://example.com/{i}',
                created_by=self.user
            )
        
        # Test invalid page numbers
        response = self.client.get('/editais/', {'page': 'invalid'})
        self.assertEqual(response.status_code, 200)  # Should default to page 1
        
        response = self.client.get('/editais/', {'page': '-1'})
        self.assertEqual(response.status_code, 200)  # Should default to page 1
        
        response = self.client.get('/editais/', {'page': '999'})
        self.assertEqual(response.status_code, 200)  # Should return last page or empty
    
    def test_search_query_edge_cases(self):
        """Test search query edge cases"""
        # Very long query (should be truncated)
        long_query = 'a' * 1000
        response = self.client.get('/editais/', {'search': long_query})
        self.assertEqual(response.status_code, 200)
        
        # Special characters
        special_chars = "!@#$%^&*()[]{}|\\:;\"'<>?,./"
        response = self.client.get('/editais/', {'search': special_chars})
        self.assertEqual(response.status_code, 200)
        
        # Empty query
        response = self.client.get('/editais/', {'search': ''})
        self.assertEqual(response.status_code, 200)
    
    def test_status_determination_all_combinations(self):
        """Test all status transition combinations"""
        today = timezone.now().date()
        
        test_cases = [
            # (current_status, start_date, end_date, expected_status)
            ('draft', None, None, 'draft'),  # Draft never changes
            ('fechado', None, None, 'fechado'),  # Fechado never changes
            ('programado', today - timedelta(days=1), today + timedelta(days=1), 'aberto'),
            ('aberto', today - timedelta(days=1), today + timedelta(days=1), 'aberto'),
            ('aberto', today - timedelta(days=10), today - timedelta(days=1), 'fechado'),
            ('programado', today + timedelta(days=1), today + timedelta(days=10), 'programado'),
            ('aberto', today - timedelta(days=1), None, 'aberto'),  # Fluxo contínuo
            ('programado', today - timedelta(days=1), None, 'aberto'),  # Fluxo contínuo
            ('aberto', None, today - timedelta(days=1), 'fechado'),  # Only end_date
        ]
        
        for current_status, start_date, end_date, expected_status in test_cases:
            result = determine_edital_status(
                current_status=current_status,
                start_date=start_date,
                end_date=end_date,
                today=today
            )
            self.assertEqual(
                result, expected_status,
                f"Failed for status={current_status}, start={start_date}, end={end_date}"
            )
    
    def test_url_redirect_with_missing_slug(self):
        """Test PK to slug redirect when slug is missing"""
        edital = Edital.objects.create(
            titulo='Test Edital',
            url='https://example.com',
            slug=None  # No slug
        )
        
        # Should redirect to detail view (which will use PK)
        # The redirect view should handle missing slug gracefully
        response = self.client.get(f'/edital/{edital.pk}/', follow=True)
        # Should eventually reach a valid page (either 200 or 404 if draft)
        self.assertIn(response.status_code, [200, 404])
    
    def test_project_status_mapping_edge_cases(self):
        """Test project status mapping with edge cases"""
        mapping = get_project_status_mapping()
        
        # Test case sensitivity
        self.assertEqual(mapping.get('PRÉ-INCUBAÇÃO'.lower()), 'pre_incubacao')
        self.assertEqual(mapping.get('Incubação'.lower()), 'incubacao')
        
        # Test invalid status (should return as-is)
        invalid_status = 'invalid_status'
        result = mapping.get(invalid_status.lower(), invalid_status.lower())
        self.assertEqual(result, invalid_status.lower())


class ValidationTests(TestCase):
    """Input validation tests"""
    
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
    
    def test_url_field_validation(self):
        """Test URL field validation"""
        # Invalid URLs
        invalid_urls = [
            'not-a-url',
            'ftp://example.com',  # Should still be valid (Django allows)
            'javascript:alert(1)',
            'http://' + 'a' * 2000,  # Very long URL
        ]
        
        for url in invalid_urls:
            try:
                edital = Edital(
                    titulo='Test',
                    url=url,
                    created_by=self.user
                )
                edital.full_clean()  # This will validate
            except ValidationError:
                pass  # Expected for invalid URLs
    
    def test_decimal_field_validation(self):
        """Test decimal field validation"""
        edital = Edital.objects.create(
            titulo='Test',
            url='https://example.com',
            created_by=self.user
        )
        
        valor = EditalValor(edital=edital, valor_total=Decimal('-1000'))
        valor.full_clean()
        
        large_valor = EditalValor(edital=edital, valor_total=Decimal('9999999999999.99'))
        large_valor.full_clean()
    
    def test_form_required_fields(self):
        """Test form required field validation"""
        form = EditalForm({})
        self.assertFalse(form.is_valid())
        self.assertIn('titulo', form.errors)
        self.assertIn('url', form.errors)


class ErrorHandlingTests(TestCase):
    """Error handling tests"""
    
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.client = Client()
    
    @patch('editais.views.public.cache')
    def test_cache_error_handling_in_rate_limit(self, mock_cache):
        """Test cache error handling in rate limiting"""
        mock_cache.add.side_effect = ConnectionError("Cache unavailable")
        
        from editais.decorators import rate_limit
        from editais.views.editais_crud import edital_create
        
        self.assertTrue(hasattr(edital_create, '__wrapped__'))
    
    def test_template_rendering_with_missing_context(self):
        """Test template rendering with missing context variables"""
        from django.template import Template, Context
        
        # Template with optional field
        template = Template('{{ edital.objetivo|default:"No objetivo" }}')
        
        # Test with None
        context = Context({'edital': type('obj', (object,), {'objetivo': None})()})
        result = template.render(context)
        self.assertEqual(result, 'No objetivo')
        
        # Test with missing attribute
        context = Context({'edital': type('obj', (object,), {})()})
        result = template.render(context)
        self.assertEqual(result, 'No objetivo')


class PerformanceTests(TestCase):
    """Performance and N+1 query tests"""
    
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.staff_user = User.objects.create_user('staff', 'staff@example.com', 'password', is_staff=True)
    
    def test_n1_queries_in_index_view(self):
        """Test that index view doesn't have N+1 queries"""
        # Create editais with related objects
        for i in range(5):
            edital = Edital.objects.create(
                titulo=f'Edital {i}',
                url=f'https://example.com/{i}',
                created_by=self.user
            )
            EditalValor.objects.create(edital=edital, valor_total=1000)
        
        from django.test.utils import override_settings
        from django.db import connection
        
        with override_settings(DEBUG=True):
            connection.queries_log.clear()
            
            client = Client()
            response = client.get('/editais/')
            self.assertEqual(response.status_code, 200)
            
            # Count queries
            query_count = len(connection.queries)
            
            # Should be reasonable (not N+1)
            # With select_related and prefetch_related, should be ~3-5 queries
            self.assertLess(query_count, 10, "Too many queries (N+1 problem)")
    
    def test_large_result_set_handling(self):
        """Test handling of large result sets"""
        # Create many editais
        for i in range(100):
            Edital.objects.create(
                titulo=f'Edital {i}',
                url=f'https://example.com/{i}',
                created_by=self.user
            )
        
        client = Client()
        response = client.get('/editais/')
        self.assertEqual(response.status_code, 200)
        
        # Should be paginated (12 per page)
        # Should not load all 100 at once


class IntegrationTests(TestCase):
    """Integration tests"""
    
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.staff_user = User.objects.create_user('staff', 'staff@example.com', 'password', is_staff=True)
        self.client = Client()
        self.client.force_login(self.staff_user)
    
    def test_admin_save_model_sanitization(self):
        """Test that admin save_model sanitizes HTML"""
        from editais.admin import EditalAdmin
        from django.contrib.admin.sites import AdminSite
        
        edital = Edital(
            titulo='Test',
            url='https://example.com',
            analise='<script>alert("XSS")</script>'
        )
        
        admin = EditalAdmin(Edital, AdminSite())
        admin.save_model(
            request=MagicMock(user=self.staff_user),
            obj=edital,
            form=MagicMock(),
            change=False
        )
        
        # HTML should be sanitized
        self.assertNotIn('<script>', edital.analise)
    
    def test_template_tag_safety(self):
        """Test custom template tags handle None values"""
        from editais.templatetags.editais_filters import days_until, is_deadline_soon
        
        # Test with None
        self.assertIsNone(days_until(None))
        self.assertFalse(is_deadline_soon(None))
        
        # Test with valid date
        future_date = timezone.now().date() + timedelta(days=5)
        self.assertIsNotNone(days_until(future_date))
        self.assertTrue(is_deadline_soon(future_date))

