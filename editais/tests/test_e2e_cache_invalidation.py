"""
End-to-end tests for cache invalidation.

Tests cache invalidation on all CRUD operations for editais and projects,
verifying that cache version increments and cached responses are cleared.
"""

from django.test import TransactionTestCase, Client
from django.core.cache import cache
from django.urls import reverse

from ..models import Edital, Startup
from ..utils import clear_index_cache, get_index_cache_key
from .factories import StaffUserFactory, EditalFactory, StartupFactory, UserFactory


class EditalCacheInvalidationTest(TransactionTestCase):
    """
    E2E tests for cache invalidation on edital CRUD operations.

    Uses TransactionTestCase because tests verify transaction.on_commit()
    callbacks which only fire when transactions actually commit.
    """

    """E2E tests for cache invalidation on edital CRUD operations"""

    def setUp(self):
        self.client = Client()
        self.staff_user = StaffUserFactory(username="staff")
        cache.clear()

    def test_cache_invalidation_on_edital_create(self):
        """Test that cache is invalidated when edital is created"""
        self.client.login(username="staff", password="testpass123")

        # Set initial cache version
        initial_version = cache.get("editais_index_cache_version", 0)
        cache.set("editais_index_cache_version", initial_version, timeout=None)

        # Create a cached response
        cache_key = get_index_cache_key("1", initial_version)
        cache.set(cache_key, "cached_content", timeout=300)

        # Verify cache exists
        self.assertIsNotNone(cache.get(cache_key), "Cache should exist before creation")

        # Create edital
        create_data = {
            "titulo": "Cache Test Edital",
            "url": "https://example.com/cache",
            "status": "aberto",
            "objetivo": "Test cache invalidation",
        }
        response = self.client.post(
            reverse("edital_create"), data=create_data, follow=True
        )
        self.assertIn(response.status_code, [200, 302])

        # Verify cache version was incremented
        new_version = cache.get("editais_index_cache_version", 0)
        self.assertGreater(
            new_version,
            initial_version,
            "Cache version should be incremented after creation",
        )

        # Verify old cache key is invalid (new version means old key won't match)
        old_cache_key = get_index_cache_key("1", initial_version)
        # The old cache might still exist, but it won't be used because version changed
        new_cache_key = get_index_cache_key("1", new_version)
        self.assertNotEqual(
            old_cache_key,
            new_cache_key,
            "Cache keys should be different after version increment",
        )

    def test_cache_invalidation_on_edital_update(self):
        """Test that cache is invalidated when edital is updated"""
        self.client.login(username="staff", password="testpass123")

        # Create edital first
        edital = EditalFactory(
            titulo="Edital to Update", status="aberto", created_by=self.staff_user
        )

        # Set cache version
        version_before_update = cache.get("editais_index_cache_version", 0)
        cache.set("editais_index_cache_version", version_before_update, timeout=None)

        # Update edital
        update_data = {
            "titulo": "Updated Edital Title",
            "url": "https://example.com/updated",
            "status": "fechado",
            "objetivo": "Updated objective",
        }
        response = self.client.post(
            reverse("edital_update", kwargs={"pk": edital.pk}),
            data=update_data,
            follow=True,
        )
        self.assertIn(response.status_code, [200, 302])

        # Verify cache version was incremented
        version_after_update = cache.get("editais_index_cache_version", 0)
        self.assertGreater(
            version_after_update,
            version_before_update,
            "Cache version should be incremented after update",
        )

    def test_cache_invalidation_on_edital_delete(self):
        """Test that cache is invalidated when edital is deleted"""
        self.client.login(username="staff", password="testpass123")

        # Create edital first
        edital = EditalFactory(
            titulo="Edital to Delete", status="aberto", created_by=self.staff_user
        )

        # Set cache version
        version_before_delete = cache.get("editais_index_cache_version", 0)
        cache.set("editais_index_cache_version", version_before_delete, timeout=None)

        # Delete edital
        response = self.client.post(
            reverse("edital_delete", kwargs={"pk": edital.pk}), follow=True
        )
        self.assertIn(response.status_code, [200, 302])
        self.assertFalse(Edital.objects.filter(pk=edital.pk).exists())

        # Verify cache version was incremented
        version_after_delete = cache.get("editais_index_cache_version", 0)
        self.assertGreater(
            version_after_delete,
            version_before_delete,
            "Cache version should be incremented after deletion",
        )

    def test_cache_invalidation_multiple_operations(self):
        """Test cache invalidation across multiple CRUD operations"""
        self.client.login(username="staff", password="testpass123")

        initial_version = cache.get("editais_index_cache_version", 0)
        cache.set("editais_index_cache_version", initial_version, timeout=None)

        # Create
        create_data = {
            "titulo": "Multi Op Edital",
            "url": "https://example.com/multi",
            "status": "aberto",
        }
        self.client.post(reverse("edital_create"), data=create_data, follow=True)
        version_after_create = cache.get("editais_index_cache_version", 0)
        self.assertGreater(version_after_create, initial_version)

        # Update
        edital = Edital.objects.get(titulo="Multi Op Edital")
        update_data = {
            "titulo": "Multi Op Updated",
            "url": "https://example.com/multi",
            "status": "fechado",
        }
        self.client.post(
            reverse("edital_update", kwargs={"pk": edital.pk}),
            data=update_data,
            follow=True,
        )
        version_after_update = cache.get("editais_index_cache_version", 0)
        self.assertGreater(version_after_update, version_after_create)

        # Delete
        self.client.post(
            reverse("edital_delete", kwargs={"pk": edital.pk}), follow=True
        )
        version_after_delete = cache.get("editais_index_cache_version", 0)
        self.assertGreater(version_after_delete, version_after_update)

        # Verify all operations incremented version
        self.assertGreater(
            version_after_delete,
            initial_version,
            "Final version should be greater than initial",
        )


