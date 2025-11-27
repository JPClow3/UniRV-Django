# Implementation Plan: Hub de Editais — Módulo "Editais" (AgroHub UniRV)

**Branch**: `001-hub-editais` | **Date**: 2025-11-11 | **Updated**: 2025-01-15 (Rebuild from Codebase)  
**Spec**: [spec.md](./spec.md) | **Analysis**: [analysis.md](./analysis.md)  
**Status**: ✅ Implementation Complete (95%)

## Summary

Criar o módulo Editais como parte do site AgroHub UniRV — um hub de editais de fomento direcionado a startups, professores e alunos da UniRV. O módulo permite que visitantes busquem e visualizem editais, e que administradores criem, editem e removam editais via CRUD.

**Abordagem Técnica**: 
- Django 5.2.7+ com modelos existentes (Edital, Cronograma, EditalValor)
- Adicionar campos `slug`, `start_date`, `end_date` ao modelo Edital
- Restringir operações administrativas (CRUD/exportação) a usuários `is_staff`
- URLs baseadas em slug com redirecionamento 301 de URLs antigas (PK)
- Busca e filtros na interface pública
- Django Admin customizado para interface administrativa
- Cache para listagens públicas (TTL: 5 minutos)
- Management command para atualização automática de status baseado em datas

## Technical Context

**Language/Version**: Python 3.9+ / Django 5.2.7+  
**Primary Dependencies**: Django 5.2.7, WhiteNoise 6.7.0, bleach 6.1.0, requests 2.32.3, beautifulsoup4 4.12.3  
**Storage**: SQLite (desenvolvimento), PostgreSQL (produção)  
**Testing**: Django TestCase, pytest (opcional), cobertura mínima 85%  
**Target Platform**: Linux server (produção), Windows/Linux/Mac (desenvolvimento)  
**Project Type**: Web application (Django)  
**Performance Goals**: 
- Listagem pública carrega em menos de 2 segundos com 100+ editais
- Busca case-insensitive em múltiplos campos
- Cache de listagens públicas (TTL: 5 minutos)
- Queries otimizadas com select_related/prefetch_related

**Constraints**: 
- Conformidade com Constituição do projeto (segurança, TDD, Django best practices)
- Todos os campos e mensagens em português brasileiro (pt-BR)
- TIME_ZONE = "America/Sao_Paulo"
- DEBUG=False em produção
- SECRET_KEY em variável de ambiente
- Cobertura de testes mínima: 85%

**Scale/Scope**: 
- Módulo inicial para gerenciamento de editais
- Suporte a múltiplos usuários (administradores, editores, visitantes)
- Paginação: 12 itens por página (padrão)
- Operações administrativas (CRUD/exportação) restritas a usuários `is_staff`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ Django Best Practices
- [x] Seguir Django conventions e patterns
- [x] Usar Django's built-in features (models, views, forms, admin)
- [x] Aderir à estrutura de projeto Django (apps em diretórios separados)
- [x] Usar Django ORM para todas as operações de banco de dados
- [x] Seguir Django naming conventions (lowercase app names, snake_case)

### ✅ Security First
- [x] SECRET_KEY em variável de ambiente (.env)
- [x] Validação e sanitização de input do usuário (Django forms, bleach)
- [x] Configurações de segurança em produção (HTTPS, secure cookies, HSTS, CSRF)
- [x] Usar Django's built-in authentication e authorization
- [x] Proteção contra SQL injection (Django ORM exclusivamente)

### ✅ Test-Driven Development
- [x] Escrever testes antes de implementar features (TDD: Red-Green-Refactor)
- [x] Cobertura de testes requerida para todas as novas features
- [x] Usar Django's TestCase para unit e integration tests
- [x] Testar models, views, forms, e custom management commands
- [x] Executar testes antes de commit: `python manage.py test`

### ✅ Database Migrations
- [x] Sempre criar migrations para mudanças de modelo: `python manage.py makemigrations`
- [x] Revisar arquivos de migration antes de aplicar: `python manage.py migrate`
- [x] Nunca editar migration files existentes depois de aplicados em produção
- [x] Manter arquivos de migration em version control

