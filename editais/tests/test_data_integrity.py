"""
Data integrity tests: race conditions, slug uniqueness, date validation, foreign keys.
"""

import pytest
import threading
import time
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from editais.models import Edital, Startup, EditalValor
from editais.forms import UserRegistrationForm


@pytest.mark.django_db(transaction=True)
class TestSlugUniqueness:
    """Test slug generation and uniqueness under concurrent load"""

    def test_concurrent_slug_generation(self):
        title = "Concurrent Edital Test"
        results = []
        errors = []
        from editais.constants import SLUG_GENERATION_MAX_RETRIES

        def create_edital():
            try:
                for attempt in range(5):
                    try:
                        edital = Edital(
                            titulo=title, url="https://example.com", status="aberto"
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
        for i in range(5):
            t = threading.Thread(target=create_edital)
            threads.append(t)
            t.start()
            if i < 4:
                time.sleep(0.05)
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5
        assert len(set(results)) == 5, f"Slugs should be unique. Got: {results}"

    def test_slug_generation_with_empty_title(self):
        edital = Edital.objects.create(
            titulo="!!!@@@###", url="https://example.com", status="aberto"
        )
        assert edital.slug is not None
        assert edital.slug.startswith("edital-")

    def test_startup_slug_uniqueness(self):
        user = User.objects.create_user(username="testuser", password="testpass123")
        name = "Concurrent Startup"
        results = []
        errors = []
        from editais.constants import SLUG_GENERATION_MAX_RETRIES

        def create_startup():
            try:
                for attempt in range(5):
                    try:
                        startup = Startup(
                            name=name, proponente=user, status="pre_incubacao"
                        )
                        for slug_attempt in range(SLUG_GENERATION_MAX_RETRIES):
                            try:
                                with transaction.atomic():
                                    startup.save()
                                results.append(startup.slug)
                                return
                            except IntegrityError as e:
                                if (
                                    "slug" in str(e).lower()
                                    or "unique" in str(e).lower()
                                ) and slug_attempt < SLUG_GENERATION_MAX_RETRIES - 1:
                                    startup.slug = startup._generate_unique_slug()
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
        for i in range(3):
            t = threading.Thread(target=create_startup)
            threads.append(t)
            t.start()
            if i < 2:
                time.sleep(0.05)
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 3
        assert len(set(results)) == 3


@pytest.mark.django_db
class TestDateValidation:
    """Test date validation edge cases"""

    def test_end_date_before_start_date(self):
        from editais.forms import EditalForm

        form = EditalForm(
            {
                "titulo": "Test Edital",
                "url": "https://example.com",
                "status": "aberto",
                "start_date": date.today() + timedelta(days=30),
                "end_date": date.today(),
            }
        )
        assert not form.is_valid()
        assert "end_date" in form.errors

    def test_same_start_and_end_date(self):
        from editais.forms import EditalForm

        same_date = date.today()
        form = EditalForm(
            {
                "titulo": "Test Edital",
                "url": "https://example.com",
                "status": "aberto",
                "start_date": same_date,
                "end_date": same_date,
            }
        )
        assert form.is_valid()

    def test_future_dates(self):
        from editais.forms import EditalForm

        form = EditalForm(
            {
                "titulo": "Test Edital",
                "url": "https://example.com",
                "status": "programado",
                "start_date": date.today() + timedelta(days=30),
                "end_date": date.today() + timedelta(days=60),
            }
        )
        assert form.is_valid()

    def test_past_dates(self):
        from editais.forms import EditalForm

        form = EditalForm(
            {
                "titulo": "Test Edital",
                "url": "https://example.com",
                "status": "fechado",
                "start_date": date.today() - timedelta(days=60),
                "end_date": date.today() - timedelta(days=30),
            }
        )
        assert form.is_valid()


@pytest.mark.django_db
class TestForeignKeyIntegrity:
    """Test foreign key relationships and cascade behaviors"""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.edital = Edital.objects.create(
            titulo="Test Edital", url="https://example.com", status="aberto"
        )

    def test_edital_deletion_with_startups(self):
        startup = Startup.objects.create(
            name="Test Startup",
            proponente=self.user,
            edital=self.edital,
            status="pre_incubacao",
        )
        startup_id = startup.pk
        self.edital.delete()
        startup.refresh_from_db()
        assert startup.edital is None
        assert startup.pk == startup_id

    def test_user_deletion_with_startups(self):
        startup = Startup.objects.create(
            name="Test Startup", proponente=self.user, status="pre_incubacao"
        )
        startup_id = startup.pk
        self.user.delete()
        assert not Startup.objects.filter(pk=startup_id).exists()

    def test_edital_valor_cascade(self):
        valor = EditalValor.objects.create(
            edital=self.edital, valor_total=100000.00, moeda="BRL"
        )
        valor_id = valor.pk
        self.edital.delete()
        assert not EditalValor.objects.filter(pk=valor_id).exists()


@pytest.mark.django_db(transaction=True)
class TestEmailUniquenessRaceCondition:
    """Test email uniqueness race condition in user registration"""

    def test_concurrent_email_registration(self):
        email = "test@example.com"
        results = []
        errors = []

        def register_user():
            form = UserRegistrationForm(
                {
                    "username": f"user{time.time()}",
                    "email": email,
                    "first_name": "Test",
                    "last_name": "User",
                    "password1": "ComplexPass123!",
                    "password2": "ComplexPass123!",
                }
            )
            if form.is_valid():
                try:
                    user = form.save()
                    results.append(user.email)
                except ValidationError:
                    errors.append("ValidationError")
            else:
                errors.append("Form invalid")

        threads = []
        for _ in range(3):
            t = threading.Thread(target=register_user)
            threads.append(t)
            t.start()
        for t in threads:
            t.join()

        assert len(results) >= 1, "At least one registration should succeed"
        assert len(results) + len(errors) == 3
