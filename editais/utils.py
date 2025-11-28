"""
Utility functions for the editais app.
"""

from typing import Optional, TYPE_CHECKING
from datetime import date
import logging
import bleach
from django.utils.safestring import mark_safe
from django.utils import timezone

from .constants import HTML_FIELDS

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
    """
    today = today or timezone.now().date()

    if current_status == 'draft':
        return 'draft'

    if start_date and end_date:
        if end_date < today and current_status == 'aberto':
            return 'fechado'
        if start_date <= today <= end_date and current_status == 'programado':
            return 'aberto'
        if start_date > today and current_status not in ['draft', 'programado']:
            return 'programado'
    elif start_date and not end_date:
        if start_date <= today and current_status == 'programado':
            return 'aberto'
        if start_date > today and current_status not in ['draft', 'programado']:
            return 'programado'
    elif not start_date and end_date:
        if end_date < today and current_status == 'aberto':
            return 'fechado'

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

