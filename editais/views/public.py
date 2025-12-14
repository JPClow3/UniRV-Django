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
from django_ratelimit.decorators import ratelimit

from ..constants import (
    CACHE_TTL_INDEX, PAGINATION_DEFAULT,
    ACTIVE_PROJECT_STATUSES, SECONDS_PER_DAY, CACHE_TTL_15_MINUTES,
    MAX_SEARCH_LENGTH, MAX_STARTUPS_DISPLAY
)
from ..models import Edital, Project
from ..utils import mark_edital_fields_safe, parse_date_filter, get_search_suggestions
from ..cache_utils import get_index_cache_key, get_detail_cache_key, get_cached_response, cache_response
from ..exceptions import EditalNotFoundError

logger = logging.getLogger(__name__)


def build_search_query(query: str) -> Q:
    """
    Build a Q object for searching editais by query string.
    
    This function is used by tests and provides a way to build search queries
    that match the behavior of the Edital.search() method.
    
    Args:
        query: Search query string (will be truncated if too long)
        
    Returns:
        Q: Django Q object for filtering editais
    """
    if not query:
        return Q()
    
    # Convert query to string if it's not already
    if not isinstance(query, str):
        query = str(query) if query is not None else ''
        if not query:
            return Q()
    
    # Truncate if too long
    if len(query) > MAX_SEARCH_LENGTH:
        query = query[:MAX_SEARCH_LENGTH]
    
    # Build Q object with icontains for searchable fields
    # Using the same fields as Edital.search() fallback
    from django.conf import settings
    search_fields = getattr(settings, 'EDITAL_SEARCH_FIELDS', [
        'titulo', 'entidade_principal', 'numero_edital'
    ])
    
    q_objects = Q()
    for field in search_fields:
        q_objects |= Q(**{f'{field}__icontains': query})
    
    return q_objects


def home(request: HttpRequest) -> HttpResponse:
    """Home page - landing page with hero, stats, features, etc."""
    # Fetch active startups for Innovation Deck
    # Use ACTIVE_PROJECT_STATUSES constant which includes pre_incubacao, incubacao, and graduada
    active_startups = Project.objects.filter(
        status__in=ACTIVE_PROJECT_STATUSES
    ).only(
        'id', 'name', 'logo', 'category', 'slug'
    ).order_by('-submitted_on')[:12]
    
    # Partners list - single source of truth for marquee
    PARTNERS = ['SENAI', 'SEBRAE', 'FAPEG', 'FINEP', 'UNIRV', 'INOVALAB']
    
    context = {
        'startups': active_startups,
        'partners': PARTNERS,
    }
    return render(request, 'home.html', context)


def ambientes_inovacao(request: HttpRequest) -> HttpResponse:
    """Ambientes de Inovação page - list of innovation environments"""
    return render(request, 'ambientes_inovacao.html')


def projetos_aprovados(request: HttpRequest) -> HttpResponse:
    """Projetos Aprovados page - list of approved projects"""
    return render(request, 'projetos_aprovados.html')


