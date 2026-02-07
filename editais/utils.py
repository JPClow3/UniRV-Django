"""
Utility functions for the editais app.
"""

from typing import Optional, TYPE_CHECKING, List
from datetime import date, datetime
import logging
import re
import time
import bleach
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.utils.text import slugify
from django.core.cache import cache
from django.db import models, connection, DatabaseError, OperationalError
from django.db.models import QuerySet
from redis.exceptions import RedisError

from .constants import HTML_FIELDS, CACHE_FALLBACK_PAGE_RANGE
from .cache_utils import (
    get_index_cache_key as _get_index_cache_key,
)

if TYPE_CHECKING:
    from .models import Edital

logger = logging.getLogger(__name__)

# Allowed tags and attributes for HTML sanitization
ALLOWED_TAGS = [
    "p",
    "br",
    "strong",
    "em",
    "u",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "ul",
    "ol",
    "li",
    "blockquote",
    "a",
    "code",
    "pre",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "div",
    "span",
]
ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "target", "rel"],
    "div": ["class", "id"],
    "span": ["class"],
    "table": ["class"],
    "th": ["scope"],
    "abbr": ["title"],
    "acronym": ["title"],
}


def sanitize_html(text: Optional[str]) -> str:
    """
    Sanitiza conteúdo HTML para prevenir ataques XSS.

    Uses bleach library with protocol filtering for robust XSS prevention.
    Allows only http, https, and mailto protocols in href attributes.
    Also removes dangerous protocol strings from plain text as defense-in-depth.

    Args:
        text: Texto a ser sanitizado

    Returns:
        str: Texto sanitizado ou string vazia em caso de erro
    """
    if not text:
        return ""

    try:
        # Use bleach's protocol whitelist for robust XSS prevention in attributes
        # This properly handles all encoding bypass attempts (Unicode, URL encoding, etc.)
        # The protocols parameter handles javascript:, data:, vbscript: and other dangerous
        # protocols including HTML entity encoded variants (e.g., java&#x73;cript:)
        sanitized = bleach.clean(
            text,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            protocols=["http", "https", "mailto"],  # Only allow safe protocols
            strip=True,
        )

        # Defense-in-depth: remove dangerous protocol strings from plain text
        # This handles edge cases where dangerous protocols appear as plain text
        dangerous_protocols = [
            r"javascript\s*:",
            r"vbscript\s*:",
            r"data\s*:\s*text/html",
        ]
        for pattern in dangerous_protocols:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)

        return sanitized
    except (TypeError, AttributeError, ValueError) as e:
        # bleach.clean() can raise TypeError (invalid type), AttributeError (missing attribute),
        # or ValueError (invalid value). Catch these specifically.
        logger.error(f"Erro ao sanitizar HTML: {e}", exc_info=True)
        # Return empty string on error to prevent XSS
        return ""


