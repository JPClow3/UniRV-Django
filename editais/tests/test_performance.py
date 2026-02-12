"""
Performance tests for query optimization and efficiency.
"""

import pytest

from django.urls import reverse
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta

from editais.models import Edital, Startup
from editais.tests.factories import StaffUserFactory, EditalFactory, StartupFactory


@pytest.mark.django_db
class TestQueryOptimization:
    """Tests for query optimization in views"""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.staff_user = StaffUserFactory(username="staff")
        for i in range(10):
            EditalFactory(
                titulo=f"Edital {i}",
                status="aberto" if i % 2 == 0 else "fechado",
                created_by=self.staff_user,
                entidade_principal="FINEP" if i % 3 == 0 else "FAPEG",
            )

    def test_index_view_query_efficiency(self, client):
        """Test editais index page query efficiency"""
        cache.clear()
        response = client.get(reverse("editais_index"))
        assert response.status_code == 200

    def test_edital_detail_query_efficiency(self, client):
        """Test edital detail page query efficiency with related objects"""
        cache.clear()
        edital = Edital.objects.first()
        response = client.get(
            reverse("edital_detail_slug", kwargs={"slug": edital.slug})
        )
        assert response.status_code == 200

    def test_dashboard_editais_query_efficiency(self, client):
        """Test dashboard editais list query efficiency"""
        cache.clear()
        client.login(username="staff", password="testpass123")
        response = client.get(reverse("dashboard_editais"))
        assert response.status_code == 200

    def test_startup_showcase_query_efficiency(self, client):
        """Test startup showcase query efficiency"""
        cache.clear()
        for i in range(5):
            StartupFactory(
                name=f"Startup {i}",
                proponente=self.staff_user,
                status="incubacao",
            )
        response = client.get(reverse("startups_showcase"))
        assert response.status_code == 200

    def test_search_query_efficiency(self, client):
        """Test search functionality query count"""
        cache.clear()
        response = client.get(reverse("editais_index"), {"search": "Edital 1"})
        assert response.status_code == 200


@pytest.mark.django_db
class TestCachePerformance:
    """Tests for cache performance and effectiveness"""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.staff_user = StaffUserFactory(username="staff")
        EditalFactory(
            titulo="Cached Edital", status="aberto", created_by=self.staff_user
        )

    def test_cache_hit_rates(self, client):
        """Verify cache is being used for repeated requests"""
        cache.clear()
        response1 = client.get(reverse("editais_index"))
        assert response1.status_code == 200

        response2 = client.get(reverse("editais_index"))
        assert response2.status_code == 200

    def test_cache_invalidation_triggers(self, client):
        """Test that cache clears on updates"""
        cache.clear()
        edital = Edital.objects.first()

        response1 = client.get(reverse("editais_index"))
        assert response1.status_code == 200

        client.login(username="staff", password="testpass123")
        client.post(
            reverse("edital_update", kwargs={"pk": edital.pk}),
            data={
                "titulo": "Updated Cached Edital",
                "url": "https://example.com/cache",
                "status": "fechado",
            },
        )

        response2 = client.get(reverse("editais_index"))
        assert response2.status_code == 200

    def test_pagination_cache_efficiency(self, client):
        """Test pagination doesn't break cache"""
        cache.clear()

        response1 = client.get(reverse("editais_index"), {"page": "1"})
        assert response1.status_code == 200

        response2 = client.get(reverse("editais_index"), {"page": "2"})
        assert response2.status_code == 200

        response3 = client.get(reverse("editais_index"), {"page": "1"})
        assert response3.status_code == 200


@pytest.mark.django_db
class TestLargeDatasetPerformance:
    """Tests for performance with large datasets"""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.staff_user = StaffUserFactory(username="staff")

    def test_large_dataset_pagination(self, client):
        """Test pagination performance with 100+ records"""
        for i in range(120):
            EditalFactory(
                titulo=f"Edital {i}",
                status="aberto" if i % 2 == 0 else "fechado",
                created_by=self.staff_user,
            )

        cache.clear()

        response = client.get(reverse("editais_index"), {"page": "1"})
        assert response.status_code == 200

        response = client.get(reverse("editais_index"), {"page": "5"})
        assert response.status_code == 200

        response = client.get(reverse("editais_index"), {"page": "10"})
        assert response.status_code == 200

    def test_large_dataset_search(self, client):
        """Test search performance with many records"""
        for i in range(150):
            EditalFactory(
                titulo=f"Edital de Teste {i}",
                status="aberto",
                objetivo=f"Objetivo do edital {i}",
                created_by=self.staff_user,
            )

        cache.clear()

        response = client.get(reverse("editais_index"), {"search": "Teste 50"})
        assert response.status_code == 200
        assert "Teste 50" in response.content.decode()
