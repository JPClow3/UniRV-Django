from typing import Optional, Any
import logging
from django.contrib.auth.models import User
from django.conf import settings
from django.db import models, IntegrityError, transaction
from django.db.models import Q
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from simple_history.models import HistoricalRecords

from .utils import determine_edital_status, generate_unique_slug, sanitize_edital_fields
from .constants import SLUG_GENERATION_MAX_RETRIES, SLUG_GENERATION_MAX_ATTEMPTS_EDITAL, SLUG_GENERATION_MAX_ATTEMPTS_PROJECT, MAX_SEARCH_LENGTH

logger = logging.getLogger(__name__)


class EditalQuerySet(models.QuerySet):
    """Custom QuerySet for Edital model with common query patterns."""
    
    def with_related(self):
        """Add select_related for created_by and updated_by to optimize queries."""
        return self.select_related('created_by', 'updated_by')
    
    def with_prefetch(self):
        """Add prefetch_related for valores and cronogramas to optimize queries."""
        return self.prefetch_related('valores', 'cronogramas')
    
    def with_full_prefetch(self):
        """Add all common prefetch_related for detail views."""
        # Note: simple_history creates a 'history' related manager automatically
        # but it doesn't support prefetch_related, so we exclude it
        return self.prefetch_related('valores', 'cronogramas')
    
    def active(self):
        """Filter editais that are not drafts."""
        return self.exclude(status='draft')
    
    def search(self, query: str):
        """
        Search editais by query string.
        
        Uses PostgreSQL full-text search when available (with GIN indexes for performance),
        falls back to icontains for SQLite/other databases.
        
        Args:
            query: Search query string (will be truncated if too long)
            
        Returns:
            QuerySet: Filtered and ranked queryset
        """
        if not query:
            return self
        
        # Convert query to string if it's not already (defensive programming)
        # This handles edge cases where query might be passed as int, None, etc.
        if not isinstance(query, str):
            query = str(query) if query is not None else ''
            if not query:
                return self
        
        if len(query) > MAX_SEARCH_LENGTH:
            query = query[:MAX_SEARCH_LENGTH]
        
        # Check if we're using PostgreSQL
        db_engine = settings.DATABASES['default'].get('ENGINE', '')
        is_postgres = 'postgresql' in db_engine or 'postgis' in db_engine
        
        if is_postgres:
            # Use PostgreSQL full-text search with Portuguese language configuration
            # This enables stemming (e.g., "startup" matches "startups") and ranking
            try:
                # Create search vector from all searchable fields
                search_fields = getattr(settings, 'EDITAL_SEARCH_FIELDS', [
                    'titulo', 'entidade_principal', 'numero_edital',
                    'analise', 'objetivo', 'etapas', 'recursos',
                    'itens_financiaveis', 'criterios_elegibilidade',
                    'criterios_avaliacao', 'itens_essenciais_observacoes',
                    'detalhes_unirv'
                ])
                
                # Build search vector with Portuguese language configuration
                # 'portuguese' config provides stemming and stop word removal
                search_vector = SearchVector(*search_fields, config='portuguese')
                
                # Create search query with Portuguese config
                search_query_obj = SearchQuery(query, config='portuguese')
                
                # Annotate queryset with search rank for relevance ordering
                return self.annotate(
                    search=search_vector,
                    rank=SearchRank(search_vector, search_query_obj)
                ).filter(search=search_query_obj).order_by('-rank', '-data_atualizacao')
            except Exception as e:
                # Fallback to icontains if full-text search fails
                logger.warning(f"PostgreSQL full-text search failed, falling back to icontains: {e}")
                is_postgres = False
        
        # Fallback: Use icontains for SQLite or if PostgreSQL search fails
        q_objects = Q()
        search_fields = getattr(settings, 'EDITAL_SEARCH_FIELDS', [
            'titulo', 'entidade_principal', 'numero_edital'
        ])
        
        # Validate fields exist on the model to prevent FieldError
        # Only use concrete fields (not reverse relations, many-to-many, etc.) that support text search
        # get_fields() includes reverse relations, so we filter to only concrete CharField/TextField fields
        try:
            model_fields = {
                f.name for f in self.model._meta.get_fields()
                if hasattr(f, 'get_internal_type') and f.get_internal_type() in ('CharField', 'TextField')
            }
        except Exception as e:
            # Fallback: use all field names if validation fails
            model_fields = {f.name for f in self.model._meta.get_fields() if hasattr(f, 'name')}
        
        valid_search_fields = [f for f in search_fields if f in model_fields]
        
        if not valid_search_fields:
            # If no valid fields, return empty queryset
            logger.warning(f"No valid search fields found in EDITAL_SEARCH_FIELDS. Fields checked: {search_fields}")
            return self.none()
        
        for field in valid_search_fields:
            q_objects |= Q(**{f'{field}__icontains': query})
        
        return self.filter(q_objects)


