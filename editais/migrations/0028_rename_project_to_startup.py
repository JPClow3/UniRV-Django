# Generated manually to rename Project model to Startup
# Date: 2026-01-27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('editais', '0027_add_date_check_constraints'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Project',
            new_name='Startup',
        ),
    ]
