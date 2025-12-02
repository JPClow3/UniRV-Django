"""
Utility functions for the editais app.
"""

from typing import Optional, TYPE_CHECKING
from datetime import date
import logging
import bleach
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.core.cache import cache

from .constants import HTML_FIELDS, CACHE_FALLBACK_PAGE_RANGE

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
        return ""
    # Ensure text is a string
    if not isinstance(text, str):
        text = str(text)
    try:
        cleaned = bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)
        return cleaned
    except Exception as e:
        logger.error(f"Erro ao sanitizar HTML: {e}")
        # If sanitization fails, return empty string to prevent XSS
        return ''


def determine_edital_status(
    *,
    current_status: str,
    start_date: Optional[date],
    end_date: Optional[date],
    today: Optional[date] = None,
) -> str:
    """
    Centraliza a lógica de status para manter consistência entre salvamentos e jobs.
    
    Lógica de transição:
    - draft: sempre permanece draft (não muda automaticamente)
    - programado: muda para 'aberto' quando start_date <= today
    - aberto: muda para 'fechado' quando end_date < today
    - em_andamento: muda para 'fechado' quando end_date < today
    - fechado: permanece fechado (não muda automaticamente)
    """
    today = today or timezone.now().date()

    # Draft status nunca muda automaticamente
    if current_status == 'draft':
        return 'draft'
    
    # Fechado status nunca muda automaticamente (só manualmente)
    if current_status == 'fechado':
        return 'fechado'

    # Caso 1: Tem start_date e end_date
    if start_date and end_date:
        # Se já passou do prazo, deve estar fechado
        if end_date < today:
            if current_status in ['aberto', 'em_andamento']:
                return 'fechado'
            return current_status
        
        # Se está no período válido (start_date <= today <= end_date)
        if start_date <= today <= end_date:
            # Se estava programado, deve abrir
            if current_status == 'programado':
                return 'aberto'
            # Se já estava aberto ou em_andamento, mantém
            if current_status in ['aberto', 'em_andamento']:
                return current_status
            # Outros statuses no período válido viram aberto
            return 'aberto'
        
        # Se ainda não começou (start_date > today)
        if start_date > today:
            # Se não está programado ou draft, programa
            if current_status not in ['draft', 'programado', 'fechado']:
                return 'programado'
            return current_status
    
    # Caso 2: Tem start_date mas não tem end_date (fluxo contínuo)
    elif start_date and not end_date:
        # Se já começou (start_date <= today)
        if start_date <= today:
            # Se estava programado, deve abrir
            if current_status == 'programado':
                return 'aberto'
            # Se já estava aberto ou em_andamento, mantém
            if current_status in ['aberto', 'em_andamento']:
                return current_status
            # Outros statuses viram aberto
            return 'aberto'
        
        # Se ainda não começou (start_date > today) - this is always true here
        # Se não está programado ou draft, programa
        if current_status not in ['draft', 'programado', 'fechado']:
            return 'programado'
        return current_status
    
    # Caso 3: Não tem start_date mas tem end_date
    elif not start_date and end_date:
        # Se já passou do prazo, deve estar fechado
        if end_date < today:
            if current_status in ['aberto', 'em_andamento', 'programado']:
                return 'fechado'
            return current_status
        
        # Se ainda não passou do prazo (end_date >= today)
        # Mantém o status atual (pode estar aberto, em_andamento, etc.)
        return current_status
    
    # Caso 4: Não tem nem start_date nem end_date
    # Mantém o status atual (não há lógica automática)
    return current_status


def sanitize_edital_fields(edital: 'Edital') -> 'Edital':
    """
    Sanitiza todos os campos de texto de uma instância de edital.
    
    Args:
        edital: Instância do modelo Edital
        
    Returns:
        Edital: Instância sanitizada
    """
    for field in HTML_FIELDS:
        value = getattr(edital, field, None)
        if value:
            setattr(edital, field, sanitize_html(value))
    return edital


def mark_edital_fields_safe(edital: 'Edital') -> 'Edital':
    """
    Sanitiza e marca campos HTML como seguros para renderização em templates.
    Cria atributos {field}_safe que contêm HTML sanitizado e marcado como seguro.
    Os campos originais permanecem inalterados para que Django possa auto-escapá-los.
    
    Args:
        edital: Instância do modelo Edital
        
    Returns:
        Edital: Instância com campos _safe sanitizados e marcados como seguros
    """
    for field in HTML_FIELDS:
        value = getattr(edital, field, None)
        if value:
            # Sanitize the value and mark it as safe for the _safe attribute
            # Original field remains unchanged (will be auto-escaped by Django)
            sanitized_value = sanitize_html(value)
            setattr(edital, f'{field}_safe', mark_safe(sanitized_value))
    return edital


def get_project_status_mapping() -> dict:
    """
    Retorna um dicionário que mapeia nomes de status de projeto (display names)
    para valores de status do modelo.
    
    Returns:
        dict: Mapeamento de nomes de exibição para valores de status
    """
    return {
        'pré-incubação': 'pre_incubacao',
        'pre-incubacao': 'pre_incubacao',
        'incubação': 'incubacao',
        'incubacao': 'incubacao',
        'graduada': 'graduada',
        'suspensa': 'suspensa',
    }


def get_project_sort_mapping() -> dict:
    """
    Retorna um dicionário que mapeia nomes de ordenação para campos de ordenação.
    
    Returns:
        dict: Mapeamento de nomes de ordenação para campos do modelo
    """
    return {
        'submitted_on_desc': '-submitted_on',  # Default: newest first
        'submitted_on_asc': 'submitted_on',
        'name_asc': 'name',
        'name_desc': '-name',
        'status_asc': 'status',
        'status_desc': '-status',
        'note_desc': '-note',
        'note_asc': 'note',
    }


def clear_index_cache() -> None:
    """
    Clear all index page cache keys.
    Uses a cache versioning pattern: increment a version number that's part of all cache keys.
    This invalidates all cached pages regardless of page number.
    
    Uses atomic operations to prevent race conditions when multiple requests try to clear cache simultaneously.
    
    This function is public and can be called from views, management commands, or services.
    """
    version_key = 'editais_index_cache_version'
    
    # Use atomic increment if available (Redis, Memcached), otherwise fallback to get+set
    try:
        # Try atomic increment first (works with Redis, Memcached)
        new_version = cache.incr(version_key)
        if new_version is None:
            # Key doesn't exist, initialize it
            cache.set(version_key, 1, timeout=None)
    except (AttributeError, ValueError, TypeError):
        # Fallback for cache backends that don't support incr (e.g., LocMemCache)
        # Use a simple increment - race condition is acceptable for cache invalidation
        # (worst case: cache is cleared multiple times, which is harmless)
        current_version = cache.get(version_key, 0)
        new_version = current_version + 1
        cache.set(version_key, new_version, timeout=None)  # Never expire the version key
    
    # Also clear the old version key pattern for pages as a fallback
    # (in case any old cache entries exist without versioning)
    # Note: This is a fallback mechanism. The versioning system above should handle most cases.
    for page_num in range(1, CACHE_FALLBACK_PAGE_RANGE + 1):
        old_cache_key = f'editais_index_page_{page_num}'
        cache.delete(old_cache_key)

