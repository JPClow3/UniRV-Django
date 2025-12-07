"""
Serviços de negócio para o aplicativo Editais.

Este módulo contém a lógica de negócio extraída das views,
seguindo o princípio de separação de responsabilidades.
"""

from typing import TYPE_CHECKING, Dict, Any, Optional
from datetime import timedelta
from django.db.models import Q
from django.db.models.query import QuerySet
from django.db import transaction
from django.utils import timezone

from .models import Edital
from .constants import DEADLINE_WARNING_DAYS, OPEN_EDITAL_STATUSES
from .utils import sanitize_edital_fields, clear_index_cache, apply_tipo_filter

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
        
        with transaction.atomic():
            edital = form.save(commit=False)
            edital.created_by = user
            edital.updated_by = user
            sanitize_edital_fields(edital)
            edital.save()
            # History tracking is now handled automatically by django-simple-history
            
            transaction.on_commit(clear_index_cache)
        
        return edital
    
    @staticmethod
    def get_editais_by_status(status: str) -> QuerySet:
        """
        Retorna editais filtrados por status.
        
        Args:
            status: Status do edital
            
        Returns:
            QuerySet de editais com o status especificado
        """
        return Edital.objects.with_related().filter(status=status)
    
    @staticmethod
    def apply_filters(queryset: QuerySet, filters: Dict[str, Any]) -> QuerySet:
        """
        Aplica múltiplos filtros a um queryset de editais.
        
        Args:
            queryset: QuerySet base
            filters: Dicionário com filtros a aplicar:
                - search_query: Busca de texto
                - status: Filtro de status
                - tipo: Filtro de tipo (Fluxo Contínuo/Fomento)
                - start_date: Data de início mínima
                - end_date: Data de término máxima
                
        Returns:
            QuerySet filtrado
        """
        from .views.public import build_search_query
        from .utils import parse_date_filter
        
        if filters.get('search_query'):
            # Use queryset-aware search for PostgreSQL full-text search support
            search_q, queryset = build_search_query(filters['search_query'], queryset)
        
        if filters.get('status'):
            queryset = queryset.filter(status=filters['status'])
        
        if filters.get('tipo'):
            queryset = apply_tipo_filter(queryset, filters['tipo'])
        
        start_date = parse_date_filter(filters.get('start_date', ''))
        if start_date:
            queryset = queryset.filter(start_date__gte=start_date)
        
        end_date = parse_date_filter(filters.get('end_date', ''))
        if end_date:
            queryset = queryset.filter(end_date__lte=end_date)
        
        return queryset
    

