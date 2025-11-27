# Clarifications: Hub de Editais — Módulo "Editais"

**Feature**: 001-hub-editais  
**Created**: 2025-11-11  
**Updated**: 2025-01-15 (Added CLAR-020 to CLAR-024)  
**Status**: ✅ All Resolved - Implementation Complete

## Overview

Este documento identifica requisitos que precisam de esclarecimento antes da implementação. Cada item precisa de uma decisão explícita do product owner ou equipe técnica.

---

## 🔴 CRITICAL - Blocking Implementation

### CLAR-001: Mapeamento de Status ✅ RESOLVIDO

**Context**: O sistema existente usa status: 'aberto', 'fechado', 'em_andamento'. A especificação sugere adicionar 'draft' ('rascunho').

**Questions**:

1. Como mapear 'em_andamento'? Deve ser tratado como equivalente a 'published' para exibição pública?
2. Qual é a diferença entre 'aberto' e 'em_andamento'? Ambos devem ser visíveis publicamente?
3. Status 'draft' deve ser visível apenas para administradores? Ou também para usuários autenticados?
4. Deve haver migração de dados existentes? Ex: todos os 'em_andamento' viram 'aberto'?

**Decisão Tomada** ✅:

- `draft` (rascunho): visível apenas para o criador e usuários com permissão de CRUD
- `aberto`: edital aceitando submissões (público)
- `em_andamento`: edital fechado para submissões (pode ser renomeado futuramente) (público)
- `fechado`: encerrado (histórico) (público)
- **Nenhuma migração de dados necessária** (base vazia)

**Impacto na Implementação**:

- Status choices: `draft`, `aberto`, `em_andamento`, `fechado`
- Filtro de visibilidade: rascunhos apenas para usuários com permissão CRUD
- Listagem pública: exibir 'aberto', 'em_andamento', 'fechado' (não exibir 'draft')

---

### CLAR-002: Campos de Data (start_date, end_date) vs. Cronograma ✅ RESOLVIDO

**Context**: Existem dois modelos possíveis: adicionar start_date/end_date diretamente ao Edital OU usar o modelo Cronograma existente.

**Questions**:

1. Um edital pode ter múltiplos cronogramas? (ex: período de inscrição, período de análise, período de execução)
2. Se usar start_date/end_date no Edital, qual é o propósito? Período de inscrição?
3. O modelo Cronograma deve ser mantido para cronogramas complexos (múltiplas fases)?
4. Na listagem pública, quais datas devem ser exibidas? start_date/end_date do Edital ou data_inicio/data_fim do primeiro Cronograma?

**Decisão Tomada** ✅:

- Um edital pode ter várias etapas e cronogramas distintos
- `start_date` = data de abertura; `end_date` = data de encerramento geral
- Cronogramas adicionais cobrem etapas como submissão e análise
- Na listagem pública: mostrar data de abertura e a data de encerramento da próxima etapa (ou de submissão se não houver)

**Impacto na Implementação**:

- Manter modelo Cronograma existente
- Adicionar campos `start_date` e `end_date` ao modelo Edital
- Lógica de exibição: na listagem, mostrar start_date e próxima data de encerramento do Cronograma
- Manter relação Edital → Cronograma (um para muitos)

---

### CLAR-003: Mapeamento de Campos (description, requirements) ✅ RESOLVIDO

**Context**: Existem campos existentes (objetivo, criterios_elegibilidade) e novos campos sugeridos (description, requirements).

**Questions**:

1. Os novos campos 'description' e 'requirements' devem substituir os campos existentes?
2. Ou devem ser campos adicionais que consolidam informações de múltiplos campos existentes?
3. Como mapear dados existentes? Popular 'description' a partir de 'objetivo'? Popular 'requirements' a partir de 'criterios_elegibilidade'?
4. Na interface pública, quais campos devem ser exibidos? Todos os campos existentes + novos, ou apenas novos?

**Decisão Tomada** ✅:

- **Manter os campos originais em português** (`objetivo`, `criterios_elegibilidade`)
- **Remover os campos novos em inglês** (`description`, `requirements`)
- **Toda a terminologia do sistema deve permanecer em português**

**Impacto na Implementação**:

- NÃO adicionar campos `description` e `requirements`
- Usar campos existentes: `objetivo`, `criterios_elegibilidade`, `analise`, `etapas`, etc.
- Garantir que toda interface use terminologia em português
- Templates e formulários devem usar nomes de campos em português

---

### CLAR-004: Geração Automática de Slug ✅ RESOLVIDO

**Context**: Slug deve ser único e gerado automaticamente a partir do título.

**Questions**:

1. Como gerar slug quando título já existe? Adicionar sufixo numérico? (ex: 'edital-fomento', 'edital-fomento-2')
2. Slug deve ser editável por administradores ou sempre gerado automaticamente?
3. Como lidar com caracteres especiais/acentos no título? Remover acentos? Manter?
4. Qual o comprimento máximo do slug? Django default é 50, suficiente?
5. Para editais existentes sem slug, como gerar slugs únicos durante migração?

