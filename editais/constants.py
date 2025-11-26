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

