"""
Dashboard views for the editais app.

This module contains all dashboard views for authenticated users.
"""

import logging
from datetime import timedelta
from typing import Union
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import Q, Count, Avg
from django.http import HttpResponse, HttpRequest, HttpResponseRedirect
from django.shortcuts import redirect
from django.utils import timezone

from ..constants import (
    DEADLINE_WARNING_DAYS,
    EVALUATION_PROJECT_STATUSES,
    CACHE_TTL_5_MINUTES
)
from ..decorators import rate_limit, staff_required
from ..forms import EditalForm
from ..models import Edital, Project
from ..services import EditalService
from .public import build_search_query

logger = logging.getLogger(__name__)


@login_required
def dashboard_home(request: HttpRequest) -> HttpResponse:
    """Dashboard home page matching React DashboardHomePage"""
    from django.shortcuts import render
    
    # Calculate statistics for staff users
    context = {}
    if request.user.is_staff:
        context = {
            'total_usuarios': User.objects.count(),
            'editais_ativos': Edital.objects.filter(status='aberto').count(),
            'projetos_submetidos': Project.objects.count(),
            'avaliacoes_pendentes': Project.objects.filter(
                status__in=EVALUATION_PROJECT_STATUSES
            ).count(),
        }
    return render(request, 'dashboard/home.html', context)


@login_required
@staff_required
def dashboard_editais(request: HttpRequest) -> HttpResponse:
    """Dashboard editais management page"""
    from django.shortcuts import render
    
    try:
        search_query = request.GET.get('search', '')
        status_filter = request.GET.get('status', '')
        tipo_filter = request.GET.get('tipo', '')
        
        # Base queryset for stats calculation (before status filter to show all statuses)
        stats_base = Edital.objects.with_related()
        
        if search_query:
            stats_base = stats_base.filter(build_search_query(search_query))
        
        # Apply tipo filter to stats base as well (but not status filter)
        if tipo_filter:
            if tipo_filter == 'Fluxo Contínuo':
                stats_base = stats_base.filter(end_date__isnull=True)
            elif tipo_filter == 'Fomento':
                stats_base = stats_base.filter(end_date__isnull=False)
        
        # Calculate stats from base queryset (before status filtering)
        # This ensures stats show breakdown across all statuses
        stats = stats_base.aggregate(
            total_editais=Count('id'),
            publicados=Count('id', filter=Q(status='aberto')),
            rascunhos=Count('id', filter=Q(status='draft'))
        )
        
        # Calculate total submissions (projects) across all editais
        total_submissoes = Project.objects.count()
        
        # Now build the display queryset with all filters including status
        editais = Edital.objects.with_related().with_prefetch()
        
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
        
        context = {
            'editais': editais,
            'total_editais': stats['total_editais'],
            'publicados': stats['publicados'],
            'rascunhos': stats['rascunhos'],
            'total_submissoes': total_submissoes
        }
        
        return render(request, 'dashboard/editais.html', context)
    
    except Exception as e:
        logger.error(
            f"Erro ao carregar dashboard de editais - usuário: {request.user.username}, "
            f"erro: {str(e)}",
            exc_info=True
        )
        messages.error(request, 'Erro ao carregar editais. Tente novamente.')
        # Calculate total_submissoes even in error case for consistency
        try:
            total_submissoes = Project.objects.count()
        except Exception:
            total_submissoes = 0
        context = {
            'editais': Edital.objects.none(),
            'total_editais': 0,
            'publicados': 0,
            'rascunhos': 0,
            'total_submissoes': total_submissoes,
        }
        return render(request, 'dashboard/editais.html', context)