### ✅ Code Quality & Documentation
- [x] Seguir PEP 8 Python style guide
- [x] Escrever docstrings para todas as classes, funções e métodos
- [x] Manter funções e classes focadas e pequenas (Single Responsibility Principle)
- [x] Usar nomes de variáveis e funções significativos (preferencialmente em português para código user-facing)
- [x] Manter README.md atualizado com instruções de setup e estrutura do projeto

### ✅ Static Files & Media Management
- [x] Usar WhiteNoise para servir arquivos estáticos em produção
- [x] Coletar arquivos estáticos antes do deploy: `python manage.py collectstatic`
- [x] Organizar arquivos estáticos por tipo (CSS, JS, imagens) em diretórios separados

### ✅ Environment Configuration
- [x] Usar variáveis de ambiente para toda configuração que varia entre ambientes
- [x] Fornecer `.env.example` com todas as variáveis requeridas (sem valores sensíveis)
- [x] Documentar todas as variáveis de ambiente no README.md

**Status**: ✅ Todas as verificações de conformidade passaram. Pronto para implementação.

## Project Structure

### Documentation (this feature)

```text
specs/001-hub-editais/
├── plan.md              # This file (/speckit.plan command output)
├── spec.md              # Feature specification
├── clarifications.md    # Resolved clarifications
├── research.md          # Phase 0 output (to be created)
├── data-model.md        # Phase 1 output (to be created)
├── quickstart.md        # Phase 1 output (to be created)
├── contracts/           # Phase 1 output (to be created)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
UniRV-Django/
├── editais/                    # App principal de editais
│   ├── __init__.py
│   ├── admin.py                # Django Admin customizado
│   ├── apps.py
│   ├── forms.py                # Formulários para CRUD
│   ├── models.py               # Modelos: Edital, Cronograma, EditalValor
│   ├── views.py                # Views públicas e administrativas
│   ├── urls.py                 # URLs públicas e administrativas
│   ├── tests.py                # Testes unitários e de integração
│   ├── management/
│   │   └── commands/
│   │       ├── __init__.py
│   │       ├── seed_editais.py         # Comando existente
│   │       └── update_edital_status.py # NOVO: Atualizar status automaticamente
│   ├── migrations/             # Migrations do Django
│   │   ├── __init__.py
│   │   ├── 0001_initial.py
│   │   ├── 0002_edital_analise.py
│   │   ├── 0003_alter_cronograma_options_alter_edital_options_and_more.py
│   │   ├── 0004_edital_idx_data_atualizacao_edital_idx_status_and_more.py
│   │   ├── 0005_add_slug_start_date_end_date.py  # NOVO: Adicionar campos
│   │   └── 0006_add_status_draft_programado.py   # NOVO: Adicionar status
│   └── templatetags/
│       └── __init__.py
├── templates/
│   ├── base.html
│   └── editais/
│       ├── list.html           # Listagem pública com busca e filtros
│       ├── detail.html         # Detalhe público do edital
│       ├── create.html         # (Opcional: se não usar Django Admin)
│       ├── update.html         # (Opcional: se não usar Django Admin)
│       └── delete.html         # (Opcional: se não usar Django Admin)
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── main.js
│   └── img/
│       └── Logo.svg
├── UniRV_Django/
│   ├── __init__.py
│   ├── settings.py             # Configurações do projeto
│   ├── urls.py                 # URLs principais
│   ├── wsgi.py
│   └── asgi.py
├── requirements.txt
├── manage.py
└── db.sqlite3                  # Database SQLite (desenvolvimento)
```

**Structure Decision**: 
- Estrutura Django padrão com app `editais` existente
- Templates organizados por app (`templates/editais/`)
- Static files organizados por tipo (CSS, JS, imagens)
- Migrations versionadas no diretório `editais/migrations/`
- Management commands em `editais/management/commands/`

## Complexity Tracking

> **No violations detected** - Todas as decisões estão alinhadas com a Constituição do projeto e seguem Django best practices.

## Implementation Phases

### Phase 0: Research & Analysis ✅

