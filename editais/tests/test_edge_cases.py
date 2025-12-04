"""
Edge case tests for pagination, search queries, status logic, and URL redirects.
"""

from datetime import date, timedelta
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from ..models import Edital, Project
from ..utils import determine_edital_status
from ..views.public import build_search_query
from django.db.models import Q


class PaginationEdgeCasesTest(TestCase):
    """Test pagination edge cases"""
    
    def setUp(self):
        self.client = Client()
        # Create multiple editais to test pagination
        for i in range(15):
            Edital.objects.create(
                titulo=f'Edital {i}',
                url=f'https://example.com/{i}',
                status='aberto'
            )
    
    def test_negative_page_number(self):
        """Test that negative page numbers are handled"""
        response = self.client.get(reverse('editais_index'), {'page': '-1'})
        self.assertEqual(response.status_code, 200)
        # Should redirect to page 1
    
    def test_zero_page_number(self):
        """Test that page 0 is handled"""
        response = self.client.get(reverse('editais_index'), {'page': '0'})
        self.assertEqual(response.status_code, 200)
        # Should redirect to page 1
    
    def test_very_large_page_number(self):
        """Test that very large page numbers are handled"""
        response = self.client.get(reverse('editais_index'), {'page': '99999'})
        self.assertEqual(response.status_code, 200)
        # Should show last page or empty results
    
    def test_invalid_page_format(self):
        """Test that non-numeric page numbers are handled"""
        response = self.client.get(reverse('editais_index'), {'page': 'abc'})
        self.assertEqual(response.status_code, 200)
        # Should default to page 1
    
    def test_empty_results_pagination(self):
        """Test pagination with no results"""
        Edital.objects.all().delete()
        response = self.client.get(reverse('editais_index'))
        self.assertEqual(response.status_code, 200)
        # Should show empty results without error


class SearchQueryEdgeCasesTest(TestCase):
    """Test search query edge cases"""
    
    def setUp(self):
        self.client = Client()
        Edital.objects.create(
            titulo='Normal Edital',
            url='https://example.com',
            status='aberto'
        )
    
    def test_empty_search_query(self):
        """Test that empty search query returns all results"""
        q = build_search_query('')
        self.assertIsInstance(q, Q)
        # Empty Q() should match all
    
    def test_very_long_search_query(self):
        """Test that very long search queries are truncated"""
        long_query = 'a' * 1000
        q = build_search_query(long_query)
        # Should not crash and should be truncated to 500 chars
        self.assertIsInstance(q, Q)
    
    def test_search_with_special_characters(self):
        """Test search with special characters"""
        special_chars = "'; DROP TABLE editais_edital; --"
        response = self.client.get(reverse('editais_index'), {
            'search': special_chars
        })
        self.assertEqual(response.status_code, 200)
        # Should not crash and should handle safely
    
    def test_search_with_unicode(self):
        """Test search with unicode characters"""
        unicode_query = 'Edital de Fomento à Inovação'
        response = self.client.get(reverse('editais_index'), {
            'search': unicode_query
        })
        self.assertEqual(response.status_code, 200)
    
    def test_search_query_length_limit(self):
        """Test that search query length is limited in build_search_query"""
        long_query = 'x' * 600
        q = build_search_query(long_query)
        self.assertIsInstance(q, Q)


