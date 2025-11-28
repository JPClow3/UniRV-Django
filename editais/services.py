"""
Serviços de negócio para o aplicativo Editais.

Este módulo contém a lógica de negócio extraída das views,
seguindo o princípio de separação de responsabilidades.
"""

from typing import Dict, List
from datetime import timedelta
from django.db.models import Q
from django.db.models.query import QuerySet
from django.utils import timezone

from .models import Edital
from .constants import DEADLINE_WARNING_DAYS
from .utils import determine_edital_status


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
        
        return Edital.objects.select_related(
            'created_by', 'updated_by'
        ).filter(
            end_date__gte=today,
            end_date__lte=deadline,
            status__in=['aberto', 'em_andamento']
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
        ).select_related('created_by', 'updated_by').order_by('-data_criacao')
    
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
        ).select_related('created_by', 'updated_by').order_by('-data_atualizacao')
    
    @staticmethod
    def update_status_by_dates() -> Dict[str, int]:
        """
        Atualiza o status dos editais baseado nas datas.
        
        Esta lógica também está no método save() do modelo Edital,
        mas é útil para atualizações em lote via management command.
        
        Returns:
            dict com contagem de editais atualizados por status
        """
        today = timezone.now().date()
        now = timezone.now()
        updated_count = {'fechado': 0, 'programado': 0, 'aberto': 0}
        to_update: List[Edital] = []

        queryset = Edital.objects.exclude(status='draft').only('id', 'status', 'start_date', 'end_date')
        for edital in queryset:
            new_status = determine_edital_status(
                current_status=edital.status,
                start_date=edital.start_date,
                end_date=edital.end_date,
                today=today,
            )
            if new_status != edital.status:
                edital.status = new_status
                edital.data_atualizacao = now
                to_update.append(edital)
                if new_status in updated_count:
                    updated_count[new_status] += 1

        if to_update:
            Edital.objects.bulk_update(to_update, ['status', 'data_atualizacao'])

        return updated_count

