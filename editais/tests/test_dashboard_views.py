"""
Tests for dashboard views (dashboard_home, dashboard_editais, dashboard_startups, etc.).
"""

import pytest
from django.urls import reverse
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta

from editais.models import Edital, Startup
from editais.tests.factories import (
    UserFactory,
    StaffUserFactory,
    EditalFactory,
    StartupFactory,
)


@pytest.mark.django_db
class TestDashboardHomeView:
    """Tests for dashboard home view"""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.user = UserFactory(username="testuser")

    def test_dashboard_home_requires_login(self, client):
        resp = client.get(reverse("dashboard_home"))
        assert resp.status_code == 302
        assert reverse("login") in resp.url

    def test_dashboard_home_loads_for_authenticated_user(self, client):
        client.login(username="testuser", password="testpass123")
        resp = client.get(reverse("dashboard_home"))
        assert resp.status_code == 200


@pytest.mark.django_db
class TestDashboardEditaisView:
    """Tests for dashboard editais view"""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.staff_user = StaffUserFactory(username="staff")
        self.regular_user = UserFactory(username="regular")
        self.edital = EditalFactory(
            titulo="Test Edital", status="aberto", created_by=self.staff_user
        )

    def test_dashboard_editais_requires_login(self, client):
        resp = client.get(reverse("dashboard_editais"))
        assert resp.status_code == 302

    def test_dashboard_editais_requires_staff(self, client):
        client.login(username="regular", password="testpass123")
        resp = client.get(reverse("dashboard_editais"))
        assert resp.status_code == 403

    def test_dashboard_editais_loads_for_staff(self, client):
        client.login(username="staff", password="testpass123")
        resp = client.get(reverse("dashboard_editais"))
        assert resp.status_code == 200

    def test_dashboard_editais_search_filter(self, client):
        client.login(username="staff", password="testpass123")
        resp = client.get(
            reverse("dashboard_editais"), {"search": "Test", "status": "aberto"}
        )
        assert resp.status_code == 200
        assert "Test Edital" in resp.content.decode()

    def test_dashboard_editais_tipo_filter(self, client):
        client.login(username="staff", password="testpass123")
        EditalFactory(
            titulo="Fomento Edital",
            status="aberto",
            end_date=timezone.now().date() + timedelta(days=30),
            created_by=self.staff_user,
        )
        resp = client.get(reverse("dashboard_editais"), {"tipo": "Fomento"})
        assert resp.status_code == 200
        assert "Fomento Edital" in resp.content.decode()


@pytest.mark.django_db
class TestDashboardStartupsView:
    @pytest.fixture(autouse=True)
    def _setup(self):
        self.user = UserFactory(username="testuser")

    def test_requires_login(self, client):
        resp = client.get(reverse("dashboard_startups"))
        assert resp.status_code == 302

    def test_loads_for_authenticated_user(self, client):
        client.login(username="testuser", password="testpass123")
        resp = client.get(reverse("dashboard_startups"))
        assert resp.status_code == 200


@pytest.mark.django_db
class TestDashboardUsuariosView:
    @pytest.fixture(autouse=True)
    def _setup(self):
        self.staff_user = StaffUserFactory(username="staff")
        self.regular_user = UserFactory(username="regular")

    def test_requires_login(self, client):
        resp = client.get(reverse("dashboard_usuarios"))
        assert resp.status_code == 302

    def test_requires_staff(self, client):
        client.login(username="regular", password="testpass123")
        assert client.get(reverse("dashboard_usuarios")).status_code == 403

    def test_loads_for_staff(self, client):
        client.login(username="staff", password="testpass123")
        assert client.get(reverse("dashboard_usuarios")).status_code == 200


@pytest.mark.django_db
class TestDashboardSubmeterStartupView:
    @pytest.fixture(autouse=True)
    def _setup(self):
        self.user = UserFactory(username="testuser")

    def test_requires_login(self, client):
        resp = client.get(reverse("dashboard_submeter_startup"))
        assert resp.status_code == 302

    def test_loads_for_authenticated_user(self, client):
        client.login(username="testuser", password="testpass123")
        assert client.get(reverse("dashboard_submeter_startup")).status_code == 200


