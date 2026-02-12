"""
Testes para funcionalidades administrativas do app editais.
"""

import pytest
from datetime import timedelta
from unittest.mock import MagicMock

from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone

from editais.models import Edital


@pytest.mark.django_db
class TestEditalAdmin:
    """Testes para interface administrativa de editais."""

    @pytest.fixture(autouse=True)
    def _setup(self, client):
        self.admin = User.objects.create_user(
            username="admin", password="admin123", is_staff=True, is_superuser=True
        )
        client.login(username="admin", password="admin123")
        cache.clear()

        self.edital1 = Edital.objects.create(
            titulo="Edital Aberto",
            url="https://example.com/1",
            status="aberto",
            entidade_principal="CNPq",
            numero_edital="001/2025",
        )
        self.edital2 = Edital.objects.create(
            titulo="Edital Fechado",
            url="https://example.com/2",
            status="fechado",
            entidade_principal="FAPEG",
            numero_edital="002/2025",
        )
        self.edital3 = Edital.objects.create(
            titulo="Edital Programado",
            url="https://example.com/3",
            status="programado",
            entidade_principal="SEBRAE",
            numero_edital="003/2025",
            start_date=timezone.now().date() + timedelta(days=10),
        )

    def test_admin_can_access_create_page(self, client):
        resp = client.get(reverse("edital_create"))
        assert resp.status_code == 200

    def test_admin_can_create_edital(self, client):
        data = {
            "titulo": "Novo Edital",
            "url": "https://example.com/new",
            "status": "aberto",
            "numero_edital": "004/2025",
            "entidade_principal": "CNPq",
            "objetivo": "Objetivo do novo edital",
        }
        resp = client.post(reverse("edital_create"), data=data)
        assert resp.status_code == 302
        assert Edital.objects.filter(titulo="Novo Edital").exists()

    def test_admin_can_access_update_page(self, client):
        resp = client.get(reverse("edital_update", args=[self.edital1.pk]))
        assert resp.status_code == 200

    def test_admin_can_update_edital(self, client):
        data = {
            "titulo": "Edital Atualizado",
            "url": self.edital1.url,
            "status": "fechado",
            "numero_edital": self.edital1.numero_edital,
            "entidade_principal": self.edital1.entidade_principal,
        }
        resp = client.post(reverse("edital_update", args=[self.edital1.pk]), data=data)
        assert resp.status_code == 302
        self.edital1.refresh_from_db()
        assert self.edital1.titulo == "Edital Atualizado"
        assert self.edital1.status == "fechado"

    def test_admin_can_access_delete_page(self, client):
        resp = client.get(reverse("edital_delete", args=[self.edital1.pk]))
        assert resp.status_code == 200
        assert self.edital1.titulo in resp.content.decode()

    def test_admin_can_delete_edital(self, client):
        edital = Edital.objects.create(
            titulo="Edital para Deletar", url="https://example.com/delete"
        )
        resp = client.post(reverse("edital_delete", args=[edital.pk]))
        assert resp.status_code == 302
        assert not Edital.objects.filter(pk=edital.pk).exists()

    def test_admin_can_view_draft_edital(self, client):
        edital_draft = Edital.objects.create(
            titulo="Edital Draft", url="https://example.com/draft", status="draft"
        )
        if edital_draft.slug:
            resp = client.get(
                reverse("edital_detail_slug", kwargs={"slug": edital_draft.slug})
            )
            assert resp.status_code == 200

    def test_slug_not_editable(self, client):
        original_slug = self.edital1.slug
        data = {
            "titulo": "Título Atualizado",
            "url": self.edital1.url,
            "status": self.edital1.status,
            "numero_edital": self.edital1.numero_edital,
            "entidade_principal": self.edital1.entidade_principal,
        }
        client.post(reverse("edital_update", args=[self.edital1.pk]), data=data)
        self.edital1.refresh_from_db()
        assert self.edital1.slug == original_slug

    def test_admin_save_model_sanitizes_html(self):
        from editais.admin import EditalAdmin

        admin = EditalAdmin(Edital, None)
        edital = Edital(
            titulo="Teste XSS",
            url="https://example.com/test",
            analise='<script>alert("XSS")</script>Texto normal',
            objetivo="<img src=x onerror=alert(1)>",
        )
        mock_request = MagicMock()
        mock_request.user = self.admin
        admin.save_model(mock_request, edital, None, change=False)

        assert "<script>" not in edital.analise
        assert "onerror" not in edital.objetivo
        assert "Texto normal" in edital.analise

    def test_admin_save_model_tracks_created_by(self):
        from editais.admin import EditalAdmin

        admin = EditalAdmin(Edital, None)
        edital = Edital(titulo="Teste Created By", url="https://example.com/test")
        mock_request = MagicMock()
        mock_request.user = self.admin
        admin.save_model(mock_request, edital, None, change=False)
        assert edital.created_by == self.admin

    def test_admin_save_model_tracks_updated_by(self):
        from editais.admin import EditalAdmin

        admin = EditalAdmin(Edital, None)
        edital = Edital.objects.create(
            titulo="Teste Updated By", url="https://example.com/test"
        )
        mock_request = MagicMock()
        mock_request.user = self.admin
        admin.save_model(mock_request, edital, None, change=True)
        assert edital.updated_by == self.admin

    def test_created_by_tracked(self, client):
        data = {
            "titulo": "Edital com Rastreamento",
            "url": "https://example.com/track",
            "status": "aberto",
        }
        client.post(reverse("edital_create"), data=data)
        edital = Edital.objects.get(titulo="Edital com Rastreamento")
        assert edital.created_by == self.admin
        assert edital.updated_by == self.admin

    def test_updated_by_tracked(self, client):
        data = {
            "titulo": self.edital1.titulo,
            "url": self.edital1.url,
            "status": "fechado",
            "numero_edital": self.edital1.numero_edital,
            "entidade_principal": self.edital1.entidade_principal,
        }
        client.post(reverse("edital_update", args=[self.edital1.pk]), data=data)
        self.edital1.refresh_from_db()
        assert self.edital1.updated_by == self.admin


