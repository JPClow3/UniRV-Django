# Generated migration to enable PostgreSQL trigram extension for fuzzy search
import logging

from django.db import migrations

logger = logging.getLogger(__name__)


def enable_pg_trgm_forward(apps, schema_editor):
    """Enable pg_trgm extension if using PostgreSQL."""
    if schema_editor.connection.vendor == "postgresql":
        with schema_editor.connection.cursor() as cursor:
            cursor.execute("SAVEPOINT pg_trgm_ext")
            try:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
                cursor.execute("RELEASE SAVEPOINT pg_trgm_ext")
            except Exception as e:
                cursor.execute("ROLLBACK TO SAVEPOINT pg_trgm_ext")
                logger.warning(
                    "Could not enable pg_trgm extension: %s. "
                    "This may require superuser privileges.",
                    e,
                )


def enable_pg_trgm_reverse(apps, schema_editor):
    """Drop pg_trgm extension (optional, for rollback)."""
    if schema_editor.connection.vendor == "postgresql":
        with schema_editor.connection.cursor() as cursor:
            cursor.execute("SAVEPOINT pg_trgm_drop")
            try:
                cursor.execute("DROP EXTENSION IF EXISTS pg_trgm;")
                cursor.execute("RELEASE SAVEPOINT pg_trgm_drop")
            except Exception:
                cursor.execute("ROLLBACK TO SAVEPOINT pg_trgm_drop")


class Migration(migrations.Migration):

    dependencies = [
        ("editais", "0017_alter_editalvalor_valor_total_alter_project_logo"),
    ]

    operations = [
        migrations.RunPython(enable_pg_trgm_forward, enable_pg_trgm_reverse),
    ]
