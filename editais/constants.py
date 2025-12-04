"""
Constantes do aplicativo Editais.

Este módulo mantém compatibilidade com código existente.
As constantes foram reorganizadas em sub-módulos (constants/cache.py, constants/limits.py, constants/status.py)
mas são re-exportadas aqui para manter compatibilidade.
"""

# Re-export all constants from sub-modules for backward compatibility
from .constants.cache import *
from .constants.limits import *
from .constants.status import *

