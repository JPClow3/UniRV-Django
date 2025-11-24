import csv
import logging

import bleach
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db import connection
from django.db.models import Q
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views.decorators.cache import cache_page

from .constants import (
    CACHE_TTL_INDEX, PAGINATION_DEFAULT, DEADLINE_WARNING_DAYS
)
from .decorators import rate_limit
from .exceptions import EditalNotFoundError, EditalPermissionError
from .forms import EditalForm
from .models import Edital
from .services import EditalService

logger = logging.getLogger(__name__)

# Allowed tags and attributes for HTML sanitization
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'blockquote', 'a', 'code', 'pre', 'table',
    'thead', 'tbody', 'tr', 'th', 'td', 'div', 'span'
]
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target', 'rel'],
    'div': ['class', 'id'],
    'span': ['class'],
    'table': ['class'],
    'th': ['scope'],
    'abbr': ['title'],
    'acronym': ['title']
}


def sanitize_html(text):
    """
    Sanitiza conteúdo HTML para prevenir ataques XSS.
    
    Args:
        text: Texto a ser sanitizado
        
    Returns:
        str: Texto sanitizado ou string vazia em caso de erro
    """
    if not text:
        return text
    # Ensure text is a string
    if not isinstance(text, str):
        text = str(text)
    try:
        cleaned = bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)
        return cleaned
    except Exception as e:
        logger.error(f"Erro ao sanitizar HTML: {e}")
        # If sanitization fails, return empty string to prevent XSS
        return ''


def sanitize_edital_fields(edital):
    """
    Sanitiza todos os campos de texto de uma instância de edital.
    
    Args:
        edital: Instância do modelo Edital
        
    Returns:
        Edital: Instância sanitizada
    """
    fields = [
        'analise', 'objetivo', 'etapas', 'recursos',
        'itens_financiaveis', 'criterios_elegibilidade',
        'criterios_avaliacao', 'itens_essenciais_observacoes',
        'detalhes_unirv'
    ]
    for field in fields:
        value = getattr(edital, field, None)
        if value:
            setattr(edital, field, sanitize_html(value))
    return edital


def mark_edital_fields_safe(edital):
    """
    Marca campos HTML sanitizados como seguros para renderização em templates.
    
    Args:
        edital: Instância do modelo Edital
        
    Returns:
        Edital: Instância com campos marcados como seguros
    """
    fields = [
        'analise', 'objetivo', 'etapas', 'recursos',
        'itens_financiaveis', 'criterios_elegibilidade',
        'criterios_avaliacao', 'itens_essenciais_observacoes',
        'detalhes_unirv'
    ]
    for field in fields:
        value = getattr(edital, field, None)
        if value:
            setattr(edital, f'{field}_safe', mark_safe(value))
    return edital


def build_search_query(search_query):
    """
    Constrói um objeto Q para busca de texto completo em todos os campos de edital.
    
    Args:
        search_query: String de busca
        
    Returns:
        Q: Objeto Q do Django para filtragem
    """
    if not search_query:
        return Q()

    q_objects = Q()
    search_fields = getattr(settings, 'EDITAL_SEARCH_FIELDS', [
        'titulo', 'entidade_principal', 'numero_edital'
    ])

    for field in search_fields:
        q_objects |= Q(**{f'{field}__icontains': search_query})

    return q_objects


def _clear_index_cache():
    """
    Helper function to clear all index page cache keys.
    Uses a cache versioning pattern: increment a version number that's part of all cache keys.
    This invalidates all cached pages regardless of page number.
    """
    # Get current cache version (defaults to 0 if not set)
    version_key = 'editais_index_cache_version'
    current_version = cache.get(version_key, 0)
    
    # Increment version to invalidate all existing cached pages
    new_version = current_version + 1
    cache.set(version_key, new_version, timeout=None)  # Never expire the version key
    
    # Also clear the old version key pattern for pages 1-10 as a fallback
    # (in case any old cache entries exist without versioning)
    # Note: This is a fallback mechanism. The versioning system above should handle most cases.
    for page_num in range(1, 11):
        old_cache_key = f'editais_index_page_{page_num}'
        cache.delete(old_cache_key)


