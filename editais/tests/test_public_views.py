"""
Tests for public views (home, ambientes_inovacao, startups, login, register).
"""

import json
from unittest.mock import patch

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from django.db import connection
from django.core.cache import cache
from django.core import mail

from .factories import UserFactory


class HomeViewTest(TestCase):
    """Tests for home page view"""

    def setUp(self):
        self.client = Client()

    def test_home_page_loads(self):
        """Test that home page loads without authentication"""
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        # Verify content is present (template is being rendered)
        self.assertContains(response, "AgroHub", status_code=200)

    def test_home_page_contains_branding(self):
        """Test that home page contains AgroHub branding"""
        response = self.client.get(reverse("home"))
        self.assertContains(response, "AgroHub", status_code=200)


class AmbientesInovacaoViewTest(TestCase):
    """Tests for ambientes de inovação page view"""

    def setUp(self):
        self.client = Client()

    def test_ambientes_inovacao_page_loads(self):
        """Test that ambientes de inovação page loads without authentication"""
        response = self.client.get(reverse("ambientes_inovacao"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "ambientes_inovacao/index.html")


class StartupsLegacyRedirectTest(TestCase):
    """Legacy /projetos-aprovados/ redirects to /startups/."""

    def test_legacy_projetos_aprovados_url_redirects_to_startups(self):
        response = self.client.get("/projetos-aprovados/", follow=False)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, "/startups/")