**Decisão Tomada** ✅:

- Gerar automaticamente com `slugify(título)`
- Remover acentos
- Se houver duplicado, adicionar sufixo "-2", "-3", etc.
- **Slugs não podem ser editados manualmente**
- Sem limite de tamanho; usar slug completo

**Impacto na Implementação**:

- Usar `django.utils.text.slugify()` para gerar slug
- Implementar função para garantir unicidade (adicionar sufixo numérico se necessário)
- Slug field: `unique=True`, `blank=False` (gerado automaticamente)
- No modelo, usar `save()` method ou signal para gerar slug automaticamente
- Campo slug não deve aparecer em formulários (gerado automaticamente)

---

## 🟡 HIGH PRIORITY - Affects User Experience

### CLAR-005: Funcionalidade de Busca ✅ RESOLVIDO

**Context**: Busca por título, organização e palavras-chave.

**Questions**:

1. A busca deve ser case-sensitive ou case-insensitive?
2. A busca deve procurar em quais campos exatamente? Apenas título e organização, ou também em descrição, requisitos, etc.?
3. A busca deve ser "contém" (partial match) ou "começa com" ou ambos?
4. A busca deve usar operador AND (todos os termos) ou OR (qualquer termo)?
5. Deve haver busca por frase exata (entre aspas)?
6. A busca deve ser em tempo real (JavaScript) ou apenas após submit do formulário?

**Decisão Tomada** ✅:

- Case-insensitive
- Buscar em: título, descrição, datas e termos específicos
- Modo "contém" (partial match)
- Operadores aplicáveis (AND/OR - definir na implementação)
- Executar apenas após submit (sem busca em tempo real)

**Impacto na Implementação**:

- Busca case-insensitive usando `icontains` do Django ORM
- Campos pesquisados: `titulo`, `objetivo`, `analise`, `numero_edital`, `entidade_principal`
- Implementar busca com operador AND (todos os termos) por padrão
- Busca após submit do formulário (não em tempo real)
- Considerar usar `Q` objects do Django para busca avançada

---

### CLAR-006: Comportamento de Filtros ✅ RESOLVIDO

**Context**: Filtros por status, localização, datas.

**Questions**:

1. Os filtros devem ser combinados com AND (todos devem ser atendidos) ou OR (qualquer um)?
2. Filtro de data: buscar por data de início, data de fim, ou ambas?
3. Filtro de localização: busca exata ou partial match? Case-sensitive?
4. Quando nenhum filtro é aplicado, devem ser exibidos apenas editais 'aberto' ou todos os status exceto 'draft'?
5. Filtros devem persistir na URL (query parameters) para permitir compartilhamento de URLs filtradas?

**Decisão Tomada** ✅:

- Filtros combinam com operadores lógicos (AND)
- Filtro aplica-se a ambas as datas (início e fim)
- Por padrão, mostrar todos os editais, mas oferecer opção "somente abertos"
- Filtros devem aparecer na URL (query parameters)

**Impacto na Implementação**:

- Filtros combinados com AND
- Filtro de data: aplicar a `start_date` e `end_date`
- Opção de filtro "somente abertos" (status='aberto')
- Padrão: exibir todos os status exceto 'draft' (para não-autenticados)
- Persistir filtros na URL usando query parameters (`?status=aberto&data_inicio=2025-01-01`)
- Implementar filtro de localização REMOVIDO do MVP (ver CLAR-013)

---

### CLAR-007: Validação de Upload de Anexos ✅ RESOLVIDO

**Context**: Upload de múltiplos anexos com validação de tipo e tamanho.

**Questions**:

1. Quais tipos de arquivo são permitidos? Apenas PDF? PDF, DOC, DOCX, XLS, XLSX? Outros?
2. Qual é o tamanho máximo exato? 10MB por arquivo? 10MB total para todos os anexos?
3. Quantos anexos podem ser anexados por edital? Limite de quantidade?
4. O que acontece se um upload falhar? Todos os anexos são rejeitados ou apenas o que falhou?
5. Anexos devem ter nomes únicos ou podem ter o mesmo nome?
6. Deve haver validação de conteúdo do arquivo (ex: verificar se PDF é válido) ou apenas extensão?

**Decisão Tomada** ✅:

- **Upload removido do MVP. Nenhum arquivo pode ser anexado nesta fase.**

**Impacto na Implementação**:

- **NÃO implementar modelo EditalAttachment no MVP**
- **NÃO implementar upload de arquivos no MVP**
- Remover referências a anexos da interface pública
- Manter campo `url` no modelo Edital para links externos
- Upload de anexos será implementado em fase futura

---

### CLAR-008: Comportamento de Status e Datas ✅ RESOLVIDO

**Context**: Edge case: edital com data de fim no passado mas status ainda 'publicado'.

**Questions**:

1. O sistema deve atualizar automaticamente o status quando data de fim passa?
2. Ou administrador deve atualizar manualmente?
3. Editais com data de fim no passado devem ser exibidos na lista pública? Em uma seção separada "Histórico"?
4. Deve haver aviso visual para editais próximos do prazo (ex: "Encerra em 3 dias")?
5. O que acontece quando um edital é criado com data de início no futuro? Deve ter status especial?

