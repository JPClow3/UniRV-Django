from django.test import TestCase
from django.urls import reverse
from .models import Edital


class EditaisCrudTest(TestCase):
    def setUp(self):
        self.payload = {
            "titulo": "Edital Teste",
            "url": "https://example.com/edital-teste",
            "status": "aberto",
        }

    def test_index_page_loads(self):
        resp = self.client.get(reverse("editais_index"))
        self.assertEqual(resp.status_code, 200)

    def test_create_edital(self):
        resp = self.client.post(reverse("edital_create"), data=self.payload)
        # should redirect to detail on success
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Edital.objects.count(), 1)
        edital = Edital.objects.first()
        self.assertEqual(edital.titulo, self.payload["titulo"])

    def test_update_edital(self):
        # create first
        resp = self.client.post(reverse("edital_create"), data=self.payload)
        self.assertEqual(resp.status_code, 302)
        edital = Edital.objects.first()
        # update
        new_title = "Edital Teste Atualizado"
        update_payload = {**self.payload, "titulo": new_title}
        resp = self.client.post(reverse("edital_update", args=[edital.pk]), data=update_payload)
        self.assertEqual(resp.status_code, 302)
        edital.refresh_from_db()
        self.assertEqual(edital.titulo, new_title)

    def test_delete_edital(self):
        # create first
        self.client.post(reverse("edital_create"), data=self.payload)
        edital = Edital.objects.first()
        # delete
        resp = self.client.post(reverse("edital_delete", args=[edital.pk]))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Edital.objects.count(), 0)
from django.core.management.base import BaseCommand
from django.utils import timezone
from editais.models import Edital, EditalValor, Cronograma


class Command(BaseCommand):
    help = "Seed the database with sample 'editais' data for local development."

    def handle(self, *args, **options):
        # Minimal example editais
        samples = [
            {
                "numero_edital": "01/2025",
                "titulo": "Programa de Fomento à Inovação no Agro",
                "url": "https://example.com/edital-inovacao-agro",
                "entidade_principal": "Agência de Fomento X",
                "status": "aberto",
                "objetivo": "Apoiar projetos de inovação tecnológica no agronegócio.",
            },
            {
                "numero_edital": "02/2025",
                "titulo": "Chamamento Público para Pesquisas em Sustentabilidade",
                "url": "https://example.com/chamamento-sustentabilidade",
                "entidade_principal": "Fundação Y",
                "status": "em_andamento",
                "objetivo": "Fomentar pesquisas em práticas sustentáveis.",
            },
        ]

        created_count = 0
        for data in samples:
            edital, created = Edital.objects.get_or_create(
                titulo=data["titulo"],
                defaults=data,
            )
            if created:
                created_count += 1
                # attach a valor
                EditalValor.objects.create(edital=edital, valor_total=1000000, moeda="BRL")
                # attach a cronograma
                Cronograma.objects.create(
                    edital=edital,
                    data_inicio=timezone.now().date(),
                    data_fim=timezone.now().date(),
                    descricao="Período de submissão",
                )

        self.stdout.write(self.style.SUCCESS(f"Seed complete. Created {created_count} new editais."))