class EditalManager(models.Manager):
    """Custom manager for Edital model."""
    
    def get_queryset(self):
        """Return custom QuerySet."""
        return EditalQuerySet(self.model, using=self._db)
    
    def with_related(self):
        """Add select_related for created_by and updated_by."""
        return self.get_queryset().with_related()
    
    def with_prefetch(self):
        """Add prefetch_related for valores and cronogramas."""
        return self.get_queryset().with_prefetch()
    
    def with_full_prefetch(self):
        """Add all common prefetch_related for detail views."""
        return self.get_queryset().with_full_prefetch()
    
    def active(self):
        """Filter editais that are not drafts."""
        return self.get_queryset().active()
    
    def search(self, query: str):
        """
        Search editais by query string.
        
        Uses PostgreSQL full-text search when available (with GIN indexes for performance),
        falls back to icontains for SQLite/other databases.
        
        Args:
            query: Search query string (will be truncated if too long)
            
        Returns:
            QuerySet: Filtered and ranked queryset
        """
        if not query:
            return self.get_queryset()
        
        # Convert query to string if it's not already (defensive programming)
        # This handles edge cases where query might be passed as int, None, etc.
        if not isinstance(query, str):
            query = str(query) if query is not None else ''
            if not query:
                return self.get_queryset()
        
        if len(query) > MAX_SEARCH_LENGTH:
            query = query[:MAX_SEARCH_LENGTH]
        
        # Check if we're using PostgreSQL
        db_engine = settings.DATABASES['default'].get('ENGINE', '')
        is_postgres = 'postgresql' in db_engine or 'postgis' in db_engine
        
        if is_postgres:
            # Use PostgreSQL full-text search with Portuguese language configuration
            # This enables stemming (e.g., "startup" matches "startups") and ranking
            try:
                # Create search vector from all searchable fields
                search_fields = getattr(settings, 'EDITAL_SEARCH_FIELDS', [
                    'titulo', 'entidade_principal', 'numero_edital',
                    'analise', 'objetivo', 'etapas', 'recursos',
                    'itens_financiaveis', 'criterios_elegibilidade',
                    'criterios_avaliacao', 'itens_essenciais_observacoes',
                    'detalhes_unirv'
                ])
                
                # Build search vector with Portuguese language configuration
                # 'portuguese' config provides stemming and stop word removal
                search_vector = SearchVector(*search_fields, config='portuguese')
                
                # Create search query with Portuguese config
                search_query_obj = SearchQuery(query, config='portuguese')
                
                # Annotate queryset with search rank for relevance ordering
                return self.get_queryset().annotate(
                    search=search_vector,
                    rank=SearchRank(search_vector, search_query_obj)
                ).filter(search=search_query_obj).order_by('-rank', '-data_atualizacao')
            except Exception as e:
                # Fallback to icontains if full-text search fails
                logger.warning(f"PostgreSQL full-text search failed, falling back to icontains: {e}")
                is_postgres = False
        
        # Fallback: Use icontains for SQLite or if PostgreSQL search fails
        q_objects = Q()
        search_fields = getattr(settings, 'EDITAL_SEARCH_FIELDS', [
            'titulo', 'entidade_principal', 'numero_edital'
        ])
        
        # Validate fields exist on the model to prevent FieldError
        # Only use concrete fields (not reverse relations, many-to-many, etc.) that support text search
        # get_fields() includes reverse relations, so we filter to only concrete CharField/TextField fields
        try:
            model_fields = {
                f.name for f in self.model._meta.get_fields()
                if hasattr(f, 'get_internal_type') and f.get_internal_type() in ('CharField', 'TextField')
            }
        except Exception as e:
            # Fallback: use all field names if validation fails
            model_fields = {f.name for f in self.model._meta.get_fields() if hasattr(f, 'name')}
        
        valid_search_fields = [f for f in search_fields if f in model_fields]
        
        if not valid_search_fields:
            # If no valid fields, return empty queryset
            logger.warning(f"No valid search fields found in EDITAL_SEARCH_FIELDS. Fields checked: {search_fields}")
            return self.get_queryset().none()
        
        for field in valid_search_fields:
            q_objects |= Q(**{f'{field}__icontains': query})
        
        return self.get_queryset().filter(q_objects)


