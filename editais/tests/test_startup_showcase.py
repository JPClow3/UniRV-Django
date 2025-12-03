"""
Comprehensive tests for startups_showcase view.

Tests filtering, search, stats calculation, error handling, security, and edge cases.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import DatabaseError
from django.core.cache import cache
from unittest.mock import patch, MagicMock

from editais.models import Project, Edital
from editais.constants import ACTIVE_PROJECT_STATUSES, MAX_STARTUPS_DISPLAY


class StartupShowcaseViewTest(TestCase):
    """Test startups_showcase view functionality"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Create some test projects
        self.project1 = Project.objects.create(
            name='AgTech Startup',
            description='An agricultural technology startup',
            category='agtech',
            status='pre_incubacao',
            proponente=self.user
        )
        self.project2 = Project.objects.create(
            name='BioTech Company',
            description='A biotechnology company',
            category='biotech',
            status='incubacao',
            proponente=self.user
        )
        self.project3 = Project.objects.create(
            name='Graduated Startup',
            description='A graduated startup',
            category='iot',
            status='graduada',
            proponente=self.user
        )
        # Create a suspended project (should not appear)
        self.suspended = Project.objects.create(
            name='Suspended Startup',
            description='A suspended startup',
            category='other',
            status='suspensa',
            proponente=self.user
        )
    
    def test_startup_showcase_loads(self):
        """Test that startups showcase page loads"""
        response = self.client.get(reverse('startups_showcase'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'startups.html')
    
    def test_startup_showcase_displays_active_projects(self):
        """Test that only active projects are displayed"""
        response = self.client.get(reverse('startups_showcase'))
        self.assertContains(response, self.project1.name)
        self.assertContains(response, self.project2.name)
        self.assertContains(response, self.project3.name)
        # Suspended project should not appear
        self.assertNotContains(response, self.suspended.name)
    
    def test_category_filtering(self):
        """Test filtering by category"""
        # Filter by agtech
        response = self.client.get(reverse('startups_showcase'), {'category': 'agtech'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.project1.name)
        self.assertNotContains(response, self.project2.name)
        self.assertNotContains(response, self.project3.name)
        
        # Filter by biotech
        response = self.client.get(reverse('startups_showcase'), {'category': 'biotech'})
        self.assertContains(response, self.project2.name)
        self.assertNotContains(response, self.project1.name)
    
    def test_category_filter_all(self):
        """Test that category='all' shows all categories"""
        response = self.client.get(reverse('startups_showcase'), {'category': 'all'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.project1.name)
        self.assertContains(response, self.project2.name)
        self.assertContains(response, self.project3.name)
    
    def test_search_functionality(self):
        """Test search functionality"""
        # Search by name
        response = self.client.get(reverse('startups_showcase'), {'search': 'AgTech'})
        self.assertContains(response, self.project1.name)
        self.assertNotContains(response, self.project2.name)
        
        # Search by description
        response = self.client.get(reverse('startups_showcase'), {'search': 'biotechnology'})
        self.assertContains(response, self.project2.name)
    
    def test_search_with_special_characters(self):
        """Test search with special characters"""
        response = self.client.get(reverse('startups_showcase'), {'search': '!@#$%^&*()'})
        self.assertEqual(response.status_code, 200)
        # Should not crash, just return empty results
    
    def test_search_sql_injection_attempt(self):
        """Test SQL injection attempts in search"""
        malicious_queries = [
            "'; DROP TABLE editais_project; --",
            "' OR '1'='1",
            "1' UNION SELECT * FROM auth_user--",
        ]
        
        for query in malicious_queries:
            response = self.client.get(reverse('startups_showcase'), {'search': query})
            # Should not crash, should treat as literal string
            self.assertEqual(response.status_code, 200)
    
    def test_stats_calculation(self):
        """Test that stats are calculated correctly"""
        response = self.client.get(reverse('startups_showcase'))
        self.assertEqual(response.status_code, 200)
        
        # Check that stats are in context
        context = response.context
        self.assertIn('stats', context)
        stats = context['stats']
        self.assertIn('total_active', stats)
        self.assertIn('graduadas', stats)
        self.assertIn('total_valuation', stats)
        
        # Should have 3 active projects (excluding suspended)
        self.assertEqual(stats['total_active'], 3)
        # Should have 1 graduated
        self.assertEqual(stats['graduadas'], 1)
    
    def test_stats_with_empty_database(self):
        """Test stats calculation with empty database"""
        # Delete all projects
        Project.objects.all().delete()
        
        response = self.client.get(reverse('startups_showcase'))
        self.assertEqual(response.status_code, 200)
        
        context = response.context
        stats = context['stats']
        self.assertEqual(stats['total_active'], 0)
        self.assertEqual(stats['graduadas'], 0)
        self.assertEqual(stats['total_valuation'], 0)
    
    def test_stats_with_category_filter(self):
        """Test that stats are calculated before category filter is applied"""
        # Create more projects
        Project.objects.create(
            name='Another AgTech',
            category='agtech',
            status='pre_incubacao',
            proponente=self.user
        )
        
        # Stats should include all active projects, not just filtered ones
        response = self.client.get(reverse('startups_showcase'), {'category': 'agtech'})
        context = response.context
        stats = context['stats']
        # Total should be 4 (all active), not just 2 (agtech)
        self.assertEqual(stats['total_active'], 4)
    
    def test_max_startups_display_limit(self):
        """Test that results are limited to MAX_STARTUPS_DISPLAY"""
        # Create many projects
        for i in range(MAX_STARTUPS_DISPLAY + 10):
            Project.objects.create(
                name=f'Startup {i}',
                category='other',
                status='pre_incubacao',
                proponente=self.user
            )
        
        response = self.client.get(reverse('startups_showcase'))
        context = response.context
        startups = context['startups']
        # Should be limited to MAX_STARTUPS_DISPLAY
        self.assertLessEqual(len(startups), MAX_STARTUPS_DISPLAY)
    
    def test_ordering_by_submitted_on(self):
        """Test that startups are ordered by submitted_on (newest first)"""
        # Create projects with different submission times
        old_project = Project.objects.create(
            name='Old Startup',
            category='other',
            status='pre_incubacao',
            proponente=self.user
        )
        # submitted_on is auto_now_add, so we can't easily control it
        # But we can verify ordering exists
        
        response = self.client.get(reverse('startups_showcase'))
        context = response.context
        startups = list(context['startups'])
        # Should be ordered (newest first)
        if len(startups) > 1:
            for i in range(len(startups) - 1):
                self.assertGreaterEqual(
                    startups[i].submitted_on,
                    startups[i + 1].submitted_on
                )
    
    def test_database_error_handling(self):
        """Test error handling when database fails"""
        # The view catches DatabaseError and returns default context
        # Patch the queryset to raise DatabaseError when filter is called
        with patch('editais.views.public.Project.objects.select_related') as mock_select:
            mock_queryset = MagicMock()
            # Make filter raise DatabaseError
            mock_queryset.filter.side_effect = DatabaseError("Database connection failed")
            mock_select.return_value = mock_queryset
            
            response = self.client.get(reverse('startups_showcase'))
            # Should return 200 with default empty context
            self.assertEqual(response.status_code, 200)
            context = response.context
            # View should return default context on error
            self.assertEqual(len(context['startups']), 0)
            self.assertEqual(context['stats']['total_active'], 0)
    
    def test_stats_aggregation_error_handling(self):
        """Test error handling when stats aggregation fails"""
        # Patch the queryset to raise ValueError when aggregate is called
        with patch('editais.views.public.Project.objects.select_related') as mock_select:
            mock_queryset = MagicMock()
            # Make filter return the queryset, but aggregate raises ValueError
            filtered_queryset = MagicMock()
            filtered_queryset.aggregate.side_effect = ValueError("Aggregation error")
            mock_queryset.filter.return_value = filtered_queryset
            mock_select.return_value = mock_queryset
            
            response = self.client.get(reverse('startups_showcase'))
            # Should return 200 with default stats (view catches ValueError)
            self.assertEqual(response.status_code, 200)
            context = response.context
            # View should catch ValueError and use default stats
            self.assertEqual(context['stats']['total_active'], 0)
    
    def test_projects_without_proponente_excluded(self):
        """Test that projects without proponente are excluded"""
        # Create project without proponente (should not be possible via model, but test edge case)
        # Actually, proponente is required, so this test verifies the filter works
        response = self.client.get(reverse('startups_showcase'))
        # All projects should have proponente
        context = response.context
        for startup in context['startups']:
            self.assertIsNotNone(startup.proponente)
    
    def test_projects_with_edital_relationship(self):
        """Test that projects with edital relationship are handled correctly"""
        edital = Edital.objects.create(
            titulo='Test Edital',
            url='https://example.com',
            status='aberto'
        )
        project_with_edital = Project.objects.create(
            name='Project with Edital',
            category='other',
            status='pre_incubacao',
            proponente=self.user,
            edital=edital
        )
        
        response = self.client.get(reverse('startups_showcase'))
        self.assertContains(response, project_with_edital.name)
        # Should not crash when accessing edital relationship
    
    def test_xss_in_project_description(self):
        """Test XSS prevention in project descriptions"""
        xss_project = Project.objects.create(
            name='XSS Test',
            description='<script>alert("XSS")</script>',
            category='other',
            status='pre_incubacao',
            proponente=self.user
        )
        
        response = self.client.get(reverse('startups_showcase'))
        # Description should be escaped (Django auto-escapes)
        # Check that the escaped version appears, not the raw script
        content = response.content.decode('utf-8')
        # Should contain escaped version somewhere in the content
        # (Django auto-escapes template variables)
        self.assertIn('&lt;script&gt;', content)
        # Should NOT contain unescaped script tag
        # Note: The template uses {{ startup.description|truncatewords:25 }} which auto-escapes
        # Check that we don't have unescaped <script> in the description area
        # Find the project name and check nearby content
        name_index = content.find('XSS Test')
        if name_index != -1:
            # Check a section around the project name (description should be nearby)
            section_start = max(0, name_index - 100)
            section_end = min(len(content), name_index + 1000)
            project_section = content[section_start:section_end]
            # Should have escaped version
            self.assertIn('&lt;script&gt;', project_section)
            # Should have escaped quotes
            self.assertIn('&quot;XSS&quot;', project_section)
    
    def test_very_long_search_query(self):
        """Test handling of very long search queries"""
        long_query = 'a' * 10000
        response = self.client.get(reverse('startups_showcase'), {'search': long_query})
        # Should not crash
        self.assertEqual(response.status_code, 200)
    
    def test_empty_search_query(self):
        """Test handling of empty search query"""
        response = self.client.get(reverse('startups_showcase'), {'search': ''})
        self.assertEqual(response.status_code, 200)
        # Should show all projects
        context = response.context
        self.assertGreater(len(context['startups']), 0)
    
    def test_invalid_category_filter(self):
        """Test handling of invalid category filter"""
        response = self.client.get(reverse('startups_showcase'), {'category': 'invalid_category'})
        self.assertEqual(response.status_code, 200)
        # Should handle gracefully, probably show no results or all results
    
    def test_cache_behavior(self):
        """Test that view handles cache correctly"""
        # Clear cache
        cache.clear()
        
        response1 = self.client.get(reverse('startups_showcase'))
        self.assertEqual(response1.status_code, 200)
        
        # Second request should work (cache or not)
        response2 = self.client.get(reverse('startups_showcase'))
        self.assertEqual(response2.status_code, 200)
    
    def test_context_variables_present(self):
        """Test that all required context variables are present"""
        response = self.client.get(reverse('startups_showcase'))
        context = response.context
        
        required_vars = ['startups', 'category_filter', 'search_query', 'stats']
        for var in required_vars:
            self.assertIn(var, context, f"Missing context variable: {var}")
    
    def test_stats_graduadas_count(self):
        """Test that graduadas count is correct"""
        # Create more graduated startups
        for i in range(3):
            Project.objects.create(
                name=f'Graduated {i}',
                category='other',
                status='graduada',
                proponente=self.user
            )
        
        response = self.client.get(reverse('startups_showcase'))
        context = response.context
        stats = context['stats']
        # Should have 4 graduated (1 original + 3 new)
        self.assertEqual(stats['graduadas'], 4)
    
    def test_total_valuation_calculation(self):
        """Test total valuation calculation (placeholder)"""
        response = self.client.get(reverse('startups_showcase'))
        context = response.context
        stats = context['stats']
        # Valuation is placeholder: graduadas * 1.0
        self.assertEqual(stats['total_valuation'], stats['graduadas'] * 1)

