# Generated migration to add trigram GIN indexes for search performance
from django.db import migrations
from django.db import connection


def add_trigram_indexes_forward(apps, schema_editor):
    """Add GIN indexes using trigram similarity for searchable fields."""
    if connection.vendor == 'postgresql':
        with connection.cursor() as cursor:
            try:
                # Check if extension is available
                cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm';")
                if not cursor.fetchone():
                    # Extension not enabled, skip indexes
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning("pg_trgm extension not found. Skipping trigram indexes.")
                    return
                
                # Create GIN indexes for trigram similarity searches
                # Using CONCURRENTLY to avoid locking in production
                indexes = [
                    ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_edital_titulo_trgm "
                     "ON editais_edital USING gin(titulo gin_trgm_ops);"),
                    ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_edital_entidade_trgm "
                     "ON editais_edital USING gin(entidade_principal gin_trgm_ops);"),
                    ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_edital_numero_trgm "
                     "ON editais_edital USING gin(numero_edital gin_trgm_ops);"),
                ]
                
                for index_sql in indexes:
                    try:
                        cursor.execute(index_sql)
                    except Exception as e:
                        # CONCURRENTLY requires no active transactions
                        # Fall back to regular index creation
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f"Could not create index concurrently: {e}. "
                                     f"Trying without CONCURRENTLY...")
                        # Remove CONCURRENTLY and try again
                        index_sql_fallback = index_sql.replace("CONCURRENTLY ", "")
                        try:
                            cursor.execute(index_sql_fallback)
                        except Exception as e2:
                            logger.error(f"Failed to create index: {e2}")
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Error creating trigram indexes: {e}")


def add_trigram_indexes_reverse(apps, schema_editor):
    """Drop trigram indexes."""
    if connection.vendor == 'postgresql':
        with connection.cursor() as cursor:
            indexes = [
                "DROP INDEX IF EXISTS idx_edital_titulo_trgm;",
                "DROP INDEX IF EXISTS idx_edital_entidade_trgm;",
                "DROP INDEX IF EXISTS idx_edital_numero_trgm;",
            ]
            for drop_sql in indexes:
                try:
                    cursor.execute(drop_sql)
                except Exception:
                    # Ignore errors on reverse migration
                    pass


class Migration(migrations.Migration):

    dependencies = [
        ('editais', '0018_enable_pg_trgm_extension'),
    ]

    operations = [
        migrations.RunPython(
            add_trigram_indexes_forward,
            add_trigram_indexes_reverse
        ),
    ]

