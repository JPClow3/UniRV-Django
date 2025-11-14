import csv

import bleach
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.safestring import mark_safe

from .forms import EditalForm
from .models import Edital

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
    """Sanitize HTML content to prevent XSS attacks."""
    if not text:
        return text
    # Ensure text is a string
    if not isinstance(text, str):
        text = str(text)
    try:
        cleaned = bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)
        return cleaned
    except Exception:
        # If sanitization fails, return empty string to prevent XSS
        return ''


def sanitize_edital_fields(edital):
    """
    Sanitize all text fields in an edital instance.
    Helper function to avoid code duplication.
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
    Mark sanitized HTML fields as safe for template rendering.
    Helper function to avoid code duplication.
    """
    fields = [
        'objetivo', 'etapas', 'recursos',
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
    Build a Q object for full-text search across all edital fields.
    Uses settings.EDITAL_SEARCH_FIELDS for field list.
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


def index(request):
    """Landing page com todos os editais"""
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    start_date_filter = request.GET.get('start_date', '')
    end_date_filter = request.GET.get('end_date', '')
    only_open = request.GET.get('only_open', '') == '1'  # Checkbox "somente abertos"
    page_number = request.GET.get('page', '1')

    # Build cache key based on query parameters
    # Only cache if no search or filter is applied (most common case)
    cache_key = None
    has_filters = search_query or status_filter or start_date_filter or end_date_filter or only_open
    use_cache = not has_filters and not request.user.is_authenticated
    cache_ttl = getattr(settings, 'EDITAIS_CACHE_TTL', 300)  # 5 minutes default

    if use_cache:
        # Get current cache version to ensure we get the latest cached data
        version_key = 'editais_index_cache_version'
        cache_version = cache.get(version_key, 0)
        cache_key = f'editais_index_page_{page_number}_v{cache_version}'
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

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

    # Use pagination constant from settings
    per_page = getattr(settings, 'EDITAIS_PER_PAGE', 12)
    paginator = Paginator(editais, per_page)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'start_date_filter': start_date_filter,
        'end_date_filter': end_date_filter,
        'only_open': only_open,
        'status_choices': Edital.STATUS_CHOICES,
        'total_count': page_obj.paginator.count,  # Total count for results counter
    }
    
    response = render(request, 'editais/index.html', context)
    
    # Cache the response if applicable
    if use_cache and cache_key:
        cache.set(cache_key, response, cache_ttl)
    
    return response


def edital_detail(request, slug=None, pk=None):
    """Página de detalhes do edital - suporta slug ou PK"""
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
        from django.http import Http404
        raise Http404("Edital não encontrado")
    
    # FR-010: Hide draft editais from non-authenticated or non-staff users
    if edital.status == 'draft':
        if not request.user.is_authenticated or not request.user.is_staff:
            from django.http import Http404
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
    return render(request, 'editais/detail.html', context)


def edital_detail_redirect(request, pk):
    """Redirect PK-based URLs to slug-based URLs (301 permanent redirect)"""
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
def edital_create(request):
    """Página para cadastrar novo edital - Requer autenticação e is_staff"""
    if not request.user.is_staff:
        return render(request, '403.html', {
            'message': 'Apenas usuários staff podem criar editais.'
        }, status=403)
    
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
            messages.success(request, 'Edital cadastrado com sucesso!')
            return redirect(edital.get_absolute_url())
    else:
        form = EditalForm()

    return render(request, 'editais/create.html', {'form': form})


@login_required
def edital_update(request, pk):
    """Página para editar edital - Requer autenticação e is_staff"""
    if not request.user.is_staff:
        return render(request, '403.html', {
            'message': 'Apenas usuários staff podem editar editais.'
        }, status=403)
    
    edital = get_object_or_404(Edital, pk=pk)

    if request.method == 'POST':
        form = EditalForm(request.POST, instance=edital)
        if form.is_valid():
            # IMPORTANT: Capture original values BEFORE save(commit=False)
            # After save(commit=False), form.instance will have new values
            from .models import EditalHistory
            # Refresh from DB to get original values (handle edge case where object might be deleted)
            try:
                original_edital = Edital.objects.get(pk=edital.pk)  # Fresh DB query
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
            messages.success(request, 'Edital atualizado com sucesso!')
            return redirect(edital.get_absolute_url())
    else:
        form = EditalForm(instance=edital)

    return render(request, 'editais/update.html', {'form': form, 'edital': edital})


@login_required
def edital_delete(request, pk):
    """Deletar edital - Requer autenticação e is_staff"""
    if not request.user.is_staff:
        return render(request, '403.html', {
            'message': 'Apenas usuários staff podem deletar editais.'
        }, status=403)
    
    edital = get_object_or_404(Edital, pk=pk)

    if request.method == 'POST':
        # Create history entry before deletion (preserve title)
        from .models import EditalHistory
        EditalHistory.objects.create(
            edital=edital,
            edital_titulo=edital.titulo,  # Preserve title before deletion
            user=request.user,
            action='delete',
            changes_summary={'titulo': edital.titulo}
        )
        
        edital.delete()
        # Invalidate cache for index pages (clear all index cache keys)
        _clear_index_cache()
        messages.success(request, 'Edital excluído com sucesso!')
        return redirect('editais_index')

    return render(request, 'editais/delete.html', {'edital': edital})


@login_required
def export_editais_csv(request):
    """Export editais to CSV file - Requer autenticação e is_staff"""
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
def admin_dashboard(request):
    """Dashboard administrativo com estatísticas e gráficos"""
    if not request.user.is_staff:
        return render(request, '403.html', {
            'message': 'Apenas usuários staff podem acessar o dashboard.'
        }, status=403)
    
    from django.db.models import Count, Q
    from django.utils import timezone
    from datetime import timedelta
    
    # Estatísticas gerais
    total_editais = Edital.objects.count()
    editais_por_status = Edital.objects.values('status').annotate(count=Count('id')).order_by('status')
    
    # Editais recentes (últimos 7 dias)
    seven_days_ago = timezone.now() - timedelta(days=7)
    editais_recentes = Edital.objects.filter(
        data_criacao__gte=seven_days_ago
    ).select_related('created_by').order_by('-data_criacao')[:10]
    
    # Editais próximos do prazo (7 dias)
    today = timezone.now().date()
    deadline_date = today + timedelta(days=7)
    editais_proximos_prazo = Edital.objects.filter(
        end_date__gte=today,
        end_date__lte=deadline_date,
        status__in=['aberto', 'em_andamento']
    ).order_by('end_date')[:10]
    
    # Atividades recentes (criados e atualizados)
    atividades_recentes = Edital.objects.filter(
        Q(data_criacao__gte=seven_days_ago) | Q(data_atualizacao__gte=seven_days_ago)
    ).select_related('created_by', 'updated_by').order_by('-data_atualizacao')[:15]
    
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

