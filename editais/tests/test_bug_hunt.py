"""
Comprehensive bug hunt tests covering security, data integrity, edge cases,
validation, error handling, performance, and integration issues.
"""

import pytest
import threading
import time
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from editais.models import Edital, EditalValor, Cronograma, Startup
from editais.forms import EditalForm, UserRegistrationForm
from editais.utils import (
    determine_edital_status,
    sanitize_html,
    get_startup_status_mapping,
    clear_index_cache,
)
from editais.decorators import get_client_ip
from editais.constants import HTML_FIELDS, SLUG_GENERATION_MAX_RETRIES


@pytest.mark.django_db
class TestSecurity:
    """Security vulnerability tests"""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.user = User.objects.create_user("testuser", "test@example.com", "password")
        self.staff_user = User.objects.create_user(
            "staff", "staff@example.com", "password", is_staff=True
        )

    def test_sql_injection_in_search_query(self, client):
        malicious_queries = [
            "'; DROP TABLE editais_edital; --",
            "' OR '1'='1",
            "1' UNION SELECT * FROM auth_user--",
            "'; DELETE FROM editais_edital WHERE '1'='1",
        ]
        for query in malicious_queries:
            response = client.get("/editais/", {"search": query})
            assert response.status_code == 200

    def test_xss_in_html_fields(self):
        xss_payloads = [
            '<script>alert("XSS")</script>',
            '<img src=x onerror=alert("XSS")>',
            '<svg onload=alert("XSS")>',
            'javascript:alert("XSS")',
            "<iframe src=\"javascript:alert('XSS')\"></iframe>",
        ]
        for payload in xss_payloads:
            sanitized = sanitize_html(payload)
            assert "<script>" not in sanitized
            assert "onerror=" not in sanitized
            assert "onload=" not in sanitized
            assert "javascript:" not in sanitized.lower()

    def test_csrf_protection_on_forms(self, client):
        from django.test import Client as DjClient

        client.force_login(self.staff_user)
        csrf_client = DjClient(enforce_csrf_checks=True)
        response = csrf_client.post(
            "/cadastrar/",
            {"titulo": "Test Edital", "url": "https://example.com"},
            follow=False,
        )
        assert response.status_code in [403, 400]

    def test_authentication_bypass_attempts(self, client):
        staff_urls = ["/dashboard/editais/", "/dashboard/usuarios/", "/cadastrar/"]
        for url in staff_urls:
            response = client.get(url)
            assert response.status_code in [302, 403]

        client.force_login(self.user)
        for url in staff_urls:
            response = client.get(url)
            assert response.status_code == 403

    def test_draft_edital_visibility(self, client):
        edital = Edital.objects.create(
            titulo="Draft Edital", url="https://example.com", status="draft"
        )
        response = client.get(edital.get_absolute_url())
        assert response.status_code == 404

        client.force_login(self.user)
        response = client.get(edital.get_absolute_url())
        assert response.status_code == 404

        client.force_login(self.staff_user)
        response = client.get(edital.get_absolute_url())
        assert response.status_code == 200

    def test_information_disclosure_in_errors(self, client):
        response = client.get("/edital/99999/")
        assert response.status_code == 404
        if hasattr(response, "content"):
            content = response.content.decode("utf-8")
            assert "Traceback" not in content
            assert "settings.py" not in content


@pytest.mark.django_db(transaction=True)
class TestDataIntegrity:
    """Data integrity and race condition tests"""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.user = User.objects.create_user("testuser", "test@example.com", "password")

    def test_slug_uniqueness_under_concurrent_load(self):
        results = []
        errors = []

        def create_edital(title):
            try:
                for attempt in range(5):
                    try:
                        edital = Edital(
                            titulo=title,
                            url="https://example.com",
                            created_by=self.user,
                        )
                        for slug_attempt in range(SLUG_GENERATION_MAX_RETRIES):
                            try:
                                with transaction.atomic():
                                    edital.save()
                                results.append(edital.slug)
                                return
                            except IntegrityError as e:
                                if (
                                    "slug" in str(e).lower()
                                    or "unique" in str(e).lower()
                                ) and slug_attempt < SLUG_GENERATION_MAX_RETRIES - 1:
                                    edital.slug = edital._generate_unique_slug()
                                    continue
                                raise
                        break
                    except Exception as e:
                        if "locked" in str(e).lower() and attempt < 4:
                            time.sleep(0.1 * (attempt + 1))
                            continue
                        raise
            except Exception as e:
                errors.append(str(e))

        threads = []
        for i in range(10):
            t = threading.Thread(target=create_edital, args=("Test Edital",))
            threads.append(t)
            t.start()
            if i < 9:
                time.sleep(0.05)
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == len(set(results)), "Duplicate slugs generated"

    def test_foreign_key_cascade_deletion(self):
        edital = Edital.objects.create(
            titulo="Test Edital", url="https://example.com", created_by=self.user
        )
        valor = EditalValor.objects.create(edital=edital, valor_total=1000)
        cronograma = Cronograma.objects.create(edital=edital, descricao="Test")
        project = Startup.objects.create(
            name="Test Project", proponente=self.user, edital=edital
        )
        edital.delete()
        assert not EditalValor.objects.filter(pk=valor.pk).exists()
        assert not Cronograma.objects.filter(pk=cronograma.pk).exists()
        project.refresh_from_db()
        assert project.edital is None

    def test_null_empty_field_handling(self):
        edital = Edital.objects.create(
            titulo="Test", url="https://example.com", objetivo="", entidade_principal=""
        )
        assert edital.objetivo == ""
        assert edital.entidade_principal == ""

        from django.template import Template, Context

        template = Template('{{ edital.objetivo|default:"No objetivo" }}')
        result = template.render(Context({"edital": edital}))
        assert result == "No objetivo"


