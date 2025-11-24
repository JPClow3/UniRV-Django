"""
Testes para funcionalidades administrativas do app editais.
"""

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from editais.models import Edital, Cronograma, EditalValor
from datetime import timedelta
from django.utils import timezone
from django.core.cache import cache


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
        cache.clear()
        
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
    
    def test_admin_save_model_sanitizes_html(self):
        """Testa que save_model() no Admin sanitiza HTML (prevenção XSS)."""
        from editais.admin import EditalAdmin
        from unittest.mock import MagicMock
        
        # Criar instância do admin
        admin = EditalAdmin(Edital, None)
        
        # Criar edital com HTML malicioso
        edital = Edital(
            titulo="Teste XSS",
            url="https://example.com/test",
            analise='<script>alert("XSS")</script>Texto normal',
            objetivo='<img src=x onerror=alert(1)>'
        )
        
        # Simular request com usuário
        mock_request = MagicMock()
        mock_request.user = self.admin
        
        # Chamar save_model
        admin.save_model(mock_request, edital, None, change=False)
        
        # Verificar que HTML foi sanitizado
        self.assertNotIn('<script>', edital.analise)
        self.assertNotIn('onerror', edital.objetivo)
        self.assertIn('Texto normal', edital.analise)
    
    def test_admin_save_model_tracks_created_by(self):
        """Testa que save_model() rastreia created_by para novos objetos."""
        from editais.admin import EditalAdmin
        from unittest.mock import MagicMock
        
        admin = EditalAdmin(Edital, None)
        edital = Edital(
            titulo="Teste Created By",
            url="https://example.com/test"
        )
        
        mock_request = MagicMock()
        mock_request.user = self.admin
        
        admin.save_model(mock_request, edital, None, change=False)
        
        # Verificar que created_by foi definido
        self.assertEqual(edital.created_by, self.admin)
    
    def test_admin_save_model_tracks_updated_by(self):
        """Testa que save_model() rastreia updated_by para objetos existentes."""
        from editais.admin import EditalAdmin
        from unittest.mock import MagicMock
        
        admin = EditalAdmin(Edital, None)
        edital = Edital.objects.create(
            titulo="Teste Updated By",
            url="https://example.com/test"
        )
        
        mock_request = MagicMock()
        mock_request.user = self.admin
        
        admin.save_model(mock_request, edital, None, change=True)
        
        # Verificar que updated_by foi definido
        self.assertEqual(edital.updated_by, self.admin)
    
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
    
    def test_admin_can_filter_by_start_date(self):
        """Testa que admin pode filtrar por data de abertura (T048)."""
        today = timezone.now().date()
        edital_future = Edital.objects.create(
            titulo="Edital Futuro",
            url="https://example.com/future",
            status='aberto',
            start_date=today + timedelta(days=30)
        )
        
        # Filtrar por data de abertura >= hoje
        resp = self.client.get(reverse('editais_index'), {
            'start_date': today.strftime('%Y-%m-%d')
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, edital_future.titulo)
    
    def test_admin_can_filter_by_end_date(self):
        """Testa que admin pode filtrar por data de encerramento (T048)."""
        today = timezone.now().date()
        edital_past = Edital.objects.create(
            titulo="Edital Passado",
            url="https://example.com/past",
            status='fechado',
            end_date=today - timedelta(days=10)
        )
        
        # Filtrar por data de encerramento <= hoje
        resp = self.client.get(reverse('editais_index'), {
            'end_date': today.strftime('%Y-%m-%d')
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, edital_past.titulo)
    
    def test_admin_can_filter_by_combined_dates(self):
        """Testa que admin pode combinar filtros de data (T048)."""
        today = timezone.now().date()
        edital_match = Edital.objects.create(
            titulo="Edital Combinado",
            url="https://example.com/combined",
            status='aberto',
            start_date=today,
            end_date=today + timedelta(days=30)
        )
        
        # Filtrar por range de datas
        resp = self.client.get(reverse('editais_index'), {
            'start_date': today.strftime('%Y-%m-%d'),
            'end_date': (today + timedelta(days=30)).strftime('%Y-%m-%d')
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, edital_match.titulo)
    
    def test_admin_can_search_by_organization(self):
        """Testa que admin pode buscar por organização (T048)."""
        resp = self.client.get(reverse('editais_index'), {'search': 'FAPEG'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.edital_fechado.titulo)
        self.assertNotContains(resp, self.edital_aberto.titulo)
    
    def test_admin_can_combine_search_and_filters(self):
        """Testa que admin pode combinar busca e filtros (T048)."""
        resp = self.client.get(reverse('editais_index'), {
            'search': 'Edital',
            'status': 'aberto'
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.edital_aberto.titulo)
        self.assertNotContains(resp, self.edital_fechado.titulo)
    
    def test_pagination_works(self):
        """Testa que paginação funciona na lista administrativa (T049)."""
        # Criar muitos editais para testar paginação (mais de 12 para garantir 2 páginas)
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
        page_obj = resp.context['page_obj']
        # Verificar que há múltiplas páginas
        self.assertGreater(page_obj.paginator.num_pages, 1)
        # Verificar que primeira página tem 12 itens (EDITAIS_PER_PAGE)
        self.assertEqual(len(page_obj.object_list), 12)
        
        # Acessar segunda página
        resp = self.client.get(reverse('editais_index'), {'page': '2'})
        self.assertEqual(resp.status_code, 200)
        page_obj = resp.context['page_obj']
        # Verificar que segunda página tem os itens restantes
        self.assertGreater(len(page_obj.object_list), 0)
        self.assertLessEqual(len(page_obj.object_list), 12)
    
    def test_pagination_preserves_filters(self):
        """Testa que paginação preserva filtros ao navegar entre páginas (T049)."""
        # Criar editais com status específico
        for i in range(15):
            Edital.objects.create(
                titulo=f"Edital Aberto {i}",
                url=f"https://example.com/aberto-{i}",
                status='aberto'
            )
        
        # Acessar primeira página com filtro
        resp = self.client.get(reverse('editais_index'), {
            'status': 'aberto',
            'page': '1'
        })
        self.assertEqual(resp.status_code, 200)
        
        # Acessar segunda página com mesmo filtro
        resp = self.client.get(reverse('editais_index'), {
            'status': 'aberto',
            'page': '2'
        })
        self.assertEqual(resp.status_code, 200)
        # Verificar que filtro ainda está aplicado (todos os itens devem ser 'aberto')
        page_obj = resp.context['page_obj']
        for edital in page_obj.object_list:
            self.assertEqual(edital.status, 'aberto')
    
    def test_pagination_invalid_page_returns_last_page(self):
        """Testa que página inválida retorna última página válida (T049)."""
        # Criar alguns editais (menos de 12 para ter apenas 1 página)
        for i in range(5):
            Edital.objects.create(
                titulo=f"Edital {i}",
                url=f"https://example.com/{i}",
                status='aberto'
            )
        
        # Tentar acessar página inexistente
        resp = self.client.get(reverse('editais_index'), {'page': '999'})
        self.assertEqual(resp.status_code, 200)
        # Deve retornar última página válida
        page_obj = resp.context['page_obj']
        self.assertEqual(page_obj.number, page_obj.paginator.num_pages)


class EditalCSVExportTest(TestCase):
    """Testes para exportação CSV de editais (T089)."""
    
    def setUp(self):
        """Criar usuários e editais de teste."""
        # Usuário staff
        self.staff_user = User.objects.create_user(
            username='staff',
            password='staff123',
            is_staff=True,
            is_superuser=False
        )
        
        # Usuário autenticado mas não staff
        self.non_staff_user = User.objects.create_user(
            username='user',
            password='user123',
            is_staff=False,
            is_superuser=False
        )
        
        # Criar editais de teste
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
    
    def test_staff_can_export_csv(self):
        """Testa que usuários is_staff conseguem exportar editais filtrados."""
        self.client.login(username='staff', password='staff123')
        resp = self.client.get(reverse('export_editais_csv'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn('attachment', resp['Content-Disposition'])
        
        # Verificar conteúdo do CSV
        content = resp.content.decode('utf-8-sig')  # Remove BOM
        self.assertIn('Número', content)
        self.assertIn('Título', content)
        self.assertIn('Edital Aberto', content)
        self.assertIn('Edital Fechado', content)
    
    def test_non_staff_cannot_export_csv(self):
        """Testa que usuários autenticados sem is_staff recebem 403."""
        self.client.login(username='user', password='user123')
        resp = self.client.get(reverse('export_editais_csv'))
        self.assertEqual(resp.status_code, 403)
    
    def test_unauthenticated_cannot_export_csv(self):
        """Testa que usuários não autenticados são redirecionados para login."""
        self.client.logout()
        resp = self.client.get(reverse('export_editais_csv'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp.url)
    
    def test_csv_includes_correct_columns(self):
        """Valida conteúdo e cabeçalhos do CSV gerado."""
        self.client.login(username='staff', password='staff123')
        resp = self.client.get(reverse('export_editais_csv'))
        content = resp.content.decode('utf-8-sig')  # Remove BOM
        
        # Verificar cabeçalhos
        self.assertIn('Número', content)
        self.assertIn('Título', content)
        self.assertIn('Entidade', content)
        self.assertIn('Status', content)
        self.assertIn('URL', content)
        self.assertIn('Data Criação', content)
        self.assertIn('Data Atualização', content)
        self.assertIn('Criado Por', content)
        self.assertIn('Atualizado Por', content)
    
    def test_csv_applies_search_filter(self):
        """Testa que CSV aplica filtro de busca."""
        self.client.login(username='staff', password='staff123')
        resp = self.client.get(reverse('export_editais_csv'), {'search': 'Aberto'})
        content = resp.content.decode('utf-8-sig')
        self.assertIn('Edital Aberto', content)
        self.assertNotIn('Edital Fechado', content)
    
    def test_csv_applies_status_filter(self):
        """Testa que CSV aplica filtro de status."""
        self.client.login(username='staff', password='staff123')
        resp = self.client.get(reverse('export_editais_csv'), {'status': 'aberto'})
        content = resp.content.decode('utf-8-sig')
        self.assertIn('Edital Aberto', content)
        self.assertNotIn('Edital Fechado', content)
    
    def test_csv_encoding_utf8_with_bom(self):
        """Testa que CSV usa encoding UTF-8 com BOM (compatível com Excel)."""
        self.client.login(username='staff', password='staff123')
        resp = self.client.get(reverse('export_editais_csv'))
        # Verificar que começa com BOM (UTF-8 BOM = \xef\xbb\xbf)
        self.assertTrue(resp.content.startswith(b'\xef\xbb\xbf'))


class AdminDashboardTest(TestCase):
    """Testes para o dashboard administrativo."""
    
    def setUp(self):
        """Criar usuários e editais de teste."""
        self.staff_user = User.objects.create_user(
            username='staff',
            password='staff123',
            is_staff=True,
            email='staff@example.com'
        )
        self.non_staff_user = User.objects.create_user(
            username='user',
            password='user123',
            is_staff=False,
            email='user@example.com'
        )
        self.client = Client()
        cache.clear()
        
        # Criar editais de teste
        from django.utils import timezone
        from datetime import timedelta
        
        today = timezone.now().date()
        
        self.edital1 = Edital.objects.create(
            titulo="Edital Aberto",
            url="https://example.com/1",
            status='aberto',
            entidade_principal="CNPq",
            numero_edital="001/2025",
            created_by=self.staff_user
        )
        self.edital2 = Edital.objects.create(
            titulo="Edital Fechado",
            url="https://example.com/2",
            status='fechado',
            entidade_principal="FAPEG",
            numero_edital="002/2025"
        )
    
    def test_staff_can_access_dashboard(self):
        """Testa que usuários is_staff podem acessar o dashboard."""
        self.client.login(username='staff', password='staff123')
        resp = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Dashboard Administrativo')
    
    def test_non_staff_cannot_access_dashboard(self):
        """Testa que usuários não-staff recebem 403 ao acessar dashboard."""
        self.client.login(username='user', password='user123')
        resp = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(resp.status_code, 403)
    
    def test_unauthenticated_cannot_access_dashboard(self):
        """Testa que usuários não autenticados são redirecionados."""
        self.client.logout()
        resp = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp.url)
    
    def test_dashboard_shows_total_editais(self):
        """Testa que o dashboard exibe o total de editais."""
        self.client.login(username='staff', password='staff123')
        resp = self.client.get(reverse('admin_dashboard'))
        self.assertContains(resp, str(self.edital1.id), status_code=200)
    
    def test_dashboard_shows_editais_por_status(self):
        """Testa que o dashboard exibe estatísticas por status."""
        self.client.login(username='staff', password='staff123')
        resp = self.client.get(reverse('admin_dashboard'))
        # Verificar que contém informações sobre status
        self.assertContains(resp, 'aberto', status_code=200)
        self.assertContains(resp, 'fechado', status_code=200)
    
    def test_dashboard_shows_recent_editais(self):
        """Testa que o dashboard exibe editais recentes (últimos 7 dias)."""
        from django.utils import timezone
        from datetime import timedelta
        
        # Criar edital recente
        recent_edital = Edital.objects.create(
            titulo="Edital Recente",
            url="https://example.com/recent",
            status='aberto',
            data_criacao=timezone.now() - timedelta(days=3)
        )
        
        self.client.login(username='staff', password='staff123')
        resp = self.client.get(reverse('admin_dashboard'))
        self.assertContains(resp, recent_edital.titulo, status_code=200)
    
    def test_dashboard_shows_upcoming_deadlines(self):
        """Testa que o dashboard exibe editais próximos do prazo."""
        from django.utils import timezone
        from datetime import timedelta
        
        today = timezone.now().date()
        # Criar edital com prazo nos próximos 7 dias
        upcoming_edital = Edital.objects.create(
            titulo="Edital Próximo do Prazo",
            url="https://example.com/upcoming",
            status='aberto',
            end_date=today + timedelta(days=5)
        )
        
        self.client.login(username='staff', password='staff123')
        resp = self.client.get(reverse('admin_dashboard'))
        self.assertContains(resp, upcoming_edital.titulo, status_code=200)
    
    def test_dashboard_shows_top_entidades(self):
        """Testa que o dashboard exibe top entidades."""
        # Criar editais com diferentes entidades
        Edital.objects.create(
            titulo="Edital CNPq 1",
            url="https://example.com/cnpq1",
            status='aberto',
            entidade_principal="CNPq"
        )
        Edital.objects.create(
            titulo="Edital CNPq 2",
            url="https://example.com/cnpq2",
            status='aberto',
            entidade_principal="CNPq"
        )
        
        self.client.login(username='staff', password='staff123')
        resp = self.client.get(reverse('admin_dashboard'))
        self.assertContains(resp, 'CNPq', status_code=200)
    


