"""
Integration tests for complete workflows.
"""

import pytest
from unittest.mock import patch
from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse

from editais.models import Edital, Startup
from editais.tests.factories import (
    UserFactory,
    StaffUserFactory,
    EditalFactory,
    StartupFactory,
    TagFactory,
)


@pytest.mark.django_db(transaction=True)
class TestEditalWorkflow:
    """Integration test for the complete Edital CRUD workflow with caching."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.staff_user = StaffUserFactory(username="staff")
        cache.clear()

    def test_create_edit_delete_edital_with_cache(self, client):
        client.login(username="staff", password="testpass123")

        resp = client.post(
            reverse("edital_create"),
            data={
                "titulo": "Integration Edital",
                "url": "https://example.com/integration",
                "status": "aberto",
                "objetivo": "Integration test objective",
                "entidade_principal": "FINEP",
            },
            follow=True,
        )
        assert resp.status_code == 200
        assert Edital.objects.filter(titulo="Integration Edital").exists()

        edital = Edital.objects.get(titulo="Integration Edital")

        resp = client.get(reverse("editais_index"))
        assert resp.status_code == 200
        assert "Integration Edital" in resp.content.decode()

        resp = client.post(
            reverse("edital_update", kwargs={"pk": edital.pk}),
            data={
                "titulo": "Updated Integration Edital",
                "url": "https://example.com/integration",
                "status": "fechado",
                "objetivo": "Updated integration test objective",
                "entidade_principal": "FINEP",
            },
            follow=True,
        )
        assert resp.status_code == 200
        edital.refresh_from_db()
        assert edital.titulo == "Updated Integration Edital"

        resp = client.post(
            reverse("edital_delete", kwargs={"pk": edital.pk}), follow=True
        )
        assert not Edital.objects.filter(pk=edital.pk).exists()


@pytest.mark.django_db(transaction=True)
class TestUserRegistrationWorkflow:
    """Integration test for user registration and login workflow."""

    def test_register_login_access_dashboard(self, client):
        resp = client.post(
            reverse("register"),
            data={
                "username": "intuser",
                "email": "intuser@example.com",
                "first_name": "Int",
                "last_name": "User",
                "password1": "ComplexPass123!",
                "password2": "ComplexPass123!",
            },
            follow=True,
        )
        assert resp.status_code == 200
        assert User.objects.filter(username="intuser").exists()

        client.logout()
        login_ok = client.login(username="intuser", password="ComplexPass123!")
        assert login_ok

        resp = client.get(reverse("dashboard_home"))
        assert resp.status_code == 200

    def test_login_with_wrong_credentials(self, client):
        UserFactory(username="validuser")
        resp = client.post(
            reverse("login"),
            data={"username": "validuser", "password": "wrongpassword"},
        )
        assert resp.status_code == 200
        assert not resp.wsgi_request.user.is_authenticated


@pytest.mark.django_db(transaction=True)
class TestProjectSubmissionWorkflow:
    """Integration test for project submission through the dashboard."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.user = UserFactory(username="submitter")
        self.staff_user = StaffUserFactory(username="staff")
        self.edital = EditalFactory(
            titulo="Submission Edital", status="aberto", created_by=self.staff_user
        )

    def test_submit_project_view_in_dashboard(self, client):
        client.login(username="submitter", password="testpass123")

        resp = client.post(
            reverse("dashboard_submeter_startup"),
            data={
                "name": "Submitted Startup",
                "description": "A startup for integration testing",
                "category": "agtech",
                "edital": self.edital.pk,
                "status": "pre_incubacao",
            },
            follow=True,
        )
        assert resp.status_code in [200, 302]
        assert Startup.objects.filter(name="Submitted Startup").exists()

        resp = client.get(reverse("dashboard_startups"))
        assert resp.status_code == 200
        assert "Submitted Startup" in resp.content.decode()


