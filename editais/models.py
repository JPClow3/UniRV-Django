from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.utils import timezone


class Edital(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Rascunho'),
        ('aberto', 'Aberto'),
        ('em_andamento', 'Em Andamento'),
        ('fechado', 'Fechado'),
        ('programado', 'Programado'),
    ]

    numero_edital = models.CharField(max_length=100, blank=True, null=True)
    titulo = models.CharField(max_length=500)
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, editable=False)
    url = models.URLField(max_length=1000)
    entidade_principal = models.CharField(max_length=200, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    start_date = models.DateField(blank=True, null=True, verbose_name='Data de Abertura')
    end_date = models.DateField(blank=True, null=True, verbose_name='Data de Encerramento')
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    # User tracking for activity log
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_editais',
        verbose_name='Criado por'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_editais',
        verbose_name='Atualizado por'
    )

    # Conteúdo
    analise = models.TextField(blank=True)  # Nova seção: Análise do Edital
    objetivo = models.TextField(blank=True)
    etapas = models.TextField(blank=True)
    recursos = models.TextField(blank=True)
    itens_financiaveis = models.TextField(blank=True)
    criterios_elegibilidade = models.TextField(blank=True)
    criterios_avaliacao = models.TextField(blank=True)
    itens_essenciais_observacoes = models.TextField(blank=True)
    detalhes_unirv = models.TextField(blank=True)

    class Meta:
        ordering = ['-data_atualizacao']
        verbose_name = 'Edital'
        verbose_name_plural = 'Editais'
        indexes = [
            models.Index(fields=['-data_atualizacao'], name='idx_data_atualizacao'),
            models.Index(fields=['status'], name='idx_status'),
            models.Index(fields=['entidade_principal'], name='idx_entidade'),
            models.Index(fields=['numero_edital'], name='idx_numero'),
            models.Index(fields=['slug'], name='idx_slug'),
            models.Index(fields=['status', 'start_date', 'end_date'], name='idx_status_dates'),
            models.Index(fields=['titulo'], name='idx_titulo'),
        ]

    def _generate_unique_slug(self):
        """Generate a unique slug from the title"""
        base_slug = slugify(self.titulo)
        slug = base_slug
        queryset = Edital.objects.all()
        
        # Exclude current object if editing
        if self.pk:
            queryset = queryset.exclude(pk=self.pk)
        
        # Check for uniqueness and append number if needed
        counter = 1
        while queryset.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug

    def clean(self):
        """Validate model fields"""
        super().clean()
        
        # Validate dates
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValidationError({
                    'end_date': 'A data de encerramento deve ser posterior à data de abertura.'
                })

    def save(self, *args, **kwargs):
        # Generate slug only if it doesn't exist (on creation)
        if not self.slug:
            self.slug = self._generate_unique_slug()
        
        # Auto-update status based on dates
        today = timezone.now().date()
        
        if self.start_date and self.end_date:
            if self.end_date < today and self.status == 'aberto':
                self.status = 'fechado'
            elif self.start_date > today and self.status != 'draft':
                self.status = 'programado'
        
        super().save(*args, **kwargs)

    def get_summary(self):
        """Return a short summary for list views"""
        if self.objetivo:
            return self.objetivo[:200] + '...' if len(self.objetivo) > 200 else self.objetivo
        return ''

    def is_open(self):
        """Check if edital is currently open"""
        return self.status == 'aberto'

    def is_closed(self):
        """Check if edital is closed"""
        return self.status == 'fechado'

    def __str__(self):
        return self.titulo

    def get_absolute_url(self):
        """Return URL using slug if available, otherwise use PK"""
        if self.slug:
            return reverse('edital_detail_slug', kwargs={'slug': self.slug})
        return reverse('edital_detail', kwargs={'pk': self.pk})


class EditalValor(models.Model):
    edital = models.ForeignKey(Edital, on_delete=models.CASCADE, related_name='valores')
    valor_total = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    moeda = models.CharField(max_length=10, default='BRL')

    def __str__(self):
        return f'{self.edital.titulo} - {self.valor_total} {self.moeda}'


class Cronograma(models.Model):
    edital = models.ForeignKey(Edital, on_delete=models.CASCADE, related_name='cronogramas')
    data_inicio = models.DateField(blank=True, null=True)
    data_fim = models.DateField(blank=True, null=True)
    data_publicacao = models.DateField(blank=True, null=True)
    descricao = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ['data_inicio']
        verbose_name = 'Cronograma'
        verbose_name_plural = 'Cronogramas'

    def __str__(self):
        return f'{self.edital.titulo} - {self.descricao}'

