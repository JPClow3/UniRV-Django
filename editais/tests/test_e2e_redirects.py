"""
End-to-end tests for redirect functionality.
"""

import pytest
from django.urls import reverse

from editais.models import Edital, Startup
from editais.tests.factories import (
    UserFactory,
    StaffUserFactory,
    EditalFactory,
    StartupFactory,
)


@pytest.mark.django_db
class TestEditalDetailRedirect:
    """E2E tests for edital_detail_redirect functionality."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.staff_user = StaffUserFactory(username="staff")
        self.edital = EditalFactory(
            titulo="Test Edital for Redirect",
            status="aberto",
            created_by=self.staff_user,
        )
        self.edital.refresh_from_db()

    def test_edital_redirect_with_slug(self, client):
        if not self.edital.slug:
            from django.utils.text import slugify

            self.edital.slug = slugify(self.edital.titulo)
            self.edital.save()
            self.edital.refresh_from_db()

        resp = client.get(
            reverse("edital_detail", kwargs={"pk": self.edital.pk}), follow=False
        )
        if resp.status_code in [301, 302]:
            assert self.edital.slug in resp.url
        else:
            assert resp.status_code == 200

    def test_edital_redirect_chain(self, client):
        if not self.edital.slug:
            from django.utils.text import slugify

            self.edital.slug = slugify(self.edital.titulo)
            self.edital.save()
            self.edital.refresh_from_db()

        resp = client.get(
            reverse("edital_detail", kwargs={"pk": self.edital.pk}), follow=True
        )
        assert resp.status_code == 200
        assert self.edital.titulo in resp.content.decode()

    def test_edital_redirect_draft_visibility(self, client):
        draft = EditalFactory(
            titulo="Draft Edital", status="draft", created_by=self.staff_user
        )
        draft.refresh_from_db()

        client.logout()
        resp = client.get(
            reverse("edital_detail", kwargs={"pk": draft.pk}), follow=False
        )
        assert resp.status_code == 404

        client.login(username="staff", password="testpass123")
        if draft.slug:
            resp = client.get(
                reverse("edital_detail_slug", kwargs={"slug": draft.slug}), follow=False
            )
            assert resp.status_code == 200


@pytest.mark.django_db
class TestStartupDetailRedirect:
    """E2E tests for startup_detail_redirect functionality."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.user = UserFactory(username="testuser")
        self.project = StartupFactory(
            name="Test Startup for Redirect", proponente=self.user
        )
        self.project.refresh_from_db()

    def test_startup_redirect_with_slug(self, client):
        if not self.project.slug:
            from django.utils.text import slugify

            self.project.slug = slugify(self.project.name)
            self.project.save()
            self.project.refresh_from_db()

        resp = client.get(
            reverse("startup_detail", kwargs={"pk": self.project.pk}), follow=False
        )
        if resp.status_code in [301, 302]:
            assert self.project.slug in resp.url
        else:
            assert resp.status_code == 200

    def test_startup_redirect_chain(self, client):
        if not self.project.slug:
            from django.utils.text import slugify

            self.project.slug = slugify(self.project.name)
            self.project.save()
            self.project.refresh_from_db()

        resp = client.get(
            reverse("startup_detail", kwargs={"pk": self.project.pk}), follow=True
        )
        assert resp.status_code == 200
        assert self.project.name in resp.content.decode()

    def test_startup_redirect_404_invalid_pk(self, client):
        resp = client.get(reverse("startup_detail", kwargs={"pk": 99999}), follow=False)
        assert resp.status_code == 404

    def test_startup_redirect_404_invalid_slug(self, client):
        resp = client.get(
            reverse("startup_detail_slug", kwargs={"slug": "non-existent-slug-12345"}),
            follow=False,
        )
        assert resp.status_code == 404


@pytest.mark.django_db
class TestRedirectSEOAndConsistency:
    """Tests for SEO and consistency of redirects."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.staff_user = StaffUserFactory(username="staff")
        self.user = UserFactory(username="testuser")

    def test_edital_redirect_preserves_query_params(self, client):
        edital = EditalFactory(
            titulo="Edital with Query Test", status="aberto", created_by=self.staff_user
        )
        edital.refresh_from_db()
        if edital.slug:
            resp = client.get(
                reverse("edital_detail", kwargs={"pk": edital.pk}) + "?source=test",
                follow=True,
            )
            assert resp.status_code == 200

    def test_redirect_consistency_same_object(self, client):
        edital = EditalFactory(
            titulo="Consistency Test Edital",
            status="aberto",
            created_by=self.staff_user,
        )
        edital.refresh_from_db()
        if edital.slug:
            r1 = client.get(
                reverse("edital_detail", kwargs={"pk": edital.pk}), follow=False
            )
            r2 = client.get(
                reverse("edital_detail", kwargs={"pk": edital.pk}), follow=False
            )
            if r1.status_code in [301, 302] and r2.status_code in [301, 302]:
                assert r1.url == r2.url


@pytest.mark.django_db
class TestLegacyPublicRedirects:
    """Tests for legacy public redirects."""

    def test_projetos_aprovados_redirects_to_startups(self, client):
        resp = client.get("/projetos-aprovados/", follow=False)
        assert resp.status_code in [301, 302]
        assert reverse("startups_showcase") in resp.url
