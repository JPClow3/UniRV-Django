"""
Root conftest.py — shared pytest fixtures for AgroHub.

Re-exports factory_boy factories as pytest fixtures via ``pytest-factoryboy``
and provides common helpers (authenticated client, mock email, etc.).
"""

import os
import django
from django.conf import settings
import pytest
from pytest_factoryboy import register


# Configure Django cache for tests
# Uses LocMemCache for instant testing - no Redis required
def pytest_configure():
    """Configure pytest and Django settings before tests run."""
    if not settings.configured:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "UniRV_Django.settings")
        django.setup()

    # Ensure testing flag is enabled for rate limiting/caching behavior
    settings.TESTING = True

    # Override cache backend for testing - use LocMemCache for instant tests
    # Falls back to LocMemCache if Redis is not available (for SQLite dev testing)
    try:
        import redis
    except ImportError:
        redis_available = False
    else:
        redis_available = True
        try:
            redis.Redis(
                host=settings.CACHES["default"]
                .get("LOCATION", "localhost:6379")
                .split(":")[0],
                port=int(
                    settings.CACHES["default"]
                    .get("LOCATION", "localhost:6379")
                    .split(":")[1]
                ),
                socket_connect_timeout=1,
            ).ping()
        except (redis.ConnectionError, OSError, ValueError, IndexError):
            redis_available = False

    if not redis_available:
        # Redis unavailable; switch to local memory cache for all backends
        locmem_cache = {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "unique-snowflake",
        }
        settings.CACHES = {
            "default": locmem_cache,
            "sessions": locmem_cache,
        }
        # Recarrega as conexoes de cache com as novas configuracoes
        from django.core.cache import caches

        caches.close_all()
        from django.core.cache import cache as django_cache

        django_cache.clear()


from editais.tests.factories import (
    UserFactory,
    StaffUserFactory,
    SuperUserFactory,
    TagFactory,
    EditalFactory,
    StartupFactory,
    EditalValorFactory,
    CronogramaFactory,
)

# Register factory_boy factories as pytest fixtures.
# This auto-creates fixtures like ``user``, ``staff_user``, ``edital``, etc.
register(UserFactory)
register(StaffUserFactory, _name="staff_user")
register(SuperUserFactory, _name="super_user")
register(TagFactory)
register(EditalFactory)
register(StartupFactory)
register(EditalValorFactory)
register(CronogramaFactory)


@pytest.fixture()
def auth_client(client, user):
    """Django test client authenticated as a regular user."""
    client.force_login(user)
    return client


@pytest.fixture()
def staff_client(client, staff_user):
    """Django test client authenticated as a staff user."""
    client.force_login(staff_user)
    return client


@pytest.fixture()
def super_client(client, super_user):
    """Django test client authenticated as a superuser."""
    client.force_login(super_user)
    return client


@pytest.fixture()
def edital_with_valores(edital_factory, edital_valor_factory):
    """Edital with associated EditalValor instances."""
    edital = edital_factory()
    edital_valor_factory(edital=edital, tipo_valor="total")
    edital_valor_factory(edital=edital, tipo_valor="mensal")
    return edital


@pytest.fixture()
def edital_with_cronograma(edital_factory, cronograma_factory):
    """Edital with associated Cronograma items."""
    edital = edital_factory()
    cronograma_factory(edital=edital)
    cronograma_factory(edital=edital)
    return edital


@pytest.fixture()
def cache():
    """
    Inject Django's cache for tests.
    Uses the configured backend (LocalMemCache by default for ci/local testing).
    """
    from django.core.cache import cache as django_cache

    # Clear before test
    try:
        django_cache.clear()
    except Exception:
        pass  # Redis might not be available (Windows issue)
    yield django_cache
    # Clear after test
    try:
        django_cache.clear()
    except Exception:
        pass