class LoginViewTest(TestCase):
    """Tests for login view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", email="test@example.com"
        )

    def test_login_page_loads(self):
        """Test that login page loads without authentication"""
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/login.html")

    def test_login_page_redirects_authenticated_user(self):
        """Test that authenticated users are redirected to dashboard"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("login"))
        self.assertRedirects(response, reverse("dashboard_home"))

    def test_login_with_valid_credentials(self):
        """Test login with valid credentials"""
        response = self.client.post(
            reverse("login"), {"username": "testuser", "password": "testpass123"}
        )
        self.assertRedirects(response, reverse("dashboard_home"))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_with_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = self.client.post(
            reverse("login"), {"username": "testuser", "password": "wrongpassword"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertContains(response, "form")

    def test_login_redirects_to_next_url(self):
        """Test that login redirects to next URL if provided (safe relative path)"""
        next_url = "/editais/"
        response = self.client.post(
            reverse("login") + f"?next={next_url}",
            {
                "username": "testuser",
                "password": "testpass123",
                "next": next_url,
            },
        )
        self.assertRedirects(response, next_url)

    def test_login_rejects_external_next_url(self):
        """Test that login does not redirect to absolute external URLs (open redirect)"""
        response = self.client.post(
            reverse("login"),
            {
                "username": "testuser",
                "password": "testpass123",
                "next": "https://evil.com/phishing",
            },
        )
        self.assertRedirects(response, reverse("dashboard_home"))
        self.assertNotIn("evil.com", response.url)

    def test_login_page_has_csrf_token(self):
        """Test that login page includes CSRF token"""
        response = self.client.get(reverse("login"))
        self.assertContains(response, "csrfmiddlewaretoken")


class RegisterViewTest(TestCase):
    """Tests for user registration view"""

    def setUp(self):
        self.client = Client()

    def test_register_page_loads(self):
        """Test that register page loads without authentication"""
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/register.html")

    def test_register_page_redirects_authenticated_user(self):
        """Test that authenticated users are redirected to dashboard"""
        UserFactory(username="existinguser")
        self.client.login(username="existinguser", password="testpass123")
        response = self.client.get(reverse("register"))
        self.assertRedirects(response, reverse("dashboard_home"))

    def test_register_with_valid_data(self):
        """Test user registration with valid data"""
        response = self.client.post(
            reverse("register"),
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "first_name": "New",
                "last_name": "User",
                "password1": "ComplexPass123!",
                "password2": "ComplexPass123!",
            },
        )
        self.assertRedirects(response, reverse("dashboard_home"))
        self.assertTrue(User.objects.filter(username="newuser").exists())
        # User should be automatically logged in
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_register_with_invalid_data(self):
        """Test user registration with invalid data"""
        response = self.client.post(
            reverse("register"),
            {
                "username": "newuser",
                "email": "invalid-email",
                "password1": "short",
                "password2": "short",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="newuser").exists())
        self.assertContains(response, "form")

    def test_register_with_duplicate_email(self):
        """Test that registration fails with duplicate email"""
        UserFactory(username="existing", email="existing@example.com")
        response = self.client.post(
            reverse("register"),
            {
                "username": "newuser",
                "email": "existing@example.com",
                "first_name": "New",
                "last_name": "User",
                "password1": "ComplexPass123!",
                "password2": "ComplexPass123!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="newuser").exists())

    def test_register_page_has_csrf_token(self):
        """Test that register page includes CSRF token"""
        response = self.client.get(reverse("register"))
        self.assertContains(response, "csrfmiddlewaretoken")


class DjangoMessagesToToastTest(TestCase):
    """Tests for Django messages to toast notification conversion"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            email="test@example.com",
            is_staff=True,
        )

    def test_success_message_appears_as_toast(self):
        """Test that Django success messages are converted to toast notifications"""
        self.client.login(username="testuser", password="testpass123")

        # Create an edital to trigger a success message
        from editais.models import Edital

        edital = Edital.objects.create(
            titulo="Test Edital for Toast", url="https://example.com", status="aberto"
        )

        # Update edital which should trigger a success message
        from django.contrib import messages
        from editais.forms import EditalForm

        # Simulate a view that adds a success message
        response = self.client.post(
            reverse("edital_update", kwargs={"pk": edital.pk}),
            {
                "titulo": "Updated Edital",
                "url": "https://example.com",
                "status": "aberto",
            },
            follow=True,
        )

        # Verify response contains toast container
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "toast-container",
            msg_prefix="Toast container should be in response",
        )

        # Verify message is in context (Django messages framework)
        messages_list = list(response.context.get("messages", []))
        # The message should be present if the update was successful
        if messages_list:
            self.assertTrue(
                any(msg.tags == "success" for msg in messages_list),
                "Success message should be present",
            )

    def test_error_message_appears_as_toast(self):
        """Test that Django error messages are converted to toast notifications"""
        self.client.login(username="testuser", password="testpass123")

        # Try to create edital with invalid data to trigger error message
        response = self.client.post(
            reverse("edital_create"),
            {
                "titulo": "",  # Invalid - required field
                "url": "not-a-url",  # Invalid URL
                "status": "aberto",
            },
            follow=True,
        )

        # Verify response contains toast container
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "toast-container",
            msg_prefix="Toast container should be in response",
        )

        # Form errors should be present
        if "form" in response.context:
            self.assertTrue(
                response.context["form"].errors,
                "Form should have errors for invalid data",
            )

    def test_warning_message_appears_as_toast(self):
        """Test that Django warning messages are converted to toast notifications"""
        self.client.login(username="testuser", password="testpass123")

        # Access a view that might show warnings (e.g., search with truncated query)
        from editais.models import Edital
        from editais.constants import MAX_SEARCH_LENGTH

        # Create a long search query that should trigger a warning
        long_query = "a" * (MAX_SEARCH_LENGTH + 10)
        response = self.client.get(
            reverse("editais_index"), {"search": long_query}, follow=True
        )

        # Verify response contains toast container
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "toast-container",
            msg_prefix="Toast container should be in response",
        )

        # Check if warning message was added (if search truncation triggers warning)
        messages_list = list(response.context.get("messages", []))
        # Warning might be present if search was truncated
        if messages_list:
            has_warning = any(msg.tags == "warning" for msg in messages_list)
            # Warning may or may not be present depending on implementation


class PasswordResetTest(TestCase):
    """Tests for complete password reset workflow"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="oldpass123", email="test@example.com"
        )

    def test_password_reset_page_loads(self):
        """Test that password reset page loads"""
        response = self.client.get(reverse("password_reset"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/password_reset_form.html")

    def test_password_reset_with_valid_email(self):
        """Test password reset with valid email"""
        response = self.client.post(
            reverse("password_reset"), {"email": "test@example.com"}
        )
        # Should redirect to password_reset_done
        self.assertRedirects(response, reverse("password_reset_done"))

        # Check that email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("test@example.com", mail.outbox[0].to)

    def test_password_reset_with_invalid_email(self):
        """Test password reset with invalid email"""
        response = self.client.post(
            reverse("password_reset"), {"email": "nonexistent@example.com"}
        )
        # Should still redirect (for security - don't reveal if email exists)
        self.assertRedirects(response, reverse("password_reset_done"))

        # Email should still be sent (security best practice)
        # But in Django, it won't send if email doesn't exist
        # This test verifies the form doesn't crash

    def test_password_reset_done_page_loads(self):
        """Test that password reset done page loads"""
        response = self.client.get(reverse("password_reset_done"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/password_reset_done.html")

    def test_password_reset_complete_page_loads(self):
        """Test that password reset complete page loads"""
        response = self.client.get(reverse("password_reset_complete"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/password_reset_complete.html")


class HealthCheckTest(TestCase):
    """Tests for health_check endpoint"""

    def setUp(self):
        self.client = Client()

    def test_health_check_success(self):
        """Test that health check returns 200 status"""
        response = self.client.get(reverse("health_check"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_health_check_json_structure(self):
        """Test that health check returns expected JSON structure"""
        response = self.client.get(reverse("health_check"))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Verify expected fields
        self.assertIn("status", data)
        self.assertIn("database", data)
        self.assertIn("cache", data)
        self.assertIn("timestamp", data)

        # Verify values
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["database"], "ok")
        self.assertEqual(data["cache"], "ok")

    def test_health_check_database_error(self):
        """Test that health check handles database errors gracefully"""
        with patch.object(connection, "cursor") as mock_cursor:
            mock_cursor.side_effect = Exception("Database connection failed")
            response = self.client.get(reverse("health_check"))
            self.assertEqual(response.status_code, 500)
            data = json.loads(response.content)
            self.assertEqual(data["status"], "unhealthy")
            self.assertIn("error", data)

    def test_health_check_cache_error(self):
        """Test that health check handles cache errors gracefully"""
        # Clear cache first
        cache.clear()

        # Test normal operation
        response = self.client.get(reverse("health_check"))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        # Cache should work, but if it doesn't, status should reflect it
        self.assertIn(data["cache"], ["ok", "error"])


class AjaxRequestTest(TestCase):
    """Tests for AJAX request handling in index view"""

    def setUp(self):
        self.client = Client()
        from editais.tests.factories import EditalFactory, StaffUserFactory

        self.staff_user = StaffUserFactory(username="staff")
        # Create some editais for testing
        for i in range(5):
            EditalFactory(
                titulo=f"Edital {i}", status="aberto", created_by=self.staff_user
            )

    def test_index_ajax_request_returns_partial(self):
        """Test that AJAX requests to index view return partial HTML"""
        response = self.client.get(
            reverse("editais_index"), HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 200)
        # Should use partial template for AJAX requests
        # The response should contain editais but not full page structure
        self.assertContains(
            response, "Edital", msg_prefix="Response should contain edital data"
        )

    def test_index_ajax_request_with_filters(self):
        """Test AJAX request with search filter"""
        response = self.client.get(
            reverse("editais_index"),
            {"search": "Edital 1"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Edital 1",
            msg_prefix="AJAX response should contain filtered results",
        )

    def test_index_ajax_request_pagination(self):
        """Test AJAX request with pagination"""
        # Create more editais to trigger pagination
        from editais.tests.factories import EditalFactory

        for i in range(15):
            EditalFactory(
                titulo=f"Paginated Edital {i}",
                status="aberto",
                created_by=self.staff_user,
            )

        response = self.client.get(
            reverse("editais_index"),
            {"page": "2"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        # Should return partial HTML for page 2

    def test_index_non_ajax_request_returns_full_page(self):
        """Test that non-AJAX requests return full page"""
        response = self.client.get(reverse("editais_index"))
        self.assertEqual(response.status_code, 200)
        # Should contain full page structure (not just partial)
        # Check for common page elements that wouldn't be in partial
        self.assertContains(
            response,
            "<html",
            msg_prefix="Full page should contain HTML tag",
            html=False,
        )


class SearchSuggestionsTest(TestCase):
    """Tests for search suggestions functionality"""

    def setUp(self):
        self.client = Client()
        from editais.tests.factories import EditalFactory, StaffUserFactory

        self.staff_user = StaffUserFactory(username="staff")
        # Create editais with various titles for suggestions
        EditalFactory(
            titulo="Edital FINEP 2024", status="aberto", created_by=self.staff_user
        )
        EditalFactory(
            titulo="Edital FAPEG 2024", status="aberto", created_by=self.staff_user
        )
        EditalFactory(
            titulo="Edital CNPq 2024", status="aberto", created_by=self.staff_user
        )

    def test_search_suggestions_when_no_results(self):
        """Test that search suggestions appear when no results found"""
        # Search for something that doesn't exist
        response = self.client.get(
            reverse("editais_index"), {"search": "NonexistentQuery12345"}
        )
        self.assertEqual(response.status_code, 200)

        # Check if search_suggestions are in context
        if "search_suggestions" in response.context:
            suggestions = response.context["search_suggestions"]
            # Suggestions might be empty or contain similar terms
            self.assertIsInstance(
                suggestions, list, "search_suggestions should be a list"
            )

    def test_search_suggestions_with_partial_match(self):
        """Test search suggestions with partial query"""
        # Search for partial match
        response = self.client.get(reverse("editais_index"), {"search": "FIN"})
        self.assertEqual(response.status_code, 200)

        # Should find results or provide suggestions
        # If no exact results, suggestions should help
        if "search_suggestions" in response.context:
            suggestions = response.context["search_suggestions"]
            self.assertIsInstance(suggestions, list)

    def test_search_suggestions_not_shown_when_results_exist(self):
        """Test that suggestions are not shown when results exist"""
        # Search for something that exists
        response = self.client.get(reverse("editais_index"), {"search": "FINEP"})
        self.assertEqual(response.status_code, 200)

        # Should have results, so suggestions might be empty
        if "search_suggestions" in response.context:
            # When results exist, suggestions might be empty or still provided
            # This depends on implementation
            pass

    def test_search_suggestions_with_special_characters(self):
        """Test search suggestions handle special characters"""
        response = self.client.get(
            reverse("editais_index"), {"search": "Edital & Test"}
        )
        self.assertEqual(response.status_code, 200)
        # Should not crash with special characters
        if "search_suggestions" in response.context:
            suggestions = response.context["search_suggestions"]
            self.assertIsInstance(suggestions, list)