@pytest.mark.django_db
class TestDashboardNovoEditalView:
    @pytest.fixture(autouse=True)
    def _setup(self):
        self.staff_user = StaffUserFactory(username="staff")
        self.regular_user = UserFactory(username="regular")

    def test_requires_login(self, client):
        resp = client.get(reverse("dashboard_novo_edital"))
        assert resp.status_code == 302

    def test_requires_staff(self, client):
        client.login(username="regular", password="testpass123")
        assert client.get(reverse("dashboard_novo_edital")).status_code == 403

    def test_get_form(self, client):
        client.login(username="staff", password="testpass123")
        resp = client.get(reverse("dashboard_novo_edital"))
        assert resp.status_code == 200
        assert "form" in resp.context

    def test_post_valid(self, client):
        client.login(username="staff", password="testpass123")
        resp = client.post(
            reverse("dashboard_novo_edital"),
            data={
                "titulo": "Novo Edital de Teste",
                "url": "https://example.com/novo",
                "status": "aberto",
                "objetivo": "Objetivo do novo edital",
            },
        )
        assert resp.status_code == 302
        assert Edital.objects.filter(titulo="Novo Edital de Teste").exists()

    def test_post_invalid(self, client):
        client.login(username="staff", password="testpass123")
        resp = client.post(
            reverse("dashboard_novo_edital"),
            data={"titulo": "", "url": "not-a-url", "status": "aberto"},
        )
        assert resp.status_code == 200
        assert resp.context["form"].errors


@pytest.mark.django_db
class TestDashboardStartupUpdateView:
    @pytest.fixture(autouse=True)
    def _setup(self):
        self.staff_user = StaffUserFactory(username="staff")
        self.regular_user = UserFactory(username="regular")
        self.other_user = UserFactory(username="other")
        self.project = StartupFactory(name="Test Startup", proponente=self.regular_user)

    def test_requires_login(self, client):
        resp = client.get(
            reverse("dashboard_startup_update", kwargs={"pk": self.project.pk})
        )
        assert resp.status_code == 302

    def test_owner_can_edit(self, client):
        client.login(username="regular", password="testpass123")
        resp = client.get(
            reverse("dashboard_startup_update", kwargs={"pk": self.project.pk})
        )
        assert resp.status_code == 200

    def test_other_user_cannot_edit(self, client):
        client.login(username="other", password="testpass123")
        resp = client.get(
            reverse("dashboard_startup_update", kwargs={"pk": self.project.pk})
        )
        assert resp.status_code == 302

    def test_staff_can_edit_any(self, client):
        client.login(username="staff", password="testpass123")
        resp = client.get(
            reverse("dashboard_startup_update", kwargs={"pk": self.project.pk})
        )
        assert resp.status_code == 200

    def test_get_form_context(self, client):
        client.login(username="regular", password="testpass123")
        resp = client.get(
            reverse("dashboard_startup_update", kwargs={"pk": self.project.pk})
        )
        assert "form" in resp.context
        assert "startup" in resp.context
        assert resp.context["startup"] == self.project

    def test_post_valid(self, client):
        client.login(username="regular", password="testpass123")
        resp = client.post(
            reverse("dashboard_startup_update", kwargs={"pk": self.project.pk}),
            data={
                "name": "Updated Startup Name",
                "description": "Updated description",
                "category": "biotech",
                "status": "incubacao",
            },
        )
        assert resp.status_code == 302
        self.project.refresh_from_db()
        assert self.project.name == "Updated Startup Name"

    def test_post_invalid(self, client):
        client.login(username="regular", password="testpass123")
        resp = client.post(
            reverse("dashboard_startup_update", kwargs={"pk": self.project.pk}),
            data={"name": "", "description": "Updated", "category": "invalid_category"},
        )
        assert resp.status_code == 200
        assert resp.context["form"].errors

    def test_404_nonexistent(self, client):
        client.login(username="staff", password="testpass123")
        resp = client.get(reverse("dashboard_startup_update", kwargs={"pk": 99999}))
        assert resp.status_code == 404