**Decisão Tomada** ✅:

- Atualizar status automaticamente conforme data
- Mostrar editais encerrados na lista pública
- Mostrar aviso de "prazo próximo"
- Adicionar novo status "programado" para editais futuros

**Impacto na Implementação**:

- Implementar task/management command para atualizar status automaticamente (executar diariamente)
- Lógica: se `end_date < hoje` e status='aberto', atualizar para 'fechado'
- Adicionar status 'programado' para editais com `start_date > hoje`
- Exibir aviso visual na lista pública para editais com prazo próximo (últimos 7 dias)
- Manter editais encerrados visíveis na lista pública (não filtrar)

---

## 🟢 MEDIUM PRIORITY - Implementation Details

### CLAR-009: Migração de URLs (PK → Slug) ✅ RESOLVIDO

**Context**: Migrar de URLs baseadas em PK para URLs baseadas em slug.

**Questions**:

1. Por quanto tempo manter suporte a URLs baseadas em PK? 1 mês? 3 meses? Permanentemente?
2. URLs antigas devem redirecionar (301) para novas URLs ou retornar 404?
3. Como lidar com editais existentes que não têm slug? Gerar slugs durante migração?
4. Deve haver página de redirecionamento ou redirecionamento direto?
5. Como garantir que slugs gerados são únicos durante migração?

**Decisão Tomada** ✅:

- Adotar URLs baseadas em slug
- Migrar rotas antigas com redirecionamento 301
- Gerar automaticamente todos os slugs com slugify
- Validar unicidade durante a geração

**Impacto na Implementação**:

- Implementar URLs baseadas em slug: `/editais/<slug>/`
- Manter compatibilidade com URLs antigas (PK) e redirecionar (301) para slug
- Gerar slugs para todos os editais existentes durante migração (data migration)
- Validar unicidade durante geração (adicionar sufixo numérico se necessário)
- Redirecionamento direto (sem página intermediária)
- Atualizar `get_absolute_url()` para usar slug

---

### CLAR-010: Sistema de Favoritos (EditalFavorite) ✅ RESOLVIDO

**Context**: Modelo EditalFavorite já existe, mas está marcado como "out of scope" na especificação.

**Questions**:

1. A funcionalidade de favoritos deve ser mantida mesmo estando "out of scope"?
2. Se mantida, deve ser visível apenas para usuários autenticados?
3. Deve haver interface para gerenciar favoritos (listar, remover)?
4. Favoritos devem ser exibidos na lista pública (ícone de coração, etc.)?
5. Deve haver notificações quando um edital favoritado é atualizado?

**Decisão Tomada** ✅:

- **Remover funcionalidade de favoritos do MVP**
- Qualquer usuário poderá "salvar" (ícone de bandeira) em versões futuras
- Alterar nomenclatura para "salvar" em vez de "favoritar"

**Impacto na Implementação**:

- **NÃO implementar funcionalidade de favoritos no MVP**
- Manter modelo EditalFavorite no banco (não remover), mas não usar na interface
- Não exibir ícones de favorito na lista pública
- Não criar página "Meus Favoritos"
- Funcionalidade de "salvar" será implementada em fase futura com nova nomenclatura

---

### CLAR-011: Permissões e Autenticação ✅ RESOLVIDO

**Context**: CRUD apenas para staff (is_staff=True).

**Questions**:

1. Usuários autenticados (não-staff) podem ver editais em 'draft'?
2. Usuários autenticados podem favoritar editais?
3. Deve haver diferentes níveis de permissão? (ex: editor, moderador, admin)
4. Como criar usuários staff? Apenas via Django admin ou há interface customizada?
5. Deve haver auditoria de quem criou/editou cada edital? (já existe created_by/updated_by)

**Decisão Tomada** ✅:

- Usuários autenticados podem visualizar rascunhos conforme nível de permissão
- Implementar múltiplos níveis de acesso (staff, editor, admin)
- Usuários staff criados via Django Admin
- Auditoria ativa (created_by / updated_by)

**Impacto na Implementação**:

- Implementar sistema de permissões com níveis: staff (básico), editor (pode criar/editar), admin (pode deletar)
- Usar Django Groups ou campo customizado no User model
- Rascunhos visíveis apenas para usuários com permissão apropriada
- Manter auditoria (created_by/updated_by) - já existe no modelo
- Criar usuários staff via Django Admin
- Considerar usar Django permissions system (add_edital, change_edital, delete_edital)

---

### CLAR-012: Paginação e Performance ✅ RESOLVIDO

**Context**: Paginação de 20 itens por página.

**Questions**:

1. Paginação deve ser "previous/next" ou numérica (1, 2, 3, ...)?
2. Quantos números de página devem ser exibidos? (ex: 1, 2, 3, ..., 10)
3. Deve haver opção para alterar itens por página? (20, 50, 100)
4. Como otimizar queries para listagem? Usar select_related/prefetch_related?
5. Deve haver cache de listagens? Se sim, por quanto tempo?

