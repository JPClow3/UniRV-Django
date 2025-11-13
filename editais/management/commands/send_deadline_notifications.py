"""
Management command para enviar notificações por email sobre editais próximos do prazo.

Este comando deve ser executado diariamente via cron/task scheduler.

Uso:
    python manage.py send_deadline_notifications
"""

import logging
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from editais.models import Edital

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Envia notificações por email sobre editais próximos do prazo (7 dias antes)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Número de dias antes do prazo para enviar notificação (padrão: 7)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executa sem enviar emails (apenas mostra o que seria enviado)',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email de destino para teste (sobrescreve lista de destinatários)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostra informações detalhadas sobre cada email',
        )

    def handle(self, *args, **options):
        days_ahead = options['days']
        dry_run = options['dry_run']
        test_email = options.get('email')
        verbose = options['verbose']
        
        today = timezone.now().date()
        deadline_date = today + timedelta(days=days_ahead)
        
        # Find editais that are closing soon
        editais_closing_soon = Edital.objects.filter(
            end_date__gte=today,
            end_date__lte=deadline_date,
            status__in=['aberto', 'em_andamento']
        ).select_related('created_by', 'updated_by').order_by('end_date')
        
        if not editais_closing_soon.exists():
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✓ Nenhum edital com prazo nos próximos {days_ahead} dias."
                )
            )
            return
        
        # Get list of staff users to notify
        from django.contrib.auth.models import User
        recipients = User.objects.filter(is_staff=True, is_active=True, email__isnull=False).exclude(email='')
        
        if test_email:
            recipients = [test_email]
        else:
            recipients = [user.email for user in recipients if user.email]
        
        if not recipients:
            self.stdout.write(
                self.style.WARNING(
                    "\n⚠ Nenhum destinatário encontrado. Configure emails para usuários staff."
                )
            )
            return
        
        # Prepare email content
        context = {
            'editais': editais_closing_soon,
            'days_ahead': days_ahead,
            'deadline_date': deadline_date,
            'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
        }
        
        # Render email templates
        subject = f'Editais próximos do prazo - {len(editais_closing_soon)} edital(is)'
        text_content = render_to_string('editais/emails/deadline_notification.txt', context)
        html_content = render_to_string('editais/emails/deadline_notification.html', context)
        
        emails_sent = 0
        errors = []
        
        for recipient in recipients:
            try:
                if verbose:
                    self.stdout.write(f"  Enviando email para: {recipient}")
                
                if not dry_run:
                    email = EmailMultiAlternatives(
                        subject,
                        text_content,
                        settings.DEFAULT_FROM_EMAIL,
                        [recipient]
                    )
                    email.attach_alternative(html_content, "text/html")
                    email.send()
                
                emails_sent += 1
            except Exception as e:
                error_msg = f"Erro ao enviar email para {recipient}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
                if verbose:
                    self.stdout.write(self.style.ERROR(f"  ERRO: {error_msg}"))
        
        # Summary
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"\n[DRY RUN] {emails_sent} email(s) seriam enviados para {len(recipients)} destinatário(s)."
                )
            )
            self.stdout.write(
                f"  {len(editais_closing_soon)} edital(is) próximo(s) do prazo encontrado(s)."
            )
        else:
            if emails_sent > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\n✓ {emails_sent} email(s) enviado(s) com sucesso para {len(recipients)} destinatário(s)."
                    )
                )
                self.stdout.write(
                    f"  {len(editais_closing_soon)} edital(is) próximo(s) do prazo notificado(s)."
                )
        
        if errors:
            self.stdout.write(
                self.style.ERROR(f"\n⚠ {len(errors)} erro(s) encontrado(s):")
            )
            for error in errors:
                self.stdout.write(self.style.ERROR(f"  - {error}"))
        
        # Logging
        logger.info(
            f"send_deadline_notifications: {emails_sent} emails enviados, "
            f"{len(editais_closing_soon)} editais, {len(errors)} erros"
        )