**Status**: ✅ Completed  
**Output**: [research.md](./research.md) ✅ Created

**Tasks**:
- [x] Analisar modelos existentes (Edital, Cronograma, EditalValor, EditalFavorite)
- [x] Analisar estrutura de URLs existente
- [x] Identificar campos existentes vs. campos necessários
- [x] Documentar decisões de clarificação
- [x] Validar conformidade com Constituição

**Findings**:
- Modelos existentes: Edital, Cronograma, EditalValor, EditalFavorite
- Campos existentes em português: titulo, entidade_principal, objetivo, criterios_elegibilidade, etc.
- URLs atuais usam PK (`/editais/<pk>/`)
- Base de dados vazia (nenhuma migração de dados necessária)
- Sistema de favoritos existe mas será removido do MVP
- Upload de anexos será removido do MVP

### Phase 1: Design & Data Model ✅

**Status**: ✅ Completed  
**Output**: [data-model.md](./data-model.md) ✅ Created

**Tasks**:
- [x] Definir escopo de permissões (operações administrativas restritas a usuários `is_staff`)
- [x] Definir modelo de dados atualizado (Edital com slug, start_date, end_date)
- [x] Definir status choices: draft, aberto, em_andamento, fechado, programado
- [x] Definir sistema de permissões (staff, editor, admin)
- [x] Definir estrutura de URLs (slug-based)
- [x] Definir estrutura de templates
- [x] Documentar decisões de clarificação

**Data Model Decisions**:
- Adicionar campos `slug`, `start_date`, `end_date` ao modelo Edital
- Manter modelo Cronograma existente (para cronogramas detalhados/múltiplas etapas)
- Manter modelo EditalValor existente (para valores financeiros)
- **NÃO criar modelo EditalAttachment** (upload de anexos REMOVIDO do MVP)
- Manter modelo EditalFavorite no banco (não usar na interface - REMOVIDO do MVP)

**URL Structure**:
- URLs públicas: `/editais/` (listagem), `/editais/<slug>/` (detalhe)
- URLs administrativas: `/admin/editais/` (Django Admin)
- Redirecionamento 301 de URLs antigas (PK) para novas URLs (slug)

**Template Structure**:
- `editais/list.html` - Listagem pública com busca e filtros
- `editais/detail.html` - Detalhe público do edital
- Django Admin customizado para interface administrativa

### Phase 2: Implementation Plan

**Status**: ✅ Completed (95%)  
**Output**: This document (plan.md) ✅ Updated

#### 2.1: Database Migrations ✅

**Status**: ✅ Completed  
**Tasks**:
1. ✅ Criar migration para adicionar campo `slug` ao modelo Edital
   - ✅ Campo: `SlugField(unique=True, max_length=255, editable=False)`
   - ✅ Gerado automaticamente no método `save()` com fallback
   - ✅ Não editável manualmente

2. ✅ Criar migration para adicionar campos `start_date` e `end_date` ao modelo Edital
   - ✅ Campos: `DateField(blank=True, null=True)`
   - ✅ `start_date` = data de abertura
   - ✅ `end_date` = data de encerramento geral

3. ✅ Criar migration para adicionar status 'draft' e 'programado' aos STATUS_CHOICES
   - ✅ Adicionar 'draft' (Rascunho)
   - ✅ Adicionar 'programado' (Programado)

4. ✅ Criar migration para adicionar índices
   - ✅ Índice em `slug` (idx_slug)
   - ✅ Índice em `status, start_date, end_date` (idx_status_dates)
   - ✅ Índice em `titulo` (idx_titulo)
   - ✅ Índices adicionais em Cronograma, EditalValor, EditalHistory, Project

5. ✅ Criar data migration para popular slugs a partir de títulos existentes
   - ✅ Migration 0006_populate_slugs.py implementada
   - ✅ Usa `slugify()` para gerar slugs
   - ✅ Garante unicidade (adiciona sufixo numérico se necessário)

6. ✅ Criar modelo EditalHistory para auditoria
   - ✅ Migration 0007_editalhistory_delete_editalfavorite_and_more.py
   - ✅ Preserva histórico mesmo após deleção

