"""
Template tags customizados para o app editais.
"""

from django import template
from urllib.parse import urlencode

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
