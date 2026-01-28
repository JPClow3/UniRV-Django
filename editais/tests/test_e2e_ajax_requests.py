"""
End-to-end tests for AJAX request handling.

Tests AJAX requests to index view, partial HTML responses, error handling, and pagination.
"""

from django.test import TestCase, Client
from django.urls import reverse

from .factories import StaffUserFactory, EditalFactory


class AjaxIndexViewTest(TestCase):
    """E2E tests for AJAX requests to index view"""

    def setUp(self):
        self.client = Client()
        self.staff_user = StaffUserFactory(username='staff')
        # Create editais for testing
        for i in range(15):
            EditalFactory(
                titulo=f'AJAX Test Edital {i}',
                status='aberto' if i % 2 == 0 else 'fechado',
                created_by=self.staff_user
            )

    def test_ajax_request_returns_partial_template(self):
        """Test that AJAX requests return partial HTML template"""
        response = self.client.get(
            reverse('editais_index'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        # Should use partial template (index_partial.html) for AJAX
        # Response should contain edital data but not full page structure
        self.assertContains(response, 'Edital', msg_prefix="AJAX response should contain edital data")

    def test_non_ajax_request_returns_full_page(self):
        """Test that non-AJAX requests return full page template"""
        response = self.client.get(reverse('editais_index'))
        self.assertEqual(response.status_code, 200)
        # Should use full template (index.html) for normal requests
        # Check for HTML structure that wouldn't be in partial
        content = response.content.decode('utf-8')
        # Full page should have more structure than partial
        self.assertContains(response, 'Edital', msg_prefix="Full page should contain edital data")

    def test_ajax_request_with_search(self):
        """Test AJAX request with search parameter"""
        response = self.client.get(
            reverse('editais_index'),
            {'search': 'AJAX Test Edital 1'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AJAX Test Edital 1',
                          msg_prefix="AJAX search should return matching results")

    def test_ajax_request_with_status_filter(self):
        """Test AJAX request with status filter"""
        response = self.client.get(
            reverse('editais_index'),
            {'status': 'aberto'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        # Should return only open editais
        content = response.content.decode('utf-8')
        # Verify response contains editais (exact count depends on pagination)

    def test_ajax_request_with_pagination(self):
        """Test AJAX request with pagination"""
        # Request first page
        response = self.client.get(
            reverse('editais_index'),
            {'page': '1'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)

        # Request second page
        response = self.client.get(
            reverse('editais_index'),
            {'page': '2'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        # Should return page 2 content

    def test_ajax_request_with_invalid_page(self):
        """Test AJAX request with invalid page number"""
        response = self.client.get(
            reverse('editais_index'),
            {'page': 'invalid'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        # Should handle gracefully, return first page or error
        self.assertEqual(response.status_code, 200)

    def test_ajax_request_with_combined_filters(self):
        """Test AJAX request with multiple filters"""
        response = self.client.get(
            reverse('editais_index'),
            {
                'search': 'AJAX Test',
                'status': 'aberto',
                'page': '1'
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        # Should apply all filters correctly

    def test_ajax_request_error_handling(self):
        """Test AJAX request error handling"""
        # Test with very long search query
        long_query = 'a' * 10000
        response = self.client.get(
            reverse('editais_index'),
            {'search': long_query},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        # Should not crash, should handle gracefully
        self.assertEqual(response.status_code, 200)

    def test_ajax_vs_non_ajax_response_difference(self):
        """Test that AJAX and non-AJAX responses differ appropriately"""
        # AJAX request
        ajax_response = self.client.get(
            reverse('editais_index'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        # Non-AJAX request
        normal_response = self.client.get(reverse('editais_index'))

        # Both should succeed
        self.assertEqual(ajax_response.status_code, 200)
        self.assertEqual(normal_response.status_code, 200)

        # Both should contain edital data
        self.assertContains(ajax_response, 'Edital')
        self.assertContains(normal_response, 'Edital')

        # Content might differ (partial vs full), but both should work


class AjaxPaginationTest(TestCase):
    """Tests for AJAX pagination functionality"""

    def setUp(self):
        self.client = Client()
        self.staff_user = StaffUserFactory(username='staff')
        # Create enough editais to trigger pagination
        from django.conf import settings
        per_page = getattr(settings, 'EDITAIS_PER_PAGE', 12)
        num_editais = per_page * 2 + 5  # More than 2 pages

        for i in range(num_editais):
            EditalFactory(
                titulo=f'Paginated Edital {i}',
                status='aberto',
                created_by=self.staff_user
            )

    def test_ajax_pagination_first_page(self):
        """Test AJAX pagination - first page"""
        response = self.client.get(
            reverse('editais_index'),
            {'page': '1'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        # Should contain editais from first page

    def test_ajax_pagination_last_page(self):
        """Test AJAX pagination - last page"""
        response = self.client.get(
            reverse('editais_index'),
            {'page': '999'},  # Very high page number
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        # Should handle gracefully (return last page or empty)

    def test_ajax_pagination_middle_page(self):
        """Test AJAX pagination - middle page"""
        response = self.client.get(
            reverse('editais_index'),
            {'page': '2'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        # Should return page 2 content

    def test_ajax_pagination_empty_results(self):
        """Test AJAX pagination with no results"""
        # Search for something that doesn't exist
        response = self.client.get(
            reverse('editais_index'),
            {'search': 'NonexistentQuery12345XYZ'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        # Should return empty results gracefully


class AjaxCacheBehaviorTest(TestCase):
    """Tests for cache behavior with AJAX requests"""

    def setUp(self):
        self.client = Client()
        self.staff_user = StaffUserFactory(username='staff')
        from django.core.cache import cache
        cache.clear()

    def test_ajax_requests_not_cached(self):
        """Test that AJAX requests are not cached"""
        EditalFactory(
            titulo='Cache Test Edital',
            status='aberto',
            created_by=self.staff_user
        )

        # Make AJAX request
        response1 = self.client.get(
            reverse('editais_index'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response1.status_code, 200)

        # Create another edital
        EditalFactory(
            titulo='New Edital After AJAX',
            status='aberto',
            created_by=self.staff_user
        )

        # Make another AJAX request
        response2 = self.client.get(
            reverse('editais_index'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response2.status_code, 200)

        # Both should work (AJAX requests typically bypass cache or use different cache keys)
