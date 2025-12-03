"""
Public views for the editais app.

This module contains all public-facing views that don't require authentication
or are accessible to all users.
"""

import logging
from typing import Optional, Union
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import connection, DatabaseError
from django.db.models import Q, Count
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponse, JsonResponse, HttpRequest, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils import timezone

from ..constants import (
    CACHE_TTL_INDEX, PAGINATION_DEFAULT,
    ACTIVE_PROJECT_STATUSES, SECONDS_PER_DAY, CACHE_TTL_15_MINUTES,
    MAX_SEARCH_LENGTH, MAX_STARTUPS_DISPLAY
)
from ..models import Edital, Project
from ..utils import mark_edital_fields_safe, parse_date_filter, apply_tipo_filter
from ..cache_utils import get_index_cache_key, get_detail_cache_key, get_user_cache_key
from ..exceptions import EditalNotFoundError

logger = logging.getLogger(__name__)


def build_search_query(search_query: str) -> Q:
    """
    Constrói um objeto Q para busca de texto completo em todos os campos de edital.
    
    Args:
        search_query: String de busca (será truncada se muito longa)
        
    Returns:
        Q: Objeto Q do Django para filtragem
    """
    if not search_query:
        return Q()
    
    # Validate and limit search query length to prevent DoS
    # This is a safety measure - the view also truncates, but defense in depth
    if len(search_query) > MAX_SEARCH_LENGTH:
        search_query = search_query[:MAX_SEARCH_LENGTH]

    q_objects = Q()
    search_fields = getattr(settings, 'EDITAL_SEARCH_FIELDS', [
        'titulo', 'entidade_principal', 'numero_edital'
    ])

    for field in search_fields:
        q_objects |= Q(**{f'{field}__icontains': search_query})

    return q_objects


def home(request: HttpRequest) -> HttpResponse:
    """
    Home page - landing page with hero, stats, features, etc.
    
    Note: Manual caching removed to avoid potential CSRF token caching issues.
    The home page is mostly static content, so caching is less critical.
    If caching is needed, use manual cache with render_to_string like other views.
    """
    return render(request, 'home.html')


def ambientes_inovacao(request: HttpRequest) -> HttpResponse:
    """Ambientes de Inovação page - list of innovation environments"""
    return render(request, 'ambientes_inovacao.html')


def projetos_aprovados(request: HttpRequest) -> HttpResponse:
    """Projetos Aprovados page - list of approved projects"""
    return render(request, 'projetos_aprovados.html')


def startups_showcase(request: HttpRequest) -> HttpResponse:
    """Public startups showcase page - modern design with filters
    
    Optimized for performance with query optimizations, field limiting, and timeout handling.
    """
    # Default context in case of any errors
    default_context = {
        'startups': Project.objects.none(),
        'category_filter': '',
        'search_query': '',
        'stats': {
            'total_active': 0,
            'graduadas': 0,
            'total_valuation': 0,
        },
    }
    
    try:
        # Get filter parameters
        category_filter = request.GET.get('category', '').strip()
        search_query = request.GET.get('search', '').strip()
        
        # Base queryset - optimized with select_related and only() to limit fields loaded
        # This reduces memory usage and speeds up queries significantly
        base_queryset = Project.objects.select_related('edital', 'proponente').filter(
            proponente__isnull=False,
            status__in=ACTIVE_PROJECT_STATUSES  # Exclude suspended
        ).only(
            'id', 'name', 'description', 'category', 'status', 'submitted_on',
            'edital__id', 'edital__titulo', 'edital__slug',
            'proponente__id', 'proponente__first_name', 'proponente__last_name'
        )
        
        # Apply search filter if provided
        if search_query:
            base_queryset = base_queryset.filter(
                Q(name__icontains=search_query) | Q(description__icontains=search_query)
            )
        
        # Calculate stats from base queryset BEFORE applying category filter
        # Use a more efficient count query - only count IDs, don't load full objects
        try:
            stats = base_queryset.aggregate(
                total_active=Count('id'),
                graduadas=Count('id', filter=Q(status='graduada')),
            )
        except (DatabaseError, ValueError, TypeError) as stats_error:
            logger.warning(f"Error calculating stats, using defaults: {stats_error}")
            stats = {'total_active': 0, 'graduadas': 0}
        
        # Apply category filter to display queryset
        startups = base_queryset
        if category_filter and category_filter != 'all':
            startups = startups.filter(category=category_filter)
        
        # Calculate total valuation (placeholder - can be enhanced later)
        total_valuation = (stats.get('graduadas') or 0) * 1.0  # Placeholder: 1M per graduated startup
        
        # Order by submission date (newest first) - already indexed in model
        # Limit results to prevent loading too many objects at once
        # Template can handle pagination if needed in the future
        startups = startups.order_by('-submitted_on')[:MAX_STARTUPS_DISPLAY]
        
        context = {
            'startups': startups,
            'category_filter': category_filter,
            'search_query': search_query,
            'stats': {
                'total_active': stats.get('total_active') or 0,
                'graduadas': stats.get('graduadas') or 0,
                'total_valuation': int(total_valuation),
            },
        }
        
        return render(request, 'startups.html', context)
    
    except (DatabaseError, ValueError, TypeError) as e:
        logger.error(
            f"Erro ao carregar showcase de startups - erro: {str(e)}",
            exc_info=True
        )
        # Return default empty context on any error to ensure page still renders
        return render(request, 'startups.html', default_context)


