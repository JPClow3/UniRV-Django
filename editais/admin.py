from django.contrib import admin
from dal import autocomplete
from .models import Edital, EditalValor, Cronograma, Startup, Tag
from simple_history.admin import SimpleHistoryAdmin


class EditalValorInline(admin.TabularInline):
    model = EditalValor
    extra = 1


class CronogramaInline(admin.TabularInline):
    model = Cronograma
    extra = 1


@admin.register(Edital)
class EditalAdmin(SimpleHistoryAdmin):
    list_display = (
        "titulo",
        "status",
        "entidade_principal",
        "created_by",
        "updated_by",
        "data_atualizacao",
    )
    list_filter = ("status", "entidade_principal", "created_by", "updated_by")
    search_fields = (
        "titulo",
        "entidade_principal",
        "numero_edital",
        "analise",
        "objetivo",
    )
    readonly_fields = ("created_by", "updated_by", "data_criacao", "data_atualizacao")
    inlines = [EditalValorInline, CronogramaInline]
    # Optimize queries for list view (prevent N+1 queries)
    list_select_related = ("created_by", "updated_by")

    fieldsets = (
        (
            "Informações Básicas",
            {
                "fields": (
                    "numero_edital",
                    "titulo",
                    "url",
                    "entidade_principal",
                    "status",
                )
            },
        ),
        (
            "Conteúdo",
            {
                "fields": (
                    "analise",
                    "objetivo",
                    "etapas",
                    "recursos",
                    "itens_financiaveis",
                    "criterios_elegibilidade",
                    "criterios_avaliacao",
                    "itens_essenciais_observacoes",
                    "detalhes_unirv",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Rastreamento",
            {
                "fields": (
                    "created_by",
                    "updated_by",
                    "data_criacao",
                    "data_atualizacao",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        """
        Override save_model to track user who created/updated.

        Note: HTML sanitization is now handled automatically in Edital.save() method.
        History tracking is handled automatically by django-simple-history.
        """
        # Track user who created/updated (if not already set)
        if not change:  # New object
            obj.created_by = request.user
        obj.updated_by = request.user

        # Call parent save_model to actually save
        # django-simple-history will automatically create history entries
        # sanitize_edital_fields() is called automatically in Edital.save()
        super().save_model(request, obj, form, change)


@admin.register(EditalValor)
class EditalValorAdmin(admin.ModelAdmin):
    list_display = ("edital", "valor_total", "moeda", "tipo")
    list_filter = ("moeda", "tipo")
    # Optimize queries for list view
    list_select_related = ("edital",)


@admin.register(Cronograma)
class CronogramaAdmin(admin.ModelAdmin):
    list_display = (
        "edital",
        "descricao",
        "ordem",
        "data_inicio",
        "data_fim",
        "data_publicacao",
    )
    list_filter = ("data_inicio", "data_fim", "data_publicacao")
    ordering = ("ordem", "data_inicio")
    # Optimize queries for list view
    list_select_related = ("edital",)


@admin.register(Startup)
class StartupAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "edital",
        "proponente",
        "status",
        "website",
        "incubacao_start_date",
        "submitted_on",
    )
    list_filter = ("status", "edital", "submitted_on", "tags", "category")
    search_fields = (
        "name",
        "edital__titulo",
        "edital__numero_edital",
        "proponente__username",
        "proponente__email",
        "proponente__first_name",
        "proponente__last_name",
        "tags__name",
    )
    readonly_fields = ("data_criacao", "data_atualizacao", "submitted_on")
    date_hierarchy = "submitted_on"
    # Use autocomplete widget for tags (powered by django-autocomplete-light)
    autocomplete_fields = []
    # Optimize queries for list view (prevent N+1 queries)
    list_select_related = ("edital", "proponente")
    list_prefetch_related = ("tags",)

    fieldsets = (
        (
            "Informações da Startup",
            {
                "fields": (
                    "name",
                    "description",
                    "category",
                    "edital",
                    "proponente",
                    "status",
                    "tags",
                )
            },
        ),
        ("Contato e Website", {"fields": ("contato", "website", "logo")}),
        (
            "Datas",
            {
                "fields": (
                    "incubacao_start_date",
                    "submitted_on",
                    "data_criacao",
                    "data_atualizacao",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    class Media:
        """Inclui assets do DAL Select2 para widgets de autocomplete."""

        pass

    def get_form(self, request, obj=None, **kwargs):
        """Sobrescreve o form para usar widgets DAL de autocomplete."""
        form = super().get_form(request, obj, **kwargs)
        if "tags" in form.base_fields:
            form.base_fields["tags"].widget = autocomplete.ModelSelect2Multiple(
                url="tag-autocomplete",
                attrs={"data-placeholder": "Buscar tags..."},
            )
        if "edital" in form.base_fields:
            form.base_fields["edital"].widget = autocomplete.ModelSelect2(
                url="editais_autocomplete",
                attrs={"data-placeholder": "Buscar edital..."},
            )
        return form


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name", "slug")
    readonly_fields = ("created_at",)
