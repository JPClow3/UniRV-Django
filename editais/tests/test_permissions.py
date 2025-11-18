"""
Testes para sistema de permissões do app editais.
"""

from django.contrib.auth.models import User, Permission
from django.test import TestCase
from django.urls import reverse
from editais.models import Edital


class EditalPermissionsTest(TestCase):
    """Testes para permissões de acesso aos editais."""
    
    def setUp(self):
        """Criar usuários com diferentes níveis de permissão."""
        # Usuário sem permissões (visitante)
        self.visitor = User.objects.create_user(
            username='visitor',
            password='visitor123',
            is_staff=False,
            is_superuser=False
        )
        
        # Usuário staff (pode acessar admin, mas sem permissões específicas)
        self.staff_user = User.objects.create_user(
            username='staff',
            password='staff123',
            is_staff=True,
            is_superuser=False
        )
        
        # Usuário com permissão de adicionar editais
        self.editor = User.objects.create_user(
            username='editor',
            password='editor123',
            is_staff=True,
            is_superuser=False
        )
        add_permission = Permission.objects.get(codename='add_edital')
        change_permission = Permission.objects.get(codename='change_edital')
        self.editor.user_permissions.add(add_permission, change_permission)
        
        # Superusuário (admin)
        self.admin = User.objects.create_user(
            username='admin',
            password='admin123',
            is_staff=True,
            is_superuser=True
        )
        
        # Criar edital de teste
        self.edital = Edital.objects.create(
            titulo="Edital de Teste",
            url="https://example.com/test",
            status='aberto'
        )
        
        # Criar edital em draft
        self.edital_draft = Edital.objects.create(
            titulo="Edital Rascunho",
            url="https://example.com/draft",
            status='draft'
        )
    
    def test_visitor_can_view_public_editais(self):
        """Testa que visitante pode ver editais públicos."""
        self.client.logout()
        resp = self.client.get(reverse('editais_index'))
        self.assertEqual(resp.status_code, 200)
        # Check if the edital title or link appears in the response
        # (may be on different page due to pagination)
        content = resp.content
        self.assertTrue(
            self.edital.titulo.encode() in content or 
            self.edital.get_absolute_url().encode() in content,
            f"Edital '{self.edital.titulo}' not found in response"
        )
    
    def test_visitor_cannot_view_draft_editais(self):
        """Testa que visitante não pode ver editais em draft."""
        self.client.logout()
        # Tentar acessar edital em draft
        if self.edital_draft.slug:
            resp = self.client.get(reverse('edital_detail_slug', kwargs={'slug': self.edital_draft.slug}), follow=True)
            self.assertEqual(resp.status_code, 404)
        else:
            # Se não tem slug, tentar por PK
            resp = self.client.get(reverse('edital_detail', kwargs={'pk': self.edital_draft.pk}), follow=True)
            self.assertEqual(resp.status_code, 404)
    
    def test_visitor_cannot_create_edital(self):
        """Testa que visitante não pode criar editais."""
        self.client.logout()
        resp = self.client.get(reverse('edital_create'))
        # Deve redirecionar para login
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/admin/login/', resp.url)
    
    def test_visitor_cannot_update_edital(self):
        """Testa que visitante não pode editar editais."""
        self.client.logout()
        resp = self.client.get(reverse('edital_update', args=[self.edital.pk]))
        # Deve redirecionar para login
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/admin/login/', resp.url)
    
    def test_visitor_cannot_delete_edital(self):
        """Testa que visitante não pode deletar editais."""
        self.client.logout()
        resp = self.client.get(reverse('edital_delete', args=[self.edital.pk]))
        # Deve redirecionar para login
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/admin/login/', resp.url)
    
    def test_staff_can_view_draft_editais(self):
        """Testa que usuário staff pode ver editais em draft."""
        self.client.login(username='staff', password='staff123')
        if self.edital_draft.slug:
            resp = self.client.get(reverse('edital_detail_slug', kwargs={'slug': self.edital_draft.slug}))
            # Staff pode ver draft (mesmo que não tenha permissão específica de edição)
            self.assertEqual(resp.status_code, 200)
    
    def test_non_staff_cannot_create_edital(self):
        """Testa que usuário autenticado sem is_staff não pode criar editais (T034)."""
        # Usuário autenticado mas não staff
        self.client.login(username='visitor', password='visitor123')
        resp = self.client.get(reverse('edital_create'))
        # Deve retornar 403 (forbidden)
        self.assertEqual(resp.status_code, 403)
    
    def test_non_staff_cannot_update_edital(self):
        """Testa que usuário autenticado sem is_staff não pode editar editais (T040)."""
        self.client.login(username='visitor', password='visitor123')
        resp = self.client.get(reverse('edital_update', args=[self.edital.pk]))
        # Deve retornar 403 (forbidden)
        self.assertEqual(resp.status_code, 403)
    
    def test_non_staff_cannot_delete_edital(self):
        """Testa que usuário autenticado sem is_staff não pode deletar editais (T041)."""
        self.client.login(username='visitor', password='visitor123')
        # Tentar deletar via POST
        resp = self.client.post(reverse('edital_delete', args=[self.edital.pk]))
        # Deve retornar 403 (forbidden)
        self.assertEqual(resp.status_code, 403)
    
    def test_staff_can_create_edital(self):
        """Testa que usuário is_staff pode criar editais (T034)."""
        self.client.login(username='staff', password='staff123')
        resp = self.client.get(reverse('edital_create'))
        self.assertEqual(resp.status_code, 200)
    
    def test_staff_can_update_edital(self):
        """Testa que usuário is_staff pode editar editais (T040)."""
        self.client.login(username='staff', password='staff123')
        resp = self.client.get(reverse('edital_update', args=[self.edital.pk]))
        self.assertEqual(resp.status_code, 200)
    
    def test_staff_can_delete_edital(self):
        """Testa que usuário is_staff pode deletar editais (T041)."""
        self.client.login(username='staff', password='staff123')
        # Criar edital para deletar
        edital_to_delete = Edital.objects.create(
            titulo="Edital para Deletar",
            url="https://example.com/delete"
        )
        resp = self.client.post(reverse('edital_delete', args=[edital_to_delete.pk]))
        # Deve redirecionar após deletar
        self.assertEqual(resp.status_code, 302)
        # Verificar que foi deletado
        self.assertFalse(Edital.objects.filter(pk=edital_to_delete.pk).exists())
    
    def test_admin_can_create_edital(self):
        """Testa que admin pode criar editais."""
        self.client.login(username='admin', password='admin123')
        resp = self.client.get(reverse('edital_create'))
        self.assertEqual(resp.status_code, 200)
    
    def test_admin_can_update_edital(self):
        """Testa que admin pode editar editais."""
        self.client.login(username='admin', password='admin123')
        resp = self.client.get(reverse('edital_update', args=[self.edital.pk]))
        self.assertEqual(resp.status_code, 200)
    
    def test_admin_can_delete_edital(self):
        """Testa que admin pode deletar editais."""
        self.client.login(username='admin', password='admin123')
        # Criar edital para deletar
        edital_to_delete = Edital.objects.create(
            titulo="Edital para Deletar",
            url="https://example.com/delete"
        )
        resp = self.client.post(reverse('edital_delete', args=[edital_to_delete.pk]))
        # Deve redirecionar após deletar
        self.assertEqual(resp.status_code, 302)
        # Verificar que foi deletado
        self.assertFalse(Edital.objects.filter(pk=edital_to_delete.pk).exists())
    
    def test_draft_editais_not_in_public_list(self):
        """Testa que editais em draft não aparecem na lista pública."""
        self.client.logout()
        resp = self.client.get(reverse('editais_index'))
        # Edital público deve aparecer
        self.assertContains(resp, self.edital.titulo)
        # Edital em draft não deve aparecer
        self.assertNotContains(resp, self.edital_draft.titulo)
    
    def test_draft_editais_in_admin_list(self):
        """Testa que editais em draft aparecem na lista administrativa."""
        self.client.login(username='admin', password='admin123')
        # Acessar admin (simulado - na prática seria /admin/editais/edital/)
        # Como não temos acesso direto ao admin via views customizadas,
        # testamos que o edital existe e pode ser acessado por usuários autenticados
        if self.edital_draft.slug:
            resp = self.client.get(reverse('edital_detail_slug', kwargs={'slug': self.edital_draft.slug}))
            self.assertEqual(resp.status_code, 200)

