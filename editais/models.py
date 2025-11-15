import re
from django.contrib.auth.models import User
from django.db import models, IntegrityError
from django.urls import reverse
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.utils import timezone


class Edital(models.Model):
    """
    Modelo que representa um edital de fomento.
    
    Um edital é uma oportunidade de financiamento que possui informações
    sobre título, datas, status, valores, cronograma e conteúdo detalhado.
    
    Attributes:
        numero_edital: Número identificador do edital
        titulo: Título do edital (obrigatório)
        slug: URL-friendly version do título (gerado automaticamente)
        url: URL do edital original
        entidade_principal: Entidade responsável pelo edital
        status: Status atual (draft, aberto, fechado, etc.)
        start_date: Data de abertura
        end_date: Data de encerramento
        data_criacao: Data de criação do registro
        data_atualizacao: Data da última atualização
        created_by: Usuário que criou o edital
        updated_by: Usuário que atualizou o edital pela última vez
        
    Properties:
        days_until_deadline: Dias restantes até o prazo
        is_deadline_imminent: True se prazo está próximo (7 dias)
        
    Methods:
        can_edit(user): Verifica se usuário pode editar
        get_absolute_url(): Retorna URL do edital
        is_open(): Verifica se está aberto
        is_closed(): Verifica se está fechado
    """
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
        """Generate a unique slug from the title - optimized to reduce database queries"""
        base_slug = slugify(self.titulo)
        
        # Handle edge case: if slugify returns empty string (e.g., title is only special chars)
        # Use a fallback slug based on PK or timestamp
        if not base_slug:
            if self.pk:
                base_slug = f"edital-{self.pk}"
            else:
                # For new objects, use timestamp as fallback
                import time
                base_slug = f"edital-{int(time.time())}"
        
        # Fetch slugs that match the exact base_slug or follow the pattern base_slug-N
        # This is more precise than startswith and avoids false matches
        # Strategy: Get exact match and slugs starting with base_slug-, then filter in Python
        # This works across all database backends (SQLite, PostgreSQL, MySQL)
        queryset = Edital.objects.filter(
            models.Q(slug=base_slug) | models.Q(slug__startswith=f"{base_slug}-")
        )
        if self.pk:
            queryset = queryset.exclude(pk=self.pk)
        
        # Filter in Python to ensure we only get slugs matching base_slug or base_slug-N pattern
        # This avoids false matches like "editable" when base_slug is "edit"
        all_slugs = queryset.values_list('slug', flat=True)
        existing_slugs = set()
        pattern = re.compile(rf'^{re.escape(base_slug)}(-\d+)?$')
        for slug in all_slugs:
            if pattern.match(slug):
                existing_slugs.add(slug)
        
        # Find next available slug in memory (no additional queries)
        slug = base_slug
        counter = 1
        max_attempts = 10000  # Safety limit to prevent infinite loops
        attempts = 0
        
        while slug in existing_slugs and attempts < max_attempts:
            slug = f"{base_slug}-{counter}"
            counter += 1
            attempts += 1
        
        # If we hit the limit, append timestamp to ensure uniqueness
        if attempts >= max_attempts:
            import time
            slug = f"{base_slug}-{int(time.time())}"
        
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
        
        # Ensure slug is never None after save (DB-001 fix)
        if not self.slug:
            raise ValidationError('Slug não pode ser None. Título inválido para geração de slug.')
        
        # Auto-update status based on dates
        today = timezone.now().date()
        
        if self.start_date and self.end_date:
            if self.end_date <= today and self.status == 'aberto':
                self.status = 'fechado'
            elif self.start_date <= today and self.end_date >= today and self.status == 'programado':
                # Adicionar lógica para mover de programado para aberto
                self.status = 'aberto'
            elif self.start_date > today and self.status != 'draft':
                self.status = 'programado'
        
        # Handle race condition for slug uniqueness (retry if IntegrityError)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                super().save(*args, **kwargs)
                # Ensure slug is set after save (double-check)
                if not self.slug:
                    self.slug = self._generate_unique_slug()
                    super().save(*args, **kwargs)
                break
            except ValidationError:
                # Re-raise validation errors
                raise
            except IntegrityError as e:
                # Check if it's an IntegrityError related to slug uniqueness
                if 'slug' in str(e).lower() or 'unique' in str(e).lower():
                    if attempt < max_retries - 1:
                        # Regenerate slug and retry
                        self.slug = self._generate_unique_slug()
                        continue
                # Re-raise other exceptions
                raise

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

    @property
    def days_until_deadline(self):
        """
        Retorna o número de dias até a data de encerramento.
        
        Returns:
            int: Número de dias até o prazo, ou None se não houver data de encerramento
        """
        if not self.end_date:
            return None
        delta = self.end_date - timezone.now().date()
        return delta.days
    
    @property
    def is_deadline_imminent(self):
        """
        Verifica se o prazo está próximo (dentro de 7 dias).
        
        Returns:
            bool: True se o prazo está dentro de 7 dias, False caso contrário
        """
        days = self.days_until_deadline
        if days is None:
            return False
        return 0 <= days <= 7
    
    def can_edit(self, user):
        """
        Verifica se o usuário pode editar este edital.
        
        Args:
            user: Instância de User do Django
            
        Returns:
            bool: True se o usuário pode editar, False caso contrário
        """
        if not user or not user.is_authenticated:
            return False
        return user.is_staff or user == self.created_by
    
    def __str__(self):
        return self.titulo
    
    def __repr__(self):
        return f"<Edital: {self.titulo[:50]} (pk={self.pk}, status={self.status})>"

    def get_absolute_url(self):
        """Return URL using slug if available, otherwise use PK"""
        if self.slug:
            return reverse('edital_detail_slug', kwargs={'slug': self.slug})
        if self.pk:
            return reverse('edital_detail', kwargs={'pk': self.pk})
        # If object is not saved yet, return empty string
        return ''


