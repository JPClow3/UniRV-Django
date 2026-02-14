from typing import Optional, Any
import logging
import os
from django.contrib.auth.models import User
from django.conf import settings
from django.db import (
    models,
    connection,
    ProgrammingError,
    OperationalError,
    IntegrityError,
    transaction,
)
from django.db.models import Q
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from simple_history.models import HistoricalRecords

from .utils import determine_edital_status, generate_unique_slug, sanitize_edital_fields
from .constants import (
    SLUG_GENERATION_MAX_ATTEMPTS_EDITAL,
    SLUG_GENERATION_MAX_ATTEMPTS_STARTUP,
    SLUG_GENERATION_MAX_RETRIES,
    MAX_SEARCH_LENGTH,
    MAX_LOGO_FILE_SIZE,
)

logger = logging.getLogger(__name__)


class SlugGenerationMixin:
    """
    Mixin for models that need unique slug generation with retry logic.

    Provides common slug generation functionality to avoid code duplication
    between Edital and Startup models.

    Class attributes to override:
        SLUG_PREFIX: str - Prefix for the slug (e.g., 'edital', 'startup')
        SLUG_MAX_ATTEMPTS: int - Max attempts for unique slug generation
        SLUG_SOURCE_FIELD: str - Field name to generate slug from (e.g., 'titulo', 'name')
    """

    SLUG_PREFIX: str = ""
    SLUG_MAX_ATTEMPTS: int = 10
    SLUG_SOURCE_FIELD: str = "titulo"

    def _generate_unique_slug(self) -> str:
        """
        Generate a unique slug from the source field.

        RACE CONDITION HANDLING:
        Slug uniqueness is enforced at the database level with a unique constraint.
        The save() method includes retry logic that regenerates the slug if an
        IntegrityError occurs due to concurrent creation with the same title.
        """
        source_text = getattr(self, self.SLUG_SOURCE_FIELD, "")
        return generate_unique_slug(
            text=source_text,
            model_class=self.__class__,
            slug_field_name="slug",
            prefix=self.SLUG_PREFIX,
            pk=self.pk,
            max_attempts=self.SLUG_MAX_ATTEMPTS,
        )

    def _save_with_slug_retry(self, save_func, *args, **kwargs) -> None:
        """
        Save the model with retry logic for slug conflicts.

        Each save attempt uses its own savepoint so that IntegrityError
        from slug conflicts does not corrupt the outer transaction.

        Args:
            save_func: The parent save function to call
            *args, **kwargs: Arguments to pass to save_func
        """
        for attempt in range(SLUG_GENERATION_MAX_RETRIES):
            try:
                # Generate slug only if it doesn't exist (on creation)
                if not self.slug:
                    self.slug = self._generate_unique_slug()
                # Ensure slug is never None after save
                if not self.slug:
                    raise ValidationError(
                        "Slug não pode ser None. Campo fonte inválido para geração de slug."
                    )
                with transaction.atomic():
                    save_func(*args, **kwargs)
                return
            except IntegrityError as e:
                if (
                    "slug" in str(e).lower() or "unique" in str(e).lower()
                ) and attempt < SLUG_GENERATION_MAX_RETRIES - 1:
                    self.slug = self._generate_unique_slug()
                    continue
                raise


