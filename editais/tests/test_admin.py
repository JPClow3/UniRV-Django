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
    def _setup(self, client, staff_user):
        self.client = client
        self.staff_user = staff_user
        self.client.force_login(staff_user)
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

    def test_admin_can_access_create_page(self):
        resp = self.client.get(reverse("edital_create"))
        assert resp.status_code == 200

    def test_admin_can_create_edital(self):
        data = {
            "titulo": "Novo Edital",
            "url": "https://example.com/new",
            "status": "aberto",
            "numero_edital": "004/2025",
            "entidade_principal": "CNPq",
            "objetivo": "Objetivo do novo edital",
        }
        resp = self.client.post(reverse("edital_create"), data=data)
        assert resp.status_code == 302
        assert Edital.objects.filter(titulo="Novo Edital").exists()

    def test_admin_can_access_update_page(self):
        resp = self.client.get(reverse("edital_update", args=[self.edital1.pk]))
        assert resp.status_code == 200

    def test_admin_can_update_edital(self):
        data = {
            "titulo": "Edital Atualizado",
            "url": self.edital1.url,
            "status": "fechado",
            "numero_edital": self.edital1.numero_edital,
            "entidade_principal": self.edital1.entidade_principal,
        }
        resp = self.client.post(reverse("edital_update", args=[self.edital1.pk]), data=data)
        assert resp.status_code == 302
        self.edital1.refresh_from_db()
        assert self.edital1.titulo == "Edital Atualizado"
        assert self.edital1.status == "fechado"

    def test_admin_can_access_delete_page(self):
        resp = self.client.get(reverse("edital_delete", args=[self.edital1.pk]))
        assert resp.status_code == 200
        assert self.edital1.titulo in resp.content.decode()

    def test_admin_can_delete_edital(self):
        edital = Edital.objects.create(
            titulo="Edital para Deletar", url="https://example.com/delete"
        )
        resp = self.client.post(reverse("edital_delete", args=[edital.pk]))
        assert resp.status_code == 302
        assert not Edital.objects.filter(pk=edital.pk).exists()

    def test_admin_can_view_draft_edital(self):
        edital_draft = Edital.objects.create(
            titulo="Edital Draft", url="https://example.com/draft", status="draft"
        )
        if edital_draft.slug:
            resp = self.client.get(
                reverse("edital_detail_slug", kwargs={"slug": edital_draft.slug})
            )
            assert resp.status_code == 200

    def test_slug_not_editable(self):
        original_slug = self.edital1.slug
        data = {
            "titulo": "Título Atualizado",
            "url": self.edital1.url,
            "status": self.edital1.status,
            "numero_edital": self.edital1.numero_edital,
            "entidade_principal": self.edital1.entidade_principal,
        }
        self.client.post(reverse("edital_update", args=[self.edital1.pk]), data=data)
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
        mock_request.user = self.staff_user
        admin.save_model(mock_request, edital, None, change=False)

        assert "<script>" not in edital.analise
        assert "onerror" not in edital.objetivo
        assert "Texto normal" in edital.analise

    def test_admin_save_model_tracks_created_by(self):
        from editais.admin import EditalAdmin

        admin = EditalAdmin(Edital, None)
        edital = Edital(titulo="Teste Created By", url="https://example.com/test")
        mock_request = MagicMock()
        mock_request.user = self.staff_user
        admin.save_model(mock_request, edital, None, change=False)
        assert edital.created_by == self.staff_user

    def test_admin_save_model_tracks_updated_by(self):
        from editais.admin import EditalAdmin

        admin = EditalAdmin(Edital, None)
        edital = Edital.objects.create(
            titulo="Teste Updated By", url="https://example.com/test"
        )
        mock_request = MagicMock()
        mock_request.user = self.staff_user
        admin.save_model(mock_request, edital, None, change=True)
        assert edital.updated_by == self.staff_user

    def test_created_by_tracked(self):
        data = {
            "titulo": "Edital com Rastreamento",
            "url": "https://example.com/track",
            "status": "aberto",
        }
        self.client.post(reverse("edital_create"), data=data)
        edital = Edital.objects.get(titulo="Edital com Rastreamento")
        assert edital.created_by == self.staff_user
        assert edital.updated_by == self.staff_user

    def test_updated_by_tracked(self):
        data = {
            "titulo": self.edital1.titulo,
            "url": self.edital1.url,
            "status": "fechado",
            "numero_edital": self.edital1.numero_edital,
            "entidade_principal": self.edital1.entidade_principal,
        }
        self.client.post(reverse("edital_update", args=[self.edital1.pk]), data=data)
        self.edital1.refresh_from_db()
        assert self.edital1.updated_by == self.staff_user


