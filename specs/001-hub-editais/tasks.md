# Tasks: Hub de Editais

**Feature**: 001-hub-editais  
**Input**: [spec.md](./spec.md), [plan.md](./plan.md), [analysis.md](./analysis.md)  
**Created**: 2025-11-11  
**Status**: Pronto para Implementação

**Prerequisites**: 
- plan.md (required) ✅
- spec.md (required for user stories) ✅
- analysis.md (required for gaps) ✅

**Tests**: Testes são OBRIGATÓRIOS - cobertura mínima de 85% (conforme Constituição e spec.md)

**Organization**: Tarefas organizadas por user story para permitir implementação e testes independentes de cada story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode ser executada em paralelo (arquivos diferentes, sem dependências)
- **[Story]**: Qual user story esta tarefa pertence (ex: US1, US2, US3)
- Incluir caminhos de arquivo exatos nas descrições

## Path Conventions

- **Django Project**: `editais/` (app Django)
- **Models**: `editais/models.py`
- **Views**: `editais/views.py`
- **Templates**: `templates/editais/`
- **Tests**: `editais/tests.py`
- **URLs**: `editais/urls.py`
- **Forms**: `editais/forms.py`
- **Admin**: `editais/admin.py`
- **Management Commands**: `editais/management/commands/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verificação de pré-requisitos e estrutura básica

- [ ] T001 Verificar estrutura do projeto Django existente
- [ ] T002 Verificar dependências instaladas (Django >= 5.2.7, bleach, WhiteNoise)
- [ ] T003 [P] Configurar linting e formatação (flake8, black) se não estiver configurado
- [ ] T004 Verificar configuração de settings.py (LANGUAGE_CODE, TIME_ZONE, etc.)
- [ ] T005 Verificar app 'editais' registrado no INSTALLED_APPS

**Checkpoint**: Estrutura do projeto verificada e pronta para implementação

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Infraestrutura core que DEVE estar completa antes de QUALQUER user story poder ser implementada

**⚠️ CRITICAL**: Nenhuma user story pode começar até que esta fase esteja completa

### 2.1: Database Migrations

- [ ] T006 Criar migration para adicionar campo `slug` ao modelo Edital em `editais/migrations/0005_add_slug_to_edital.py`
  - Campo: `SlugField(unique=True, max_length=255, blank=True)`
  - Permitir null temporariamente para migração de dados existentes
- [ ] T007 Criar migration para adicionar campos `start_date` e `end_date` em `editais/migrations/0006_add_dates_to_edital.py`
  - Campos: `DateField(blank=True, null=True)`
- [ ] T008 Criar migration para adicionar status 'draft' e 'programado' em `editais/migrations/0007_add_status_choices.py`
  - Adicionar 'draft' (Rascunho) e 'programado' (Programado) aos STATUS_CHOICES
- [ ] T009 Criar migration para adicionar índices em `editais/migrations/0008_add_indexes.py`
  - Índice em `slug`
  - Índice composto em `status, start_date, end_date`
  - Índice em `titulo` (para busca)
- [ ] T010 Criar data migration para popular slugs existentes em `editais/migrations/0009_populate_slugs.py`
  - Usar `slugify()` para gerar slugs a partir de títulos
  - Garantir unicidade (adicionar sufixo numérico se necessário)
  - Atualizar campo `slug` para não permitir null após população
- [ ] T011 Testar migrations em ambiente de desenvolvimento
- [ ] T012 Verificar reversibilidade das migrations

### 2.2: Model Updates

- [ ] T013 Atualizar modelo Edital em `editais/models.py`
  - Adicionar campo `slug = models.SlugField(unique=True, max_length=255)`
  - Adicionar campos `start_date` e `end_date`
  - Adicionar status 'draft' e 'programado' aos STATUS_CHOICES
  - Implementar método `_generate_unique_slug()`
  - Atualizar método `save()` para gerar slug automaticamente (apenas se não existir)
  - Atualizar método `save()` para definir status 'programado' se start_date > hoje
  - Implementar método `clean()` para validar datas (end_date > start_date)
  - Atualizar `get_absolute_url()` para usar slug
  - Atualizar índices no Meta
- [ ] T014 Verificar que modelos existentes (Cronograma, EditalValor) estão mantidos
- [ ] T015 Verificar que modelo EditalFavorite está mantido no banco (não usado na interface)

### 2.3: URL Structure

- [ ] T016 Atualizar URLs públicas em `editais/urls.py`
  - Adicionar rota `/editais/<slug>/` para detalhe público
  - Manter rota `/editais/<pk>/` com redirecionamento 301 para slug
- [ ] T017 Atualizar view de detalhe para suportar slug e PK em `editais/views.py`
  - Implementar lógica para buscar por slug ou PK
  - Implementar redirecionamento 301 de PK para slug

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Visualizar Lista de Editais com Busca (Priority: P1) 🎯 MVP

**Goal**: Visitantes podem ver lista de editais com busca e filtros

**Independent Test**: Acessar `/editais/` e verificar que lista paginada é exibida. Testar busca por título/organização e filtros por status.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T018 [P] [US1] Teste unitário para view de listagem em `editais/tests/test_views.py`
  - Testar que lista de editais é exibida
  - Testar que apenas editais publicados são exibidos (não 'draft')
  - Testar paginação
- [ ] T019 [P] [US1] Teste de integração para busca em `editais/tests/test_search.py`
  - Testar busca case-insensitive
  - Testar busca em múltiplos campos (título, organização, etc.)
  - Testar busca modo "contém"
- [ ] T020 [P] [US1] Teste de integração para filtros em `editais/tests/test_filters.py`
  - Testar filtro de status
  - Testar filtro de datas
  - Testar opção "somente abertos"
  - Testar combinação de filtros (AND)

### Implementation for User Story 1

- [ ] T021 [US1] Implementar view de listagem em `editais/views.py`
  - Filtrar editais por status (não exibir 'draft' para não-autenticados)
  - Implementar busca case-insensitive (título, objetivo, análise, número, entidade)
  - Implementar filtros (status, datas, "somente abertos")
  - Implementar paginação numérica (5 páginas visíveis)
  - Implementar opção para alterar itens por página (20, 50, 100)
  - Persistir filtros na URL (query parameters)
  - Otimizar queries com select_related e prefetch_related
- [ ] T022 [US1] Criar template de listagem em `templates/editais/list.html`
  - Search bar
  - Filtros (status, datas, "somente abertos")
  - Cards com resumo (título, organização, datas, status)
  - Aviso "prazo próximo" para editais com prazo nos últimos 7 dias
  - Paginação numérica (5 páginas visíveis)
  - Opção para alterar itens por página
  - Mensagem "Nenhum edital encontrado" quando não há resultados
- [ ] T023 [US1] Implementar helper function para busca em `editais/views.py`
  - Função `build_search_query()` para construir Q object
  - Buscar em: título, objetivo, análise, número do edital, entidade principal
  - Modo "contém" (icontains)
- [ ] T024 [US1] Implementar helper function para filtros em `editais/views.py`
  - Função para aplicar filtros de status
  - Função para aplicar filtros de data
  - Função para aplicar opção "somente abertos"
  - Combinar filtros com operador AND
- [ ] T025 [US1] Implementar cache para listagens públicas em `editais/views.py`
  - Cache com TTL de 5 minutos
  - Invalidar cache quando editais são criados/editados/deletados

**Checkpoint**: User Story 1 deve estar totalmente funcional e testável independentemente

---

## Phase 4: User Story 2 - Visualizar Detalhes de um Edital (Priority: P1) 🎯 MVP

**Goal**: Visitantes podem ver detalhes completos de um edital

**Independent Test**: Acessar `/editais/<slug>/` e verificar que todos os campos são exibidos, incluindo objetivo, critérios de elegibilidade, prazos, cronogramas e link externo.

### Tests for User Story 2 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T026 [P] [US2] Teste unitário para view de detalhe em `editais/tests/test_views.py`
  - Testar que detalhes do edital são exibidos
  - Testar que editais 'draft' retornam 404 para não-autenticados
  - Testar que editais publicados são exibidos para todos
- [ ] T027 [P] [US2] Teste de integração para redirecionamento PK → slug em `editais/tests/test_urls.py`
  - Testar redirecionamento 301 de `/editais/<pk>/` para `/editais/<slug>/`
  - Testar que slug inválido retorna 404
- [ ] T028 [P] [US2] Teste de integração para exibição de campos em `editais/tests/test_detail.py`
  - Testar que todos os campos são exibidos
  - Testar que cronogramas são exibidos
  - Testar que link externo é exibido

### Implementation for User Story 2

- [ ] T029 [US2] Atualizar view de detalhe em `editais/views.py`
  - Suportar busca por slug ou PK
  - Filtrar editais 'draft' para não-autenticados (retornar 404)
  - Otimizar queries com select_related e prefetch_related
  - Sanitizar campos HTML antes de exibir
- [ ] T030 [US2] Criar template de detalhe em `templates/editais/detail.html`
  - Header com título e status
  - Metadados (número, entidade, datas, status)
  - Objetivo formatado
  - Critérios de elegibilidade
  - Cronogramas exibidos
  - Link externo (url)
  - Aviso "prazo próximo" se aplicável
  - Valores financeiros (EditalValor) exibidos
- [ ] T031 [US2] Implementar redirecionamento 301 de PK para slug em `editais/views.py`
  - Se acessado por PK, redirecionar para URL com slug
  - Manter compatibilidade durante período de transição

**Checkpoint**: User Story 2 deve estar totalmente funcional e testável independentemente

---

## Phase 5: User Story 3 - Criar Novo Edital (Priority: P2)

**Goal**: Administradores podem criar novos editais através da interface administrativa

**Independent Test**: Fazer login como staff/admin, acessar interface de criação, preencher campos obrigatórios e verificar que edital é criado com slug gerado automaticamente.

### Tests for User Story 3 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T032 [P] [US3] Teste unitário para criação de edital em `editais/tests/test_models.py`
  - Testar geração automática de slug
  - Testar unicidade de slug (adicionar sufixo se duplicado)
  - Testar status 'programado' se start_date > hoje
  - Testar validação de datas (end_date > start_date)
- [ ] T033 [P] [US3] Teste de integração para formulário de criação em `editais/tests/test_forms.py`
  - Testar validação de campos obrigatórios
  - Testar validação de datas
  - Testar sanitização de HTML
- [ ] T034 [P] [US3] Teste de integração para permissões em `editais/tests/test_permissions.py`
  - Testar que usuários sem permissão não podem criar editais
  - Testar que usuários com permissão podem criar editais

### Implementation for User Story 3

- [ ] T035 [US3] Implementar sistema de permissões em `editais/admin.py`
  - Criar grupos Django (staff, editor, admin)
  - Definir permissões (add_edital, change_edital, delete_edital)
  - Atribuir permissões a grupos
- [ ] T036 [US3] Customizar Django Admin para criação de edital em `editais/admin.py`
  - Configurar EditalAdmin com campos apropriados
  - Implementar método `save_model()` para gerar slug automaticamente
  - Implementar validação de datas
  - Sanitizar HTML em campos de texto
  - Adicionar preview antes de publicar
- [ ] T037 [US3] Implementar formulário de criação em `editais/forms.py`
  - Validação de campos obrigatórios (título, status)
  - Validação de datas (end_date > start_date)
  - Sanitização de HTML (bleach)
  - Campo slug readonly (não editável)
- [ ] T038 [US3] Implementar método `_generate_unique_slug()` no modelo Edital
  - Gerar slug a partir do título usando slugify
  - Remover acentos
  - Adicionar sufixo numérico se duplicado (-2, -3, etc.)
  - Garantir unicidade
- [ ] T039 [US3] Implementar lógica de status automático no método `save()`
  - Definir status 'programado' se start_date > hoje
  - Manter status existente se não for 'aberto'

**Checkpoint**: User Story 3 deve estar totalmente funcional e testável independentemente

---

## Phase 6: User Story 4 - Editar e Gerenciar Editais (Priority: P2)

**Goal**: Administradores podem editar e deletar editais existentes

**Independent Test**: Fazer login como staff/admin, acessar edição de edital, modificar campos e verificar que alterações são salvas. Testar exclusão com confirmação.

### Tests for User Story 4 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T040 [P] [US4] Teste unitário para edição de edital em `editais/tests/test_models.py`
  - Testar que slug não muda quando título é alterado
  - Testar validação de datas na edição
  - Testar que status 'draft' oculta edital da lista pública
- [ ] T041 [P] [US4] Teste de integração para formulário de edição em `editais/tests/test_forms.py`
  - Testar validação de campos
  - Testar sanitização de HTML
  - Testar que slug não pode ser editado
- [ ] T042 [P] [US4] Teste de integração para exclusão em `editais/tests/test_admin.py`
  - Testar que confirmação é exibida antes de deletar
  - Testar que usuários sem permissão não podem deletar

### Implementation for User Story 4

- [ ] T043 [US4] Customizar Django Admin para edição de edital em `editais/admin.py`
  - Configurar campos editáveis
  - Implementar validação de datas
  - Sanitizar HTML em campos de texto
  - Campo slug readonly (não editável)
  - Adicionar preview antes de publicar
- [ ] T044 [US4] Implementar formulário de edição em `editais/forms.py`
  - Validação de campos
  - Validação de datas (end_date > start_date)
  - Sanitização de HTML (bleach)
  - Campo slug readonly
- [ ] T045 [US4] Implementar confirmação de exclusão em `editais/admin.py`
  - Adicionar ação de exclusão com confirmação modal
  - Mensagem "Tem certeza que deseja deletar este edital?"
- [ ] T046 [US4] Implementar sistema de mensagens toast em `templates/admin/base_site.html`
  - Mensagens de sucesso após operações CRUD
  - Mensagens de erro no canto inferior direito
  - Mensagens temporárias (desaparecem após 5 segundos)
- [ ] T047 [US4] Atualizar view de listagem para ocultar editais 'draft' de não-autenticados
  - Filtrar editais por status na view pública
  - Permitir que usuários com permissão CRUD vejam editais 'draft'

**Checkpoint**: User Story 4 deve estar totalmente funcional e testável independentemente

---

## Phase 7: User Story 5 - Filtrar e Paginar Editais na Interface Administrativa (Priority: P3)

**Goal**: Administradores podem filtrar e paginar lista de editais na interface administrativa

**Independent Test**: Fazer login como staff/admin, acessar lista administrativa, testar filtros e paginação.

### Tests for User Story 5 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T048 [P] [US5] Teste de integração para filtros administrativos em `editais/tests/test_admin.py`
  - Testar filtros de status
  - Testar filtros de data
  - Testar busca por título/organização
- [ ] T049 [P] [US5] Teste de integração para paginação administrativa em `editais/tests/test_admin.py`
  - Testar paginação quando há muitos editais
  - Testar navegação entre páginas

### Implementation for User Story 5

- [ ] T050 [US5] Customizar Django Admin list view em `editais/admin.py`
  - Adicionar filtros (status, data, organização)
  - Adicionar busca por título/organização
  - Configurar paginação
  - Adicionar campos exibidos na lista
- [ ] T051 [US5] Customizar layout visual do Django Admin em `templates/admin/base_site.html`
  - Mesmo layout visual do site
  - Estilos consistentes

**Checkpoint**: User Story 5 deve estar totalmente funcional e testável independentemente

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Melhorias que afetam múltiplas user stories

### 8.1: Management Commands

- [ ] T052 Criar management command `update_edital_status.py` em `editais/management/commands/update_edital_status.py`
  - Atualizar status 'fechado' se end_date < hoje e status='aberto'
  - Atualizar status 'programado' se start_date > hoje
  - Adicionar logging
- [ ] T053 Testar management command manualmente
- [ ] T054 Documentar como configurar cron/task scheduler para executar command diariamente

### 8.2: Performance & Optimization

- [ ] T055 Otimizar queries em todas as views
  - Usar select_related para created_by/updated_by
  - Usar prefetch_related para cronogramas
  - Minimizar número de queries por página
- [ ] T056 Implementar cache para listagens públicas
  - Configurar cache backend (Redis, Memcached, ou database cache)
  - Implementar invalidação de cache quando editais são criados/editados/deletados
- [ ] T057 Adicionar índices adicionais se necessário
  - Analisar queries lentas
  - Adicionar índices conforme necessário

### 8.3: Security & Validation

- [ ] T058 Implementar sanitização de HTML em todos os campos de texto
  - Usar bleach para sanitizar HTML
  - Configurar tags e atributos permitidos
- [ ] T059 Validar entrada em todas as views
  - Prevenir SQL injection (usar Django ORM)
  - Prevenir XSS (sanitizar HTML)
  - Validar datas e campos obrigatórios
- [ ] T060 Implementar proteção CSRF em todas as operações de escrita
  - Verificar que CSRF está habilitado
  - Testar proteção CSRF

### 8.4: Localization & Internationalization

- [ ] T061 Verificar configuração de LANGUAGE_CODE='pt-br' em `UniRV_Django/settings.py`
- [ ] T062 Verificar configuração de TIME_ZONE='America/Sao_Paulo' em `UniRV_Django/settings.py`
- [ ] T063 Verificar que todos os templates estão em português
- [ ] T064 Verificar que todas as mensagens estão em português
- [ ] T065 Verificar formatos de data e número seguindo padrões brasileiros

### 8.5: Cleanup & Maintenance

- [ ] T066 Remover funcionalidade de favoritos das views em `editais/views.py`
  - Remover views `toggle_favorite()` e `my_favorites()`
  - Manter modelo EditalFavorite no banco (não deletar)
- [ ] T067 Remover URLs de favoritos em `editais/urls.py`
  - Remover rotas de favoritos
- [ ] T068 Remover referências a favoritos nos templates
  - Remover botões de favoritar
  - Remover páginas de favoritos
- [ ] T069 Adicionar nota no código indicando que favoritos foram removidos do MVP

### 8.6: Testing & Coverage

- [ ] T070 Executar todos os testes: `python manage.py test editais`
- [ ] T071 Verificar cobertura de testes: `coverage run manage.py test editais`
- [ ] T072 Gerar relatório de cobertura: `coverage report`
- [ ] T073 Identificar e corrigir gaps de cobertura (alcançar mínimo de 85%)
- [ ] T074 Executar testes de integração
- [ ] T075 Executar testes de performance (se aplicável)

### 8.7: Documentation

- [ ] T076 Atualizar README.md
  - Instruções de setup
  - Estrutura do projeto
  - Variáveis de ambiente
  - Comandos de migração
  - Comandos de teste
- [ ] T077 Documentar URLs públicas e administrativas
- [ ] T078 Documentar sistema de permissões
- [ ] T079 Documentar management commands
- [ ] T080 Documentar cache e performance

### 8.8: Production Readiness

- [ ] T081 Verificar configuração de DEBUG=False para produção
- [ ] T082 Verificar configuração de ALLOWED_HOSTS
- [ ] T083 Verificar configuração de SECRET_KEY (variável de ambiente)
- [ ] T084 Verificar configuração de WhiteNoise para static files
- [ ] T085 Verificar configuração de Gunicorn
- [ ] T086 Verificar configuração de HTTPS
- [ ] T087 Verificar backup de banco de dados
- [ ] T088 Verificar logging configurado para produção

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sem dependências - pode começar imediatamente
- **Foundational (Phase 2)**: Depende do Setup - BLOQUEIA todas as user stories
- **User Stories (Phase 3+)**: Todas dependem da conclusão da fase Foundational
  - User stories podem então prosseguir em paralelo (se houver equipe)
  - Ou sequencialmente em ordem de prioridade (P1 → P2 → P3)
- **Polish (Phase 8)**: Depende de todas as user stories desejadas estarem completas

### User Story Dependencies

- **User Story 1 (P1)**: Pode começar após Foundational (Phase 2) - Sem dependências de outras stories
- **User Story 2 (P1)**: Pode começar após Foundational (Phase 2) - Depende de US1 para URLs
- **User Story 3 (P2)**: Pode começar após Foundational (Phase 2) - Depende de US1/US2 para estrutura
- **User Story 4 (P2)**: Pode começar após Foundational (Phase 2) - Depende de US3 para criação
- **User Story 5 (P3)**: Pode começar após Foundational (Phase 2) - Depende de US3/US4 para admin

### Within Each User Story

- Testes (se incluídos) DEVEM ser escritos e FALHAR antes da implementação
- Models antes de views
- Views antes de templates
- Implementação core antes de integração
- Story completa antes de passar para próxima prioridade

### Parallel Opportunities

- Todas as tarefas de Setup marcadas [P] podem ser executadas em paralelo
- Todas as tarefas de Foundational marcadas [P] podem ser executadas em paralelo (dentro da Phase 2)
- Uma vez que a fase Foundational esteja completa, todas as user stories podem começar em paralelo (se a equipe permitir)
- Todos os testes de uma user story marcados [P] podem ser executados em paralelo
- Models dentro de uma story marcados [P] podem ser executados em paralelo
- Diferentes user stories podem ser trabalhadas em paralelo por diferentes membros da equipe

---

## Parallel Example: User Story 1

```bash
# Executar todos os testes para User Story 1 juntos:
Task: "Teste unitário para view de listagem em editais/tests/test_views.py"
Task: "Teste de integração para busca em editais/tests/test_search.py"
Task: "Teste de integração para filtros em editais/tests/test_filters.py"

