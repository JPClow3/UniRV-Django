"""
Serviços de negócio para o aplicativo Editais.

Este módulo contém a lógica de negócio extraída das views,
seguindo o princípio de separação de responsabilidades.
"""

from datetime import timedelta
from django.db.models import Q
from django.utils import timezone

from .models import Edital
from .constants import DEADLINE_WARNING_DAYS


class EditalService:
    """Serviço para operações de negócio relacionadas a editais."""
    
    @staticmethod
    def get_editais_by_deadline(days=DEADLINE_WARNING_DAYS):
        """
        Retorna editais que expiram dentro de N dias.
        
        Args:
            days: Número de dias até o prazo (padrão: 7)
            
        Returns:
            QuerySet de editais próximos do prazo
        """
        today = timezone.now().date()
        deadline = today + timedelta(days=days)
        
        return Edital.objects.filter(
            end_date__gte=today,
            end_date__lte=deadline,
            status__in=['aberto', 'em_andamento']
        ).order_by('end_date')
    
    @staticmethod
    def get_recent_editais(days=7):
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
    def get_recent_activities(days=7):
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
    def update_status_by_dates():
        """
        Atualiza o status dos editais baseado nas datas.
        
        Esta lógica também está no método save() do modelo Edital,
        mas é útil para atualizações em lote via management command.
        
        Returns:
            dict com contagem de editais atualizados por status
        """
        today = timezone.now().date()
        now = timezone.now()
        
        updated_count = {
            'fechado': 0,
            'programado': 0,
            'aberto': 0,
        }
        
        # Atualizar editais para 'fechado'
        count_closed = Edital.objects.filter(
            end_date__lte=today,
            status='aberto'
        ).update(status='fechado', data_atualizacao=now)
        updated_count['fechado'] = count_closed
        
        # Atualizar editais para 'programado'
        count_scheduled = Edital.objects.filter(
            start_date__gt=today
        ).exclude(
            status__in=['draft', 'programado']
        ).update(status='programado', data_atualizacao=now)
        updated_count['programado'] = count_scheduled
        
        # Atualizar editais para 'aberto'
        count_opened = Edital.objects.filter(
            start_date__lte=today,
            end_date__gte=today,
            status='programado'
        ).update(status='aberto', data_atualizacao=now)
        updated_count['aberto'] = count_opened
        
        return updated_count

