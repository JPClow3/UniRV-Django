"""
Edge case tests for pagination, search queries, status logic, and URL redirects.
"""

import pytest
from datetime import timedelta
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from editais.models import Edital, Startup
from editais.utils import determine_edital_status


@pytest.mark.django_db
class TestPaginationEdgeCases:
    """Test pagination edge cases"""

    @pytest.fixture(autouse=True)
    def _create_editais(self):
        for i in range(15):
            Edital.objects.create(
                titulo=f"Edital {i}",
                url=f"https://example.com/{i}",
                status="aberto",
            )

    def test_negative_page_number(self, client):
        response = client.get(reverse("editais_index"), {"page": "-1"})
        assert response.status_code == 200

    def test_zero_page_number(self, client):
        response = client.get(reverse("editais_index"), {"page": "0"})
        assert response.status_code == 200

    def test_very_large_page_number(self, client):
        response = client.get(reverse("editais_index"), {"page": "99999"})
        assert response.status_code == 200

    def test_invalid_page_format(self, client):
        response = client.get(reverse("editais_index"), {"page": "abc"})
        assert response.status_code == 200

    def test_empty_results_pagination(self, client):
        Edital.objects.all().delete()
        response = client.get(reverse("editais_index"))
        assert response.status_code == 200


@pytest.mark.django_db
class TestSearchQueryEdgeCases:
    """Test search query edge cases"""

    @pytest.fixture(autouse=True)
    def _create_edital(self):
        Edital.objects.create(
            titulo="Normal Edital", url="https://example.com", status="aberto"
        )

    def test_empty_search_query(self):
        qs = Edital.objects.search("")
        assert list(qs) == list(Edital.objects.all())

    def test_very_long_search_query(self):
        qs = Edital.objects.search("a" * 1000)
        assert qs is not None

    def test_search_with_special_characters(self, client):
        special_chars = "'; DROP TABLE editais_edital; --"
        response = client.get(reverse("editais_index"), {"search": special_chars})
        assert response.status_code == 200

    def test_search_with_unicode(self, client):
        response = client.get(
            reverse("editais_index"), {"search": "Edital de Fomento à Inovação"}
        )
        assert response.status_code == 200

    def test_search_query_length_limit(self):
        qs = Edital.objects.search("x" * 600)
        assert qs is not None


@pytest.mark.django_db
class TestStatusDeterminationEdgeCases:
    """Test status determination logic with edge cases"""

    def test_status_with_none_dates(self):
        today = timezone.now().date()
        status = determine_edital_status(
            current_status="aberto", start_date=None, end_date=None, today=today
        )
        assert status == "aberto"

    def test_status_with_only_start_date(self):
        today = timezone.now().date()
        status = determine_edital_status(
            current_status="programado",
            start_date=today - timedelta(days=5),
            end_date=None,
            today=today,
        )
        assert status == "aberto"

    def test_status_with_only_end_date(self):
        today = timezone.now().date()
        status = determine_edital_status(
            current_status="aberto",
            start_date=None,
            end_date=today + timedelta(days=5),
            today=today,
        )
        assert status == "aberto"

    def test_status_on_exact_start_date(self):
        today = timezone.now().date()
        status = determine_edital_status(
            current_status="programado",
            start_date=today,
            end_date=today + timedelta(days=30),
            today=today,
        )
        assert status == "aberto"

    def test_status_on_exact_end_date(self):
        today = timezone.now().date()
        status = determine_edital_status(
            current_status="aberto",
            start_date=today - timedelta(days=30),
            end_date=today,
            today=today,
        )
        assert status == "aberto"

    def test_status_after_end_date(self):
        today = timezone.now().date()
        status = determine_edital_status(
            current_status="aberto",
            start_date=today - timedelta(days=60),
            end_date=today - timedelta(days=1),
            today=today,
        )
        assert status == "fechado"

    def test_draft_status_never_changes(self):
        today = timezone.now().date()
        status = determine_edital_status(
            current_status="draft",
            start_date=today - timedelta(days=5),
            end_date=today + timedelta(days=5),
            today=today,
        )
        assert status == "draft"

    def test_closed_status_never_changes(self):
        today = timezone.now().date()
        status = determine_edital_status(
            current_status="fechado",
            start_date=today - timedelta(days=5),
            end_date=today + timedelta(days=5),
            today=today,
        )
        assert status == "fechado"

    def test_status_with_invalid_date_types(self):
        with pytest.raises(TypeError):
            determine_edital_status(
                current_status="aberto",
                start_date="not-a-date",
                end_date=None,
                today=timezone.now().date(),
            )


@pytest.mark.django_db
class TestURLRedirectEdgeCases:
    """Test URL redirect edge cases"""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.staff = User.objects.create_user(
            username="testuser", password="testpass123", is_staff=True
        )

    def test_redirect_with_missing_slug(self, client):
        client.login(username="testuser", password="testpass123")
        edital = Edital.objects.create(
            titulo="Test Edital", url="https://example.com", status="aberto"
        )
        Edital.objects.filter(pk=edital.pk).update(slug=None)
        edital.refresh_from_db()
        assert edital.slug is None

        response = client.get(reverse("edital_detail", kwargs={"pk": edital.pk}))
        assert response.status_code in (200, 404)
        if response.status_code == 200:
            assert edital.titulo in response.content.decode()

    def test_redirect_draft_edital_visibility(self, client):
        Edital.objects.create(
            titulo="Draft Edital", url="https://example.com", status="draft"
        )
        edital = Edital.objects.get(titulo="Draft Edital")

        regular = User.objects.create_user(
            username="regular", password="testpass123", is_staff=False
        )
        client.login(username="regular", password="testpass123")
        response = client.get(reverse("edital_detail", kwargs={"pk": edital.pk}))
        assert response.status_code == 404

    def test_startup_redirect_with_missing_slug(self, client):
        client.login(username="testuser", password="testpass123")
        proponente = User.objects.create_user(
            username="proponente", password="testpass123"
        )
        project = Startup.objects.create(
            name="Test Startup", proponente=proponente, status="pre_incubacao"
        )
        Startup.objects.filter(pk=project.pk).update(slug=None)
        project.refresh_from_db()
        assert project.slug is None

        response = client.get(reverse("startup_detail", kwargs={"pk": project.pk}))
        assert response.status_code in (200, 404)
        if response.status_code == 200:
            assert project.name in response.content.decode()
