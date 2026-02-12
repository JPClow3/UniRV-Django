"""
End-to-end tests for complete user journeys.
"""

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse

from editais.models import Edital, Startup
from editais.tests.factories import (
    UserFactory,
    StaffUserFactory,
    EditalFactory,
    StartupFactory,
)


@pytest.mark.django_db(transaction=True)
class TestCompleteUserRegistrationJourney:
    """E2E test: Complete user journey from registration to project submission."""

    @pytest.fixture(autouse=True)
    def _setup(self, client):
        self.staff_user = StaffUserFactory(username="staff")
        self.edital = EditalFactory(
            titulo="Edital para Projetos", status="aberto", created_by=self.staff_user
        )

    def test_complete_user_journey_registration_to_project(self, client):
        assert client.get(reverse("home")).status_code == 200

        resp = client.get(reverse("editais_index"))
        assert resp.status_code == 200
        assert self.edital.titulo in resp.content.decode()

        resp = client.get(
            reverse("edital_detail_slug", kwargs={"slug": self.edital.slug})
        )
        assert resp.status_code == 200

        resp = client.post(
            reverse("register"),
            data={
                "username": "newuser",
                "email": "newuser@example.com",
                "first_name": "New",
                "last_name": "User",
                "password1": "ComplexPass123!",
                "password2": "ComplexPass123!",
            },
            follow=True,
        )
        assert resp.status_code == 200
        assert User.objects.filter(username="newuser").exists()
        assert resp.wsgi_request.user.is_authenticated

        resp = client.post(
            reverse("dashboard_submeter_startup"),
            data={
                "name": "My Startup",
                "description": "Description of my startup",
                "category": "agtech",
                "edital": self.edital.pk,
                "status": "pre_incubacao",
            },
            follow=True,
        )
        assert resp.status_code in [200, 302]
        assert Startup.objects.filter(name="My Startup").exists()


@pytest.mark.django_db
class TestAnonymousUserJourney:
    """E2E test: Anonymous user journey from browse to registration"""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.staff_user = StaffUserFactory(username="staff")
        for i in range(10):
            EditalFactory(
                titulo=f"Edital {i}",
                status="aberto" if i % 2 == 0 else "fechado",
                created_by=self.staff_user,
            )

    def test_anonymous_browse_search_filter_register_journey(self, client):
        assert client.get(reverse("editais_index")).status_code == 200

        resp = client.get(reverse("editais_index"), {"search": "Edital 1"})
        assert resp.status_code == 200
        assert "Edital 1" in resp.content.decode()

        assert (
            client.get(reverse("editais_index"), {"status": "aberto"}).status_code
            == 200
        )

        edital = Edital.objects.filter(status="aberto").first()
        if edital and edital.slug:
            resp = client.get(
                reverse("edital_detail_slug", kwargs={"slug": edital.slug})
            )
            assert resp.status_code == 200

        assert client.get(reverse("startups_showcase")).status_code == 200

        resp = client.post(
            reverse("register"),
            data={
                "username": "browser",
                "email": "browser@example.com",
                "first_name": "Browser",
                "last_name": "User",
                "password1": "ComplexPass123!",
                "password2": "ComplexPass123!",
            },
            follow=True,
        )
        assert resp.status_code == 200
        assert User.objects.filter(username="browser").exists()
        assert client.get(reverse("dashboard_home")).status_code == 200


@pytest.mark.django_db(transaction=True)
class TestStaffUserCRUDJourney:
    """E2E test: Staff user complete CRUD journey with cache verification."""

    @pytest.fixture(autouse=True)
    def _setup(self, client):
        self.staff_user = StaffUserFactory(username="staff")
        cache.clear()

    def test_staff_create_view_edit_delete_with_cache_verification(self, client):
        client.login(username="staff", password="testpass123")
        initial_version = cache.get("editais_index_cache_version", 0)

        client.post(
            reverse("edital_create"),
            data={
                "titulo": "Staff Created Edital",
                "url": "https://example.com/staff",
                "status": "aberto",
                "objetivo": "Objective for staff edital",
                "entidade_principal": "FINEP",
            },
            follow=True,
        )
        assert Edital.objects.filter(titulo="Staff Created Edital").exists()
        v1 = cache.get("editais_index_cache_version", 0)
        assert v1 > initial_version

        edital = Edital.objects.get(titulo="Staff Created Edital")
        resp = client.get(reverse("edital_detail_slug", kwargs={"slug": edital.slug}))
        assert resp.status_code == 200

        client.post(
            reverse("edital_update", kwargs={"pk": edital.pk}),
            data={
                "titulo": "Staff Updated Edital",
                "url": "https://example.com/staff",
                "status": "fechado",
                "objetivo": "Updated objective",
                "entidade_principal": "FINEP",
            },
            follow=True,
        )
        edital.refresh_from_db()
        assert edital.titulo == "Staff Updated Edital"
        v2 = cache.get("editais_index_cache_version", 0)
        assert v2 > v1

        client.post(reverse("edital_delete", kwargs={"pk": edital.pk}), follow=True)
        assert not Edital.objects.filter(pk=edital.pk).exists()
        v3 = cache.get("editais_index_cache_version", 0)
        assert v3 > v2


@pytest.mark.django_db
class TestUserProjectSubmissionJourney:
    """E2E test: User submits project and tracks status through showcase"""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.user = UserFactory(username="testuser")
        self.staff_user = StaffUserFactory(username="staff")
        self.edital = EditalFactory(
            titulo="Open Edital for Projects",
            status="aberto",
            created_by=self.staff_user,
        )

    def test_user_submit_project_track_in_showcase(self, client):
        client.login(username="testuser", password="testpass123")

        resp = client.post(
            reverse("dashboard_submeter_startup"),
            data={
                "name": "Showcase Startup",
                "description": "A startup for showcase testing",
                "category": "agtech",
                "edital": self.edital.pk,
                "status": "pre_incubacao",
            },
            follow=True,
        )
        assert resp.status_code in [200, 302]
        assert Startup.objects.filter(name="Showcase Startup").exists()

        resp = client.get(reverse("dashboard_startups"))
        assert resp.status_code == 200
        assert "Showcase Startup" in resp.content.decode()

        resp = client.get(reverse("startups_showcase"))
        assert resp.status_code == 200
        assert "Showcase Startup" in resp.content.decode()
        assert resp.context["stats"]["total_active"] >= 1
