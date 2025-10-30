from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.safestring import mark_safe
import bleach

from .models import Edital
from .forms import EditalForm

# Allowed tags and attributes for HTML sanitization
ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                'ul', 'ol', 'li', 'blockquote', 'a', 'code', 'pre', 'table',
                'thead', 'tbody', 'tr', 'th', 'td', 'div', 'span']
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
    # Bleach will clean and return safe HTML string
    cleaned = bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)
    return cleaned


def index(request):
    """Landing page com todos os editais"""
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    editais = Edital.objects.all()

    if search_query:
        editais = editais.filter(
            Q(titulo__icontains=search_query) |
            Q(entidade_principal__icontains=search_query) |
            Q(numero_edital__icontains=search_query)
        )

    if status_filter:
        editais = editais.filter(status=status_filter)

    paginator = Paginator(editais, 12)  # 12 editais por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': Edital.STATUS_CHOICES,
    }
    return render(request, 'editais/index.html', context)


def edital_detail(request, pk):
    """Página de detalhes do edital"""
    edital = get_object_or_404(Edital, pk=pk)
    valores = edital.valores.all()
    cronogramas = edital.cronogramas.all()

    # Mark sanitized HTML as safe for rendering
    # Since content is already sanitized in the database, we can safely mark it
    if edital.analise:
        edital.analise_safe = mark_safe(edital.analise)
    if edital.objetivo:
        edital.objetivo_safe = mark_safe(edital.objetivo)
    if edital.etapas:
        edital.etapas_safe = mark_safe(edital.etapas)
    if edital.recursos:
        edital.recursos_safe = mark_safe(edital.recursos)
    if edital.itens_financiaveis:
        edital.itens_financiaveis_safe = mark_safe(edital.itens_financiaveis)
    if edital.criterios_elegibilidade:
        edital.criterios_elegibilidade_safe = mark_safe(edital.criterios_elegibilidade)
    if edital.criterios_avaliacao:
        edital.criterios_avaliacao_safe = mark_safe(edital.criterios_avaliacao)
    if edital.itens_essenciais_observacoes:
        edital.itens_essenciais_observacoes_safe = mark_safe(edital.itens_essenciais_observacoes)
    if edital.detalhes_unirv:
        edital.detalhes_unirv_safe = mark_safe(edital.detalhes_unirv)

    context = {
        'edital': edital,
        'valores': valores,
        'cronogramas': cronogramas,
    }
    return render(request, 'editais/detail.html', context)


@login_required
def edital_create(request):
    """Página para cadastrar novo edital - Requer autenticação"""
    if request.method == 'POST':
        form = EditalForm(request.POST)
        if form.is_valid():
            edital = form.save(commit=False)
            # Sanitize all text fields before saving
            edital.analise = sanitize_html(edital.analise)
            edital.objetivo = sanitize_html(edital.objetivo)
            edital.etapas = sanitize_html(edital.etapas)
            edital.recursos = sanitize_html(edital.recursos)
            edital.itens_financiaveis = sanitize_html(edital.itens_financiaveis)
            edital.criterios_elegibilidade = sanitize_html(edital.criterios_elegibilidade)
            edital.criterios_avaliacao = sanitize_html(edital.criterios_avaliacao)
            edital.itens_essenciais_observacoes = sanitize_html(edital.itens_essenciais_observacoes)
            edital.detalhes_unirv = sanitize_html(edital.detalhes_unirv)
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
            # Sanitize all text fields before saving
            edital.analise = sanitize_html(edital.analise)
            edital.objetivo = sanitize_html(edital.objetivo)
            edital.etapas = sanitize_html(edital.etapas)
            edital.recursos = sanitize_html(edital.recursos)
            edital.itens_financiaveis = sanitize_html(edital.itens_financiaveis)
            edital.criterios_elegibilidade = sanitize_html(edital.criterios_elegibilidade)
            edital.criterios_avaliacao = sanitize_html(edital.criterios_avaliacao)
            edital.itens_essenciais_observacoes = sanitize_html(edital.itens_essenciais_observacoes)
            edital.detalhes_unirv = sanitize_html(edital.detalhes_unirv)
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
