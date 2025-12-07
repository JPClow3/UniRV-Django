from django.contrib import admin
from .models import Edital, EditalValor, Cronograma, Project
from .utils import sanitize_edital_fields
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
        'titulo',
        'status',
        'entidade_principal',
        'created_by',
        'updated_by',
        'data_atualizacao'
    )
    list_filter = ('status', 'entidade_principal', 'created_by', 'updated_by')
    search_fields = (
        'titulo',
        'entidade_principal',
        'numero_edital',
        'analise',
        'objetivo'
    )
    readonly_fields = ('created_by', 'updated_by', 'data_criacao', 'data_atualizacao')
    inlines = [EditalValorInline, CronogramaInline]

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('numero_edital', 'titulo', 'url', 'entidade_principal', 'status')
        }),
        ('Conteúdo', {
            'fields': (
                'analise', 'objetivo', 'etapas', 'recursos',
                'itens_financiaveis', 'criterios_elegibilidade',
                'criterios_avaliacao', 'itens_essenciais_observacoes',
                'detalhes_unirv'
            ),
            'classes': ('collapse',)
        }),
        ('Rastreamento', {
            'fields': ('created_by', 'updated_by', 'data_criacao', 'data_atualizacao'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        """
        Override save_model to sanitize HTML content before saving.
        This prevents XSS vulnerabilities when editing through Django Admin.
        
        Note: History tracking is now handled automatically by django-simple-history.
        """
        # Sanitize HTML fields before saving (same as web views)
        sanitize_edital_fields(obj)
        
        # Track user who created/updated (if not already set)
        if not change:  # New object
            obj.created_by = request.user
        obj.updated_by = request.user
        
        # Call parent save_model to actually save
        # django-simple-history will automatically create history entries
        super().save_model(request, obj, form, change)


@admin.register(EditalValor)
class EditalValorAdmin(admin.ModelAdmin):
    list_display = ('edital', 'valor_total', 'moeda')
    list_filter = ('moeda',)


@admin.register(Cronograma)
class CronogramaAdmin(admin.ModelAdmin):
    list_display = ('edital', 'descricao', 'data_inicio', 'data_fim', 'data_publicacao')
    list_filter = ('data_inicio', 'data_fim', 'data_publicacao')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'edital',
        'proponente',
        'status',
        'contato',
        'submitted_on'
    )
    list_filter = ('status', 'edital', 'submitted_on')
    search_fields = (
        'name',
        'edital__titulo',
        'edital__numero_edital',
        'proponente__username',
        'proponente__email',
        'proponente__first_name',
        'proponente__last_name'
    )
    readonly_fields = ('data_criacao', 'data_atualizacao', 'submitted_on')
    date_hierarchy = 'submitted_on'
    
    fieldsets = (
        ('Informações da Startup', {
            'fields': ('name', 'description', 'category', 'edital', 'proponente', 'status', 'contato', 'logo')
        }),
        ('Datas', {
            'fields': ('submitted_on', 'data_criacao', 'data_atualizacao'),
            'classes': ('collapse',)
        }),
    )


