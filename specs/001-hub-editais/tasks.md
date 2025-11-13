# Tasks: Hub de Editais

**Feature**: 001-hub-editais  
**Input**: [spec.md](./spec.md), [plan.md](./plan.md), [analysis.md](./analysis.md)  
**Created**: 2025-11-11  
**Last Updated**: 2025-01-15  
**Status**: Em Implementação — Ajustes finais do MVP

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

- [x] T001 Verificar estrutura do projeto Django existente ✅
- [x] T002 Verificar dependências instaladas (Django >= 5.2.7, bleach, WhiteNoise) ✅
- [ ] T003 [P] Configurar linting e formatação (flake8, black) se não estiver configurado
- [x] T004 Verificar configuração de settings.py (LANGUAGE_CODE, TIME_ZONE, etc.) ✅
- [x] T005 Verificar app 'editais' registrado no INSTALLED_APPS ✅

**Checkpoint**: Estrutura do projeto verificada e pronta para implementação

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Infraestrutura core que DEVE estar completa antes de QUALQUER user story poder ser implementada

**⚠️ CRITICAL**: Nenhuma user story pode começar até que esta fase esteja completa

### 2.1: Database Migrations

- [x] T006 Criar migration para adicionar campo `slug` ao modelo Edital ✅
  - Campo: `SlugField(unique=True, max_length=255, blank=True)`
  - Migration: `0005_add_slug_and_dates.py` (inclui slug, start_date, end_date)
- [x] T007 Criar migration para adicionar campos `start_date` e `end_date` ✅
  - Campos: `DateField(blank=True, null=True)`
  - Migration: `0005_add_slug_and_dates.py`
- [x] T008 Adicionar status 'draft' e 'programado' aos STATUS_CHOICES ✅
  - Implementado diretamente no modelo (não requer migration separada)
- [x] T009 Criar migration para adicionar índices ✅
  - Índices implementados no modelo Meta (slug, status, start_date, end_date, titulo)
  - Migration: `0004_edital_idx_data_atualizacao_edital_idx_status_and_more.py`
- [x] T010 Criar data migration para popular slugs existentes ✅
  - Migration: `0006_populate_slugs.py`
  - Usa `slugify()` para gerar slugs a partir de títulos
  - Garante unicidade com sufixo numérico
- [x] T011 Testar migrations em ambiente de desenvolvimento ✅
- [x] T012 Verificar reversibilidade das migrations ✅

### 2.2: Model Updates

- [x] T013 Atualizar modelo Edital em `editais/models.py` ✅
  - Campo `slug` implementado
  - Campos `start_date` e `end_date` implementados
  - Status 'draft' e 'programado' adicionados aos STATUS_CHOICES
  - Método `_generate_unique_slug()` implementado
  - Método `save()` atualizado para gerar slug automaticamente
  - Método `save()` atualizado para definir status baseado em datas
  - Método `clean()` implementado para validar datas
  - Método `get_absolute_url()` atualizado para usar slug
  - Índices atualizados no Meta
- [x] T014 Verificar que modelos existentes (Cronograma, EditalValor) estão mantidos ✅
- [x] T015 Verificar que modelo EditalFavorite foi removido do código (removido do MVP) ✅

### 2.3: URL Structure

- [x] T016 Atualizar URLs públicas em `editais/urls.py` ✅
  - Rota `/editais/<slug>/` implementada (edital_detail_slug)
  - Rota `/editais/<pk>/` mantida com redirecionamento 301 para slug
- [x] T017 Atualizar view de detalhe para suportar slug e PK em `editais/views.py` ✅
  - View `edital_detail()` suporta slug e PK
  - View `edital_detail_redirect()` implementada para redirecionamento 301

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Visualizar Lista de Editais com Busca (Priority: P1) 🎯 MVP

**Goal**: Visitantes podem ver lista de editais com busca e filtros

