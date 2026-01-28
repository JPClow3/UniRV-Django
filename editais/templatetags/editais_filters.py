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
    Returns None if date is None to allow template filters to handle missing dates properly.
    
    Args:
        date: Date object or None
        
    Returns:
        Optional[int]: Number of days until the date (negative if in the past), or None if date is None
    """
    if not date:
        return None
    
    from django.utils import timezone
    today = timezone.now().date()
    try:
        delta = date - today
        return delta.days
    except (TypeError, AttributeError):
        # Handle invalid date types gracefully
        return 0


@register.filter
def is_deadline_soon(date: Optional[date_type]) -> bool:
    """
    Retorna True se a data está nos próximos 7 dias (prazo próximo).
    
    Args:
        date: Date object or None
        
    Returns:
        bool: True if deadline is within 7 days
    """
    if not date:
        return False
    
    days = days_until(date)
    # days_until now returns 0 instead of None, but keep check for safety
    if days is None:
        return False
    return 0 <= days <= 7


@register.filter
def is_transparent_header(url_name: Optional[str]) -> bool:
    """
    Indica se o cabeçalho deve usar o tema transparente/gradiente.
    
    Args:
        url_name: URL name or None
        
    Returns:
        bool: True if header should be transparent
    """
    if not url_name:
        return False
    return url_name in {'edital_detail', 'edital_detail_slug'}


@register.filter
def startswith(value: Optional[str], arg: str) -> bool:
    """
    Check if a string starts with the given prefix.
    
    Usage in templates:
        {% if current_url|startswith:'edital_' %}
    
    Args:
        value: String to check or None
        arg: Prefix to check for
        
    Returns:
        bool: True if value starts with arg
    """
    if not value:
        return False
    return str(value).startswith(str(arg))


@register.filter
def is_textarea_widget(widget) -> bool:
    """
    Check if a widget is a Textarea widget.
    
    Usage in templates:
        {% if field.field.widget|is_textarea_widget %}
    
    Args:
        widget: Django form widget
        
    Returns:
        bool: True if widget is a Textarea
    """
    from django.forms import Textarea
    return isinstance(widget, Textarea)


@register.filter
def is_select_widget(widget) -> bool:
    """
    Check if a widget is a Select widget.
    
    Usage in templates:
        {% if field.field.widget|is_select_widget %}
    
    Args:
        widget: Django form widget
        
    Returns:
        bool: True if widget is a Select or SelectMultiple
    """
    from django.forms import Select, SelectMultiple
    return isinstance(widget, (Select, SelectMultiple))


@register.filter
def is_svg(file_field) -> bool:
    """
    Check if a FileField or ImageField value is an SVG file.
    
    Usage in templates:
        {% if startup.logo|is_svg %}
            <img src="{{ startup.logo.url }}" />
        {% else %}
            {% safe_thumbnail startup.logo "card_thumb" as thumb %}
        {% endif %}
    
    Args:
        file_field: FileField or ImageField value (FileFieldFile/ImageFieldFile instance)
        
    Returns:
        bool: True if the file is an SVG file (by extension)
    """
    if not file_field:
        return False
    
    # Get the filename from the field
    # FileField and ImageField both have a .name attribute
    filename = getattr(file_field, 'name', '')
    if not filename:
        return False
    
    # Check file extension
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
    Map startup phase/status to Tailwind badge classes.
    Use in templates: {{ startup.status|phase_badge_class }}
    """
    if not status:
        return DEFAULT_PHASE_BADGE
    return PHASE_BADGE_CLASSES.get(status, DEFAULT_PHASE_BADGE)


@register.filter
def category_badge_class(category: Optional[str]) -> str:
    """
    Map startup category to Tailwind badge classes.
    Use in templates: {{ startup.category|category_badge_class }}
    """
    if not category:
        return DEFAULT_CATEGORY_BADGE
    return CATEGORY_BADGE_CLASSES.get(category, DEFAULT_CATEGORY_BADGE)


@register.filter
def total_error_count(form) -> int:
    """
    Count the total number of errors in a form (including multiple errors per field).
    
    Usage in templates:
        Há {{ form|total_error_count }} erro{{ form|total_error_count|pluralize }} no formulário
    
    Args:
        form: Django form instance
        
    Returns:
        int: Total number of errors (field errors + non-field errors)
    """
    if not form or not hasattr(form, 'errors'):
        return 0
    
    count = 0
    # Count field errors
    for field in form:
        if field.errors:
            count += len(field.errors)
    # Count non-field errors
    if form.non_field_errors():
        count += len(form.non_field_errors())
    
    return count