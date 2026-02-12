"""Funcoes utilitarias de cache para geracao padronizada de chaves."""

import logging
from typing import Optional, Dict, Any
from django.core.cache import cache
from django.contrib.auth.models import User
from django.http import HttpResponse

logger = logging.getLogger(__name__)


def get_user_cache_key(user: Optional[User]) -> str:
    """Gera o sufixo da chave de cache com base na autenticacao do usuario."""
    # Handle None or AnonymousUser (which has is_authenticated = False)
    if user and hasattr(user, "is_authenticated") and user.is_authenticated:
        if hasattr(user, "is_staff") and user.is_staff:
            return "staff"
        return "auth"
    return "public"


def get_cache_key(prefix: str, **kwargs) -> str:
    """Gera uma chave de cache padronizada a partir do prefixo e kwargs."""
    if not kwargs:
        return prefix

    sorted_items = sorted(kwargs.items())
    parts = [f"{key}:{value}" for key, value in sorted_items]
    return f"{prefix}_{'_'.join(parts)}"


def get_index_cache_key(page_number: str, cache_version: Optional[int] = None) -> str:
    """Gera chave de cache para a pagina de index com suporte a versao."""
    if cache_version is not None:
        return f"editais_index_page_{page_number}_v{cache_version}"
    return f"editais_index_page_{page_number}"


def get_detail_cache_key(
    model_type: str, identifier: str, user: Optional[User] = None
) -> str:
    """Gera chave de cache para views de detalhe."""
    user_key = get_user_cache_key(user)
    return get_cache_key(
        f"{model_type}_detail", identifier=identifier, user_key=user_key
    )


def get_cached_response(cache_key: str) -> Optional[HttpResponse]:
    """
    Recupera resposta HTTP do cache, se existir.

    Args:
        cache_key: Chave de cache para consulta

    Returns:
        HttpResponse se houver conteudo no cache; caso contrario, None
    """
    cached_content = cache.get(cache_key)
    if cached_content:
        return HttpResponse(cached_content)
    return None


def cache_response(cache_key: str, rendered_content: str, timeout: int) -> None:
    """
    Armazena o HTML renderizado no cache.

    Args:
        cache_key: Chave do cache
        rendered_content: HTML renderizado a ser armazenado
        timeout: Tempo de expiracao em segundos
    """
    cache.set(cache_key, rendered_content, timeout)
