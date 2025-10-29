from django.contrib import admin
from .models import Edital, EditalValor, Cronograma


class EditalValorInline(admin.TabularInline):
    model = EditalValor
    extra = 1


class CronogramaInline(admin.TabularInline):
    model = Cronograma
    extra = 1


@admin.register(Edital)
class EditalAdmin(admin.ModelAdmin):
    list_display = ("titulo", "status", "entidade_principal", "data_atualizacao")
    list_filter = ("status", "entidade_principal")
    search_fields = ("titulo", "entidade_principal", "numero_edital")
    inlines = [EditalValorInline, CronogramaInline]


@admin.register(EditalValor)
class EditalValorAdmin(admin.ModelAdmin):
    list_display = ("edital", "valor_total", "moeda")
    list_filter = ("moeda",)


@admin.register(Cronograma)
class CronogramaAdmin(admin.ModelAdmin):
    list_display = ("edital", "descricao", "data_inicio", "data_fim", "data_publicacao")
    list_filter = ("data_inicio", "data_fim", "data_publicacao")