7. ✅ Criar modelo Project para showcase de propostas de startups (**NOTA**: Nomenclatura incorreta - refatoração futura, ver CLAR-020)
   - ✅ Migration 0010_create_project_model.py
   - ✅ Índices otimizados implementados

**Migrations Aplicadas**: 10 migrations (0001 a 0010)  
**Dependencies**: None  
**Actual Time**: Completed

#### 2.2: Model Updates ✅

**Status**: ✅ Completed  
**Tasks**:
1. ✅ Atualizar modelo Edital
   - ✅ Adicionar campos `slug`, `start_date`, `end_date`
   - ✅ Adicionar status 'draft' e 'programado' aos STATUS_CHOICES
   - ✅ Implementar método `_generate_unique_slug()` com fallback e regex pattern matching
   - ✅ Implementar lógica de status automático no método `save()` com edge cases
   - ✅ Atualizar `get_absolute_url()` para usar slug (com fallback para PK)
   - ✅ Atualizar índices no Meta (15+ índices)
   - ✅ Implementar métodos: `is_open()`, `is_closed()`, `can_edit(user)`
   - ✅ Implementar propriedades: `days_until_deadline`, `is_deadline_imminent`
   - ✅ Validação de datas em `clean()`
   - ✅ Tratamento de race conditions em slug uniqueness

2. ✅ Manter e melhorar modelos existentes
   - ✅ Cronograma: Índices otimizados adicionados
   - ✅ EditalValor: Choices para moeda (BRL/USD/EUR), índices otimizados
   - ✅ EditalFavorite: Removido do MVP (modelo deletado)

3. ✅ Criar novos modelos
   - ✅ EditalHistory: Histórico completo de alterações com preservação após deleção
   - ✅ Project: Sistema de showcase de propostas de startups com status e notas (**NOTA**: Nomenclatura incorreta - refatoração futura, ver CLAR-020)

**Dependencies**: 2.1 (Database Migrations) ✅  
**Actual Time**: Completed

#### 2.3: URL Migration ✅

**Status**: ✅ Completed  
**Tasks**:
1. ✅ Atualizar URLs públicas
   - ✅ Adicionar rota `/edital/<slug>/` para detalhe (edital_detail_slug)
   - ✅ Manter rota `/edital/<pk>/` com redirecionamento 301 para slug (edital_detail_redirect)
   - ✅ Atualizar view de detalhe para suportar slug e PK
   - ✅ Listagem pública: `/editais/` com busca e filtros

2. ✅ Atualizar URLs administrativas
   - ✅ Dashboard routes: `/dashboard/editais/`, `/dashboard/projetos/`, etc.
   - ✅ CRUD routes: `/cadastrar/`, `/edital/<pk>/editar/`, `/edital/<pk>/excluir/`
   - ✅ Django Admin customizado com sanitização HTML

3. ✅ URLs adicionais implementadas
   - ✅ Home, login, register, password reset
   - ✅ Ambientes de inovação, projetos aprovados
   - ✅ Health check endpoint

**Dependencies**: 2.2 (Model Updates) ✅  
**Actual Time**: Completed

#### 2.4: Views & Forms ✅

**Status**: ✅ Completed  
**Tasks**:
1. ✅ Implementar views públicas
   - ✅ View de listagem (`index`) com busca e filtros avançados
   - ✅ View de detalhe (`edital_detail`) suportando slug e PK
   - ✅ Paginação numérica exibindo 12 itens por página
   - ✅ Cache versionado de listagens públicas (TTL: 5 minutos)
   - ✅ Cache diferenciado por tipo de usuário (staff/auth/public) para segurança
   - ✅ Views: home, ambientes_inovacao, projetos_aprovados, login, register

2. ✅ Implementar views administrativas
   - ✅ Django Admin customizado com sanitização HTML
   - ✅ Dashboard views: home, editais, projetos, avaliacoes, usuarios, relatorios
   - ✅ CRUD views: create, update, delete com verificação `is_staff`
   - ✅ Rate limiting implementado (5 requisições/minuto por IP)
   - ✅ Histórico de alterações (EditalHistory) em todas as operações