@cache_page(60 * 5)  # Cache for 5 minutes
def home(request):
    """Home page - landing page with hero, stats, features, etc."""
    return render(request, 'home.html')


def ambientes_inovacao(request):
    """Ambientes de Inovação page - list of innovation environments"""
    return render(request, 'ambientes_inovacao.html')


def projetos_aprovados(request):
    """Projetos Aprovados page - list of approved projects"""
    return render(request, 'projetos_aprovados.html')


def login_view(request):
    """Custom login page matching React design"""
    from django.contrib.auth import authenticate, login
    from django.contrib.auth.forms import AuthenticationForm
    from django.shortcuts import redirect
    
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


def register_view(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('dashboard_home')
    
    from .forms import UserRegistrationForm
    from django.contrib.auth import login
    from django.core.mail import send_mail
    from django.conf import settings
    
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
            except Exception as e:
                logger.warning(f"Failed to send welcome email to {user.email}: {e}")
            
            messages.success(request, 'Conta criada com sucesso! Bem-vindo ao AgroHub!')
            return redirect('dashboard_home')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'registration/register.html', {'form': form})


# Dashboard Views
@login_required
def dashboard_home(request):
    """Dashboard home page matching React DashboardHomePage"""
    return render(request, 'dashboard/home.html')


@login_required
def dashboard_editais(request):
    """Dashboard editais management page"""
    if not request.user.is_staff:
        return render(request, '403.html', {'message': 'Acesso negado'}, status=403)
    
    from django.db.models import Count, Q
    
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    tipo_filter = request.GET.get('tipo', '')
    
    # Optimize queries with select_related and prefetch_related
    editais = Edital.objects.select_related(
        'created_by', 'updated_by'
    ).prefetch_related('valores', 'cronogramas')
    
    if search_query:
        editais = editais.filter(build_search_query(search_query))
    
    if status_filter:
        editais = editais.filter(status=status_filter)
    
    if tipo_filter:
        if tipo_filter == 'Fluxo Contínuo':
            editais = editais.filter(end_date__isnull=True)
        elif tipo_filter == 'Fomento':
            editais = editais.filter(end_date__isnull=False)
    
    editais = editais.order_by('-data_criacao')
    
    # Optimize stats queries using annotations (single query instead of multiple)
    stats = Edital.objects.aggregate(
        total_editais=Count('id'),
        publicados=Count('id', filter=Q(status='aberto')),
        rascunhos=Count('id', filter=Q(status='draft'))
    )
    
    context = {
        'editais': editais,
        'total_editais': stats['total_editais'],
        'publicados': stats['publicados'],
        'rascunhos': stats['rascunhos'],
        'total_submissoes': 0  # Placeholder
    }
    
    return render(request, 'dashboard/editais.html', context)


@login_required
def dashboard_projetos(request):
    """Dashboard projetos page"""
    projects_data = [
        {
            'id': 1,
            'name': 'AgroTech Solutions',
            'edital_id': '1',
            'edital_label': 'Edital 001/2024',
            'proponente': 'João Silva',
            'submitted_on': '15/02/2024',
            'status': 'Em Avaliação',
            'note': None,
        },
        {
            'id': 2,
            'name': 'EduPlay',
            'edital_id': '2',
            'edital_label': 'Edital 002/2024',
            'proponente': 'Maria Santos',
            'submitted_on': '20/01/2024',
            'status': 'Aprovado',
            'note': '8.5',
        },
        {
            'id': 3,
            'name': 'GreenFarm',
            'edital_id': '3',
            'edital_label': 'Edital 003/2024',
            'proponente': 'Lucas Pereira',
            'submitted_on': '05/03/2024',
            'status': 'Pendente',
            'note': None,
        },
        {
            'id': 4,
            'name': 'LogiSmart',
            'edital_id': '1',
            'edital_label': 'Edital 001/2024',
            'proponente': 'Ana Oliveira',
            'submitted_on': '28/02/2024',
            'status': 'Reprovado',
            'note': '6.2',
        },
    ]

    search_query = request.GET.get('search', '').strip().lower()
    edital_filter = request.GET.get('edital', '').strip()
    status_filter = request.GET.get('status', '').strip().lower()

    def matches(project):
        if search_query and search_query not in project['name'].lower():
            return False
        if edital_filter and edital_filter != project['edital_id']:
            return False
        if status_filter and status_filter != project['status'].lower():
            return False
        return True

    filtered_projects = [project for project in projects_data if matches(project)]

    stats = {
        'total': len(projects_data),
        'em_avaliacao': sum(1 for p in projects_data if p['status'] == 'Em Avaliação'),
        'aprovados': sum(1 for p in projects_data if p['status'] == 'Aprovado'),
        'approval_rate': f"{round((sum(1 for p in projects_data if p['status'] == 'Aprovado') / max(len(projects_data), 1)) * 100)}%",
    }

    context = {
        'projects': filtered_projects,
        'search_query': request.GET.get('search', '').strip(),
        'edital_filter': edital_filter,
        'status_filter': request.GET.get('status', '').strip(),
        'stats': stats,
    }

    return render(request, 'dashboard/projetos.html', context)


