"""View mixins for common patterns across the editais app."""

from typing import Optional
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpRequest, HttpResponse
from django.core.cache import cache

from ..constants import CACHE_TTL_15_MINUTES
from ..cache_utils import get_detail_cache_key


class StaffRequiredMixin(UserPassesTestMixin):
    """Mixin that requires user to be staff."""
    def test_func(self):
        # Check authentication first, then staff status
        return (self.request.user.is_authenticated and 
                hasattr(self.request.user, 'is_staff') and 
                self.request.user.is_staff)


class CachedDetailViewMixin:
    """Mixin for detail views that need caching."""
    cache_ttl = CACHE_TTL_15_MINUTES
    model_name = None
    
    def get_cache_key(self, identifier: str, request: HttpRequest) -> str:
        """Generate cache key for this detail view."""
        model_name = self.model_name or self.model.__name__.lower()
        return get_detail_cache_key(model_name, identifier, request.user)
    
    def get_cached_response(self, cache_key: str) -> Optional[HttpResponse]:
        """Get cached response if available."""
        cached_content = cache.get(cache_key)
        if cached_content:
            from django.http import HttpResponse
            return HttpResponse(cached_content)
        return None
    
    def cache_response(self, cache_key: str, rendered_content: str) -> None:
        """Cache rendered content."""
        cache.set(cache_key, rendered_content, self.cache_ttl)


class FilteredListViewMixin:
    """Mixin for list views that support filtering."""
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
        """Apply common filters to queryset."""
        from ..utils import apply_tipo_filter
        
        search_query = self.get_search_query(request)
        if search_query:
            # Use model's search method which handles PostgreSQL full-text search or SQLite fallback
            queryset = queryset.search(search_query)
        
        status_filter = self.get_status_filter(request)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        tipo_filter = self.get_tipo_filter(request)
        queryset = apply_tipo_filter(queryset, tipo_filter)
        
        return queryset

