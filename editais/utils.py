"""
Utility functions for the editais app.
"""

from typing import Optional
import logging
import bleach
from django.utils.safestring import mark_safe

from .constants import HTML_FIELDS
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


def sanitize_edital_fields(edital: Edital) -> Edital:
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


def mark_edital_fields_safe(edital: Edital) -> Edital:
    """
    Marca campos HTML sanitizados como seguros para renderização em templates.
    
    Args:
        edital: Instância do modelo Edital
        
    Returns:
        Edital: Instância com campos marcados como seguros
    """
    for field in HTML_FIELDS:
        value = getattr(edital, field, None)
        if value:
            setattr(edital, f'{field}_safe', mark_safe(value))
    return edital