class Edital(models.Model):
    """
    Modelo que representa um edital de fomento.
    
    Um edital é uma oportunidade de financiamento com informações sobre
    título, datas, status, valores, cronograma e conteúdo detalhado.
    
    Properties:
        days_until_deadline: Dias restantes até o prazo
        is_deadline_imminent: True se prazo está próximo (7 dias)
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
    analise = models.TextField(blank=True, null=True)  # Nova seção: Análise do Edital
    objetivo = models.TextField(blank=True, null=True)
    etapas = models.TextField(blank=True, null=True)
    recursos = models.TextField(blank=True, null=True)
    itens_financiaveis = models.TextField(blank=True, null=True)
    criterios_elegibilidade = models.TextField(blank=True, null=True)
    criterios_avaliacao = models.TextField(blank=True, null=True)
    itens_essenciais_observacoes = models.TextField(blank=True, null=True)
    detalhes_unirv = models.TextField(blank=True, null=True)

    objects = EditalManager()

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

    def _generate_unique_slug(self) -> str:
        """
        Generate a unique slug from the title - optimized to reduce database queries.
        
        RACE CONDITION HANDLING:
        Slug uniqueness is enforced at the database level with a unique constraint.
        The save() method includes retry logic that regenerates the slug if an
        IntegrityError occurs due to concurrent creation with the same title.
        This handles race conditions where multiple requests create editais with
        the same title simultaneously.
        """
        return generate_unique_slug(
            text=self.titulo,
            model_class=Edital,
            slug_field_name='slug',
            prefix='edital',
            pk=self.pk,
            max_attempts=SLUG_GENERATION_MAX_ATTEMPTS_EDITAL
        )

    def clean(self) -> None:
        """Validate model fields"""
        super().clean()
        
        # Validate dates
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValidationError({
                    'end_date': 'A data de encerramento deve ser posterior à data de abertura.'
                })

    def save(self, *args: Any, **kwargs: Any) -> None:
        # Generate slug only if it doesn't exist (on creation)
        if not self.slug:
            self.slug = self._generate_unique_slug()
        
        # Ensure slug is never None after save (DB-001 fix)
        if not self.slug:
            raise ValidationError('Slug não pode ser None. Título inválido para geração de slug.')
        
        today = timezone.now().date()
        self.status = determine_edital_status(
            current_status=self.status,
            start_date=self.start_date,
            end_date=self.end_date,
            today=today,
        )
        
        # Sanitize HTML fields to prevent XSS attacks
        # This ensures data is sanitized regardless of entry point (admin, views, shell, API, etc.)
        sanitize_edital_fields(self)
        
        # RACE CONDITION HANDLING: Slug uniqueness retry logic
        # When multiple requests create editais with the same title simultaneously,
        # the database unique constraint on slug may cause IntegrityError.
        # This retry mechanism regenerates the slug and attempts to save again.
        # The transaction.atomic() wrapper ensures each attempt is atomic.
        # This is an acceptable race condition pattern - retry with new slug value.
        max_retries = SLUG_GENERATION_MAX_RETRIES
        for attempt in range(max_retries):
            try:
                with transaction.atomic():
                    super().save(*args, **kwargs)
                break
            except ValidationError:
                # Re-raise validation errors (not race conditions)
                raise
            except IntegrityError as e:
                # Check if it's an IntegrityError related to slug uniqueness
                if 'slug' in str(e).lower() or 'unique' in str(e).lower():
                    if attempt < max_retries - 1:
                        # Regenerate slug and retry (handles race condition)
                        self.slug = self._generate_unique_slug()
                        continue
                # Re-raise other IntegrityErrors (not slug-related)
                raise

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
    def is_deadline_imminent(self) -> bool:
        """
        Verifica se o prazo está próximo (dentro de 7 dias).
        
        Returns:
            bool: True se o prazo está dentro de 7 dias, False caso contrário
        """
        days = self.days_until_deadline
        if days is None:
            return False
        return 0 <= days <= 7

    def __str__(self):
        return self.titulo
    
    def __repr__(self):
        return f"<Edital: {self.titulo[:50]} (pk={self.pk}, status={self.status})>"

    def get_absolute_url(self) -> str:
        """Return URL using slug if available, otherwise use PK"""
        if self.slug:
            return reverse('edital_detail_slug', kwargs={'slug': self.slug})
        if self.pk:
            return reverse('edital_detail', kwargs={'pk': self.pk})
        # If object is not saved yet, return empty string
        return ''

    history = HistoricalRecords()  # Automatic audit logging via django-simple-history


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
    valor_total = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text='Valor total (não pode ser negativo)'
    )
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


class Project(models.Model):
    """
    Modelo que representa uma startup incubada no AgroHub.
    
    Uma startup é uma empresa em processo de incubação na Ypetec, parte do AgroHub.
    Contém informações sobre a startup e seu status no processo de incubação.
    
    Attributes:
        name: Nome da startup
        edital: Edital relacionado (ForeignKey, opcional - pode ser None para startups sem edital)
        proponente: Usuário responsável pela startup (ForeignKey)
        submitted_on: Data de entrada na incubadora
        status: Status atual no processo de incubação (Pré-Incubação, Incubação, Graduada, Suspensa)
        contato: Informações de contato da startup (opcional)
        data_criacao: Data de criação do registro
        data_atualizacao: Data da última atualização
    """
    STATUS_CHOICES = [
        ('pre_incubacao', 'Pré-Incubação'),
        ('incubacao', 'Incubação'),
        ('graduada', 'Graduada'),
        ('suspensa', 'Suspensa'),
    ]
    
    # Status constants for use in code (avoid magic strings)
    STATUS_PRE_INCUBACAO = 'pre_incubacao'
    STATUS_INCUBACAO = 'incubacao'
    STATUS_GRADUADA = 'graduada'
    STATUS_SUSPENSA = 'suspensa'
    
    CATEGORY_CHOICES = [
        ('agtech', 'AgTech'),
        ('biotech', 'BioTech'),
        ('iot', 'IoT & Hardware'),
        ('edtech', 'EdTech'),
        ('other', 'Outro'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='Nome da Startup')
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Descrição',
        help_text='Descrição da startup e sua solução'
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='other',
        verbose_name='Categoria',
        help_text='Categoria da startup'
    )
    edital = models.ForeignKey(
        Edital,
        on_delete=models.SET_NULL,
        related_name='startups',
        verbose_name='Edital',
        null=True,
        blank=True,
        help_text='Edital relacionado (opcional - startups podem não ter edital)'
    )
    proponente = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='startups',
        verbose_name='Responsável'
    )
    submitted_on = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data de Entrada'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pre_incubacao',
        verbose_name='Status'
    )
    contato = models.TextField(
        blank=True,
        null=True,
        verbose_name='Contato',
        help_text='Informações de contato da startup (email, telefone, website, etc.)'
    )
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, editable=False, verbose_name='Slug')
    logo = models.FileField(
        upload_to='startups/logos/',
        blank=True,
        null=True,
        verbose_name='Logo',
        help_text='Logo da startup (máximo 5MB, formatos: JPG, PNG, GIF, SVG)'
    )
    
    def clean(self) -> None:
        """Validate model fields including logo file upload"""
        super().clean()
        
        # Validate logo file if provided
        if self.logo:
            # Check file size (5MB limit)
            if self.logo.size > 5 * 1024 * 1024:  # 5MB in bytes
                raise ValidationError({
                    'logo': 'O arquivo de logo é muito grande. Tamanho máximo: 5MB.'
                })
            
            # Check file extension
            import os
            ext = os.path.splitext(self.logo.name)[1].lower()
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.svgz']
            if ext not in allowed_extensions:
                raise ValidationError({
                    'logo': f'Formato de arquivo não permitido. Use: {", ".join(allowed_extensions)}'
                })
            
            # Check content type if available (for FileField, content_type may not always be available)
            if hasattr(self.logo, 'content_type') and self.logo.content_type:
                content_type = self.logo.content_type
                allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/svg+xml']
                if content_type not in allowed_types:
                    raise ValidationError({
                        'logo': 'Tipo de arquivo não permitido. Use apenas imagens JPG, PNG, GIF ou SVG.'
                    })
    
    class Meta:
        db_table = 'editais_startup'  # Explicit table name since table was renamed from editais_project
        ordering = ['-submitted_on']
        verbose_name = 'Startup'
        verbose_name_plural = 'Startups'
        indexes = [
            models.Index(fields=['-submitted_on'], name='idx_project_submitted'),
            models.Index(fields=['status'], name='idx_project_status'),
            models.Index(fields=['edital', 'status'], name='idx_project_edital_status'),
            models.Index(fields=['proponente'], name='idx_project_proponente'),
            models.Index(fields=['category'], name='idx_project_category'),
            models.Index(fields=['slug'], name='idx_project_slug'),
        ]
    
    def get_phase_display(self):
        """Map status to phase for display"""
        phase_mapping = {
            'pre_incubacao': 'Ideação',
            'incubacao': 'MVP',
            'graduada': 'Escala',
            'suspensa': 'Suspensa',
        }
        return phase_mapping.get(self.status, 'Ideação')
    
    def get_phase_badge_class(self):
        """Get CSS classes for phase badge"""
        phase_classes = {
            'pre_incubacao': 'bg-purple-100 text-purple-700 border-purple-200',
            'incubacao': 'bg-yellow-100 text-yellow-700 border-yellow-200',
            'graduada': 'bg-blue-100 text-blue-700 border-blue-200',
            'suspensa': 'bg-gray-100 text-gray-700 border-gray-200',
        }
        return phase_classes.get(self.status, 'bg-gray-100 text-gray-700 border-gray-200')
    
    def get_badge_color(self):
        """Get CSS classes for category badge based on category"""
        category_classes = {
            'agtech': 'bg-green-100 text-green-700 border-green-200',
            'biotech': 'bg-blue-100 text-blue-700 border-blue-200',
            'iot': 'bg-purple-100 text-purple-700 border-purple-200',
            'edtech': 'bg-orange-100 text-orange-700 border-orange-200',
        }
        return category_classes.get(self.category, 'bg-gray-100 text-gray-700 border-gray-200')
    
    def __str__(self):
        edital_titulo = (self.edital.titulo or '')[:50] if self.edital and self.edital.titulo else ''
        return f'{self.name} - {edital_titulo}' if edital_titulo else self.name
    
    def _generate_unique_slug(self) -> str:
        """Generate a unique slug from the name - optimized to reduce database queries"""
        return generate_unique_slug(
            text=self.name,
            model_class=Project,
            slug_field_name='slug',
            prefix='startup',
            pk=self.pk,
            max_attempts=SLUG_GENERATION_MAX_ATTEMPTS_PROJECT
        )
    
    def save(self, *args: Any, **kwargs: Any) -> None:
        # Generate slug only if it doesn't exist (on creation)
        if not self.slug:
            self.slug = self._generate_unique_slug()
        
        # Ensure slug is never None after save
        if not self.slug:
            raise ValidationError('Slug não pode ser None. Nome inválido para geração de slug.')
        
        # Handle race condition for slug uniqueness (retry if IntegrityError)
        # Wrap in transaction to ensure atomicity
        max_retries = SLUG_GENERATION_MAX_RETRIES
        for attempt in range(max_retries):
            try:
                with transaction.atomic():
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
    
    def get_absolute_url(self) -> str:
        """Return URL using slug if available, otherwise use PK"""
        if self.slug:
            return reverse('startup_detail_slug', kwargs={'slug': self.slug})
        if self.pk:
            return reverse('startup_detail', kwargs={'pk': self.pk})
        # If object is not saved yet, return empty string
        return ''
    
    def __repr__(self):
        return f"<Project: {self.name} (pk={self.pk}, status={self.status}, edital_id={self.edital_id})>"

