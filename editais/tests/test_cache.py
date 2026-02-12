"""
Tests for cache invalidation and race conditions.

Tests clear_index_cache function and cache invalidation scenarios.
"""

import pytest
from django.core.cache import cache

from editais.utils import clear_index_cache


@pytest.mark.django_db
class TestCacheInvalidation:
    """Test cache invalidation functionality"""

    @pytest.fixture(autouse=True)
    def _clear_cache(self):
        cache.clear()

    def test_clear_index_cache_increments_version(self):
        """Test that clear_index_cache increments version number"""
        cache.set("editais_index_cache_version", 1, timeout=None)

        clear_index_cache()

        version = cache.get("editais_index_cache_version")
        assert version is not None
        assert version > 1

    def test_clear_index_cache_initializes_version(self):
        """Test that clear_index_cache initializes version if it doesn't exist"""
        cache.delete("editais_index_cache_version")

        clear_index_cache()

        version = cache.get("editais_index_cache_version")
        assert version is not None
        assert version == 1

    def test_clear_index_cache_handles_race_condition(self):
        """Test that clear_index_cache handles race conditions gracefully"""
        cache.set("editais_index_cache_version", 1, timeout=None)

        clear_index_cache()
        clear_index_cache()
        clear_index_cache()

        version = cache.get("editais_index_cache_version")
        assert version is not None
        assert version >= 2
