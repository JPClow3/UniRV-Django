"""
Template tags for generating responsive image srcsets with CDN support.

Supports both static files and CDN URLs for optimal image delivery.
"""

from django import template
from django.conf import settings
from django.templatetags.static import static

register = template.Library()


def get_cdn_base_url():
    """Get CDN base URL from settings, or None if not configured."""
    return getattr(settings, 'CDN_BASE_URL', None)


def get_image_formats():
    """Get preferred image formats from settings."""
    return getattr(settings, 'CDN_IMAGE_FORMATS', ['avif', 'webp', 'jpg'])


@register.simple_tag
def hero_srcset(image_name, *widths, format='webp'):
    """
    Generate a srcset string for hero images with CDN or static file support.
    
    Args:
        image_name: Base name of the image (e.g., 'hero' for 'agrohub-hero')
        *widths: Variable number of widths (e.g., 480, 768, 1024, 1600, 2400)
        format: Image format ('avif', 'webp', 'jpg')
    
    Returns:
        str: Complete srcset string ready for use in <source> or <img> tags
    
    Example:
        {% hero_srcset "hero" 480 768 1024 1600 2400 "avif" %}
    """
    cdn_base = get_cdn_base_url()
    srcset_parts = []
    
    for width in widths:
        if cdn_base:
            # CDN URL pattern: {cdn_base}/hero/{image_name}-{width}w.{format}
            url = f"{cdn_base.rstrip('/')}/img/hero/{image_name}-{width}w.{format}"
        else:
            # Static file URL
            static_path = f"img/hero/{image_name}-{width}w.{format}"
            url = static(static_path)
        
        srcset_parts.append(f"{url} {width}w")
    
    return ", ".join(srcset_parts)


@register.simple_tag
def hero_image_url(image_name, width=1024, format='jpg'):
    """
    Generate a single hero image URL with CDN or static file support.
    
    Args:
        image_name: Base name of the image (e.g., 'hero' for 'agrohub-hero')
        width: Image width (default: 1024)
        format: Image format ('avif', 'webp', 'jpg')
    
    Returns:
        str: Complete image URL
    
    Example:
        {% hero_image_url "hero" 1024 "jpg" %}
    """
    cdn_base = get_cdn_base_url()
    
    if cdn_base:
        url = f"{cdn_base.rstrip('/')}/img/hero/{image_name}-{width}w.{format}"
    else:
        static_path = f"img/hero/{image_name}-{width}w.{format}"
        url = static(static_path)
    
    return url


@register.simple_tag
def hero_lqip_url(image_name='hero'):
    """
    Generate LQIP (Low Quality Image Placeholder) URL.
    
    Args:
        image_name: Base name of the image (default: 'hero')
    
    Returns:
        str: LQIP image URL
    
    Example:
        {% hero_lqip_url "hero" %}
    """
    cdn_base = get_cdn_base_url()
    
    if cdn_base:
        url = f"{cdn_base.rstrip('/')}/img/hero/{image_name}-lqip.jpg"
    else:
        static_path = f"img/hero/{image_name}-lqip.jpg"
        url = static(static_path)
    
    return url

