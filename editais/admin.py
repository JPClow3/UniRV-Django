from django.contrib import admin
from .models import Edital, EditalValor, Cronograma, EditalHistory, Project
from .utils import sanitize_edital_fields


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
        from .models import EditalHistory
        from django.db import transaction
        
        # Sanitize HTML fields before saving (same as web views)
        sanitize_edital_fields(obj)
        
        # Track user who created/updated (if not already set)
        if not change:  # New object
            obj.created_by = request.user
        obj.updated_by = request.user
        
        # Capture original values for history tracking (before save)
        from .services import EditalService
        
        if change:
            try:
                original_obj = Edital.objects.get(pk=obj.pk)
                # Create temporary object with form values for comparison
                temp_obj = Edital()
                # Handle case where form might be None (e.g., in tests)
                changed_fields = form.changed_data if form and hasattr(form, 'changed_data') else []
                for field in changed_fields:
                    if hasattr(obj, field):
                        setattr(temp_obj, field, form.cleaned_data.get(field, getattr(obj, field)))
                changes = EditalService.track_changes(
                    original_obj=original_obj,
                    new_obj=temp_obj,
                    user=request.user,
                    changed_fields=changed_fields
                )
            except Edital.DoesNotExist:
                changes = {}
        else:
            changes = {'titulo': obj.titulo}
        
        # Call parent save_model to actually save
        super().save_model(request, obj, form, change)
        
        # Create history entry after save
        with transaction.atomic():
            EditalHistory.objects.create(
                edital=obj,
                edital_titulo=obj.titulo,
                user=request.user,
                action='create' if not change else 'update',
                changes_summary=changes
            )


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


