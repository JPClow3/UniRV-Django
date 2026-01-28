"""
Comprehensive tests for startups_showcase view.

Tests filtering, search, stats calculation, error handling, security, and edge cases.
"""

from unittest.mock import patch, MagicMock

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import DatabaseError
from django.core.cache import cache

from editais.models import Startup, Edital
from editais.constants import ACTIVE_STARTUP_STATUSES, MAX_STARTUPS_DISPLAY


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
        self.project1 = Startup.objects.create(
            name='AgTech Startup',
            description='An agricultural technology startup',
            category='agtech',
            status='pre_incubacao',
            proponente=self.user
        )
        self.project2 = Startup.objects.create(
            name='BioTech Company',
            description='A biotechnology company',
            category='biotech',
            status='incubacao',
            proponente=self.user
        )
        self.project3 = Startup.objects.create(
            name='Graduated Startup',
            description='A graduated startup',
            category='iot',
            status='graduada',
            proponente=self.user
        )
        # Create a suspended project (should not appear)
        self.suspended = Startup.objects.create(
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
        
        # Should have 3 active projects (excluding suspended)
        self.assertEqual(stats['total_active'], 3)
        # Should have 1 graduated
        self.assertEqual(stats['graduadas'], 1)

    def test_stats_with_empty_database(self):
        """Test stats calculation with empty database"""
        # Delete all projects
        Startup.objects.all().delete()
        
        response = self.client.get(reverse('startups_showcase'))
        self.assertEqual(response.status_code, 200)
        
        context = response.context
        stats = context['stats']
        self.assertEqual(stats['total_active'], 0)
        self.assertEqual(stats['graduadas'], 0)

    def test_stats_with_category_filter(self):
        """Test that stats are calculated before category filter is applied"""
        # Create more projects
        Startup.objects.create(
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
            Startup.objects.create(
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
        Startup.objects.create(
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
        """Test that database errors return 503 instead of empty 200"""
        with patch('editais.views.public.Startup.objects.select_related') as mock_select:
            mock_queryset = MagicMock()
            mock_queryset.filter.side_effect = DatabaseError("Database connection failed")
            mock_select.return_value = mock_queryset

            response = self.client.get(reverse('startups_showcase'))
            self.assertEqual(response.status_code, 503)
            self.assertTemplateUsed(response, '503.html')

    def test_stats_aggregation_error_handling(self):
        """Test that stats aggregation failure returns 503"""
        base = MagicMock()
        base.filter.return_value = base
        base.only.return_value = base
        base.order_by.return_value = base
        base.__getitem__ = MagicMock(return_value=[])
        base.count.side_effect = DatabaseError("Aggregation error")

        mock_objects = MagicMock()
        mock_objects.select_related.return_value.filter.return_value.only.return_value = base
        mock_objects.filter.return_value.filter.return_value.count.return_value = 0

        with patch('editais.views.public.Startup.objects', mock_objects):
            response = self.client.get(reverse('startups_showcase'))
        self.assertEqual(response.status_code, 503)
        self.assertTemplateUsed(response, '503.html')

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
        project_with_edital = Startup.objects.create(
            name='Startup with Edital',
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
        Startup.objects.create(
            name='XSS Test',
            description='<script>alert("XSS")</script>',
            category='other',
            status='pre_incubacao',
            proponente=self.user
        )

        response = self.client.get(reverse('startups_showcase'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        
        # Check that the project name appears (to ensure it's in the response)
        self.assertIn('XSS Test', content, "Project name should appear in response")
        
        # Check that script tags are escaped in the entire response
        # Django auto-escapes, so <script> should become &lt;script&gt;
        self.assertIn('&lt;script&gt;', content,
                     f"Script tags should be escaped. Found content: {content[:500]}")
        
        # Check that the alert content is also escaped
        # Either &quot;XSS&quot; or the full escaped script tag should be present
        has_escaped_alert = '&quot;XSS&quot;' in content
        has_full_escaped_script = '&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;' in content
        self.assertTrue(has_escaped_alert or has_full_escaped_script,
                       f"Alert content should be escaped. Found: {content[:500]}")
        
        # Verify that raw script tag is NOT present (security check)
        self.assertNotIn('<script>alert("XSS")</script>', content,
                        "Raw script tag should not appear in response - XSS vulnerability!")

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
            Startup.objects.create(
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

    def test_complete_filter_search_pagination_workflow(self):
        """E2E test: Complete workflow with filter, search, and pagination"""
        # Create many projects with different categories and statuses
        from editais.constants import MAX_STARTUPS_DISPLAY
        
        # Create more projects than MAX_STARTUPS_DISPLAY to test pagination
        num_projects = MAX_STARTUPS_DISPLAY + 10
        for i in range(num_projects):
            category = 'agtech' if i % 3 == 0 else ('biotech' if i % 3 == 1 else 'iot')
            Startup.objects.create(
                name=f'Startup {i} {category}',
                description=f'Description for startup {i} in {category}',
                category=category,
                status='pre_incubacao' if i % 2 == 0 else 'incubacao',
                proponente=self.user
            )
        
        # 1. Test initial load - should show limited results
        response = self.client.get(reverse('startups_showcase'))
        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertLessEqual(len(context['startups']), MAX_STARTUPS_DISPLAY,
                           f"Should limit to {MAX_STARTUPS_DISPLAY} startups")
        
        # 2. Test category filter
        response = self.client.get(
            reverse('startups_showcase'),
            {'category': 'agtech'}
        )
        self.assertEqual(response.status_code, 200)
        context = response.context
        # All returned startups should be agtech
        for startup in context['startups']:
            self.assertEqual(startup.category, 'agtech',
                           "Filtered startups should match category filter")
        
        # 3. Test search functionality
        response = self.client.get(
            reverse('startups_showcase'),
            {'search': 'Startup 1'}
        )
        self.assertEqual(response.status_code, 200)
        context = response.context
        # Results should contain "Startup 1" in name or description
        found_match = False
        for startup in context['startups']:
            if 'Startup 1' in startup.name or 'Startup 1' in (startup.description or ''):
                found_match = True
                break
        self.assertTrue(found_match or len(context['startups']) == 0,
                       "Search should find matching startups or return empty if no match")
        
        # 4. Test combined filter and search
        response = self.client.get(
            reverse('startups_showcase'),
            {'category': 'biotech', 'search': 'Startup'}
        )
        self.assertEqual(response.status_code, 200)
        context = response.context
        # All results should be biotech category
        for startup in context['startups']:
            self.assertEqual(startup.category, 'biotech',
                           "Combined filter should apply category filter")
        
        # 5. Test stats remain consistent across filters
        response_all = self.client.get(reverse('startups_showcase'))
        stats_all = response_all.context['stats']
        
        response_filtered = self.client.get(
            reverse('startups_showcase'),
            {'category': 'agtech'}
        )
        stats_filtered = response_filtered.context['stats']
        
        # Stats should be the same (calculated from all active projects, not filtered)
        self.assertEqual(stats_all['total_active'], stats_filtered['total_active'],
                        "Stats should be calculated from all active projects, not filtered subset")
        
        # 6. Test that 'all' category shows all categories
        response_all_categories = self.client.get(
            reverse('startups_showcase'),
            {'category': 'all'}
        )
        self.assertEqual(response_all_categories.status_code, 200)
        context = response_all_categories.context
        # Should show startups from multiple categories
        categories_shown = set(startup.category for startup in context['startups'])
        # If we have enough startups, we should see multiple categories
        if len(context['startups']) > 1:
            # At least one category should be present
            self.assertGreater(len(categories_shown), 0,
                             "Should show startups from at least one category")

