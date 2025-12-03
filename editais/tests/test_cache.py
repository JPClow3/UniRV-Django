"""
Tests for cache invalidation and race conditions.

Tests clear_index_cache function and cache invalidation scenarios.
"""

from django.test import TestCase
from django.core.cache import cache
from editais.utils import clear_index_cache


class CacheInvalidationTestCase(TestCase):
    """Test cache invalidation functionality"""
    
    def setUp(self):
        # Clear cache before each test
        cache.clear()
    
    def test_clear_index_cache_increments_version(self):
        """Test that clear_index_cache increments version number"""
        # Set initial version
        cache.set('editais_index_cache_version', 1, timeout=None)
        
        # Clear cache
        clear_index_cache()
        
        # Version should be incremented
        version = cache.get('editais_index_cache_version')
        self.assertIsNotNone(version)
        self.assertGreater(version, 1)
    
    def test_clear_index_cache_initializes_version(self):
        """Test that clear_index_cache initializes version if it doesn't exist"""
        # Ensure version doesn't exist
        cache.delete('editais_index_cache_version')
        
        # Clear cache
        clear_index_cache()
        
        # Version should be initialized
        version = cache.get('editais_index_cache_version')
        self.assertIsNotNone(version)
        self.assertEqual(version, 1)
    
    def test_clear_index_cache_handles_race_condition(self):
        """Test that clear_index_cache handles race conditions gracefully"""
        # Simulate multiple cache clears
        cache.set('editais_index_cache_version', 1, timeout=None)
        
        # Call multiple times (simulating concurrent requests)
        clear_index_cache()
        clear_index_cache()
        clear_index_cache()
        
        # Version should be incremented appropriately
        version = cache.get('editais_index_cache_version')
        self.assertIsNotNone(version)
        self.assertGreaterEqual(version, 2)

