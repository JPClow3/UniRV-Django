from django.core.management.base import BaseCommand
from django.utils import timezone
from editais.models import Edital, EditalValor, Cronograma


class Command(BaseCommand):
    help = "Seed the database with sample 'editais' data for local development."

    def handle(self, *args, **options):
        samples = [
            {
                "numero_edital": "01/2025",
                "titulo": "Programa de Fomento à Inovação no Agro",
                "url": "https://example.com/edital-inovacao-agro",
                "entidade_principal": "Agência de Fomento X",
                "status": "aberto",
                "objetivo": "Apoiar projetos de inovação tecnológica no agronegócio.",
                "analise": "## Pontos-chave\n- Público: produtores e startups\n- Abrangência nacional",
            },
            {
                "numero_edital": "02/2025",
                "titulo": "Chamamento Público para Pesquisas em Sustentabilidade",
                "url": "https://example.com/chamamento-sustentabilidade",
                "entidade_principal": "Fundação Y",
                "status": "em_andamento",
                "objetivo": "Fomentar pesquisas em práticas sustentáveis.",
                "analise": "Critérios de avaliação priorizam impacto ambiental e viabilidade.",
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
                # Attach a sample valor
                EditalValor.objects.create(
                    edital=edital,
                    valor_total=1000000,
                    moeda="BRL",
                )
                # Attach a sample cronograma
                Cronograma.objects.create(
                    edital=edital,
                    data_inicio=timezone.now().date(),
                    data_fim=timezone.now().date(),
                    descricao="Período de submissão",
                )

        self.stdout.write(self.style.SUCCESS(f"Seed complete. Created {created_count} new edital(is)."))

