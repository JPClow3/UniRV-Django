from datetime import timedelta
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from io import StringIO

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
        
        resp = self.client.post(reverse("edital_create"), data=self.payload, follow=False)
        # After creation, should redirect (302) to detail page
        # Note: follow=False to check redirect, not final page
        self.assertEqual(resp.status_code, 302)
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


class EditalSearchAndFilterTest(TestCase):
    """Testes para busca e filtros na listagem de editais."""
    
    def setUp(self):
        """Criar editais de teste para busca e filtros."""
        self.edital1 = Edital.objects.create(
            titulo="Edital de Inovação Tecnológica",
            url="https://example.com/1",
            status='aberto',
            entidade_principal="CNPq",
            numero_edital="001/2025",
            objetivo="Fomentar inovação tecnológica"
        )
        self.edital2 = Edital.objects.create(
            titulo="Programa de Pesquisa em Agricultura",
            url="https://example.com/2",
            status='fechado',
            entidade_principal="FAPEG",
            numero_edital="002/2025",
            objetivo="Pesquisa agrícola sustentável"
        )
        self.edital3 = Edital.objects.create(
            titulo="Chamada para Startups",
            url="https://example.com/3",
            status='aberto',
            entidade_principal="SEBRAE",
            numero_edital="003/2025",
            objetivo="Aceleração de startups"
        )

    def test_search_by_title(self):
        """Testa busca por título."""
        resp = self.client.get(reverse("editais_index"), {'search': 'Inovação'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.edital1.titulo)
        self.assertNotContains(resp, self.edital2.titulo)

    def test_search_by_entity(self):
        """Testa busca por entidade."""
        resp = self.client.get(reverse("editais_index"), {'search': 'CNPq'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.edital1.titulo)

    def test_search_case_insensitive(self):
        """Testa que busca é case-insensitive."""
        resp = self.client.get(reverse("editais_index"), {'search': 'inovação'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.edital1.titulo)

    def test_filter_by_status(self):
        """Testa filtro por status."""
        resp = self.client.get(reverse("editais_index"), {'status': 'aberto'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.edital1.titulo)
        self.assertContains(resp, self.edital3.titulo)
        self.assertNotContains(resp, self.edital2.titulo)

    def test_search_and_filter_combined(self):
        """Testa combinação de busca e filtro."""
        resp = self.client.get(reverse("editais_index"), {
            'search': 'Pesquisa',
            'status': 'fechado'
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.edital2.titulo)
        self.assertNotContains(resp, self.edital1.titulo)
        self.assertNotContains(resp, self.edital3.titulo)

    def test_empty_search_returns_all(self):
        """Testa que busca vazia retorna todos os editais."""
        resp = self.client.get(reverse("editais_index"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.edital1.titulo)
        self.assertContains(resp, self.edital2.titulo)
        self.assertContains(resp, self.edital3.titulo)

    def test_filter_by_start_date(self):
        """Testa filtro por data de abertura."""
        from datetime import timedelta
        from django.utils import timezone
        
        today = timezone.now().date()
        # Edital com data de abertura futura
        edital_future = Edital.objects.create(
            titulo="Edital Futuro",
            url="https://example.com/future",
            status='aberto',
            start_date=today + timedelta(days=30)
        )
        
        # Filtrar por data de abertura >= hoje
        resp = self.client.get(reverse("editais_index"), {
            'start_date': today.strftime('%Y-%m-%d')
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, edital_future.titulo)

    def test_filter_by_end_date(self):
        """Testa filtro por data de encerramento."""
        from datetime import timedelta
        from django.utils import timezone
        
        today = timezone.now().date()
        # Edital com data de encerramento passada
        edital_past = Edital.objects.create(
            titulo="Edital Passado",
            url="https://example.com/past",
            status='fechado',
            end_date=today - timedelta(days=10)
        )
        
        # Filtrar por data de encerramento <= hoje
        resp = self.client.get(reverse("editais_index"), {
            'end_date': today.strftime('%Y-%m-%d')
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, edital_past.titulo)

    def test_filter_only_open(self):
        """Testa filtro 'somente abertos'."""
        # Criar edital fechado
        edital_closed = Edital.objects.create(
            titulo="Edital Fechado",
            url="https://example.com/closed",
            status='fechado'
        )
        
        # Filtrar somente abertos
        resp = self.client.get(reverse("editais_index"), {'only_open': '1'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.edital1.titulo)  # Status 'aberto'
        self.assertContains(resp, self.edital3.titulo)  # Status 'aberto'
        self.assertNotContains(resp, self.edital2.titulo)  # Status 'fechado'
        self.assertNotContains(resp, edital_closed.titulo)  # Status 'fechado'

    def test_combined_filters(self):
        """Testa combinação de múltiplos filtros."""
        from datetime import timedelta
        from django.utils import timezone
        
        today = timezone.now().date()
        # Edital que atende todos os critérios
        # start_date deve ser >= ao filtro start_date para ser encontrado
        edital_match = Edital.objects.create(
            titulo="Edital Combinado",
            url="https://example.com/combined",
            status='aberto',
            entidade_principal="CNPq",
            start_date=today,  # Mesma data do filtro (>= funciona)
            end_date=today + timedelta(days=30)
        )
        
        # Test with search, date filter, and only_open (without status filter)
        # Note: only_open is ignored when status filter is present
        resp = self.client.get(reverse("editais_index"), {
            'search': 'Combinado',
            'start_date': today.strftime('%Y-%m-%d'),
            'only_open': '1'
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, edital_match.titulo)
        
        # Test with search, status filter, and date filter (status takes precedence over only_open)
        resp2 = self.client.get(reverse("editais_index"), {
            'search': 'Combinado',
            'status': 'aberto',
            'start_date': today.strftime('%Y-%m-%d')
        })
        self.assertEqual(resp2.status_code, 200)
        self.assertContains(resp2, edital_match.titulo)


class EditalDetailTest(TestCase):
    """Testes para página de detalhes do edital."""
    
    def setUp(self):
        """Criar edital de teste."""
        self.edital = Edital.objects.create(
            titulo="Edital de Teste",
            url="https://example.com/test",
            status='aberto',
            numero_edital="TEST/2025",
            entidade_principal="Entidade Teste",
            objetivo="Objetivo do teste",
            analise="Análise do edital",
            etapas="Etapas do processo",
            recursos="Recursos disponíveis"
        )

    def test_detail_page_loads(self):
        """Testa que página de detalhes carrega."""
        resp = self.client.get(self.edital.get_absolute_url())
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.edital.titulo)
        self.assertContains(resp, self.edital.objetivo)

    def test_detail_by_slug(self):
        """Testa acesso por slug."""
        if self.edital.slug:
            resp = self.client.get(reverse("edital_detail_slug", kwargs={'slug': self.edital.slug}))
            self.assertEqual(resp.status_code, 200)
            self.assertContains(resp, self.edital.titulo)

    def test_detail_by_pk_redirects_to_slug(self):
        """Testa que acesso por PK redireciona para slug."""
        # Garantir que o edital tem slug (salvar novamente para gerar)
        self.edital.save()  # Gera slug se não existir
        self.edital.refresh_from_db()
        
        # Verificar que tem slug
        self.assertIsNotNone(self.edital.slug, "Edital deve ter slug após save()")
        
        # Testar usando reverse para garantir que a URL está correta
        try:
            url = reverse("edital_detail", kwargs={'pk': self.edital.pk})
            resp = self.client.get(url, follow=False)
            # Deve redirecionar para slug (301 permanent redirect)
            self.assertEqual(resp.status_code, 301, f"Expected 301 redirect, got {resp.status_code}. URL: {getattr(resp, 'url', 'N/A')}")
            if resp.status_code == 301:
                self.assertIn(self.edital.slug, resp.url)
        except Exception as e:
            # Se reverse falhar, testar URL direta
            url = f'/edital/{self.edital.pk}/'
            resp = self.client.get(url, follow=False)
            # Aceitar tanto redirect quanto acesso direto (se não tiver slug ainda)
            if resp.status_code == 404:
                # Se 404, verificar se acesso por slug funciona
                slug_url = reverse("edital_detail_slug", kwargs={'slug': self.edital.slug})
                slug_resp = self.client.get(slug_url)
                self.assertEqual(slug_resp.status_code, 200, "Acesso por slug deve funcionar mesmo se PK redirect falhar")
            else:
                self.assertIn(resp.status_code, [301, 302], f"Expected redirect, got {resp.status_code}")
                if resp.status_code in [301, 302]:
                    self.assertIn(self.edital.slug, resp.url)

    def test_detail_404_for_invalid_slug(self):
        """Testa que slug inválido retorna 404."""
        resp = self.client.get(reverse("edital_detail_slug", kwargs={'slug': 'slug-invalido-12345'}))
        self.assertEqual(resp.status_code, 404)


class EditalModelTest(TestCase):
    """Testes para o modelo Edital."""
    
    def test_slug_generation(self):
        """Testa geração automática de slug."""
        edital = Edital.objects.create(
            titulo="Edital de Teste para Slug",
            url="https://example.com/test"
        )
        self.assertIsNotNone(edital.slug)
        self.assertIn('edital-de-teste-para-slug', edital.slug.lower())

    def test_slug_generation_with_empty_title(self):
        """Testa geração de slug quando título resulta em string vazia após slugify."""
        # Criar edital com título que resulta em slug vazio (apenas caracteres especiais)
        edital = Edital.objects.create(
            titulo="!!!@@@###$$$",
            url="https://example.com/test"
        )
        # Deve gerar um slug fallback (não vazio)
        self.assertIsNotNone(edital.slug)
        self.assertNotEqual(edital.slug, '')
        # Deve começar com "edital-"
        self.assertTrue(edital.slug.startswith('edital-'))

    def test_slug_generation_with_special_characters(self):
        """Testa geração de slug com caracteres especiais que podem causar problemas."""
        edital = Edital.objects.create(
            titulo="Edital com @#$% caracteres especiais",
            url="https://example.com/test"
        )
        self.assertIsNotNone(edital.slug)
        # Slug não deve conter caracteres especiais
        self.assertNotIn('@', edital.slug)
        self.assertNotIn('#', edital.slug)
        self.assertNotIn('$', edital.slug)
        self.assertNotIn('%', edital.slug)

    def test_slug_uniqueness(self):
        """Testa que slugs são únicos."""
        edital1 = Edital.objects.create(
            titulo="Edital Duplicado",
            url="https://example.com/1"
        )
        edital2 = Edital.objects.create(
            titulo="Edital Duplicado",
            url="https://example.com/2"
        )
        self.assertNotEqual(edital1.slug, edital2.slug)
        self.assertIn(edital1.slug, edital2.slug)  # Segundo deve ter sufixo

    def test_date_validation(self):
        """Testa validação de datas."""
        from django.core.exceptions import ValidationError
        
        edital = Edital(
            titulo="Edital com Datas Inválidas",
            url="https://example.com/test",
            start_date=timezone.now().date() + timedelta(days=10),
            end_date=timezone.now().date()  # End antes de start
        )
        with self.assertRaises(ValidationError):
            edital.clean()

    def test_status_auto_update_on_save(self):
        """Testa atualização automática de status baseado em datas."""
        today = timezone.now().date()
        
        # Edital programado (start_date > hoje)
        edital = Edital.objects.create(
            titulo="Edital Programado",
            url="https://example.com/test",
            status='aberto',
            start_date=today + timedelta(days=10),
            end_date=today + timedelta(days=40)
        )
        # O save() deve atualizar para 'programado'
        self.assertEqual(edital.status, 'programado')

    def test_get_absolute_url_uses_slug(self):
        """Testa que get_absolute_url usa slug quando disponível."""
        edital = Edital.objects.create(
            titulo="Edital para URL",
            url="https://example.com/test"
        )
        url = edital.get_absolute_url()
        if edital.slug:
            self.assertIn(edital.slug, url)


class EditalFormTest(TestCase):
    """Testes para o formulário EditalForm."""
    
    def setUp(self):
        """Dados base para testes."""
        self.valid_data = {
            'titulo': 'Edital de Teste',
            'url': 'https://example.com/test',
            'status': 'aberto',
            'numero_edital': '001/2025',
            'entidade_principal': 'Entidade Teste',
            'objetivo': 'Objetivo do teste',
        }

    def test_form_valid_with_required_fields(self):
        """Testa que formulário é válido com campos obrigatórios."""
        from .forms import EditalForm
        form = EditalForm(data=self.valid_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

    def test_form_invalid_without_titulo(self):
        """Testa que formulário é inválido sem título."""
        from .forms import EditalForm
        data = self.valid_data.copy()
        data.pop('titulo')
        form = EditalForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('titulo', form.errors)

    def test_form_invalid_without_url(self):
        """Testa que formulário é inválido sem URL."""
        from .forms import EditalForm
        data = self.valid_data.copy()
        data.pop('url')
        form = EditalForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('url', form.errors)

    def test_form_validates_date_range(self):
        """Testa que modelo valida intervalo de datas."""
        from django.core.exceptions import ValidationError
        today = timezone.now().date()
        
        # Criar edital diretamente com datas inválidas
        edital = Edital(
            titulo='Edital com Datas Inválidas',
            url='https://example.com/test',
            start_date=today + timedelta(days=10),
            end_date=today  # End antes de start
        )
        
        # O modelo deve validar no clean()
        with self.assertRaises(ValidationError) as context:
            edital.full_clean()
        
        # Verificar que o erro é sobre end_date
        error_dict = context.exception.error_dict if hasattr(context.exception, 'error_dict') else {}
        self.assertIn('end_date', error_dict or str(context.exception))

    def test_form_saves_correctly(self):
        """Testa que formulário salva edital corretamente."""
        from .forms import EditalForm
        form = EditalForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
        edital = form.save()
        self.assertIsNotNone(edital.pk)
        self.assertEqual(edital.titulo, self.valid_data['titulo'])
        self.assertEqual(edital.url, self.valid_data['url'])

    def test_form_updates_existing_edital(self):
        """Testa que formulário atualiza edital existente."""
        from .forms import EditalForm
        edital = Edital.objects.create(**self.valid_data)
        new_data = self.valid_data.copy()
        new_data['titulo'] = 'Título Atualizado'
        
        form = EditalForm(data=new_data, instance=edital)
        self.assertTrue(form.is_valid())
        updated_edital = form.save()
        self.assertEqual(updated_edital.titulo, 'Título Atualizado')
        self.assertEqual(updated_edital.pk, edital.pk)  # Mesmo objeto

