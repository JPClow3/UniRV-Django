"""Mixins de views para padrões comuns no app de editais."""

from typing import Optional
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpRequest, HttpResponse
from django.core.cache import cache

from ..constants import CACHE_TTL_15_MINUTES
from ..cache_utils import get_detail_cache_key


class StaffRequiredMixin(UserPassesTestMixin):
    """Mixin que exige que o usuário seja staff."""

    def test_func(self):
        # Verifica autenticação primeiro, depois status de staff
        return (
            self.request.user.is_authenticated
            and hasattr(self.request.user, "is_staff")
            and self.request.user.is_staff
        )


class CachedDetailViewMixin:
    """Mixin para views de detalhe que necessitam de cache."""

    cache_ttl = CACHE_TTL_15_MINUTES
    model_name = None

    def get_cache_key(self, identifier: str, request: HttpRequest) -> str:
        """Gera a chave de cache para esta view de detalhe."""
        model_name = self.model_name or self.model.__name__.lower()
        return get_detail_cache_key(model_name, identifier, request.user)

    def get_cached_response(self, cache_key: str) -> Optional[HttpResponse]:
        """Retorna a resposta em cache, se disponível."""
        cached_content = cache.get(cache_key)
        if cached_content is not None:
            return HttpResponse(cached_content)
        return None

    def cache_response(self, cache_key: str, rendered_content: str) -> None:
        """Armazena o conteúdo renderizado em cache."""
        cache.set(cache_key, rendered_content, self.cache_ttl)


class FilteredListViewMixin:
    """Mixin para views de lista com suporte a filtragem."""

    def get_search_query(self, request: HttpRequest) -> str:
        """Extrai a consulta de busca da requisição."""
        return request.GET.get("search", "").strip()

    def get_status_filter(self, request: HttpRequest) -> str:
        """Extrai o filtro de status da requisição."""
        return request.GET.get("status", "").strip()

    def get_tipo_filter(self, request: HttpRequest) -> str:
        """Extrai o filtro de tipo da requisição."""
        return request.GET.get("tipo", "").strip()

    def apply_filters(self, queryset, request: HttpRequest):
        """Aplica filtros comuns ao queryset."""
        from ..utils import apply_tipo_filter

        search_query = self.get_search_query(request)
        if search_query:
            # Usa o método de busca do model (busca full-text do PostgreSQL)
            queryset = queryset.search(search_query)

        status_filter = self.get_status_filter(request)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        tipo_filter = self.get_tipo_filter(request)
        queryset = apply_tipo_filter(queryset, tipo_filter)

        return queryset
