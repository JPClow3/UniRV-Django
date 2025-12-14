"""
Safe thumbnail template tags that handle missing easy-thumbnails gracefully.
"""
from django import template

register = template.Library()

try:
    from easy_thumbnails.files import get_thumbnailer
    from easy_thumbnails.alias import aliases
    HAS_THUMBNAILS = True
except ImportError:
    HAS_THUMBNAILS = False


class SafeThumbnailNode(template.Node):
    def __init__(self, source_expr, alias_expr, var_name):
        self.source_expr = source_expr
        self.alias_expr = alias_expr
        self.var_name = var_name
    
    def render(self, context):
        try:
            source = self.source_expr.resolve(context)
            alias = self.alias_expr.resolve(context)
        except template.VariableDoesNotExist:
            context[self.var_name] = None
            return ''
        
        if not HAS_THUMBNAILS or not source:
            context[self.var_name] = None
            return ''
        
        try:
            # Get thumbnailer for the source image
            thumbnailer = get_thumbnailer(source)
            
            # Get alias options
            if alias in aliases.all():
                options = aliases.get(alias, target=None)
            else:
                # If alias doesn't exist, return None
                context[self.var_name] = None
                return ''
            
            # Generate thumbnail
            thumb = thumbnailer.get_thumbnail(options)
            context[self.var_name] = thumb
            return ''
        except Exception:
            # If thumbnail generation fails, return None
            context[self.var_name] = None
            return ''


@register.tag(name='safe_thumbnail')
def do_safe_thumbnail(parser, token):
    """
    Safely generate thumbnail, falling back to original image if thumbnails unavailable.
    
    Usage:
        {% safe_thumbnail startup.logo "detail_thumb" as thumb %}
        {% if thumb %}
            <img src="{{ thumb.url }}" />
        {% else %}
            <img src="{{ startup.logo.url }}" />
        {% endif %}
    """
    try:
        # Split the tag contents
        tag_name, source_expr, alias_expr, as_keyword, var_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            f"{token.contents.split()[0]} tag requires exactly 4 arguments: "
            "source, alias, 'as', and variable name"
        )
    
    if as_keyword != 'as':
        raise template.TemplateSyntaxError(
            f"{token.contents.split()[0]} tag's third argument must be 'as'"
        )
    
    return SafeThumbnailNode(
        parser.compile_filter(source_expr),
        parser.compile_filter(alias_expr),
        var_name
    )

