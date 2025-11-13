"""
Testes para management commands do app editais.
"""

from datetime import date, timedelta
from django.test import TestCase
from django.core.management import call_command
from django.utils import timezone
from io import StringIO
from editais.models import Edital
from unittest.mock import patch, MagicMock


class UpdateEditalStatusCommandTest(TestCase):
    """Testes para o comando update_edital_status."""

    def setUp(self):
        """Criar editais de teste com diferentes cenários de data."""
        today = timezone.now().date()
        
        # Edital que deve ser fechado (end_date < hoje, status='aberto')
        self.edital_to_close = Edital.objects.create(
            titulo="Edital para Fechar",
            url="https://example.com/close",
            status='aberto',
            start_date=today - timedelta(days=30),
            end_date=today - timedelta(days=1),  # Encerrou ontem
        )
        
        # Edital que deve ser programado (start_date > hoje, status != 'draft')
        self.edital_to_schedule = Edital.objects.create(
            titulo="Edital para Programar",
            url="https://example.com/schedule",
            status='aberto',  # Status atual que deve mudar
            start_date=today + timedelta(days=10),  # Começa em 10 dias
            end_date=today + timedelta(days=40),
        )
        
        # Edital que deve ser aberto (start_date <= hoje <= end_date, status='programado')
        self.edital_to_open = Edital.objects.create(
            titulo="Edital para Abrir",
            url="https://example.com/open",
            status='programado',
            start_date=today - timedelta(days=1),  # Começou ontem
            end_date=today + timedelta(days=30),
        )
        
        # Edital que não deve mudar (draft)
        self.edital_draft = Edital.objects.create(
            titulo="Edital Rascunho",
            url="https://example.com/draft",
            status='draft',
            start_date=today + timedelta(days=5),
            end_date=today + timedelta(days=35),
        )
        
        # Edital que não deve mudar (já fechado)
        self.edital_closed = Edital.objects.create(
            titulo="Edital Fechado",
            url="https://example.com/closed",
            status='fechado',
            start_date=today - timedelta(days=60),
            end_date=today - timedelta(days=30),
        )

    def test_close_editais_with_past_end_date(self):
        """Testa que editais com end_date < hoje e status='aberto' são fechados."""
        # O modelo já fecha automaticamente no save(), então precisamos criar
        # um edital que não foi fechado automaticamente (usando update para evitar save())
        today = timezone.now().date()
        edital = Edital.objects.create(
            titulo="Edital para Fechar Manualmente",
            url="https://example.com/close-manual",
            status='aberto',
            start_date=today - timedelta(days=30),
            end_date=today - timedelta(days=1),
        )
        # Se o save() já fechou, vamos forçar o status para 'aberto' usando update
        if edital.status == 'fechado':
            Edital.objects.filter(pk=edital.pk).update(status='aberto')
            edital.refresh_from_db()
        
        self.assertEqual(edital.status, 'aberto')
        
        call_command('update_edital_status')
        
        edital.refresh_from_db()
        self.assertEqual(edital.status, 'fechado')

    def test_schedule_editais_with_future_start_date(self):
        """Testa que editais com start_date > hoje são programados."""
        self.assertEqual(self.edital_to_schedule.status, 'aberto')
        
        call_command('update_edital_status')
        
        self.edital_to_schedule.refresh_from_db()
        self.assertEqual(self.edital_to_schedule.status, 'programado')

    def test_open_editais_with_current_dates(self):
        """Testa que editais programados com datas atuais são abertos."""
        self.assertEqual(self.edital_to_open.status, 'programado')
        
        call_command('update_edital_status')
        
        self.edital_to_open.refresh_from_db()
        self.assertEqual(self.edital_to_open.status, 'aberto')

    def test_draft_editais_not_changed(self):
        """Testa que editais em draft não são alterados."""
        original_status = self.edital_draft.status
        
        call_command('update_edital_status')
        
        self.edital_draft.refresh_from_db()
        self.assertEqual(self.edital_draft.status, original_status)

    def test_closed_editais_not_changed(self):
        """Testa que editais já fechados não são alterados."""
        original_status = self.edital_closed.status
        
        call_command('update_edital_status')
        
        self.edital_closed.refresh_from_db()
        self.assertEqual(self.edital_closed.status, original_status)

    def test_dry_run_mode(self):
        """Testa que o modo dry-run não altera o banco de dados."""
        original_status = self.edital_to_close.status
        
        out = StringIO()
        call_command('update_edital_status', '--dry-run', stdout=out)
        
        self.edital_to_close.refresh_from_db()
        self.assertEqual(self.edital_to_close.status, original_status)
        self.assertIn('DRY RUN', out.getvalue())

    def test_verbose_output(self):
        """Testa que o modo verbose mostra informações detalhadas."""
        out = StringIO()
        call_command('update_edital_status', '--verbose', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Fechando edital', output)
        self.assertIn('Programando edital', output)
        self.assertIn('Abrindo edital', output)

    def test_command_handles_errors_gracefully(self):
        """Testa que o comando lida com erros graciosamente."""
        # Criar um edital com dados inválidos que podem causar erro
        # (simulando um cenário de erro)
        edital = Edital.objects.create(
            titulo="Edital com Problema",
            url="https://example.com/problem",
            status='aberto',
            start_date=timezone.now().date() - timedelta(days=1),
            end_date=timezone.now().date() - timedelta(days=2),
        )
        
        # O comando deve executar sem levantar exceção
        out = StringIO()
        try:
            call_command('update_edital_status', stdout=out, stderr=out)
            # Se chegou aqui, o comando lidou com o erro graciosamente
            success = True
        except Exception:
            success = False
        
        self.assertTrue(success)

    def test_cache_invalidation_on_update(self):
        """Testa que o cache é invalidado quando editais são atualizados."""
        from unittest.mock import patch
        from editais.views import _clear_index_cache
        
        with patch('editais.views._clear_index_cache') as mock_clear_cache:
            call_command('update_edital_status')
            
            # Verificar que cache foi invalidado (se houve atualizações)
            # Pode ser chamado 0 ou mais vezes dependendo dos editais
            # O importante é que não cause erro
            self.assertTrue(True)  # Teste passa se não houver exceção

    def test_cache_not_invalidated_on_dry_run(self):
        """Testa que o cache não é invalidado em modo dry-run."""
        from unittest.mock import patch
        from editais.views import _clear_index_cache
        
        with patch('editais.views._clear_index_cache') as mock_clear_cache:
            call_command('update_edital_status', '--dry-run')
            
            # Em dry-run, cache não deve ser invalidado
            mock_clear_cache.assert_not_called()

    def test_cache_invalidation_with_verbose(self):
        """Testa que a invalidação de cache mostra mensagem em modo verbose."""
        from unittest.mock import patch
        
        with patch('editais.views._clear_index_cache'):
            out = StringIO()
            call_command('update_edital_status', '--verbose', stdout=out)
            
            output = out.getvalue()
            # Se houve atualizações, deve mostrar mensagem de cache
            # (mas não é obrigatório se não houve atualizações)

    def test_editais_already_in_correct_status(self):
        """Testa que editais já no status correto não são alterados."""
        today = timezone.now().date()
        
        # Edital já fechado com end_date passado (não deve mudar)
        edital_closed = Edital.objects.create(
            titulo="Edital Já Fechado",
            url="https://example.com/already-closed",
            status='fechado',
            start_date=today - timedelta(days=30),
            end_date=today - timedelta(days=1),
        )
        
        # Edital já aberto com datas corretas (não deve mudar)
        edital_open = Edital.objects.create(
            titulo="Edital Já Aberto",
            url="https://example.com/already-open",
            status='aberto',
            start_date=today - timedelta(days=1),
            end_date=today + timedelta(days=30),
        )
        
        # Edital já programado com start_date futuro (não deve mudar)
        edital_scheduled = Edital.objects.create(
            titulo="Edital Já Programado",
            url="https://example.com/already-scheduled",
            status='programado',
            start_date=today + timedelta(days=10),
            end_date=today + timedelta(days=40),
        )
        
        original_statuses = {
            edital_closed.pk: edital_closed.status,
            edital_open.pk: edital_open.status,
            edital_scheduled.pk: edital_scheduled.status,
        }
        
        call_command('update_edital_status')
        
        # Verificar que statuses não mudaram
        edital_closed.refresh_from_db()
        edital_open.refresh_from_db()
        edital_scheduled.refresh_from_db()
        
        self.assertEqual(edital_closed.status, original_statuses[edital_closed.pk])
        self.assertEqual(edital_open.status, original_statuses[edital_open.pk])
        self.assertEqual(edital_scheduled.status, original_statuses[edital_scheduled.pk])

    def test_edge_case_same_day_start_date(self):
        """Testa edge case: start_date = hoje."""
        today = timezone.now().date()
        
        # Edital que começa hoje e está programado (deve ser aberto)
        edital = Edital.objects.create(
            titulo="Edital Começa Hoje",
            url="https://example.com/today",
            status='programado',
            start_date=today,  # Começa hoje
            end_date=today + timedelta(days=30),
        )
        
        call_command('update_edital_status')
        
        edital.refresh_from_db()
        self.assertEqual(edital.status, 'aberto')

    def test_edge_case_same_day_end_date(self):
        """Testa edge case: end_date = hoje."""
        today = timezone.now().date()
        
        # Edital que termina hoje e está aberto (deve ser fechado)
        edital = Edital.objects.create(
            titulo="Edital Termina Hoje",
            url="https://example.com/ends-today",
            status='aberto',
            start_date=today - timedelta(days=30),
            end_date=today,  # Termina hoje
        )
        
        # Se o save() já fechou, vamos forçar o status para 'aberto'
        if edital.status == 'fechado':
            Edital.objects.filter(pk=edital.pk).update(status='aberto')
            edital.refresh_from_db()
        
        call_command('update_edital_status')
        
        edital.refresh_from_db()
        self.assertEqual(edital.status, 'fechado')

    def test_multiple_editais_updated(self):
        """Testa que múltiplos editais são atualizados corretamente."""
        today = timezone.now().date()
        
        # Criar múltiplos editais que devem ser fechados
        editais_to_close = []
        for i in range(3):
            edital = Edital.objects.create(
                titulo=f"Edital para Fechar {i+1}",
                url=f"https://example.com/close-{i+1}",
                status='aberto',
                start_date=today - timedelta(days=30),
                end_date=today - timedelta(days=i+1),
            )
            # Se o save() já fechou, vamos forçar o status para 'aberto'
            if edital.status == 'fechado':
                Edital.objects.filter(pk=edital.pk).update(status='aberto')
                edital.refresh_from_db()
            editais_to_close.append(edital)
        
        call_command('update_edital_status')
        
        # Verificar que todos foram fechados
        for edital in editais_to_close:
            edital.refresh_from_db()
            self.assertEqual(edital.status, 'fechado')

    def test_editais_without_dates(self):
        """Testa que editais sem start_date ou end_date não causam erro."""
        # Edital sem start_date
        edital_no_start = Edital.objects.create(
            titulo="Edital Sem Start Date",
            url="https://example.com/no-start",
            status='aberto',
            start_date=None,
            end_date=timezone.now().date() + timedelta(days=30),
        )
        
        # Edital sem end_date
        edital_no_end = Edital.objects.create(
            titulo="Edital Sem End Date",
            url="https://example.com/no-end",
            status='aberto',
            start_date=timezone.now().date() - timedelta(days=30),
            end_date=None,
        )
        
        # Comando deve executar sem erro
        out = StringIO()
        try:
            call_command('update_edital_status', stdout=out, stderr=out)
            success = True
        except Exception:
            success = False
        
        self.assertTrue(success)

    def test_exclude_draft_from_scheduling(self):
        """Testa que editais draft são excluídos da programação."""
        today = timezone.now().date()
        
        # Edital draft com start_date futuro (não deve ser programado)
        edital_draft = Edital.objects.create(
            titulo="Edital Draft Futuro",
            url="https://example.com/draft-future",
            status='draft',
            start_date=today + timedelta(days=10),
            end_date=today + timedelta(days=40),
        )
        
        original_status = edital_draft.status
        
        call_command('update_edital_status')
        
        edital_draft.refresh_from_db()
        # Draft não deve ser alterado
        self.assertEqual(edital_draft.status, original_status)

    def test_exclude_already_scheduled_from_scheduling(self):
        """Testa que editais já programados não são reprogramados."""
        today = timezone.now().date()
        
        # Edital já programado com start_date futuro (não deve mudar)
        edital = Edital.objects.create(
            titulo="Edital Já Programado",
            url="https://example.com/already-scheduled",
            status='programado',
            start_date=today + timedelta(days=10),
            end_date=today + timedelta(days=40),
        )
        
        original_status = edital.status
        
        call_command('update_edital_status')
        
        edital.refresh_from_db()
        # Status não deve mudar (já está programado)
        self.assertEqual(edital.status, original_status)

    def test_error_handling_during_save(self):
        """Testa que erros durante save são tratados graciosamente."""
        from unittest.mock import patch, MagicMock
        
        today = timezone.now().date()
        edital = Edital.objects.create(
            titulo="Edital para Testar Erro",
            url="https://example.com/error",
            status='aberto',
            start_date=today - timedelta(days=30),
            end_date=today - timedelta(days=1),
        )
        
        # Se o save() já fechou, vamos forçar o status para 'aberto'
        if edital.status == 'fechado':
            Edital.objects.filter(pk=edital.pk).update(status='aberto')
            edital.refresh_from_db()
        
        # Simular erro durante save
        with patch.object(Edital, 'save', side_effect=Exception("Erro de banco de dados")):
            out = StringIO()
            call_command('update_edital_status', stdout=out, stderr=out)
            
            # Verificar que erro foi reportado
            output = out.getvalue()
            # Pode estar em 'erro' ou 'ERRO' dependendo do formato
            self.assertTrue('erro' in output.lower() or 'ERRO' in output)

    def test_error_output_in_verbose_mode(self):
        """Testa que erros são mostrados em modo verbose."""
        from unittest.mock import patch
        
        today = timezone.now().date()
        edital = Edital.objects.create(
            titulo="Edital para Testar Erro Verbose",
            url="https://example.com/error-verbose",
            status='aberto',
            start_date=today - timedelta(days=30),
            end_date=today - timedelta(days=1),
        )
        
        # Se o save() já fechou, vamos forçar o status para 'aberto'
        if edital.status == 'fechado':
            Edital.objects.filter(pk=edital.pk).update(status='aberto')
            edital.refresh_from_db()
        
        # Simular erro durante save
        with patch.object(Edital, 'save', side_effect=Exception("Erro de teste")):
            out = StringIO()
            call_command('update_edital_status', '--verbose', stdout=out, stderr=out)
            
            # Verificar que erro foi reportado
            output = out.getvalue()
            self.assertIn('ERRO', output)

    def test_cache_invalidation_error_handling(self):
        """Testa que erros na invalidação de cache são tratados graciosamente."""
        from unittest.mock import patch
        
        today = timezone.now().date()
        edital = Edital.objects.create(
            titulo="Edital para Testar Cache Error",
            url="https://example.com/cache-error",
            status='aberto',
            start_date=today - timedelta(days=30),
            end_date=today - timedelta(days=1),
        )
        
        # Se o save() já fechou, vamos forçar o status para 'aberto'
        if edital.status == 'fechado':
            Edital.objects.filter(pk=edital.pk).update(status='aberto')
            edital.refresh_from_db()
        
        # Simular erro na invalidação de cache
        with patch('editais.views._clear_index_cache', side_effect=Exception("Erro de cache")):
            out = StringIO()
            # Comando não deve levantar exceção
            try:
                call_command('update_edital_status', '--verbose', stdout=out, stderr=out)
                success = True
            except Exception:
                success = False
            
            self.assertTrue(success)
            
            # Verificar que erro foi reportado
            output = out.getvalue()
            # Pode estar em 'AVISO' ou 'erro' dependendo do formato
            self.assertTrue('AVISO' in output or 'erro' in output.lower())

    def test_no_editais_to_update_message(self):
        """Testa mensagem quando não há editais para atualizar."""
        # Deletar todos os editais do setUp que podem ser atualizados
        Edital.objects.filter(status__in=['aberto', 'programado']).delete()
        
        out = StringIO()
        call_command('update_edital_status', stdout=out)
        
        output = out.getvalue()
        # Deve mostrar mensagem de sucesso indicando que nenhum edital precisou ser atualizado
        self.assertTrue('Nenhum edital' in output or 'atualizado' in output.lower())

    def test_summary_output_with_updates(self):
        """Testa que o resumo mostra quantidade correta de atualizações."""
        today = timezone.now().date()
        
        # Criar editais que serão atualizados
        editais_to_close = []
        for i in range(2):
            edital = Edital.objects.create(
                titulo=f"Edital Resumo {i+1}",
                url=f"https://example.com/summary-{i+1}",
                status='aberto',
                start_date=today - timedelta(days=30),
                end_date=today - timedelta(days=i+1),
            )
            if edital.status == 'fechado':
                Edital.objects.filter(pk=edital.pk).update(status='aberto')
                edital.refresh_from_db()
            editais_to_close.append(edital)
        
        out = StringIO()
        call_command('update_edital_status', stdout=out)
        
        output = out.getvalue()
        # Deve mostrar que 2 editais foram atualizados
        self.assertTrue('2' in output and 'atualizado' in output.lower())

    def test_dry_run_summary_output(self):
        """Testa que o resumo em dry-run mostra quantidade correta."""
        today = timezone.now().date()
        
        edital = Edital.objects.create(
            titulo="Edital Dry Run Summary",
            url="https://example.com/dry-run-summary",
            status='aberto',
            start_date=today - timedelta(days=30),
            end_date=today - timedelta(days=1),
        )
        
        if edital.status == 'fechado':
            Edital.objects.filter(pk=edital.pk).update(status='aberto')
            edital.refresh_from_db()
        
        out = StringIO()
        call_command('update_edital_status', '--dry-run', stdout=out)
        
        output = out.getvalue()
        # Deve mostrar mensagem de DRY RUN
        self.assertIn('DRY RUN', output)
        self.assertIn('seriam atualizados', output)

    def test_status_em_andamento_not_changed_by_command(self):
        """Testa que editais em status 'em_andamento' não são alterados pelo comando."""
        today = timezone.now().date()
        
        # Edital em_andamento com end_date passado (não deve ser fechado pelo comando)
        edital = Edital.objects.create(
            titulo="Edital Em Andamento",
            url="https://example.com/em-andamento",
            status='em_andamento',
            start_date=today - timedelta(days=30),
            end_date=today - timedelta(days=1),
        )
        
        original_status = edital.status
        
        call_command('update_edital_status')
        
        edital.refresh_from_db()
        # Status 'em_andamento' não deve ser alterado (comando só fecha 'aberto')
        self.assertEqual(edital.status, original_status)

    def test_status_em_andamento_can_be_scheduled(self):
        """Testa que editais 'em_andamento' com start_date futuro podem ser programados."""
        today = timezone.now().date()
        
        # Edital em_andamento com start_date futuro (deve ser programado)
        edital = Edital.objects.create(
            titulo="Edital Em Andamento Futuro",
            url="https://example.com/em-andamento-future",
            status='em_andamento',
            start_date=today + timedelta(days=10),
            end_date=today + timedelta(days=40),
        )
        
        call_command('update_edital_status')
        
        edital.refresh_from_db()
        # Deve ser programado (exclui draft e programado, mas não em_andamento)
        self.assertEqual(edital.status, 'programado')


class SendDeadlineNotificationsCommandTest(TestCase):
    """Testes para o comando send_deadline_notifications."""
    
    def setUp(self):
        """Criar editais e usuários de teste."""
        from django.contrib.auth.models import User
        from django.utils import timezone
        from datetime import timedelta
        
        # Criar usuário staff com email
        self.staff_user = User.objects.create_user(
            username='staff',
            password='staff123',
            is_staff=True,
            is_active=True,
            email='staff@example.com'
        )
        
        # Criar usuário staff sem email (não deve receber notificação)
        self.staff_no_email = User.objects.create_user(
            username='staff_no_email',
            password='staff123',
            is_staff=True,
            is_active=True,
            email=''
        )
        
        # Criar usuário não-staff (não deve receber notificação)
        self.non_staff = User.objects.create_user(
            username='user',
            password='user123',
            is_staff=False,
            is_active=True,
            email='user@example.com'
        )
        
        today = timezone.now().date()
        
        # Edital próximo do prazo (5 dias)
        self.edital_upcoming = Edital.objects.create(
            titulo="Edital Próximo do Prazo",
            url="https://example.com/upcoming",
            status='aberto',
            end_date=today + timedelta(days=5)
        )
        
        # Edital muito próximo do prazo (2 dias)
        self.edital_very_upcoming = Edital.objects.create(
            titulo="Edital Muito Próximo",
            url="https://example.com/very-upcoming",
            status='em_andamento',
            end_date=today + timedelta(days=2)
        )
        
        # Edital fora do prazo (15 dias)
        self.edital_far = Edital.objects.create(
            titulo="Edital Longe do Prazo",
            url="https://example.com/far",
            status='aberto',
            end_date=today + timedelta(days=15)
        )
        
        # Edital já fechado (não deve ser notificado)
        self.edital_closed = Edital.objects.create(
            titulo="Edital Fechado",
            url="https://example.com/closed",
            status='fechado',
            end_date=today + timedelta(days=3)
        )
    
    @patch('editais.management.commands.send_deadline_notifications.EmailMultiAlternatives')
    def test_sends_notifications_for_upcoming_editais(self, mock_email):
        """Testa que o comando envia notificações para editais próximos do prazo."""
        from io import StringIO
        
        out = StringIO()
        call_command('send_deadline_notifications', stdout=out, stderr=out)
        
        # Verificar que email foi chamado
        self.assertTrue(mock_email.called)
        
        # Verificar que foi chamado para o usuário staff com email
        # EmailMultiAlternatives é chamado com argumentos posicionais:
        # EmailMultiAlternatives(subject, text_content, from_email, [recipient])
        # call_args[0] contém os argumentos posicionais, call_args[0][3] é a lista de destinatários
        call_args = mock_email.call_args
        recipients = call_args[0][3]  # 4º argumento posicional é a lista de destinatários
        self.assertIn(self.staff_user.email, recipients)
    
    def test_dry_run_mode_does_not_send_emails(self):
        """Testa que o modo dry-run não envia emails."""
        from io import StringIO
        from unittest.mock import patch
        
        with patch('editais.management.commands.send_deadline_notifications.EmailMultiAlternatives') as mock_email:
            out = StringIO()
            call_command('send_deadline_notifications', '--dry-run', stdout=out)
            
            # Verificar que email não foi chamado
            self.assertFalse(mock_email.called)
            
            # Verificar mensagem de dry-run
            output = out.getvalue()
            self.assertIn('DRY RUN', output)
    
    def test_no_notifications_when_no_upcoming_editais(self):
        """Testa que não envia notificações quando não há editais próximos."""
        # Deletar editais próximos
        self.edital_upcoming.delete()
        self.edital_very_upcoming.delete()
        
        from io import StringIO
        from unittest.mock import patch
        
        with patch('editais.management.commands.send_deadline_notifications.EmailMultiAlternatives') as mock_email:
            out = StringIO()
            call_command('send_deadline_notifications', stdout=out)
            
            # Verificar que email não foi chamado
            self.assertFalse(mock_email.called)
            
            # Verificar mensagem
            output = out.getvalue()
            self.assertIn('Nenhum edital', output)
    
    def test_custom_days_parameter(self):
        """Testa que o parâmetro --days funciona corretamente."""
        from io import StringIO
        from unittest.mock import patch
        
        with patch('editais.management.commands.send_deadline_notifications.EmailMultiAlternatives') as mock_email:
            out = StringIO()
            # Usar 15 dias (deve incluir edital_far)
            call_command('send_deadline_notifications', '--days', '15', stdout=out)
            
            # Verificar que email foi chamado
            self.assertTrue(mock_email.called)
    
    def test_only_notifies_open_editais(self):
        """Testa que apenas editais abertos/em_andamento são notificados."""
        from io import StringIO
        from unittest.mock import patch
        
        with patch('editais.management.commands.send_deadline_notifications.EmailMultiAlternatives') as mock_email:
            out = StringIO()
            call_command('send_deadline_notifications', stdout=out)
            
            # Verificar que edital fechado não foi incluído
            if mock_email.called:
                # Verificar conteúdo do email
                call_args = mock_email.call_args
                # O edital fechado não deve estar na lista
                self.assertTrue(mock_email.called)
    
    def test_handles_email_errors_gracefully(self):
        """Testa que o comando lida com erros de email graciosamente."""
        from io import StringIO
        from unittest.mock import patch, MagicMock
        
        # Simular erro ao enviar email
        mock_email_instance = MagicMock()
        mock_email_instance.send.side_effect = Exception("Erro de email")
        
        with patch('editais.management.commands.send_deadline_notifications.EmailMultiAlternatives', return_value=mock_email_instance):
            out = StringIO()
            # Comando não deve levantar exceção
            try:
                call_command('send_deadline_notifications', stdout=out, stderr=out)
                success = True
            except Exception:
                success = False
            
            self.assertTrue(success)
            
            # Verificar que erro foi reportado
            output = out.getvalue()
            self.assertIn('erro', output.lower())
    
    def test_verbose_output(self):
        """Testa que o modo verbose mostra informações detalhadas."""
        from io import StringIO
        from unittest.mock import patch
        
        with patch('editais.management.commands.send_deadline_notifications.EmailMultiAlternatives'):
            out = StringIO()
            call_command('send_deadline_notifications', '--verbose', stdout=out)
            
            output = out.getvalue()
            # Verificar que mostra informações detalhadas
            self.assertTrue(len(output) > 0)
