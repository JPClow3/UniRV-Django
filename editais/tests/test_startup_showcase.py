"""
Tests for startups_showcase view.
"""

from unittest.mock import patch, MagicMock

import pytest

from django.contrib.auth.models import User
from django.db import DatabaseError
from django.urls import reverse
from django.core.cache import cache

from editais.models import Startup, Edital
from editais.constants import ACTIVE_STARTUP_STATUSES, MAX_STARTUPS_DISPLAY


@pytest.mark.django_db
class TestStartupShowcaseView:
    """Test startups_showcase view functionality"""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.project1 = Startup.objects.create(
            name="AgTech Startup",
            description="An agricultural technology startup",
            category="agtech",
            status="pre_incubacao",
            proponente=self.user,
        )
        self.project2 = Startup.objects.create(
            name="BioTech Company",
            description="A biotechnology company",
            category="biotech",
            status="incubacao",
            proponente=self.user,
        )
        self.project3 = Startup.objects.create(
            name="Graduated Startup",
            description="A graduated startup",
            category="iot",
            status="graduada",
            proponente=self.user,
        )
        self.suspended = Startup.objects.create(
            name="Suspended Startup",
            description="A suspended startup",
            category="other",
            status="suspensa",
            proponente=self.user,
        )

    def test_startup_showcase_loads(self, client):
        """Test that startups showcase page loads"""
        response = client.get(reverse("startups_showcase"))
        assert response.status_code == 200

    def test_startup_showcase_displays_active_projects(self, client):
        """Test that only active projects are displayed"""
        response = client.get(reverse("startups_showcase"))
        content = response.content.decode()
        assert self.project1.name in content
        assert self.project2.name in content
        assert self.project3.name in content
        assert self.suspended.name not in content

    def test_category_filtering(self, client):
        """Test filtering by category"""
        response = client.get(reverse("startups_showcase"), {"category": "agtech"})
        assert response.status_code == 200
        assert self.project1.name in response.content.decode()
        assert self.project2.name not in response.content.decode()

        response = client.get(reverse("startups_showcase"), {"category": "biotech"})
        assert self.project2.name in response.content.decode()
        assert self.project1.name not in response.content.decode()

    def test_category_filter_all(self, client):
        """Test that category='all' shows all categories"""
        response = client.get(reverse("startups_showcase"), {"category": "all"})
        content = response.content.decode()
        assert self.project1.name in content
        assert self.project2.name in content
        assert self.project3.name in content

    def test_search_functionality(self, client):
        """Test search functionality"""
        response = client.get(reverse("startups_showcase"), {"search": "AgTech"})
        assert self.project1.name in response.content.decode()
        assert self.project2.name not in response.content.decode()

        response = client.get(reverse("startups_showcase"), {"search": "biotechnology"})
        assert self.project2.name in response.content.decode()

    def test_search_with_special_characters(self, client):
        """Test search with special characters"""
        response = client.get(reverse("startups_showcase"), {"search": "!@#$%^&*()"})
        assert response.status_code == 200

    def test_search_sql_injection_attempt(self, client):
        """Test SQL injection attempts in search"""
        malicious_queries = [
            "'; DROP TABLE editais_project; --",
            "' OR '1'='1",
            "1' UNION SELECT * FROM auth_user--",
        ]

        for query in malicious_queries:
            response = client.get(reverse("startups_showcase"), {"search": query})
            assert response.status_code == 200

    def test_stats_calculation(self, client):
        """Test that stats are calculated correctly"""
        response = client.get(reverse("startups_showcase"))
        assert response.status_code == 200

        context = response.context
        assert "stats" in context
        stats = context["stats"]
        assert "total_active" in stats
        assert "graduadas" in stats

        assert stats["total_active"] == 3
        assert stats["graduadas"] == 1

    def test_stats_with_empty_database(self, client):
        """Test stats calculation with empty database"""
        Startup.objects.all().delete()
        response = client.get(reverse("startups_showcase"))
        assert response.status_code == 200

        context = response.context
        stats = context["stats"]
        assert stats["total_active"] == 0
        assert stats["graduadas"] == 0

    def test_max_startups_display_limit(self, client):
        """Test that results are limited to MAX_STARTUPS_DISPLAY"""
        for i in range(MAX_STARTUPS_DISPLAY + 10):
            Startup.objects.create(
                name=f"Startup {i}",
                category="other",
                status="pre_incubacao",
                proponente=self.user,
            )

        response = client.get(reverse("startups_showcase"))
        context = response.context
        startups = context["startups"]
        assert len(startups) <= MAX_STARTUPS_DISPLAY

    def test_ordering_by_submitted_on(self, client):
        """Test that startups are ordered by submitted_on (newest first)"""
        Startup.objects.create(
            name="Old Startup",
            category="other",
            status="pre_incubacao",
            proponente=self.user,
        )

        response = client.get(reverse("startups_showcase"))
        context = response.context
        startups = list(context["startups"])
        if len(startups) > 1:
            for i in range(len(startups) - 1):
                assert startups[i].submitted_on >= startups[i + 1].submitted_on

    def test_xss_in_project_description(self, client):
        """Test XSS prevention in project descriptions"""
        Startup.objects.create(
            name="XSS Test",
            description='<script>alert("XSS")</script>',
            category="other",
            status="pre_incubacao",
            proponente=self.user,
        )

        response = client.get(reverse("startups_showcase"))
        assert response.status_code == 200
        content = response.content.decode()

        assert "XSS Test" in content
        assert "&lt;script&gt;" in content
        assert '<script>alert("XSS")</script>' not in content

    def test_very_long_search_query(self, client):
        """Test handling of very long search queries"""
        long_query = "a" * 10000
        response = client.get(reverse("startups_showcase"), {"search": long_query})
        assert response.status_code == 200

    def test_empty_search_query(self, client):
        """Test handling of empty search query"""
        response = client.get(reverse("startups_showcase"), {"search": ""})
        assert response.status_code == 200
        assert len(response.context["startups"]) > 0

    def test_invalid_category_filter(self, client):
        """Test handling of invalid category filter"""
        response = client.get(
            reverse("startups_showcase"), {"category": "invalid_category"}
        )
        assert response.status_code == 200

    def test_cache_behavior(self, client):
        """Test that view handles cache correctly"""
        cache.clear()
        response1 = client.get(reverse("startups_showcase"))
        assert response1.status_code == 200

        response2 = client.get(reverse("startups_showcase"))
        assert response2.status_code == 200

    def test_context_variables_present(self, client):
        """Test that all required context variables are present"""
        response = client.get(reverse("startups_showcase"))
        context = response.context

        required_vars = ["startups", "category_filter", "search_query", "stats"]
        for var in required_vars:
            assert var in context

    def test_stats_graduadas_count(self, client):
        """Test that graduadas count is correct"""
        for i in range(3):
            Startup.objects.create(
                name=f"Graduated {i}",
                category="other",
                status="graduada",
                proponente=self.user,
            )

        response = client.get(reverse("startups_showcase"))
        context = response.context
        stats = context["stats"]
        assert stats["graduadas"] == 4