3. ✅ Implementar formulários
   - ✅ `EditalForm` para criar/editar edital
   - ✅ `UserRegistrationForm` para registro de usuários
   - ✅ Validação de dados (datas, campos obrigatórios)
   - ✅ Sanitização de HTML (bleach) em views e admin

4. ✅ Implementar Service Layer
   - ✅ `EditalService` com métodos estáticos para lógica de negócio
   - ✅ Separação de responsabilidades (views vs services)

5. ✅ Implementar utilitários
   - ✅ `sanitize_html()`, `sanitize_edital_fields()`, `mark_edital_fields_safe()`
   - ✅ `rate_limit()` decorator
   - ✅ `get_client_ip()` helper
   - ✅ Exceções customizadas (EditalNotFoundError)

**Dependencies**: 2.3 (URL Migration) ✅  
**Actual Time**: Completed

#### 2.5: Templates ✅

**Status**: ✅ Completed  
**Tasks**:
1. ✅ Criar template de listagem (`editais/index.html`)
   - ✅ Search bar com busca case-insensitive
   - ✅ Filtros (status, tipo, datas, "somente abertos")
   - ✅ Cards com resumo (título, organização, datas, status)
   - ✅ Aviso "prazo próximo" para editais com prazo nos últimos 7 dias
   - ✅ Paginação numérica para 12 itens por página
   - ✅ Tailwind CSS integrado

2. ✅ Criar template de detalhe (`editais/detail.html`)
   - ✅ Header com título e status
   - ✅ Metadados (organização, datas, status)
   - ✅ Objetivo formatado (HTML sanitizado)
   - ✅ Critérios de elegibilidade
   - ✅ Cronogramas
   - ✅ Link externo (url)
   - ✅ Aviso "prazo próximo" se aplicável
   - ✅ Histórico de alterações

3. ✅ Criar templates administrativos
   - ✅ Dashboard templates: home, editais, projetos, avaliacoes, usuarios, relatorios
   - ✅ CRUD templates: create, update, delete
   - ✅ Base template com Tailwind CSS

4. ✅ Templates públicos adicionais
   - ✅ home.html, ambientes_inovacao.html, projetos_aprovados.html
   - ✅ Registration templates: login, register, password reset

5. ✅ Templates de erro
   - ✅ 403.html, 404.html, 500.html

**Dependencies**: 2.4 (Views & Forms) ✅  
**Actual Time**: Completed

#### 2.6: Permissions System ✅

**Status**: ✅ Completed  
**Tasks**:
1. ✅ Restringir operações administrativas (CRUD/exportação) a usuários `is_staff`
   - ✅ Garantir `@login_required` + `request.user.is_staff` em todas as views administrativas
   - ✅ Exibir mensagens apropriadas (403.html) para usuários sem permissão
   - ✅ Ajustar templates/botões para aparecer apenas para `is_staff`
   - ✅ Verificação implementada em: create, update, delete, dashboard views

2. ✅ Atualizar Django Admin
   - ✅ Confirmar que somente `is_staff` tem acesso às ações CRUD
   - ✅ Sanitização HTML implementada no `save_model()`
   - ✅ Rastreamento automático de `created_by` e `updated_by`

3. ✅ Filtro de visibilidade
   - ✅ Editais 'draft' ocultados automaticamente para não autenticados/não-staff
   - ✅ Implementado em views públicas (index, detail)

**Dependencies**: 2.4 (Views & Forms) ✅  
**Actual Time**: Completed

#### 2.7: Search & Filters ✅

**Status**: ✅ Completed  
**Tasks**:
1. ✅ Implementar busca
   - ✅ Case-insensitive (`icontains`)
   - ✅ Buscar em: título, entidade_principal, numero_edital
   - ✅ Modo "contém" (partial match)
   - ✅ Operador OR entre campos (AND entre termos)
   - ✅ Executar após submit (não em tempo real)
   - ✅ Função `build_search_query()` implementada

