"""
Dashboard views for the editais app.

This module contains all dashboard views for authenticated users.
"""

import logging
from datetime import timedelta
from typing import Union
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import DatabaseError
from django.db.models import Q, Count, Avg
from django.http import HttpResponse, HttpRequest, HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone

from ..constants import (
    DEADLINE_WARNING_DAYS,
    CACHE_TTL_5_MINUTES
)
from ..decorators import rate_limit, staff_required
from ..forms import EditalForm, ProjectForm
from ..models import Edital, Project
from ..services import EditalService
from ..utils import apply_tipo_filter

logger = logging.getLogger(__name__)


@login_required
def dashboard_home(request: HttpRequest) -> HttpResponse:
    """Dashboard home page matching React DashboardHomePage"""
    from django.shortcuts import render
    
    # Calculate statistics for staff users
    context = {}
    if request.user.is_staff:
        # Get recent activities from editais and projects
        # Use select_related to avoid N+1 queries when accessing created_by/updated_by
        recent_editais = Edital.objects.select_related('created_by', 'updated_by').filter(
            data_atualizacao__gte=timezone.now() - timedelta(days=7)
        ).order_by('-data_atualizacao')[:5]
        
        recent_projects = Project.objects.filter(
            data_atualizacao__gte=timezone.now() - timedelta(days=7)
        ).select_related('proponente', 'edital').order_by('-data_atualizacao')[:5]
        
        # Combine and sort activities
        activities = []
        for edital in recent_editais:
            activities.append({
                'type': 'edital',
                'title': edital.titulo,
                'date': edital.data_atualizacao,
                'icon': 'fa-file-alt',
                'color': 'blue',
            })
        for project in recent_projects:
            activities.append({
                'type': 'project',
                'title': project.name,
                'date': project.data_atualizacao,
                'icon': 'fa-rocket',
                'color': 'green',
            })
        
        # Sort by date descending
        activities.sort(key=lambda x: x['date'], reverse=True)
        activities = activities[:10]  # Limit to 10 most recent
        
        context = {
            'total_usuarios': User.objects.count(),
            'editais_ativos': Edital.objects.filter(status='aberto').count(),
            'startups_incubadas': Project.objects.count(),
            'recent_activities': activities,
        }
    else:
        # For non-staff users, show their own recent projects
        user_projects = Project.objects.filter(
            proponente=request.user
        ).order_by('-data_atualizacao')[:5]
        
        activities = []
        for project in user_projects:
            activities.append({
                'type': 'project',
                'title': project.name,
                'date': project.data_atualizacao,
                'icon': 'fa-rocket',
                'color': 'green',
            })
        
        context = {
            'recent_activities': activities,
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
            # Use model's search method which handles PostgreSQL full-text search or SQLite fallback
            stats_base = stats_base.search(search_query)
        
        # Apply tipo filter to stats base as well (but not status filter)
        stats_base = apply_tipo_filter(stats_base, tipo_filter)
        
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
            # Use model's search method which handles PostgreSQL full-text search or SQLite fallback
            editais = editais.search(search_query)
        
        if status_filter:
            editais = editais.filter(status=status_filter)
        
        editais = apply_tipo_filter(editais, tipo_filter)
        
        editais = editais.order_by('-data_criacao')
        
        context = {
            'editais': editais,
            'total_editais': stats['total_editais'],
            'publicados': stats['publicados'],
            'rascunhos': stats['rascunhos'],
            'total_submissoes': total_submissoes
        }
        
        return render(request, 'dashboard/editais.html', context)
    
    except (DatabaseError, ValueError) as e:
        logger.error(
            f"Erro ao carregar dashboard de editais - usuário: {request.user.username}, "
            f"erro: {str(e)}",
            exc_info=True
        )
        messages.error(request, 'Erro ao carregar editais. Tente novamente.')
        # Calculate total_submissoes even in error case for consistency
        try:
            total_submissoes = Project.objects.count()
        except DatabaseError:
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
    """Dashboard startups page - Public startup showcase"""
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
    
    except (DatabaseError, ValueError) as e:
        logger.error(
            f"Erro ao carregar dashboard de startups - usuário: {request.user.username}, "
            f"erro: {str(e)}",
            exc_info=True
        )
        messages.error(request, 'Erro ao carregar startups. Tente novamente.')
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
                'suspensa': 0,
            },
            'available_editais': Edital.objects.none(),
            'recent_update_cutoff': timezone.now() - timedelta(days=2),
        }
        return render(request, 'dashboard/projetos.html', context)