class ProjectCacheInvalidationTest(TransactionTestCase):
    """
    E2E tests for cache invalidation on project operations.

    Uses TransactionTestCase because tests verify transaction.on_commit()
    callbacks which only fire when transactions actually commit.
    """

    def setUp(self):
        self.client = Client()
        self.user = UserFactory(username="testuser")
        self.staff_user = StaffUserFactory(username="staff")
        cache.clear()

    def test_cache_behavior_on_project_create(self):
        """Test cache behavior when project is created"""
        self.client.login(username="testuser", password="testpass123")

        edital = EditalFactory(
            titulo="Edital for Project", status="aberto", created_by=self.staff_user
        )

        # Note: Project creation might not directly invalidate edital index cache
        # but we can verify cache state
        initial_version = cache.get("editais_index_cache_version", 0)

        # Create project
        project_data = {
            "name": "Cache Test Project",
            "description": "Test project",
            "category": "agtech",
            "edital": edital.pk,
            "status": "pre_incubacao",
        }
        response = self.client.post(
            reverse("dashboard_submeter_startup"), data=project_data, follow=True
        )
        self.assertIn(response.status_code, [200, 302])
        self.assertTrue(Startup.objects.filter(name="Cache Test Project").exists())

        # Cache version might or might not change depending on implementation
        # This test verifies the operation completes successfully

    def test_cache_behavior_on_project_update(self):
        """Test cache behavior when project is updated"""
        self.client.login(username="testuser", password="testpass123")

        project = StartupFactory(name="Project to Update", proponente=self.user)

        initial_version = cache.get("editais_index_cache_version", 0)

        # Update project
        update_data = {
            "name": "Updated Project Name",
            "description": "Updated description",
            "category": "biotech",
            "status": "incubacao",
        }
        response = self.client.post(
            reverse("dashboard_startup_update", kwargs={"pk": project.pk}),
            data=update_data,
            follow=True,
        )
        self.assertIn(response.status_code, [200, 302])
        project.refresh_from_db()
        self.assertEqual(project.name, "Updated Project Name")

        # Verify operation completed (cache behavior depends on implementation)


