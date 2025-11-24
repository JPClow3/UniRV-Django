"""
Decorators customizados para o aplicativo Editais.
"""

import logging
from functools import wraps
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator

from .constants import RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """
    Get the real client IP address, handling proxies and load balancers.
    
    Checks X-Forwarded-For header first (common for proxies), then falls back
    to REMOTE_ADDR. Returns 'unknown' if neither is available.
    
    Args:
        request: Django HttpRequest object
        
    Returns:
        str: Client IP address
    """
    # Check X-Forwarded-For header (set by proxies/load balancers)
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # X-Forwarded-For can contain multiple IPs; the first is the client
        ip = x_forwarded_for.split(',')[0].strip()
        if ip:
            return ip
    
    # Fallback to REMOTE_ADDR
    return request.META.get('REMOTE_ADDR', 'unknown')


def rate_limit(key='ip', rate=RATE_LIMIT_REQUESTS, window=RATE_LIMIT_WINDOW, method='POST'):
    """
    Decorator para rate limiting usando cache do Django.
    
    Args:
        key: Chave para identificar o limite ('ip' ou 'user')
        rate: Número máximo de requisições permitidas
        window: Janela de tempo em segundos
        method: Método HTTP a ser limitado ('POST', 'GET', ou None para todos)
    
    Returns:
        Decorator function
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if getattr(settings, 'TESTING', False):
                return view_func(request, *args, **kwargs)
            # Aplicar rate limiting apenas para o método especificado
            if method and request.method != method:
                return view_func(request, *args, **kwargs)
            
            # Determinar a chave de cache baseada no tipo
            if key == 'ip':
                client_ip = get_client_ip(request)
                cache_key = f'rate_limit_ip_{client_ip}'
            elif key == 'user':
                if not request.user.is_authenticated:
                    return view_func(request, *args, **kwargs)
                cache_key = f'rate_limit_user_{request.user.id}'
            else:
                return view_func(request, *args, **kwargs)
            
            # Verificar contador atual
            current_count = cache.get(cache_key, 0)
            
            if current_count >= rate:
                logger.warning(
                    f"Rate limit excedido: {key}={cache_key}, "
                    f"count={current_count}, method={request.method}"
                )
                return HttpResponse(
                    'Muitas requisições. Por favor, tente novamente em alguns instantes.',
                    status=429
                )
            
            # Incrementar contador
            cache.set(cache_key, current_count + 1, window)
            
            # Chamar a view original
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator

