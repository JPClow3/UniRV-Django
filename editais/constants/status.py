"""
Status-related constants.
"""

__all__ = [
    'ACTIVE_STARTUP_STATUSES',
    'EVALUATION_STARTUP_STATUSES',
    'DRAFT_STATUSES',
    'OPEN_EDITAL_STATUSES',
    'HTML_FIELDS',
    'SECONDS_PER_HOUR',
    'SECONDS_PER_DAY',
]

# Status de Startups (fases ativas: Ideação, MVP, Escala)
ACTIVE_STARTUP_STATUSES = ['pre_incubacao', 'incubacao', 'graduada']
EVALUATION_STARTUP_STATUSES = ['pre_incubacao', 'incubacao']

# Status de Editais
DRAFT_STATUSES = ['draft', 'programado']
OPEN_EDITAL_STATUSES = ['aberto', 'em_andamento']

# Campos HTML que precisam de sanitização
HTML_FIELDS = [
    'analise', 'objetivo', 'etapas', 'recursos',
    'itens_financiaveis', 'criterios_elegibilidade',
    'criterios_avaliacao', 'itens_essenciais_observacoes',
    'detalhes_unirv'
]

# Time constants (in seconds)
SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 86400  # 24 hours in seconds

