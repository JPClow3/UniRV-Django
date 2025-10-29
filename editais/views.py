from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Edital
from .forms import EditalForm


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

    context = {
        'edital': edital,
        'valores': valores,
        'cronogramas': cronogramas,
    }
    return render(request, 'editais/detail.html', context)


def edital_create(request):
    """Página para cadastrar novo edital"""
    if request.method == 'POST':
        form = EditalForm(request.POST)
        if form.is_valid():
            edital = form.save()
            messages.success(request, 'Edital cadastrado com sucesso!')
            return redirect('edital_detail', pk=edital.pk)
    else:
        form = EditalForm()

    return render(request, 'editais/create.html', {'form': form})


def edital_update(request, pk):
    """Página para editar edital"""
    edital = get_object_or_404(Edital, pk=pk)

    if request.method == 'POST':
        form = EditalForm(request.POST, instance=edital)
        if form.is_valid():
            form.save()
            messages.success(request, 'Edital atualizado com sucesso!')
            return redirect('edital_detail', pk=edital.pk)
    else:
        form = EditalForm(instance=edital)

    return render(request, 'editais/update.html', {'form': form, 'edital': edital})


def edital_delete(request, pk):
    """Deletar edital"""
    edital = get_object_or_404(Edital, pk=pk)

    if request.method == 'POST':
        edital.delete()
        messages.success(request, 'Edital excluído com sucesso!')
        return redirect('editais_index')

    return render(request, 'editais/delete.html', {'edital': edital})