@pytest.mark.django_db
class TestEditalAdminFilters:
    """Testes para filtros administrativos."""

    @pytest.fixture(autouse=True)
    def _setup(self, client):
        self.admin = User.objects.create_user(
            username="admin", password="admin123", is_staff=True, is_superuser=True
        )
        client.login(username="admin", password="admin123")

        self.edital_aberto = Edital.objects.create(
            titulo="Edital Aberto",
            url="https://example.com/aberto",
            status="aberto",
            entidade_principal="CNPq",
        )
        self.edital_fechado = Edital.objects.create(
            titulo="Edital Fechado",
            url="https://example.com/fechado",
            status="fechado",
            entidade_principal="FAPEG",
        )
        self.edital_programado = Edital.objects.create(
            titulo="Edital Programado",
            url="https://example.com/programado",
            status="programado",
            entidade_principal="SEBRAE",
        )

    def test_admin_can_search_by_title(self, client):
        resp = client.get(reverse("editais_index"), {"search": "Aberto"})
        assert resp.status_code == 200
        assert self.edital_aberto.titulo in resp.content.decode()

    def test_admin_can_filter_by_status(self, client):
        resp = client.get(reverse("editais_index"), {"status": "aberto"})
        assert resp.status_code == 200
        content = resp.content.decode()
        assert self.edital_aberto.titulo in content
        assert self.edital_fechado.titulo not in content

    def test_admin_can_filter_by_entity(self, client):
        resp = client.get(reverse("editais_index"), {"search": "CNPq"})
        assert resp.status_code == 200
        assert self.edital_aberto.titulo in resp.content.decode()

    def test_admin_can_filter_by_start_date(self, client):
        today = timezone.now().date()
        edital_future = Edital.objects.create(
            titulo="Edital Futuro",
            url="https://example.com/future",
            status="aberto",
            start_date=today + timedelta(days=30),
        )
        resp = client.get(
            reverse("editais_index"),
            {"start_date": today.strftime("%Y-%m-%d")},
        )
        assert resp.status_code == 200
        assert edital_future.titulo in resp.content.decode()

    def test_admin_can_filter_by_end_date(self, client):
        today = timezone.now().date()
        edital_past = Edital.objects.create(
            titulo="Edital Passado",
            url="https://example.com/past",
            status="fechado",
            end_date=today - timedelta(days=10),
        )
        resp = client.get(
            reverse("editais_index"),
            {"end_date": today.strftime("%Y-%m-%d")},
        )
        assert resp.status_code == 200
        assert edital_past.titulo in resp.content.decode()

    def test_admin_can_combine_search_and_filters(self, client):
        resp = client.get(
            reverse("editais_index"), {"search": "Edital", "status": "aberto"}
        )
        assert resp.status_code == 200
        content = resp.content.decode()
        assert self.edital_aberto.titulo in content
        assert self.edital_fechado.titulo not in content

    def test_pagination_works(self, client):
        for i in range(15):
            Edital.objects.create(
                titulo=f"Edital {i}",
                url=f"https://example.com/{i}",
                status="aberto",
            )
        resp = client.get(reverse("editais_index"))
        assert resp.status_code == 200
        page_obj = resp.context["page_obj"]
        assert page_obj.paginator.num_pages > 1
        assert len(page_obj.object_list) == 12

        resp = client.get(reverse("editais_index"), {"page": "2"})
        assert resp.status_code == 200
        page_obj = resp.context["page_obj"]
        assert len(page_obj.object_list) > 0
        assert len(page_obj.object_list) <= 12

    def test_pagination_preserves_filters(self, client):
        for i in range(15):
            Edital.objects.create(
                titulo=f"Edital Aberto {i}",
                url=f"https://example.com/aberto-{i}",
                status="aberto",
            )
        resp = client.get(reverse("editais_index"), {"status": "aberto", "page": "2"})
        assert resp.status_code == 200
        page_obj = resp.context["page_obj"]
        for edital in page_obj.object_list:
            assert edital.status == "aberto"

    def test_pagination_invalid_page_returns_last_page(self, client):
        for i in range(5):
            Edital.objects.create(
                titulo=f"Edital {i}",
                url=f"https://example.com/{i}",
                status="aberto",
            )
        resp = client.get(reverse("editais_index"), {"page": "999"})
        assert resp.status_code == 200
        page_obj = resp.context["page_obj"]
        assert page_obj.number == page_obj.paginator.num_pages


