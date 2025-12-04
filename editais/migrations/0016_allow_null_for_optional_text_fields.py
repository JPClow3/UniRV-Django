# Generated manually for bug hunt follow-up improvements

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('editais', '0015_remove_note_add_contato_update_related_names'),
    ]

    operations = [
        migrations.AlterField(
            model_name='edital',
            name='analise',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='edital',
            name='objetivo',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='edital',
            name='etapas',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='edital',
            name='recursos',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='edital',
            name='itens_financiaveis',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='edital',
            name='criterios_elegibilidade',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='edital',
            name='criterios_avaliacao',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='edital',
            name='itens_essenciais_observacoes',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='edital',
            name='detalhes_unirv',
            field=models.TextField(blank=True, null=True),
        ),
    ]