**Decisão Tomada** ✅:

- Paginação numérica com 5 páginas visíveis
- Permitir alterar itens por página
- Otimizar queries com select_related e prefetch_related
- Habilitar cache para listagens

**Impacto na Implementação**:

- Implementar paginação numérica (1, 2, 3, 4, 5, ..., última)
- Exibir 5 números de página visíveis de cada vez
- Adicionar opção para alterar itens por página (dropdown: 20, 50, 100)
- Usar `select_related()` para created_by/updated_by
- Usar `prefetch_related()` para cronogramas (se necessário)
- Implementar cache para listagens públicas (usar Django cache framework)
- Cache TTL: 5 minutos (configurável)

---

### CLAR-013: Localização (Campo location) ✅ RESOLVIDO

**Context**: Filtro por localização (estado/cidade) como campo de texto.

**Questions**:

1. O campo location deve ser um campo de texto livre ou um campo com opções pré-definidas?
2. Se texto livre, como normalizar? (ex: "Rio de Janeiro" vs. "RJ" vs. "Rio de Janeiro, RJ")
3. Deve haver autocomplete para localização?
4. Filtro de localização deve buscar em estado, cidade, ou ambos?
5. Como lidar com editais que não têm localização específica? (ex: nacionais)

**Decisão Tomada** ✅:

- Todo o sistema deve usar campos e rótulos em português
- **Remover filtros de localização do MVP**
- Campo de localização poderá ser adicionado futuramente se houver necessidade

**Impacto na Implementação**:

- **NÃO implementar campo `location` no MVP**
- **NÃO implementar filtro de localização no MVP**
- Remover referências a localização da interface pública
- Campo de localização será implementado em fase futura se necessário

---

## 🔵 LOW PRIORITY - Nice to Have

### CLAR-014: Interface Administrativa ✅ RESOLVIDO

**Context**: CRUD via Django Admin ou painel customizado.

**Questions**:

1. Deve usar Django Admin padrão ou criar interface administrativa customizada?
2. Se customizada, qual é o escopo? Apenas CRUD de editais ou também outros modelos?
3. Interface customizada deve ter mesmo visual do site público ou design diferente?
4. Deve haver preview de edital antes de publicar?
5. Deve haver rascunhos automáticos (salvar automaticamente enquanto edita)?

**Decisão Tomada** ✅:

- Usar Django Admin com o mesmo layout visual do site
- Incluir preview antes de publicar
- Suporte a rascunhos automáticos enquanto edita

**Impacto na Implementação**:

- Usar Django Admin padrão, mas customizar visual para corresponder ao site público
- Customizar Django Admin usando templates e CSS personalizados
- Adicionar action "Preview" no Django Admin para visualizar edital antes de publicar
- Implementar rascunhos automáticos (salvar automaticamente a cada X segundos) - pode ser em fase futura
- Considerar usar Django Admin extensions (django-admin-interface) para melhorar visual

---

### CLAR-015: Mensagens de Erro e Validação ✅ RESOLVIDO

**Context**: Mensagens de erro e validação em português.

**Questions**:

1. Mensagens de erro devem ser técnicas (para desenvolvedores) ou amigáveis (para usuários)?
2. Deve haver mensagens de sucesso após operações? (ex: "Edital criado com sucesso!")
3. Como exibir erros de validação? Lista no topo do formulário? Inline em cada campo?
4. Deve haver confirmação antes de deletar edital? (ex: "Tem certeza que deseja deletar?")
5. Mensagens devem ser persistentes (permanecem após reload) ou temporárias (desaparecem após alguns segundos)?

**Decisão Tomada** ✅:

- Mensagens amigáveis para usuários finais
- Mensagens de sucesso após operações CRUD
- Exibir erros no canto inferior direito
- Confirmar antes de deletar ("Tem certeza?")
- Mensagens temporárias que desaparecem após alguns segundos

**Impacto na Implementação**:

- Mensagens amigáveis em português para usuários finais
- Mensagens técnicas em logs (para desenvolvedores)
- Mensagens de sucesso após criar/editar/deletar (ex: "Edital criado com sucesso!")
- Exibir mensagens de erro no canto inferior direito (usar toast notifications)
- Confirmação antes de deletar (modal JavaScript: "Tem certeza que deseja deletar este edital?")
- Mensagens temporárias (desaparecem após 5 segundos ou ao fechar)
- Erros de validação inline em cada campo do formulário
- Usar Django messages framework para mensagens de sucesso/erro

---

## 🔵 POST-IMPLEMENTATION - Questões Identificadas Durante Implementação

### CLAR-016: Funcionalidade de Export CSV ✅ RESOLVIDO

**Context**: Durante a implementação, foi adicionada uma funcionalidade de export CSV (`export_editais_csv()`) que não estava na especificação original.

**Questions**:

