from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Edital


class EditaisCrudTest(TestCase):
    def setUp(self):
        # Create a test user for authenticated operations
        self.user = User.objects.create_user(
            username='admin',
            password='admin'
        )
        self.payload = {
            "titulo": "Edital Teste",
            "url": "https://example.com/edital-teste",
            "status": "aberto",
            "numero_edital": "001/2025",
            "entidade_principal": "Entidade Teste",
            "objetivo": "Objetivo do teste",
        }

    def test_index_page_loads(self):
        """Test that index page loads without authentication"""
        resp = self.client.get(reverse("editais_index"))
        self.assertEqual(resp.status_code, 200)

    def test_create_edital(self):
        """Test creating an edital (requires authentication)"""
        # Login first
        self.client.login(username='admin', password='admin')
        
        resp = self.client.post(reverse("edital_create"), data=self.payload, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Edital.objects.count(), 1)
        edital = Edital.objects.first()
        self.assertEqual(edital.titulo, self.payload["titulo"])
        self.assertEqual(edital.url, self.payload["url"])

    def test_update_edital(self):
        """Test updating an edital (requires authentication)"""
        # Login first
        self.client.login(username='admin', password='admin')
        
        # Create edital using model directly
        edital = Edital.objects.create(**self.payload)
        self.assertIsNotNone(edital.pk)
        
        # Update via view
        new_title = "Edital Teste Atualizado"
        update_payload = {**self.payload, "titulo": new_title}
        resp = self.client.post(reverse("edital_update", args=[edital.pk]), data=update_payload)
        self.assertEqual(resp.status_code, 302)
        edital.refresh_from_db()
        self.assertEqual(edital.titulo, new_title)

    def test_delete_edital(self):
        """Test deleting an edital (requires authentication)"""
        # Login first
        self.client.login(username='admin', password='admin')
        
        # Create edital using model directly
        edital = Edital.objects.create(**self.payload)
        self.assertIsNotNone(edital.pk)
        
        # Delete via view
        resp = self.client.post(reverse("edital_delete", args=[edital.pk]))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Edital.objects.count(), 0)

    def test_create_requires_authentication(self):
        """Test that create view requires authentication"""
        resp = self.client.get(reverse("edital_create"))
        # Should redirect to login
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/admin/login/', resp.url)

    def test_update_requires_authentication(self):
        """Test that update view requires authentication"""
        edital = Edital.objects.create(**self.payload)
        resp = self.client.get(reverse("edital_update", args=[edital.pk]))
        # Should redirect to login
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/admin/login/', resp.url)

    def test_delete_requires_authentication(self):
        """Test that delete view requires authentication"""
        edital = Edital.objects.create(**self.payload)
        resp = self.client.get(reverse("edital_delete", args=[edital.pk]))
        # Should redirect to login
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/admin/login/', resp.url)

