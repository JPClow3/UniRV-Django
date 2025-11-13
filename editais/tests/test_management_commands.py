"""
Testes para management commands do app editais.
"""

from datetime import date, timedelta
from django.test import TestCase
from django.core.management import call_command
from django.utils import timezone
from io import StringIO
from editais.models import Edital


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

