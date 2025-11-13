"""
Management command para atualizar automaticamente o status dos editais
baseado nas datas de abertura (start_date) e encerramento (end_date).

Este comando deve ser executado diariamente via cron/task scheduler.

Uso:
    python manage.py update_edital_status
"""

import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from django.core.cache import cache
from editais.models import Edital

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Atualiza automaticamente o status dos editais baseado nas datas de abertura e encerramento."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executa sem fazer alterações no banco de dados (apenas mostra o que seria alterado)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostra informações detalhadas sobre cada edital atualizado',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        today = timezone.now().date()
        
        updated_count = 0
        errors = []

        # Atualizar editais que devem ser fechados (end_date < hoje e status='aberto')
        editais_to_close = Edital.objects.filter(
            end_date__lt=today,
            status='aberto'
        )
        
        for edital in editais_to_close:
            try:
                if verbose:
                    self.stdout.write(
                        f"  Fechando edital '{edital.titulo}' (ID: {edital.pk}) - "
                        f"end_date: {edital.end_date}"
                    )
                
                if not dry_run:
                    edital.status = 'fechado'
                    edital.save(update_fields=['status', 'data_atualizacao'])
                
                updated_count += 1
            except Exception as e:
                error_msg = f"Erro ao fechar edital ID {edital.pk}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
                if verbose:
                    self.stdout.write(self.style.ERROR(f"  ERRO: {error_msg}"))

        # Atualizar editais que devem ser programados (start_date > hoje e status != 'draft')
        editais_to_schedule = Edital.objects.filter(
            start_date__gt=today
        ).exclude(
            status__in=['draft', 'programado']
        )
        
        for edital in editais_to_schedule:
            try:
                if verbose:
                    self.stdout.write(
                        f"  Programando edital '{edital.titulo}' (ID: {edital.pk}) - "
                        f"start_date: {edital.start_date}, status atual: {edital.status}"
                    )
                
                if not dry_run:
                    edital.status = 'programado'
                    edital.save(update_fields=['status', 'data_atualizacao'])
                
                updated_count += 1
            except Exception as e:
                error_msg = f"Erro ao programar edital ID {edital.pk}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
                if verbose:
                    self.stdout.write(self.style.ERROR(f"  ERRO: {error_msg}"))

        # Atualizar editais que devem ser abertos (start_date <= hoje <= end_date e status='programado')
        editais_to_open = Edital.objects.filter(
            start_date__lte=today,
            end_date__gte=today,
            status='programado'
        )
        
        for edital in editais_to_open:
            try:
                if verbose:
                    self.stdout.write(
                        f"  Abrindo edital '{edital.titulo}' (ID: {edital.pk}) - "
                        f"start_date: {edital.start_date}, end_date: {edital.end_date}"
                    )
                
                if not dry_run:
                    edital.status = 'aberto'
                    edital.save(update_fields=['status', 'data_atualizacao'])
                
                updated_count += 1
            except Exception as e:
                error_msg = f"Erro ao abrir edital ID {edital.pk}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
                if verbose:
                    self.stdout.write(self.style.ERROR(f"  ERRO: {error_msg}"))

        # Resumo
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"\n[DRY RUN] {updated_count} edital(is) seriam atualizados."
                )
            )
        else:
            if updated_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\n✓ {updated_count} edital(is) atualizado(s) com sucesso."
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        "\n✓ Nenhum edital precisou ser atualizado."
                    )
                )

        if errors:
            self.stdout.write(
                self.style.ERROR(f"\n⚠ {len(errors)} erro(s) encontrado(s):")
            )
            for error in errors:
                self.stdout.write(self.style.ERROR(f"  - {error}"))

        # Invalidate cache if any editais were updated
        if updated_count > 0 and not dry_run:
            try:
                # Import cache clearing function from views
                from editais.views import _clear_index_cache
                _clear_index_cache()
                if verbose:
                    self.stdout.write(self.style.SUCCESS("  Cache invalidado com sucesso."))
            except Exception as e:
                error_msg = f"Erro ao invalidar cache: {str(e)}"
                logger.warning(error_msg)
                if verbose:
                    self.stdout.write(self.style.WARNING(f"  AVISO: {error_msg}"))

        # Logging
        logger.info(
            f"update_edital_status: {updated_count} editais atualizados, "
            f"{len(errors)} erros"
        )

