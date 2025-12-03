# Generated migration to populate slugs for existing Project instances

from django.db import migrations
from django.utils.text import slugify
import time


def populate_project_slugs(apps, schema_editor):
    """Populate slugs for existing Project instances"""
    Project = apps.get_model('editais', 'Project')
    
    for project in Project.objects.filter(slug__isnull=True):
        if project.name:
            base_slug = slugify(project.name)
            if not base_slug:
                base_slug = f"startup-{project.pk}"
            
            # Check if slug already exists
            slug = base_slug
            counter = 1
            while Project.objects.filter(slug=slug).exclude(pk=project.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
                if counter > 100:  # Safety limit
                    slug = f"{base_slug}-{int(time.time())}"
                    break
            
            project.slug = slug
            project.save(update_fields=['slug'])


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