class EditalValor(models.Model):
    """
    Modelo que representa o valor financeiro de um edital.
    
    Um edital pode ter múltiplos valores em diferentes moedas.
    
    Attributes:
        edital: Edital relacionado (ForeignKey)
        valor_total: Valor total do edital
        moeda: Moeda do valor (BRL, USD, EUR)
    """
    MOEDA_CHOICES = [
        ('BRL', 'Real Brasileiro (R$)'),
        ('USD', 'Dólar Americano (US$)'),
        ('EUR', 'Euro (€)'),
    ]
    
    edital = models.ForeignKey(Edital, on_delete=models.CASCADE, related_name='valores')
    valor_total = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    moeda = models.CharField(
        max_length=10,
        choices=MOEDA_CHOICES,
        default='BRL',
        help_text='Moeda do valor total'
    )

    class Meta:
        verbose_name = 'Valor do Edital'
        verbose_name_plural = 'Valores dos Editais'
        # Índice composto para queries que filtram por edital e moeda
        indexes = [
            models.Index(fields=['edital', 'moeda'], name='idx_edital_moeda'),
        ]

    def __str__(self):
        return f'{self.edital.titulo} - {self.valor_total} {self.moeda}'
    
    def __repr__(self):
        return f"<EditalValor: edital_id={self.edital_id}, valor={self.valor_total} {self.moeda}>"


class Cronograma(models.Model):
    """
    Modelo que representa um item do cronograma de um edital.
    
    Um edital pode ter múltiplos itens de cronograma com datas e descrições.
    
    Attributes:
        edital: Edital relacionado (ForeignKey)
        data_inicio: Data de início do item
        data_fim: Data de fim do item
        data_publicacao: Data de publicação
        descricao: Descrição do item do cronograma
    """
    edital = models.ForeignKey(Edital, on_delete=models.CASCADE, related_name='cronogramas')
    data_inicio = models.DateField(blank=True, null=True)
    data_fim = models.DateField(blank=True, null=True)
    data_publicacao = models.DateField(blank=True, null=True)
    descricao = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ['data_inicio']
        verbose_name = 'Cronograma'
        verbose_name_plural = 'Cronogramas'
        # Índices para melhorar queries de cronogramas
        indexes = [
            models.Index(fields=['edital', 'data_inicio'], name='idx_cronograma_edital_data'),
            models.Index(fields=['data_inicio'], name='idx_cronograma_data_inicio'),
        ]

    def __str__(self):
        return f'{self.edital.titulo} - {self.descricao}'
    
    def __repr__(self):
        return f"<Cronograma: edital_id={self.edital_id}, descricao={self.descricao[:30]}>"


class EditalHistory(models.Model):
    """
    Modelo que representa o histórico de alterações em editais.
    
    Mantém um registro de todas as ações (criar, atualizar, deletar)
    realizadas em editais para fins de auditoria.
    
    Attributes:
        edital: Edital relacionado (pode ser None se deletado)
        edital_titulo: Título preservado quando edital é deletado
        user: Usuário que realizou a ação
        action: Tipo de ação (create, update, delete)
        field_name: Nome do campo alterado (legado)
        old_value: Valor antigo (legado)
        new_value: Valor novo (legado)
        timestamp: Data e hora da ação
        changes_summary: Resumo das mudanças em formato JSON
    """
    edital = models.ForeignKey(
        Edital,
        on_delete=models.SET_NULL,  # Preserve history even if edital is deleted
        null=True,
        blank=True,
        related_name='history'
    )
    edital_titulo = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text='Título do edital (preservado quando edital é deletado)'
    )
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='edital_changes'
    )
    action = models.CharField(
        max_length=20,
        choices=[
            ('create', 'Criado'),
            ('update', 'Atualizado'),
            ('delete', 'Excluído'),
        ]
    )
    field_name = models.CharField(max_length=100, blank=True, null=True)
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    changes_summary = models.JSONField(default=dict, blank=True)  # Resumo das mudanças
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Histórico de Edital'
        verbose_name_plural = 'Históricos de Editais'
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['edital', '-timestamp']),
        ]
    
    def __str__(self):
        titulo = self.edital.titulo if self.edital else (self.edital_titulo or 'Edital Deletado')
        return f'{titulo} - {self.get_action_display()} - {self.timestamp.strftime("%d/%m/%Y %H:%M")}'
    
    def __repr__(self):
        edital_id = self.edital_id if self.edital else None
        return f"<EditalHistory: edital_id={edital_id}, action={self.action}, timestamp={self.timestamp}>"

