"""
Constantes do aplicativo Editais.

Este módulo contém todas as constantes reutilizáveis do aplicativo,
evitando valores mágicos espalhados pelo código.
"""

# Prazos e alertas
DEADLINE_WARNING_DAYS = 7

# Paginação
PAGINATION_DEFAULT = 12

# Cache
CACHE_TTL_INDEX = 300  # 5 minutos em segundos

# Rate Limiting
RATE_LIMIT_REQUESTS = 5  # Número de requisições permitidas
RATE_LIMIT_WINDOW = 60  # Janela de tempo em segundos (1 minuto)

# Campos HTML que precisam de sanitização
HTML_FIELDS = [
    'analise', 'objetivo', 'etapas', 'recursos',
    'itens_financiaveis', 'criterios_elegibilidade',
    'criterios_avaliacao', 'itens_essenciais_observacoes',
    'detalhes_unirv'
]

# Status de Projetos (Startups)
ACTIVE_PROJECT_STATUSES = ['pre_incubacao', 'incubacao', 'graduada']
EVALUATION_PROJECT_STATUSES = ['pre_incubacao', 'incubacao']

# Status de Editais
DRAFT_STATUSES = ['draft', 'programado']
OPEN_EDITAL_STATUSES = ['aberto', 'em_andamento']

# Cache TTLs (Time To Live in seconds)
CACHE_TTL_5_MINUTES = 300  # 5 minutos em segundos
CACHE_TTL_15_MINUTES = 900  # 15 minutos em segundos

# Time constants (in seconds)
SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 86400  # 24 hours in seconds

# Retry and limits
SLUG_GENERATION_MAX_RETRIES = 3
CACHE_FALLBACK_PAGE_RANGE = 10  # Number of pages to clear in cache fallback

