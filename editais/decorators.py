"""
Decorators customizados para o aplicativo Editais.
"""

import logging
from typing import Callable, Any, Optional
from functools import wraps
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, HttpRequest
from django.shortcuts import render

from .constants import RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW

logger = logging.getLogger(__name__)


def _track_rate_limit_bypass(key: str, cache_key: str, client_ip: str, user_id: Any) -> None:
    """
    Track rate limit bypass events for monitoring.
    
    Stores metrics in cache with daily aggregation. This helps identify:
    - Cache reliability issues
    - Potential abuse patterns
    - System health metrics
    
    Args:
        key: Rate limit key type ('ip' or 'user')
        cache_key: The cache key that failed
        client_ip: Client IP address (if applicable)
        user_id: User ID (if applicable)
    """
    from datetime import date
    try:
        # Create daily metric key
        today = date.today().isoformat()
        metric_key = f'rate_limit_bypass_count_{key}_{today}'
        
        # Increment counter (atomic operation if supported)
        try:
            cache.incr(metric_key)
        except (ValueError, AttributeError, TypeError):
            # Key doesn't exist or incr not supported, initialize it
            cache.set(metric_key, 1, timeout=86400 * 2)  # Keep for 2 days
        
        # Also track per-identifier bypasses (for abuse detection)
        if key == 'ip' and client_ip != 'N/A':
            ip_metric_key = f'rate_limit_bypass_ip_{client_ip}_{today}'
            try:
                cache.incr(ip_metric_key)
            except (ValueError, AttributeError, TypeError):
                cache.set(ip_metric_key, 1, timeout=86400 * 2)
        elif key == 'user' and user_id != 'N/A':
            user_metric_key = f'rate_limit_bypass_user_{user_id}_{today}'
            try:
                cache.incr(user_metric_key)
            except (ValueError, AttributeError, TypeError):
                cache.set(user_metric_key, 1, timeout=86400 * 2)
    except Exception as e:
        # Don't let metrics tracking break rate limiting
        logger.debug(f"Failed to track rate limit bypass metrics: {e}")


def staff_required(view_func: Callable) -> Callable:
    """
    Decorator que verifica se o usuário é staff.
    Retorna 403 se o usuário não for staff.
    
    Args:
        view_func: Função da view a ser decorada
        
    Returns:
        Função decorada que verifica permissão de staff
    """
    @wraps(view_func)
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
        if not request.user.is_staff:
            logger.warning(
                f"Unauthorized staff access attempt - user: {request.user.username}, "
                f"IP: {request.META.get('REMOTE_ADDR')}, view: {view_func.__name__}"
            )
            return render(request, '403.html', {'message': 'Acesso negado'}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


def get_client_ip(request: HttpRequest) -> str:
    """
    Get the real client IP address, handling proxies and load balancers securely.
    
    SECURITY: Only trusts X-Forwarded-For header if behind a trusted proxy.
    Validates IP format to prevent spoofing attacks.
    
    Args:
        request: Django HttpRequest object
        
    Returns:
        str: Client IP address (validated) or 'unknown' if invalid
    """
    from django.core.exceptions import ValidationError
    from django.core.validators import validate_ipv46_address
    
    def is_valid_ip(ip: str) -> bool:
        """Validate IP address format using Django's validator."""
        if not ip:
            return False
        try:
            validate_ipv46_address(ip.strip())
            return True
        except ValidationError:
            return False
    
    # Primary source: REMOTE_ADDR (most reliable, can't be spoofed)
    remote_addr = request.META.get('REMOTE_ADDR', '').strip()
    
    # Only trust X-Forwarded-For if we're behind a trusted proxy
    # Check if USE_X_FORWARDED_HOST is set (indicates trusted proxy)
    trust_proxy = getattr(settings, 'USE_X_FORWARDED_HOST', False) or getattr(settings, 'SECURE_PROXY_SSL_HEADER', None) is not None
    
    if trust_proxy:
        # Behind trusted proxy: check X-Forwarded-For header
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '').strip()
        if x_forwarded_for:
            # X-Forwarded-For can contain multiple IPs; the first is the client
            ip = x_forwarded_for.split(',')[0].strip()
            if is_valid_ip(ip):
                return ip
            else:
                logger.warning(f"Invalid IP in X-Forwarded-For header: {ip}")
    
    # Fallback to REMOTE_ADDR (always use if valid)
    if remote_addr and is_valid_ip(remote_addr):
        return remote_addr
    
    # If both sources are invalid, return 'unknown'
    logger.warning(f"Could not determine valid client IP. REMOTE_ADDR={remote_addr}")
    return 'unknown'


def rate_limit(key: str = 'ip', rate: int = RATE_LIMIT_REQUESTS, window: int = RATE_LIMIT_WINDOW, method: Optional[str] = 'POST') -> Callable[[Callable], Callable]:
    """
    Decorator para rate limiting usando cache do Django.
    
    DESIGN DECISION - Fail-Open Behavior:
    When cache is unavailable (connection errors, timeouts), this decorator allows
    requests to proceed rather than blocking them. This ensures service availability
    during cache outages. Rate limiting is a protective measure, not a critical
    security control, so fail-open behavior is intentional.
    
    RACE CONDITIONS:
    Cache operations (add, incr) may have race conditions, but these are acceptable
    for rate limiting. The worst case is slightly inaccurate rate counting, which
    does not compromise security or functionality.
    
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
            # NOTE: Cache race conditions are acceptable - worst case is slightly inaccurate counting
            try:
                key_added = cache.add(cache_key, 1, window)
            except (ConnectionError, OSError, AttributeError, TypeError) as e:
                # Cache backend unavailable (connection error, timeout, etc.)
                # DESIGN DECISION: Fail-open behavior - allow request to proceed for availability
                # Log error with structured context for monitoring
                client_ip = get_client_ip(request) if key == 'ip' else 'N/A'
                user_id = request.user.id if key == 'user' and request.user.is_authenticated else 'N/A'
                logger.warning(
                    "Rate limit bypass due to cache error - cache.add failed",
                    extra={
                        'cache_key': cache_key,
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'client_ip': client_ip,
                        'user_id': user_id,
                        'request_path': request.path,
                        'request_method': request.method,
                    }
                )
                # Track bypass metrics for monitoring
                _track_rate_limit_bypass(key, cache_key, client_ip, user_id)
                return view_func(request, *args, **kwargs)
            
            if not key_added:
                try:
                    current_count = cache.incr(cache_key)
                except (ConnectionError, OSError, AttributeError, TypeError) as e:
                    # DESIGN DECISION: Fail-open behavior - allow request to proceed
                    client_ip = get_client_ip(request) if key == 'ip' else 'N/A'
                    user_id = request.user.id if key == 'user' and request.user.is_authenticated else 'N/A'
                    logger.warning(
                        "Rate limit bypass due to cache error - cache.incr failed",
                        extra={
                            'cache_key': cache_key,
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'client_ip': client_ip,
                            'user_id': user_id,
                            'request_path': request.path,
                            'request_method': request.method,
                        }
                    )
                    # Track bypass metrics for monitoring
                    _track_rate_limit_bypass(key, cache_key, client_ip, user_id)
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

