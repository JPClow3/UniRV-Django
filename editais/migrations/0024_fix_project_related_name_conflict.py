# Generated manually to fix related_name conflict
# Date: 2026-01-27
#
# CRITICAL FIX: Resolves related_name conflict introduced in migration 0015
#
# PROBLEM:
# Migration 0015 changed both ForeignKey fields to use 'startups' as related_name:
#   - project.edital.related_name = 'startups'
#   - project.proponente.related_name = 'startups'
#
# This created a conflict because Django's reverse relationship system cannot have
# two ForeignKeys on the same model pointing to different models (Edital and User)
# with the same related_name. This would cause:
#   - SystemCheckError when running 'python manage.py check'
#   - Runtime errors when accessing reverse relations
#   - Ambiguity: edital.startups vs user.startups
#
# SOLUTION:
# Change proponente.related_name from 'startups' to 'startups_owned' to:
#   - Resolve the conflict (edital.startups remains for Edital model)
#   - Provide semantic clarity: 'startups_owned' indicates ownership/responsibility
#   - Maintain consistency: edital.startups (startups related to an edital)
#                          user.startups_owned (startups owned by a user)
#
# The 'startups_owned' name was chosen because:
#   - It clearly indicates the relationship (user owns/manages these startups)
#   - It's distinct from 'startups' (which represents edital-related startups)
#   - It follows Django naming conventions for related names

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('editais', '0023_change_logo_to_filefield'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Fix related_name conflict by changing proponente.related_name to 'startups_owned'
        # This resolves the conflict with edital.related_name='startups' from migration 0015
        migrations.AlterField(
            model_name='project',
            name='proponente',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='startups_owned',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Responsável'
            ),
        ),
    ]
