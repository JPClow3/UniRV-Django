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
            # Try to add the key with value 1 if it doesn't exist (atomic operation)
            # This handles the first request in the window
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
            
            if key_added:
                # Key was added (first request in window), allow request
                pass
            else:
                # Key already exists, try to increment atomically
                try:
                    # Try atomic increment (works with Redis, LocMemCache, etc.)
                    current_count = cache.incr(cache_key)
                    if current_count > rate:
                        logger.warning(
                            f"Rate limit excedido: {key}={cache_key}, "
                            f"count={current_count}, method={request.method}"
                        )
                        return HttpResponse(
                            'Muitas requisições. Por favor, tente novamente em alguns instantes.',
                            status=429
                        )
                except Exception as e:
                    # Fallback if incr() fails for any reason:
                    # - Not supported by cache backend (ValueError, AttributeError)
                    # - Cache backend unavailable (connection errors, timeouts)
                    # - Any other cache-related exception
                    logger.warning(
                        f"Cache error in rate_limit (cache.incr): {type(e).__name__}: {e}. "
                        f"Falling back to get/set. key={cache_key}"
                    )
                    try:
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
                        # Increment with potential race condition (fallback only)
                        cache.set(cache_key, current_count + 1, window)
                    except Exception as fallback_error:
                        # If fallback also fails, log and allow request (fail open)
                        logger.error(
                            f"Cache error in rate_limit fallback (cache.get/set): "
                            f"{type(fallback_error).__name__}: {fallback_error}. "
                            f"Allowing request to proceed. key={cache_key}"
                        )
                        return view_func(request, *args, **kwargs)
            
            # Chamar a view original
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator

