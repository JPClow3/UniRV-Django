# Generated migration to remove deprecated EditalHistory model
#
# This migration removes the custom EditalHistory model (created in 0007, improved in 0008)
# and replaces it with django-simple-history, which provides:
# - Automatic change tracking without manual implementation
# - Better performance and scalability
# - Built-in admin integration
# - More robust handling of edge cases
#
# The Edital model now uses HistoricalRecords() from django-simple-history,
# which automatically creates a HistoricalEdital model (see migration 0022).
# This transition from custom history tracking to a library-based solution
# provides better maintainability and feature completeness.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('editais', '0020_add_fulltext_search_index'),
    ]

    operations = [
        # Remove custom EditalHistory model - replaced by django-simple-history
        migrations.DeleteModel(
            name='EditalHistory',
        ),
    ]