@pytest.mark.django_db
class TestEditalAdminFilters:
    """Testes para filtros administrativos."""

    @pytest.fixture(autouse=True)
    def _setup(self, client, staff_user):
        self.client = client
        self.staff_user = staff_user
        self.client.force_login(staff_user)
        cache.clear()

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

    def test_admin_can_search_by_title(self):
        resp = self.client.get(reverse("editais_index"), {"search": "Aberto"})
        assert resp.status_code == 200
        assert self.edital_aberto.titulo in resp.content.decode()

    def test_admin_can_filter_by_status(self):
        resp = self.client.get(reverse("editais_index"), {"status": "aberto"})
        assert resp.status_code == 200
        content = resp.content.decode()
        assert self.edital_aberto.titulo in content
        assert self.edital_fechado.titulo not in content

    def test_admin_can_filter_by_entity(self):
        resp = self.client.get(reverse("editais_index"), {"search": "CNPq"})
        assert resp.status_code == 200
        assert self.edital_aberto.titulo in resp.content.decode()

    def test_admin_can_filter_by_start_date(self):
        today = timezone.now().date()
        edital_future = Edital.objects.create(
            titulo="Edital Futuro",
            url="https://example.com/future",
            status="aberto",
            start_date=today + timedelta(days=30),
        )
        resp = self.client.get(
            reverse("editais_index"),
            {"start_date": today.strftime("%Y-%m-%d")},
        )
        assert resp.status_code == 200
        assert edital_future.titulo in resp.content.decode()

    def test_admin_can_filter_by_end_date(self):
        today = timezone.now().date()
        edital_past = Edital.objects.create(
            titulo="Edital Passado",
            url="https://example.com/past",
            status="fechado",
            end_date=today - timedelta(days=10),
        )
        resp = self.client.get(
            reverse("editais_index"),
            {"end_date": today.strftime("%Y-%m-%d")},
        )
        assert resp.status_code == 200
        assert edital_past.titulo in resp.content.decode()

    def test_admin_can_combine_search_and_filters(self):
        resp = self.client.get(
            reverse("editais_index"), {"search": "Edital", "status": "aberto"}
        )
        assert resp.status_code == 200
        content = resp.content.decode()
        assert self.edital_aberto.titulo in content
        assert self.edital_fechado.titulo not in content

    def test_pagination_works(self):
        for i in range(15):
            Edital.objects.create(
                titulo=f"Edital {i}",
                url=f"https://example.com/{i}",
                status="aberto",
            )
        resp = self.client.get(reverse("editais_index"))
        assert resp.status_code == 200
        page_obj = resp.context["page_obj"]
        assert page_obj.paginator.num_pages > 1
        assert len(page_obj.object_list) == 12

        resp = self.client.get(reverse("editais_index"), {"page": "2"})
        assert resp.status_code == 200
        page_obj = resp.context["page_obj"]
        assert len(page_obj.object_list) > 0
        assert len(page_obj.object_list) <= 12

    def test_pagination_preserves_filters(self):
        for i in range(15):
            Edital.objects.create(
                titulo=f"Edital Aberto {i}",
                url=f"https://example.com/aberto-{i}",
                status="aberto",
            )
        resp = self.client.get(reverse("editais_index"), {"status": "aberto", "page": "2"})
        assert resp.status_code == 200
        page_obj = resp.context["page_obj"]
        for edital in page_obj.object_list:
            assert edital.status == "aberto"

    def test_pagination_invalid_page_returns_last_page(self):
        for i in range(5):
            Edital.objects.create(
                titulo=f"Edital {i}",
                url=f"https://example.com/{i}",
                status="aberto",
            )
        resp = self.client.get(reverse("editais_index"), {"page": "999"})
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

    def test_staff_can_access_dashboard(self, staff_client, staff_user):
        resp = staff_client.get(reverse("admin_dashboard"))
        assert resp.status_code == 200
        assert "Dashboard Administrativo" in resp.content.decode()

    def test_non_staff_cannot_access_dashboard(self, auth_client):
        resp = auth_client.get(reverse("admin_dashboard"))
        assert resp.status_code == 403

    def test_unauthenticated_cannot_access_dashboard(self, client):
        resp = client.get(reverse("admin_dashboard"))
        assert resp.status_code == 302
        assert "/login/" in resp.url

    def test_dashboard_shows_editais_por_status(self, staff_client):
        resp = staff_client.get(reverse("admin_dashboard"))
        content = resp.content.decode()
        assert "Edital Aberto" in content
        assert "Edital Fechado" in content

    def test_dashboard_shows_recent_editais(self, staff_client, staff_user):
        recent_edital = Edital.objects.create(
            titulo="Edital Recente",
            url="https://example.com/recent",
            status="aberto",
            data_criacao=timezone.now() - timedelta(days=3),
            created_by=staff_user,
        )
        resp = staff_client.get(reverse("admin_dashboard"))
        assert recent_edital.titulo in resp.content.decode()

    def test_dashboard_shows_upcoming_deadlines(self, staff_client):
        today = timezone.now().date()
        upcoming = Edital.objects.create(
            titulo="Edital Próximo do Prazo",
            url="https://example.com/upcoming",
            status="aberto",
            end_date=today + timedelta(days=5),
        )
        resp = staff_client.get(reverse("admin_dashboard"))
        content = resp.content.decode()
        assert upcoming.titulo in content

    def test_dashboard_shows_top_entidades(self, staff_client):
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
        resp = staff_client.get(reverse("admin_dashboard"))
        assert "CNPq" in resp.content.decode()