def startups_showcase(request: HttpRequest) -> HttpResponse:
    """Public startups showcase page - modern design with filters"""
    default_context = {
        'startups': Project.objects.none(),
        'category_filter': '',
        'search_query': '',
        'stats': {
            'total_active': 0,
        },
    }
    
    try:
        category_filter = request.GET.get('category', '').strip()
        search_query = request.GET.get('search', '').strip()
        
        base_queryset = Project.objects.select_related('edital', 'proponente').filter(
            proponente__isnull=False,
            status__in=ACTIVE_PROJECT_STATUSES
        ).only(
            'id', 'name', 'description', 'category', 'status', 'submitted_on',
            'edital__id', 'edital__titulo', 'edital__slug',
            'proponente__id', 'proponente__first_name', 'proponente__last_name'
        )
        
        if search_query:
            base_queryset = base_queryset.filter(
                Q(name__icontains=search_query) | Q(description__icontains=search_query)
            )
        
        try:
            # Calculate stats including graduated startups
            all_active_projects = Project.objects.filter(
                proponente__isnull=False,
                status__in=ACTIVE_PROJECT_STATUSES
            )
            graduadas_count = all_active_projects.filter(status='graduada').count()
            stats = {
                'total_active': base_queryset.count(),
                'graduadas': graduadas_count,
                'total_valuation': graduadas_count * 1,  # Placeholder calculation: graduadas * 1.0
            }
        except DatabaseError as stats_error:
            logger.warning(f"Error calculating stats, using defaults: {stats_error}")
            stats = {
                'total_active': 0,
                'graduadas': 0,
                'total_valuation': 0,
            }
        
        startups = base_queryset
        if category_filter and category_filter != 'all':
            startups = startups.filter(category=category_filter)
        
        startups = startups.order_by('-submitted_on')[:MAX_STARTUPS_DISPLAY]
        
        context = {
            'startups': startups,
            'category_filter': category_filter,
            'search_query': search_query,
            'stats': stats,
        }
        
        return render(request, 'startups.html', context)
    
    except DatabaseError as e:
        logger.error(
            f"Erro ao carregar showcase de startups - erro: {str(e)}",
            exc_info=True
        )
        return render(request, 'startups.html', default_context)


def _login_view_impl(request: HttpRequest) -> Union[HttpResponse, HttpResponseRedirect]:
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

