from django.contrib import admin
from .models import Edital, EditalValor, Cronograma, EditalHistory
from .views import sanitize_edital_fields


class EditalValorInline(admin.TabularInline):
    model = EditalValor
    extra = 1


class CronogramaInline(admin.TabularInline):
    model = Cronograma
    extra = 1


@admin.register(Edital)
class EditalAdmin(admin.ModelAdmin):
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
        """
        # Sanitize HTML fields before saving (same as web views)
        sanitize_edital_fields(obj)
        
        # Track user who created/updated (if not already set)
        if not change:  # New object
            obj.created_by = request.user
        obj.updated_by = request.user
        
        # Call parent save_model to actually save
        super().save_model(request, obj, form, change)


@admin.register(EditalValor)
class EditalValorAdmin(admin.ModelAdmin):
    list_display = ('edital', 'valor_total', 'moeda')
    list_filter = ('moeda',)


@admin.register(Cronograma)
class CronogramaAdmin(admin.ModelAdmin):
    list_display = ('edital', 'descricao', 'data_inicio', 'data_fim', 'data_publicacao')
    list_filter = ('data_inicio', 'data_fim', 'data_publicacao')


@admin.register(EditalHistory)
class EditalHistoryAdmin(admin.ModelAdmin):
    list_display = ('edital_titulo_display', 'action', 'user', 'timestamp')
    list_filter = ('action', 'timestamp', 'user')
    search_fields = ('edital__titulo', 'edital_titulo', 'user__username')
    readonly_fields = ('edital', 'edital_titulo', 'user', 'action', 'field_name', 'old_value', 'new_value', 'timestamp', 'changes_summary')
    date_hierarchy = 'timestamp'
    
    def edital_titulo_display(self, obj):
        """Display edital title (from edital or preserved edital_titulo)"""
        return obj.edital.titulo if obj.edital else (obj.edital_titulo or 'Edital Deletado')
    edital_titulo_display.short_description = 'Edital'
    
    def has_add_permission(self, request):
        return False  # History entries are created automatically


