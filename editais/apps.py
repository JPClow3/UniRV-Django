from django.apps import AppConfig


class EditaisConfig(AppConfig):
    """App configuration for the 'editais' application.

    - default_auto_field ensures BigAutoField IDs by default (Django 3.2+).
    - verbose_name is shown in the Django admin site and elsewhere.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "editais"
    verbose_name = "Editais de Fomento"