# Executar implementação:
Task: "Implementar view de listagem em editais/views.py"
Task: "Criar template de listagem em templates/editais/list.html"
Task: "Implementar helper function para busca em editais/views.py"
Task: "Implementar helper function para filtros em editais/views.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 & 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. Complete Phase 4: User Story 2
5. **STOP and VALIDATE**: Testar User Stories 1 e 2 independentemente
6. Deploy/demo se estiver pronto

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP parcial!)
3. Add User Story 2 → Test independently → Deploy/Demo (MVP completo!)
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo
6. Add User Story 5 → Test independently → Deploy/Demo
7. Cada story adiciona valor sem quebrar stories anteriores

### Parallel Team Strategy

Com múltiplos desenvolvedores:

1. Equipe completa Setup + Foundational juntos
2. Uma vez que Foundational esteja completo:
   - Desenvolvedor A: User Story 1
   - Desenvolvedor B: User Story 2
   - Desenvolvedor C: User Story 3
3. Stories completam e integram independentemente

---

## Notes

- [P] tasks = arquivos diferentes, sem dependências
- [Story] label mapeia tarefa para user story específica para rastreabilidade
- Cada user story deve ser independentemente completável e testável
- Verificar que testes falham antes de implementar
- Commitar após cada tarefa ou grupo lógico
- Parar em qualquer checkpoint para validar story independentemente
- Evitar: tarefas vagas, conflitos no mesmo arquivo, dependências cross-story que quebram independência

---

## Task Summary

**Total de Tarefas**: 88  
**Por Fase**:
- Phase 1 (Setup): 5 tarefas
- Phase 2 (Foundational): 18 tarefas
- Phase 3 (US1): 8 tarefas
- Phase 4 (US2): 6 tarefas
- Phase 5 (US3): 8 tarefas
- Phase 6 (US4): 8 tarefas
- Phase 7 (US5): 4 tarefas
- Phase 8 (Polish): 31 tarefas

**Tarefas com Testes**: 27 tarefas de teste  
**Tarefas de Implementação**: 61 tarefas

**Última Atualização**: 2025-11-11