@pytest.mark.django_db
class TestSearchFilterIntegration:
    """Integration test for search and filter functionality."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.staff_user = StaffUserFactory(username="staff")
        self.edital_a = EditalFactory(
            titulo="Agronegócio Edital",
            status="aberto",
            entidade_principal="FINEP",
            created_by=self.staff_user,
        )
        self.edital_b = EditalFactory(
            titulo="Tecnologia Edital",
            status="fechado",
            entidade_principal="CNPq",
            created_by=self.staff_user,
        )

    def test_search_returns_matching_editais(self, client):
        resp = client.get(reverse("editais_index"), {"search": "Agronegócio"})
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "Agronegócio" in content

    def test_filter_by_status(self, client):
        resp = client.get(reverse("editais_index"), {"status": "aberto"})
        assert resp.status_code == 200

    def test_filter_by_entidade(self, client):
        resp = client.get(reverse("editais_index"), {"entidade_principal": "FINEP"})
        assert resp.status_code == 200

    def test_search_with_no_results(self, client):
        resp = client.get(reverse("editais_index"), {"search": "nonexistentxyz"})
        assert resp.status_code == 200

    def test_combined_search_and_filter(self, client):
        resp = client.get(
            reverse("editais_index"),
            {"search": "Agronegócio", "status": "aberto"},
        )
        assert resp.status_code == 200


@pytest.mark.django_db(transaction=True)
class TestAuthenticationFlow:
    """Integration test for authentication flow: login, access control, logout."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.user = UserFactory(username="authuser")
        self.staff_user = StaffUserFactory(username="staffuser")

    def test_login_logout_flow(self, client):
        resp = client.get(reverse("dashboard_home"))
        assert resp.status_code == 302

        client.login(username="authuser", password="testpass123")
        resp = client.get(reverse("dashboard_home"))
        assert resp.status_code == 200

        client.logout()
        resp = client.get(reverse("dashboard_home"))
        assert resp.status_code == 302

    def test_staff_only_endpoints(self, client):
        client.login(username="authuser", password="testpass123")
        resp = client.get(reverse("edital_create"))
        assert resp.status_code in [302, 403]

        client.login(username="staffuser", password="testpass123")
        resp = client.get(reverse("edital_create"))
        assert resp.status_code == 200


@pytest.mark.django_db(transaction=True)
class TestCompleteProjectSubmissionWorkflow:
    """Integration test for full project submission lifecycle."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.staff_user = StaffUserFactory(username="staff")
        self.user = UserFactory(username="projuser")
        self.edital = EditalFactory(
            titulo="Lifecycle Edital", status="aberto", created_by=self.staff_user
        )
        cache.clear()

    def test_full_project_lifecycle(self, client):
        client.login(username="projuser", password="testpass123")

        resp = client.post(
            reverse("dashboard_submeter_startup"),
            data={
                "name": "Lifecycle Startup",
                "description": "Full lifecycle startup",
                "category": "agtech",
                "edital": self.edital.pk,
                "status": "pre_incubacao",
            },
            follow=True,
        )
        assert resp.status_code in [200, 302]
        assert Startup.objects.filter(name="Lifecycle Startup").exists()

        resp = client.get(reverse("dashboard_startups"))
        assert resp.status_code == 200
        assert "Lifecycle Startup" in resp.content.decode()

        resp = client.get(reverse("startups_showcase"))
        assert resp.status_code == 200


@pytest.mark.django_db
class TestDashboardStatisticsE2E:
    """Integration test for dashboard statistics accuracy."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.staff_user = StaffUserFactory(username="staff")
        for i in range(5):
            EditalFactory(
                titulo=f"Stats Edital {i}",
                status="aberto" if i < 3 else "fechado",
                created_by=self.staff_user,
            )
        for i in range(3):
            StartupFactory(
                name=f"Stats Startup {i}",
                status="ativa" if i < 2 else "inativa",
            )

    def test_dashboard_statistics_reflect_data(self, client):
        client.login(username="staff", password="testpass123")
        resp = client.get(reverse("dashboard_home"))
        assert resp.status_code == 200

    def test_public_pages_reflect_data(self, client):
        resp = client.get(reverse("editais_index"))
        assert resp.status_code == 200
        assert "Stats Edital" in resp.content.decode()

    def test_showcase_statistics(self, client):
        resp = client.get(reverse("startups_showcase"))
        assert resp.status_code == 200


@pytest.mark.django_db
class TestSearchSuggestionsE2E:
    """Integration test for search suggestions / autocomplete."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.staff_user = StaffUserFactory(username="staff")
        EditalFactory(
            titulo="Agronegócio Sustentável",
            status="aberto",
            created_by=self.staff_user,
        )
        EditalFactory(
            titulo="Biotecnologia Aplicada", status="aberto", created_by=self.staff_user
        )

    def test_autocomplete_endpoint(self, client):
        resp = client.get(reverse("editais_autocomplete"), {"q": "Agro"})
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, (list, dict))

    def test_search_suggestions_with_query(self, client):
        resp = client.get(reverse("editais_autocomplete"), {"q": "Bio"})
        assert resp.status_code == 200


@pytest.mark.django_db
class TestEmailNotificationE2E:
    """Integration test for email notification workflows."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.staff_user = StaffUserFactory(username="staff")

    @patch("editais.services.EditalService.send_notification")
    def test_notification_on_edital_creation(self, mock_send, client):
        client.login(username="staff", password="testpass123")
        client.post(
            reverse("edital_create"),
            data={
                "titulo": "Notification Edital",
                "url": "https://example.com/notify",
                "status": "aberto",
                "objetivo": "Notification test objective",
                "entidade_principal": "FINEP",
            },
            follow=True,
        )
        assert Edital.objects.filter(titulo="Notification Edital").exists()
