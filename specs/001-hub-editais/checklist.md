# Implementation Checklist: Hub de Editais

**Feature**: 001-hub-editais  
**Created**: 2025-11-11  
**Status**: Pronto para Implementação  
**Reference**: [spec.md](./spec.md), [plan.md](./plan.md), [analysis.md](./analysis.md)

**Note**: Este checklist é gerado pelo comando `/speckit.checklist` baseado nos requisitos da especificação, plano de implementação e análise. Marque os itens como concluídos usando `[x]` e adicione comentários quando necessário.

---

## 📋 Pre-Implementation Checklist

### Documentação e Planejamento

- [ ] CHK001: Especificação completa e revisada (spec.md)
- [ ] CHK002: Todas as clarificações resolvidas (15/15)
- [ ] CHK003: Plano de implementação criado (plan.md)
- [ ] CHK004: Análise de gaps realizada (analysis.md)
- [ ] CHK005: Inconsistências críticas corrigidas (ISSUE-001, ISSUE-002)
- [ ] CHK006: Dependências identificadas e resolvidas
- [ ] CHK007: Riscos identificados e mitigados

---

## 🗄️ Phase 2.1: Database Migrations

### Migrations de Campos

- [ ] CHK008: Migration criada para adicionar campo `slug` (SlugField, unique=True, max_length=255)
- [ ] CHK009: Migration criada para adicionar campo `start_date` (DateField, blank=True, null=True)
- [ ] CHK010: Migration criada para adicionar campo `end_date` (DateField, blank=True, null=True)
- [ ] CHK011: Migration criada para adicionar status 'draft' aos STATUS_CHOICES
- [ ] CHK012: Migration criada para adicionar status 'programado' aos STATUS_CHOICES
- [ ] CHK013: Migration criada para adicionar índice em `slug`
- [ ] CHK014: Migration criada para adicionar índice em `status, start_date, end_date`
- [ ] CHK015: Migration criada para adicionar índice em `titulo` (para busca)
- [ ] CHK016: Data migration criada para popular slugs existentes (se houver dados)
- [ ] CHK017: Migrations testadas em ambiente de desenvolvimento
- [ ] CHK018: Migrations revisadas para reversibilidade

---

## 🏗️ Phase 2.2: Model Updates

### Modelo Edital

- [ ] CHK019: Campo `slug` adicionado ao modelo Edital
- [ ] CHK020: Campos `start_date` e `end_date` adicionados ao modelo Edital
- [ ] CHK021: Status 'draft' e 'programado' adicionados aos STATUS_CHOICES
- [ ] CHK022: Método `_generate_unique_slug()` implementado
- [ ] CHK023: Método `save()` atualizado para gerar slug automaticamente (apenas se não existir)
- [ ] CHK024: Método `save()` atualizado para definir status 'programado' se start_date > hoje
- [ ] CHK025: Método `get_absolute_url()` atualizado para usar slug
- [ ] CHK026: Índices atualizados no Meta (slug, status_dates, titulo)
- [ ] CHK027: Validação de datas implementada (end_date > start_date) no método `clean()`
- [ ] CHK028: Slug não pode ser editado manualmente (readonly no admin)

### Modelos Existentes

- [ ] CHK029: Modelo Cronograma mantido sem alterações
- [ ] CHK030: Modelo EditalValor mantido sem alterações
- [ ] CHK031: Modelo EditalFavorite mantido no banco (não usado na interface)

---

## 🔗 Phase 2.3: URL Migration

### URLs Públicas

- [ ] CHK032: Rota `/editais/<slug>/` adicionada para detalhe público
- [ ] CHK033: Rota `/editais/<pk>/` mantida com redirecionamento 301 para slug
- [ ] CHK034: View de detalhe atualizada para suportar slug e PK
- [ ] CHK035: Redirecionamento 301 testado para URLs antigas

### URLs Administrativas

- [ ] CHK036: Django Admin configurado para usar slug nas URLs
- [ ] CHK037: URLs administrativas funcionando com slug

---

## 👁️ Phase 2.4: Views & Forms

### Views Públicas

- [ ] CHK038: View de listagem implementada com busca (FR-002)
- [ ] CHK039: View de listagem implementada com filtros de status (FR-003)
- [ ] CHK040: View de listagem implementada com filtros de data (FR-021)
- [ ] CHK041: View de listagem implementada com opção "somente abertos" (FR-021)
- [ ] CHK042: View de listagem implementada com paginação numérica (5 páginas visíveis) exibindo 12 itens por página (FR-012)
- [ ] CHK043: View de listagem garante `settings.EDITAIS_PER_PAGE = 12`
- [ ] CHK044: View de listagem implementada com cache (TTL: 5 minutos) (FR-025)
- [ ] CHK045: View de listagem filtra editais por status (não exibe 'draft' para não-autenticados) (FR-010)
- [ ] CHK046: View de detalhe implementada com suporte a slug e PK
- [ ] CHK047: View de detalhe exibe todos os campos do edital (FR-004)
- [ ] CHK048: View de detalhe exibe link externo (url) (FR-009)
- [ ] CHK049: View de detalhe exibe cronogramas relacionados
- [ ] CHK050: View de detalhe exibe valores relacionados (EditalValor)