2. ✅ Implementar filtros
   - ✅ Filtros combinados com AND
   - ✅ Filtro de status (aberto, em_andamento, fechado, draft, programado)
   - ✅ Filtro de tipo (Fluxo Contínuo vs Fomento)
   - ✅ Filtro de datas (start_date, end_date)
   - ✅ Opção "somente abertos"
   - ✅ Persistir filtros na URL (query parameters)
   - ✅ Filtros implementados em views públicas e administrativas

**Dependencies**: 2.4 (Views & Forms) ✅  
**Actual Time**: Completed

#### 2.8: Management Command ✅

**Status**: ✅ Completed  
**Tasks**:
1. ✅ Criar management command `update_edital_status.py`
   - ✅ Atualizar status automaticamente baseado em datas
   - ✅ Lógica: se `end_date <= hoje` e status='aberto', atualizar para 'fechado'
   - ✅ Lógica: se `start_date > hoje`, atualizar para 'programado'
   - ✅ Lógica: se `start_date <= hoje <= end_date` e status='programado', atualizar para 'aberto'
   - ✅ Suporte a `--dry-run` e `--verbose`
   - ✅ Error handling individual para cada edital
   - ✅ Cache invalidation após atualizações
   - ✅ Executar diariamente (via cron ou task scheduler)

2. ✅ Outros management commands
   - ✅ `populate_from_pdfs.py` (se implementado)
   - ✅ `seed_editais.py` para desenvolvimento/testes

3. ✅ Service Layer
   - ✅ `EditalService.update_status_by_dates()` implementado
   - ✅ Lógica reutilizável entre modelo e command

**Dependencies**: 2.2 (Model Updates) ✅  
**Actual Time**: Completed

#### 2.9: Cache Implementation ✅

**Status**: ✅ Completed  
**Tasks**:
1. ✅ Implementar cache para listagens públicas
   - ✅ Usar Django cache framework
   - ✅ TTL: 5 minutos (CACHE_TTL_INDEX=300)
   - ✅ Cache versionado para invalidação eficiente
   - ✅ Invalidar cache quando editais são criados/editados/deletados
   - ✅ Função `_clear_index_cache()` implementada

2. ✅ Cache de detalhes
   - ✅ Cache diferenciado por tipo de usuário (staff/auth/public)
   - ✅ TTL: 15 minutos
   - ✅ Previne cache poisoning e CSRF token leakage

3. ✅ Otimizar queries
   - ✅ Usar `select_related()` para created_by/updated_by
   - ✅ Usar `prefetch_related()` para cronogramas, valores, history
   - ✅ Usar `only()` para limitar campos retornados
   - ✅ Minimizar database queries por página
   - ✅ Queries agregadas para estatísticas

**Dependencies**: 2.4 (Views & Forms) ✅  
**Actual Time**: Completed

#### 2.10: Testing ✅

**Status**: ✅ Completed (169+ testes passando)  
**Tasks**:
1. ✅ Testes unitários
   - ✅ Testar modelo Edital (slug generation, status automático, validações)
   - ✅ Testar views (listagem, detalhe, busca, filtros, dashboard)
   - ✅ Testar formulários (validação, sanitização)
   - ✅ Testar sistema de permissões
   - ✅ Testar Django Admin

2. ✅ Testes de integração
   - ✅ Testar fluxo completo de criação de edital
   - ✅ Testar fluxo completo de edição de edital
   - ✅ Testar fluxo completo de exclusão de edital
   - ✅ Testar busca e filtros
   - ✅ Testar redirecionamento de URLs (PK → slug)
   - ✅ Testar workflows completos

3. ✅ Testes de segurança
   - ✅ CSRF protection
   - ✅ XSS prevention
   - ✅ SQL injection prevention
   - ✅ Authentication/Authorization

4. ✅ Testes de management commands
   - ✅ `update_edital_status` com todos os cenários
   - ✅ Error handling
   - ✅ Cache invalidation

5. ⚠️ Cobertura mínima de 85%
   - ⚠️ Executar `coverage run manage.py test` (pendente)
   - ⚠️ Gerar relatório de cobertura (pendente)
   - ✅ 169+ testes implementados e passando

