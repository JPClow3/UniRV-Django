"""
Template tags customizados para o app editais.
"""

from typing import Optional
from datetime import date as date_type
from django import template
from urllib.parse import urlencode

register = template.Library()


@register.filter
def days_until(date: Optional[date_type]) -> Optional[int]:
    """
    Calcula quantos dias faltam até a data (ou quantos dias se passaram se negativo).
    Retorna None se a data for None, permitindo que filtros no template lidem
    corretamente com datas ausentes.
    
    Args:
        date: Objeto date ou None
        
    Returns:
        Optional[int]: Numero de dias até a data (negativo se no passado) ou None
    """
    if not date:
        return None
    
    from django.utils import timezone
    today = timezone.now().date()
    try:
        delta = date - today
        return delta.days
    except (TypeError, AttributeError):
        # Trata tipos invalidos de data sem quebrar o template
        return 0


@register.filter
def is_deadline_soon(date: Optional[date_type]) -> bool:
    """
    Retorna True se a data está nos próximos 7 dias (prazo próximo).
    
    Args:
        date: Objeto date ou None
        
    Returns:
        bool: True se o prazo estiver dentro de 7 dias
    """
    if not date:
        return False
    
    days = days_until(date)
    # days_until retorna 0 em caso invalido; mantem checagem por seguranca
    if days is None:
        return False
    return 0 <= days <= 7


@register.filter
def is_transparent_header(url_name: Optional[str]) -> bool:
    """
    Indica se o cabeçalho deve usar o tema transparente/gradiente.
    
    Args:
        url_name: Nome da URL ou None
        
    Returns:
        bool: True se o cabecalho deve ser transparente
    """
    if not url_name:
        return False
    return url_name in {'edital_detail', 'edital_detail_slug'}


@register.filter
def startswith(value: Optional[str], arg: str) -> bool:
    """
    Verifica se uma string comeca com o prefixo informado.
    
    Uso em templates:
        {% if current_url|startswith:'edital_' %}
    
    Args:
        value: String para verificar ou None
        arg: Prefixo a ser verificado
        
    Returns:
        bool: True se value comeca com arg
    """
    if not value:
        return False
    return str(value).startswith(str(arg))


@register.filter
def is_textarea_widget(widget) -> bool:
    """
    Verifica se o widget e do tipo Textarea.
    
    Uso em templates:
        {% if field.field.widget|is_textarea_widget %}
    
    Args:
        widget: Widget de formulario do Django
        
    Returns:
        bool: True se o widget for um Textarea
    """
    from django.forms import Textarea
    return isinstance(widget, Textarea)


@register.filter
def is_select_widget(widget) -> bool:
    """
    Verifica se o widget e um Select.
    
    Uso em templates:
        {% if field.field.widget|is_select_widget %}
    
    Args:
        widget: Widget de formulario do Django
        
    Returns:
        bool: True se o widget for Select ou SelectMultiple
    """
    from django.forms import Select, SelectMultiple
    return isinstance(widget, (Select, SelectMultiple))


@register.filter
def is_svg(file_field) -> bool:
    """
    Verifica se um FileField ou ImageField aponta para um SVG.
    
    Uso em templates:
        {% if startup.logo|is_svg %}
            <img src="{{ startup.logo.url }}" />
        {% else %}
            {% safe_thumbnail startup.logo "card_thumb" as thumb %}
        {% endif %}
    
    Args:
        file_field: Valor de FileField ou ImageField (FileFieldFile/ImageFieldFile)
        
    Returns:
        bool: True se o arquivo for SVG (por extensao)
    """
    if not file_field:
        return False
    
    # Extrai o nome do arquivo do campo (.name)
    filename = getattr(file_field, 'name', '')
    if not filename:
        return False
    
    # Verifica a extensao do arquivo
    import os
    ext = os.path.splitext(filename)[1].lower()
    return ext in ['.svg', '.svgz']


# Semantic token → Tailwind CSS mapping (single source of truth for badge styling)
PHASE_BADGE_CLASSES = {
    'pre_incubacao': 'bg-purple-100 text-purple-700 border-purple-200',
    'incubacao': 'bg-yellow-100 text-yellow-700 border-yellow-200',
    'graduada': 'bg-blue-100 text-blue-700 border-blue-200',
    'suspensa': 'bg-gray-100 text-gray-700 border-gray-200',
}
DEFAULT_PHASE_BADGE = 'bg-gray-100 text-gray-700 border-gray-200'

CATEGORY_BADGE_CLASSES = {
    'agtech': 'bg-green-100 text-green-700 border-green-200',
    'biotech': 'bg-blue-100 text-blue-700 border-blue-200',
    'iot': 'bg-purple-100 text-purple-700 border-purple-200',
    'edtech': 'bg-orange-100 text-orange-700 border-orange-200',
}
DEFAULT_CATEGORY_BADGE = 'bg-gray-100 text-gray-700 border-gray-200'


@register.filter
def phase_badge_class(status: Optional[str]) -> str:
    """
    Mapeia o status/fase da startup para classes de badge do Tailwind.
    Uso em templates: {{ startup.status|phase_badge_class }}
    """
    if not status:
        return DEFAULT_PHASE_BADGE
    return PHASE_BADGE_CLASSES.get(status, DEFAULT_PHASE_BADGE)


@register.filter
def category_badge_class(category: Optional[str]) -> str:
    """
    Mapeia a categoria da startup para classes de badge do Tailwind.
    Uso em templates: {{ startup.category|category_badge_class }}
    """
    if not category:
        return DEFAULT_CATEGORY_BADGE
    return CATEGORY_BADGE_CLASSES.get(category, DEFAULT_CATEGORY_BADGE)


@register.filter
def total_error_count(form) -> int:
    """
    Conta o total de erros do formulario (inclui multiplos erros por campo).
    
    Uso em templates:
        Há {{ form|total_error_count }} erro{{ form|total_error_count|pluralize }} no formulário
    
    Args:
        form: Instancia de formulario do Django
        
    Returns:
        int: Total de erros (erros de campo + erros globais)
    """
    if not form or not hasattr(form, 'errors'):
        return 0
    
    count = 0
    # Conta erros de campo
    for field in form:
        if field.errors:
            count += len(field.errors)
    # Conta erros globais do formulario
    if form.non_field_errors():
        count += len(form.non_field_errors())
    
    return count


@register.filter
def field_describedby(field) -> str:
    """
    Monta o valor de aria-describedby para um campo de formulario.

    Inclui ids de help text e de erro quando existirem.
    Retorna uma lista de ids separada por espaco.
    """
    if not field:
        return ""
    ids = []
    if getattr(field, "help_text", ""):
        ids.append(f"{field.auto_id}_helptext")
    if getattr(field, "errors", None):
        if field.errors:
            ids.append(f"{field.auto_id}_error")
    return " ".join(ids)