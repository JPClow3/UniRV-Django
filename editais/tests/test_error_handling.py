"""
Error handling tests: database errors, cache errors, template errors.
"""

from unittest.mock import patch, MagicMock
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import DatabaseError, transaction
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from ..models import Edital
from ..decorators import rate_limit, get_client_ip
from ..utils import clear_index_cache


class DatabaseErrorHandlingTest(TestCase):
    """Test database error handling"""
    
    def setUp(self):
        self.client = Client()
        Edital.objects.create(
            titulo='Test Edital',
            url='https://example.com',
            status='aberto'
        )
    
    @patch('editais.views.public.Edital.objects')
    def test_database_error_in_index_view(self, mock_objects):
        """Test that database errors in index view are handled gracefully"""
        mock_objects.with_related.side_effect = DatabaseError("Database connection failed")
        
        response = self.client.get(reverse('editais_index'))
        # Should return 200 with empty results, not 500
        self.assertEqual(response.status_code, 200)
    
    @patch('editais.views.public.get_object_or_404')
    def test_database_error_in_detail_view(self, mock_get):
        """Test that database errors in detail view are handled"""
        mock_get.side_effect = DatabaseError("Database connection failed")
        
        response = self.client.get(reverse('edital_detail_slug', kwargs={'slug': 'test'}))
        # Should return 404, not 500
        self.assertEqual(response.status_code, 404)


class CacheErrorHandlingTest(TestCase):
    """Test cache error handling"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=True
        )
        self.client.login(username='testuser', password='testpass123')
    
    @patch('editais.decorators.cache')
    def test_rate_limit_with_cache_failure(self, mock_cache):
        """Test that rate limiting fails open when cache is unavailable"""
        mock_cache.add.side_effect = ConnectionError("Cache unavailable")
        
        # Create a simple view with rate limiting
        from django.http import HttpResponse
        from functools import wraps
        
        @rate_limit(key='ip', rate=5, window=60, method='POST')
        def test_view(request):
            return HttpResponse("OK")
        
        # Should not raise exception, should allow request
        response = test_view(MagicMock(method='POST', user=MagicMock(is_authenticated=False)))
        self.assertEqual(response.status_code, 200)
    
    @patch('editais.utils.cache')
    def test_clear_index_cache_with_cache_failure(self, mock_cache):
        """Test that cache clearing handles errors gracefully"""
        mock_cache.incr.side_effect = AttributeError("Method not available")
        mock_cache.get.return_value = 1
        mock_cache.set.side_effect = ConnectionError("Cache unavailable")
        
        # Should not raise exception
        try:
            clear_index_cache()
        except Exception as e:
            self.fail(f"clear_index_cache should handle cache errors gracefully, got: {e}")


class TemplateErrorHandlingTest(TestCase):
    """Test template rendering with missing context"""
    
    def setUp(self):
        self.client = Client()
    
    def test_template_with_missing_optional_context(self):
        """Test that templates handle missing optional context gracefully"""
        # This is more of a manual test, but we can test that views provide required context
        response = self.client.get(reverse('home'))
        # Should render without error even if some optional context is missing
        self.assertEqual(response.status_code, 200)
    
    def test_template_filter_with_none_value(self):
        """Test that template filters handle None values"""
        from editais.templatetags.editais_filters import days_until, is_deadline_soon
        
        # days_until should return None for None (allows template to handle missing dates)
        result = days_until(None)
        self.assertIsNone(result)
        
        # is_deadline_soon should return False for None
        result = is_deadline_soon(None)
        self.assertFalse(result)


class ManagementCommandErrorHandlingTest(TestCase):
    """Test management command error handling"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=True
        )
    
    def test_update_edital_status_with_invalid_data(self):
        """Test that management command handles invalid data gracefully"""
        from django.core.management import call_command
        from io import StringIO
        
        # Create edital with invalid date combination (should be caught by model validation)
        edital = Edital.objects.create(
            titulo='Test Edital',
            url='https://example.com',
            status='aberto',
            start_date=None,
            end_date=None
        )
        
        # Command should run without crashing
        out = StringIO()
        try:
            call_command('update_edital_status', stdout=out, verbosity=0)
        except Exception as e:
            self.fail(f"Command should handle edge cases gracefully, got: {e}")
        
        # Should complete successfully
        self.assertIn('atualizado', out.getvalue().lower() or 'nenhum')


class IPAddressHandlingTest(TestCase):
    """Test IP address extraction and validation"""
    
    def test_get_client_ip_with_valid_remote_addr(self):
        """Test IP extraction with valid REMOTE_ADDR"""
        request = MagicMock()
        request.META = {'REMOTE_ADDR': '192.168.1.1'}
        
        ip = get_client_ip(request)
        self.assertEqual(ip, '192.168.1.1')
    
    def test_get_client_ip_with_invalid_ip(self):
        """Test IP extraction with invalid IP"""
        request = MagicMock()
        request.META = {'REMOTE_ADDR': 'invalid-ip'}
        
        ip = get_client_ip(request)
        self.assertEqual(ip, 'unknown')
    
    def test_get_client_ip_with_x_forwarded_for(self):
        """Test IP extraction with X-Forwarded-For header"""
        from django.test import override_settings
        
        with override_settings(USE_X_FORWARDED_HOST=True):
            request = MagicMock()
            request.META = {
                'REMOTE_ADDR': '10.0.0.1',
                'HTTP_X_FORWARDED_FOR': '192.168.1.1, 10.0.0.1'
            }
            
            ip = get_client_ip(request)
            # Should use first IP from X-Forwarded-For
            self.assertEqual(ip, '192.168.1.1')

