import csv

import bleach
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.safestring import mark_safe

from .forms import EditalForm
from .models import Edital, EditalFavorite

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
    cleaned = bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)
    return cleaned


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


def index(request):
    """Landing page com todos os editais"""
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    # Optimize queries with select_related for foreign keys
    editais = Edital.objects.select_related(
        'created_by', 'updated_by'
    ).only(
        'id', 'numero_edital', 'titulo', 'url', 'entidade_principal',
        'status', 'data_criacao', 'data_atualizacao', 'objetivo',
        'created_by', 'updated_by'
    )

    # Apply full-text search across all fields
    if search_query:
        editais = editais.filter(build_search_query(search_query))

    if status_filter:
        editais = editais.filter(status=status_filter)

    # Use pagination constant from settings
    per_page = getattr(settings, 'EDITAIS_PER_PAGE', 12)
    paginator = Paginator(editais, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get user's favorited edital IDs for quick lookup
    favorited_ids = []
    if request.user.is_authenticated:
        favorited_ids = list(
            EditalFavorite.objects.filter(user=request.user)
            .values_list('edital_id', flat=True)
        )

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': Edital.STATUS_CHOICES,
        'favorited_ids': favorited_ids,
    }
    return render(request, 'editais/index.html', context)


def edital_detail(request, pk):
    """Página de detalhes do edital"""
    # Optimize query with select_related and prefetch_related
    edital = get_object_or_404(
        Edital.objects.select_related('created_by', 'updated_by')
        .prefetch_related('valores', 'cronogramas'),
        pk=pk
    )
    valores = edital.valores.all()
    cronogramas = edital.cronogramas.all()
    """Página de detalhes do edital"""
    edital = get_object_or_404(Edital, pk=pk)
    valores = edital.valores.all()
    cronogramas = edital.cronogramas.all()

    # Mark sanitized HTML as safe for rendering using helper function
    mark_edital_fields_safe(edital)

    # Check if user has favorited this edital
    is_favorited = False
    if request.user.is_authenticated:
        is_favorited = EditalFavorite.objects.filter(
            user=request.user,
            edital=edital
        ).exists()

    context = {
        'edital': edital,
        'valores': valores,
        'cronogramas': cronogramas,
        'is_favorited': is_favorited,
    }
    return render(request, 'editais/detail.html', context)


@login_required
def edital_create(request):
    """Página para cadastrar novo edital - Requer autenticação"""
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
            messages.success(request, 'Edital cadastrado com sucesso!')
            return redirect('edital_detail', pk=edital.pk)
    else:
        form = EditalForm()

    return render(request, 'editais/create.html', {'form': form})


@login_required
def edital_update(request, pk):
    """Página para editar edital - Requer autenticação"""
    edital = get_object_or_404(Edital, pk=pk)

    if request.method == 'POST':
        form = EditalForm(request.POST, instance=edital)
        if form.is_valid():
            edital = form.save(commit=False)
            # Track who updated this edital
            edital.updated_by = request.user
            # Sanitize all text fields using helper function
            sanitize_edital_fields(edital)
            edital.save()
            messages.success(request, 'Edital atualizado com sucesso!')
            return redirect('edital_detail', pk=edital.pk)
    else:
        form = EditalForm(instance=edital)

    return render(request, 'editais/update.html', {'form': form, 'edital': edital})


@login_required
def edital_delete(request, pk):
    """Deletar edital - Requer autenticação"""
    edital = get_object_or_404(Edital, pk=pk)

    if request.method == 'POST':
        edital.delete()
        messages.success(request, 'Edital excluído com sucesso!')
        return redirect('editais_index')

    return render(request, 'editais/delete.html', {'edital': edital})


@login_required
def toggle_favorite(request, pk):
    """Toggle favorite status for an edital (AJAX endpoint)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    edital = get_object_or_404(Edital, pk=pk)
    favorite, created = EditalFavorite.objects.get_or_create(
        user=request.user,
        edital=edital
    )

    if not created:
        # Already favorited, so remove it
        favorite.delete()
        is_favorited = False
        message = 'Removido dos favoritos'
    else:
        # Just created, so it's now favorited
        is_favorited = True
        message = 'Adicionado aos favoritos'

    return JsonResponse({
        'success': True,
        'is_favorited': is_favorited,
        'message': message
    })


@login_required
def my_favorites(request):
    """List user's favorited editais"""
    favorites = EditalFavorite.objects.filter(user=request.user).select_related('edital')

    per_page = getattr(settings, 'EDITAIS_PER_PAGE', 12)
    paginator = Paginator(favorites, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'is_favorites_page': True,
    }
    return render(request, 'editais/favorites.html', context)


@login_required
def export_editais_csv(request):
    """Export editais to CSV file"""
    # Get filtered editais (same filters as index page)
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    editais = Edital.objects.all()

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

    # Write data
    for edital in editais:
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

