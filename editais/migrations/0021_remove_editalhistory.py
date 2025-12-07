# Generated migration to remove deprecated EditalHistory model
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('editais', '0020_add_fulltext_search_index'),
    ]

    operations = [
        migrations.DeleteModel(
            name='EditalHistory',
        ),
    ]