### Exportação CSV

- [ ] CHK050A: View `export_editais_csv` restrita a usuários `is_staff` (FR-028)
- [ ] CHK050B: Exportação aplica filtros de busca/status equivalentes à listagem
- [ ] CHK050C: CSV inclui colunas Número, Título, Entidade, Status, URL, Datas, Criado/Atualizado Por
- [ ] CHK050D: CSV gerado com encoding UTF-8 e BOM (compatível com Excel)

### Views Administrativas

- [ ] CHK051: Sistema de permissões básico implementado (operações administrativas restritas a usuários `is_staff`) (FR-023)
- [ ] CHK052: View de criação implementada com verificação `request.user.is_staff` (FR-005)
- [ ] CHK053: View de edição implementada com verificação `request.user.is_staff` (FR-006)
- [ ] CHK054: View de exclusão implementada com verificação `request.user.is_staff` (FR-007)
- [ ] CHK055: View de exclusão implementada com confirmação modal (FR-007, FR-027)
- [ ] CHK056: Usuários `is_staff` podem ver editais em status 'draft' (FR-011)

### Busca e Filtros

- [ ] CHK057: Busca case-insensitive implementada (FR-020)
- [ ] CHK058: Busca em título, objetivo, análise, número do edital e entidade principal (FR-020)
- [ ] CHK059: Busca modo "contém" implementada (FR-020)
- [ ] CHK060: Busca executada apenas após submit do formulário (FR-020)
- [ ] CHK061: Filtros combinados com operador AND (FR-021)
- [ ] CHK062: Filtros persistidos na URL (query parameters) (FR-021)
- [ ] CHK063: Filtro de data aplicado a start_date e end_date (FR-021)

### Formulários

- [ ] CHK064: Formulário de criação implementado (Django Admin ou custom)
- [ ] CHK065: Formulário de edição implementado (Django Admin ou custom)
- [ ] CHK066: Validação de datas implementada (end_date > start_date) (FR-013)
- [ ] CHK067: Validação de slug implementada (único, gerado automaticamente) (FR-008)
- [ ] CHK068: Sanitização de HTML implementada (bleach) (FR-015)
- [ ] CHK069: Campos obrigatórios validados (título, status)

---

## 🎨 Phase 2.5: Templates

### Template de Listagem

- [ ] CHK070: Template `editais/list.html` criado
- [ ] CHK071: Search bar implementada no template
- [ ] CHK072: Filtros de status implementados no template
- [ ] CHK073: Filtros de data implementados no template
- [ ] CHK074: Opção "somente abertos" implementada no template
- [ ] CHK075: Cards com resumo implementados (título, organização, datas, status)
- [ ] CHK076: Aviso "prazo próximo" implementado para editais com prazo nos últimos 7 dias (FR-024)
- [ ] CHK077: Paginação numérica implementada (5 páginas visíveis, 12 itens por página)
- [ ] CHK078: Botão de exportação CSV exibido apenas para usuários `is_staff`
- [ ] CHK079: Mensagem "Nenhum edital encontrado" exibida quando não há resultados

### Template de Detalhe

- [ ] CHK080: Template `editais/detail.html` criado
- [ ] CHK081: Header com título e status implementado
- [ ] CHK082: Metadados exibidos (número, entidade, datas, status)
- [ ] CHK083: Objetivo formatado exibido
- [ ] CHK084: Critérios de elegibilidade exibidos
- [ ] CHK085: Cronogramas exibidos
- [ ] CHK086: Link externo (url) exibido
- [ ] CHK087: Aviso "prazo próximo" exibido se aplicável
- [ ] CHK088: Valores financeiros (EditalValor) exibidos

### Templates Administrativos

- [ ] CHK089: Django Admin customizado com mesmo layout visual do site (FR-026)
- [ ] CHK090: Preview de edital implementado no Django Admin (FR-026)
- [ ] CHK091: Template de confirmação de exclusão implementado (modal ou página)
- [ ] CHK092: Mensagens de sucesso/erro exibidas (toast notifications) (FR-027)

---

## 🔒 Phase 2.6: Permissions & Security

### Sistema de Permissões