class EditalQuerySet(models.QuerySet):
    """Custom QuerySet for Edital model with common query patterns."""

    def with_related(self):
        """Add select_related for created_by and updated_by to optimize queries."""
        return self.select_related("created_by", "updated_by")

    def with_prefetch(self):
        """Add prefetch_related for valores and cronogramas to optimize queries."""
        return self.prefetch_related("valores", "cronogramas")

    def active(self):
        """Filter editais that are not drafts."""
        return self.exclude(status="draft")

    def search(self, query: str):
        """
        Search editais by query string.

        Uses PostgreSQL full-text search with GIN indexes for performance.

        Args:
            query: Search query string (will be truncated if too long)

        Returns:
            QuerySet: Filtered and ranked queryset
        """
        if not query:
            return self

        # Convert query to string if it's not already (defensive programming)
        if not isinstance(query, str):
            query = str(query) if query is not None else ""
            if not query:
                return self

        if len(query) > MAX_SEARCH_LENGTH:
            query = query[:MAX_SEARCH_LENGTH]

        # Only use PostgreSQL full-text search when available (SQLite uses icontains)
        if connection.vendor != "postgresql":
            pass  # Fall through to icontains below
        else:
            # PostgreSQL full-text search with Portuguese language configuration
            # Enables stemming (e.g., "startup" matches "startups") and ranking
            search_fields = getattr(
                settings,
                "EDITAL_SEARCH_FIELDS",
                [
                    "titulo",
                    "entidade_principal",
                    "numero_edital",
                    "analise",
                    "objetivo",
                    "etapas",
                    "recursos",
                    "itens_financiaveis",
                    "criterios_elegibilidade",
                    "criterios_avaliacao",
                    "itens_essenciais_observacoes",
                    "detalhes_unirv",
                ],
            )

            try:
                # Build search vector with Portuguese language configuration
                # 'portuguese' config provides stemming and stop word removal
                search_vector = SearchVector(*search_fields, config="portuguese")

                # Create search query with Portuguese config
                search_query_obj = SearchQuery(query, config="portuguese")

                # Annotate queryset with search rank for relevance ordering
                return (
                    self.annotate(
                        search=search_vector,
                        rank=SearchRank(search_vector, search_query_obj),
                    )
                    .filter(search=search_query_obj)
                    .order_by("-rank", "-data_atualizacao")
                )
            except (
                AttributeError,
                ValueError,
                TypeError,
                ProgrammingError,
                OperationalError,
                NotImplementedError,
            ) as e:
                # Fallback to icontains if full-text search fails
                # (e.g., pg_catalog extension not enabled, non-PostgreSQL backend,
                #  or missing full-text search configuration)
                logger.warning(
                    f"PostgreSQL full-text search failed, falling back to icontains: {e}"
                )

        # Fallback: icontains search (used for SQLite or when PostgreSQL full-text fails)
        q_objects = Q()
        fallback_fields = getattr(
            settings,
            "EDITAL_SEARCH_FIELDS",
            ["titulo", "entidade_principal", "numero_edital"],
        )

        # Validate fields exist on the model to prevent FieldError
        try:
            model_fields = {
                f.name
                for f in self.model._meta.get_fields()
                if hasattr(f, "get_internal_type")
                and f.get_internal_type() in ("CharField", "TextField")
            }
        except (AttributeError, TypeError):
            model_fields = {
                f.name for f in self.model._meta.get_fields() if hasattr(f, "name")
            }

        valid_search_fields = [f for f in fallback_fields if f in model_fields]

        if not valid_search_fields:
            logger.warning(
                f"No valid search fields found in EDITAL_SEARCH_FIELDS. Fields checked: {fallback_fields}"
            )
            return self.none()

        for field in valid_search_fields:
            q_objects |= Q(**{f"{field}__icontains": query})

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

    def active(self):
        """Filter editais that are not drafts."""
        return self.get_queryset().active()

    def search(self, query: str):
        """
        Search editais by query string.

        Uses PostgreSQL full-text search with GIN indexes for performance.

        Args:
            query: Search query string (will be truncated if too long)

        Returns:
            QuerySet: Filtered and ranked queryset
        """
        return self.get_queryset().search(query)


