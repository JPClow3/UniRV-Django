"""Cache utility functions for standardized cache key generation and management."""

import logging
from typing import Optional, Dict, Any
from django.core.cache import cache
from django.contrib.auth.models import User
from django.http import HttpResponse

logger = logging.getLogger(__name__)


def get_user_cache_key(user: Optional[User]) -> str:
    """Generate a cache key suffix based on user authentication status."""
    # Handle None or AnonymousUser (which has is_authenticated = False)
    if user and hasattr(user, "is_authenticated") and user.is_authenticated:
        if hasattr(user, "is_staff") and user.is_staff:
            return "staff"
        return "auth"
    return "public"


def get_cache_key(prefix: str, **kwargs) -> str:
    """Generate a standardized cache key from prefix and keyword arguments."""
    if not kwargs:
        return prefix

    sorted_items = sorted(kwargs.items())
    parts = [f"{key}:{value}" for key, value in sorted_items]
    return f"{prefix}_{'_'.join(parts)}"


def get_index_cache_key(page_number: str, cache_version: Optional[int] = None) -> str:
    """Generate cache key for index pages with versioning support."""
    if cache_version is not None:
        return f"editais_index_page_{page_number}_v{cache_version}"
    return f"editais_index_page_{page_number}"


def get_detail_cache_key(
    model_type: str, identifier: str, user: Optional[User] = None
) -> str:
    """Generate cache key for detail views."""
    user_key = get_user_cache_key(user)
    return get_cache_key(
        f"{model_type}_detail", identifier=identifier, user_key=user_key
    )


def get_cached_response(cache_key: str) -> Optional[HttpResponse]:
    """
    Get cached HTTP response if available.

    Args:
        cache_key: Cache key to look up

    Returns:
        HttpResponse if cached content exists, None otherwise
    """
    cached_content = cache.get(cache_key)
    if cached_content:
        return HttpResponse(cached_content)
    return None


def cache_response(cache_key: str, rendered_content: str, timeout: int) -> None:
    """
    Cache rendered HTTP response content.

    Args:
        cache_key: Cache key to store content under
        rendered_content: Rendered HTML content to cache
        timeout: Cache timeout in seconds
    """
    cache.set(cache_key, rendered_content, timeout)