@login_required
def dashboard_avaliacoes(request):
    """Dashboard avaliações page"""
    return render(request, 'dashboard/avaliacoes.html')


@login_required
def dashboard_usuarios(request):
    """Dashboard usuarios page"""
    if not request.user.is_staff:
        # Log unauthorized access attempt
        security_logger = logging.getLogger('django.security')
        security_logger.warning(
            f"Unauthorized dashboard access attempt - user: {request.user.username}, "
            f"IP: {request.META.get('REMOTE_ADDR')}, view: dashboard_usuarios"
        )
        return render(request, '403.html', {'message': 'Acesso negado'}, status=403)
    return render(request, 'dashboard/usuarios.html')


@login_required
def dashboard_relatorios(request):
    """Dashboard relatorios page"""
    if not request.user.is_staff:
        return render(request, '403.html', {'message': 'Acesso negado'}, status=403)
    return render(request, 'dashboard/relatorios.html')


@login_required
def dashboard_novo_edital(request):
    """Dashboard novo edital page"""
    if not request.user.is_staff:
        return render(request, '403.html', {'message': 'Acesso negado'}, status=403)
    return render(request, 'dashboard/novo_edital.html')


@login_required
def dashboard_submeter_projeto(request):
    """Dashboard submeter projeto page"""
    return render(request, 'dashboard/submeter_projeto.html')


# Note: Manual caching is implemented below, @cache_page decorator removed to avoid conflicts
def index(request):
    """Landing page com todos os editais"""
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    tipo_filter = request.GET.get('tipo', '')  # Novo filtro: Fluxo Contínuo ou Fomento
    start_date_filter = request.GET.get('start_date', '')
    end_date_filter = request.GET.get('end_date', '')
    only_open = request.GET.get('only_open', '') == '1'  # Checkbox "somente abertos"
    page_number = request.GET.get('page', '1')

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
        cache_key = f'editais_index_page_{page_number}_v{cache_version}'
        # Try to get cached content (string, not HttpResponse object)
        cached_content = cache.get(cache_key)
        if cached_content:
            # Create a new HttpResponse for each request from cached content
            # This prevents issues with shared mutable state in HttpResponse objects
            return HttpResponse(cached_content)

    # Optimize queries with select_related and prefetch_related
    editais = Edital.objects.select_related(
        'created_by', 'updated_by'
    ).prefetch_related('valores').only(
        'id', 'numero_edital', 'titulo', 'url', 'entidade_principal',
        'status', 'start_date', 'end_date', 'objetivo', 
        'data_criacao', 'data_atualizacao', 'slug',
        'created_by', 'updated_by'
    )

    # Hide draft editais from non-authenticated users (FR-010)
    if not request.user.is_authenticated or not request.user.is_staff:
        editais = editais.exclude(status='draft')

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
    if tipo_filter:
        if tipo_filter == 'Fluxo Contínuo':
            editais = editais.filter(end_date__isnull=True)
        elif tipo_filter == 'Fomento':
            editais = editais.filter(end_date__isnull=False)

    # Apply date filters
    if start_date_filter:
        try:
            from datetime import datetime
            start_date = datetime.strptime(start_date_filter, '%Y-%m-%d').date()
            editais = editais.filter(start_date__gte=start_date)
        except (ValueError, TypeError):
            # Invalid date format, ignore filter
            pass

    if end_date_filter:
        try:
            from datetime import datetime
            end_date = datetime.strptime(end_date_filter, '%Y-%m-%d').date()
            editais = editais.filter(end_date__lte=end_date)
        except (ValueError, TypeError):
            # Invalid date format, ignore filter
            pass

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