1. A funcionalidade de export CSV deve ser mantida no MVP?
2. Se mantida, deve ser acessível apenas para administradores ou também para usuários autenticados?
3. Quais campos devem ser incluídos no CSV exportado?
4. Deve haver filtros aplicados ao export (mesmos filtros da listagem)?
5. Deve ser adicionada à especificação oficial?

**Decisão Tomada** ✅:

- **Manter funcionalidade de export CSV no MVP**
- **Acesso restrito a usuários autenticados** (via `@login_required`)
- **Campos incluídos**: Número, Título, Entidade, Status, URL, Data Criação, Data Atualização, Criado Por, Atualizado Por
- **Filtros aplicados**: Mesmos filtros da página de listagem (busca, status)
- **Formato**: CSV com encoding UTF-8 (BOM para compatibilidade com Excel)
- **Adicionar à especificação**: Sim, como funcionalidade opcional do MVP

**Impacto na Implementação**:

- Funcionalidade já implementada e funcional
- Adicionar à spec.md como funcionalidade opcional
- Documentar no README.md
- Manter acesso restrito a usuários autenticados
- Considerar adicionar permissões mais granulares no futuro (staff only)

---

### CLAR-017: Inconsistência em Paginação (12 vs 20 itens) ✅ RESOLVIDO

**Context**: A especificação mencionava "20 itens por página (padrão)", mas o código implementado usava `EDITAIS_PER_PAGE = 12`.

**Questions**:

1. Qual deve ser o valor padrão correto? 12 ou 20 itens por página?
2. A especificação deve ser atualizada para refletir 12 itens?
3. Ou o código deve ser atualizado para usar 20 itens?

**Decisão Tomada** ✅:

- **Padronizar para 12 itens por página** no MVP
- Atualizar `spec.md`, `plan.md`, `checklist.md` e demais referências para refletir 12 itens por página
- Manter `EDITAIS_PER_PAGE = 12` nas configurações do projeto

**Impacto na Implementação**:

- Atualizar documentação (spec.md, plan.md, analysis.md, checklist.md) para mencionar 12 itens por página
- Garantir que testes e templates considerem 12 itens como padrão
- Nenhuma alteração de código necessária (implementação já usa 12)

**Prioridade**: Média  
**Status**: ✅ Resolvido

---

### CLAR-018: Sistema de Permissões Avançado ✅ RESOLVIDO

**Context**: O sistema atual usava apenas `@login_required` (qualquer usuário autenticado podia criar/editar/deletar). A especificação mencionava sistema de permissões com múltiplos níveis (staff, editor, admin).

**Questions**:

1. O sistema de permissões avançado é crítico para o MVP?
2. Quais são os níveis exatos de permissão necessários?
3. Como implementar: Django Groups, Permissions customizadas, ou campo customizado no User?
4. Quando deve ser implementado: MVP ou fase futura?

**Decisão Tomada** ✅:

- **MVP**: Implementar apenas o básico — operações de criação/edição/remoção restritas a usuários `is_staff` (ou com permissão Django equivalente)
- **Usuários autenticados não-staff**: apenas visualizar listagem e detalhes
- **Fase futura**: Avaliar sistema completo de múltiplos níveis (staff, editor, admin) conforme roadmap

**Impacto na Implementação**:

- Atualizar views (`edital_create`, `edital_update`, `edital_delete`, `export_editais_csv`) para exigir `is_staff` ou permissões equivalentes
- Atualizar documentação (spec.md, plan.md, checklist.md) para refletir abordagem básica no MVP
- Manter nota no backlog para evolução futura do sistema de permissões

**Prioridade**: Alta  
**Status**: ✅ Resolvido

---

## 📋 Summary of Decisions

### Critical (Blocking) ✅ TODAS RESOLVIDAS

- [x] CLAR-001: Mapeamento de Status ✅
- [x] CLAR-002: Campos de Data vs. Cronograma ✅
- [x] CLAR-003: Mapeamento de Campos (description, requirements) ✅
- [x] CLAR-004: Geração Automática de Slug ✅

### High Priority ✅ TODAS RESOLVIDAS

- [x] CLAR-005: Funcionalidade de Busca ✅
- [x] CLAR-006: Comportamento de Filtros ✅

### Implementation Decisions ✅ TODAS IMPLEMENTADAS

- [x] IMPL-001: Slug Generation with Fallback ✅
- [x] IMPL-002: Cache Security (User Type Differentiation) ✅
- [x] IMPL-003: Status Update Logic (Deadline Day Inclusion) ✅
- [x] IMPL-004: Individual Save() Calls in Management Command ✅
- [x] IMPL-005: HTML Sanitization in Both Views and Admin ✅
- [x] IMPL-006: Project Queryset Filtering ✅
- [x] IMPL-007: Auto-Update Status Logic in save() Method ✅
- [x] CLAR-007: Validação de Upload de Anexos ✅ (Removido do MVP)
- [x] CLAR-008: Comportamento de Status e Datas ✅

### Medium Priority ✅ TODAS RESOLVIDAS