def login_view(request: HttpRequest) -> Union[HttpResponse, HttpResponseRedirect]:
    """Custom login page matching React design"""
    from django.contrib.auth import authenticate, login
    from django.contrib.auth.forms import AuthenticationForm
    
    if request.user.is_authenticated:
        return redirect('dashboard_home')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', '/dashboard/home/')
                return redirect(next_url)
    else:
        form = AuthenticationForm()
    
    return render(request, 'registration/login.html', {'form': form})


def register_view(request: HttpRequest) -> Union[HttpResponse, HttpResponseRedirect]:
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('dashboard_home')
    
    from ..forms import UserRegistrationForm
    from django.contrib.auth import login
    from django.core.mail import send_mail
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Log the user in automatically after registration
            login(request, user)
            
            # Log successful registration
            logger.info(
                f"User registered successfully - username: {user.username}, "
                f"email: {user.email}, IP: {request.META.get('REMOTE_ADDR')}"
            )
            
            # Send welcome email (optional, only if email is configured)
            try:
                if hasattr(settings, 'EMAIL_HOST') and settings.EMAIL_HOST:
                    send_mail(
                        subject='Bem-vindo ao AgroHub!',
                        message=f'Olá {user.first_name},\n\nBem-vindo ao sistema de gestão de editais do AgroHub UniRV!\n\nSua conta foi criada com sucesso.',
                        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@agrohub.unirv.edu.br'),
                        recipient_list=[user.email],
                        fail_silently=True,
                    )
            except (ConnectionError, OSError, ValueError) as e:
                logger.warning(f"Failed to send welcome email to {user.email}: {e}")
            
            messages.success(request, 'Conta criada com sucesso! Bem-vindo ao AgroHub!')
            return redirect('dashboard_home')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'registration/register.html', {'form': form})


