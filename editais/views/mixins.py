"""
View mixins for common patterns across the editais app.

This module provides reusable mixins for common view functionality,
reducing code duplication and ensuring consistent behavior.
"""

from typing import Optional
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpRequest, HttpResponse
from django.core.cache import cache
from django.template.loader import render_to_string

from ..constants import CACHE_TTL_15_MINUTES
from ..cache_utils import get_detail_cache_key


class StaffRequiredMixin(UserPassesTestMixin):
    """
    Mixin that requires user to be staff.
    
    Can be used with class-based views as an alternative to the @staff_required decorator.
    """
    def test_func(self):
        return self.request.user.is_staff


class CachedDetailViewMixin:
    """
    Mixin for detail views that need caching.
    
    Provides methods for cache key generation and cached response handling.
    """
    cache_ttl = CACHE_TTL_15_MINUTES
    model_name = None  # Should be set by subclass (e.g., 'edital', 'startup')
    
    def get_cache_key(self, identifier: str, request: HttpRequest) -> str:
        """
        Generate cache key for this detail view.
        
        Args:
            identifier: Slug or PK identifier
            request: HttpRequest object
            
        Returns:
            str: Cache key
        """
        model_name = self.model_name or self.model.__name__.lower()
        return get_detail_cache_key(model_name, identifier, request.user)
    
    def get_cached_response(self, cache_key: str) -> Optional[HttpResponse]:
        """
        Get cached response if available.
        
        Args:
            cache_key: Cache key to check
            
        Returns:
            HttpResponse if cached, None otherwise
        """
        cached_content = cache.get(cache_key)
        if cached_content:
            from django.http import HttpResponse
            return HttpResponse(cached_content)
        return None
    
    def cache_response(self, cache_key: str, rendered_content: str) -> None:
        """
        Cache rendered content.
        
        Args:
            cache_key: Cache key
            rendered_content: Rendered template content
        """
        cache.set(cache_key, rendered_content, self.cache_ttl)


class FilteredListViewMixin:
    """
    Mixin for list views that support filtering.
    
    Provides common filter handling logic.
    """
    def get_search_query(self, request: HttpRequest) -> str:
        """Extract search query from request."""
        return request.GET.get('search', '').strip()
    
    def get_status_filter(self, request: HttpRequest) -> str:
        """Extract status filter from request."""
        return request.GET.get('status', '').strip()
    
    def get_tipo_filter(self, request: HttpRequest) -> str:
        """Extract tipo filter from request."""
        return request.GET.get('tipo', '').strip()
    
    def apply_filters(self, queryset, request: HttpRequest):
        """
        Apply common filters to queryset.
        
        Subclasses should override this to add model-specific filters.
        """
        from ..utils import apply_tipo_filter
        from .public import build_search_query
        
        search_query = self.get_search_query(request)
        if search_query:
            queryset = queryset.filter(build_search_query(search_query))
        
        status_filter = self.get_status_filter(request)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        tipo_filter = self.get_tipo_filter(request)
        queryset = apply_tipo_filter(queryset, tipo_filter)
        
        return queryset