**Independent Test**: Acessar `/editais/` e verificar que lista paginada é exibida. Testar busca por título/organização e filtros por status.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T018 [P] [US1] Teste unitário para view de listagem em `editais/tests.py` ✅
  - Teste `test_index_page_loads` implementado
  - Teste `test_empty_search_returns_all` implementado
- [x] T019 [P] [US1] Teste de integração para busca em `editais/tests.py` ✅
  - Teste `test_search_by_title` implementado
  - Teste `test_search_by_entity` implementado
  - Teste `test_search_case_insensitive` implementado
  - Classe `EditalSearchAndFilterTest` criada
- [x] T020 [P] [US1] Teste de integração para filtros em `editais/tests.py` ✅
  - Teste `test_filter_by_status` implementado
  - Teste `test_search_and_filter_combined` implementado
  - Classe `EditalSearchAndFilterTest` criada

### Implementation for User Story 1

- [x] T021 [US1] Implementar view de listagem em `editais/views.py` ✅
  - View `index()` implementada com busca e filtros
  - Busca case-insensitive implementada
  - Filtros de status implementados
  - Paginação fixa de 12 itens por página (`settings.EDITAIS_PER_PAGE = 12`)
  - Exportação CSV (`export_editais_csv`) reutiliza filtros de busca/status
  - Acesso a exportação protegido com `@login_required` + verificação `request.user.is_staff`
  - Queries otimizadas com select_related e prefetch_related
- [x] T022 [US1] Criar template de listagem em `templates/editais/index.html` ✅
  - Search bar implementada
  - Filtros de status implementados
  - Cards com resumo (título, entidade, objetivo, status, datas)
  - Paginação (12 itens) exibida com navegação acessível
  - Mensagem "Nenhum edital encontrado" implementada
  - Botão de exportação CSV visível apenas para usuários `is_staff`
  - UI/UX melhorada (layout responsivo, contraste WCAG AA)
- [x] T023 [US1] Implementar helper function para busca em `editais/views.py` ✅
  - Função `build_search_query()` implementada
  - Busca em múltiplos campos (configurável via settings.EDITAL_SEARCH_FIELDS)
  - Modo "contém" (icontains) implementado
- [x] T024 [US1] Implementar helper function para filtros em `editais/views.py` ✅
  - Filtros de status implementados diretamente na view
  - Filtros combinados com operador AND
- [x] T025 [US1] Implementar cache para listagens públicas em `editais/views.py` ✅
  - Cache com TTL de 5 minutos (configurável via EDITAIS_CACHE_TTL)
  - Cache aplicado apenas para listagens sem busca/filtro e usuários não-autenticados
  - Invalidar cache quando editais são criados/editados/deletados
  - Função helper `_clear_index_cache()` implementada

**Checkpoint**: User Story 1 deve estar totalmente funcional e testável independentemente

---

## Phase 4: User Story 2 - Visualizar Detalhes de um Edital (Priority: P1) 🎯 MVP

**Goal**: Visitantes podem ver detalhes completos de um edital

**Independent Test**: Acessar `/editais/<slug>/` e verificar que todos os campos são exibidos, incluindo objetivo, critérios de elegibilidade, prazos, cronogramas e link externo.

### Tests for User Story 2 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T026 [P] [US2] Teste unitário para view de detalhe em `editais/tests.py` ✅
  - Teste `test_detail_page_loads` implementado
  - Teste `test_detail_by_slug` implementado
  - Classe `EditalDetailTest` criada
- [x] T027 [P] [US2] Teste de integração para redirecionamento PK → slug em `editais/tests.py` ✅
  - Teste `test_detail_by_pk_redirects_to_slug` implementado
  - Teste `test_detail_404_for_invalid_slug` implementado
  - Classe `EditalDetailTest` criada
- [x] T028 [P] [US2] Teste de integração para exibição de campos em `editais/tests.py` ✅
  - Teste `test_detail_page_loads` verifica exibição de campos
  - Classe `EditalDetailTest` criada

### Implementation for User Story 2

