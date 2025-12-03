"""
Utility functions for the editais app.
"""

from typing import Optional, TYPE_CHECKING, Union
from datetime import date, datetime
import logging
import re
import time
import bleach
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.utils.text import slugify
from django.core.cache import cache
from django.db import models
from django.db.models import QuerySet

from .constants import HTML_FIELDS, CACHE_FALLBACK_PAGE_RANGE, SLUG_GENERATION_MAX_ATTEMPTS_EDITAL, SLUG_GENERATION_MAX_ATTEMPTS_PROJECT, CACHE_TTL_15_MINUTES

if TYPE_CHECKING:
    from .models import Edital

logger = logging.getLogger(__name__)

# Allowed tags and attributes for HTML sanitization
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'blockquote', 'a', 'code', 'pre', 'table',
    'thead', 'tbody', 'tr', 'th', 'td', 'div', 'span'
]
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target', 'rel'],
    'div': ['class', 'id'],
    'span': ['class'],
    'table': ['class'],
    'th': ['scope'],
    'abbr': ['title'],
    'acronym': ['title']
}


def sanitize_html(text: Optional[str]) -> str:
    """
    Sanitiza conteúdo HTML para prevenir ataques XSS.
    
    Args:
        text: Texto a ser sanitizado
        
    Returns:
        str: Texto sanitizado ou string vazia em caso de erro
    """
    if not text:
        return ''
    
    # Remove javascript: and data:text/html URLs before sanitization
    # This prevents XSS through href/src attributes
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'data:text/html', '', text, flags=re.IGNORECASE)
    
    try:
        # Sanitize HTML using bleach
        sanitized = bleach.clean(
            text,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            strip=True
        )
        
        # Remove javascript: and data:text/html URLs after sanitization as well
        # (in case they were added back or missed)
        sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'data:text/html', '', sanitized, flags=re.IGNORECASE)
        
        return sanitized
    except Exception as e:
        logger.error(f"Erro ao sanitizar HTML: {e}", exc_info=True)
        # Return empty string on error to prevent XSS
        return ''


def determine_edital_status(
    current_status: str,
    start_date: Optional[date],
    end_date: Optional[date],
    today: Optional[date] = None
) -> str:
    """
    Determina o status de um edital com base nas datas.
    
    Regras:
    - Draft e fechado nunca mudam automaticamente
    - Se start_date <= today <= end_date: aberto
    - Se today > end_date: fechado
    - Se start_date > today: programado
    
    Args:
        current_status: Status atual do edital
        start_date: Data de início (opcional)
        end_date: Data de fim (opcional)
        today: Data de hoje (padrão: timezone.now().date())
        
    Returns:
        str: Novo status do edital
    """
    if today is None:
        today = timezone.now().date()
    
    # Draft e fechado nunca mudam automaticamente
    if current_status in ('draft', 'fechado'):
        return current_status
    
    # Se não há datas, mantém o status atual
    if not start_date and not end_date:
        return current_status
    
    # Se há apenas start_date (fluxo contínuo)
    if start_date and not end_date:
        if start_date <= today:
            return 'aberto'
        else:
            return 'programado'
    
    # Se há apenas end_date
    if end_date and not start_date:
        if end_date < today:
            return 'fechado'
        else:
            return current_status
    
    # Se há ambas as datas
    if start_date and end_date:
        if end_date < today:
            return 'fechado'
        elif start_date <= today:
            return 'aberto'
        else:
            return 'programado'
    
    return current_status


def generate_unique_slug(
    text: str,
    model_class: type[models.Model],
    slug_field_name: str = 'slug',
    prefix: Optional[str] = None,
    pk: Optional[int] = None,
    max_length: int = 255,
    max_attempts: int = 10
) -> str:
    """
    Gera um slug único para um modelo.
    
    Args:
        text: Texto para gerar o slug
        model_class: Classe do modelo Django
        slug_field_name: Nome do campo slug no modelo
        prefix: Prefixo opcional para o slug
        pk: Primary key do objeto (para excluir do check de unicidade)
        max_length: Comprimento máximo do slug
        max_attempts: Número máximo de tentativas
        
    Returns:
        str: Slug único
    """
    if not text:
        return ''
    
    # Gerar slug base
    base_slug = slugify(text)
    if prefix:
        base_slug = f"{prefix}-{base_slug}"
    
    # Truncar se necessário
    base_slug = base_slug[:max_length]
    if not base_slug:
        # Se o slug base está vazio, usar um padrão
        base_slug = prefix or 'item'
    
    slug = base_slug
    attempt = 0
    
    # Verificar se o slug já existe
    while attempt < max_attempts:
        # Verificar unicidade (excluir o próprio objeto se pk fornecido)
        filter_kwargs = {slug_field_name: slug}
        queryset = model_class.objects.filter(**filter_kwargs)
        if pk:
            queryset = queryset.exclude(pk=pk)
        
        if not queryset.exists():
            return slug
        
        # Tentar com sufixo numérico
        attempt += 1
        suffix = f'-{attempt}'
        # Garantir que o slug não exceda max_length
        available_length = max_length - len(suffix)
        slug = f"{base_slug[:available_length]}{suffix}"
    
    # Se todas as tentativas falharam, usar timestamp
    timestamp_suffix = f'-{int(time.time())}'
    available_length = max_length - len(timestamp_suffix)
    return f"{base_slug[:available_length]}{timestamp_suffix}"


