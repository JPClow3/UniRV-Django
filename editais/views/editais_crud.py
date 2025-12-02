"""
CRUD views for editais.

This module contains Create, Read, Update, Delete operations for editais.
"""

import logging
from typing import Union
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse, HttpRequest, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from ..decorators import rate_limit, staff_required
from ..forms import EditalForm
from ..models import Edital
from ..services import EditalService
from ..utils import sanitize_edital_fields, clear_index_cache

logger = logging.getLogger(__name__)


@login_required
@staff_required
@rate_limit(key='ip', rate=5, window=60, method='POST')
def edital_create(request: HttpRequest) -> Union[HttpResponse, HttpResponseRedirect]:
    """
    Página para cadastrar novo edital - Requer autenticação e is_staff.
    
    Args:
        request: HttpRequest
        
    Returns:
        HttpResponse: Formulário de criação ou redirecionamento após sucesso
    """
    
    logger.info(
        f"edital_create iniciado - usuário: {request.user.username}, "
        f"IP: {request.META.get('REMOTE_ADDR')}"
    )
    
    try:
        if request.method == 'POST':
            form = EditalForm(request.POST)
            if form.is_valid():
                edital = EditalService.create_edital(form, request.user)
                
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
@staff_required
@rate_limit(key='ip', rate=5, window=60, method='POST')
def edital_update(request: HttpRequest, pk: int) -> Union[HttpResponse, HttpResponseRedirect]:
    """
    Página para editar edital - Requer autenticação e is_staff.
    
    Args:
        request: HttpRequest
        pk: Primary key do edital
        
    Returns:
        HttpResponse: Formulário de edição ou redirecionamento após sucesso
    """
    
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
            from ..models import EditalHistory
            # Refresh from DB to get original values (handle edge case where object might be deleted)
            try:
                # Use select_related to avoid N+1 queries if accessing related fields
                original_edital = Edital.objects.with_related().get(pk=edital.pk)  # Fresh DB query
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
            
            with transaction.atomic():
                edital = form.save(commit=False)
                edital.updated_by = request.user
                sanitize_edital_fields(edital)
                edital.save()
                if changes:
                    EditalHistory.objects.create(
                        edital=edital,
                        edital_titulo=edital.titulo,
                        user=request.user,
                        action='update',
                        changes_summary=changes
                    )
                transaction.on_commit(clear_index_cache)
            
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
@staff_required
@rate_limit(key='ip', rate=5, window=60, method='POST')
def edital_delete(request: HttpRequest, pk: int) -> Union[HttpResponse, HttpResponseRedirect]:
    """
    Deletar edital - Requer autenticação e is_staff.
    
    Args:
        request: HttpRequest
        pk: Primary key do edital
        
    Returns:
        HttpResponse: Página de confirmação ou redirecionamento após exclusão
    """
    
    edital = get_object_or_404(Edital, pk=pk)
    
    logger.info(
        f"edital_delete iniciado - edital_id: {pk}, "
        f"usuário: {request.user.username}, IP: {request.META.get('REMOTE_ADDR')}"
    )

    if request.method == 'POST':
        try:
            # Create history entry before deletion (preserve title)
            from ..models import EditalHistory
            with transaction.atomic():
                EditalHistory.objects.create(
                    edital=edital,
                    edital_titulo=edital.titulo,
                    user=request.user,
                    action='delete',
                    changes_summary={'titulo': edital.titulo}
                )
                titulo_edital = edital.titulo
                edital.delete()
                transaction.on_commit(clear_index_cache)
            
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

