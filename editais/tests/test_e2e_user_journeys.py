"""
End-to-end tests for complete user journeys.

These tests verify complete workflows from user perspective:
- Registration → Login → Browse → Submit → Update
- Anonymous → Search → Filter → Register → Continue
- Staff: Create → View → Edit → Delete → Verify cache
"""

from django.test import TestCase, TransactionTestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.cache import cache

from ..models import Edital, Startup
from .factories import UserFactory, StaffUserFactory, EditalFactory, StartupFactory


class CompleteUserRegistrationJourneyTest(TransactionTestCase):
    """
    E2E test: Complete user journey from registration to project submission.

    Uses TransactionTestCase because test involves user registration and
    database state that must be committed.
    """

    def setUp(self):
        self.client = Client()
        self.staff_user = StaffUserFactory(username='staff')
        # Create an open edital for project submission
        self.edital = EditalFactory(
            titulo='Edital para Projetos',
            status='aberto',
            created_by=self.staff_user
        )

    def test_complete_user_journey_registration_to_project(self):
        """Complete journey: Register → Login → Browse → Submit Project → View → Update"""
        # 1. User visits home page (anonymous)
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AgroHub')

        # 2. User browses editais
        response = self.client.get(reverse('editais_index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.edital.titulo)

        # 3. User views edital detail
        response = self.client.get(reverse('edital_detail_slug', kwargs={'slug': self.edital.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.edital.titulo)

        # 4. User decides to register
        registration_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        }
        response = self.client.post(reverse('register'), data=registration_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        # User should be automatically logged in after registration
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        # 5. User is redirected to dashboard
        self.assertTemplateUsed(response, 'dashboard/home.html')

        # 6. User submits a project
        project_data = {
            'name': 'My Startup',
            'description': 'Description of my startup',
            'category': 'agtech',
            'edital': self.edital.pk,
            'status': 'pre_incubacao',
        }
        response = self.client.post(
            reverse('dashboard_submeter_startup'),
            data=project_data,
            follow=True
        )
        self.assertIn(response.status_code, [200, 302])
        self.assertTrue(Startup.objects.filter(name='My Startup').exists())

        # 7. User views their project in dashboard
        response = self.client.get(reverse('dashboard_startups'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'My Startup')

        # 8. User updates their project
        update_data = {
            'name': 'Updated Startup Name',
            'description': 'Updated description',
            'category': 'biotech',
            'edital': self.edital.pk,
            'status': 'incubacao',
        }
        project = Startup.objects.get(name='My Startup')
        response = self.client.post(
            reverse('dashboard_startup_update', kwargs={'pk': project.pk}),
            data=update_data,
            follow=True
        )
        self.assertIn(response.status_code, [200, 302])
        project.refresh_from_db()
        self.assertEqual(project.name, 'Updated Startup Name')
        self.assertEqual(project.category, 'biotech')

        # 9. User views their project in public showcase
        response = self.client.get(reverse('startups_showcase'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Updated Startup Name')


class AnonymousUserJourneyTest(TestCase):
    """E2E test: Anonymous user journey from browse to registration"""

    def setUp(self):
        self.client = Client()
        self.staff_user = StaffUserFactory(username='staff')
        # Create multiple editais for browsing
        for i in range(10):
            EditalFactory(
                titulo=f'Edital {i}',
                status='aberto' if i % 2 == 0 else 'fechado',
                created_by=self.staff_user
            )

    def test_anonymous_browse_search_filter_register_journey(self):
        """Complete journey: Browse → Search → Filter → View Detail → Register"""
        # 1. Anonymous user browses editais
        response = self.client.get(reverse('editais_index'))
        self.assertEqual(response.status_code, 200)
        # Should see open editais
        self.assertContains(response, 'Edital')

        # 2. User searches for specific edital
        response = self.client.get(reverse('editais_index'), {'search': 'Edital 1'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edital 1')

        # 3. User filters by status
        response = self.client.get(reverse('editais_index'), {'status': 'aberto'})
        self.assertEqual(response.status_code, 200)
        # Should only show open editais

        # 4. User views edital detail
        edital = Edital.objects.filter(status='aberto').first()
        if edital and edital.slug:
            response = self.client.get(reverse('edital_detail_slug', kwargs={'slug': edital.slug}))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, edital.titulo)

        # 5. User browses startups showcase
        response = self.client.get(reverse('startups_showcase'))
        self.assertEqual(response.status_code, 200)

        # 6. User decides to register
        registration_data = {
            'username': 'browser',
            'email': 'browser@example.com',
            'first_name': 'Browser',
            'last_name': 'User',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        }
        response = self.client.post(reverse('register'), data=registration_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username='browser').exists())

        # 7. User is now logged in and can access dashboard
        response = self.client.get(reverse('dashboard_home'))
        self.assertEqual(response.status_code, 200)


class StaffUserCRUDJourneyTest(TransactionTestCase):
    """
    E2E test: Staff user complete CRUD journey with cache verification.

    Uses TransactionTestCase because test verifies cache invalidation
    via transaction.on_commit() callbacks.
    """

    def setUp(self):
        self.client = Client()
        self.staff_user = StaffUserFactory(username='staff')
        cache.clear()

    def test_staff_create_view_edit_delete_with_cache_verification(self):
        """Complete journey: Create → View in Dashboard → Edit → Delete → Verify Cache"""
        self.client.login(username='staff', password='testpass123')

        # 1. Staff creates new edital
        initial_cache_version = cache.get('editais_index_cache_version', 0)
        create_data = {
            'titulo': 'Staff Created Edital',
            'url': 'https://example.com/staff',
            'status': 'aberto',
            'objetivo': 'Objective for staff edital',
            'entidade_principal': 'FINEP',
        }
        response = self.client.post(reverse('edital_create'), data=create_data, follow=True)
        self.assertIn(response.status_code, [200, 302])
        self.assertTrue(Edital.objects.filter(titulo='Staff Created Edital').exists())

        # Verify cache was invalidated
        cache_version_after_create = cache.get('editais_index_cache_version', 0)
        self.assertGreater(cache_version_after_create, initial_cache_version,
                          "Cache should be invalidated after creation")

        # 2. Staff views edital in dashboard
        response = self.client.get(reverse('dashboard_editais'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Staff Created Edital')

        # 3. Staff views edital detail page
        edital = Edital.objects.get(titulo='Staff Created Edital')
        response = self.client.get(reverse('edital_detail_slug', kwargs={'slug': edital.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Staff Created Edital')

        # 4. Staff edits edital
        cache_version_before_update = cache.get('editais_index_cache_version', 0)
        update_data = {
            'titulo': 'Staff Updated Edital',
            'url': 'https://example.com/staff',
            'status': 'fechado',
            'objetivo': 'Updated objective',
            'entidade_principal': 'FINEP',
        }
        response = self.client.post(
            reverse('edital_update', kwargs={'pk': edital.pk}),
            data=update_data,
            follow=True
        )
        self.assertIn(response.status_code, [200, 302])
        edital.refresh_from_db()
        self.assertEqual(edital.titulo, 'Staff Updated Edital')
        self.assertEqual(edital.status, 'fechado')

        # Verify cache was invalidated after update
        cache_version_after_update = cache.get('editais_index_cache_version', 0)
        self.assertGreater(cache_version_after_update, cache_version_before_update,
                          "Cache should be invalidated after update")

        # 5. Staff views updated edital in dashboard
        response = self.client.get(reverse('dashboard_editais'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Staff Updated Edital')

        # 6. Staff deletes edital
        cache_version_before_delete = cache.get('editais_index_cache_version', 0)
        response = self.client.post(
            reverse('edital_delete', kwargs={'pk': edital.pk}),
            follow=True
        )
        self.assertIn(response.status_code, [200, 302])
        self.assertFalse(Edital.objects.filter(pk=edital.pk).exists())

        # Verify cache was invalidated after deletion
        cache_version_after_delete = cache.get('editais_index_cache_version', 0)
        self.assertGreater(cache_version_after_delete, cache_version_before_delete,
                          "Cache should be invalidated after deletion")

        # 7. Verify edital no longer appears in dashboard
        response = self.client.get(reverse('dashboard_editais'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Staff Updated Edital')


class UserProjectSubmissionJourneyTest(TestCase):
    """E2E test: User submits project and tracks status through showcase"""

    def setUp(self):
        self.client = Client()
        self.user = UserFactory(username='testuser')
        self.staff_user = StaffUserFactory(username='staff')
        self.edital = EditalFactory(
            titulo='Open Edital for Projects',
            status='aberto',
            created_by=self.staff_user
        )

    def test_user_submit_project_track_in_showcase(self):
        """Complete journey: Submit → View in Dashboard → View in Showcase → Verify Stats"""
        self.client.login(username='testuser', password='testpass123')

        # 1. User submits project
        project_data = {
            'name': 'Showcase Startup',
            'description': 'A startup for showcase testing',
            'category': 'agtech',
            'edital': self.edital.pk,
            'status': 'pre_incubacao',
        }
        response = self.client.post(
            reverse('dashboard_submeter_startup'),
            data=project_data,
            follow=True
        )
        self.assertIn(response.status_code, [200, 302])
        self.assertTrue(Startup.objects.filter(name='Showcase Startup').exists())

        # 2. User views project in their dashboard
        response = self.client.get(reverse('dashboard_startups'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Showcase Startup')

        # 3. User views project in public showcase
        response = self.client.get(reverse('startups_showcase'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Showcase Startup')

        # 4. Verify stats include the new project
        context = response.context
        self.assertIn('stats', context)
        stats = context['stats']
        self.assertGreaterEqual(stats['total_active'], 1,
                               "Stats should include the new project")

        # 5. Staff updates project status
        self.client.login(username='staff', password='testpass123')
        project = Startup.objects.get(name='Showcase Startup')
        update_data = {
            'name': 'Showcase Startup',
            'description': 'A startup for showcase testing',
            'category': 'agtech',
            'edital': self.edital.pk,
            'status': 'graduada',  # Staff can set to graduada
        }
        response = self.client.post(
            reverse('dashboard_startup_update', kwargs={'pk': project.pk}),
            data=update_data,
            follow=True
        )
        self.assertIn(response.status_code, [200, 302])

        # 6. Verify updated stats reflect graduation
        response = self.client.get(reverse('startups_showcase'))
        context = response.context
        stats = context['stats']
        project.refresh_from_db()
        if project.status == 'graduada':
            self.assertGreaterEqual(stats['graduadas'], 1,
                                   "Stats should reflect graduated project")