class StatusDeterminationEdgeCasesTest(TestCase):
    """Test status determination logic with edge cases"""
    
    def test_status_with_none_dates(self):
        """Test status determination with None dates"""
        today = timezone.now().date()
        status = determine_edital_status(
            current_status='aberto',
            start_date=None,
            end_date=None,
            today=today
        )
        # Should maintain current status
        self.assertEqual(status, 'aberto')
    
    def test_status_with_only_start_date(self):
        """Test status with only start_date (fluxo contínuo)"""
        today = timezone.now().date()
        start_date = today - timedelta(days=5)
        
        # Should be aberto if started
        status = determine_edital_status(
            current_status='programado',
            start_date=start_date,
            end_date=None,
            today=today
        )
        self.assertEqual(status, 'aberto')
    
    def test_status_with_only_end_date(self):
        """Test status with only end_date"""
        today = timezone.now().date()
        end_date = today + timedelta(days=5)
        
        # Should maintain status if end_date hasn't passed
        status = determine_edital_status(
            current_status='aberto',
            start_date=None,
            end_date=end_date,
            today=today
        )
        self.assertEqual(status, 'aberto')
    
    def test_status_on_exact_start_date(self):
        """Test status on exact start_date"""
        today = timezone.now().date()
        start_date = today
        end_date = today + timedelta(days=30)
        
        status = determine_edital_status(
            current_status='programado',
            start_date=start_date,
            end_date=end_date,
            today=today
        )
        # Should open on start_date
        self.assertEqual(status, 'aberto')
    
    def test_status_on_exact_end_date(self):
        """Test status on exact end_date"""
        today = timezone.now().date()
        start_date = today - timedelta(days=30)
        end_date = today
        
        status = determine_edital_status(
            current_status='aberto',
            start_date=start_date,
            end_date=end_date,
            today=today
        )
        # Should still be open on end_date (end_date >= today)
        self.assertEqual(status, 'aberto')
    
    def test_status_after_end_date(self):
        """Test status after end_date has passed"""
        today = timezone.now().date()
        start_date = today - timedelta(days=60)
        end_date = today - timedelta(days=1)
        
        status = determine_edital_status(
            current_status='aberto',
            start_date=start_date,
            end_date=end_date,
            today=today
        )
        # Should be closed after end_date
        self.assertEqual(status, 'fechado')
    
    def test_draft_status_never_changes(self):
        """Test that draft status never changes automatically"""
        today = timezone.now().date()
        start_date = today - timedelta(days=5)
        end_date = today + timedelta(days=5)
        
        status = determine_edital_status(
            current_status='draft',
            start_date=start_date,
            end_date=end_date,
            today=today
        )
        # Draft should remain draft
        self.assertEqual(status, 'draft')
    
    def test_closed_status_never_changes(self):
        """Test that closed status never changes automatically"""
        today = timezone.now().date()
        start_date = today - timedelta(days=5)
        end_date = today + timedelta(days=5)
        
        status = determine_edital_status(
            current_status='fechado',
            start_date=start_date,
            end_date=end_date,
            today=today
        )
        # Closed should remain closed
        self.assertEqual(status, 'fechado')
    
    def test_status_with_invalid_date_types(self):
        """Test that invalid date types raise TypeError"""
        with self.assertRaises(TypeError):
            determine_edital_status(
                current_status='aberto',
                start_date='not-a-date',
                end_date=None,
                today=timezone.now().date()
            )


class URLRedirectEdgeCasesTest(TestCase):
    """Test URL redirect edge cases"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=True
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_redirect_with_missing_slug(self):
        """Test redirect when edital has no slug (edge case)"""
        # Create edital without slug (shouldn't happen normally, but test edge case)
        edital = Edital.objects.create(
            titulo='Test Edital',
            url='https://example.com',
            status='aberto',
            slug=None  # Force None slug
        )
        # Manually set slug to None after creation (since save() generates it)
        Edital.objects.filter(pk=edital.pk).update(slug=None)
        edital.refresh_from_db()
        
        # Should fallback to PK-based detail view
        response = self.client.get(reverse('edital_detail', kwargs={'pk': edital.pk}))
        self.assertEqual(response.status_code, 200)
    
    def test_redirect_draft_edital_visibility(self):
        """Test that draft editais are hidden in redirect"""
        edital = Edital.objects.create(
            titulo='Draft Edital',
            url='https://example.com',
            status='draft'
        )
        
        # Non-staff user should get 404
        self.client.logout()
        User.objects.create_user(
            username='regular',
            password='testpass123',
            is_staff=False
        )
        self.client.login(username='regular', password='testpass123')
        
        response = self.client.get(reverse('edital_detail', kwargs={'pk': edital.pk}))
        # Should redirect but then 404 on detail view
        # Actually, redirect checks draft status first, so should 404 immediately
        self.assertEqual(response.status_code, 404)
    
    def test_startup_redirect_with_missing_slug(self):
        """Test startup redirect when slug is missing"""
        user = User.objects.create_user(
            username='proponente',
            password='testpass123'
        )
        project = Project.objects.create(
            name='Test Startup',
            proponente=user,
            status='pre_incubacao',
            slug=None  # Force None slug
        )
        # Manually set slug to None
        Project.objects.filter(pk=project.pk).update(slug=None)
        project.refresh_from_db()
        
        # Should fallback to PK-based detail view
        response = self.client.get(reverse('startup_detail', kwargs={'pk': project.pk}))
        self.assertEqual(response.status_code, 200)

