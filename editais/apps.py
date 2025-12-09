import logging
import os
from django.apps import AppConfig
from django.conf import settings


logger = logging.getLogger(__name__)


class EditaisConfig(AppConfig):
    """App configuration for the 'editais' application.

    - default_auto_field ensures BigAutoField IDs by default (Django 3.2+).
    - verbose_name is shown in the Django admin site and elsewhere.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "editais"
    verbose_name = "Editais de Fomento"

    def ready(self):
        """
        Validate Redis cache connection if configured.
        
        This method is called after Django apps are fully loaded, so it's safe
        to import and use django.core.cache here. Connection failures are logged
        as warnings but do not prevent application startup.
        """
        # Only check Redis connection in production (non-DEBUG mode)
        if not settings.DEBUG:
            redis_host = os.environ.get('REDIS_HOST', '')
            if redis_host:
                # Check if cache backend is actually Redis (not LocMemCache fallback)
                cache_backend = settings.CACHES.get('default', {}).get('BACKEND', '')
                is_redis_backend = 'redis' in cache_backend.lower()
                
                if is_redis_backend:
                    try:
                        from django.core.cache import cache
                        
                        # Test Redis connection with a simple set/get operation
                        test_key = 'unirv_redis_connection_test'
                        test_value = 'ok'
                        cache.set(test_key, test_value, timeout=1)
                        retrieved_value = cache.get(test_key)
                        
                        if retrieved_value == test_value:
                            logger.info(f"Redis cache connection successful (host: {redis_host})")
                        else:
                            logger.warning(
                                f"Redis cache connection test failed: expected '{test_value}', "
                                f"got '{retrieved_value}'. Cache may not be working correctly."
                            )
                    except Exception as e:
                        # Log warning but don't crash startup
                        # This allows the app to continue with LocMemCache fallback if configured
                        logger.warning(
                            f"Redis cache connection validation failed: {e}. "
                            "The application will continue but cache functionality may be limited. "
                            "Check your REDIS_HOST and REDIS_PORT environment variables."
                        )
                else:
                    # REDIS_HOST is set but cache backend is not Redis (likely fell back to LocMemCache)
                    logger.warning(
                        f"REDIS_HOST is configured ({redis_host}) but cache backend is '{cache_backend}', "
                        "not Redis. Redis connection may have failed during startup. "
                        "Check your Redis server configuration and connectivity."
                    )

