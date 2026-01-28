# Generated manually to add ordem field to Cronograma
# Date: 2026-01-27

from django.db import migrations, models


def populate_ordem_from_data_inicio(apps, schema_editor):
    """Populate ordem field based on existing data_inicio ordering"""
    Cronograma = apps.get_model('editais', 'Cronograma')
    
    # For each edital, assign ordem based on data_inicio
    editais = Cronograma.objects.values_list('edital', flat=True).distinct()
    
    for edital_id in editais:
        cronogramas = Cronograma.objects.filter(edital_id=edital_id).order_by('data_inicio', 'id')
        ordem = 1
        for cronograma in cronogramas:
            cronograma.ordem = ordem
            cronograma.save(update_fields=['ordem'])
            ordem += 1


def reverse_populate_ordem(apps, schema_editor):
    """Reverse migration - no action needed"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('editais', '0025_add_editalvalor_tipo_and_unique_constraint'),
    ]

    operations = [
        migrations.AddField(
            model_name='cronograma',
            name='ordem',
            field=models.PositiveIntegerField(
                blank=True,
                help_text='Ordem de exibição do item no cronograma (opcional)',
                null=True
            ),
        ),
        migrations.AddIndex(
            model_name='cronograma',
            index=models.Index(fields=['ordem'], name='idx_cronograma_ordem'),
        ),
        migrations.AlterModelOptions(
            name='cronograma',
            options={'ordering': ['ordem', 'data_inicio'], 'verbose_name': 'Cronograma', 'verbose_name_plural': 'Cronogramas'},
        ),
        migrations.RunPython(populate_ordem_from_data_inicio, reverse_populate_ordem),
    ]