**Arquivos de Teste**: 9 arquivos (test_admin.py, test_dashboard_views.py, test_public_views.py, test_security.py, test_permissions.py, test_integration.py, test_management_commands.py, test_views_dashboard.py, test_legacy.py)  
**Dependencies**: 2.1-2.9 (All Implementation Tasks) ✅  
**Actual Time**: Completed

#### 2.11: Documentation ✅

**Status**: ✅ Completed (Specs atualizados)  
**Tasks**:
1. ✅ Atualizar README.md
   - ✅ Instruções de setup
   - ✅ Estrutura do projeto
   - ✅ Variáveis de ambiente
   - ✅ Comandos de migração
   - ✅ Comandos de teste

2. ✅ Documentar especificações
   - ✅ spec.md atualizado com implementação
   - ✅ data-model.md completo
   - ✅ research.md completo
   - ✅ analysis.md completo
   - ✅ clarifications.md atualizado
   - ✅ progress.md regenerado

3. ✅ Documentar sistema de permissões
   - ✅ Documentado em spec.md e clarifications.md
   - ✅ Sistema baseado em `is_staff` implementado

4. ⚠️ Documentação de produção
   - ⚠️ README de produção (pendente)
   - ⚠️ Guia de deploy (pendente)

**Dependencies**: 2.1-2.10 (All Implementation Tasks) ✅  
**Actual Time**: Completed (Specs), Pendente (Produção)

### Phase 3: Testing & Quality Assurance ✅

**Status**: ✅ Completed (95%)  
**Output**: Test results ✅, coverage reports ⚠️

**Tasks**:
1. ✅ Executar testes unitários e de integração (169+ testes passando)
2. ⚠️ Validar cobertura de testes (mínimo 85%) - pendente execução de `coverage`
3. ✅ Validar conformidade com Constituição
4. ✅ Validar segurança (CSRF, XSS, SQL injection) - todos testados
5. ✅ Validar performance (queries otimizadas, cache funcionando)
6. ✅ Validar localização (pt-BR) - todos os campos e mensagens em português

### Phase 4: Deployment ⏳

**Status**: ⏳ Pending  
**Output**: Deployed application

**Tasks**:
1. ⏳ Configurar variáveis de ambiente em produção
2. ⏳ Executar migrações em produção
3. ⏳ Coletar arquivos estáticos
4. ⏳ Configurar cache em produção
5. ⏳ Configurar logging em produção
6. ⏳ Configurar backup de banco de dados
7. ⏳ Configurar execução automática do management command (cron/task scheduler)

## Risk Assessment

### Technical Risks

1. **Migração de URLs (PK → Slug)**
   - **Risk**: Links antigos podem quebrar
   - **Mitigation**: Implementar redirecionamento 301 de URLs antigas para novas
   - **Impact**: Baixo (redirecionamento automático)

2. **Geração de Slug Duplicado**
   - **Risk**: Slugs duplicados podem causar erros
   - **Mitigation**: Implementar lógica de geração única com sufixo numérico
   - **Impact**: Baixo (lógica testada)

3. **Performance de Busca**
   - **Risk**: Busca pode ser lenta com muitos editais
   - **Mitigation**: Implementar índices, cache, e otimização de queries
   - **Impact**: Médio (pode ser otimizado)

### Business Risks

1. **Upload de Anexos Removido do MVP**
   - **Risk**: Usuários podem precisar de upload de anexos
   - **Mitigation**: Manter campo 'url' para links externos
   - **Impact**: Baixo (funcionalidade será adicionada em fase futura)

2. **Sistema de Favoritos Removido do MVP**
   - **Risk**: Usuários podem precisar de favoritos
   - **Mitigation**: Funcionalidade será adicionada em fase futura como "salvar"
   - **Impact**: Baixo (funcionalidade será adicionada em fase futura)

## Dependencies

### External Dependencies
- Django 5.2.7+
- WhiteNoise 6.7.0+
- bleach 6.1.0+
- Python 3.9+

### Internal Dependencies
- Modelos existentes (Edital, Cronograma, EditalValor)
- Sistema de autenticação Django
- Templates base existentes
- Static files existentes

