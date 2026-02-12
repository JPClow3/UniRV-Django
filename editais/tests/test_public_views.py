"""
Tests for public views (home, ambientes_inovacao, startups, login, register).
"""

import json

import pytest

from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from django.core import mail

from editais.models import Edital
from editais.tests.factories import UserFactory, StaffUserFactory, EditalFactory


@pytest.mark.django_db
class TestHomeView:
    """Tests for home page view"""

    def test_home_page_loads(self, client):
        """Test that home page loads without authentication"""
        response = client.get(reverse("home"))
        assert response.status_code == 200
        assert "AgroHub" in response.content.decode()

    def test_home_page_contains_branding(self, client):
        """Test that home page contains AgroHub branding"""
        response = client.get(reverse("home"))
        assert "AgroHub" in response.content.decode()


@pytest.mark.django_db
class TestAmbientesInovacaoView:
    """Tests for ambientes de inovação page view"""

    def test_page_loads(self, client):
        """Test that ambientes de inovação page loads without authentication"""
        response = client.get(reverse("ambientes_inovacao"))
        assert response.status_code == 200


@pytest.mark.django_db
class TestLoginView:
    """Tests for login view"""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", email="test@example.com"
        )

    def test_login_page_loads(self, client):
        """Test that login page loads without authentication"""
        response = client.get(reverse("login"))
        assert response.status_code == 200

    def test_login_page_redirects_authenticated_user(self, client):
        """Test that authenticated users are redirected to dashboard"""
        client.login(username="testuser", password="testpass123")
        response = client.get(reverse("login"))
        assert response.status_code == 302
        assert reverse("dashboard_home") in response.url

    def test_login_with_valid_credentials(self, client):
        """Test login with valid credentials"""
        response = client.post(
            reverse("login"), {"username": "testuser", "password": "testpass123"}
        )
        assert response.status_code == 302
        assert reverse("dashboard_home") in response.url

    def test_login_with_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        response = client.post(
            reverse("login"), {"username": "testuser", "password": "wrongpassword"}
        )
        assert response.status_code == 200
        assert not response.wsgi_request.user.is_authenticated

    def test_login_redirects_to_next_url(self, client):
        """Test that login redirects to next URL if provided"""
        next_url = "/editais/"
        response = client.post(
            reverse("login") + f"?next={next_url}",
            {
                "username": "testuser",
                "password": "testpass123",
                "next": next_url,
            },
        )
        assert response.status_code == 302
        assert next_url in response.url

    def test_login_rejects_external_next_url(self, client):
        """Test that login does not redirect to absolute external URLs"""
        response = client.post(
            reverse("login"),
            {
                "username": "testuser",
                "password": "testpass123",
                "next": "https://evil.com/phishing",
            },
        )
        assert response.status_code == 302
        assert "evil.com" not in response.url
        assert reverse("dashboard_home") in response.url

    def test_login_page_has_csrf_token(self, client):
        """Test that login page includes CSRF token"""
        response = client.get(reverse("login"))
        assert "csrfmiddlewaretoken" in response.content.decode()


