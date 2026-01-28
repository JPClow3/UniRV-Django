# Generated manually to add database-level CHECK constraints for date ranges
# Date: 2026-01-27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('editais', '0026_add_cronograma_ordem_and_validation'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='edital',
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(('end_date__isnull', True)) |
                    models.Q(('start_date__isnull', True)) |
                    models.Q(('end_date__gte', models.F('start_date')))
                ),
                name='edital_end_date_after_start_date'
            ),
        ),
        migrations.AddConstraint(
            model_name='cronograma',
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(('data_fim__isnull', True)) |
                    models.Q(('data_inicio__isnull', True)) |
                    models.Q(('data_fim__gte', models.F('data_inicio')))
                ),
                name='cronograma_data_fim_after_data_inicio'
            ),
        ),
    ]