@pytest.mark.django_db
class TestDashboardStatistics:
    @pytest.fixture(autouse=True)
    def _setup(self):
        self.staff_user = StaffUserFactory(username="staff")
        self.regular_user = UserFactory(username="regular")

    def test_dashboard_home_statistics_for_staff(self, client):
        open_edital = EditalFactory(
            titulo="Open Edital", status="aberto", created_by=self.staff_user
        )
        EditalFactory(
            titulo="Closed Edital", status="fechado", created_by=self.staff_user
        )
        StartupFactory(
            name="Test Startup", proponente=self.regular_user, edital=open_edital
        )

        client.login(username="staff", password="testpass123")
        resp = client.get(reverse("dashboard_home"))
        ctx = resp.context
        assert "total_usuarios" in ctx
        assert "editais_ativos" in ctx
        assert ctx["editais_ativos"] == 1

    def test_dashboard_home_statistics_for_regular_user(self, client):
        StartupFactory(name="User Startup", proponente=self.regular_user)
        client.login(username="regular", password="testpass123")
        resp = client.get(reverse("dashboard_home"))
        ctx = resp.context
        assert "recent_activities" in ctx
        assert "total_usuarios" not in ctx

    def test_dashboard_editais_statistics(self, client):
        EditalFactory(titulo="Draft Edital", status="draft", created_by=self.staff_user)
        EditalFactory(titulo="Open Edital", status="aberto", created_by=self.staff_user)
        EditalFactory(
            titulo="Another Open", status="aberto", created_by=self.staff_user
        )

        client.login(username="staff", password="testpass123")
        resp = client.get(reverse("dashboard_editais"))
        ctx = resp.context
        assert ctx["total_editais"] == 3
        assert ctx["publicados"] == 2
        assert ctx["rascunhos"] == 1


@pytest.mark.django_db
class TestDashboardActivityFeed:
    @pytest.fixture(autouse=True)
    def _setup(self):
        self.staff_user = StaffUserFactory(username="staff")
        self.regular_user = UserFactory(username="regular")

    def test_activity_feed_for_staff(self, client):
        EditalFactory(
            titulo="Recent Edital",
            status="aberto",
            created_by=self.staff_user,
            data_atualizacao=timezone.now() - timedelta(days=1),
        )
        StartupFactory(
            name="Recent Startup",
            proponente=self.regular_user,
            data_atualizacao=timezone.now() - timedelta(days=2),
        )

        client.login(username="staff", password="testpass123")
        resp = client.get(reverse("dashboard_home"))
        activities = resp.context["recent_activities"]
        assert isinstance(activities, list)
        titles = [a.get("title", "") for a in activities]
        assert "Recent Edital" in titles
        assert "Recent Startup" in titles

    def test_activity_feed_for_regular_user(self, client):
        StartupFactory(
            name="My Startup",
            proponente=self.regular_user,
            data_atualizacao=timezone.now() - timedelta(days=1),
        )
        other_user = UserFactory(username="other")
        StartupFactory(
            name="Other Startup",
            proponente=other_user,
            data_atualizacao=timezone.now() - timedelta(days=1),
        )

        client.login(username="regular", password="testpass123")
        resp = client.get(reverse("dashboard_home"))
        titles = [a.get("title", "") for a in resp.context["recent_activities"]]
        assert "My Startup" in titles
        assert "Other Startup" not in titles

    def test_activity_feed_ordering(self, client):
        EditalFactory(
            titulo="Old Edital",
            status="aberto",
            created_by=self.staff_user,
            data_atualizacao=timezone.now() - timedelta(days=5),
        )
        EditalFactory(
            titulo="New Edital",
            status="aberto",
            created_by=self.staff_user,
            data_atualizacao=timezone.now() - timedelta(days=1),
        )

        client.login(username="staff", password="testpass123")
        resp = client.get(reverse("dashboard_home"))
        activities = resp.context["recent_activities"]
        if len(activities) >= 2:
            dates = [a.get("date") for a in activities if a.get("date")]
            for i in range(len(dates) - 1):
                assert dates[i] >= dates[i + 1]

    def test_activity_feed_limit(self, client):
        for i in range(20):
            EditalFactory(
                titulo=f"Edital {i}",
                status="aberto",
                created_by=self.staff_user,
                data_atualizacao=timezone.now() - timedelta(days=i % 3),
            )

        client.login(username="staff", password="testpass123")
        resp = client.get(reverse("dashboard_home"))
        assert len(resp.context["recent_activities"]) <= 15


