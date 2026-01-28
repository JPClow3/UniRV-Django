# Generated manually to add new fields to Startup model
# Date: 2026-01-27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('editais', '0028_rename_project_to_startup'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Nome da tag (ex: "AgTech", "Inovação", "Sustentabilidade")', max_length=50, unique=True, verbose_name='Nome')),
                ('slug', models.SlugField(blank=True, editable=False, max_length=50, null=True, unique=True, verbose_name='Slug')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')),
            ],
            options={
                'verbose_name': 'Tag',
                'verbose_name_plural': 'Tags',
                'ordering': ['name'],
            },
        ),
        migrations.AddIndex(
            model_name='tag',
            index=models.Index(fields=['name'], name='idx_tag_name'),
        ),
        migrations.AddIndex(
            model_name='tag',
            index=models.Index(fields=['slug'], name='idx_tag_slug'),
        ),
        migrations.AddField(
            model_name='startup',
            name='website',
            field=models.URLField(blank=True, help_text='Website da startup (ex: https://www.exemplo.com)', null=True, verbose_name='Website'),
        ),
        migrations.AddField(
            model_name='startup',
            name='incubacao_start_date',
            field=models.DateField(blank=True, help_text='Data em que a startup iniciou o processo de incubação', null=True, verbose_name='Data de Início da Incubação'),
        ),
        migrations.AddField(
            model_name='startup',
            name='tags',
            field=models.ManyToManyField(blank=True, help_text='Tags para categorização da startup', to='editais.tag', verbose_name='Tags'),
        ),
    ]
