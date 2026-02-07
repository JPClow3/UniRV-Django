# Generated migration to add trigram GIN indexes for search performance
import logging

from django.db import migrations

logger = logging.getLogger(__name__)


def add_trigram_indexes_forward(apps, schema_editor):
    """Add GIN indexes using trigram similarity for searchable fields."""
    if schema_editor.connection.vendor == "postgresql":
        with schema_editor.connection.cursor() as cursor:
            # Check if extension is available
            try:
                cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm';")
                has_trgm = cursor.fetchone()
            except Exception:
                has_trgm = None

            if not has_trgm:
                logger.warning("pg_trgm extension not found. Skipping trigram indexes.")
                return

            # Create GIN indexes CONCURRENTLY for trigram similarity searches
            # CONCURRENTLY avoids holding an exclusive lock that blocks writes
            indexes = [
                (
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_edital_titulo_trgm "
                    "ON editais_edital USING gin(titulo gin_trgm_ops);"
                ),
                (
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_edital_entidade_trgm "
                    "ON editais_edital USING gin(entidade_principal gin_trgm_ops);"
                ),
                (
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_edital_numero_trgm "
                    "ON editais_edital USING gin(numero_edital gin_trgm_ops);"
                ),
            ]

            for index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                except Exception as e:
                    logger.error("Failed to create index: %s", e)


def add_trigram_indexes_reverse(apps, schema_editor):
    """Drop trigram indexes."""
    if schema_editor.connection.vendor == "postgresql":
        with schema_editor.connection.cursor() as cursor:
            indexes = [
                "DROP INDEX CONCURRENTLY IF EXISTS idx_edital_titulo_trgm;",
                "DROP INDEX CONCURRENTLY IF EXISTS idx_edital_entidade_trgm;",
                "DROP INDEX CONCURRENTLY IF EXISTS idx_edital_numero_trgm;",
            ]
            for drop_sql in indexes:
                try:
                    cursor.execute(drop_sql)
                except Exception:
                    pass


class Migration(migrations.Migration):

    # CONCURRENTLY cannot run inside a transaction
    atomic = False

    dependencies = [
        ("editais", "0018_enable_pg_trgm_extension"),
    ]

    operations = [
        migrations.RunPython(add_trigram_indexes_forward, add_trigram_indexes_reverse),
    ]
