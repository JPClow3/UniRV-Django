"""
End-to-end tests for AJAX request handling.
"""

import pytest
from django.conf import settings
from django.core.cache import cache
from django.urls import reverse

from editais.tests.factories import StaffUserFactory, EditalFactory


@pytest.mark.django_db
class TestAjaxIndexView:
    """E2E tests for AJAX requests to index view"""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.staff_user = StaffUserFactory(username="staff")
        for i in range(15):
            EditalFactory(
                titulo=f"AJAX Test Edital {i}",
                status="aberto" if i % 2 == 0 else "fechado",
                created_by=self.staff_user,
            )

    def test_ajax_request_returns_partial_template(self, client):
        resp = client.get(
            reverse("editais_index"), HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        assert resp.status_code == 200
        assert "Edital" in resp.content.decode()

    def test_non_ajax_request_returns_full_page(self, client):
        resp = client.get(reverse("editais_index"))
        assert resp.status_code == 200
        assert "Edital" in resp.content.decode()

    def test_ajax_request_with_search(self, client):
        resp = client.get(
            reverse("editais_index"),
            {"search": "AJAX Test Edital 1"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        assert resp.status_code == 200
        assert "AJAX Test Edital 1" in resp.content.decode()

    def test_ajax_request_with_status_filter(self, client):
        resp = client.get(
            reverse("editais_index"),
            {"status": "aberto"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        assert resp.status_code == 200

    def test_ajax_request_with_pagination(self, client):
        resp = client.get(
            reverse("editais_index"),
            {"page": "1"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        assert resp.status_code == 200
        resp = client.get(
            reverse("editais_index"),
            {"page": "2"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        assert resp.status_code == 200

    def test_ajax_request_with_invalid_page(self, client):
        resp = client.get(
            reverse("editais_index"),
            {"page": "invalid"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        assert resp.status_code == 200

    def test_ajax_request_with_combined_filters(self, client):
        resp = client.get(
            reverse("editais_index"),
            {"search": "AJAX Test", "status": "aberto", "page": "1"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        assert resp.status_code == 200

    def test_ajax_request_error_handling(self, client):
        resp = client.get(
            reverse("editais_index"),
            {"search": "a" * 10000},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        assert resp.status_code == 200

    def test_ajax_vs_non_ajax_response_difference(self, client):
        ajax = client.get(
            reverse("editais_index"), HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        normal = client.get(reverse("editais_index"))
        assert ajax.status_code == 200
        assert normal.status_code == 200
        assert "Edital" in ajax.content.decode()
        assert "Edital" in normal.content.decode()


@pytest.mark.django_db
class TestAjaxPagination:
    """Tests for AJAX pagination functionality"""

    @pytest.fixture(autouse=True)
    def _setup(self):
        staff = StaffUserFactory(username="staff")
        per_page = getattr(settings, "EDITAIS_PER_PAGE", 12)
        for i in range(per_page * 2 + 5):
            EditalFactory(
                titulo=f"Paginated Edital {i}", status="aberto", created_by=staff
            )

    def test_ajax_pagination_first_page(self, client):
        resp = client.get(
            reverse("editais_index"),
            {"page": "1"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        assert resp.status_code == 200

    def test_ajax_pagination_last_page(self, client):
        resp = client.get(
            reverse("editais_index"),
            {"page": "999"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        assert resp.status_code == 200

    def test_ajax_pagination_empty_results(self, client):
        resp = client.get(
            reverse("editais_index"),
            {"search": "NonexistentQuery12345XYZ"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        assert resp.status_code == 200


@pytest.mark.django_db
class TestAjaxCacheBehavior:
    """Tests for cache behavior with AJAX requests"""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.staff_user = StaffUserFactory(username="staff")
        cache.clear()

    def test_ajax_requests_not_cached(self, client):
        EditalFactory(
            titulo="Cache Test Edital", status="aberto", created_by=self.staff_user
        )
        resp1 = client.get(
            reverse("editais_index"), HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        assert resp1.status_code == 200

        EditalFactory(
            titulo="New Edital After AJAX", status="aberto", created_by=self.staff_user
        )
        resp2 = client.get(
            reverse("editais_index"), HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        assert resp2.status_code == 200