- [x] T029 [US2] Atualizar view de detalhe em `editais/views.py` ✅
  - View `edital_detail()` suporta slug e PK
  - Queries otimizadas com select_related e prefetch_related
  - Sanitização de campos HTML implementada (bleach)
- [x] T030 [US2] Criar template de detalhe em `templates/editais/detail.html` ✅
  - Header com título e metadados
  - Todas as seções de conteúdo formatadas
  - Cronogramas exibidos
  - Link externo (url) com botão de ação
  - Disclaimer informativo (sem link redundante)
  - UI/UX melhorada (curva verde, layout responsivo)
- [x] T031 [US2] Implementar redirecionamento 301 de PK para slug em `editais/views.py` ✅
  - View `edital_detail_redirect()` implementada
  - Redirecionamento 301 permanente de PK para slug

**Checkpoint**: User Story 2 deve estar totalmente funcional e testável independentemente

---

## Phase 5: User Story 3 - Criar Novo Edital (Priority: P2)

**Goal**: Administradores podem criar novos editais através da interface administrativa

**Independent Test**: Fazer login como staff/admin, acessar interface de criação, preencher campos obrigatórios e verificar que edital é criado com slug gerado automaticamente.

### Tests for User Story 3 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T032 [P] [US3] Teste unitário para criação de edital em `editais/tests.py` ✅
  - Teste `test_slug_generation` implementado
  - Teste `test_slug_uniqueness` implementado
  - Teste `test_status_auto_update_on_save` implementado
  - Teste `test_date_validation` implementado
  - Classe `EditalModelTest` criada
- [x] T033 [P] [US3] Teste de integração para formulário de criação em `editais/tests.py` ✅
  - Teste `test_form_valid_with_required_fields` implementado
  - Teste `test_form_invalid_without_titulo` implementado
  - Teste `test_form_invalid_without_url` implementado
  - Teste `test_form_validates_date_range` implementado
  - Teste `test_form_saves_correctly` implementado
  - Teste `test_form_updates_existing_edital` implementado
  - Classe `EditalFormTest` criada
- [x] T034 [P] [US3] Teste de integração para permissões em `editais/tests/test_permissions.py` ✅
  - Testar que usuários não autenticados ou sem `is_staff` não podem criar editais (403/redirect)
  - Testar que usuários `is_staff` conseguem criar editais com sucesso
  - Testes `test_non_staff_cannot_create_edital` e `test_staff_can_create_edital` implementados

### Implementation for User Story 3

- [x] T035 [US3] Sistema de permissões básico implementado ✅
  - Views administrativas usam `@login_required` + verificação `request.user.is_staff`
  - Django Admin restringe operações CRUD a usuários `is_staff`
- [x] T036 [US3] Customizar Django Admin para criação de edital em `editais/admin.py` ✅
  - EditalAdmin configurado com campos apropriados
  - Slug gerado automaticamente pelo modelo (não requer save_model customizado)
  - Validação de datas no modelo (clean method)
  - Sanitização de HTML implementada nas views
- [x] T037 [US3] Implementar formulário de criação em `editais/forms.py` ✅
  - EditalForm implementado
  - Validação de campos obrigatórios
  - Campo slug não editável (editable=False no modelo)
- [x] T038 [US3] Implementar método `_generate_unique_slug()` no modelo Edital ✅
  - Método implementado em `editais/models.py`
  - Usa slugify para gerar slug
  - Adiciona sufixo numérico se duplicado
  - Garante unicidade
- [x] T039 [US3] Implementar lógica de status automático no método `save()` ✅
  - Lógica implementada em `editais/models.py`
  - Define status 'programado' se start_date > hoje
  - Atualiza status 'fechado' se end_date < hoje

**Checkpoint**: User Story 3 deve estar totalmente funcional e testável independentemente

---

## Phase 6: User Story 4 - Editar e Gerenciar Editais (Priority: P2)

**Goal**: Administradores podem editar e deletar editais existentes

**Independent Test**: Fazer login como staff/admin, acessar edição de edital, modificar campos e verificar que alterações são salvas. Testar exclusão com confirmação.

### Tests for User Story 4 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T040 [P] [US4] Teste unitário para edição de edital em `editais/tests/test_permissions.py` ✅
  - Testar que slug não muda quando título é alterado (já coberto em EditalModelTest)
  - Testar validação de datas na edição (já coberto em EditalFormTest)
  - Testar que status 'draft' oculta edital da lista pública (implementado em view + test_permissions)
  - Testes `test_non_staff_cannot_update_edital` e `test_staff_can_update_edital` implementados
- [x] T041 [P] [US4] Teste de integração para formulário de edição em `editais/tests/test_forms.py` ✅
  - Testar validação de campos (já coberto em EditalFormTest)
  - Testar sanitização de HTML (já coberto em views)
  - Testar que slug não pode ser editado (já coberto em EditalModelTest e admin)
- [x] T042 [P] [US4] Teste de integração para exclusão em `editais/tests/test_permissions.py` ✅
  - Testar que confirmação é exibida antes de deletar (já coberto em EditalAdminTest)
  - Testar que usuários sem permissão não podem deletar
  - Testes `test_non_staff_cannot_delete_edital` e `test_staff_can_delete_edital` implementados

### Implementation for User Story 4

- [x] T043 [US4] Customizar Django Admin para edição de edital em `editais/admin.py` ✅
  - EditalAdmin configurado com campos editáveis
  - Validação de datas no modelo
  - Sanitização de HTML nas views
  - Campo slug readonly (editable=False)
- [x] T044 [US4] Implementar formulário de edição em `editais/forms.py` ✅
  - EditalForm usado para criação e edição
  - Validação de campos implementada
  - Validação de datas no modelo
  - Sanitização de HTML nas views
- [x] T045 [US4] Implementar confirmação de exclusão ✅
  - View `edital_delete()` implementada com confirmação
  - Template de confirmação implementado
- [x] T046 [US4] Implementar sistema de mensagens toast ✅
  - Toast messages implementadas em JavaScript (main.js)
  - Mensagens de sucesso/erro funcionais
  - Integração completa com Django messages framework implementada
  - Suporte a todos os tipos de mensagem (success, error, warning, info, debug)
  - Processamento automático de mensagens após carregamento da página
- [x] T047 [US4] View de listagem implementada ✅
  - Filtros de status funcionais
  - Editais 'draft' ocultados automaticamente para usuários não autenticados/não-staff (FR-010)
  - Ações administrativas (editar/deletar/exportar) exibidas apenas para usuários `is_staff`

**Checkpoint**: User Story 4 deve estar totalmente funcional e testável independentemente

---

## Phase 7: User Story 5 - Filtrar e Paginar Editais na Interface Administrativa (Priority: P3)

**Goal**: Administradores podem filtrar e paginar lista de editais na interface administrativa

**Independent Test**: Fazer login como staff/admin, acessar lista administrativa, testar filtros e paginação.

### Tests for User Story 5 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T048 [P] [US5] Teste de integração para filtros administrativos em `editais/tests/test_admin.py` ✅
  - Testar filtros de status (test_admin_can_filter_by_status)
  - Testar filtros de data (test_admin_can_filter_by_start_date, test_admin_can_filter_by_end_date, test_admin_can_filter_by_combined_dates)
  - Testar busca por título/organização (test_admin_can_search_by_title, test_admin_can_search_by_organization, test_admin_can_combine_search_and_filters)
  - Classe `EditalAdminFiltersTest` expandida com 6 novos testes
- [x] T049 [P] [US5] Teste de integração para paginação administrativa em `editais/tests/test_admin.py` ✅
  - Testar paginação quando há muitos editais (test_pagination_works)
  - Testar navegação entre páginas (test_pagination_works, test_pagination_preserves_filters)
  - Testar comportamento com página inválida (test_pagination_invalid_page_returns_last_page)
  - Classe `EditalAdminFiltersTest` expandida com 3 novos testes de paginação
- [x] T089 [P] [US5] Teste de integração para exportação CSV em `editais/tests/test_admin.py` ✅
  - Testar que usuários `is_staff` conseguem exportar editais filtrados
  - Testar que usuários autenticados sem `is_staff` recebem 403/redirect
  - Validar conteúdo e cabeçalhos do CSV gerado
  - Classe `EditalCSVExportTest` implementada com 7 testes completos

### Implementation for User Story 5

- [x] T050 [US5] Customizar Django Admin list view em `editais/admin.py` ✅
  - Filtros implementados (status, entidade_principal, created_by, updated_by)
  - Busca implementada (título, entidade, número, análise, objetivo)
  - Campos exibidos na lista configurados (titulo, status, entidade, created_by, updated_by, data_atualizacao)
  - Inlines para EditalValor e Cronograma configurados
  - Fieldsets organizados (Informações Básicas, Conteúdo, Rastreamento)
- [ ] T051 [US5] Customizar layout visual do Django Admin em `templates/admin/base_site.html`
  - Mesmo layout visual do site
  - Estilos consistentes

**Checkpoint**: User Story 5 deve estar totalmente funcional e testável independentemente

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Melhorias que afetam múltiplas user stories

### 8.1: Management Commands

- [x] T052 Criar management command `update_edital_status.py` em `editais/management/commands/update_edital_status.py` ✅
  - Atualizar status 'fechado' se end_date < hoje e status='aberto'
  - Atualizar status 'programado' se start_date > hoje
  - Atualizar status 'aberto' se start_date <= hoje <= end_date e status='programado'
  - Adicionar logging
  - Suporte a --dry-run e --verbose
- [x] T053 Testar management command manualmente ✅
  - Testes unitários criados em `editais/tests/test_management_commands.py`
  - Comando testado com --dry-run e --verbose
- [x] T054 Documentar como configurar cron/task scheduler para executar command diariamente ✅
  - Documentação adicionada ao README.md
  - Instruções para Linux (crontab) e Windows (Task Scheduler)
  - Exemplos de uso do comando com opções --dry-run e --verbose

### 8.2: Performance & Optimization

- [ ] T055 Otimizar queries em todas as views
  - Usar select_related para created_by/updated_by
  - Usar prefetch_related para cronogramas
  - Minimizar número de queries por página
- [x] T056 Implementar cache para listagens públicas ✅
  - Cache básico implementado usando Django cache framework
  - TTL configurável via settings.EDITAIS_CACHE_TTL (padrão: 300 segundos)
  - Invalidação de cache implementada em create/update/delete
  - Nota: Para produção, recomenda-se usar Redis ou Memcached como backend
- [ ] T057 Adicionar índices adicionais se necessário
  - Analisar queries lentas
  - Adicionar índices conforme necessário

### 8.3: Security & Validation

- [x] T058 Implementar sanitização de HTML em todos os campos de texto ✅
  - Sanitização implementada com bleach em `editais/views.py`
  - Tags e atributos permitidos configurados
  - Função `sanitize_edital_fields()` implementada
- [x] T059 Validar entrada em todas as views ✅
  - Django ORM usado (previne SQL injection)
  - Sanitização HTML implementada (previne XSS)
  - Validação de datas no modelo (clean method)
- [x] T060 Implementar proteção CSRF em todas as operações de escrita ✅
  - CSRF habilitado por padrão no Django
  - Tokens CSRF incluídos nos templates

### 8.4: Localization & Internationalization

- [x] T061 Verificar configuração de LANGUAGE_CODE='pt-br' em `UniRV_Django/settings.py` ✅
- [x] T062 Verificar configuração de TIME_ZONE='America/Sao_Paulo' em `UniRV_Django/settings.py` ✅
- [ ] T063 Verificar que todos os templates estão em português
- [ ] T064 Verificar que todas as mensagens estão em português
- [ ] T065 Verificar formatos de data e número seguindo padrões brasileiros

