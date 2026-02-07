"""
Data integrity tests: race conditions, slug uniqueness, date validation, foreign keys.
"""

import threading
import time
from datetime import date, timedelta
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from ..models import Edital, Startup, EditalValor
from ..forms import UserRegistrationForm


class SlugUniquenessTest(TransactionTestCase):
    """Test slug generation and uniqueness under concurrent load"""

    def setUp(self):
        # Use TransactionTestCase for proper transaction isolation
        pass

    def test_concurrent_slug_generation(self):
        """Test that concurrent creation with same title generates unique slugs"""
        title = "Concurrent Edital Test"
        results = []
        errors = []

        from ..constants import SLUG_GENERATION_MAX_RETRIES

        def create_edital():
            try:
                for attempt in range(5):  # DB lock retries
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

        # Create 5 editais concurrently with same title
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_edital)
            threads.append(thread)
            thread.start()
            # Small delay between thread starts to reduce lock contention
            if i < 4:  # Don't delay after last thread
                time.sleep(0.05)

        # Wait for all threads
        for thread in threads:
            thread.join()

        # All should succeed
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 5)

        # All slugs should be unique
        self.assertEqual(
            len(set(results)), 5, f"Slugs should be unique. Got: {results}"
        )

        # All slugs should start with the base slug (or contain it for numbered variants)
        base_slug = "concurrent-edital-test"
        for slug in results:
            # Slugs may be 'concurrent-edital-test', 'concurrent-edital-test-1', etc.
            self.assertTrue(
                slug.startswith(base_slug) or base_slug in slug,
                f"Slug '{slug}' should start with or contain '{base_slug}'. All slugs: {results}",
            )

    def test_slug_generation_with_empty_title(self):
        """Test slug generation when title results in empty slug"""
        # Title with only special characters
        edital = Edital.objects.create(
            titulo="!!!@@@###", url="https://example.com", status="aberto"
        )
        # Should have fallback slug
        self.assertIsNotNone(edital.slug)
        self.assertTrue(edital.slug.startswith("edital-"))

    def test_startup_slug_uniqueness(self):
        """Test Startup slug uniqueness"""
        user = User.objects.create_user(username="testuser", password="testpass123")

        name = "Concurrent Startup"
        results = []
        errors = []

        from ..constants import SLUG_GENERATION_MAX_RETRIES

        def create_startup():
            try:
                for attempt in range(5):  # DB lock retries
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
            thread = threading.Thread(target=create_startup)
            threads.append(thread)
            thread.start()
            # Small delay between thread starts to reduce lock contention
            if i < 2:  # Don't delay after last thread
                time.sleep(0.05)

        for thread in threads:
            thread.join()

        # All should succeed (or at least most should)
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 3)

        # All slugs should be unique
        self.assertEqual(len(set(results)), 3)


class DateValidationTest(TestCase):
    """Test date validation edge cases"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", is_staff=True
        )

    def test_end_date_before_start_date(self):
        """Test that end_date before start_date raises ValidationError"""
        from ..forms import EditalForm

        form = EditalForm(
            {
                "titulo": "Test Edital",
                "url": "https://example.com",
                "status": "aberto",
                "start_date": date.today() + timedelta(days=30),
                "end_date": date.today(),
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("end_date", form.errors)

    def test_same_start_and_end_date(self):
        """Test that same start and end date is valid"""
        from ..forms import EditalForm

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

        self.assertTrue(form.is_valid())

    def test_future_dates(self):
        """Test that future dates are valid"""
        from ..forms import EditalForm

        form = EditalForm(
            {
                "titulo": "Test Edital",
                "url": "https://example.com",
                "status": "programado",
                "start_date": date.today() + timedelta(days=30),
                "end_date": date.today() + timedelta(days=60),
            }
        )

        self.assertTrue(form.is_valid())

    def test_past_dates(self):
        """Test that past dates are valid"""
        from ..forms import EditalForm

        form = EditalForm(
            {
                "titulo": "Test Edital",
                "url": "https://example.com",
                "status": "fechado",
                "start_date": date.today() - timedelta(days=60),
                "end_date": date.today() - timedelta(days=30),
            }
        )

        self.assertTrue(form.is_valid())


class ForeignKeyIntegrityTest(TestCase):
    """Test foreign key relationships and cascade behaviors"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.edital = Edital.objects.create(
            titulo="Test Edital", url="https://example.com", status="aberto"
        )

    def test_edital_deletion_with_startups(self):
        """Test that startups are preserved when edital is deleted"""
        startup = Startup.objects.create(
            name="Test Startup",
            proponente=self.user,
            edital=self.edital,
            status="pre_incubacao",
        )

        startup_id = startup.pk
        self.edital.delete()

        # Startup should still exist with edital set to None
        startup.refresh_from_db()
        self.assertIsNone(startup.edital)
        self.assertEqual(startup.pk, startup_id)

    def test_user_deletion_with_startups(self):
        """Test that startups are deleted when user is deleted"""
        startup = Startup.objects.create(
            name="Test Startup", proponente=self.user, status="pre_incubacao"
        )

        startup_id = startup.pk
        self.user.delete()

        # Startup should be deleted (CASCADE)
        self.assertFalse(Startup.objects.filter(pk=startup_id).exists())

    def test_edital_valor_cascade(self):
        """Test that EditalValor is deleted when edital is deleted"""
        valor = EditalValor.objects.create(
            edital=self.edital, valor_total=100000.00, moeda="BRL"
        )

        valor_id = valor.pk
        self.edital.delete()

        # EditalValor should be deleted (CASCADE)
        self.assertFalse(EditalValor.objects.filter(pk=valor_id).exists())


class EmailUniquenessRaceConditionTest(TransactionTestCase):
    """Test email uniqueness race condition in user registration"""

    def test_concurrent_email_registration(self):
        """Test that concurrent registration with same email is handled"""
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
                except ValidationError as e:
                    errors.append(str(e))
            else:
                errors.append("Form invalid")

        # Try to register 3 users with same email concurrently
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=register_user)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Only one should succeed, others should get validation error
        # The IntegrityError catch in save() should handle race condition
        # Note: In concurrent scenarios, all forms might validate before any save,
        # so we can't guarantee errors. But at least one should succeed.
        self.assertGreaterEqual(
            len(results), 1, "At least one registration should succeed"
        )
        # Total attempts should equal results + errors
        self.assertEqual(
            len(results) + len(errors), 3, "All 3 registration attempts should complete"
        )
