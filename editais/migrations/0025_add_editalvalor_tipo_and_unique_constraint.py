# Generated manually to add tipo field and unique constraint
# Date: 2026-01-27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('editais', '0024_fix_project_related_name_conflict'),
    ]

    operations = [
        migrations.AddField(
            model_name='editalvalor',
            name='tipo',
            field=models.CharField(
                choices=[('total', 'Valor Total'), ('por_projeto', 'Por Projeto'), ('outro', 'Outro')],
                default='total',
                help_text='Tipo de valor (total, por projeto, etc.)',
                max_length=20
            ),
        ),
        migrations.AlterUniqueTogether(
            name='editalvalor',
            unique_together={('edital', 'moeda')},
        ),
    ]
