from django.contrib import admin
from .models import Edital, EditalValor, Cronograma, EditalFavorite


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


@admin.register(EditalValor)
class EditalValorAdmin(admin.ModelAdmin):
    list_display = ('edital', 'valor_total', 'moeda')
    list_filter = ('moeda',)


@admin.register(Cronograma)
class CronogramaAdmin(admin.ModelAdmin):
    list_display = ('edital', 'descricao', 'data_inicio', 'data_fim', 'data_publicacao')
    list_filter = ('data_inicio', 'data_fim', 'data_publicacao')


@admin.register(EditalFavorite)
class EditalFavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'edital', 'created_at')
    list_filter = ('user', 'created_at')
    search_fields = ('user__username', 'edital__titulo')
    readonly_fields = ('created_at',)
