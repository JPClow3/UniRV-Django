# Generated migration to add GIN index for PostgreSQL full-text search
from django.db import migrations
from django.db import connection


def add_fulltext_search_index_forward(apps, schema_editor):
    """Add GIN index for full-text search on searchable fields."""
    if connection.vendor == 'postgresql':
        with connection.cursor() as cursor:
            try:
                # Create a GIN index on a generated tsvector column for full-text search
                # This combines all searchable fields into a single searchable vector
                # Using Portuguese language configuration for proper stemming
                index_sql = """
                    CREATE INDEX IF NOT EXISTS idx_edital_fulltext_search 
                    ON editais_edital 
                    USING gin(
                        to_tsvector('portuguese',
                            COALESCE(titulo, '') || ' ' ||
                            COALESCE(entidade_principal, '') || ' ' ||
                            COALESCE(numero_edital, '') || ' ' ||
                            COALESCE(analise, '') || ' ' ||
                            COALESCE(objetivo, '') || ' ' ||
                            COALESCE(etapas, '') || ' ' ||
                            COALESCE(recursos, '') || ' ' ||
                            COALESCE(itens_financiaveis, '') || ' ' ||
                            COALESCE(criterios_elegibilidade, '') || ' ' ||
                            COALESCE(criterios_avaliacao, '') || ' ' ||
                            COALESCE(itens_essenciais_observacoes, '') || ' ' ||
                            COALESCE(detalhes_unirv, '')
                        )
                    );
                """
                cursor.execute(index_sql)
            except Exception as e:
                # Log but don't fail migration
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Could not create full-text search index: {e}. "
                             f"This may require superuser privileges or the index may already exist.")


def add_fulltext_search_index_reverse(apps, schema_editor):
    """Drop full-text search index."""
    if connection.vendor == 'postgresql':
        with connection.cursor() as cursor:
            try:
                cursor.execute("DROP INDEX IF EXISTS idx_edital_fulltext_search;")
            except Exception:
                # Ignore errors on reverse migration
                pass


class Migration(migrations.Migration):

    dependencies = [
        ('editais', '0019_add_trigram_indexes'),
    ]

    operations = [
        migrations.RunPython(
            add_fulltext_search_index_forward,
            add_fulltext_search_index_reverse
        ),
    ]

