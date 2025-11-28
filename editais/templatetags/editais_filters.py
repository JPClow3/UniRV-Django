"""
Template tags customizados para o app editais.
"""

from django import template
from urllib.parse import urlencode

register = template.Library()


@register.simple_tag
def preserve_filters(request, **kwargs):
    """
    Preserva todos os parâmetros de filtro da URL atual, permitindo sobrescrever alguns.
    
    Uso:
        {% preserve_filters request page=2 %}
        {% preserve_filters request search='' %}  # Remove search
    """
    params = request.GET.copy()
    
    # Atualizar ou remover parâmetros
    for key, value in kwargs.items():
        if value is None or value == '':
            # Remover parâmetro se valor for None ou vazio
            params.pop(key, None)
        else:
            params[key] = value
    
    return urlencode(params)


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