class Edital(SlugGenerationMixin, models.Model):
    """
    Modelo que representa um edital de fomento.

    Um edital é uma oportunidade de financiamento com informações sobre
    título, datas, status, valores, cronograma e conteúdo detalhado.

    Properties:
        days_until_deadline: Dias restantes até o prazo
        is_deadline_imminent: True se prazo está próximo (7 dias)
    """

    # SlugGenerationMixin configuration
    SLUG_PREFIX = "edital"
    SLUG_MAX_ATTEMPTS = SLUG_GENERATION_MAX_ATTEMPTS_EDITAL
    SLUG_SOURCE_FIELD = "titulo"

    STATUS_CHOICES = [
        ("draft", "Rascunho"),
        ("aberto", "Aberto"),
        ("em_andamento", "Em Andamento"),
        ("fechado", "Fechado"),
        ("programado", "Programado"),
    ]

    numero_edital = models.CharField(max_length=100, blank=True, null=True)
    titulo = models.CharField(max_length=500)
    slug = models.SlugField(
        max_length=255, unique=True, blank=True, null=True, editable=False
    )
    url = models.URLField(max_length=1000)
    entidade_principal = models.CharField(max_length=200, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    start_date = models.DateField(
        blank=True, null=True, verbose_name="Data de Abertura"
    )
    end_date = models.DateField(
        blank=True, null=True, verbose_name="Data de Encerramento"
    )
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    # User tracking for activity log
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_editais",
        verbose_name="Criado por",
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_editais",
        verbose_name="Atualizado por",
    )

    # Conteúdo
    analise = models.TextField(blank=True, null=True)
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
        ordering = ["-data_atualizacao"]
        verbose_name = "Edital"
        verbose_name_plural = "Editais"
        indexes = [
            models.Index(fields=["-data_atualizacao"], name="idx_data_atualizacao"),
            models.Index(fields=["status"], name="idx_status"),
            models.Index(fields=["entidade_principal"], name="idx_entidade"),
            models.Index(fields=["numero_edital"], name="idx_numero"),
            models.Index(fields=["slug"], name="idx_slug"),
            models.Index(
                fields=["status", "start_date", "end_date"], name="idx_status_dates"
            ),
            models.Index(fields=["titulo"], name="idx_titulo"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_date__gte=models.F("start_date"))
                | models.Q(end_date__isnull=True)
                | models.Q(start_date__isnull=True),
                name="edital_end_date_after_start_date",
            ),
        ]

    def clean(self) -> None:
        """Validate model fields"""
        super().clean()

        # Validate dates
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValidationError(
                    {
                        "end_date": "A data de encerramento deve ser posterior à data de abertura."
                    }
                )

        # Validate that slug can be generated if title exists
        if not self.slug and self.titulo:
            try:
                test_slug = self._generate_unique_slug()
                if not test_slug:
                    raise ValidationError(
                        {
                            "titulo": "Título inválido para geração de slug. Use um título válido."
                        }
                    )
            except ValidationError:
                # Re-raise ValidationError as-is (don't wrap it)
                raise
            except Exception as e:
                # If slug generation fails with other exceptions, raise validation error
                raise ValidationError({"titulo": f"Erro ao gerar slug: {str(e)}"})

    def save(self, *args: Any, **kwargs: Any) -> None:
        today = timezone.now().date()
        self.status = determine_edital_status(
            current_status=self.status,
            start_date=self.start_date,
            end_date=self.end_date,
            today=today,
        )
        # Sanitize HTML fields to prevent XSS attacks
        sanitize_edital_fields(self)
        self._save_with_slug_retry(super().save, *args, **kwargs)

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
            return reverse("edital_detail_slug", kwargs={"slug": self.slug})
        if self.pk:
            return reverse("edital_detail", kwargs={"pk": self.pk})
        # If object is not saved yet, return empty string
        return ""

    @property
    def descricao(self) -> Optional[str]:
        """Compatibilidade: alias de objetivo para chamadas legadas."""
        return self.objetivo

    @descricao.setter
    def descricao(self, value: Optional[str]) -> None:
        self.objetivo = value

    history = HistoricalRecords()