@login_required
def dashboard_projetos(request: HttpRequest) -> HttpResponse:
    """Dashboard projetos page - Public startup showcase"""
    from django.shortcuts import render
    from ..utils import get_project_status_mapping, get_project_sort_mapping
    
    try:
        # Get filter parameters
        search_query = request.GET.get('search', '').strip()
        edital_filter = request.GET.get('edital', '').strip()
        status_filter = request.GET.get('status', '').strip()
        sort_by = request.GET.get('sort', 'submitted_on_desc').strip()
        
        # Base queryset with optimized select_related
        # Note: edital is now optional, so we don't filter it out
        projects = Project.objects.select_related('edital', 'proponente').filter(
            proponente__isnull=False
        )
        
        # Apply search filter
        if search_query:
            projects = projects.filter(name__icontains=search_query)
        
        # Apply edital filter (optional - can filter by edital or show all)
        # Validate edital ID is a positive integer
        if edital_filter:
            try:
                edital_id = int(edital_filter)
                if edital_id > 0:
                    projects = projects.filter(edital_id=edital_id)
                else:
                    # Invalid edital ID, ignore filter
                    edital_filter = ''
            except (ValueError, TypeError):
                # Invalid edital ID format, ignore filter
                edital_filter = ''
        
        # Calculate stats from base queryset BEFORE applying status filter
        stats_base = projects
        stats = stats_base.aggregate(
            total=Count('id'),
            pre_incubacao=Count('id', filter=Q(status='pre_incubacao')),
            incubacao=Count('id', filter=Q(status='incubacao')),
            graduada=Count('id', filter=Q(status='graduada')),
            suspensa=Count('id', filter=Q(status='suspensa')),
        )
        
        # Apply status filter (map display names to model values)
        status_mapping = get_project_status_mapping()
        if status_filter:
            status_value = status_mapping.get(status_filter.lower(), status_filter.lower())
            projects = projects.filter(status=status_value)
        
        # Apply sorting
        sort_mapping = get_project_sort_mapping()
        sort_field = sort_mapping.get(sort_by, '-submitted_on')
        projects = projects.order_by(sort_field)
        
        # Get available editais for dropdown (all editais, ordered by most recent)
        available_editais = Edital.objects.all().order_by('-data_atualizacao')
        
        # Calculate graduation rate (startups that graduated)
        total_projects = stats['total'] or 0
        if total_projects > 0:
            graduadas = stats['graduada'] or 0
            graduation_rate = round((graduadas / total_projects) * 100)
            stats['graduation_rate'] = f"{graduation_rate}%"
        else:
            stats['graduation_rate'] = "0%"
        
        recent_update_cutoff = timezone.now() - timedelta(days=2)

        context = {
            'projects': projects,
            'search_query': search_query,
            'edital_filter': edital_filter,
            'status_filter': status_filter,
            'sort_by': sort_by,
            'stats': stats,
            'available_editais': available_editais,
            'recent_update_cutoff': recent_update_cutoff,
        }
        
        return render(request, 'dashboard/projetos.html', context)
    
    except Exception as e:
        logger.error(
            f"Erro ao carregar dashboard de projetos - usuário: {request.user.username}, "
            f"erro: {str(e)}",
            exc_info=True
        )
        messages.error(request, 'Erro ao carregar projetos. Tente novamente.')
        # Return empty context on error
        context = {
            'projects': [],
            'search_query': '',
            'edital_filter': '',
            'status_filter': '',
            'sort_by': 'submitted_on_desc',
            'stats': {
                'total': 0,
                'pre_incubacao': 0,
                'incubacao': 0,
                'graduada': 0,
                'suspensa': 0,
                'graduation_rate': '0%',
            },
            'available_editais': Edital.objects.none(),
            'recent_update_cutoff': timezone.now() - timedelta(days=2),
        }
        return render(request, 'dashboard/projetos.html', context)


@login_required
def dashboard_avaliacoes(request: HttpRequest) -> HttpResponse:
    """Dashboard avaliações page"""
    from django.shortcuts import render
    
    # Get startups that need evaluation (in pre-incubation or incubation)
    projects = Project.objects.select_related('edital', 'proponente').filter(
        status__in=EVALUATION_PROJECT_STATUSES
    ).order_by('-submitted_on')
    
    # Calculate statistics
    total = Project.objects.filter(status__in=EVALUATION_PROJECT_STATUSES).count()
    pre_incubacao = Project.objects.filter(status='pre_incubacao').count()
    em_incubacao = Project.objects.filter(status='incubacao').count()
    graduadas = Project.objects.filter(status='graduada').count()
    
    # Calculate average note (only for projects with notes)
    # Note: note is a DecimalField, so we only check for isnull, not empty string
    projetos_com_nota = Project.objects.exclude(note__isnull=True)
    nota_media = 0
    if projetos_com_nota.exists():
        nota_media = projetos_com_nota.aggregate(Avg('note'))['note__avg'] or 0
        nota_media = round(nota_media, 1)
    
    context = {
        'evaluations': projects,
        'total': total,
        'pre_incubacao': pre_incubacao,
        'em_incubacao': em_incubacao,
        'graduadas': graduadas,
        'nota_media': nota_media,
    }
    return render(request, 'dashboard/avaliacoes.html', context)


@login_required
@staff_required
def dashboard_usuarios(request: HttpRequest) -> HttpResponse:
    """Dashboard usuarios page"""
    from django.shortcuts import render
    
    # Get all users with related data
    users = User.objects.all().order_by('-date_joined')
    
    # Search functionality
    search_query = request.GET.get('search', '').strip()
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    context = {
        'users': users,
        'search_query': search_query,
    }
    return render(request, 'dashboard/usuarios.html', context)


