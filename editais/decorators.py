"""
Decorators customizados para o aplicativo Editais.
"""

import logging
from typing import Callable, Any, Optional
from functools import wraps
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, HttpRequest

from .constants import RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW

logger = logging.getLogger(__name__)


def get_client_ip(request: HttpRequest) -> str:
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


def rate_limit(key: str = 'ip', rate: int = RATE_LIMIT_REQUESTS, window: int = RATE_LIMIT_WINDOW, method: Optional[str] = 'POST') -> Callable[[Callable], Callable]:
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
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
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
            
            # Use atomic operations to prevent race conditions
            try:
                key_added = cache.add(cache_key, 1, window)
            except Exception as e:
                # Cache backend unavailable (connection error, timeout, etc.)
                # Log error but allow request to proceed (fail open)
                logger.error(
                    f"Cache error in rate_limit (cache.add): {type(e).__name__}: {e}. "
                    f"Allowing request to proceed. key={cache_key}"
                )
                return view_func(request, *args, **kwargs)
            
            if not key_added:
                try:
                    current_count = cache.incr(cache_key)
                except Exception as e:
                    logger.error(
                        f"Cache error in rate_limit (cache.incr): {type(e).__name__}: {e}. "
                        f"Rate limiting disabled for key={cache_key} in this window."
                    )
                    return view_func(request, *args, **kwargs)

                if current_count > rate:
                    logger.warning(
                        f"Rate limit excedido: {key}={cache_key}, "
                        f"count={current_count}, method={request.method}"
                    )
                    return HttpResponse(
                        'Muitas requisições. Por favor, tente novamente em alguns instantes.',
                        status=429
                    )
            
            # Chamar a view original
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator

