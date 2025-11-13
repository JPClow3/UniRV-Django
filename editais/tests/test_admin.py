"""
Testes para funcionalidades administrativas do app editais.
"""

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from editais.models import Edital, Cronograma, EditalValor
from datetime import timedelta
from django.utils import timezone


class EditalAdminTest(TestCase):
    """Testes para interface administrativa de editais."""
    
    def setUp(self):
        """Criar usuário admin e editais de teste."""
        self.admin = User.objects.create_user(
            username='admin',
            password='admin123',
            is_staff=True,
            is_superuser=True
        )
        self.client = Client()
        self.client.login(username='admin', password='admin123')
        
        # Criar editais com diferentes status
        self.edital1 = Edital.objects.create(
            titulo="Edital Aberto",
            url="https://example.com/1",
            status='aberto',
            entidade_principal="CNPq",
            numero_edital="001/2025"
        )
        self.edital2 = Edital.objects.create(
            titulo="Edital Fechado",
            url="https://example.com/2",
            status='fechado',
            entidade_principal="FAPEG",
            numero_edital="002/2025"
        )
        self.edital3 = Edital.objects.create(
            titulo="Edital Programado",
            url="https://example.com/3",
            status='programado',
            entidade_principal="SEBRAE",
            numero_edital="003/2025",
            start_date=timezone.now().date() + timedelta(days=10)
        )
    
    def test_admin_can_access_create_page(self):
        """Testa que admin pode acessar página de criação."""
        resp = self.client.get(reverse('edital_create'))
        self.assertEqual(resp.status_code, 200)
    
    def test_admin_can_create_edital(self):
        """Testa que admin pode criar edital."""
        data = {
            'titulo': 'Novo Edital',
            'url': 'https://example.com/new',
            'status': 'aberto',
            'numero_edital': '004/2025',
            'entidade_principal': 'CNPq',
            'objetivo': 'Objetivo do novo edital'
        }
        resp = self.client.post(reverse('edital_create'), data=data)
        # Deve redirecionar após criar
        self.assertEqual(resp.status_code, 302)
        # Verificar que foi criado
        self.assertTrue(Edital.objects.filter(titulo='Novo Edital').exists())
    
    def test_admin_can_access_update_page(self):
        """Testa que admin pode acessar página de edição."""
        resp = self.client.get(reverse('edital_update', args=[self.edital1.pk]))
        self.assertEqual(resp.status_code, 200)
    
    def test_admin_can_update_edital(self):
        """Testa que admin pode atualizar edital."""
        data = {
            'titulo': 'Edital Atualizado',
            'url': self.edital1.url,
            'status': 'fechado',
            'numero_edital': self.edital1.numero_edital,
            'entidade_principal': self.edital1.entidade_principal
        }
        resp = self.client.post(reverse('edital_update', args=[self.edital1.pk]), data=data)
        # Deve redirecionar após atualizar
        self.assertEqual(resp.status_code, 302)
        # Verificar que foi atualizado
        self.edital1.refresh_from_db()
        self.assertEqual(self.edital1.titulo, 'Edital Atualizado')
        self.assertEqual(self.edital1.status, 'fechado')
    
    def test_admin_can_access_delete_page(self):
        """Testa que admin pode acessar página de confirmação de exclusão."""
        resp = self.client.get(reverse('edital_delete', args=[self.edital1.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.edital1.titulo)
    
    def test_admin_can_delete_edital(self):
        """Testa que admin pode deletar edital."""
        edital_to_delete = Edital.objects.create(
            titulo="Edital para Deletar",
            url="https://example.com/delete"
        )
        resp = self.client.post(reverse('edital_delete', args=[edital_to_delete.pk]))
        # Deve redirecionar após deletar
        self.assertEqual(resp.status_code, 302)
        # Verificar que foi deletado
        self.assertFalse(Edital.objects.filter(pk=edital_to_delete.pk).exists())
    
    def test_admin_can_view_all_editais(self):
        """Testa que admin pode ver todos os editais na lista."""
        # Criar edital em draft
        edital_draft = Edital.objects.create(
            titulo="Edital Draft",
            url="https://example.com/draft",
            status='draft'
        )
        
        # Admin pode ver todos os editais (incluindo draft)
        if edital_draft.slug:
            resp = self.client.get(reverse('edital_detail_slug', kwargs={'slug': edital_draft.slug}))
            self.assertEqual(resp.status_code, 200)
    
    def test_slug_not_editable(self):
        """Testa que slug não pode ser editado manualmente."""
        original_slug = self.edital1.slug
        # Tentar atualizar título (que não deve mudar o slug)
        data = {
            'titulo': 'Título Atualizado',
            'url': self.edital1.url,
            'status': self.edital1.status,
            'numero_edital': self.edital1.numero_edital,
            'entidade_principal': self.edital1.entidade_principal
        }
        self.client.post(reverse('edital_update', args=[self.edital1.pk]), data=data)
        self.edital1.refresh_from_db()
        # Slug não deve mudar quando título muda
        self.assertEqual(self.edital1.slug, original_slug)
    
    def test_created_by_tracked(self):
        """Testa que created_by é rastreado ao criar edital."""
        data = {
            'titulo': 'Edital com Rastreamento',
            'url': 'https://example.com/track',
            'status': 'aberto'
        }
        self.client.post(reverse('edital_create'), data=data)
        edital = Edital.objects.get(titulo='Edital com Rastreamento')
        self.assertEqual(edital.created_by, self.admin)
        self.assertEqual(edital.updated_by, self.admin)
    
    def test_updated_by_tracked(self):
        """Testa que updated_by é rastreado ao atualizar edital."""
        data = {
            'titulo': self.edital1.titulo,
            'url': self.edital1.url,
            'status': 'fechado',
            'numero_edital': self.edital1.numero_edital,
            'entidade_principal': self.edital1.entidade_principal
        }
        self.client.post(reverse('edital_update', args=[self.edital1.pk]), data=data)
        self.edital1.refresh_from_db()
        self.assertEqual(self.edital1.updated_by, self.admin)


class EditalAdminFiltersTest(TestCase):
    """Testes para filtros administrativos."""
    
    def setUp(self):
        """Criar usuário admin e editais com diferentes características."""
        self.admin = User.objects.create_user(
            username='admin',
            password='admin123',
            is_staff=True,
            is_superuser=True
        )
        self.client = Client()
        self.client.login(username='admin', password='admin123')
        
        # Criar editais com diferentes status
        self.edital_aberto = Edital.objects.create(
            titulo="Edital Aberto",
            url="https://example.com/aberto",
            status='aberto',
            entidade_principal="CNPq"
        )
        self.edital_fechado = Edital.objects.create(
            titulo="Edital Fechado",
            url="https://example.com/fechado",
            status='fechado',
            entidade_principal="FAPEG"
        )
        self.edital_programado = Edital.objects.create(
            titulo="Edital Programado",
            url="https://example.com/programado",
            status='programado',
            entidade_principal="SEBRAE"
        )
    
    def test_admin_can_search_by_title(self):
        """Testa que admin pode buscar por título na interface administrativa."""
        # Nota: Este teste verifica a funcionalidade de busca
        # Na prática, a busca administrativa seria testada via Django Admin
        # Aqui testamos que os editais existem e podem ser acessados
        resp = self.client.get(reverse('editais_index'), {'search': 'Aberto'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.edital_aberto.titulo)
    
    def test_admin_can_filter_by_status(self):
        """Testa que admin pode filtrar por status."""
        resp = self.client.get(reverse('editais_index'), {'status': 'aberto'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.edital_aberto.titulo)
        self.assertNotContains(resp, self.edital_fechado.titulo)
    
    def test_admin_can_filter_by_entity(self):
        """Testa que admin pode filtrar por entidade."""
        resp = self.client.get(reverse('editais_index'), {'search': 'CNPq'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.edital_aberto.titulo)
    
    def test_pagination_works(self):
        """Testa que paginação funciona na lista administrativa."""
        # Criar muitos editais para testar paginação
        for i in range(15):
            Edital.objects.create(
                titulo=f"Edital {i}",
                url=f"https://example.com/{i}",
                status='aberto'
            )
        
        # Acessar primeira página
        resp = self.client.get(reverse('editais_index'))
        self.assertEqual(resp.status_code, 200)
        # Verificar que paginação está presente
        self.assertIn('page_obj', resp.context)
        
        # Acessar segunda página
        resp = self.client.get(reverse('editais_index'), {'page': '2'})
        self.assertEqual(resp.status_code, 200)