## Timeline

### Actual Total Time: Completed (95%)

- Phase 0: Research & Analysis ✅ (Completed)
- Phase 1: Design & Data Model ✅ (Completed)
- Phase 2: Implementation ✅ (Completed - 95%)
  - 2.1: Database Migrations ✅ (10 migrations aplicadas)
  - 2.2: Model Updates ✅ (5 modelos implementados)
  - 2.3: URL Migration ✅ (URLs baseadas em slug implementadas)
  - 2.4: Views & Forms ✅ (20+ views implementadas)
  - 2.5: Templates ✅ (15+ templates criados)
  - 2.6: Permissions System ✅ (Sistema baseado em is_staff)
  - 2.7: Search & Filters ✅ (Busca e filtros avançados)
  - 2.8: Management Command ✅ (update_edital_status implementado)
  - 2.9: Cache Implementation ✅ (Cache versionado implementado)
  - 2.10: Testing ✅ (169+ testes passando)
  - 2.11: Documentation ✅ (Specs atualizados, produção pendente)
- Phase 3: Testing & Quality Assurance ✅ (95% - coverage pendente)
- Phase 4: Deployment ⏳ (Pending)

## Success Criteria

### Technical Success Criteria
- [x] Todas as migrations aplicadas com sucesso (10 migrations)
- [x] Modelos atualizados e funcionando (5 modelos)
- [x] URLs migradas para slug com redirecionamento 301
- [x] Views públicas e administrativas funcionando (20+ views)
- [x] Templates criados e estilizados (15+ templates)
- [x] Sistema de permissões implementado (baseado em is_staff)
- [x] Busca e filtros funcionando
- [x] Management command funcionando
- [x] Cache implementado e funcionando (cache versionado)
- [ ] Cobertura de testes ≥ 85% (pendente verificação)
- [x] Conformidade com Constituição validada

### Business Success Criteria
- [x] Visitantes conseguem buscar e visualizar editais
- [x] Usuários `is_staff` conseguem criar/editar/deletar editais
- [x] Sistema de permissões básico (restrições `is_staff`) funcionando
- [x] Status atualizados automaticamente baseado em datas
- [x] Performance adequada (listagem carrega em < 2 segundos)
- [x] Todos os campos e mensagens em português brasileiro

## Notes

- Base de dados vazia (nenhuma migração de dados necessária)
- Upload de anexos REMOVIDO do MVP (manter campo 'url' para links externos)
- Sistema de favoritos REMOVIDO do MVP (será "salvar" em fase futura)
- Filtro de localização REMOVIDO do MVP (será adicionado em fase futura se necessário)
- Todos os campos em português (não adicionar campos em inglês)
- Slug gerado automaticamente, não editável
- Status automático baseado em datas (management command diário)
- **Modelo Project**: Nomenclatura incorreta - representa propostas de startups (showcase), não projetos submetidos. Refatoração futura necessária (CLAR-020)
- **Rota Dashboard**: `/dashboard/editais/novo/` precisa implementar processamento POST (CLAR-021)
- **Sistema de Notificações**: Priorizado para próxima fase (CLAR-024)

## Next Steps

1. ✅ **Specification**: Completed
2. ✅ **Clarifications**: All resolved (24/24) - Recent: CLAR-020 (Project nomenclature), CLAR-021 (Dashboard route), CLAR-022 (Status distinction), CLAR-023 (Project workflow), CLAR-024 (Feature prioritization)
3. ✅ **Plan**: This document (Updated)
4. ✅ **Tasks**: Detailed task list created (85/89 completed - 95%)
5. ✅ **Implementation**: Completed (95%)
6. ⏳ **Coverage**: Verify test coverage ≥ 85%
7. ⏳ **Dashboard Route**: Implement POST processing for `/dashboard/editais/novo/` (CLAR-021)
8. ⏳ **Documentation**: Production README and deployment guide
9. ⏳ **Deployment**: Configure production environment
10. ⏳ **Future Refactoring**: Rename Project model to StartupProposal (CLAR-020)