def determine_edital_status(
    current_status: str,
    start_date: Optional[date],
    end_date: Optional[date],
    today: Optional[date] = None,
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
    if current_status in ("draft", "fechado"):
        return current_status

    # Se não há datas, mantém o status atual
    if not start_date and not end_date:
        return current_status

    # Se há apenas start_date (fluxo contínuo)
    if start_date and not end_date:
        if start_date <= today:
            return "aberto"
        else:
            return "programado"

    # Se há apenas end_date
    if end_date and not start_date:
        if end_date < today:
            return "fechado"
        else:
            return current_status

    # Se há ambas as datas
    if start_date and end_date:
        if end_date < today:
            return "fechado"
        elif start_date <= today:
            return "aberto"
        else:
            return "programado"

    return current_status


def generate_unique_slug(
    text: str,
    model_class: type[models.Model],
    slug_field_name: str = "slug",
    prefix: Optional[str] = None,
    pk: Optional[int] = None,
    max_length: int = 255,
    max_attempts: int = 10,
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
    # Gerar slug base
    if not text:
        # Se texto está vazio, usar apenas o prefixo ou padrão
        base_slug = prefix or "item"
    else:
        base_slug = slugify(text)
        if prefix:
            base_slug = f"{prefix}-{base_slug}"

    # Truncar se necessário
    base_slug = base_slug[:max_length]
    if not base_slug:
        # Se o slug base está vazio, usar um padrão
        base_slug = prefix or "item"

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
        suffix = f"-{attempt}"
        # Garantir que o slug não exceda max_length
        available_length = max_length - len(suffix)
        slug = f"{base_slug[:available_length]}{suffix}"

    # Se todas as tentativas falharam, usar timestamp com precisão de microssegundos
    # para evitar colisões em requisições simultâneas
    timestamp_suffix = f"-{int(time.time() * 1000000)}"
    available_length = max_length - len(timestamp_suffix)
    return f"{base_slug[:available_length]}{timestamp_suffix}"


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
    Cria atributos {field}_safe para cada campo HTML.

    Isso permite que HTML sanitizado seja renderizado sem escape adicional.

    Args:
        edital: Instância do modelo Edital
    """
    for field_name in HTML_FIELDS:
        if hasattr(edital, field_name):
            field_value = getattr(edital, field_name)
            if field_value:
                # Create {field}_safe attribute instead of modifying original
                sanitized = sanitize_html(field_value)
                setattr(edital, f"{field_name}_safe", mark_safe(sanitized))


def apply_tipo_filter(queryset: QuerySet, tipo: Optional[str]) -> QuerySet:
    """
    Aplica filtro de tipo (tipo de edital) ao queryset.

    Args:
        queryset: QuerySet de Editais
        tipo: Tipo de edital para filtrar (opcional)

    Returns:
        QuerySet filtrado
    """
    if not tipo or tipo == "all":
        return queryset

    # Se o modelo Edital tiver campo 'tipo', filtrar por ele
    # Caso contrário, retornar queryset sem filtro
    if hasattr(queryset.model, "tipo"):
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
        return datetime.strptime(date_string, "%Y-%m-%d").date()
    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid date filter value: {date_string!r} - {e}")
        return None


# Phase labels for startup maturity (symbolic, not pass/fail). Used in forms, filters, UI.
PHASE_CHOICES = [
    ("pre_incubacao", "Ideação"),
    ("incubacao", "MVP"),
    ("graduada", "Escala"),
    ("suspensa", "Suspensa"),
]


def get_startup_status_mapping() -> dict:
    """
    Retorna mapeamento de labels de status para valores de status.
    Mapeia nomes de exibição (case-insensitive) para valores do modelo.
    Inclui tanto labels de fase (Ideação, MVP, Escala) quanto labels antigas (Pré-Incubação, etc.).
    """
    from .models import Startup

    mapping = {label.lower(): status for status, label in Startup.STATUS_CHOICES}
    # Add phase labels so filter dropdown can use them
    for code, label in PHASE_CHOICES:
        mapping[label.lower()] = code
    return mapping


def get_startup_sort_mapping() -> dict:
    """
    Retorna mapeamento de opções de ordenação para startups.
    """
    return {
        "submitted_on_desc": "-submitted_on",
        "submitted_on_asc": "submitted_on",
        "name_asc": "name",
        "name_desc": "-name",
        "status_asc": "status",
        "status_desc": "-status",
        "updated_on_desc": "-data_atualizacao",
        "updated_on_asc": "data_atualizacao",
    }


def clear_dashboard_cache() -> None:
    """
    Clear dashboard-specific cache keys.

    Clears cached statistics, recent editais, and deadline editais used by the admin dashboard.
    This function is called as part of clear_all_caches() to ensure dashboard shows fresh data.
    """
    dashboard_keys = [
        "admin_dashboard_stats",
        "admin_dashboard_recentes",
        "admin_dashboard_deadline",
    ]
    try:
        for key in dashboard_keys:
            cache.delete(key)
    except (ConnectionError, TimeoutError, RedisError, OSError) as e:
        logger.warning(
            "Failed to clear dashboard cache - cache unavailable: %s", e, exc_info=True
        )


def clear_all_caches() -> None:
    """
    Clear all relevant caches including index and dashboard caches.

    This function should be called after any edital create/update/delete operation
    to ensure all cached data is invalidated.
    """
    clear_index_cache()
    clear_dashboard_cache()


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
    version_key = "editais_index_cache_version"

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
            cache.set(
                version_key, new_version, timeout=None
            )  # Never expire the version key
    except (ConnectionError, TimeoutError, RedisError, OSError) as e:
        # Cache is unavailable - fail gracefully
        # Log the error but don't raise - cache clearing is not critical
        logger.warning(
            "Failed to clear index cache - cache unavailable: %s", e, exc_info=True
        )
        return

    # Also clear the old version key pattern for pages as a fallback
    # (in case any old cache entries exist without versioning)
    # Note: This is a fallback mechanism. The versioning system above should handle most cases.
    try:
        for page_num in range(1, CACHE_FALLBACK_PAGE_RANGE + 1):
            old_cache_key = f"editais_index_page_{page_num}"
            cache.delete(old_cache_key)
    except (ConnectionError, TimeoutError, RedisError, OSError) as e:
        # Cache delete failed - log but don't raise
        logger.warning(
            "Failed to delete old cache keys - cache unavailable: %s", e, exc_info=True
        )


def get_index_cache_key(page_number: str, cache_version: Optional[int] = None) -> str:
    """
    Backwards-compatible helper for generating index cache keys.

    Historically, tests imported get_index_cache_key from this module.
    The implementation now lives in editais.cache_utils, so this thin
    wrapper simply forwards to the canonical implementation to avoid
    breaking existing callers.
    """
    return _get_index_cache_key(page_number, cache_version)


def get_search_suggestions(query: str, limit: int = 3) -> List[str]:
    """
    Get search suggestions using PostgreSQL trigram similarity.

    Uses PostgreSQL's pg_trgm extension to find similar titles, entity names,
    or edital numbers when no search results are found. This provides helpful
    "Did you mean?" suggestions to users.

    Args:
        query: Search query string
        limit: Maximum number of suggestions to return (default: 3)

    Returns:
        List of suggestion strings (titles, entity names, or edital numbers)
        Returns empty list if not using PostgreSQL, extension not available,
        or query is empty.
    """
    if not query or not query.strip():
        return []

    # Only work with PostgreSQL
    if connection.vendor != "postgresql":
        return []

    # Normalize query for cache key
    query_normalized = query.strip().lower()
    cache_key = f"search_suggestions_{query_normalized}_{limit}"

    # Check cache first
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    suggestions = []

    try:
        with connection.cursor() as cursor:
            # Check if pg_trgm extension is available
            cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm';")
            if not cursor.fetchone():
                # Extension not available, return empty list
                logger.debug("pg_trgm extension not available for search suggestions")
                return []

            # Search across multiple fields and combine results
            # Use UNION to get unique suggestions from different fields
            cursor.execute(
                """
                WITH suggestions AS (
                    SELECT DISTINCT titulo as suggestion,
                           similarity(titulo, %s) as sim
                    FROM editais_edital
                    WHERE titulo IS NOT NULL 
                      AND similarity(titulo, %s) > 0.3
                    
                    UNION
                    
                    SELECT DISTINCT entidade_principal as suggestion,
                           similarity(entidade_principal, %s) as sim
                    FROM editais_edital
                    WHERE entidade_principal IS NOT NULL 
                      AND similarity(entidade_principal, %s) > 0.3
                    
                    UNION
                    
                    SELECT DISTINCT numero_edital as suggestion,
                           similarity(numero_edital, %s) as sim
                    FROM editais_edital
                    WHERE numero_edital IS NOT NULL 
                      AND similarity(numero_edital, %s) > 0.3
                )
                SELECT suggestion
                FROM suggestions
                ORDER BY sim DESC
                LIMIT %s
            """,
                [query, query, query, query, query, query, limit],
            )

            suggestions = [row[0] for row in cursor.fetchall() if row[0]]

    except (DatabaseError, OperationalError) as e:
        # Database error (connection, query, etc.) - fail gracefully
        # Suggestions are a nice-to-have feature, not critical
        logger.warning("Error generating search suggestions: %s", e, exc_info=True)
        return []

    # Cache suggestions for 5 minutes
    if suggestions:
        cache.set(cache_key, suggestions, 300)  # 5 minutes
    else:
        # Cache empty result for shorter time to allow retry
        cache.set(cache_key, [], 60)  # 1 minute

    return suggestions
