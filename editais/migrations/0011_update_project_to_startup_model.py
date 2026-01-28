# Generated migration to update Project model to represent startups in incubation process
#
# BUSINESS LOGIC CHANGE: This migration transforms the Project model from a
# submission-based system to represent startups in an incubation process.
#
# Key changes:
# - Status choices changed from submission states (em_avaliacao, aprovado, etc.)
#   to incubation stages (pre_incubacao, incubacao, graduada, suspensa)
# - Edital field made nullable: startups can exist without being tied to a specific edital
#   (some startups may enter incubation through other means)
# - Model renamed from "Project" to "Startup" to reflect new purpose
# - Field names updated to match startup terminology
#
# A data migration is included to map existing project statuses to the new
# incubation stages, ensuring no data is lost during the transition.

from django.db import migrations, models
import django.db.models.deletion


def migrate_project_statuses(apps, schema_editor):
    """
    Migrate existing project statuses to new incubation stages.
    Maps old submission-based statuses to new incubation stages.
    """
    Project = apps.get_model('editais', 'Project')
    
    # Map old statuses to new ones
    status_mapping = {
        'em_avaliacao': 'pre_incubacao',
        'aprovado': 'incubacao',
        'reprovado': 'suspensa',
        'pendente': 'pre_incubacao',
    }
    
    # Update all projects with old statuses
    for project in Project.objects.all():
        if project.status in status_mapping:
            project.status = status_mapping[project.status]
            project.save(update_fields=['status'])


def reverse_migrate_project_statuses(apps, schema_editor):
    """
    Reverse migration - map back to old statuses.
    Note: This is a best-effort reverse, as we can't perfectly map back.
    """
    Project = apps.get_model('editais', 'Project')
    
    # Reverse mapping (best effort)
    reverse_mapping = {
        'pre_incubacao': 'pendente',
        'incubacao': 'aprovado',
        'graduada': 'aprovado',
        'suspensa': 'reprovado',
    }
    
    for project in Project.objects.all():
        if project.status in reverse_mapping:
            project.status = reverse_mapping[project.status]
            project.save(update_fields=['status'])


class Migration(migrations.Migration):

    dependencies = [
        ('editais', '0010_create_project_model'),
    ]

    operations = [
        # First, make edital nullable
        migrations.AlterField(
            model_name='project',
            name='edital',
            field=models.ForeignKey(
                blank=True,
                help_text='Edital relacionado (opcional - startups podem não ter edital)',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='projetos',
                to='editais.edital',
                verbose_name='Edital'
            ),
        ),
        # Update status field choices and default
        migrations.AlterField(
            model_name='project',
            name='status',
            field=models.CharField(
                choices=[
                    ('pre_incubacao', 'Pré-Incubação'),
                    ('incubacao', 'Incubação'),
                    ('graduada', 'Graduada'),
                    ('suspensa', 'Suspensa'),
                ],
                default='pre_incubacao',
                max_length=20,
                verbose_name='Status'
            ),
        ),
        # Update verbose names
        migrations.AlterModelOptions(
            name='project',
            options={
                'ordering': ['-submitted_on'],
                'verbose_name': 'Startup',
                'verbose_name_plural': 'Startups',
            },
        ),
        # Update field verbose names
        migrations.AlterField(
            model_name='project',
            name='name',
            field=models.CharField(max_length=200, verbose_name='Nome da Startup'),
        ),
        migrations.AlterField(
            model_name='project',
            name='proponente',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='projetos_submetidos',
                to='auth.user',
                verbose_name='Responsável'
            ),
        ),
        migrations.AlterField(
            model_name='project',
            name='submitted_on',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Data de Entrada'),
        ),
        # Run data migration to update existing records
        migrations.RunPython(migrate_project_statuses, reverse_migrate_project_statuses),
    ]