class EditalValor(models.Model):
    """
    Modelo que representa o valor financeiro de um edital.

    Um edital pode ter múltiplos valores em diferentes moedas.

    Attributes:
        edital: Edital relacionado (ForeignKey)
        valor_total: Valor total do edital
        moeda: Moeda do valor (BRL, USD, EUR)
        tipo: Tipo de valor (total, por projeto, etc.)
    """

    MOEDA_CHOICES = [
        ("BRL", "Real Brasileiro (R$)"),
        ("USD", "Dólar Americano (US$)"),
        ("EUR", "Euro (€)"),
    ]

    TIPO_CHOICES = [
        ("total", "Valor Total"),
        ("por_projeto", "Por Projeto"),
        ("outro", "Outro"),
    ]

    edital = models.ForeignKey(Edital, on_delete=models.CASCADE, related_name="valores")
    valor_total = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text="Valor total (não pode ser negativo)",
    )
    moeda = models.CharField(
        max_length=10,
        choices=MOEDA_CHOICES,
        default="BRL",
        help_text="Moeda do valor total",
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default="total",
        help_text="Tipo de valor (total, por projeto, etc.)",
    )

    class Meta:
        verbose_name = "Valor do Edital"
        verbose_name_plural = "Valores dos Editais"
        # Índice composto para queries que filtram por edital e moeda
        indexes = [
            models.Index(fields=["edital", "moeda"], name="idx_edital_moeda"),
        ]
        # Constraint única: cada edital pode ter apenas um valor por moeda
        unique_together = [["edital", "moeda"]]

    def __str__(self):
        tipo_display = self.get_tipo_display()
        return (
            f"{self.edital.titulo} - {self.valor_total} {self.moeda} ({tipo_display})"
        )

    def __repr__(self):
        return f"<EditalValor: edital_id={self.edital_id}, valor={self.valor_total} {self.moeda}, tipo={self.tipo}>"


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
        ordem: Ordem de exibição do item no cronograma
    """

    edital = models.ForeignKey(
        Edital, on_delete=models.CASCADE, related_name="cronogramas"
    )
    data_inicio = models.DateField(blank=True, null=True)
    data_fim = models.DateField(blank=True, null=True)
    data_publicacao = models.DateField(blank=True, null=True)
    descricao = models.CharField(max_length=300, blank=True)
    ordem = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Ordem de exibição do item no cronograma (opcional)",
    )

    class Meta:
        ordering = ["ordem", "data_inicio"]
        verbose_name = "Cronograma"
        verbose_name_plural = "Cronogramas"
        # Índices para melhorar queries de cronogramas
        indexes = [
            models.Index(
                fields=["edital", "data_inicio"], name="idx_cronograma_edital_data"
            ),
            models.Index(fields=["data_inicio"], name="idx_cronograma_data_inicio"),
            models.Index(fields=["ordem"], name="idx_cronograma_ordem"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(data_fim__gte=models.F("data_inicio"))
                | models.Q(data_fim__isnull=True)
                | models.Q(data_inicio__isnull=True),
                name="cronograma_data_fim_after_data_inicio",
            ),
        ]

    def clean(self) -> None:
        """Validate model fields"""
        super().clean()

        # Validate dates: data_fim must be >= data_inicio if both are provided
        if self.data_inicio and self.data_fim:
            if self.data_fim < self.data_inicio:
                raise ValidationError(
                    {
                        "data_fim": "A data de fim deve ser posterior ou igual à data de início."
                    }
                )

    def __str__(self):
        return f"{self.edital.titulo} - {self.descricao}"

    def __repr__(self):
        return (
            f"<Cronograma: edital_id={self.edital_id}, descricao={self.descricao[:30]}>"
        )


class Tag(models.Model):
    """
    Modelo que representa uma tag para categorização de startups.

    Tags permitem categorização flexível e múltipla de startups.
    """

    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Nome",
        help_text='Nome da tag (ex: "AgTech", "Inovação", "Sustentabilidade")',
    )
    slug = models.SlugField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        editable=False,
        verbose_name="Slug",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")

    class Meta:
        ordering = ["name"]
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        indexes = [
            models.Index(fields=["name"], name="idx_tag_name"),
            models.Index(fields=["slug"], name="idx_tag_slug"),
        ]

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Generate slug from name if not provided, with retry on conflicts."""
        for attempt in range(3):
            try:
                if not self.slug and self.name:
                    self.slug = generate_unique_slug(
                        text=self.name,
                        model_class=Tag,
                        slug_field_name="slug",
                        prefix="tag",
                        pk=self.pk,
                        max_attempts=10,
                    )
                with transaction.atomic():
                    super().save(*args, **kwargs)
                return
            except IntegrityError as e:
                if (
                    "slug" in str(e).lower() or "unique" in str(e).lower()
                ) and attempt < 2:
                    self.slug = ""
                    continue
                raise

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<Tag: {self.name} (slug={self.slug})>"


