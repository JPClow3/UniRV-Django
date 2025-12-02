#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import shutil


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'UniRV_Django.settings')
    try:
        from django.core.management import execute_from_command_line
        
        # Interceptar comando collectstatic para limpar antes de coletar
        if len(sys.argv) > 1 and sys.argv[1] == 'collectstatic':
            from django.conf import settings
            
            # Limpar staticfiles antes de coletar
            staticfiles_dir = settings.STATIC_ROOT
            if staticfiles_dir and os.path.exists(staticfiles_dir):
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Limpando diretorio {staticfiles_dir}...")
                try:
                    shutil.rmtree(str(staticfiles_dir))
                    logger.info(f"Diretorio limpo com sucesso")
                except Exception as e:
                    logger.warning(f"Nao foi possivel limpar {staticfiles_dir}: {e}")
                    logger.warning("Continuando com collectstatic mesmo assim...")
        
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