# Apply rate limiting to login view (5 requests per minute per IP for POST requests)
login_view = ratelimit(key='ip', rate='5/m', method='POST')(_login_view_impl)


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
            login(request, user)
            
            logger.info(
                f"User registered successfully - username: {user.username}, "
                f"email: {user.email}, IP: {request.META.get('REMOTE_ADDR')}"
            )
            
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
        orgao_filter = request.GET.get('orgao', '')
        start_date_filter = request.GET.get('start_date', '')
        end_date_filter = request.GET.get('end_date', '')
        only_open = request.GET.get('only_open', '') == '1'
        page_number = request.GET.get('page', '1')
        
        try:
            page_number_int = int(page_number)
            if page_number_int < 1:
                page_number = '1'
        except ValueError:
            page_number = '1'
        
        if search_query and len(search_query) > MAX_SEARCH_LENGTH:
            search_query = search_query[:MAX_SEARCH_LENGTH]
            messages.warning(request, f'A busca foi truncada para {MAX_SEARCH_LENGTH} caracteres.')

        # Cache only for anonymous users without filters
        has_filters = search_query or status_filter or orgao_filter or start_date_filter or end_date_filter or only_open
        use_cache = not has_filters and not request.user.is_authenticated
        cache_ttl = getattr(settings, 'EDITAIS_CACHE_TTL', CACHE_TTL_INDEX)

        cache_key = None
        if use_cache:
            version_key = 'editais_index_cache_version'
            cache_version = cache.get(version_key, 0)
            cache_key = get_index_cache_key(page_number, cache_version)
            cached_response = get_cached_response(cache_key)
            if cached_response:
                return cached_response

        editais = Edital.objects.with_related().prefetch_related('valores').only(
            'id', 'numero_edital', 'titulo', 'url', 'entidade_principal',
            'status', 'start_date', 'end_date', 'objetivo', 
            'data_criacao', 'data_atualizacao', 'slug',
            'created_by', 'updated_by'
        )

        if not request.user.is_authenticated or not request.user.is_staff:
            editais = editais.active()

        if search_query:
            # Use model's search method which handles PostgreSQL full-text search or SQLite fallback
            editais = editais.search(search_query)

        if status_filter:
            editais = editais.filter(status=status_filter)
        elif only_open:
            editais = editais.filter(status='aberto')
        
        if orgao_filter:
            # Use exact match for better filter consistency with dropdown
            editais = editais.filter(entidade_principal=orgao_filter)

        start_date = parse_date_filter(start_date_filter)
        if start_date:
            editais = editais.filter(start_date__gte=start_date)

        end_date = parse_date_filter(end_date_filter)
        if end_date:
            editais = editais.filter(end_date__lte=end_date)

        per_page = getattr(settings, 'EDITAIS_PER_PAGE', PAGINATION_DEFAULT)
        paginator = Paginator(editais, per_page)
        page_obj = paginator.get_page(page_number)

        # Generate search suggestions if no results found and search query exists
        search_suggestions = []
        if page_obj.paginator.count == 0 and search_query:
            try:
                search_suggestions = get_search_suggestions(search_query, limit=3)
            except Exception as e:
                # Log but don't fail - suggestions are nice-to-have
                logger.warning(f"Error generating search suggestions: {e}", exc_info=True)

        # Get unique orgãos for filter dropdown (only from active editais for non-staff)
        base_queryset_for_orgaos = Edital.objects
        if not request.user.is_authenticated or not request.user.is_staff:
            base_queryset_for_orgaos = base_queryset_for_orgaos.active()
        
        unique_orgaos = base_queryset_for_orgaos.exclude(
            entidade_principal__isnull=True
        ).exclude(
            entidade_principal=''
        ).values_list('entidade_principal', flat=True).distinct().order_by('entidade_principal')
        
        context = {
            'page_obj': page_obj,
            'search_query': search_query,
            'status_filter': status_filter,
            'orgao_filter': orgao_filter,
            'start_date_filter': start_date_filter,
            'end_date_filter': end_date_filter,
            'only_open': only_open,
            'status_choices': Edital.STATUS_CHOICES,
            'unique_orgaos': unique_orgaos,
            'total_count': page_obj.paginator.count,
            'search_suggestions': search_suggestions,
        }
        
        # Check if this is an AJAX request - return partial HTML for better performance
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if is_ajax:
            # Return only the grid and pagination sections for AJAX requests
            template_name = 'editais/index_partial.html'
        else:
            # Return full page for normal requests
            template_name = 'editais/index.html'
        
        rendered_content = render_to_string(template_name, context, request=request)
        
        if use_cache and cache_key and not is_ajax:
            # Only cache full page responses, not partials
            cache_response(cache_key, rendered_content, cache_ttl)
        
        return HttpResponse(rendered_content)
    
    except (DatabaseError, EmptyPage, PageNotAnInteger) as e:
        logger.error(
            f"Erro ao carregar página de editais - IP: {request.META.get('REMOTE_ADDR')}, "
            f"erro: {str(e)}",
            exc_info=True
        )
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
            'orgao_filter': '',
            'start_date_filter': '',
            'end_date_filter': '',
            'only_open': False,
            'status_choices': Edital.STATUS_CHOICES,
            'unique_orgaos': [],
            'total_count': 0,
            'search_suggestions': [],
        }
        
        # Check if this is an AJAX request for error handling too
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if is_ajax:
            template_name = 'editais/index_partial.html'
        else:
            template_name = 'editais/index.html'
            messages.error(request, 'Erro ao carregar editais. Tente novamente.')
        
        return render(request, template_name, context)


