# Implementation Plan: Hub de Editais — Módulo "Editais" (AgroHub UniRV)

**Branch**: `001-hub-editais` | **Date**: 2025-11-11 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-hub-editais/spec.md`

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

**Status**: Completed  
**Output**: [research.md](./research.md) (to be created)

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

**Status**: Completed  
**Output**: [data-model.md](./data-model.md) (to be created), [quickstart.md](./quickstart.md) (to be created)

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

**Status**: In Progress  
**Output**: This document (plan.md)

#### 2.1: Database Migrations

**Tasks**:
1. Criar migration para adicionar campo `slug` ao modelo Edital
   - Campo: `SlugField(unique=True, max_length=255)`
   - Gerado automaticamente no método `save()`
   - Não editável manualmente

2. Criar migration para adicionar campos `start_date` e `end_date` ao modelo Edital
   - Campos: `DateField(blank=True, null=True)`
   - `start_date` = data de abertura
   - `end_date` = data de encerramento geral

3. Criar migration para adicionar status 'draft' e 'programado' aos STATUS_CHOICES
   - Adicionar 'draft' (Rascunho)
   - Adicionar 'programado' (Programado)

4. Criar migration para adicionar índices
   - Índice em `slug`
   - Índice em `status, start_date, end_date`
   - Índice em `titulo` (para busca)

5. Criar data migration para popular slugs a partir de títulos existentes (se houver dados)
   - Usar `slugify()` para gerar slugs
   - Garantir unicidade (adicionar sufixo numérico se necessário)

**Dependencies**: None  
**Estimated Time**: 4-6 hours

#### 2.2: Model Updates

**Tasks**:
1. Atualizar modelo Edital
   - Adicionar campos `slug`, `start_date`, `end_date`
   - Adicionar status 'draft' e 'programado' aos STATUS_CHOICES
   - Implementar método `_generate_unique_slug()`
   - Implementar lógica de status automático no método `save()`
   - Atualizar `get_absolute_url()` para usar slug
   - Atualizar índices no Meta

2. Manter modelos existentes
   - Cronograma (sem alterações)
   - EditalValor (sem alterações)
   - EditalFavorite (manter no banco, não usar na interface)

**Dependencies**: 2.1 (Database Migrations)  
**Estimated Time**: 3-4 hours

#### 2.3: URL Migration

**Tasks**:
1. Atualizar URLs públicas
   - Adicionar rota `/editais/<slug>/` para detalhe
   - Manter rota `/editais/<pk>/` com redirecionamento 301 para slug
   - Atualizar view de detalhe para suportar slug e PK

2. Atualizar URLs administrativas
   - Usar Django Admin (sem alterações de URL necessárias)
   - Customizar Django Admin para usar slug nas URLs

**Dependencies**: 2.2 (Model Updates)  
**Estimated Time**: 2-3 hours

#### 2.4: Views & Forms

**Tasks**:
1. Implementar views públicas
   - View de listagem com busca e filtros
   - View de detalhe (suportar slug e PK)
   - Paginação numérica (5 páginas visíveis) exibindo 12 itens por página
   - Cache de listagens públicas (TTL: 5 minutos)

2. Implementar views administrativas
   - Usar Django Admin padrão
   - Customizar Django Admin (visual, preview, etc.)
   - Restringir operações de criação/edição/exclusão/exportação a usuários `is_staff`

3. Implementar formulários
   - Formulário para criar/editar edital (Django Admin ou custom)
   - Validação de dados (datas, slug, etc.)
   - Sanitização de HTML (bleach)

4. Implementar endpoint de exportação CSV
   - View protegida por `@login_required` + verificação `is_staff`
   - Exportar dados filtrados (busca/status) com campos Número, Título, Entidade, Status, URL, datas e responsáveis
   - Responder em CSV UTF-8 com BOM para compatibilidade com Excel

**Dependencies**: 2.3 (URL Migration)  
**Estimated Time**: 9-11 hours

#### 2.5: Templates

**Tasks**:
1. Criar template de listagem (`editais/list.html`)
   - Search bar
   - Filtros (status, datas, "somente abertos")
   - Cards com resumo (título, organização, datas, status)
   - Aviso "prazo próximo" para editais com prazo nos últimos 7 dias
   - Paginação numérica (5 páginas visíveis) para 12 itens por página
   - Botão de exportação CSV visível somente para usuários `is_staff`

2. Criar template de detalhe (`editais/detail.html`)
   - Header com título e status
   - Metadados (organização, datas, status)
   - Objetivo formatado
   - Critérios de elegibilidade
   - Cronogramas
   - Link externo (url)
   - Aviso "prazo próximo" se aplicável

3. Customizar Django Admin
   - Mesmo layout visual do site
   - Preview antes de publicar
   - Mensagens toast (canto inferior direito)

**Dependencies**: 2.4 (Views & Forms)  
**Estimated Time**: 6-8 hours

#### 2.6: Permissions System

**Tasks**:
1. Restringir operações administrativas (CRUD/exportação) a usuários `is_staff`
   - Garantir `@login_required` + `request.user.is_staff` nas views de criação/edição/exclusão/exportação
   - Exibir mensagens apropriadas para usuários sem permissão
   - Ajustar templates/botões para aparecer apenas para `is_staff`

2. Atualizar Django Admin
   - Confirmar que somente `is_staff` tem acesso às ações CRUD
   - Revisar permissões padrão (add/change/delete) conforme necessário

**Dependencies**: 2.4 (Views & Forms)  
**Estimated Time**: 1-2 hours

#### 2.7: Search & Filters

**Tasks**:
1. Implementar busca
   - Case-insensitive
   - Buscar em: título, objetivo, análise, número do edital, entidade principal
   - Modo "contém" (partial match)
   - Operador AND (todos os termos)
   - Executar após submit (não em tempo real)

2. Implementar filtros
   - Filtros combinados com AND
   - Filtro de status (aberto, em_andamento, fechado)
   - Filtro de datas (start_date, end_date)
   - Opção "somente abertos"
   - Persistir filtros na URL (query parameters)

**Dependencies**: 2.4 (Views & Forms)  
**Estimated Time**: 4-5 hours

#### 2.8: Management Command

**Tasks**:
1. Criar management command `update_edital_status.py`
   - Atualizar status automaticamente baseado em datas
   - Lógica: se `end_date < hoje` e status='aberto', atualizar para 'fechado'
   - Executar diariamente (via cron ou task scheduler)

2. Configurar execução automática
   - Documentar como configurar cron/task scheduler
   - Testar em ambiente de desenvolvimento

**Dependencies**: 2.2 (Model Updates)  
**Estimated Time**: 2-3 hours

#### 2.9: Cache Implementation

**Tasks**:
1. Implementar cache para listagens públicas
   - Usar Django cache framework
   - TTL: 5 minutos (configurável)
   - Invalidar cache quando editais são criados/editados/deletados

2. Otimizar queries
   - Usar `select_related()` para created_by/updated_by
   - Usar `prefetch_related()` para cronogramas
   - Minimizar database queries por página

**Dependencies**: 2.4 (Views & Forms)  
**Estimated Time**: 2-3 hours

#### 2.10: Testing

**Tasks**:
1. Testes unitários
   - Testar modelo Edital (slug generation, status automático)
   - Testar views (listagem, detalhe, busca, filtros)
   - Testar formulários (validação, sanitização)
   - Testar sistema de permissões

2. Testes de integração
   - Testar fluxo completo de criação de edital
   - Testar fluxo completo de edição de edital
   - Testar fluxo completo de exclusão de edital
   - Testar busca e filtros
   - Testar redirecionamento de URLs (PK → slug)

3. Alcançar cobertura mínima de 85%
   - Executar `coverage run manage.py test`
   - Gerar relatório de cobertura
   - Identificar e corrigir gaps de cobertura

**Dependencies**: 2.1-2.9 (All Implementation Tasks)  
**Estimated Time**: 10-12 hours

#### 2.11: Documentation

**Tasks**:
1. Atualizar README.md
   - Instruções de setup
   - Estrutura do projeto
   - Variáveis de ambiente
   - Comandos de migração
   - Comandos de teste

2. Documentar API/URLs
   - Documentar URLs públicas
   - Documentar URLs administrativas
   - Documentar query parameters

3. Documentar sistema de permissões
   - Documentar níveis de permissão
   - Documentar como criar usuários com permissões
   - Documentar como configurar grupos

**Dependencies**: 2.1-2.10 (All Implementation Tasks)  
**Estimated Time**: 3-4 hours

### Phase 3: Testing & Quality Assurance

**Status**: Pending  
**Output**: Test results, coverage reports

**Tasks**:
1. Executar testes unitários e de integração
2. Validar cobertura de testes (mínimo 85%)
3. Validar conformidade com Constituição
4. Validar segurança (CSRF, XSS, SQL injection)
5. Validar performance (queries otimizadas, cache funcionando)
6. Validar localização (pt-BR)

### Phase 4: Deployment

**Status**: Pending  
**Output**: Deployed application

**Tasks**:
1. Configurar variáveis de ambiente em produção
2. Executar migrações em produção
3. Coletar arquivos estáticos
4. Configurar cache em produção
5. Configurar logging em produção
6. Configurar backup de banco de dados
7. Configurar execução automática do management command (cron/task scheduler)

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

### Estimated Total Time: 45-55 hours

- Phase 0: Research & Analysis ✅ (Completed)
- Phase 1: Design & Data Model ✅ (Completed)
- Phase 2: Implementation (35-45 hours)
  - 2.1: Database Migrations (4-6 hours)
  - 2.2: Model Updates (3-4 hours)
  - 2.3: URL Migration (2-3 hours)
  - 2.4: Views & Forms (9-11 hours)
  - 2.5: Templates (6-8 hours)
  - 2.6: Permissions System (1-2 hours)
  - 2.7: Search & Filters (4-5 hours)
  - 2.8: Management Command (2-3 hours)
  - 2.9: Cache Implementation (2-3 hours)
  - 2.10: Testing (10-12 hours)
  - 2.11: Documentation (3-4 hours)
- Phase 3: Testing & Quality Assurance (8-10 hours)
- Phase 4: Deployment (4-6 hours)

## Success Criteria

### Technical Success Criteria
- [ ] Todas as migrations aplicadas com sucesso
- [ ] Modelos atualizados e funcionando
- [ ] URLs migradas para slug com redirecionamento 301
- [ ] Views públicas e administrativas funcionando
- [ ] Templates criados e estilizados
- [ ] Sistema de permissões implementado
- [ ] Busca e filtros funcionando
- [ ] Management command funcionando
- [ ] Cache implementado e funcionando
- [ ] Cobertura de testes ≥ 85%
- [ ] Conformidade com Constituição validada

### Business Success Criteria
- [ ] Visitantes conseguem buscar e visualizar editais
- [ ] Usuários `is_staff` conseguem criar/editar/deletar/exportar editais
- [ ] Sistema de permissões básico (restrições `is_staff`) funcionando
- [ ] Status atualizados automaticamente baseado em datas
- [ ] Performance adequada (listagem carrega em < 2 segundos)
- [ ] Todos os campos e mensagens em português brasileiro

## Notes

- Base de dados vazia (nenhuma migração de dados necessária)
- Upload de anexos REMOVIDO do MVP (manter campo 'url' para links externos)
- Sistema de favoritos REMOVIDO do MVP (será "salvar" em fase futura)
- Filtro de localização REMOVIDO do MVP (será adicionado em fase futura se necessário)
- Todos os campos em português (não adicionar campos em inglês)
- Slug gerado automaticamente, não editável
- Status automático baseado em datas (management command diário)

## Next Steps

1. ✅ **Specification**: Completed
2. ✅ **Clarifications**: All resolved
3. ✅ **Plan**: This document
4. ⏳ **Tasks**: Create detailed task list (`