@login_required
@staff_required
def dashboard_relatorios(request: HttpRequest) -> HttpResponse:
    """Dashboard relatorios page"""
    from django.shortcuts import render
    
    # Calculate statistics
    total_projetos = Project.objects.count()
    startups_incubacao = Project.objects.filter(status='incubacao').count()
    startups_graduadas = Project.objects.filter(status='graduada').count()
    
    # Calculate graduation rate, handling division by zero
    taxa_graduacao = 0
    if total_projetos > 0:
        taxa_graduacao = round((startups_graduadas / total_projetos) * 100)
    
    usuarios_ativos = User.objects.filter(projetos_submetidos__isnull=False).distinct().count()
    editais_ativos = Edital.objects.filter(status='aberto').count()
    
    context = {
        'total_projetos': total_projetos,
        'taxa_graduacao': taxa_graduacao,
        'startups_incubacao': startups_incubacao,
        'startups_graduadas': startups_graduadas,
        'usuarios_ativos': usuarios_ativos,
        'editais_ativos': editais_ativos,
    }
    
    return render(request, 'dashboard/relatorios.html', context)


@login_required
def dashboard_submeter_projeto(request: HttpRequest) -> HttpResponse:
    """Dashboard submeter projeto page - Add new startups to the incubator"""
    from django.shortcuts import render
    return render(request, 'dashboard/submeter_projeto.html')


@login_required
@staff_required
@rate_limit(key='ip', rate=5, window=60, method='POST')
def dashboard_novo_edital(request: HttpRequest) -> Union[HttpResponse, HttpResponseRedirect]:
    """
    Dashboard page para criar novo edital - Requer autenticação e is_staff.
    Usa o mesmo EditalForm que a rota /cadastrar/ para consistência (CLAR-021).
    
    Args:
        request: HttpRequest
        
    Returns:
        HttpResponse: Formulário de criação ou redirecionamento após sucesso
    """
    from django.shortcuts import render
    
    logger.info(
        f"dashboard_novo_edital iniciado - usuário: {request.user.username}, "
        f"IP: {request.META.get('REMOTE_ADDR')}"
    )
    
    try:
        if request.method == 'POST':
            form = EditalForm(request.POST)
            if form.is_valid():
                edital = EditalService.create_edital(form, request.user)
                
                logger.info(
                    f"edital criado via dashboard com sucesso - ID: {edital.pk}, "
                    f"título: {edital.titulo}, usuário: {request.user.username}"
                )
                
                messages.success(request, 'Edital cadastrado com sucesso!')
                # Redirect to dashboard editais list after creation
                return redirect('dashboard_editais')
        else:
            form = EditalForm()

        return render(request, 'dashboard/novo_edital.html', {'form': form})
    except Exception as e:
        logger.error(
            f"Erro ao criar edital via dashboard - usuário: {request.user.username}, "
            f"erro: {str(e)}",
            exc_info=True
        )
        messages.error(request, 'Erro ao cadastrar edital. Tente novamente.')
        form = EditalForm(request.POST if request.method == 'POST' else None)
        return render(request, 'dashboard/novo_edital.html', {'form': form})


@login_required
@staff_required
@rate_limit(key='ip', rate=10, window=60, method='GET')
def admin_dashboard(request: HttpRequest) -> HttpResponse:
    """
    Dashboard administrativo com estatísticas e gráficos.
    
    Args:
        request: HttpRequest
        
    Returns:
        HttpResponse: Página do dashboard
    """
    from django.shortcuts import render
    
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
            }, CACHE_TTL_5_MINUTES)
        
        # Cache recent editais query
        cache_key_recentes = 'admin_dashboard_recentes'
        editais_recentes = cache.get(cache_key_recentes)
        if not editais_recentes:
            editais_recentes = EditalService.get_recent_editais(days=7)[:10]
            cache.set(cache_key_recentes, editais_recentes, CACHE_TTL_5_MINUTES)
        
        # Cache deadline editais query
        cache_key_deadline = 'admin_dashboard_deadline'
        editais_proximos_prazo = cache.get(cache_key_deadline)
        if not editais_proximos_prazo:
            editais_proximos_prazo = EditalService.get_editais_by_deadline(
                days=DEADLINE_WARNING_DAYS
            )[:10]
            cache.set(cache_key_deadline, editais_proximos_prazo, CACHE_TTL_5_MINUTES)
        
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