def edital_detail(request: HttpRequest, slug: Optional[str] = None, pk: Optional[int] = None) -> HttpResponse:
    """
    Página de detalhes do edital - suporta slug ou PK.
    """
    identifier = slug if slug else f'pk_{pk}'
    cache_key = get_detail_cache_key('edital', identifier, request.user)
    
    cached_response = get_cached_response(cache_key)
    if cached_response:
        return cached_response
    
    try:
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
        
        if edital.status == 'draft':
            if not request.user.is_authenticated or not request.user.is_staff:
                raise Http404("Edital não encontrado")
        
        valores = edital.valores.all()
        cronogramas = edital.cronogramas.all()
        mark_edital_fields_safe(edital)

        is_recent_update = False
        if edital.data_atualizacao:
            time_diff = timezone.now() - edital.data_atualizacao
            # Check if update was within the last day
            is_recent_update = time_diff.total_seconds() < SECONDS_PER_DAY

        context = {
            'edital': edital,
            'valores': valores,
            'cronogramas': cronogramas,
            'is_recent_update': is_recent_update,
        }
        
        rendered_content = render_to_string('editais/detail.html', context, request=request)
        cache_response(cache_key, rendered_content, CACHE_TTL_15_MINUTES)
        return HttpResponse(rendered_content)
    except EditalNotFoundError as e:
        logger.warning(f"Edital não encontrado: {e.identifier}")
        raise Http404("Edital não encontrado")
    except Edital.DoesNotExist:
        raise Http404("Edital não encontrado")
    except Http404:
        raise
    except (DatabaseError, ValidationError) as e:
        logger.error(f"Erro inesperado em edital_detail: {e}", exc_info=True)
        raise Http404("Erro ao carregar edital")


def edital_detail_redirect(request: HttpRequest, pk: int) -> Union[HttpResponseRedirect, HttpResponse]:
    """
    Redireciona URLs baseadas em PK para URLs baseadas em slug.
    
    Redirecionamento permanente (301) para melhorar SEO e consistência de URLs.
    Se o slug não existir, exibe a página de detalhes usando PK.
    
    Args:
        request: HttpRequest
        pk: Primary key do edital
        
    Returns:
        HttpResponseRedirect: Redirecionamento permanente para URL com slug
        HttpResponse: Página de detalhes se slug não existir
    """
    edital = get_object_or_404(Edital, pk=pk)
    
    if edital.status == 'draft':
        if not request.user.is_authenticated or not request.user.is_staff:
            raise Http404("Edital não encontrado")
    
    if edital.slug:
        return redirect('edital_detail_slug', slug=edital.slug, permanent=True)
    # Fallback to PK-based view if slug is missing (None or empty string)
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
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
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
    except (DatabaseError, OSError, ConnectionError, Exception) as e:
        # Catch all exceptions including generic Exception for test scenarios
        logger.error(f"Health check falhou: {e}", exc_info=True)
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


def startup_detail(request: HttpRequest, slug: Optional[str] = None, pk: Optional[int] = None) -> HttpResponse:
    """
    Página de detalhes da startup - suporta slug ou PK.
    """
    identifier = slug if slug else f'pk_{pk}'
    cache_key = get_detail_cache_key('startup', identifier, request.user)
    
    cached_response = get_cached_response(cache_key)
    if cached_response:
        return cached_response
    
    try:
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
        
        rendered_content = render_to_string('startups/detail.html', context, request=request)
        cache_response(cache_key, rendered_content, CACHE_TTL_15_MINUTES)
        return HttpResponse(rendered_content)
    except Project.DoesNotExist:
        raise Http404("Startup não encontrada")
    except Http404:
        raise
    except (DatabaseError, ValidationError) as e:
        logger.error(f"Erro ao carregar startup: {e}", exc_info=True)
        raise Http404("Erro ao carregar startup")


def startup_detail_redirect(request: HttpRequest, pk: int) -> Union[HttpResponseRedirect, HttpResponse]:
    """
    Redireciona URLs baseadas em PK para URLs baseadas em slug.
    
    Redirecionamento permanente (301) para melhorar SEO e consistência de URLs.
    Se o slug não existir, exibe a página de detalhes usando PK.
    
    Args:
        request: HttpRequest
        pk: Primary key da startup
        
    Returns:
        HttpResponseRedirect: Redirecionamento permanente para URL com slug
        HttpResponse: Página de detalhes se slug não existir
    """
    startup = get_object_or_404(Project, pk=pk)
    
    if startup.slug:
        return redirect('startup_detail_slug', slug=startup.slug, permanent=True)
    # Fallback to PK-based view if slug is missing (None or empty string)
    return startup_detail(request, pk=pk)