- [ ] CHK093: Grupos Django criados (opcional para versões futuras)
- [ ] CHK094: Permissões padrão (add/change/delete) conferidas a usuários `is_staff`
- [ ] CHK095: Views administrativas protegidas com verificação `request.user.is_staff`
- [ ] CHK096: Visitantes não-autenticados não podem acessar editais 'draft' (FR-010)
- [ ] CHK097: Usuários `is_staff` podem ver editais 'draft' (FR-011)

### Segurança

- [ ] CHK100: CSRF habilitado para todas as operações de escrita
- [ ] CHK101: SECRET_KEY em variável de ambiente (.env)
- [ ] CHK102: Sanitização de HTML implementada (bleach) (FR-015)
- [ ] CHK103: Proteção contra SQL injection (usar Django ORM exclusivamente) (FR-020)
- [ ] CHK104: Validação de entrada implementada
- [ ] CHK105: Slug gerado automaticamente (previne caracteres perigosos) (FR-018)

---

## ⚡ Phase 2.7: Performance & Optimization

### Otimização de Queries

- [ ] CHK106: select_related implementado para created_by/updated_by (FR-025)
- [ ] CHK107: prefetch_related implementado para cronogramas (FR-025)
- [ ] CHK108: Índices criados para campos de busca (FR-025)
- [ ] CHK109: Queries otimizadas (minimizar número de queries por página)

### Cache

- [ ] CHK110: Cache habilitado para listagens públicas (TTL: 5 minutos) (FR-025)
- [ ] CHK111: Cache configurado (Redis, Memcached, ou database cache)
- [ ] CHK112: Cache testado e funcionando

### Performance

- [ ] CHK113: Lista de editais carrega em menos de 2 segundos (100+ editais) (SC-002)
- [ ] CHK114: Paginação implementada corretamente
- [ ] CHK115: Busca otimizada (índices, cache)

---

## 🔄 Phase 2.8: Management Commands

### Commands

- [ ] CHK116: Management command `update_edital_status.py` criado
- [ ] CHK117: Command atualiza status 'fechado' se end_date < hoje e status='aberto' (FR-024)
- [ ] CHK118: Command atualiza status 'programado' se start_date > hoje (FR-024)
- [ ] CHK119: Command testado manualmente
- [ ] CHK120: Command documentado (como executar, como agendar)
- [ ] CHK121: Cron/task scheduler configurado para executar command diariamente

---

## 🧪 Phase 2.9: Testing

### Testes Unitários

- [ ] CHK122: Testes para modelo Edital criados
- [ ] CHK123: Testes para geração de slug criados (unicidade, sufixo numérico)
- [ ] CHK124: Testes para validação de datas criados
- [ ] CHK125: Testes para status automático criados
- [ ] CHK126: Testes para views públicas criados
- [ ] CHK127: Testes para views administrativas criados
- [ ] CHK128: Testes para formulários criados
- [ ] CHK129: Testes para permissões criados
- [ ] CHK130: Testes para sanitização de HTML criados

### Testes de Integração

- [ ] CHK131: Testes de integração para fluxo completo de criação de edital
- [ ] CHK132: Testes de integração para fluxo completo de edição de edital
- [ ] CHK133: Testes de integração para fluxo completo de exclusão de edital
- [ ] CHK134: Testes de integração para busca e filtros
- [ ] CHK135: Testes de integração para paginação
- [ ] CHK136: Testes de integração para redirecionamento de URLs (PK → slug)

### Cobertura de Testes

- [ ] CHK137: Cobertura de testes alcança mínimo de 85% (SC-005)
- [ ] CHK138: Testes executados e todos passando
- [ ] CHK139: Testes documentados

---

## 🌐 Phase 2.10: Localization & Internationalization

### Localização

- [ ] CHK140: LANGUAGE_CODE configurado como 'pt-br' (FR-016)
- [ ] CHK141: TIME_ZONE configurado como 'America/Sao_Paulo' (FR-017)
- [ ] CHK142: Todos os templates em português brasileiro (FR-016, SC-009)
- [ ] CHK143: Todas as mensagens em português brasileiro (FR-016, SC-009)
- [ ] CHK144: Formatos de data seguindo padrões brasileiros (FR-016)
- [ ] CHK145: Formatos de número seguindo padrões brasileiros (FR-016)
- [ ] CHK146: Todos os campos e rótulos em português (FR-016, FR-019)

---

## 🚀 Phase 2.11: Production Readiness

### Configuração de Produção

- [ ] CHK147: DEBUG=False configurado para produção (SC-010)
- [ ] CHK148: ALLOWED_HOSTS configurado corretamente (SC-010)
- [ ] CHK149: SECRET_KEY seguro e único (SC-010)
- [ ] CHK150: WhiteNoise configurado para static files (SC-010)
- [ ] CHK151: Gunicorn configurado como WSGI server
- [ ] CHK152: Nginx configurado como reverse proxy (documentado)
- [ ] CHK153: HTTPS habilitado
- [ ] CHK154: Backup de banco de dados configurado
- [ ] CHK155: Logging configurado para produção

