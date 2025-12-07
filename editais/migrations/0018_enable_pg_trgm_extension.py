# Generated migration to enable PostgreSQL trigram extension for fuzzy search
from django.db import migrations
from django.db import connection


def enable_pg_trgm_forward(apps, schema_editor):
    """Enable pg_trgm extension if using PostgreSQL."""
    if connection.vendor == 'postgresql':
        with connection.cursor() as cursor:
            try:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
            except Exception as e:
                # Extension might already exist or require superuser privileges
                # Log but don't fail migration
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Could not enable pg_trgm extension: {e}. "
                             f"This may require superuser privileges.")


def enable_pg_trgm_reverse(apps, schema_editor):
    """Drop pg_trgm extension (optional, for rollback)."""
    if connection.vendor == 'postgresql':
        with connection.cursor() as cursor:
            try:
                cursor.execute("DROP EXTENSION IF EXISTS pg_trgm;")
            except Exception:
                # Ignore errors on reverse migration
                pass


class Migration(migrations.Migration):

    dependencies = [
        ('editais', '0017_alter_editalvalor_valor_total_alter_project_logo'),
    ]

    operations = [
        migrations.RunPython(
            enable_pg_trgm_forward,
            enable_pg_trgm_reverse
        ),
    ]