@pytest.mark.django_db(transaction=True)
class TestAdminDashboardE2E:
    @pytest.fixture(autouse=True)
    def _setup(self):
        Edital.objects.all().delete()
        Startup.objects.all().delete()
        cache.clear()
        self.staff_user = StaffUserFactory(username="staff")
        self.regular_user = UserFactory(username="regular")

    def test_requires_login(self, client):
        resp = client.get(reverse("admin_dashboard"))
        assert resp.status_code == 302

    def test_requires_staff(self, client):
        client.login(username="regular", password="testpass123")
        assert client.get(reverse("admin_dashboard")).status_code == 403

    def test_loads_for_staff(self, client):
        client.login(username="staff", password="testpass123")
        resp = client.get(reverse("admin_dashboard"))
        assert resp.status_code == 200

    def test_statistics_e2e(self, client):
        EditalFactory(titulo="Open Edital", status="aberto", created_by=self.staff_user)
        EditalFactory(titulo="Draft Edital", status="draft", created_by=self.staff_user)
        EditalFactory(
            titulo="Closed Edital", status="fechado", created_by=self.staff_user
        )
        EditalFactory(
            titulo="Recent Edital",
            status="aberto",
            created_by=self.staff_user,
            data_atualizacao=timezone.now() - timedelta(days=2),
        )

        client.login(username="staff", password="testpass123")
        resp = client.get(reverse("admin_dashboard"))
        ctx = resp.context
        assert ctx["total_editais"] == 4
        assert isinstance(ctx["editais_por_status"], list)
        recent_titles = [e.titulo for e in ctx["editais_recentes"]]
        assert "Recent Edital" in recent_titles

    def test_caching_e2e(self, client):
        cache.clear()
        EditalFactory(
            titulo="Cached Edital", status="aberto", created_by=self.staff_user
        )

        client.login(username="staff", password="testpass123")
        r1 = client.get(reverse("admin_dashboard"))
        r2 = client.get(reverse("admin_dashboard"))
        assert r1.context["total_editais"] == r2.context["total_editais"]

    def test_error_handling_e2e(self, client):
        client.login(username="staff", password="testpass123")
        resp = client.get(reverse("admin_dashboard"))
        assert resp.status_code == 200
        assert isinstance(resp.context["editais_por_status"], list)


@pytest.mark.django_db
class TestDashboardCacheBehavior:
    @pytest.fixture(autouse=True)
    def _setup(self):
        self.staff_user = StaffUserFactory(username="staff")
        cache.clear()

    def test_dashboard_editais_cache_behavior(self, client):
        client.login(username="staff", password="testpass123")
        EditalFactory(
            titulo="Initial Edital", status="aberto", created_by=self.staff_user
        )
        count1 = client.get(reverse("dashboard_editais")).context["total_editais"]

        EditalFactory(titulo="New Edital", status="aberto", created_by=self.staff_user)
        count2 = client.get(reverse("dashboard_editais")).context["total_editais"]
        assert count2 >= count1 + 1


@pytest.mark.django_db
class TestAdminDashboardQueryEfficiency:
    @pytest.fixture(autouse=True)
    def _setup(self):
        cache.clear()
        self.staff_user = StaffUserFactory(username="staff")

    def test_dashboard_statistics_accuracy(self, client):
        cache.clear()
        EditalFactory(
            titulo="Edital Aberto",
            status="aberto",
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=5),
            created_by=self.staff_user,
        )
        EditalFactory(
            titulo="Edital Fechado", status="fechado", created_by=self.staff_user
        )

        total = Edital.objects.count()
        client.login(username="staff", password="testpass123")
        resp = client.get(reverse("admin_dashboard"), follow=True)
        assert resp.status_code == 200
        if resp.context:
            assert resp.context["total_editais"] == total
            status_counts = {
                item["status"]: item["count"]
                for item in resp.context["editais_por_status"]
            }
            assert "aberto" in status_counts
            assert "fechado" in status_counts

    @pytest.mark.django_db(transaction=True)
    def test_dashboard_query_efficiency(self, client, django_assert_num_queries):
        cache.clear()
        client.login(username="staff", password="testpass123")
        for i in range(5):
            EditalFactory(
                titulo=f"Edital {i}", status="aberto", created_by=self.staff_user
            )
        cache.clear()

        with django_assert_num_queries(10):
            resp = client.get(reverse("admin_dashboard"), follow=True)
            assert resp.status_code == 200