@login_required
@staff_required
def dashboard_usuarios(request: HttpRequest) -> HttpResponse:
    """Dashboard usuarios page"""
    from django.shortcuts import render
    
    # Get all users with related data
    # Note: User model doesn't have foreign keys that need select_related,
    # but we could add prefetch_related if accessing related objects like startups
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
def dashboard_submeter_projeto(request: HttpRequest) -> Union[HttpResponse, HttpResponseRedirect]:
    """Dashboard submeter startup page - Add new startups to the incubator"""
    from django.shortcuts import render
    
    try:
        if request.method == 'POST':
            form = ProjectForm(request.POST, request.FILES)
            if form.is_valid():
                project = form.save(commit=False)
                # Set proponente to current user if not staff, otherwise use form data
                if not request.user.is_staff:
                    project.proponente = request.user
                elif not project.proponente:
                    # Staff must specify proponente
                    project.proponente = request.user
                project.save()
                
                logger.info(
                    f"Startup criada com sucesso - ID: {project.pk}, "
                    f"nome: {project.name}, usuário: {request.user.username}"
                )
                
                messages.success(request, 'Startup cadastrada com sucesso!')
                return redirect('dashboard_startups')
        else:
            form = ProjectForm()
        
        return render(request, 'dashboard/submeter_projeto.html', {'form': form})
    
    except (DatabaseError, ValidationError, ValueError) as e:
        logger.error(
            f"Erro ao criar startup - usuário: {request.user.username}, "
            f"erro: {str(e)}",
            exc_info=True
        )
        messages.error(request, 'Erro ao cadastrar startup. Tente novamente.')
        if request.method == 'POST':
            form = ProjectForm(request.POST, request.FILES)
        else:
            form = ProjectForm()
        return render(request, 'dashboard/submeter_projeto.html', {'form': form})


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
    except (DatabaseError, ValidationError, ValueError) as e:
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
    except (DatabaseError, ValueError) as e:
        logger.error(
            f"Erro ao carregar dashboard - usuário: {request.user.username}, "
            f"erro: {str(e)}",
            exc_info=True
        )
        messages.error(request, 'Erro ao carregar dashboard. Tente novamente.')
        return redirect('editais_index')


@login_required
def dashboard_startup_update(request: HttpRequest, pk: int) -> Union[HttpResponse, HttpResponseRedirect]:
    """Dashboard page to update an existing startup"""
    from django.shortcuts import render
    
    project = get_object_or_404(Project, pk=pk)
    
    # Check permissions: staff can edit any startup, users can only edit their own
    if not request.user.is_staff and project.proponente != request.user:
        messages.error(request, 'Você não tem permissão para editar esta startup.')
        return redirect('dashboard_startups')
    
    try:
        if request.method == 'POST':
            form = ProjectForm(request.POST, request.FILES, instance=project)
            if form.is_valid():
                project = form.save()
                
                logger.info(
                    f"Startup atualizada com sucesso - ID: {project.pk}, "
                    f"nome: {project.name}, usuário: {request.user.username}"
                )
                
                messages.success(request, 'Startup atualizada com sucesso!')
                return redirect('dashboard_startups')
        else:
            form = ProjectForm(instance=project)
        
        return render(request, 'dashboard/startup_update.html', {
            'form': form,
            'project': project
        })
    
    except (DatabaseError, ValidationError, ValueError) as e:
        logger.error(
            f"Erro ao atualizar startup - ID: {pk}, usuário: {request.user.username}, "
            f"erro: {str(e)}",
            exc_info=True
        )
        messages.error(request, 'Erro ao atualizar startup. Tente novamente.')
        if request.method == 'POST':
            form = ProjectForm(request.POST, request.FILES, instance=project)
        else:
            form = ProjectForm(instance=project)
        return render(request, 'dashboard/startup_update.html', {
            'form': form,
            'project': project
        })