- [x] CLAR-009: Migração de URLs (PK → Slug) ✅
- [x] CLAR-010: Sistema de Favoritos (EditalFavorite) ✅ (Removido do MVP)
- [x] CLAR-011: Permissões e Autenticação ✅
- [x] CLAR-012: Paginação e Performance ✅
- [x] CLAR-013: Localização (Campo location) ✅ (Removido do MVP)

### Low Priority ✅ TODAS RESOLVIDAS

- [x] CLAR-014: Interface Administrativa ✅
- [x] CLAR-015: Mensagens de Erro e Validação ✅

### Post-Implementation

- [x] CLAR-016: Funcionalidade de Export CSV ✅ (Manter no MVP)
- [x] CLAR-017: Inconsistência em Paginação (12 vs 20) ✅ (Padronizar para 12)
- [x] CLAR-018: Sistema de Permissões Avançado ✅ (Restrito a `is_staff` no MVP)
- [x] CLAR-019: Inconsistência entre Rotas de Criação de Editais ✅ (Resolvido - Rota principal funcional)
- [x] CLAR-020: Project Model Nomenclature and Purpose ✅ (Clarificado - refatoração futura)
- [x] CLAR-021: Dashboard Route `/dashboard/editais/novo/` Implementation ✅ (Implementar com EditalForm)
- [x] CLAR-022: Status 'em_andamento' vs 'fechado' Distinction ✅ (Clarificado)
- [x] CLAR-023: Project Evaluation Workflow ✅ (Conceito incorreto - ver CLAR-020)
- [x] CLAR-024: Future Feature Prioritization ✅ (Sistema de notificações priorizado)

---

### CLAR-019: Inconsistência entre Rotas de Criação de Editais ✅ RESOLVIDO

**Context**: Existem duas rotas diferentes para criar editais:
- `/dashboard/editais/novo/` → view `dashboard_novo_edital` → template `dashboard/novo_edital.html` (não processa POST)
- `/cadastrar/` → view `edital_create` → template `editais/create.html` (processa POST corretamente)

**Decisão Tomada** ✅:

- **Rota principal**: `/cadastrar/` com view `edital_create` é a rota funcional que processa POST
- **Rota dashboard**: `/dashboard/editais/novo/` é apenas uma página placeholder que renderiza template sem processar POST
- **Template funcional**: `editais/create.html` com `EditalForm` é o template usado para criação
- **Template dashboard**: `dashboard/novo_edital.html` é um placeholder para futura integração no dashboard
- **Status atual**: Sistema funcional usa `/cadastrar/` para criação. Rota `/dashboard/editais/novo/` pode ser implementada no futuro para integração completa no dashboard

**Impacto na Implementação**:

- ✅ Rota `/cadastrar/` implementada e funcional com `EditalForm`
- ✅ View `edital_create` processa POST corretamente com validação e sanitização
- ⏳ Rota `/dashboard/editais/novo/` mantida como placeholder para futura implementação
- ✅ Sistema funcional e testado usando rota principal `/cadastrar/`

**Prioridade**: Alta  
**Status**: ✅ Resolvido (Implementação funcional confirmada)

---

### CLAR-020: Project Model Nomenclature and Purpose ✅ RESOLVIDO

**Context**: O modelo `Project` existe no código, mas sua nomenclatura e propósito não estão claros na especificação. O modelo representa propostas de startups para a incubadora AgroHub UniRV, não projetos submetidos a editais.

**Decisão Tomada** ✅:

- **Nomenclatura incorreta**: O termo "Project" não reflete a realidade - são propostas de startups (startup proposals)
- **Propósito**: É um showcase de propostas de startups da incubadora AgroHub UniRV, não um sistema de submissão
- **Acesso**: Apenas grupos específicos de usuários podem visualizar/gerenciar essas propostas
- **Não há submissão**: As propostas não são submetidas através do sistema - é apenas um showcase/exibição
- **Refatoração futura**: O modelo `Project` precisa ser renomeado e sua documentação atualizada para refletir que são propostas de startups da incubadora

**Impacto na Implementação**:

- ⏳ **Refatoração pendente**: Renomear modelo `Project` para `StartupProposal` ou `PropostaStartup` (futuro)
- ⏳ **Atualizar documentação**: Docstrings, verbose_name, help_text devem refletir que são propostas de startups
- ⏳ **Atualizar templates**: Templates devem usar terminologia correta (propostas de startups, não projetos)
- ✅ **Acesso restrito**: Manter restrição de acesso apenas para grupos específicos de usuários
- ✅ **Showcase**: Sistema funciona como showcase, não como sistema de submissão

**Prioridade**: Média (refatoração de nomenclatura pode ser feita em fase futura)  
**Status**: ✅ Resolvido (conceito clarificado, refatoração marcada para futuro)

---

### CLAR-021: Dashboard Route `/dashboard/editais/novo/` Implementation ✅ RESOLVIDO

**Context**: A rota `/dashboard/editais/novo/` existe com template mas não processa POST. A rota funcional é `/cadastrar/`.

**Decisão Tomada** ✅:

- **Implementar completamente**: A rota `/dashboard/editais/novo/` deve ser totalmente implementada para processar POST requests
- **Usar mesmo formulário**: Deve usar o mesmo `EditalForm` que a rota `/cadastrar/` para manter consistência
- **Integração no dashboard**: Esta rota permite integração completa da criação de editais no dashboard administrativo

**Impacto na Implementação**:

- ⏳ **Implementar view**: View `dashboard_novo_edital` deve processar POST requests
- ⏳ **Usar EditalForm**: Reutilizar `EditalForm` da rota `/cadastrar/`
- ⏳ **Validação e sanitização**: Aplicar mesma lógica de validação e sanitização HTML
- ⏳ **Redirecionamento**: Após criação bem-sucedida, redirecionar para dashboard ou detalhe do edital

**Prioridade**: Média  
**Status**: ✅ Resolvido (decisão tomada, implementação pendente)

---

### CLAR-022: Status 'em_andamento' vs 'fechado' Distinction ✅ RESOLVIDO

**Context**: Ambos os status indicam que o edital não está aceitando submissões, mas a distinção não estava clara.

**Decisão Tomada** ✅:

- **'em_andamento'**: Edital fechado para submissões mas ainda ativo/sendo processado
- **'fechado'**: Edital completamente encerrado/arquivado
- **Atualização automática**: Por enquanto manual, mas no futuro deve ser automática
- **Visibilidade**: Status 'em_andamento' deve ser visível nas listagens públicas (junto com 'aberto' e 'fechado')

**Impacto na Implementação**:

- ✅ **Distinção clara**: Documentar diferença entre os dois status
- ⏳ **Automação futura**: Implementar lógica automática para transição 'aberto' → 'em_andamento' → 'fechado' (futuro)
- ✅ **Visibilidade pública**: Manter 'em_andamento' visível nas listagens públicas

**Prioridade**: Baixa (já implementado, apenas documentação)  
**Status**: ✅ Resolvido

---

### CLAR-023: Project Evaluation Workflow ✅ RESOLVIDO

**Context**: O modelo `Project` tem campos `status` e `note`, mas o workflow de avaliação não estava definido.

**Decisão Tomada** ✅:

- **Conceito incorreto**: O conceito de "projetos" como submissões está incorreto
- **Realidade**: São propostas de startups da incubadora (showcase), não um sistema de avaliação de submissões
- **Refatoração necessária**: Ver CLAR-020 para detalhes sobre nomenclatura e propósito

**Impacto na Implementação**:

- ⏳ **Refatoração**: Renomear e redefinir propósito do modelo (ver CLAR-020)
- ⏳ **Remover workflow de avaliação**: Se não há submissões, não há workflow de avaliação de submissões
- ⏳ **Revisar campos**: Campos `status` e `note` podem não fazer sentido no contexto de showcase

**Prioridade**: Média (refatoração futura)  
**Status**: ✅ Resolvido (conceito clarificado)

---

### CLAR-024: Future Feature Prioritization ✅ RESOLVIDO

**Context**: Várias funcionalidades estão marcadas como "Out of Scope (Futuras Fases)" mas precisavam de decisão de priorização.

**Decisão Tomada** ✅:

- **Prioridade para próxima fase**: Sistema de notificações (email / in-app)
- **Não mover para MVP**: Nenhuma funcionalidade "out of scope" deve ser movida para o MVP atual
- **Sem timeline específica**: Não há timeline definida para implementação das funcionalidades futuras

**Impacto na Implementação**:

- ⏳ **Sistema de notificações**: Planejar e implementar em próxima fase
- ✅ **Manter escopo**: Manter funcionalidades "out of scope" fora do MVP
- ✅ **Flexibilidade**: Timeline flexível para funcionalidades futuras

**Prioridade**: Baixa (planejamento futuro)  
**Status**: ✅ Resolvido

---

## ✅ Status: Clarificações Principais Resolvidas

**Data de Resolução Inicial**: 2025-11-11  
**Última Atualização**: 2025-01-15

**Clarificações Resolvidas**: 24/24 (100%)

- ✅ 15 clarificações iniciais resolvidas
- ✅ 4 clarificações pós-implementação resolvidas (CLAR-016, CLAR-017, CLAR-018, CLAR-019)
- ✅ 5 clarificações adicionais resolvidas (CLAR-020, CLAR-021, CLAR-022, CLAR-023, CLAR-024)
- ✅ 7 decisões de implementação documentadas (IMPL-001 a IMPL-007)

**Status**: ✅ Todas as clarificações resolvidas. Implementação completa e funcional.

---

## Implementation Decisions (From Codebase)

### IMPL-001: Slug Generation with Fallback ✅ IMPLEMENTED

**Context**: Slug generation must handle edge cases where slugify returns empty string.

**Decision**: 
- If slugify returns empty string, use fallback: `edital-{pk}` for existing objects or `edital-{timestamp}` for new objects
- Use regex pattern matching to avoid false matches (e.g., "editable" when base_slug is "edit")
- Safety limit of 10000 attempts to prevent infinite loops
- If limit reached, append timestamp to ensure uniqueness