### Qualidade de Código

- [ ] CHK156: Código segue PEP 8
- [ ] CHK157: Linting executado (flake8, black)
- [ ] CHK158: Type hints adicionados onde apropriado (mypy)
- [ ] CHK159: Docstrings adicionadas a funções principais
- [ ] CHK160: Código revisado (code review)

### Documentação

- [ ] CHK161: README.md atualizado com novas funcionalidades
- [ ] CHK162: Documentação de sistema de permissões criada
- [ ] CHK163: Documentação de management commands criada
- [ ] CHK164: Documentação de cache criada
- [ ] CHK165: Documentação de deploy criada

---

## ✅ Success Criteria Verification

### Critérios de Sucesso

- [ ] CHK166: SC-001: Visitantes conseguem encontrar editais em menos de 3 cliques (testado)
- [ ] CHK167: SC-002: Lista de editais carrega em menos de 2 segundos (100+ editais) (testado)
- [ ] CHK168: SC-003: Administradores conseguem criar edital em menos de 5 minutos (testado)
- [ ] CHK169: SC-004: 100% dos editais criados são válidos (testado)
- [ ] CHK170: SC-005: Cobertura de testes alcança 85% (verificado)
- [ ] CHK171: SC-006: Sistema previne SQL injection e XSS (testado)
- [ ] CHK172: SC-007: Slugs únicos gerados com 100% de precisão (testado)
- [ ] CHK173: SC-008: Interface administrativa funciona sem erros (testado)
- [ ] CHK174: SC-009: Todos os templates e mensagens em pt-BR (verificado)
- [ ] CHK175: SC-010: Sistema pronto para produção (verificado)

---

## 🔧 Cleanup & Maintenance

### Remoção de Funcionalidades

- [ ] CHK176: Funcionalidade de favoritos removida das views (GAP-006)
- [ ] CHK177: URLs de favoritos removidas (GAP-006)
- [ ] CHK178: Referências a favoritos removidas dos templates (GAP-006)
- [ ] CHK179: Modelo EditalFavorite mantido no banco (não deletado) (GAP-006)
- [ ] CHK180: Nota adicionada no código indicando que favoritos foram removidos do MVP

### Funcionalidades Futuras

- [ ] CHK181: Upload de anexos marcado como "futura fase" (não implementado)
- [ ] CHK182: Sistema de "salvar" marcado como "futura fase" (não implementado)
- [ ] CHK183: Campo de localização marcado como "futura fase" (não implementado)
- [ ] CHK184: API REST marcada como "futura fase" (não implementado)

---

## 📊 Final Verification

### Checklist Final

- [ ] CHK185: Todos os requisitos funcionais implementados (FR-001 a FR-027)
- [ ] CHK186: Todos os critérios de sucesso atendidos (SC-001 a SC-010)
- [ ] CHK187: Todas as fases do plano de implementação concluídas (Phase 2.1 a 2.11)
- [ ] CHK188: Todos os gaps identificados na análise resolvidos (GAP-001 a GAP-012)
- [ ] CHK189: Conformidade com Constituição verificada
- [ ] CHK190: Análise de riscos atualizada
- [ ] CHK191: Documentação completa e atualizada
- [ ] CHK192: Sistema testado em ambiente de staging
- [ ] CHK193: Sistema pronto para deploy em produção

---

## 📝 Notes

### Comentários e Observações

- Adicione comentários sobre decisões tomadas durante a implementação
- Documente problemas encontrados e soluções aplicadas
- Registre alterações em relação ao plano original
- Anote melhorias futuras ou otimizações identificadas

### Referências

- **Spec**: [spec.md](./spec.md)
- **Plan**: [plan.md](./plan.md)
- **Analysis**: [analysis.md](./analysis.md)
- **Clarifications**: [clarifications.md](./clarifications.md)
- **Constitution**: [.specify/memory/constitution.md](../../.specify/memory/constitution.md)

### Status do Checklist

**Total de Itens**: 193  
**Concluídos**: 0  
**Pendentes**: 193  
**Progresso**: 0%

**Última Atualização**: 2025-11-11

---

## 🎯 Próximos Passos Após Conclusão

1. Revisar checklist completo
2. Executar testes finais
3. Revisar código (code review)
4. Atualizar documentação
5. Deploy em produção
6. Monitorar sistema após deploy

---

**Nota**: Este checklist deve ser atualizado à medida que a implementação progride. Marque os itens como concluídos usando `[x]` e adicione comentários quando necessário para documentar decisões ou problemas encontrados.
