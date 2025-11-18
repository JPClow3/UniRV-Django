"""
Tests for dashboard views (dashboard_home, dashboard_editais, dashboard_projetos, etc.).
"""

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from ..models import Edital


class DashboardHomeViewTest(TestCase):
    """Tests for dashboard home view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_dashboard_home_requires_login(self):
        """Test that dashboard home requires authentication"""
        response = self.client.get(reverse('dashboard_home'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard_home')}")
    
    def test_dashboard_home_loads_for_authenticated_user(self):
        """Test that dashboard home loads for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard_home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/home.html')


class DashboardEditaisViewTest(TestCase):
    """Tests for dashboard editais view"""
    
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staff',
            password='testpass123',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='regular',
            password='testpass123',
            is_staff=False
        )
        self.edital = Edital.objects.create(
            titulo='Test Edital',
            url='https://example.com',
            status='aberto',
            created_by=self.staff_user
        )
    
    def test_dashboard_editais_requires_login(self):
        """Test that dashboard editais requires authentication"""
        response = self.client.get(reverse('dashboard_editais'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard_editais')}")
    
    def test_dashboard_editais_requires_staff(self):
        """Test that dashboard editais requires staff permission"""
        self.client.login(username='regular', password='testpass123')
        response = self.client.get(reverse('dashboard_editais'))
        self.assertEqual(response.status_code, 403)
    
    def test_dashboard_editais_loads_for_staff(self):
        """Test that dashboard editais loads for staff user"""
        self.client.login(username='staff', password='testpass123')
        response = self.client.get(reverse('dashboard_editais'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/editais.html')
    
    def test_dashboard_editais_search_filter(self):
        """Test search and filter functionality"""
        self.client.login(username='staff', password='testpass123')
        response = self.client.get(reverse('dashboard_editais'), {
            'search': 'Test',
            'status': 'aberto'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Edital')
    
    def test_dashboard_editais_tipo_filter(self):
        """Test tipo filter (Fluxo Contínuo vs Fomento)"""
        self.client.login(username='staff', password='testpass123')
        # Test Fomento filter (has end_date)
        edital_fomento = Edital.objects.create(
            titulo='Fomento Edital',
            url='https://example.com/fomento',
            status='aberto',
            end_date=timezone.now().date() + timedelta(days=30),
            created_by=self.staff_user
        )
        response = self.client.get(reverse('dashboard_editais'), {'tipo': 'Fomento'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Fomento Edital')


class DashboardProjetosViewTest(TestCase):
    """Tests for dashboard projetos view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_dashboard_projetos_requires_login(self):
        """Test that dashboard projetos requires authentication"""
        response = self.client.get(reverse('dashboard_projetos'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard_projetos')}")
    
    def test_dashboard_projetos_loads_for_authenticated_user(self):
        """Test that dashboard projetos loads for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard_projetos'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/projetos.html')


class DashboardAvaliacoesViewTest(TestCase):
    """Tests for dashboard avaliações view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_dashboard_avaliacoes_requires_login(self):
        """Test that dashboard avaliações requires authentication"""
        response = self.client.get(reverse('dashboard_avaliacoes'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard_avaliacoes')}")
    
    def test_dashboard_avaliacoes_loads_for_authenticated_user(self):
        """Test that dashboard avaliações loads for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard_avaliacoes'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/avaliacoes.html')


class DashboardUsuariosViewTest(TestCase):
    """Tests for dashboard usuarios view"""
    
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staff',
            password='testpass123',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='regular',
            password='testpass123',
            is_staff=False
        )
    
    def test_dashboard_usuarios_requires_login(self):
        """Test that dashboard usuarios requires authentication"""
        response = self.client.get(reverse('dashboard_usuarios'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard_usuarios')}")
    
    def test_dashboard_usuarios_requires_staff(self):
        """Test that dashboard usuarios requires staff permission"""
        self.client.login(username='regular', password='testpass123')
        response = self.client.get(reverse('dashboard_usuarios'))
        self.assertEqual(response.status_code, 403)
    
    def test_dashboard_usuarios_loads_for_staff(self):
        """Test that dashboard usuarios loads for staff user"""
        self.client.login(username='staff', password='testpass123')
        response = self.client.get(reverse('dashboard_usuarios'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/usuarios.html')


class DashboardRelatoriosViewTest(TestCase):
    """Tests for dashboard relatorios view"""
    
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staff',
            password='testpass123',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='regular',
            password='testpass123',
            is_staff=False
        )
    
    def test_dashboard_relatorios_requires_login(self):
        """Test that dashboard relatorios requires authentication"""
        response = self.client.get(reverse('dashboard_relatorios'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard_relatorios')}")
    
    def test_dashboard_relatorios_requires_staff(self):
        """Test that dashboard relatorios requires staff permission"""
        self.client.login(username='regular', password='testpass123')
        response = self.client.get(reverse('dashboard_relatorios'))
        self.assertEqual(response.status_code, 403)
    
    def test_dashboard_relatorios_loads_for_staff(self):
        """Test that dashboard relatorios loads for staff user"""
        self.client.login(username='staff', password='testpass123')
        response = self.client.get(reverse('dashboard_relatorios'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/relatorios.html')


class DashboardPublicacoesViewTest(TestCase):
    """Tests for dashboard publicacoes view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    


class DashboardNovoEditalViewTest(TestCase):
    """Tests for dashboard novo edital view"""
    
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staff',
            password='testpass123',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='regular',
            password='testpass123',
            is_staff=False
        )
    
    def test_dashboard_novo_edital_requires_login(self):
        """Test that dashboard novo edital requires authentication"""
        response = self.client.get(reverse('dashboard_novo_edital'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard_novo_edital')}")
    
    def test_dashboard_novo_edital_requires_staff(self):
        """Test that dashboard novo edital requires staff permission"""
        self.client.login(username='regular', password='testpass123')
        response = self.client.get(reverse('dashboard_novo_edital'))
        self.assertEqual(response.status_code, 403)
    
    def test_dashboard_novo_edital_loads_for_staff(self):
        """Test that dashboard novo edital loads for staff user"""
        self.client.login(username='staff', password='testpass123')
        response = self.client.get(reverse('dashboard_novo_edital'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/novo_edital.html')


class DashboardSubmeterProjetoViewTest(TestCase):
    """Tests for dashboard submeter projeto view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_dashboard_submeter_projeto_requires_login(self):
        """Test that dashboard submeter projeto requires authentication"""
        response = self.client.get(reverse('dashboard_submeter_projeto'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard_submeter_projeto')}")
    
    def test_dashboard_submeter_projeto_loads_for_authenticated_user(self):
        """Test that dashboard submeter projeto loads for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard_submeter_projeto'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/submeter_projeto.html')

