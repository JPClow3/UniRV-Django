"""
Legacy tests for Edital CRUD, search/filter, detail views, model, and form.
"""

import pytest
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from editais.forms import EditalForm
from editais.models import Edital


@pytest.mark.django_db
class TestEditaisCrud:
    @pytest.fixture(autouse=True)
    def _setup(self):
        self.user = User.objects.create_user(
            username="admin", password="admin", is_staff=True
        )
        self.payload = {
            "titulo": "Edital Teste",
            "url": "https://example.com/edital-teste",
            "status": "aberto",
            "numero_edital": "001/2025",
            "entidade_principal": "Entidade Teste",
            "objetivo": "Objetivo do teste",
        }

    def test_index_page_loads(self, client):
        assert client.get(reverse("editais_index")).status_code == 200

    def test_create_edital(self, client):
        client.login(username="admin", password="admin")
        resp = client.post(reverse("edital_create"), data=self.payload, follow=False)
        assert resp.status_code == 302
        assert Edital.objects.count() == 1
        edital = Edital.objects.first()
        assert edital.titulo == self.payload["titulo"]

    def test_update_edital(self, client):
        client.login(username="admin", password="admin")
        edital = Edital.objects.create(**self.payload)
        new_title = "Edital Teste Atualizado"
        resp = client.post(
            reverse("edital_update", args=[edital.pk]),
            data={**self.payload, "titulo": new_title},
        )
        assert resp.status_code == 302
        edital.refresh_from_db()
        assert edital.titulo == new_title

    def test_delete_edital(self, client):
        client.login(username="admin", password="admin")
        edital = Edital.objects.create(**self.payload)
        resp = client.post(reverse("edital_delete", args=[edital.pk]))
        assert resp.status_code == 302
        assert Edital.objects.count() == 0

    def test_create_requires_authentication(self, client):
        resp = client.get(reverse("edital_create"))
        assert resp.status_code == 302
        assert "/login/" in resp.url

    def test_update_requires_authentication(self, client):
        edital = Edital.objects.create(**self.payload)
        resp = client.get(reverse("edital_update", args=[edital.pk]))
        assert resp.status_code == 302
        assert "/login/" in resp.url

    def test_delete_requires_authentication(self, client):
        edital = Edital.objects.create(**self.payload)
        resp = client.get(reverse("edital_delete", args=[edital.pk]))
        assert resp.status_code == 302
        assert "/login/" in resp.url


@pytest.mark.django_db
class TestEditalSearchAndFilter:
    @pytest.fixture(autouse=True)
    def _setup(self):
        future_time = timezone.now() + timedelta(days=365)
        self.edital1 = Edital.objects.create(
            titulo="Edital de Inovação Tecnológica",
            url="https://example.com/1",
            status="aberto",
            entidade_principal="CNPq",
            numero_edital="001/2025",
            objetivo="Fomentar inovação tecnológica",
        )
        self.edital1.data_atualizacao = future_time
        self.edital1.save(update_fields=["data_atualizacao"])

        self.edital2 = Edital.objects.create(
            titulo="Programa de Pesquisa em Agricultura",
            url="https://example.com/2",
            status="fechado",
            entidade_principal="FAPEG",
            numero_edital="002/2025",
            objetivo="Pesquisa agrícola sustentável",
        )
        self.edital2.data_atualizacao = future_time
        self.edital2.save(update_fields=["data_atualizacao"])

        self.edital3 = Edital.objects.create(
            titulo="Chamada para Startups",
            url="https://example.com/3",
            status="aberto",
            entidade_principal="SEBRAE",
            numero_edital="003/2025",
            objetivo="Aceleração de startups",
        )
        self.edital3.data_atualizacao = future_time
        self.edital3.save(update_fields=["data_atualizacao"])

    def test_search_by_title(self, client):
        resp = client.get(reverse("editais_index"), {"search": "Inovação"})
        assert resp.status_code == 200
        content = resp.content.decode()
        assert self.edital1.titulo in content
        assert self.edital2.titulo not in content

    def test_search_by_entity(self, client):
        resp = client.get(reverse("editais_index"), {"search": "CNPq"})
        assert self.edital1.titulo in resp.content.decode()

    def test_search_case_insensitive(self, client):
        resp = client.get(reverse("editais_index"), {"search": "inovação"})
        assert self.edital1.titulo in resp.content.decode()

    def test_filter_by_status(self, client):
        resp = client.get(reverse("editais_index"), {"status": "aberto"})
        content = resp.content.decode()
        assert self.edital1.titulo in content
        assert self.edital3.titulo in content
        assert self.edital2.titulo not in content

    def test_search_and_filter_combined(self, client):
        resp = client.get(
            reverse("editais_index"), {"search": "Pesquisa", "status": "fechado"}
        )
        content = resp.content.decode()
        assert self.edital2.titulo in content
        assert self.edital1.titulo not in content

    def test_empty_search_returns_all(self, client):
        self.edital1.refresh_from_db()
        self.edital2.refresh_from_db()
        self.edital3.refresh_from_db()

        found = set()
        page = 1
        while page <= 10:
            resp = client.get(
                reverse("editais_index"), {"page": page} if page > 1 else {}
            )
            assert resp.status_code == 200
            content = resp.content.decode()
            if self.edital1.titulo in content:
                found.add(1)
            if self.edital2.titulo in content:
                found.add(2)
            if self.edital3.titulo in content:
                found.add(3)

            if f"page={page + 1}" not in content:
                break
            page += 1

        assert found == {1, 2, 3}

    def test_filter_by_start_date(self, client):
        today = timezone.now().date()
        edital_future = Edital.objects.create(
            titulo="Edital Futuro",
            url="https://example.com/future",
            status="aberto",
            start_date=today + timedelta(days=30),
        )
        resp = client.get(
            reverse("editais_index"),
            {"start_date": today.strftime("%Y-%m-%d")},
        )
        assert edital_future.titulo in resp.content.decode()

    def test_filter_only_open(self, client):
        resp = client.get(reverse("editais_index"), {"only_open": "1"})
        content = resp.content.decode()
        assert self.edital1.titulo in content
        assert self.edital3.titulo in content
        assert self.edital2.titulo not in content