**Implementation**: `editais/models.py` - `_generate_unique_slug()` method

---

### IMPL-002: Cache Security (User Type Differentiation) ✅ IMPLEMENTED

**Context**: Cache must prevent cache poisoning between different user types.

**Decision**:
- Use different cache keys for different user types: `staff`, `auth` (authenticated non-staff), `public` (unauthenticated)
- This prevents CSRF token leakage and ensures staff users don't see cached 404 responses from public users
- Manual caching instead of `@cache_page` decorator to have fine-grained control

**Implementation**: `editais/views.py` - `edital_detail()` function

---

### IMPL-003: Status Update Logic (Deadline Day Inclusion) ✅ IMPLEMENTED

**Context**: When should editais be closed? On the deadline day or after?

**Decision**:
- Editais remain open throughout the entire deadline day (`end_date <= today` closes them)
- This means editais ending today are still considered open until the day passes
- Management command uses `end_date__lte=today` to close editais including deadline day

**Implementation**: `editais/services.py` - `update_status_by_dates()` method, `editais/management/commands/update_edital_status.py`

---

### IMPL-004: Individual Save() Calls in Management Command ✅ IMPLEMENTED

**Context**: Management command needs to handle errors for individual editais during bulk updates.

**Decision**:
- Use individual `save()` calls instead of `bulk_update()` to allow error handling per edital
- This enables tests that patch `Edital.save()` to catch exceptions
- Errors are collected and reported at the end of the command execution

**Implementation**: `editais/management/commands/update_edital_status.py`

---

### IMPL-005: HTML Sanitization in Both Views and Admin ✅ IMPLEMENTED

**Context**: HTML sanitization must be consistent across web views and Django Admin.

**Decision**:
- Sanitize HTML in both views (`edital_create`, `edital_update`) and Django Admin (`save_model()`)
- Use bleach with allowed tags and attributes defined in `utils.py`
- Mark sanitized HTML as safe for rendering using `mark_safe()`

**Implementation**: `editais/utils.py`, `editais/views.py`, `editais/admin.py`

---

### IMPL-006: Project Queryset Filtering ✅ IMPLEMENTED

**Context**: Projects with missing relationships (edital or proponente) should be filtered at queryset level.

**Decision**:
- Filter out projects with missing relationships at queryset level using `.filter(edital__isnull=False, proponente__isnull=False)`
- This ensures stats match displayed projects and prevents errors in templates
- Additional safety checks in view code to skip projects with missing relationships

**Implementation**: `editais/views.py` - `dashboard_projetos()` function

---

### IMPL-007: Auto-Update Status Logic in save() Method ✅ IMPLEMENTED

**Context**: Status should be automatically updated based on dates when saving an edital, but must handle edge cases.

**Decision**:
- Draft status is never auto-updated (manually controlled)
- Status 'em_andamento' is not auto-updated (preserved)
- Handle different date scenarios:
  - Both start_date and end_date: Update based on date range
  - Only start_date (fluxo contínuo): Update based on start_date only
  - Only end_date: Update based on end_date only
- Include deadline day in date range checks (start_date <= today <= end_date)
- Use retry logic (max 3 attempts) for slug uniqueness race conditions

**Implementation**: `editais/models.py` - `save()` method

---

## Next Steps

1. ✅ **Decisões Tomadas**: 24/24 clarificações resolvidas (100%)
2. ✅ **Implementation Decisions**: 7 decisões de implementação documentadas (IMPL-001 a IMPL-007)
3. ✅ **Implementation Complete**: Todas as funcionalidades implementadas e testadas (95% - 85/89 tasks)
4. ⏳ **Documentation**: README de produção pendente
5. ⏳ **Coverage**: Verificar cobertura de testes ≥ 85%

---

## Principais Mudanças do MVP

### Removido do MVP

- ❌ Upload de anexos (CLAR-007)
- ❌ Sistema de favoritos (CLAR-010)
- ❌ Filtro de localização (CLAR-013)
- ❌ Campos em inglês (description, requirements) - usar apenas campos em português (CLAR-003)

### Adicionado ao MVP

- ✅ Status 'draft' (rascunho) e 'programado' (CLAR-001, CLAR-008)
- ✅ Atualização automática de status baseada em datas (CLAR-008)
- ✅ Sistema de permissões com múltiplos níveis (CLAR-011)
- ✅ Cache para listagens públicas (CLAR-012)
- ✅ Preview de edital no Django Admin (CLAR-014)
- ✅ Mensagens toast (canto inferior direito) (CLAR-015)
- ✅ Export CSV de editais (CLAR-016)

### Mudanças Importantes

- ✅ Slug automático, não editável (CLAR-004)
- ✅ Todos os campos em português (CLAR-003)
- ✅ Manter modelo Cronograma + adicionar start_date/end_date ao Edital (CLAR-002)
- ✅ Busca case-insensitive, modo "contém" (CLAR-005)
- ✅ Filtros combinados com AND, persistir na URL (CLAR-006)
