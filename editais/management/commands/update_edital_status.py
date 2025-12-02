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
from django.core.cache import cache
from django.db.models import Q
from editais.models import Edital
from editais.services import EditalService
from editais.constants import DRAFT_STATUSES

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

        if verbose:
            # In verbose mode, show which editais would be affected before bulk update
            editais_to_close = Edital.objects.filter(
                end_date__lte=today,  # Close when deadline day has passed or is today
                status='aberto'
            )
            for edital in editais_to_close:
                self.stdout.write(
                    f"  Fechando edital '{edital.titulo}' (ID: {edital.pk}) - "
                    f"end_date: {edital.end_date}"
                )
            
            editais_to_schedule = Edital.objects.filter(
                start_date__gt=today
            ).exclude(
                status__in=DRAFT_STATUSES
            )
            for edital in editais_to_schedule:
                self.stdout.write(
                    f"  Programando edital '{edital.titulo}' (ID: {edital.pk}) - "
                    f"start_date: {edital.start_date}, status atual: {edital.status}"
                )
            
            editais_to_open = Edital.objects.filter(
                Q(start_date__lte=today) & (Q(end_date__gte=today) | Q(end_date__isnull=True)),
                status='programado'
            )
            for edital in editais_to_open:
                self.stdout.write(
                    f"  Abrindo edital '{edital.titulo}' (ID: {edital.pk}) - "
                    f"start_date: {edital.start_date}, end_date: {edital.end_date}"
                )

        # Count updates that would be made (for dry-run reporting)
        # Count editais that would be affected using the same logic as the service method
        count_to_close = Edital.objects.filter(
            end_date__lte=today,  # Close when deadline day has passed or is today
            status='aberto'
        ).count()
        
        count_to_schedule = Edital.objects.filter(
            start_date__gt=today
        ).exclude(
            status__in=['draft', 'programado']
        ).count()
        
        count_to_open = Edital.objects.filter(
            Q(start_date__lte=today) & (Q(end_date__gte=today) | Q(end_date__isnull=True)),
            status='programado'
        ).count()
        
        potential_updates = count_to_close + count_to_schedule + count_to_open

        if not dry_run:
            # Use individual saves to catch errors from patched save() methods (for testing)
            # This allows us to report errors for individual editais
            # Close editais individually
            editais_to_close = Edital.objects.filter(
                end_date__lte=today,
                status='aberto'
            )
            for edital in editais_to_close:
                try:
                    edital.status = 'fechado'
                    edital.save()
                    updated_count += 1
                except Exception as save_error:
                    error_msg = f"Erro ao salvar edital '{edital.titulo}' (ID: {edital.pk}): {str(save_error)}"
                    errors.append(error_msg)
                    logger.error(error_msg, exc_info=True)
                    if verbose:
                        self.stdout.write(self.style.ERROR(f"  ERRO: {error_msg}"))
            
            # Schedule editais individually
            editais_to_schedule = Edital.objects.filter(
                start_date__gt=today
            ).exclude(
                status__in=DRAFT_STATUSES
            )
            for edital in editais_to_schedule:
                try:
                    edital.status = 'programado'
                    edital.save()
                    updated_count += 1
                except Exception as save_error:
                    error_msg = f"Erro ao salvar edital '{edital.titulo}' (ID: {edital.pk}): {str(save_error)}"
                    errors.append(error_msg)
                    logger.error(error_msg, exc_info=True)
                    if verbose:
                        self.stdout.write(self.style.ERROR(f"  ERRO: {error_msg}"))
            
            # Open editais individually
            # Include continuous flow editais (end_date=None) that have started
            editais_to_open = Edital.objects.filter(
                Q(start_date__lte=today) & (Q(end_date__gte=today) | Q(end_date__isnull=True)),
                status='programado'
            )
            for edital in editais_to_open:
                try:
                    edital.status = 'aberto'
                    edital.save()
                    updated_count += 1
                except Exception as save_error:
                    error_msg = f"Erro ao salvar edital '{edital.titulo}' (ID: {edital.pk}): {str(save_error)}"
                    errors.append(error_msg)
                    logger.error(error_msg, exc_info=True)
                    if verbose:
                        self.stdout.write(self.style.ERROR(f"  ERRO: {error_msg}"))
        else:
            # In dry-run mode, use the potential updates count
            updated_count = potential_updates

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
                        f"\n[OK] {updated_count} edital(is) atualizado(s) com sucesso."
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        "\n[OK] Nenhum edital precisou ser atualizado."
                    )
                )

        if errors:
            self.stdout.write(
                self.style.ERROR(f"\n[ERRO] {len(errors)} erro(s) encontrado(s):")
            )
            for error in errors:
                self.stdout.write(self.style.ERROR(f"  - {error}"))

        # Invalidate cache if any editais were updated
        if updated_count > 0 and not dry_run:
            try:
                # Import cache clearing function from utils
                from editais.utils import clear_index_cache
                clear_index_cache()
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

