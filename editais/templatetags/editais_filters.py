"""
Template tags customizados para o app editais.
"""

from django import template
from django.utils.html import escape
from urllib.parse import urlencode
import re

register = template.Library()


@register.filter
def days_until(date):
    """
    Calcula quantos dias faltam até a data (ou quantos dias se passaram se negativo).
    """
    if not date:
        return None
    
    from django.utils import timezone
    today = timezone.now().date()
    delta = date - today
    return delta.days


@register.filter
def is_deadline_soon(date):
    """
    Retorna True se a data está nos próximos 7 dias (prazo próximo).
    """
    if not date:
        return False
    
    days = days_until(date)
    return days is not None and 0 <= days <= 7


@register.filter
def is_transparent_header(url_name):
    """
    Indica se o cabeçalho deve usar o tema transparente/gradiente.
    """
    if not url_name:
        return False
    return url_name in {'edital_detail', 'edital_detail_slug'}


@register.filter
def escape_attrs(attrs_string):
    """
    Safely escape HTML attributes string to prevent XSS attacks.
    
    This filter takes a string of HTML attributes (e.g., 'target="_blank" rel="noopener"')
    and escapes special characters in attribute values while preserving the structure.
    
    Usage in templates:
        {% include "components/button.html" with attrs='target="_blank" rel="noopener"'|escape_attrs %}
    
    Note: This filter should be used when passing user-generated or untrusted data
    to the attrs parameter. For hardcoded strings, it's optional but recommended.
    """
    if not attrs_string:
        return ''
    
    # Pattern to match attribute="value" or attribute='value' or attribute=value
    # Handles: attr="value", attr='value', attr=value, and attributes with spaces in values
    attr_pattern = r'(\w+)=(["\'])([^"\']*)\2|(\w+)=([^\s>]+)'
    
    def escape_attr_value(match):
        if match.group(1):  # Matched quoted attribute
            attr_name = match.group(1)
            quote = match.group(2)
            attr_value = match.group(3)
            escaped_value = escape(attr_value)
            return f'{attr_name}={quote}{escaped_value}{quote}'
        else:  # Matched unquoted attribute
            attr_name = match.group(4)
            attr_value = match.group(5)
            escaped_value = escape(attr_value)
            return f'{attr_name}="{escaped_value}"'
    
    # Replace all attribute values with escaped versions
    escaped = re.sub(attr_pattern, escape_attr_value, attrs_string)
    
    return escaped