def index(request: HttpRequest) -> HttpResponse:
    """Landing page com todos os editais"""
    try:
        search_query = request.GET.get('search', '')
        status_filter = request.GET.get('status', '')
        tipo_filter = request.GET.get('tipo', '')  # Novo filtro: Fluxo Contínuo ou Fomento
        start_date_filter = request.GET.get('start_date', '')
        end_date_filter = request.GET.get('end_date', '')
        only_open = request.GET.get('only_open', '') == '1'  # Checkbox "somente abertos"
        page_number = request.GET.get('page', '1')
        
        # Validate page number
        try:
            page_number_int = int(page_number)
            if page_number_int < 1:
                page_number = '1'
        except (ValueError, TypeError):
            page_number = '1'
        
        # Validate search query length (prevent DoS with very long queries)
        if search_query and len(search_query) > MAX_SEARCH_LENGTH:
            search_query = search_query[:MAX_SEARCH_LENGTH]
            messages.warning(request, f'A busca foi truncada para {MAX_SEARCH_LENGTH} caracteres.')

        # Build cache key based on query parameters
        # Only cache if no search or filter is applied (most common case)
        cache_key = None
        has_filters = search_query or status_filter or tipo_filter or start_date_filter or end_date_filter or only_open
        use_cache = not has_filters and not request.user.is_authenticated
        cache_ttl = getattr(settings, 'EDITAIS_CACHE_TTL', CACHE_TTL_INDEX)

        if use_cache:
            # Get current cache version to ensure we get the latest cached data
            version_key = 'editais_index_cache_version'
            cache_version = cache.get(version_key, 0)
            cache_key = get_index_cache_key(page_number, cache_version)
            # Try to get cached content (string, not HttpResponse object)
            cached_content = cache.get(cache_key)
            if cached_content:
                # Create a new HttpResponse for each request from cached content
                # This prevents issues with shared mutable state in HttpResponse objects
                return HttpResponse(cached_content)

        # Optimize queries with select_related and prefetch_related
        editais = Edital.objects.with_related().prefetch_related('valores').only(
            'id', 'numero_edital', 'titulo', 'url', 'entidade_principal',
            'status', 'start_date', 'end_date', 'objetivo', 
            'data_criacao', 'data_atualizacao', 'slug',
            'created_by', 'updated_by'
        )

        # Hide draft editais from non-authenticated users (FR-010)
        if not request.user.is_authenticated or not request.user.is_staff:
            editais = editais.active()

        # Apply full-text search across all fields
        if search_query:
            editais = editais.filter(build_search_query(search_query))

        # Apply status filter
        if status_filter:
            editais = editais.filter(status=status_filter)
        elif only_open:
            # Filter "somente abertos" - show only editais with status='aberto'
            editais = editais.filter(status='aberto')
        
        # Apply tipo filter (Fluxo Contínuo = sem end_date, Fomento = com end_date)
        editais = apply_tipo_filter(editais, tipo_filter)

        # Apply date filters
        start_date = parse_date_filter(start_date_filter)
        if start_date:
            editais = editais.filter(start_date__gte=start_date)

        end_date = parse_date_filter(end_date_filter)
        if end_date:
            editais = editais.filter(end_date__lte=end_date)

        # Use pagination constant
        per_page = getattr(settings, 'EDITAIS_PER_PAGE', PAGINATION_DEFAULT)
        paginator = Paginator(editais, per_page)
        page_obj = paginator.get_page(page_number)

        context = {
            'page_obj': page_obj,
            'search_query': search_query,
            'status_filter': status_filter,
            'tipo_filter': tipo_filter,
            'start_date_filter': start_date_filter,
            'end_date_filter': end_date_filter,
            'only_open': only_open,
            'status_choices': Edital.STATUS_CHOICES,
            'total_count': page_obj.paginator.count,  # Total count for results counter
        }
        
        # Render template to string instead of HttpResponse
        # This allows us to cache the content safely without caching mutable objects
        rendered_content = render_to_string('editais/index.html', context, request=request)
        
        # Cache the rendered content (string) instead of HttpResponse object
        # This prevents issues with shared mutable state and ensures each request
        # gets a fresh HttpResponse object with correct headers and middleware processing
        if use_cache and cache_key:
            cache.set(cache_key, rendered_content, cache_ttl)
        
        # Create and return a new HttpResponse for this request
        return HttpResponse(rendered_content)
    
    except (DatabaseError, ValueError, TypeError, EmptyPage, PageNotAnInteger) as e:
        logger.error(
            f"Erro ao carregar página de editais - IP: {request.META.get('REMOTE_ADDR')}, "
            f"erro: {str(e)}",
            exc_info=True
        )
        # Return empty results on error
        empty_queryset = Edital.objects.none()
        paginator = Paginator(empty_queryset, PAGINATION_DEFAULT)
        try:
            page_obj = paginator.page(1)
        except (EmptyPage, PageNotAnInteger):
            page_obj = paginator.page(1)
        
        context = {
            'page_obj': page_obj,
            'search_query': '',
            'status_filter': '',
            'tipo_filter': '',
            'start_date_filter': '',
            'end_date_filter': '',
            'only_open': False,
            'status_choices': Edital.STATUS_CHOICES,
            'total_count': 0,
        }
        messages.error(request, 'Erro ao carregar editais. Tente novamente.')
        return render(request, 'editais/index.html', context)