@pytest.mark.django_db
class TestEditalDetail:
    @pytest.fixture(autouse=True)
    def _setup(self):
        self.edital = Edital.objects.create(
            titulo="Edital de Teste",
            url="https://example.com/test",
            status="aberto",
            numero_edital="TEST/2025",
            entidade_principal="Entidade Teste",
            objetivo="Objetivo do teste",
            analise="Análise do edital",
        )

    def test_detail_page_loads(self, client):
        resp = client.get(self.edital.get_absolute_url())
        assert resp.status_code == 200
        assert self.edital.titulo in resp.content.decode()
        assert self.edital.objetivo in resp.content.decode()

    def test_detail_by_slug(self, client):
        if self.edital.slug:
            resp = client.get(
                reverse("edital_detail_slug", kwargs={"slug": self.edital.slug})
            )
            assert resp.status_code == 200

    def test_detail_by_pk_redirects_to_slug(self, client):
        self.edital.save()
        self.edital.refresh_from_db()
        assert self.edital.slug
        try:
            url = reverse("edital_detail", kwargs={"pk": self.edital.pk})
            resp = client.get(url, follow=False)
            assert resp.status_code == 301
            assert self.edital.slug in resp.url
        except Exception:
            slug_url = reverse("edital_detail_slug", kwargs={"slug": self.edital.slug})
            assert client.get(slug_url).status_code == 200

    def test_detail_404_for_invalid_slug(self, client):
        resp = client.get(
            reverse("edital_detail_slug", kwargs={"slug": "slug-invalido-12345"})
        )
        assert resp.status_code == 404


@pytest.mark.django_db
class TestEditalModel:
    def test_slug_generation(self):
        edital = Edital.objects.create(
            titulo="Edital de Teste para Slug", url="https://example.com/test"
        )
        assert edital.slug
        assert "edital-de-teste-para-slug" in edital.slug.lower()

    def test_slug_generation_with_empty_title(self):
        edital = Edital.objects.create(
            titulo="!!!@@@###$$$", url="https://example.com/test"
        )
        assert edital.slug
        assert edital.slug.startswith("edital-")

    def test_slug_uniqueness(self):
        e1 = Edital.objects.create(
            titulo="Edital Duplicado", url="https://example.com/1"
        )
        e2 = Edital.objects.create(
            titulo="Edital Duplicado", url="https://example.com/2"
        )
        assert e1.slug != e2.slug

    def test_date_validation(self):
        edital = Edital(
            titulo="Datas Inválidas",
            url="https://example.com/test",
            start_date=timezone.now().date() + timedelta(days=10),
            end_date=timezone.now().date(),
        )
        with pytest.raises(ValidationError):
            edital.clean()

    def test_status_auto_update_on_save(self):
        today = timezone.now().date()
        edital = Edital.objects.create(
            titulo="Edital Programado",
            url="https://example.com/test",
            status="aberto",
            start_date=today + timedelta(days=10),
            end_date=today + timedelta(days=40),
        )
        assert edital.status == "programado"


@pytest.mark.django_db
class TestEditalForm:
    @pytest.fixture(autouse=True)
    def _setup(self):
        self.valid_data = {
            "titulo": "Edital de Teste",
            "url": "https://example.com/test",
            "status": "aberto",
            "numero_edital": "001/2025",
            "entidade_principal": "Entidade Teste",
            "objetivo": "Objetivo do teste",
        }

    def test_form_valid_with_required_fields(self):
        form = EditalForm(data=self.valid_data)
        assert form.is_valid(), f"Form errors: {form.errors}"

    def test_form_invalid_without_titulo(self):
        data = {k: v for k, v in self.valid_data.items() if k != "titulo"}
        form = EditalForm(data=data)
        assert not form.is_valid()
        assert "titulo" in form.errors

    def test_form_invalid_without_url(self):
        data = {k: v for k, v in self.valid_data.items() if k != "url"}
        form = EditalForm(data=data)
        assert not form.is_valid()
        assert "url" in form.errors

    def test_form_validates_date_range(self):
        today = timezone.now().date()
        edital = Edital(
            titulo="Datas Inválidas",
            url="https://example.com/test",
            start_date=today + timedelta(days=10),
            end_date=today,
        )
        with pytest.raises(ValidationError):
            edital.full_clean()

    def test_form_saves_correctly(self):
        form = EditalForm(data=self.valid_data)
        assert form.is_valid()
        edital = form.save()
        assert edital.pk
        assert edital.titulo == self.valid_data["titulo"]

    def test_form_updates_existing_edital(self):
        edital = Edital.objects.create(**self.valid_data)
        new_data = {**self.valid_data, "titulo": "Título Atualizado"}
        form = EditalForm(data=new_data, instance=edital)
        assert form.is_valid()
        updated = form.save()
        assert updated.titulo == "Título Atualizado"
        assert updated.pk == edital.pk
