"""
Cache utility functions for standardized cache key generation and management.

This module provides utilities for consistent cache key generation across the application,
preventing cache key collisions and ensuring proper cache invalidation.
"""

from typing import Optional, Dict, Any
from django.core.cache import cache
from django.contrib.auth.models import User


def get_user_cache_key(user: Optional[User]) -> str:
    """
    Generate a cache key suffix based on user authentication status.
    
    Args:
        user: Django User object or None
        
    Returns:
        str: Cache key suffix ('staff', 'auth', or 'public')
    """
    if user and user.is_authenticated:
        if user.is_staff:
            return 'staff'
        return 'auth'
    return 'public'


def get_cache_key(prefix: str, **kwargs: Any) -> str:
    """
    Generate a standardized cache key from prefix and keyword arguments.
    
    Args:
        prefix: Cache key prefix (e.g., 'edital_detail', 'index_page')
        **kwargs: Additional key components (will be sorted for consistency)
        
    Returns:
        str: Generated cache key
        
    Example:
        >>> get_cache_key('edital_detail', identifier='my-slug', user_key='public')
        'edital_detail_identifier:my-slug_user_key:public'
    """
    if not kwargs:
        return prefix
    
    # Sort kwargs for consistent key generation
    sorted_items = sorted(kwargs.items())
    parts = [f"{key}:{value}" for key, value in sorted_items]
    return f"{prefix}_{'_'.join(parts)}"


def get_index_cache_key(page_number: str, cache_version: Optional[int] = None) -> str:
    """
    Generate cache key for index pages with versioning support.
    
    Args:
        page_number: Page number as string
        cache_version: Optional cache version number
        
    Returns:
        str: Cache key for the index page
    """
    if cache_version is not None:
        return f'editais_index_page_{page_number}_v{cache_version}'
    return f'editais_index_page_{page_number}'


def get_detail_cache_key(
    model_type: str,
    identifier: str,
    user: Optional[User] = None
) -> str:
    """
    Generate cache key for detail views.
    
    Args:
        model_type: Type of model ('edital' or 'startup')
        identifier: Slug or PK identifier
        user: Optional user object for user-specific caching
        
    Returns:
        str: Cache key for the detail view
    """
    user_key = get_user_cache_key(user)
    return get_cache_key(
        f'{model_type}_detail',
        identifier=identifier,
        user_key=user_key
    )