def get_detail_cache_key(model_type: str, identifier: str, user) -> str:
    """
    Gera uma chave de cache única para páginas de detalhe.
    
    A chave inclui o tipo de modelo, identificador (slug ou PK) e status de autenticação do usuário.
    Isso permite cache separado para usuários autenticados vs. não autenticados.
    
    Args:
        model_type: Tipo de modelo ('edital' ou 'startup')
        identifier: Identificador único (slug ou 'pk_{id}')
        user: Objeto User ou AnonymousUser
        
    Returns:
        str: Chave de cache
    """
    auth_status = 'auth' if user.is_authenticated else 'anon'
    return f'{model_type}_detail_{identifier}_{auth_status}'


def sanitize_edital_fields(edital) -> None:
    """
    Sanitiza todos os campos HTML de um objeto Edital.
    
    Args:
        edital: Instância do modelo Edital
    """
    for field_name in HTML_FIELDS:
        if hasattr(edital, field_name):
            field_value = getattr(edital, field_name)
            if field_value:
                sanitized = sanitize_html(field_value)
                setattr(edital, field_name, sanitized)


def mark_edital_fields_safe(edital) -> None:
    """
    Marca os campos HTML de um Edital como safe para renderização em templates.
    
    Isso permite que HTML sanitizado seja renderizado sem escape adicional.
    
    Args:
        edital: Instância do modelo Edital
    """
    for field_name in HTML_FIELDS:
        if hasattr(edital, field_name):
            field_value = getattr(edital, field_name)
            if field_value:
                setattr(edital, field_name, mark_safe(field_value))


def apply_tipo_filter(queryset: QuerySet, tipo: Optional[str]) -> QuerySet:
    """
    Aplica filtro de tipo (tipo de edital) ao queryset.
    
    Args:
        queryset: QuerySet de Editais
        tipo: Tipo de edital para filtrar (opcional)
        
    Returns:
        QuerySet filtrado
    """
    if not tipo or tipo == 'all':
        return queryset
    
    # Se o modelo Edital tiver campo 'tipo', filtrar por ele
    # Caso contrário, retornar queryset sem filtro
    if hasattr(queryset.model, 'tipo'):
        return queryset.filter(tipo=tipo)
    
    return queryset


def parse_date_filter(date_string: Optional[str]) -> Optional[date]:
    """
    Converte string de data em objeto date.
    
    Args:
        date_string: String de data no formato YYYY-MM-DD ou None
        
    Returns:
        date object ou None se string inválida
    """
    if not date_string:
        return None
    
    try:
        from datetime import datetime as dt
        return dt.strptime(date_string, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def get_project_status_mapping() -> dict:
    """
    Retorna mapeamento de status de projeto para exibição.
    
    Returns:
        dict: Mapeamento de status para labels
    """
    from .models import Project
    return {
        status: label
        for status, label in Project.STATUS_CHOICES
    }


def clear_index_cache() -> None:
    """
    Clear all index page cache keys.
    Uses a cache versioning pattern: increment a version number that's part of all cache keys.
    This invalidates all cached pages regardless of page number.
    
    RACE CONDITION HANDLING:
    Cache version increment may have race conditions when multiple requests try to clear
    cache simultaneously. This is acceptable - the worst case is cache cleared multiple
    times, which is harmless. The version increment uses atomic operations when available
    (Redis, Memcached), with a fallback to get+set for other backends.
    
    ERROR HANDLING:
    All cache operations are wrapped in try-except to handle cache failures gracefully.
    If cache is unavailable, the function will silently fail (fail-open behavior).
    
    This function is public and can be called from views, management commands, or services.
    """
    version_key = 'editais_index_cache_version'
    
    # Use atomic increment if available (Redis, Memcached), otherwise fallback to get+set
    # Wrap all cache operations in try-except to handle cache failures gracefully
    try:
        try:
            # Try atomic increment first (works with Redis, Memcached)
            new_version = cache.incr(version_key)
            if new_version is None:
                # Key doesn't exist, initialize it
                cache.set(version_key, 1, timeout=None)
        except (AttributeError, ValueError, TypeError):
            # Fallback for cache backends that don't support incr (e.g., LocMemCache)
            # RACE CONDITION NOTE: Simple increment may have race conditions, but this is acceptable
            # for cache invalidation. Worst case: cache cleared multiple times, which is harmless.
            # The goal is cache invalidation, not precise counting.
            current_version = cache.get(version_key, 0)
            new_version = current_version + 1
            cache.set(version_key, new_version, timeout=None)  # Never expire the version key
    except Exception:
        # Cache is unavailable (ConnectionError, etc.) - fail gracefully
        # Log the error but don't raise - cache clearing is not critical
        logger.warning("Failed to clear index cache - cache unavailable", exc_info=True)
        return
    
    # Also clear the old version key pattern for pages as a fallback
    # (in case any old cache entries exist without versioning)
    # Note: This is a fallback mechanism. The versioning system above should handle most cases.
    try:
        for page_num in range(1, CACHE_FALLBACK_PAGE_RANGE + 1):
            old_cache_key = f'editais_index_page_{page_num}'
            cache.delete(old_cache_key)
    except Exception:
        # Cache delete failed - log but don't raise
        logger.warning("Failed to delete old cache keys - cache unavailable", exc_info=True)