def edital_detail(request, slug=None, pk=None):
    """
    Página de detalhes do edital - suporta slug ou PK.
    
    SECURITY NOTE: This view uses manual caching that considers user authentication
    status to prevent cache poisoning. The @cache_page decorator was removed because
    it caches based only on URL, which would allow unauthorized users to cache 404
    responses that staff users would then see.
    
    Args:
        request: HttpRequest
        slug: Slug do edital (opcional)
        pk: Primary key do edital (opcional)
        
    Returns:
        HttpResponse: Página de detalhes do edital
        
    Raises:
        Http404: Se o edital não for encontrado ou não tiver permissão
    """
    # Build cache key that includes user authentication status
    # This prevents cache poisoning between authenticated/unauthenticated users
    # SECURITY: Distinguish three cases to prevent CSRF token leakage:
    # - staff: authenticated staff users (may have different permissions)
    # - auth: authenticated non-staff users (have CSRF tokens)
    # - public: unauthenticated users (no CSRF tokens)
    if request.user.is_authenticated:
        if request.user.is_staff:
            user_key = 'staff'
        else:
            user_key = 'auth'  # Authenticated non-staff
    else:
        user_key = 'public'  # Unauthenticated
    
    # Use slug if available, otherwise use pk
    identifier = slug if slug else f'pk_{pk}'
    cache_key = f'edital_detail_{identifier}_{user_key}'
    
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
                Edital.objects.select_related('created_by', 'updated_by')
                .prefetch_related('valores', 'cronogramas', 'history'),
                slug=slug
            )
        elif pk:
            edital = get_object_or_404(
                Edital.objects.select_related('created_by', 'updated_by')
                .prefetch_related('valores', 'cronogramas', 'history'),
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

        # IMPORTANT: Sanitize HTML fields before marking as safe to prevent XSS
        # This ensures any unsanitized HTML in the database is cleaned before rendering
        sanitize_edital_fields(edital)
        # Mark sanitized HTML as safe for rendering using helper function
        mark_edital_fields_safe(edital)

        context = {
            'edital': edital,
            'valores': valores,
            'cronogramas': cronogramas,
        }
        
        # Render template to string instead of HttpResponse
        # This allows us to cache the content safely without caching mutable objects
        rendered_content = render_to_string('editais/detail.html', context, request=request)
        
        # Cache the rendered content (string) instead of HttpResponse object
        # This prevents issues with shared mutable state and ensures each request
        # gets a fresh HttpResponse object with correct headers and middleware processing
        # Cache for 15 minutes (900 seconds)
        cache.set(cache_key, rendered_content, 60 * 15)
        
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
    except Exception as e:
        logger.error(f"Erro inesperado em edital_detail: {e}", exc_info=True)
        raise Http404("Erro ao carregar edital")


def edital_detail_redirect(request, pk):
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
            from django.http import Http404
            raise Http404("Edital não encontrado")
    
    if edital.slug:
        return redirect('edital_detail_slug', slug=edital.slug, permanent=True)
    # Fallback: if no slug, use detail view with PK
    return edital_detail(request, pk=pk)


@login_required
@rate_limit(key='ip', rate=5, window=60, method='POST')
def edital_create(request):
    """
    Página para cadastrar novo edital - Requer autenticação e is_staff.
    
    Args:
        request: HttpRequest
        
    Returns:
        HttpResponse: Formulário de criação ou redirecionamento após sucesso
        
    Raises:
        EditalPermissionError: Se o usuário não tiver permissão
    """
    if not request.user.is_staff:
        return render(request, '403.html', {
            'message': 'Apenas usuários staff podem criar editais.'
        }, status=403)
    
    logger.info(
        f"edital_create iniciado - usuário: {request.user.username}, "
        f"IP: {request.META.get('REMOTE_ADDR')}"
    )
    
    try:
        if request.method == 'POST':
            form = EditalForm(request.POST)
            if form.is_valid():
                edital = form.save(commit=False)
                # Track who created this edital
                edital.created_by = request.user
                edital.updated_by = request.user
                # Sanitize all text fields using helper function
                sanitize_edital_fields(edital)
                edital.save()
                
                # Create history entry
                from .models import EditalHistory
                EditalHistory.objects.create(
                    edital=edital,
                    edital_titulo=edital.titulo,
                    user=request.user,
                    action='create',
                    changes_summary={'titulo': edital.titulo}
                )
                
                # Invalidate cache for index pages (clear all index cache keys)
                _clear_index_cache()
                
                logger.info(
                    f"edital criado com sucesso - ID: {edital.pk}, "
                    f"título: {edital.titulo}, usuário: {request.user.username}"
                )
                
                messages.success(request, 'Edital cadastrado com sucesso!')
                return redirect(edital.get_absolute_url())
        else:
            form = EditalForm()

        return render(request, 'editais/create.html', {'form': form})
    except Exception as e:
        logger.error(
            f"Erro ao criar edital - usuário: {request.user.username}, "
            f"erro: {str(e)}",
            exc_info=True
        )
        messages.error(request, 'Erro ao cadastrar edital. Tente novamente.')
        form = EditalForm(request.POST if request.method == 'POST' else None)
        return render(request, 'editais/create.html', {'form': form})


@login_required
@rate_limit(key='ip', rate=5, window=60, method='POST')
def edital_update(request, pk):
    """
    Página para editar edital - Requer autenticação e is_staff.
    
    Args:
        request: HttpRequest
        pk: Primary key do edital
        
    Returns:
        HttpResponse: Formulário de edição ou redirecionamento após sucesso
        
    Raises:
        EditalPermissionError: Se o usuário não tiver permissão
        EditalNotFoundError: Se o edital não for encontrado
    """
    if not request.user.is_staff:
        return render(request, '403.html', {
            'message': 'Apenas usuários staff podem editar editais.'
        }, status=403)
    
    edital = get_object_or_404(Edital, pk=pk)
    
    logger.info(
        f"edital_update iniciado - edital_id: {pk}, "
        f"usuário: {request.user.username}, IP: {request.META.get('REMOTE_ADDR')}"
    )

    if request.method == 'POST':
        form = EditalForm(request.POST, instance=edital)
        if form.is_valid():
            # IMPORTANT: Capture original values BEFORE save(commit=False)
            # After save(commit=False), form.instance will have new values
            from .models import EditalHistory
            # Refresh from DB to get original values (handle edge case where object might be deleted)
            try:
                # Use select_related to avoid N+1 queries if accessing related fields
                original_edital = Edital.objects.select_related('created_by', 'updated_by').get(pk=edital.pk)  # Fresh DB query
            except Edital.DoesNotExist:
                # Edge case: object was deleted between get_object_or_404 and here
                messages.error(request, 'O edital não foi encontrado.')
                return redirect('editais_index')
            
            # Track changes by comparing original DB values with new form values
            changes = {}
            for field in form.changed_data:
                if field not in ['data_atualizacao', 'updated_by']:
                    # Get original value from database (before form.save)
                    old_value = str(getattr(original_edital, field, ''))
                    # Get new value from form cleaned_data
                    new_value = str(form.cleaned_data.get(field, ''))
                    if old_value != new_value:
                        changes[field] = {'old': old_value[:200], 'new': new_value[:200]}
            
            # Now save the form (this updates form.instance with new values)
            edital = form.save(commit=False)
            edital.updated_by = request.user
            # Sanitize all text fields using helper function
            sanitize_edital_fields(edital)
            edital.save()
            
            # Create history entry
            if changes:
                EditalHistory.objects.create(
                    edital=edital,
                    edital_titulo=edital.titulo,
                    user=request.user,
                    action='update',
                    changes_summary=changes
                )
            
            # Invalidate cache for index pages (clear all index cache keys)
            _clear_index_cache()
            
            logger.info(
                f"edital atualizado com sucesso - ID: {edital.pk}, "
                f"título: {edital.titulo}, usuário: {request.user.username}, "
                f"campos alterados: {list(changes.keys())}"
            )
            
            messages.success(request, 'Edital atualizado com sucesso!')
            return redirect(edital.get_absolute_url())
    else:
        form = EditalForm(instance=edital)

    try:
        return render(request, 'editais/update.html', {'form': form, 'edital': edital})
    except Exception as e:
        logger.error(
            f"Erro ao renderizar formulário de edição - edital_id: {pk}, "
            f"erro: {str(e)}",
            exc_info=True
        )
        messages.error(request, 'Erro ao carregar formulário. Tente novamente.')
        return redirect('editais_index')


@login_required
@rate_limit(key='ip', rate=5, window=60, method='POST')
def edital_delete(request, pk):
    """
    Deletar edital - Requer autenticação e is_staff.
    
    Args:
        request: HttpRequest
        pk: Primary key do edital
        
    Returns:
        HttpResponse: Página de confirmação ou redirecionamento após exclusão
        
    Raises:
        EditalPermissionError: Se o usuário não tiver permissão
        EditalNotFoundError: Se o edital não for encontrado
    """
    if not request.user.is_staff:
        return render(request, '403.html', {
            'message': 'Apenas usuários staff podem deletar editais.'
        }, status=403)
    
    edital = get_object_or_404(Edital, pk=pk)
    
    logger.info(
        f"edital_delete iniciado - edital_id: {pk}, "
        f"usuário: {request.user.username}, IP: {request.META.get('REMOTE_ADDR')}"
    )

    if request.method == 'POST':
        try:
            # Create history entry before deletion (preserve title)
            from .models import EditalHistory
            EditalHistory.objects.create(
                edital=edital,
                edital_titulo=edital.titulo,  # Preserve title before deletion
                user=request.user,
                action='delete',
                changes_summary={'titulo': edital.titulo}
            )
            
            titulo_edital = edital.titulo
            edital.delete()
            
            # Invalidate cache for index pages (clear all index cache keys)
            _clear_index_cache()
            
            logger.info(
                f"edital deletado com sucesso - ID: {pk}, "
                f"título: {titulo_edital}, usuário: {request.user.username}"
            )
            
            messages.success(request, 'Edital excluído com sucesso!')
            return redirect('editais_index')
        except Exception as e:
            logger.error(
                f"Erro ao deletar edital - edital_id: {pk}, "
                f"erro: {str(e)}",
                exc_info=True
            )
            messages.error(request, 'Erro ao excluir edital. Tente novamente.')
            return redirect('editais_index')

    return render(request, 'editais/delete.html', {'edital': edital})


@login_required
def export_editais_csv(request):
    """
    Exporta editais para arquivo CSV.
    
    Requer autenticação e permissão de staff.
    Suporta filtros de busca e status via parâmetros GET.
    
    Args:
        request: HttpRequest com parâmetros opcionais:
            - search: Termo de busca
            - status: Filtro por status
            
    Returns:
        HttpResponse: Arquivo CSV para download
    """
    if not request.user.is_staff:
        return render(request, '403.html', {
            'message': 'Apenas usuários staff podem exportar editais.'
        }, status=403)
    
    # Get filtered editais (same filters as index page)
    # Optimize query with select_related for foreign keys
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    editais = Edital.objects.select_related('created_by', 'updated_by').all()
    
    # Note: Staff users can export draft editais (intentional for admin purposes)
    # Non-staff users are already blocked by the is_staff check above

    if search_query:
        editais = editais.filter(build_search_query(search_query))

    if status_filter:
        editais = editais.filter(status=status_filter)

    # Create CSV response
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="editais.csv"'
    response.write('\ufeff')  # UTF-8 BOM for Excel compatibility

    writer = csv.writer(response)

    # Write header
    writer.writerow([
        'Número',
        'Título',
        'Entidade',
        'Status',
        'URL',
        'Data Criação',
        'Data Atualização',
        'Criado Por',
        'Atualizado Por'
    ])

    # Write data - use iterator() for better memory efficiency with large datasets
    for edital in editais.iterator(chunk_size=1000):
        writer.writerow([
            edital.numero_edital or '',
            edital.titulo,
            edital.entidade_principal or '',
            edital.get_status_display(),
            edital.url,
            edital.data_criacao.strftime('%d/%m/%Y %H:%M') if edital.data_criacao else '',
            edital.data_atualizacao.strftime('%d/%m/%Y %H:%M') if edital.data_atualizacao else '',
            edital.created_by.username if edital.created_by else '',
            edital.updated_by.username if edital.updated_by else '',
        ])

    return response


@login_required
@rate_limit(key='ip', rate=10, window=60, method='GET')
def admin_dashboard(request):
    """
    Dashboard administrativo com estatísticas e gráficos.
    
    Args:
        request: HttpRequest
        
    Returns:
        HttpResponse: Página do dashboard
        
    Raises:
        EditalPermissionError: Se o usuário não tiver permissão
    """
    if not request.user.is_staff:
        return render(request, '403.html', {
            'message': 'Apenas usuários staff podem acessar o dashboard.'
        }, status=403)
    
    from django.db.models import Count, Q
    
    try:
        # Cache expensive stats queries
        cache_key_stats = 'admin_dashboard_stats'
        cached_stats = cache.get(cache_key_stats)
        
        if cached_stats:
            total_editais = cached_stats['total_editais']
            editais_por_status = cached_stats['editais_por_status']
        else:
            # Estatísticas gerais - optimized with single query
            total_editais = Edital.objects.count()
            editais_por_status = list(Edital.objects.values('status').annotate(
                count=Count('id')
            ).order_by('status'))
            # Cache for 5 minutes
            cache.set(cache_key_stats, {
                'total_editais': total_editais,
                'editais_por_status': editais_por_status
            }, 300)
        
        # Cache recent editais query
        cache_key_recentes = 'admin_dashboard_recentes'
        editais_recentes = cache.get(cache_key_recentes)
        if not editais_recentes:
            editais_recentes = EditalService.get_recent_editais(days=7)[:10]
            cache.set(cache_key_recentes, editais_recentes, 300)
        
        # Cache deadline editais query
        cache_key_deadline = 'admin_dashboard_deadline'
        editais_proximos_prazo = cache.get(cache_key_deadline)
        if not editais_proximos_prazo:
            editais_proximos_prazo = EditalService.get_editais_by_deadline(
                days=DEADLINE_WARNING_DAYS
            )[:10]
            cache.set(cache_key_deadline, editais_proximos_prazo, 300)
        
        # Atividades recentes usando serviço
        atividades_recentes = EditalService.get_recent_activities(days=7)[:15]
        
        # Estatísticas por entidade
        top_entidades = Edital.objects.exclude(
            entidade_principal__isnull=True
        ).exclude(
            entidade_principal=''
        ).values('entidade_principal').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        context = {
            'total_editais': total_editais,
            'editais_por_status': editais_por_status,
            'editais_recentes': editais_recentes,
            'editais_proximos_prazo': editais_proximos_prazo,
            'atividades_recentes': atividades_recentes,
            'top_entidades': top_entidades,
        }
        
        return render(request, 'editais/dashboard.html', context)
    except Exception as e:
        logger.error(
            f"Erro ao carregar dashboard - usuário: {request.user.username}, "
            f"erro: {str(e)}",
            exc_info=True
        )
        messages.error(request, 'Erro ao carregar dashboard. Tente novamente.')
        return redirect('editais_index')


def health_check(request):
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
    except Exception as e:
        logger.error(f"Health check falhou: {e}", exc_info=True)
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)
