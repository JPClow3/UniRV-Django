"""
Constantes do aplicativo Editais.

Este módulo contém todas as constantes reutilizáveis do aplicativo,
evitando valores mágicos espalhados pelo código.
"""

# Busca
SEARCH_MIN_LENGTH = 3
SEARCH_DEBOUNCE_MS = 500

# Prazos e alertas
DEADLINE_WARNING_DAYS = 7

# Paginação
PAGINATION_DEFAULT = 12

# Cache
CACHE_TTL_INDEX = 300  # 5 minutos em segundos
CACHE_TTL_DETAIL = 3600  # 1 hora em segundos

# Rate Limiting
RATE_LIMIT_REQUESTS = 5  # Número de requisições permitidas
RATE_LIMIT_WINDOW = 60  # Janela de tempo em segundos (1 minuto)

# Cores de status para uso em templates/frontend
STATUS_COLORS = {
    'aberto': '#28a745',
    'fechado': '#dc3545',
    'em_andamento': '#ffc107',
    'draft': '#6c757d',
    'programado': '#007bff',
}

