from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta
from editais.models import Project, Edital


class Command(BaseCommand):
    help = "Seed the database with fictitious startups for local development."

    def _get_or_create_user(self, username, email, first_name, last_name):
        """Get or create a user for the startup proponente."""
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'is_active': True,
            }
        )
        if created:
            # Set a default password (users can change it later)
            user.set_password('startup123')
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'Created user: {username}')
            )
        return user

    def handle(self, *args, **options):
        # Get or create users for startups
        users = [
            self._get_or_create_user(
                'joao_silva',
                'joao.silva@example.com',
                'João',
                'Silva'
            ),
            self._get_or_create_user(
                'maria_santos',
                'maria.santos@example.com',
                'Maria',
                'Santos'
            ),
            self._get_or_create_user(
                'carlos_oliveira',
                'carlos.oliveira@example.com',
                'Carlos',
                'Oliveira'
            ),
            self._get_or_create_user(
                'ana_costa',
                'ana.costa@example.com',
                'Ana',
                'Costa'
            ),
            self._get_or_create_user(
                'pedro_ferreira',
                'pedro.ferreira@example.com',
                'Pedro',
                'Ferreira'
            ),
        ]

        # Get existing editais to optionally link
        editais = list(Edital.objects.all()[:3])
        if not editais:
            editais = [None] * 5

        # Define 5 fictitious startups
        startups_data = [
            {
                'name': 'AgroSense',
                'description': 'Plataforma de monitoramento inteligente para cultivos utilizando sensores IoT e inteligência artificial. A solução permite aos produtores rurais acompanhar em tempo real a umidade do solo, temperatura, umidade do ar e condições climáticas, gerando alertas automáticos e recomendações personalizadas para otimização da irrigação e aplicação de insumos.',
                'category': 'agtech',
                'status': 'incubacao',
                'proponente': users[0],
                'edital': editais[0] if editais else None,
                'submitted_on': timezone.now() - timedelta(days=120),
            },
            {
                'name': 'BioFarm Solutions',
                'description': 'Desenvolvimento de bioinsumos e fertilizantes orgânicos de alta eficiência para agricultura sustentável. A startup utiliza processos biotecnológicos para criar produtos que aumentam a produtividade agrícola enquanto reduzem o impacto ambiental, promovendo a agricultura regenerativa e o uso responsável de recursos naturais.',
                'category': 'biotech',
                'status': 'pre_incubacao',
                'proponente': users[1],
                'edital': editais[1] if len(editais) > 1 else None,
                'submitted_on': timezone.now() - timedelta(days=30),
            },
            {
                'name': 'FieldConnect',
                'description': 'Sistema de conectividade e automação para propriedades rurais baseado em IoT. A solução integra sensores, atuadores e gateways de comunicação para criar uma fazenda inteligente, permitindo controle remoto de irrigação, monitoramento de rebanhos, gestão de estoques e automação de processos agrícolas através de aplicativo mobile.',
                'category': 'iot',
                'status': 'incubacao',
                'proponente': users[2],
                'edital': editais[2] if len(editais) > 2 else None,
                'submitted_on': timezone.now() - timedelta(days=90),
            },
            {
                'name': 'AgroEdu',
                'description': 'Plataforma educacional digital focada em capacitação técnica para produtores rurais e profissionais do agronegócio. Oferece cursos online, webinars, tutoriais práticos e certificações em temas como gestão rural, tecnologias agrícolas, sustentabilidade e inovação no campo, utilizando metodologias adaptadas ao perfil do público rural.',
                'category': 'edtech',
                'status': 'pre_incubacao',
                'proponente': users[3],
                'edital': None,
                'submitted_on': timezone.now() - timedelta(days=45),
            },
            {
                'name': 'CropGuard',
                'description': 'Solução de monitoramento e controle de pragas e doenças em cultivos utilizando visão computacional e machine learning. O sistema identifica automaticamente problemas fitossanitários através de imagens capturadas por drones ou smartphones, fornecendo diagnósticos precisos e recomendações de tratamento, reduzindo perdas e o uso indiscriminado de defensivos agrícolas.',
                'category': 'agtech',
                'status': 'graduada',
                'proponente': users[4],
                'edital': editais[0] if editais else None,
                'submitted_on': timezone.now() - timedelta(days=365),
            },
        ]

        created_count = 0
        for data in startups_data:
            startup, created = Project.objects.get_or_create(
                name=data['name'],
                defaults=data,
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created startup: {startup.name} ({startup.get_category_display()}) - Status: {startup.get_status_display()}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Startup already exists: {startup.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Seed complete. Created {created_count} new startup(s).')
        )