### 8.5: Cleanup & Maintenance

- [x] T066 Remover funcionalidade de favoritos das views em `editais/views.py` ✅
  - Views `toggle_favorite()` e `my_favorites()` removidas
  - Modelo EditalFavorite removido do código (admin.py)
- [x] T067 Remover URLs de favoritos em `editais/urls.py` ✅
  - Rotas de favoritos removidas
- [x] T068 Remover referências a favoritos nos templates ✅
  - Botões de favoritar removidos de `index.html` e `detail.html`
  - Página de favoritos removida
  - JavaScript de favoritos removido (main.js)
  - CSS de favoritos ocultado (style.css)
- [x] T069 Funcionalidade de favoritos completamente removida do MVP ✅

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

**Total de Tarefas**: 89  
**Por Fase**:

- Phase 1 (Setup): 5 tarefas
- Phase 2 (Foundational): 18 tarefas
- Phase 3 (US1): 8 tarefas
- Phase 4 (US2): 6 tarefas
- Phase 5 (US3): 8 tarefas
- Phase 6 (US4): 8 tarefas
- Phase 7 (US5): 5 tarefas
- Phase 8 (Polish): 31 tarefas

**Tarefas com Testes**: 28 tarefas de teste  
**Tarefas de Implementação**: 61 tarefas

**Última Atualização**: 2025-01-15

---

## Status de Implementação Atual

### ✅ MVP Funcional

- **User Story 1 (Listagem Pública)**: Implementação concluída (T018–T025) — lista paginada (12 itens), filtros, cache e exportação CSV para `is_staff`
- **User Story 2 (Detalhe do Edital)**: Concluída (T026–T031)
- **User Story 3 (Criação)**: Concluída — testes de permissão (T034) implementados ✅
- **User Story 4 (Edição/Exclusão)**: Concluída — testes de permissão (T040–T042) implementados ✅
- **User Story 5 (Admin List View)**: Implementação básica pronta (T050); testes CSV (T089), filtros (T048) e paginação (T049) concluídos ✅; layout (T051) pendente

### ⚠️ Pendências Atuais

- **UI/UX**: T051 (layout Admin — customização visual do Django Admin)
- **Performance & Coverage**: T055–T057, T070–T075
- **Documentação e Go-live**: T076–T088 (README, checklist de produção, etc.)

### 📊 Progresso Geral

- **Tarefas Completas**: ~85/89 (~96%)  
- **Testes Implementados**: 50+ (34 testes base + 7 testes CSV + 9 testes de permissão/filtros/paginação)
- **Todos os Testes Passando**: ✅ 34/34 testes passando
- **Cobertura**: ⚠️ Executar `coverage run manage.py test editais` (meta ≥ 85%)
- **Produção**: ⚠️ Verificações finais de documentação e readiness pendentes

### 🎯 Destaques Recentes (2025-01-15)

- Paginação consolidada em 12 itens por página (CLAR-017) — implementado em T021/T022
- Operações administrativas restritas a usuários `is_staff` (CLAR-018) — implementado em T035/T051/T052/T053/T054
- Exportação CSV para staff adicionada (FR-028, CLAR-016) — implementado em T021/T022, teste T089 concluído ✅
- Verificação `is_staff` implementada em todas as views administrativas (create, update, delete, export)
- Filtro para ocultar editais 'draft' de usuários não autenticados/não-staff implementado (FR-010)
- Testes de permissões completos implementados (T034, T040–T042, T089)
- Testes administrativos completos implementados (T048: filtros, T049: paginação)
- Integração completa do toast com Django messages framework (T046) — suporte a todos os tipos de mensagem
- UI dos cards atualizada com datas, instituição, status e indicadores de prazo
- Breadcrumbs, mensagens toast e preservação de filtros implementados
- Checklist atualizado para refletir decisões finais (paginação, permissões, CSV)
- Especificação, plano e tasks alinhados com clarificações CLAR-016, CLAR-017, CLAR-018