class StartupQuerySet(models.QuerySet):
    """Custom QuerySet for Startup with search support."""

    def search(self, query: str):
        """Filter by name or description (icontains). Truncates to MAX_SEARCH_LENGTH."""
        if not query:
            return self
        q = str(query).strip() if query else ""
        if not q:
            return self
        if len(q) > MAX_SEARCH_LENGTH:
            q = q[:MAX_SEARCH_LENGTH]
        return self.filter(Q(name__icontains=q) | Q(description__icontains=q))


class StartupManager(models.Manager):
    def get_queryset(self):
        return StartupQuerySet(self.model, using=self._db)

    def search(self, query: str):
        return self.get_queryset().search(query)


class Startup(SlugGenerationMixin, models.Model):
    """
    Modelo que representa uma startup incubada no AgroHub.

    Uma startup é uma empresa em processo de incubação na Ypetec, parte do AgroHub.
    Contém informações sobre a startup e seu status no processo de incubação.

    Attributes:
        name: Nome da startup
        edital: Edital relacionado (ForeignKey, opcional - pode ser None para startups sem edital)
        proponente: Usuário responsável pela startup (ForeignKey)
        submitted_on: Data de entrada na incubadora
        status: Fase de maturidade (Ideação, MVP, Escala, Suspensa). Simbólico, não pass/fail.
        contato: Informações de contato da startup (opcional)
        data_criacao: Data de criação do registro
        data_atualizacao: Data da última atualização
    """

    # SlugGenerationMixin configuration
    SLUG_PREFIX = "startup"
    SLUG_MAX_ATTEMPTS = SLUG_GENERATION_MAX_ATTEMPTS_STARTUP
    SLUG_SOURCE_FIELD = "name"

    STATUS_CHOICES = [
        ("pre_incubacao", "Pré-Incubação"),
        ("incubacao", "Incubação"),
        ("graduada", "Graduada"),
        ("suspensa", "Suspensa"),
    ]

    # Status constants for use in code (avoid magic strings)
    STATUS_PRE_INCUBACAO = "pre_incubacao"
    STATUS_INCUBACAO = "incubacao"
    STATUS_GRADUADA = "graduada"
    STATUS_SUSPENSA = "suspensa"

    CATEGORY_CHOICES = [
        ("agtech", "AgTech"),
        ("biotech", "BioTech"),
        ("iot", "IoT & Hardware"),
        ("edtech", "EdTech"),
        ("other", "Outro"),
    ]

    name = models.CharField(max_length=200, verbose_name="Nome da Startup")
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descrição",
        help_text="Descrição da startup e sua solução",
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default="other",
        verbose_name="Categoria",
        help_text="Categoria da startup",
    )
    edital = models.ForeignKey(
        Edital,
        on_delete=models.SET_NULL,
        related_name="startups",
        verbose_name="Edital",
        null=True,
        blank=True,
        help_text="Edital relacionado (opcional - startups podem não ter edital)",
    )
    proponente = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="startups_owned",
        verbose_name="Responsável",
    )
    submitted_on = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Entrada"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pre_incubacao",
        verbose_name="Fase",
        help_text="Fase de maturidade (Ideação, MVP, Escala, Suspensa). Indicador simbólico, não avaliação de aprovação.",
    )
    contato = models.TextField(
        blank=True,
        null=True,
        verbose_name="Contato",
        help_text="Informações de contato da startup (email, telefone, etc.)",
    )
    website = models.URLField(
        blank=True,
        null=True,
        verbose_name="Website",
        help_text="Website da startup (ex: https://www.exemplo.com)",
    )
    incubacao_start_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="Data de Início da Incubação",
        help_text="Data em que a startup iniciou o processo de incubação",
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        verbose_name="Tags",
        help_text="Tags para categorização da startup",
    )
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        null=True,
        editable=False,
        verbose_name="Slug",
    )
    logo = models.FileField(
        upload_to="startups/logos/",
        blank=True,
        null=True,
        verbose_name="Logo",
        help_text="Logo da startup (máximo 5MB, formatos: JPG, PNG, GIF, SVG)",
    )

    def clean(self) -> None:
        """Validate model fields including logo file upload"""
        super().clean()

        # Validate logo file if provided
        if self.logo:
            # Check file size (5MB limit) - defensive check for size attribute
            if hasattr(self.logo, "size") and self.logo.size is not None:
                if self.logo.size > MAX_LOGO_FILE_SIZE:
                    raise ValidationError(
                        {
                            "logo": "O arquivo de logo é muito grande. Tamanho máximo: 5MB."
                        }
                    )

            # Check file extension - defensive check for name attribute
            if hasattr(self.logo, "name") and self.logo.name:
                ext = os.path.splitext(self.logo.name)[1].lower()
                allowed_extensions = [".jpg", ".jpeg", ".png", ".gif", ".svg", ".svgz"]
                if ext not in allowed_extensions:
                    raise ValidationError(
                        {
                            "logo": f'Formato de arquivo não permitido. Use: {", ".join(allowed_extensions)}'
                        }
                    )

            # Check content type if available (for FileField, content_type may not always be available)
            if hasattr(self.logo, "content_type") and self.logo.content_type:
                content_type = self.logo.content_type
                allowed_types = [
                    "image/jpeg",
                    "image/png",
                    "image/gif",
                    "image/svg+xml",
                ]
                if content_type not in allowed_types:
                    raise ValidationError(
                        {
                            "logo": "Tipo de arquivo não permitido. Use apenas imagens JPG, PNG, GIF ou SVG."
                        }
                    )

        # Validate that slug can be generated if name exists
        if not self.slug and self.name:
            try:
                test_slug = self._generate_unique_slug()
                if not test_slug:
                    raise ValidationError(
                        {
                            "name": "Nome inválido para geração de slug. Use um nome válido."
                        }
                    )
            except ValidationError:
                # Re-raise ValidationError as-is (don't wrap it)
                raise
            except Exception as e:
                # If slug generation fails with other exceptions, raise validation error
                raise ValidationError({"name": f"Erro ao gerar slug: {str(e)}"})

    objects = StartupManager()

    class Meta:
        db_table = "editais_startup"  # Explicit table name since table was renamed from editais_project
        ordering = ["-submitted_on"]
        verbose_name = "Startup"
        verbose_name_plural = "Startups"
        indexes = [
            models.Index(fields=["-submitted_on"], name="idx_project_submitted"),
            models.Index(fields=["status"], name="idx_project_status"),
            models.Index(fields=["edital", "status"], name="idx_project_edital_status"),
            models.Index(fields=["proponente"], name="idx_project_proponente"),
            models.Index(fields=["category"], name="idx_project_category"),
            models.Index(fields=["slug"], name="idx_project_slug"),
        ]

    def get_phase_display(self):
        """Map status to phase for display"""
        phase_mapping = {
            "pre_incubacao": "Ideação",
            "incubacao": "MVP",
            "graduada": "Escala",
            "suspensa": "Suspensa",
        }
        return phase_mapping.get(self.status, "Ideação")

    def __str__(self):
        edital_titulo = (
            (self.edital.titulo or "")[:50]
            if self.edital and self.edital.titulo
            else ""
        )
        return f"{self.name} - {edital_titulo}" if edital_titulo else self.name

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Save with slug generation using mixin's retry logic."""
        self._save_with_slug_retry(super().save, *args, **kwargs)

    def get_absolute_url(self) -> str:
        """Return URL using slug if available, otherwise use PK"""
        if self.slug:
            return reverse("startup_detail_slug", kwargs={"slug": self.slug})
        if self.pk:
            return reverse("startup_detail", kwargs={"pk": self.pk})
        # If object is not saved yet, return empty string
        return ""

    def __repr__(self):
        return f"<Startup: {self.name} (pk={self.pk}, status={self.status}, edital_id={self.edital_id})>"