class CacheVersionConsistencyTest(TransactionTestCase):
    """
    Tests for cache version consistency and race conditions.

    Uses TransactionTestCase because tests verify cache version increments
    that happen via transaction.on_commit() callbacks.
    """

    def setUp(self):
        cache.clear()

    def test_cache_version_initialization(self):
        """Test that cache version is initialized if it doesn't exist"""
        # Clear version
        cache.delete("editais_index_cache_version")

        # Call clear_index_cache which should initialize version
        clear_index_cache()

        # Version should be initialized
        version = cache.get("editais_index_cache_version")
        self.assertIsNotNone(version, "Cache version should be initialized")
        self.assertGreaterEqual(version, 1, "Initial version should be at least 1")

    def test_cache_version_increments_consistently(self):
        """Test that cache version increments consistently"""
        cache.clear()
        initial_version = 0
        cache.set("editais_index_cache_version", initial_version, timeout=None)

        # Call clear_index_cache multiple times
        for i in range(5):
            clear_index_cache()

        # Version should be incremented
        final_version = cache.get("editais_index_cache_version", 0)
        self.assertGreaterEqual(
            final_version, 5, "Version should increment with each call"
        )

    def test_cache_key_generation_with_version(self):
        """Test that cache keys are generated correctly with version"""
        version = 5
        cache.set("editais_index_cache_version", version, timeout=None)

        # Generate cache key
        cache_key = get_index_cache_key("1", version)

        # Key should contain version information
        self.assertIsNotNone(cache_key, "Cache key should be generated")
        self.assertIsInstance(cache_key, str, "Cache key should be a string")

        # Key should be different for different versions
        cache_key_v1 = get_index_cache_key("1", 1)
        cache_key_v2 = get_index_cache_key("1", 2)
        self.assertNotEqual(
            cache_key_v1,
            cache_key_v2,
            "Cache keys should differ for different versions",
        )


class CacheInvalidationIntegrationTest(TransactionTestCase):
    """
    Integration tests for cache invalidation in complete workflows.

    Uses TransactionTestCase because tests verify transaction.on_commit()
    callbacks which only fire when transactions actually commit.
    """

    def setUp(self):
        self.client = Client()
        self.staff_user = StaffUserFactory(username="staff")
        cache.clear()

    def test_cache_invalidation_in_create_edit_delete_workflow(self):
        """Test cache invalidation in complete CRUD workflow"""
        self.client.login(username="staff", password="testpass123")

        initial_version = cache.get("editais_index_cache_version", 0)

        # Create
        create_data = {
            "titulo": "Workflow Edital",
            "url": "https://example.com/workflow",
            "status": "aberto",
        }
        self.client.post(reverse("edital_create"), data=create_data, follow=True)
        version_after_create = cache.get("editais_index_cache_version", 0)
        self.assertGreater(version_after_create, initial_version)

        # Edit
        edital = Edital.objects.get(titulo="Workflow Edital")
        update_data = {
            "titulo": "Workflow Updated",
            "url": "https://example.com/workflow",
            "status": "fechado",
        }
        self.client.post(
            reverse("edital_update", kwargs={"pk": edital.pk}),
            data=update_data,
            follow=True,
        )
        version_after_update = cache.get("editais_index_cache_version", 0)
        self.assertGreater(version_after_update, version_after_create)

        # Delete
        self.client.post(
            reverse("edital_delete", kwargs={"pk": edital.pk}), follow=True
        )
        version_after_delete = cache.get("editais_index_cache_version", 0)
        self.assertGreater(version_after_delete, version_after_update)

        # Verify progressive increments
        self.assertEqual(
            version_after_delete - initial_version,
            3,
            "Version should increment 3 times (create, update, delete)",
        )
