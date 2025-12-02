"""
Serviços de negócio para o aplicativo Editais.

Este módulo contém a lógica de negócio extraída das views,
seguindo o princípio de separação de responsabilidades.
"""

from typing import TYPE_CHECKING
from datetime import timedelta
from django.db.models import Q
from django.db.models.query import QuerySet
from django.db import transaction
from django.utils import timezone

from .models import Edital
from .constants import DEADLINE_WARNING_DAYS, OPEN_EDITAL_STATUSES
from .utils import determine_edital_status, sanitize_edital_fields, clear_index_cache

if TYPE_CHECKING:
    from django.contrib.auth.models import User
    from django.forms import ModelForm


class EditalService:
    """Serviço para operações de negócio relacionadas a editais."""
    
    @staticmethod
    def get_editais_by_deadline(days: int = DEADLINE_WARNING_DAYS) -> QuerySet:
        """
        Retorna editais que expiram dentro de N dias.
        
        Args:
            days: Número de dias até o prazo (padrão: 7)
            
        Returns:
            QuerySet de editais próximos do prazo
        """
        today = timezone.now().date()
        deadline = today + timedelta(days=days)
        
        return Edital.objects.with_related().filter(
            end_date__gte=today,
            end_date__lte=deadline,
            status__in=OPEN_EDITAL_STATUSES
        ).order_by('end_date')
    
    @staticmethod
    def get_recent_editais(days: int = 7) -> QuerySet:
        """
        Retorna editais criados nos últimos N dias.
        
        Args:
            days: Número de dias (padrão: 7)
            
        Returns:
            QuerySet de editais recentes
        """
        cutoff_date = timezone.now() - timedelta(days=days)
        
        return Edital.objects.filter(
            data_criacao__gte=cutoff_date
        ).with_related().order_by('-data_criacao')
    
    @staticmethod
    def get_recent_activities(days: int = 7) -> QuerySet:
        """
        Retorna editais criados ou atualizados nos últimos N dias.
        
        Args:
            days: Número de dias (padrão: 7)
            
        Returns:
            QuerySet de atividades recentes
        """
        cutoff_date = timezone.now() - timedelta(days=days)
        
        return Edital.objects.filter(
            Q(data_criacao__gte=cutoff_date) | Q(data_atualizacao__gte=cutoff_date)
        ).with_related().order_by('-data_atualizacao')
    
    @staticmethod
    def create_edital(form: 'ModelForm', user: 'User') -> Edital:
        """
        Cria um novo edital a partir de um formulário válido.
        
        Este método centraliza a lógica de criação de editais, incluindo:
        - Sanitização de campos HTML
        - Criação de histórico
        - Invalidação de cache
        
        Args:
            form: Formulário EditalForm válido
            user: Usuário que está criando o edital
            
        Returns:
            Edital: Instância do edital criado
            
        Raises:
            ValueError: Se o formulário não for válido
        """
        if not form.is_valid():
            raise ValueError("Form must be valid before creating edital")
        
        from .models import EditalHistory
        
        with transaction.atomic():
            edital = form.save(commit=False)
            edital.created_by = user
            edital.updated_by = user
            sanitize_edital_fields(edital)
            edital.save()
            
            EditalHistory.objects.create(
                edital=edital,
                edital_titulo=edital.titulo,
                user=user,
                action='create',
                changes_summary={'titulo': edital.titulo}
            )
            
            transaction.on_commit(clear_index_cache)
        
        return edital