@pytest.mark.django_db
class TestEdgeCasesBugHunt:
    """Edge case and logic error tests"""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.user = User.objects.create_user("testuser", "test@example.com", "password")
        self.staff_user = User.objects.create_user(
            "staff", "staff@example.com", "password", is_staff=True
        )

    def test_pagination_edge_cases(self, client):
        for i in range(15):
            Edital.objects.create(
                titulo=f"Edital {i}",
                url=f"https://example.com/{i}",
                created_by=self.user,
            )
        assert client.get("/editais/", {"page": "invalid"}).status_code == 200
        assert client.get("/editais/", {"page": "-1"}).status_code == 200
        assert client.get("/editais/", {"page": "999"}).status_code == 200

    def test_search_query_edge_cases(self, client):
        assert client.get("/editais/", {"search": "a" * 1000}).status_code == 200
        assert client.get("/editais/", {"search": "!@#$%^&*()"}).status_code == 200
        assert client.get("/editais/", {"search": ""}).status_code == 200

    def test_status_determination_all_combinations(self):
        today = timezone.now().date()
        test_cases = [
            ("draft", None, None, "draft"),
            ("fechado", None, None, "fechado"),
            (
                "programado",
                today - timedelta(days=1),
                today + timedelta(days=1),
                "aberto",
            ),
            ("aberto", today - timedelta(days=1), today + timedelta(days=1), "aberto"),
            (
                "aberto",
                today - timedelta(days=10),
                today - timedelta(days=1),
                "fechado",
            ),
            (
                "programado",
                today + timedelta(days=1),
                today + timedelta(days=10),
                "programado",
            ),
            ("aberto", today - timedelta(days=1), None, "aberto"),
            ("programado", today - timedelta(days=1), None, "aberto"),
            ("aberto", None, today - timedelta(days=1), "fechado"),
        ]
        for current_status, start_date, end_date, expected in test_cases:
            result = determine_edital_status(
                current_status=current_status,
                start_date=start_date,
                end_date=end_date,
                today=today,
            )
            assert (
                result == expected
            ), f"Failed for status={current_status}, start={start_date}, end={end_date}"

    def test_project_status_mapping_edge_cases(self):
        mapping = get_startup_status_mapping()
        assert mapping.get("pré-incubação") == "pre_incubacao"
        assert mapping.get("incubação") == "incubacao"
        result = mapping.get("invalid_status", "invalid_status")
        assert result == "invalid_status"


@pytest.mark.django_db
class TestValidation:
    """Input validation tests"""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.user = User.objects.create_user("testuser", "test@example.com", "password")

    def test_decimal_field_validation(self):
        edital = Edital.objects.create(
            titulo="Test", url="https://example.com", created_by=self.user
        )
        valor = EditalValor(edital=edital, valor_total=Decimal("-1000"))
        with pytest.raises(ValidationError):
            valor.full_clean()

        large_valor = EditalValor(
            edital=edital, valor_total=Decimal("9999999999999.99")
        )
        large_valor.full_clean()

    def test_form_required_fields(self):
        form = EditalForm({})
        assert not form.is_valid()
        assert "titulo" in form.errors
        assert "url" in form.errors


@pytest.mark.django_db
class TestErrorHandlingBugHunt:
    """Error handling tests"""

    def test_template_rendering_with_missing_context(self):
        from django.template import Template, Context

        template = Template('{{ edital.objetivo|default:"No objetivo" }}')
        context = Context({"edital": type("obj", (object,), {"objetivo": None})()})
        assert template.render(context) == "No objetivo"

        context = Context({"edital": type("obj", (object,), {})()})
        assert template.render(context) == "No objetivo"


@pytest.mark.django_db
class TestPerformanceBugHunt:
    """Performance and N+1 query tests"""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.user = User.objects.create_user("testuser", "test@example.com", "password")

    def test_n1_queries_in_index_view(self, client):
        for i in range(5):
            edital = Edital.objects.create(
                titulo=f"Edital {i}",
                url=f"https://example.com/{i}",
                created_by=self.user,
            )
            EditalValor.objects.create(edital=edital, valor_total=1000)

        with override_settings(DEBUG=True):
            from django.db import connection

            connection.queries_log.clear()
            response = client.get("/editais/")
            assert response.status_code == 200
            assert len(connection.queries) < 10, "Too many queries (N+1 problem)"

    def test_large_result_set_handling(self, client):
        for i in range(100):
            Edital.objects.create(
                titulo=f"Edital {i}",
                url=f"https://example.com/{i}",
                created_by=self.user,
            )
        assert client.get("/editais/").status_code == 200


@pytest.mark.django_db
class TestIntegrationBugHunt:
    """Integration tests"""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.staff_user = User.objects.create_user(
            "staff", "staff@example.com", "password", is_staff=True
        )

    def test_admin_save_model_sanitization(self):
        from editais.admin import EditalAdmin
        from django.contrib.admin.sites import AdminSite

        edital = Edital(
            titulo="Test",
            url="https://example.com",
            analise='<script>alert("XSS")</script>',
        )
        admin = EditalAdmin(Edital, AdminSite())
        admin.save_model(
            request=MagicMock(user=self.staff_user),
            obj=edital,
            form=MagicMock(),
            change=False,
        )
        assert "<script>" not in edital.analise

    def test_template_tag_safety(self):
        from editais.templatetags.editais_filters import days_until, is_deadline_soon

        assert days_until(None) is None
        assert is_deadline_soon(None) is False

        future_date = timezone.now().date() + timedelta(days=5)
        assert days_until(future_date) is not None
        assert is_deadline_soon(future_date) is True
