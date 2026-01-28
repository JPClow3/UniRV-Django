# Generated migration to populate slugs for existing Project instances

from django.db import migrations
from django.utils.text import slugify


def populate_project_slugs(apps, schema_editor):
    """Populate slugs for existing Project instances - optimized for performance"""
    Project = apps.get_model('editais', 'Project')
    
    # Process in batches to reduce memory usage
    batch_size = 100
    projects_to_update = []
    
    # Pre-fetch all existing slugs once to avoid repeated queries
    all_existing_slugs = set(Project.objects.exclude(slug__isnull=True).values_list('slug', flat=True))
    
    for project in Project.objects.filter(slug__isnull=True).iterator(chunk_size=batch_size):
        # Generate base slug from name, or use PK fallback if name is empty/None
        if project.name:
            base_slug = slugify(project.name)
        else:
            # Handle edge case: project has no name (shouldn't happen in normal operation,
            # but may exist in legacy data). Use PK-based fallback.
            base_slug = f"startup-{project.pk}"
        
        # Handle edge case: if slugify returns empty string (e.g., name is only special chars)
        # Use a fallback slug based on PK (similar to model's _generate_unique_slug method)
        if not base_slug:
            # Use PK-based fallback since we're in a migration and PKs are guaranteed to exist
            base_slug = f"startup-{project.pk}"
        
        # Find next available slug in memory (no database queries in loop)
        slug = base_slug
        counter = 1
        max_attempts = 10000  # Safety limit to prevent infinite loops
        attempts = 0
        
        while slug in all_existing_slugs and attempts < max_attempts:
            slug = f"{base_slug}-{counter}"
            counter += 1
            attempts += 1
        
        # If we hit the limit, append PK to ensure uniqueness
        if attempts >= max_attempts:
            slug = f"{base_slug}-{project.pk}"
        
        # Add new slug to set to avoid conflicts within the same batch
        all_existing_slugs.add(slug)
        project.slug = slug
        projects_to_update.append(project)
        
        # Bulk update in batches to reduce database hits
        if len(projects_to_update) >= batch_size:
            Project.objects.bulk_update(projects_to_update, ['slug'], batch_size=batch_size)
            projects_to_update = []
    
    # Update remaining items
    if projects_to_update:
        Project.objects.bulk_update(projects_to_update, ['slug'], batch_size=batch_size)


def reverse_populate_project_slugs(apps, schema_editor):
    """Reverse migration - set slugs to None"""
    Project = apps.get_model('editais', 'Project')
    Project.objects.update(slug=None)


class Migration(migrations.Migration):

    dependencies = [
        ('editais', '0013_add_project_slug_and_logo'),
    ]

    operations = [
        migrations.RunPython(populate_project_slugs, reverse_populate_project_slugs),
    ]