@pytest.mark.django_db
class TestAdminDashboard:
    """Testes para o dashboard administrativo."""

    @pytest.fixture(autouse=True)
    def _setup(self, client):
        self.staff_user = User.objects.create_user(
            username="staff",
            password="staff123",
            is_staff=True,
            email="staff@example.com",
        )
        self.non_staff_user = User.objects.create_user(
            username="user",
            password="user123",
            is_staff=False,
            email="user@example.com",
        )
        cache.clear()

        self.edital1 = Edital.objects.create(
            titulo="Edital Aberto",
            url="https://example.com/1",
            status="aberto",
            entidade_principal="CNPq",
            numero_edital="001/2025",
            created_by=self.staff_user,
        )
        self.edital2 = Edital.objects.create(
            titulo="Edital Fechado",
            url="https://example.com/2",
            status="fechado",
            entidade_principal="FAPEG",
            numero_edital="002/2025",
        )

    def test_staff_can_access_dashboard(self, client):
        client.login(username="staff", password="staff123")
        resp = client.get(reverse("admin_dashboard"))
        assert resp.status_code == 200
        assert "Dashboard Administrativo" in resp.content.decode()

    def test_non_staff_cannot_access_dashboard(self, client):
        client.login(username="user", password="user123")
        resp = client.get(reverse("admin_dashboard"))
        assert resp.status_code == 403

    def test_unauthenticated_cannot_access_dashboard(self, client):
        client.logout()
        resp = client.get(reverse("admin_dashboard"))
        assert resp.status_code == 302
        assert "/login/" in resp.url

    def test_dashboard_shows_editais_por_status(self, client):
        client.login(username="staff", password="staff123")
        resp = client.get(reverse("admin_dashboard"))
        content = resp.content.decode()
        assert "aberto" in content
        assert "fechado" in content

    def test_dashboard_shows_recent_editais(self, client):
        recent_edital = Edital.objects.create(
            titulo="Edital Recente",
            url="https://example.com/recent",
            status="aberto",
            data_criacao=timezone.now() - timedelta(days=3),
        )
        client.login(username="staff", password="staff123")
        resp = client.get(reverse("admin_dashboard"))
        assert recent_edital.titulo in resp.content.decode()

    def test_dashboard_shows_upcoming_deadlines(self, client):
        today = timezone.now().date()
        upcoming = Edital.objects.create(
            titulo="Edital Próximo do Prazo",
            url="https://example.com/upcoming",
            status="aberto",
            end_date=today + timedelta(days=5),
        )
        client.login(username="staff", password="staff123")
        resp = client.get(reverse("admin_dashboard"))
        assert upcoming.titulo in resp.content.decode()

    def test_dashboard_shows_top_entidades(self, client):
        Edital.objects.create(
            titulo="Edital CNPq 1",
            url="https://example.com/cnpq1",
            status="aberto",
            entidade_principal="CNPq",
        )
        Edital.objects.create(
            titulo="Edital CNPq 2",
            url="https://example.com/cnpq2",
            status="aberto",
            entidade_principal="CNPq",
        )
        client.login(username="staff", password="staff123")
        resp = client.get(reverse("admin_dashboard"))
        assert "CNPq" in resp.content.decode()
