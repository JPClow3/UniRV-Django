"""
Status-related constants.
"""

# Status de Projetos (Startups)
ACTIVE_PROJECT_STATUSES = ['pre_incubacao', 'incubacao', 'graduada']
EVALUATION_PROJECT_STATUSES = ['pre_incubacao', 'incubacao']

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

