from django import template
try:
    import markdown2
except Exception:  # pragma: no cover
    markdown2 = None

register = template.Library()

@register.filter()
def markdown(value: str) -> str:
    """Render Markdown to safe HTML using markdown2 (if installed), else plain text.
    Use in templates: {{ text|markdown|safe }}
    """
    if not value:
        return ""
    if markdown2 is None:
        return value
    return markdown2.markdown(value, extras=["fenced-code-blocks", "tables", "strike", "smarty"])  # type: ignore