def edital_detail(request: HttpRequest, slug: Optional[str] = None, pk: Optional[int] = None) -> HttpResponse:
    """
    Página de detalhes do edital - suporta slug ou PK.
    
    Usa cache manual considerando status de autenticação para prevenir cache poisoning.
    Suporta slug ou PK para compatibilidade com URLs antigas.
    """
    # Build cache key that includes user authentication status
    # This prevents cache poisoning between authenticated/unauthenticated users
    # SECURITY: Distinguish three cases to prevent CSRF token leakage:
    # - staff: authenticated staff users (may have different permissions)
    # - auth: authenticated non-staff users (have CSRF tokens)
    # - public: unauthenticated users (no CSRF tokens)
    identifier = slug if slug else f'pk_{pk}'
    cache_key = get_detail_cache_key('edital', identifier, request.user)
    
    # Try to get cached content (string, not HttpResponse object)
    cached_content = cache.get(cache_key)
    if cached_content:
        # Create a new HttpResponse for each request from cached content
        # This prevents issues with shared mutable state in HttpResponse objects
        return HttpResponse(cached_content)
    
    try:
        # Optimize query with select_related and prefetch_related
        if slug:
            edital = get_object_or_404(
                Edital.objects.with_related().with_full_prefetch(),
                slug=slug
            )
        elif pk:
            edital = get_object_or_404(
                Edital.objects.with_related().with_full_prefetch(),
                pk=pk
            )
        else:
            raise Http404("Edital não encontrado")
        
        # FR-010: Hide draft editais from non-authenticated or non-staff users
        if edital.status == 'draft':
            if not request.user.is_authenticated or not request.user.is_staff:
                raise Http404("Edital não encontrado")
        
        valores = edital.valores.all()
        cronogramas = edital.cronogramas.all()

        # Sanitize and mark HTML fields as safe for rendering
        # This creates {field}_safe attributes with sanitized HTML marked as safe.
        # Original fields remain unchanged so Django can auto-escape them if needed.
        mark_edital_fields_safe(edital)

        # Calculate if edital was recently updated (within last 24 hours)
        is_recent_update = False
        if edital.data_atualizacao:
            time_diff = timezone.now() - edital.data_atualizacao
            # Handle negative time differences (future dates)
            if time_diff.total_seconds() >= 0:
                # Consider recent if updated within last 24 hours
                is_recent_update = time_diff.total_seconds() < SECONDS_PER_DAY

        context = {
            'edital': edital,
            'valores': valores,
            'cronogramas': cronogramas,
            'is_recent_update': is_recent_update,
        }
        
        # Render template to string instead of HttpResponse
        # This allows us to cache the content safely without caching mutable objects
        rendered_content = render_to_string('editais/detail.html', context, request=request)
        
        # Cache the rendered content (string) instead of HttpResponse object
        # This prevents issues with shared mutable state and ensures each request
        # gets a fresh HttpResponse object with correct headers and middleware processing
        # Cache for 15 minutes
        cache.set(cache_key, rendered_content, CACHE_TTL_15_MINUTES)
        
        # Create and return a new HttpResponse for this request
        return HttpResponse(rendered_content)
    except EditalNotFoundError as e:
        # Converter exceção customizada para Http404
        logger.warning(f"Edital não encontrado: {e.identifier}")
        raise Http404("Edital não encontrado")
    except Edital.DoesNotExist:
        raise Http404("Edital não encontrado")
    except Http404:
        # Re-raise Http404 sem modificação
        raise
    except (DatabaseError, ValidationError, ValueError) as e:
        logger.error(f"Erro inesperado em edital_detail: {e}", exc_info=True)
        raise Http404("Erro ao carregar edital")


