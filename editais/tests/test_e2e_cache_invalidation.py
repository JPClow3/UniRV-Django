"""
End-to-end tests for cache invalidation.
"""

import pytest
from django.core.cache import cache
from django.urls import reverse

from editais.models import Edital, Startup
from editais.utils import clear_index_cache, get_index_cache_key
from editais.tests.factories import (
    StaffUserFactory,
    EditalFactory,
    StartupFactory,
    UserFactory,
)


@pytest.mark.django_db(transaction=True)
class TestEditalCacheInvalidation:
    """E2E tests for cache invalidation on edital CRUD operations"""

    @pytest.fixture(autouse=True)
    def _setup(self, client):
        self.staff_user = StaffUserFactory(username="staff")
        cache.clear()

    def test_cache_invalidation_on_edital_create(self, client):
        client.login(username="staff", password="testpass123")
        initial_version = cache.get("editais_index_cache_version", 0)
        cache.set("editais_index_cache_version", initial_version, timeout=None)
        cache_key = get_index_cache_key("1", initial_version)
        cache.set(cache_key, "cached_content", timeout=300)
        assert cache.get(cache_key) is not None

        client.post(
            reverse("edital_create"),
            data={
                "titulo": "Cache Test Edital",
                "url": "https://example.com/cache",
                "status": "aberto",
                "objetivo": "Test cache invalidation",
            },
            follow=True,
        )

        new_version = cache.get("editais_index_cache_version", 0)
        assert new_version > initial_version

    def test_cache_invalidation_on_edital_update(self, client):
        client.login(username="staff", password="testpass123")
        edital = EditalFactory(
            titulo="Edital to Update", status="aberto", created_by=self.staff_user
        )
        version_before = cache.get("editais_index_cache_version", 0)
        cache.set("editais_index_cache_version", version_before, timeout=None)

        client.post(
            reverse("edital_update", kwargs={"pk": edital.pk}),
            data={
                "titulo": "Updated Edital Title",
                "url": "https://example.com/updated",
                "status": "fechado",
            },
            follow=True,
        )
        assert cache.get("editais_index_cache_version", 0) > version_before

    def test_cache_invalidation_on_edital_delete(self, client):
        client.login(username="staff", password="testpass123")
        edital = EditalFactory(
            titulo="Edital to Delete", status="aberto", created_by=self.staff_user
        )
        version_before = cache.get("editais_index_cache_version", 0)
        cache.set("editais_index_cache_version", version_before, timeout=None)

        client.post(reverse("edital_delete", kwargs={"pk": edital.pk}), follow=True)
        assert not Edital.objects.filter(pk=edital.pk).exists()
        assert cache.get("editais_index_cache_version", 0) > version_before

    def test_cache_invalidation_multiple_operations(self, client):
        client.login(username="staff", password="testpass123")
        initial_version = cache.get("editais_index_cache_version", 0)
        cache.set("editais_index_cache_version", initial_version, timeout=None)

        # Create
        client.post(
            reverse("edital_create"),
            data={
                "titulo": "Multi Op Edital",
                "url": "https://example.com/multi",
                "status": "aberto",
            },
            follow=True,
        )
        v_after_create = cache.get("editais_index_cache_version", 0)
        assert v_after_create > initial_version

        # Update
        edital = Edital.objects.get(titulo="Multi Op Edital")
        client.post(
            reverse("edital_update", kwargs={"pk": edital.pk}),
            data={
                "titulo": "Multi Op Updated",
                "url": "https://example.com/multi",
                "status": "fechado",
            },
            follow=True,
        )
        v_after_update = cache.get("editais_index_cache_version", 0)
        assert v_after_update > v_after_create

        # Delete
        client.post(reverse("edital_delete", kwargs={"pk": edital.pk}), follow=True)
        v_after_delete = cache.get("editais_index_cache_version", 0)
        assert v_after_delete > v_after_update


@pytest.mark.django_db(transaction=True)
class TestProjectCacheInvalidation:
    """E2E tests for cache invalidation on project operations"""

    @pytest.fixture(autouse=True)
    def _setup(self, client):
        self.user = UserFactory(username="testuser")
        self.staff_user = StaffUserFactory(username="staff")
        cache.clear()

    def test_cache_behavior_on_project_create(self, client):
        client.login(username="testuser", password="testpass123")
        edital = EditalFactory(
            titulo="Edital for Project", status="aberto", created_by=self.staff_user
        )
        response = client.post(
            reverse("dashboard_submeter_startup"),
            data={
                "name": "Cache Test Project",
                "description": "Test project",
                "category": "agtech",
                "edital": edital.pk,
                "status": "pre_incubacao",
            },
            follow=True,
        )
        assert response.status_code in [200, 302]
        assert Startup.objects.filter(name="Cache Test Project").exists()


@pytest.mark.django_db(transaction=True)
class TestCacheVersionConsistency:
    """Tests for cache version consistency"""

    @pytest.fixture(autouse=True)
    def _setup(self):
        cache.clear()

    def test_cache_version_initialization(self):
        cache.delete("editais_index_cache_version")
        clear_index_cache()
        version = cache.get("editais_index_cache_version")
        assert version is not None
        assert version >= 1

    def test_cache_version_increments_consistently(self):
        cache.set("editais_index_cache_version", 0, timeout=None)
        for _ in range(5):
            clear_index_cache()
        assert cache.get("editais_index_cache_version", 0) >= 5

    def test_cache_key_generation_with_version(self):
        k1 = get_index_cache_key("1", 1)
        k2 = get_index_cache_key("1", 2)
        assert isinstance(k1, str)
        assert k1 != k2


@pytest.mark.django_db(transaction=True)
class TestCacheInvalidationIntegration:
    """Integration tests for cache invalidation in complete workflows"""

    @pytest.fixture(autouse=True)
    def _setup(self, client):
        self.staff_user = StaffUserFactory(username="staff")
        cache.clear()

    def test_cache_invalidation_in_create_edit_delete_workflow(self, client):
        client.login(username="staff", password="testpass123")
        initial = cache.get("editais_index_cache_version", 0)

        # Create
        client.post(
            reverse("edital_create"),
            data={
                "titulo": "Workflow Edital",
                "url": "https://example.com/workflow",
                "status": "aberto",
            },
            follow=True,
        )
        v1 = cache.get("editais_index_cache_version", 0)
        assert v1 > initial

        # Edit
        edital = Edital.objects.get(titulo="Workflow Edital")
        client.post(
            reverse("edital_update", kwargs={"pk": edital.pk}),
            data={
                "titulo": "Workflow Updated",
                "url": "https://example.com/workflow",
                "status": "fechado",
            },
            follow=True,
        )
        v2 = cache.get("editais_index_cache_version", 0)
        assert v2 > v1

        # Delete
        client.post(reverse("edital_delete", kwargs={"pk": edital.pk}), follow=True)
        v3 = cache.get("editais_index_cache_version", 0)
        assert v3 > v2
        assert v3 - initial == 3
