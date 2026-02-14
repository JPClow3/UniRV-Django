"""
Tests for management commands.
"""

from datetime import date, timedelta
from io import StringIO

import pytest

from django.core.management import call_command
from django.utils import timezone

from editais.models import Edital


@pytest.mark.django_db
class TestUpdateEditalStatusCommand:
    """Tests for the update_edital_status management command"""

    @pytest.fixture(autouse=True)
    def _setup(self):
        today = timezone.now().date()

        self.edital_to_close = Edital.objects.create(
            titulo="Edital para Fechar",
            url="https://example.com/close",
            status="aberto",
            start_date=today - timedelta(days=30),
            end_date=today - timedelta(days=1),
        )
        Edital.objects.filter(pk=self.edital_to_close.pk).update(status="aberto")
        self.edital_to_close.refresh_from_db()

        self.edital_to_schedule = Edital.objects.create(
            titulo="Edital para Programar",
            url="https://example.com/schedule",
            status="aberto",
            start_date=today + timedelta(days=10),
            end_date=today + timedelta(days=40),
        )
        Edital.objects.filter(pk=self.edital_to_schedule.pk).update(status="aberto")
        self.edital_to_schedule.refresh_from_db()

        self.edital_to_open = Edital.objects.create(
            titulo="Edital para Abrir",
            url="https://example.com/open",
            status="programado",
            start_date=today - timedelta(days=1),
            end_date=today + timedelta(days=30),
        )
        Edital.objects.filter(pk=self.edital_to_open.pk).update(status="programado")
        self.edital_to_open.refresh_from_db()

        self.edital_draft = Edital.objects.create(
            titulo="Edital Rascunho",
            url="https://example.com/draft",
            status="draft",
            start_date=today + timedelta(days=5),
            end_date=today + timedelta(days=35),
        )

        self.edital_closed = Edital.objects.create(
            titulo="Edital Fechado",
            url="https://example.com/closed",
            status="fechado",
            start_date=today - timedelta(days=60),
            end_date=today - timedelta(days=30),
        )

    def test_close_editais_with_past_end_date(self):
        today = timezone.now().date()
        edital = Edital.objects.create(
            titulo="Edital para Fechar Manualmente",
            url="https://example.com/close-manual",
            status="aberto",
            start_date=today - timedelta(days=30),
            end_date=today - timedelta(days=1),
        )
        if edital.status == "fechado":
            Edital.objects.filter(pk=edital.pk).update(status="aberto")
            edital.refresh_from_db()

        assert edital.status == "aberto"
        call_command("update_edital_status")
        edital.refresh_from_db()
        assert edital.status == "fechado"

    def test_schedule_editais_with_future_start_date(self):
        assert self.edital_to_schedule.status == "aberto"
        call_command("update_edital_status")
        self.edital_to_schedule.refresh_from_db()
        assert self.edital_to_schedule.status == "programado"

    def test_open_editais_with_current_dates(self):
        assert self.edital_to_open.status == "programado"
        call_command("update_edital_status")
        self.edital_to_open.refresh_from_db()
        assert self.edital_to_open.status == "aberto"

    def test_draft_editais_not_changed(self):
        original_status = self.edital_draft.status
        call_command("update_edital_status")
        self.edital_draft.refresh_from_db()
        assert self.edital_draft.status == original_status

    def test_closed_editais_not_changed(self):
        original_status = self.edital_closed.status
        call_command("update_edital_status")
        self.edital_closed.refresh_from_db()
        assert self.edital_closed.status == original_status

    def test_dry_run_mode(self):
        original_status = self.edital_to_close.status
        out = StringIO()
        call_command("update_edital_status", "--dry-run", stdout=out)
        self.edital_to_close.refresh_from_db()
        assert self.edital_to_close.status == original_status
        assert "DRY RUN" in out.getvalue()

    def test_verbose_output(self):
        out = StringIO()
        call_command("update_edital_status", "--verbose", stdout=out)
        output = out.getvalue()
        assert (
            "Fechando edital" in output
            or "Programando edital" in output
            or "Abrindo edital" in output
        )

    def test_command_handles_errors_gracefully(self):
        Edital.objects.create(
            titulo="Edital com Problema",
            url="https://example.com/problem",
            status="aberto",
            start_date=timezone.now().date() - timedelta(days=10),
            end_date=timezone.now().date() - timedelta(days=5),
        )
        out = StringIO()
        try:
            call_command("update_edital_status", stdout=out, stderr=out)
            success = True
        except Exception:
            success = False
        assert success

    def test_editais_already_in_correct_status(self):
        today = timezone.now().date()

        edital_closed = Edital.objects.create(
            titulo="Edital Já Fechado",
            url="https://example.com/already-closed",
            status="fechado",
            start_date=today - timedelta(days=30),
            end_date=today - timedelta(days=1),
        )

        edital_open = Edital.objects.create(
            titulo="Edital Já Aberto",
            url="https://example.com/already-open",
            status="aberto",
            start_date=today - timedelta(days=1),
            end_date=today + timedelta(days=30),
        )

        edital_scheduled = Edital.objects.create(
            titulo="Edital Já Programado",
            url="https://example.com/already-scheduled",
            status="programado",
            start_date=today + timedelta(days=10),
            end_date=today + timedelta(days=40),
        )

        original_statuses = {
            edital_closed.pk: edital_closed.status,
            edital_open.pk: edital_open.status,
            edital_scheduled.pk: edital_scheduled.status,
        }

        call_command("update_edital_status")

        edital_closed.refresh_from_db()
        edital_open.refresh_from_db()
        edital_scheduled.refresh_from_db()

        assert edital_closed.status == original_statuses[edital_closed.pk]
        assert edital_open.status == original_statuses[edital_open.pk]
        assert edital_scheduled.status == original_statuses[edital_scheduled.pk]

    def test_edge_case_same_day_start_date(self):
        today = timezone.now().date()
        edital = Edital.objects.create(
            titulo="Edital Começa Hoje",
            url="https://example.com/today",
            status="programado",
            start_date=today,
            end_date=today + timedelta(days=30),
        )
        call_command("update_edital_status")
        edital.refresh_from_db()
        assert edital.status == "aberto"

    def test_edge_case_same_day_end_date(self):
        today = timezone.now().date()
        edital = Edital.objects.create(
            titulo="Edital Termina Hoje",
            url="https://example.com/ends-today",
            status="aberto",
            start_date=today - timedelta(days=30),
            end_date=today,
        )
        if edital.status == "fechado":
            Edital.objects.filter(pk=edital.pk).update(status="aberto")
            edital.refresh_from_db()

        call_command("update_edital_status")
        edital.refresh_from_db()
        assert edital.status == "fechado"

    def test_multiple_editais_updated(self):
        today = timezone.now().date()
        editais_to_close = []
        for i in range(3):
            edital = Edital.objects.create(
                titulo=f"Edital para Fechar {i+1}",
                url=f"https://example.com/close-{i+1}",
                status="aberto",
                start_date=today - timedelta(days=30),
                end_date=today - timedelta(days=i + 1),
            )
            if edital.status == "fechado":
                Edital.objects.filter(pk=edital.pk).update(status="aberto")
                edital.refresh_from_db()
            editais_to_close.append(edital)

        call_command("update_edital_status")

        for edital in editais_to_close:
            edital.refresh_from_db()
            assert edital.status == "fechado"

    def test_editais_without_dates(self):
        Edital.objects.create(
            titulo="Edital Sem Start Date",
            url="https://example.com/no-start",
            status="aberto",
            start_date=None,
            end_date=timezone.now().date() + timedelta(days=30),
        )

        Edital.objects.create(
            titulo="Edital Sem End Date",
            url="https://example.com/no-end",
            status="aberto",
            start_date=timezone.now().date() - timedelta(days=30),
            end_date=None,
        )

        out = StringIO()
        try:
            call_command("update_edital_status", stdout=out, stderr=out)
            success = True
        except Exception:
            success = False

        assert success

    def test_exclude_draft_from_scheduling(self):
        today = timezone.now().date()
        edital_draft = Edital.objects.create(
            titulo="Edital Draft Futuro",
            url="https://example.com/draft-future",
            status="draft",
            start_date=today + timedelta(days=10),
            end_date=today + timedelta(days=40),
        )

        original_status = edital_draft.status
        call_command("update_edital_status")
        edital_draft.refresh_from_db()
        assert edital_draft.status == original_status

    def test_exclude_already_scheduled_from_scheduling(self):
        today = timezone.now().date()
        edital = Edital.objects.create(
            titulo="Edital Já Programado",
            url="https://example.com/already-scheduled",
            status="programado",
            start_date=today + timedelta(days=10),
            end_date=today + timedelta(days=40),
        )

        original_status = edital.status
        call_command("update_edital_status")
        edital.refresh_from_db()
        assert edital.status == original_status