def edital_detail_redirect(request: HttpRequest, pk: int) -> HttpResponseRedirect:
    """
    Redireciona URLs baseadas em PK para URLs baseadas em slug.
    
    Redirecionamento permanente (301) para melhorar SEO e consistência de URLs.
    
    Args:
        request: HttpRequest
        pk: Primary key do edital
        
    Returns:
        HttpResponse: Redirecionamento permanente para URL com slug
    """
    edital = get_object_or_404(Edital, pk=pk)
    
    # FR-010: Hide draft editais from non-authenticated or non-staff users
    # Check before redirecting to prevent information leakage via redirect URL
    if edital.status == 'draft':
        if not request.user.is_authenticated or not request.user.is_staff:
            raise Http404("Edital não encontrado")
    
    if edital.slug:
        return redirect('edital_detail_slug', slug=edital.slug, permanent=True)
    # Fallback: if no slug, call detail view directly with PK
    # This handles edge case where slug generation failed or was None
    # Note: edital_detail accepts both slug and pk parameters
    return edital_detail(request, pk=pk)


def health_check(request: HttpRequest) -> JsonResponse:
    """
    Endpoint de health check para monitoramento.
    
    Verifica o status do banco de dados e cache.
    
    Args:
        request: HttpRequest
        
    Returns:
        JsonResponse: Status do sistema
    """
    try:
        # Verificar banco de dados
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Verificar cache
        test_key = 'health_check_test'
        cache.set(test_key, 'ok', 10)
        cache_status = cache.get(test_key) == 'ok'
        cache.delete(test_key)
        
        return JsonResponse({
            'status': 'healthy',
            'database': 'ok',
            'cache': 'ok' if cache_status else 'error',
            'timestamp': timezone.now().isoformat()
        })
    except (DatabaseError, OSError, ConnectionError) as e:
        logger.error(f"Health check falhou: {e}", exc_info=True)
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


def startup_detail(request: HttpRequest, slug: Optional[str] = None, pk: Optional[int] = None) -> HttpResponse:
    """
    Página de detalhes da startup - suporta slug ou PK.
    
    Similar ao edital_detail, mas para o modelo Project (startup).
    """
    # Build cache key that includes user authentication status
    identifier = slug if slug else f'pk_{pk}'
    cache_key = get_detail_cache_key('startup', identifier, request.user)
    
    # Try to get cached content (string, not HttpResponse object)
    cached_content = cache.get(cache_key)
    if cached_content:
        return HttpResponse(cached_content)
    
    try:
        # Optimize query with select_related
        if slug:
            startup = get_object_or_404(
                Project.objects.select_related('proponente', 'edital'),
                slug=slug
            )
        elif pk:
            startup = get_object_or_404(
                Project.objects.select_related('proponente', 'edital'),
                pk=pk
            )
        else:
            raise Http404("Startup não encontrada")
        
        context = {
            'startup': startup,
        }
        
        # Render template to string for caching
        rendered_content = render_to_string('startups/detail.html', context, request=request)
        
        # Cache the rendered content (string) for 15 minutes
        cache.set(cache_key, rendered_content, CACHE_TTL_15_MINUTES)
        
        # Create and return a new HttpResponse for this request
        return HttpResponse(rendered_content)
    except Project.DoesNotExist:
        raise Http404("Startup não encontrada")
    except Http404:
        # Re-raise Http404 without modification
        raise
    except (DatabaseError, ValidationError) as e:
        logger.error(f"Erro ao carregar startup: {e}", exc_info=True)
        raise Http404("Erro ao carregar startup")


def startup_detail_redirect(request: HttpRequest, pk: int) -> HttpResponseRedirect:
    """
    Redireciona URLs baseadas em PK para URLs baseadas em slug.
    
    Redirecionamento permanente (301) para melhorar SEO e consistência de URLs.
    
    Args:
        request: HttpRequest
        pk: Primary key da startup
        
    Returns:
        HttpResponse: Redirecionamento permanente para URL com slug
    """
    startup = get_object_or_404(Project, pk=pk)
    
    if startup.slug:
        return redirect('startup_detail_slug', slug=startup.slug, permanent=True)
    # Fallback: if no slug, use detail view with PK
    return startup_detail(request, pk=pk)