@pytest.mark.django_db
class TestRegisterView:
    """Tests for user registration view"""

    def test_register_page_loads(self, client):
        """Test that register page loads without authentication"""
        response = client.get(reverse("register"))
        assert response.status_code == 200

    def test_register_page_redirects_authenticated_user(self, client):
        """Test that authenticated users are redirected to dashboard"""
        UserFactory(username="existinguser")
        client.login(username="existinguser", password="testpass123")
        response = client.get(reverse("register"))
        assert response.status_code == 302
        assert reverse("dashboard_home") in response.url

    def test_register_with_valid_data(self, client):
        """Test user registration with valid data"""
        response = client.post(
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
        assert response.status_code == 302
        assert User.objects.filter(username="newuser").exists()
        assert response.wsgi_request.user.is_authenticated

    def test_register_with_invalid_data(self, client):
        """Test user registration with invalid data"""
        response = client.post(
            reverse("register"),
            {
                "username": "newuser",
                "email": "invalid-email",
                "password1": "short",
                "password2": "short",
            },
        )
        assert response.status_code == 200
        assert not User.objects.filter(username="newuser").exists()

    def test_register_with_duplicate_email(self, client):
        """Test that registration fails with duplicate email"""
        UserFactory(username="existing", email="existing@example.com")
        response = client.post(
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
        assert response.status_code == 200
        assert not User.objects.filter(username="newuser").exists()

    def test_register_page_has_csrf_token(self, client):
        """Test that register page includes CSRF token"""
        response = client.get(reverse("register"))
        assert "csrfmiddlewaretoken" in response.content.decode()


@pytest.mark.django_db
class TestPasswordReset:
    """Tests for complete password reset workflow"""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.user = User.objects.create_user(
            username="testuser", password="oldpass123", email="test@example.com"
        )

    def test_password_reset_page_loads(self, client):
        """Test that password reset page loads"""
        response = client.get(reverse("password_reset"))
        assert response.status_code == 200

    def test_password_reset_with_valid_email(self, client):
        """Test password reset with valid email"""
        response = client.post(reverse("password_reset"), {"email": "test@example.com"})
        assert response.status_code == 302
        assert reverse("password_reset_done") in response.url
        assert len(mail.outbox) == 1
        assert "test@example.com" in mail.outbox[0].to

    def test_password_reset_done_page_loads(self, client):
        """Test that password reset done page loads"""
        response = client.get(reverse("password_reset_done"))
        assert response.status_code == 200

    def test_password_reset_complete_page_loads(self, client):
        """Test that password reset complete page loads"""
        response = client.get(reverse("password_reset_complete"))
        assert response.status_code == 200


@pytest.mark.django_db
class TestHealthCheck:
    """Tests for health_check endpoint"""

    def test_health_check_success(self, client):
        """Test that health check returns 200 status"""
        response = client.get(reverse("health_check"))
        assert response.status_code == 200
        assert response["Content-Type"] == "application/json"

    def test_health_check_json_structure(self, client):
        """Test that health check returns expected JSON structure"""
        response = client.get(reverse("health_check"))
        assert response.status_code == 200
        data = json.loads(response.content)

        assert "status" in data
        assert "database" in data
        assert "cache" in data
        assert "timestamp" in data

        assert data["status"] == "healthy"
        assert data["database"] == "ok"
        assert data["cache"] == "ok"


@pytest.mark.django_db
class TestAjaxRequest:
    """Tests for AJAX request handling in index view"""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.staff_user = StaffUserFactory(username="staff")
        for i in range(5):
            EditalFactory(
                titulo=f"Edital {i}", status="aberto", created_by=self.staff_user
            )

    def test_index_ajax_request_returns_partial(self, client):
        """Test that AJAX requests to index view return partial HTML"""
        response = client.get(
            reverse("editais_index"), HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        assert response.status_code == 200
        assert "Edital" in response.content.decode()

    def test_index_ajax_request_with_filters(self, client):
        """Test AJAX request with search filter"""
        response = client.get(
            reverse("editais_index"),
            {"search": "Edital 1"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        assert response.status_code == 200
        assert "Edital 1" in response.content.decode()

    def test_index_ajax_request_pagination(self, client):
        """Test AJAX request with pagination"""
        for i in range(15):
            EditalFactory(
                titulo=f"Paginated Edital {i}",
                status="aberto",
                created_by=self.staff_user,
            )

        response = client.get(
            reverse("editais_index"),
            {"page": "2"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        assert response.status_code == 200

    def test_index_non_ajax_request_returns_full_page(self, client):
        """Test that non-AJAX requests return full page"""
        response = client.get(reverse("editais_index"))
        assert response.status_code == 200
        assert "<html" in response.content.decode()


@pytest.mark.django_db
class TestSearchSuggestions:
    """Tests for search suggestions functionality"""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.staff_user = StaffUserFactory(username="staff")
        EditalFactory(
            titulo="Edital FINEP 2024", status="aberto", created_by=self.staff_user
        )
        EditalFactory(
            titulo="Edital FAPEG 2024", status="aberto", created_by=self.staff_user
        )
        EditalFactory(
            titulo="Edital CNPq 2024", status="aberto", created_by=self.staff_user
        )

    def test_search_suggestions_when_no_results(self, client):
        """Test that search suggestions appear when no results found"""
        response = client.get(
            reverse("editais_index"), {"search": "NonexistentQuery12345"}
        )
        assert response.status_code == 200

    def test_search_suggestions_with_partial_match(self, client):
        """Test search suggestions with partial query"""
        response = client.get(reverse("editais_index"), {"search": "FIN"})
        assert response.status_code == 200

    def test_search_suggestions_with_special_characters(self, client):
        """Test search suggestions handle special characters"""
        response = client.get(reverse("editais_index"), {"search": "Edital & Test"})
        assert response.status_code == 200
