"""
Factory classes for test data generation using factory_boy.

These factories provide a convenient way to create test data with realistic
values, reducing boilerplate in test code.
"""

import factory
from factory import fuzzy
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from ..models import Edital, Project


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating User instances"""

    class Meta:
        model = User
        django_get_or_create = ('username',)

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = factory.Faker('first_name', locale='pt_BR')
    last_name = factory.Faker('last_name', locale='pt_BR')
    is_staff = False
    is_superuser = False

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        if not create:
            return
        password = extracted if extracted else 'testpass123'
        self.set_password(password)
        self.save()


class StaffUserFactory(UserFactory):
    """Factory for creating staff User instances"""

    is_staff = True


class SuperUserFactory(UserFactory):
    """Factory for creating superuser User instances"""

    is_staff = True
    is_superuser = True


class EditalFactory(factory.django.DjangoModelFactory):
    """Factory for creating Edital instances"""

    class Meta:
        model = Edital

    titulo = factory.Sequence(lambda n: f'Edital de Teste {n}')
    url = factory.LazyAttribute(lambda obj: f'https://example.com/edital-{obj.titulo.lower().replace(" ", "-")}')
    status = fuzzy.FuzzyChoice(['draft', 'aberto', 'em_andamento', 'fechado', 'programado'])
    entidade_principal = fuzzy.FuzzyChoice(['FINEP', 'FAPEG', 'CNPq', 'BNDES', None])
    numero_edital = factory.Sequence(lambda n: f'EDT-{n:04d}')
    objetivo = factory.Faker('text', max_nb_chars=200, locale='pt_BR')
    analise = factory.Faker('text', max_nb_chars=500, locale='pt_BR')
    etapas = factory.Faker('text', max_nb_chars=300, locale='pt_BR')
    recursos = factory.Faker('text', max_nb_chars=200, locale='pt_BR')
    itens_financiaveis = factory.Faker('text', max_nb_chars=200, locale='pt_BR')
    criterios_elegibilidade = factory.Faker('text', max_nb_chars=200, locale='pt_BR')
    criterios_avaliacao = factory.Faker('text', max_nb_chars=200, locale='pt_BR')
    itens_essenciais_observacoes = factory.Faker('text', max_nb_chars=200, locale='pt_BR')
    detalhes_unirv = factory.Faker('text', max_nb_chars=200, locale='pt_BR')
    start_date = factory.LazyFunction(lambda: timezone.now().date())
    end_date = factory.LazyFunction(lambda: timezone.now().date() + timedelta(days=30))
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.LazyAttribute(lambda obj: obj.created_by)

    class Params:
        """Traits for common variations"""
        open_edital = factory.Trait(
            status='aberto',
            start_date=factory.LazyFunction(lambda: timezone.now().date() - timedelta(days=5)),
            end_date=factory.LazyFunction(lambda: timezone.now().date() + timedelta(days=25))
        )
        closed_edital = factory.Trait(
            status='fechado',
            start_date=factory.LazyFunction(lambda: timezone.now().date() - timedelta(days=60)),
            end_date=factory.LazyFunction(lambda: timezone.now().date() - timedelta(days=30))
        )
        draft_edital = factory.Trait(
            status='draft'
        )


class ProjectFactory(factory.django.DjangoModelFactory):
    """Factory for creating Project (Startup) instances"""

    class Meta:
        model = Project

    name = factory.Sequence(lambda n: f'Startup {n}')
    description = factory.Faker('text', max_nb_chars=300, locale='pt_BR')
    category = fuzzy.FuzzyChoice(['agtech', 'biotech', 'iot', 'edtech', 'other'])
    status = fuzzy.FuzzyChoice(['pre_incubacao', 'incubacao', 'graduada', 'suspensa'])
    contato = factory.LazyAttribute(lambda obj: f'contato@{obj.name.lower().replace(" ", "")}.com')
    proponente = factory.SubFactory(UserFactory)
    edital = factory.SubFactory(EditalFactory)
    submitted_on = factory.LazyFunction(timezone.now)

    class Params:
        """Traits for common variations"""
        active_startup = factory.Trait(
            status='incubacao'
        )
        graduated_startup = factory.Trait(
            status='graduada'
        )
        without_edital = factory.Trait(
            edital=None
        )
