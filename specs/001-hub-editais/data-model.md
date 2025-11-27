# Modelo de Dados — Hub de Editais

**Versão:** 1.0  
**Data:** 2025-11-27  
**Autor:** Sistema Spec Kit (Rebuild from Codebase)  
**Fase:** 1 – Modelagem de Dados  

---

## 1. Entidades principais

### 🗂️ Edital

| Campo | Tipo | Descrição | Obrigatório | Único | Índice |
|--------|------|-----------|-------------|-------|--------|
| id | AutoField | Identificador único | Sim | Sim | PK |
| numero_edital | CharField(100) | Número do edital | Não | Não | Sim (idx_numero) |
| titulo | CharField(500) | Nome do edital | Sim | Não | Sim (idx_titulo) |
| slug | SlugField(255) | Slug único gerado automaticamente | Sim | Sim | Sim (idx_slug) |
| url | URLField(1000) | Link externo do edital | Sim | Não | Não |
| entidade_principal | CharField(200) | Órgão fomentador | Não | Não | Sim (idx_entidade) |
| status | CharField(20) | Status do edital | Sim | Não | Sim (idx_status) |
| start_date | DateField | Data de abertura | Não | Não | Sim (idx_status_dates) |
| end_date | DateField | Data de encerramento geral | Não | Não | Sim (idx_status_dates) |
| data_criacao | DateTimeField | Data de criação | Sim | Não | Sim (idx_data_atualizacao) |
| data_atualizacao | DateTimeField | Última atualização | Sim | Não | Sim (idx_data_atualizacao) |
| created_by | FK(User) | Autor / administrador | Não | Não | Não |
| updated_by | FK(User) | Último usuário que atualizou | Não | Não | Não |
| analise | TextField | Análise do edital | Não | Não | Não |
| objetivo | TextField | Objetivo do edital | Não | Não | Não |
| etapas | TextField | Etapas do edital | Não | Não | Não |
| recursos | TextField | Recursos disponíveis | Não | Não | Não |
| itens_financiaveis | TextField | Itens financiáveis | Não | Não | Não |
| criterios_elegibilidade | TextField | Critérios de participação | Não | Não | Não |
| criterios_avaliacao | TextField | Critérios de avaliação | Não | Não | Não |
| itens_essenciais_observacoes | TextField | Itens essenciais e observações | Não | Não | Não |
| detalhes_unirv | TextField | Detalhes específicos da UniRV | Não | Não | Não |

#### Status Choices

| Valor | Label | Descrição | Visibilidade Pública |
|-------|-------|-----------|---------------------|
| draft | Rascunho | Edital em rascunho | Não (apenas usuários staff) |
| aberto | Aberto | Edital aceitando submissões | Sim |
| em_andamento | Em Andamento | Edital em processo de avaliação | Sim |
| fechado | Fechado | Edital encerrado (histórico) | Sim |
| programado | Programado | Edital com data de início no futuro | Sim |

#### Métodos e Propriedades

- `_generate_unique_slug()`: Gera slug único a partir do título
- `clean()`: Validação de datas (end_date >= start_date)
- `save()`: Auto-atualização de status baseado em datas, geração de slug
- `get_summary()`: Retorna resumo do objetivo (primeiros 200 caracteres)
- `is_open()`: Verifica se status é 'aberto'
- `is_closed()`: Verifica se status é 'fechado'
- `days_until_deadline` (property): Retorna dias até o prazo ou None
- `is_deadline_imminent` (property): True se prazo está dentro de 7 dias
- `can_edit(user)`: Verifica se usuário pode editar (staff ou criador)
- `get_absolute_url()`: Retorna URL usando slug ou PK

#### Regras de Negócio

1. **Slug**: Gerado automaticamente a partir do título usando `slugify()`. Se duplicado, adiciona sufixo numérico (-2, -3, etc.). Não editável manualmente (editable=False). Nunca pode ser None após save.

2. **Status Automático no save()**: 
   - Se `start_date > hoje` e status não é 'draft' ou 'programado', define status='programado'
   - Se `start_date <= hoje <= end_date` e status='programado', define status='aberto'
   - Se `end_date < hoje` e status='aberto', define status='fechado'
   - Status 'draft' nunca é alterado automaticamente
   - Status 'em_andamento' não é alterado automaticamente

3. **Management Command**: `update_edital_status` atualiza status em lote baseado em datas:
   - Fecha editais com `end_date <= hoje` e status='aberto'
   - Programa editais com `start_date > hoje` (exceto draft e já programados)
   - Abre editais com `start_date <= hoje <= end_date` e status='programado'

4. **Validação de Datas**: `end_date` deve ser posterior a `start_date` (validado em `clean()`)

5. **Auditoria**: Campos `created_by` e `updated_by` rastreiam quem criou e atualizou cada edital (SET_NULL se usuário deletado)

6. **Ordenação Padrão**: Ordenado por `-data_atualizacao` (mais recentes primeiro)

---

### 📅 Cronograma

| Campo | Tipo | Descrição | Obrigatório | Único | Índice |
|--------|------|-----------|-------------|-------|--------|
| id | AutoField | Identificador único | Sim | Sim | PK |
| edital | FK(Edital) | Relação com edital | Sim | Não | Sim (idx_cronograma_edital_data) |
| data_inicio | DateField | Início da etapa | Não | Não | Sim (idx_cronograma_data_inicio) |
| data_fim | DateField | Fim da etapa | Não | Não | Não |
| data_publicacao | DateField | Data de publicação | Não | Não | Não |
| descricao | CharField(300) | Descrição da etapa | Não | Não | Não |

#### Regras de Negócio

1. **Relacionamento**: Um Edital pode ter múltiplos Cronogramas (um para muitos, related_name='cronogramas')
2. **Cascata**: Ao deletar um Edital, todos os Cronogramas associados são deletados (CASCADE)
3. **Ordenação**: Cronogramas ordenados por `data_inicio` (crescente)
4. **Índices**: 
   - `idx_cronograma_edital_data`: Índice composto em (edital, data_inicio)
   - `idx_cronograma_data_inicio`: Índice em data_inicio

---

### 💰 EditalValor

| Campo | Tipo | Descrição | Obrigatório | Único | Índice |
|--------|------|-----------|-------------|-------|--------|
| id | AutoField | Identificador único | Sim | Sim | PK |
| edital | FK(Edital) | Relação com edital | Sim | Não | Sim (idx_edital_moeda) |
| valor_total | DecimalField(15,2) | Valor total do edital | Não | Não | Não |
| moeda | CharField(10) | Moeda (padrão: BRL) | Sim | Não | Sim (idx_edital_moeda) |

#### Moeda Choices

| Valor | Label |
|-------|-------|
| BRL | Real Brasileiro (R$) |
| USD | Dólar Americano (US$) |
| EUR | Euro (€) |

#### Regras de Negócio

1. **Relacionamento**: Um Edital pode ter múltiplos EditalValor (um para muitos, related_name='valores')
2. **Cascata**: Ao deletar um Edital, todos os EditalValor associados são deletados (CASCADE)
3. **Moeda**: Padrão é 'BRL' (Real Brasileiro)
4. **Índice**: `idx_edital_moeda`: Índice composto em (edital, moeda) para queries otimizadas

---

### 📝 EditalHistory

| Campo | Tipo | Descrição | Obrigatório | Único | Índice |
|--------|------|-----------|-------------|-------|--------|
| id | AutoField | Identificador único | Sim | Sim | PK |
| edital | FK(Edital) | Relação com edital (pode ser NULL se deletado) | Não | Não | Sim (idx_edital_timestamp) |
| edital_titulo | CharField(500) | Título preservado quando edital é deletado | Não | Não | Não |
| user | FK(User) | Usuário que realizou a ação | Não | Não | Não |
| action | CharField(20) | Tipo de ação | Sim | Não | Não |
| field_name | CharField(100) | Nome do campo alterado (legado) | Não | Não | Não |
| old_value | TextField | Valor antigo (legado) | Não | Não | Não |
| new_value | TextField | Valor novo (legado) | Não | Não | Não |
| timestamp | DateTimeField | Data e hora da ação | Sim | Não | Sim (idx_timestamp) |
| changes_summary | JSONField | Resumo das mudanças em formato JSON | Sim | Não | Não |

#### Action Choices

| Valor | Label |
|-------|-------|
| create | Criado |
| update | Atualizado |
| delete | Excluído |

#### Regras de Negócio

1. **Relacionamento**: Um Edital pode ter múltiplos EditalHistory (um para muitos, related_name='history')
2. **Preservação**: Ao deletar um Edital, o histórico é preservado (SET_NULL em edital, preserva edital_titulo)
3. **Ordenação**: Histórico ordenado por `-timestamp` (mais recentes primeiro)
4. **Índices**: 
   - `idx_timestamp`: Índice em timestamp (decrescente)
   - `idx_edital_timestamp`: Índice composto em (edital, timestamp decrescente)
5. **changes_summary**: Armazena mudanças em formato JSON com estrutura: `{'campo': {'old': 'valor_antigo', 'new': 'valor_novo'}}`

---

### 🚀 Project

**⚠️ NOTA IMPORTANTE (CLAR-020)**: O modelo `Project` usa nomenclatura incorreta. Na realidade, representa **propostas de startups da incubadora AgroHub UniRV** (showcase), não projetos submetidos a editais. Não há sistema de submissão - é apenas um showcase/exibição. Acesso restrito a grupos específicos de usuários. **REFATORAÇÃO FUTURA**: Renomear para `StartupProposal` ou `PropostaStartup` e atualizar toda documentação.

| Campo | Tipo | Descrição | Obrigatório | Único | Índice |
|--------|------|-----------|-------------|-------|--------|
| id | AutoField | Identificador único | Sim | Sim | PK |
| name | CharField(200) | Nome da proposta de startup | Sim | Não | Não |
| edital | FK(Edital) | Edital relacionado | Sim | Não | Sim (idx_project_edital_status) |
| proponente | FK(User) | Usuário responsável pela proposta | Sim | Não | Sim (idx_project_proponente) |
| submitted_on | DateTimeField | Data de registro/exibição | Sim | Não | Sim (idx_project_submitted) |
| status | CharField(20) | Status atual | Sim | Não | Sim (idx_project_status) |
| note | DecimalField(5,2) | Nota/score da proposta | Não | Não | Não |
| data_criacao | DateTimeField | Data de criação | Sim | Não | Não |
| data_atualizacao | DateTimeField | Última atualização | Sim | Não | Não |

#### Status Choices

| Valor | Label |
|-------|-------|
| em_avaliacao | Em Avaliação |
| aprovado | Aprovado |
| reprovado | Reprovado |
| pendente | Pendente |

#### Regras de Negócio

1. **Relacionamento**: Um Edital pode ter múltiplas propostas de startups associadas (um para muitos, related_name='projetos') - **NOTA**: Ver CLAR-020 sobre nomenclatura
2. **Cascata**: Ao deletar um Edital, todas as propostas associadas são deletadas (CASCADE)
3. **Ordenação**: Propostas ordenadas por `-submitted_on` (mais recentes primeiro)
4. **Índices**: 
   - `idx_project_submitted`: Índice em submitted_on (decrescente)
   - `idx_project_status`: Índice em status
   - `idx_project_edital_status`: Índice composto em (edital, status)
   - `idx_project_proponente`: Índice em proponente

---

### 👤 User (Django User)

| Campo | Tipo | Descrição | Obrigatório | Único | Índice |
|--------|------|-----------|-------------|-------|--------|
| id | AutoField | Identificador único | Sim | Sim | PK |
| username | CharField(150) | Nome de usuário | Sim | Sim | Sim |
| email | EmailField | Email do usuário | Sim | Não | Não |
| first_name | CharField(150) | Primeiro nome | Sim | Não | Não |
| last_name | CharField(150) | Sobrenome | Sim | Não | Não |
| is_staff | BooleanField | É staff? | Sim | Não | Não |
| is_superuser | BooleanField | É superusuário? | Sim | Não | Não |
| date_joined | DateTimeField | Data de cadastro | Sim | Não | Não |
| last_login | DateTimeField | Último login | Não | Não | Não |

#### Níveis de Acesso

| Nível | Permissões | Descrição |
|-------|------------|-----------|
| staff | is_staff=True | Pode acessar dashboard e criar/editar/deletar editais |
| regular | is_staff=False | Pode visualizar editais públicos (acesso a propostas de startups restrito a grupos específicos) |
| superuser | is_superuser=True | Acesso total ao sistema |

#### Regras de Negócio

1. **Permissões**: Usuários com `is_staff=True` podem criar, editar e deletar editais
2. **Rascunhos**: Apenas usuários staff podem visualizar editais em status 'draft'
3. **Auditoria**: Campos `created_by` e `updated_by` em Edital referenciam User (SET_NULL se deletado)
4. **Propostas de Startups**: Propostas de startups da incubadora são exibidas em showcase (relacionamento através de Project). Acesso restrito a grupos específicos. **NOTA**: Ver CLAR-020 sobre nomenclatura e propósito.

---

## 2. Relacionamentos

### Diagrama de Relacionamentos

```
User (1) ────< (N) Edital (created_by, updated_by)
User (1) ────< (N) EditalHistory (user)
User (1) ────< (N) Project (proponente)
Edital (1) ────< (N) Cronograma (edital)
Edital (1) ────< (N) EditalValor (edital)
Edital (1) ────< (N) EditalHistory (edital)
Edital (1) ────< (N) Project (edital)
```

### Descrição dos Relacionamentos

1. **User → Edital (created_by)**: Um usuário pode criar múltiplos editais. Se o usuário for deletado, `created_by` é definido como NULL (SET_NULL).

2. **User → Edital (updated_by)**: Um usuário pode atualizar múltiplos editais. Se o usuário for deletado, `updated_by` é definido como NULL (SET_NULL).

3. **User → EditalHistory (user)**: Um usuário pode ter múltiplas ações no histórico. Se o usuário for deletado, `user` é definido como NULL (SET_NULL).

4. **User → Project (proponente)**: Um usuário pode ter múltiplas propostas de startups associadas. Se o usuário for deletado, todas as propostas são deletadas (CASCADE). **NOTA**: Ver CLAR-020 sobre nomenclatura.

5. **Edital → Cronograma**: Um edital pode ter múltiplos cronogramas (etapas). Ao deletar um edital, todos os cronogramas são deletados (CASCADE).

6. **Edital → EditalValor**: Um edital pode ter múltiplos valores (diferentes moedas ou valores parciais). Ao deletar um edital, todos os valores são deletados (CASCADE).

7. **Edital → EditalHistory**: Um edital pode ter múltiplas entradas de histórico. Ao deletar um edital, o histórico é preservado mas `edital` é definido como NULL (SET_NULL).

8. **Edital → Project**: Um edital pode ter múltiplas propostas de startups associadas (showcase). Ao deletar um edital, todas as propostas são deletadas (CASCADE). **NOTA**: Ver CLAR-020 sobre nomenclatura e propósito.

---

## 3. Regras de negócio

### Geração de Slug

1. **Algoritmo**: Usar `django.utils.text.slugify()` para gerar slug a partir do título
2. **Remoção de Acentos**: Acentos são removidos automaticamente pelo slugify
3. **Unicidade**: Se o slug gerado já existe, adicionar sufixo numérico (-2, -3, etc.) até encontrar um único
4. **Fallback**: Se slugify retorna string vazia, usar `edital-{pk}` ou `edital-{timestamp}` como fallback
5. **Edição**: Slug não pode ser editado manualmente (editable=False, gerado apenas na criação)
6. **Persistência**: Se o título mudar, o slug não muda (para preservar links existentes)
7. **Validação**: Slug nunca pode ser None após save (validação no método save())

### Atualização Automática de Status

1. **No método save() do modelo**:
   - Se `start_date > hoje` e status não é 'draft' ou 'programado', define status='programado'
   - Se `start_date <= hoje <= end_date` e status='programado', define status='aberto'
   - Se `end_date < hoje` e status='aberto', define status='fechado'
   - Status 'draft' nunca é alterado automaticamente
   - Status 'em_andamento' não é alterado automaticamente

2. **Management Command `update_edital_status`**:
   - Fecha editais com `end_date <= hoje` e status='aberto'
   - Programa editais com `start_date > hoje` (exceto draft e já programados)
   - Abre editais com `start_date <= hoje <= end_date` e status='programado'
   - Deve ser executado diariamente via cron/task scheduler

3. **Aviso "Prazo Próximo"**: Editais com `end_date` nos próximos 7 dias exibem aviso visual na listagem pública (propriedade `is_deadline_imminent`)

### Validação de Datas

1. **Validação**: `end_date` deve ser posterior a `start_date` (validado em `clean()`)
2. **Campos Opcionais**: `start_date` e `end_date` são opcionais (blank=True, null=True)
3. **Fluxo Contínuo**: Editais sem `end_date` são considerados "Fluxo Contínuo"
4. **Cronograma**: Datas de cronograma são independentes das datas do edital

### Permissões e Visibilidade

1. **Rascunhos**: Editais com status 'draft' são visíveis apenas para usuários com `is_staff=True`
2. **Público**: Editais com status 'aberto', 'em_andamento', 'fechado', 'programado' são visíveis publicamente
3. **CRUD**: Apenas usuários com `is_staff=True` podem criar, editar e deletar editais
4. **Administração**: Usuários staff podem ver todos os editais (incluindo rascunhos) no Django Admin

### Auditoria

1. **Criação**: Campo `created_by` rastreia quem criou o edital (definido automaticamente em views e admin)
2. **Atualização**: Campo `updated_by` rastreia quem atualizou o edital pela última vez (definido automaticamente em views e admin)
3. **Timestamps**: Campos `data_criacao` e `data_atualizacao` rastreiam quando o edital foi criado e atualizado (auto_now_add e auto_now)
4. **Histórico**: EditalHistory registra todas as ações (create, update, delete) com detalhes das mudanças

### Exclusão em Cascata

1. **Cronograma**: Ao deletar um Edital, todos os Cronogramas associados são deletados (CASCADE)
2. **EditalValor**: Ao deletar um Edital, todos os EditalValor associados são deletados (CASCADE)
3. **Project**: Ao deletar um Edital, todos os Projects associados são deletados (CASCADE)
4. **EditalHistory**: Ao deletar um Edital, o histórico é preservado mas `edital` é definido como NULL (SET_NULL)

### Sanitização de HTML

1. **Campos HTML**: Campos `analise`, `objetivo`, `etapas`, `recursos`, `itens_financiaveis`, `criterios_elegibilidade`, `criterios_avaliacao`, `itens_essenciais_observacoes`, `detalhes_unirv` são sanitizados com bleach
2. **Tags Permitidas**: p, br, strong, em, u, h1-h6, ul, ol, li, blockquote, a, code, pre, table, thead, tbody, tr, th, td, div, span
3. **Atributos Permitidos**: href, title, target, rel (para links), class, id (para div/span)
4. **Aplicação**: Sanitização aplicada em views (create/update) e Django Admin (save_model)

---

## 4. Índices e otimização

### Índices Existentes no Modelo Edital

| Índice | Campos | Descrição |
|--------|--------|-----------|
| idx_data_atualizacao | -data_atualizacao | Ordenação por data de atualização (decrescente) |
| idx_status | status | Filtro por status |
| idx_entidade | entidade_principal | Busca por entidade fomentadora |
| idx_numero | numero_edital | Busca por número do edital |
| idx_slug | slug | Busca por slug (único) |
| idx_status_dates | status, start_date, end_date | Filtro por status e datas |
| idx_titulo | titulo | Busca por título |

### Índices em Outros Modelos

| Modelo | Índice | Campos | Descrição |
|--------|--------|--------|-----------|
| Cronograma | idx_cronograma_edital_data | edital, data_inicio | Filtro por edital e data |
| Cronograma | idx_cronograma_data_inicio | data_inicio | Filtro por data de início |
| EditalValor | idx_edital_moeda | edital, moeda | Filtro por edital e moeda |
| EditalHistory | idx_timestamp | -timestamp | Ordenação por timestamp |
| EditalHistory | idx_edital_timestamp | edital, -timestamp | Filtro por edital e timestamp |
| Project | idx_project_submitted | -submitted_on | Ordenação por data de submissão |
| Project | idx_project_status | status | Filtro por status |
| Project | idx_project_edital_status | edital, status | Filtro por edital e status |
| Project | idx_project_proponente | proponente | Filtro por proponente |

### Estratégias de Otimização

1. **Queries Otimizadas**:
   - Usar `select_related()` para `created_by` e `updated_by` (ForeignKeys)
   - Usar `prefetch_related()` para `cronogramas`, `valores`, `history` (reverse ForeignKeys)
   - Usar `only()` para limitar campos retornados em listagens
   - Usar índices para campos de busca e filtros frequentes

2. **Cache**:
   - Cache de listagens públicas (TTL: 5 minutos, CACHE_TTL_INDEX=300)
   - Cache de páginas de detalhe (TTL: 15 minutos)
   - Cache versionado para invalidação eficiente (cache versioning pattern)
   - Invalidar cache quando editais são criados/editados/deletados

3. **Paginação**:
   - Paginação padrão de 12 itens por página (PAGINATION_DEFAULT=12)
   - Configurável via settings.EDITAIS_PER_PAGE

4. **Rate Limiting**:
   - Rate limiting em views de criação/edição/exclusão (5 requisições por minuto por IP)
   - Implementado via decorator `@rate_limit`

---

## 5. Exemplo de instância JSON

### Edital Completo

```json
{
  "id": 1,
  "numero_edital": "001/2025",
  "titulo": "Edital de Inovação Agro 2025",
  "slug": "edital-de-inovacao-agro-2025",
  "url": "https://exemplo.gov.br/edital/001-2025",
  "entidade_principal": "AgroHub UniRV",
  "status": "aberto",
  "start_date": "2025-01-10",
  "end_date": "2025-03-10",
  "data_criacao": "2025-01-05T10:00:00Z",
  "data_atualizacao": "2025-01-05T10:00:00Z",
  "created_by": 1,
  "updated_by": 1,
  "objetivo": "Fomentar projetos de inovação agrícola desenvolvidos por startups incubadas na UniRV.",
  "criterios_elegibilidade": "Podem participar startups incubadas na UniRV, professores e alunos da universidade.",
  "analise": "Análise detalhada do edital...",
  "etapas": "1. Inscrição\n2. Análise\n3. Seleção\n4. Execução",
  "recursos": "Recursos disponíveis para projetos selecionados...",
  "itens_financiaveis": "Equipamentos, materiais, serviços...",
  "criterios_avaliacao": "Critérios de avaliação dos projetos...",
  "itens_essenciais_observacoes": "Itens essenciais e observações importantes...",
  "detalhes_unirv": "Detalhes específicos da UniRV...",
  "cronogramas": [
    {
      "id": 1,
      "data_inicio": "2025-01-10",
      "data_fim": "2025-02-10",
      "data_publicacao": "2025-01-05",
      "descricao": "Período de inscrição"
    },
    {
      "id": 2,
      "data_inicio": "2025-02-11",
      "data_fim": "2025-02-28",
      "data_publicacao": null,
      "descricao": "Período de análise"
    }
  ],
  "valores": [
    {
      "id": 1,
      "valor_total": "100000.00",
      "moeda": "BRL"
    }
  ],
  "history": [
    {
      "id": 1,
      "action": "create",
      "user": 1,
      "timestamp": "2025-01-05T10:00:00Z",
      "changes_summary": {"titulo": "Edital de Inovação Agro 2025"}
    }
  ],
  "projetos": [
    {
      "id": 1,
      "name": "Projeto de Inovação Agrícola",
      "proponente": 2,
      "submitted_on": "2025-01-15T14:30:00Z",
      "status": "em_avaliacao",
      "note": null
    }
  ]
}
```

### Edital Mínimo (Campos Obrigatórios)

```json
{
  "titulo": "Edital de Inovação Agro 2025",
  "url": "https://exemplo.gov.br/edital/001-2025",
  "status": "draft"
}
```

**Nota**: Campos `slug`, `data_criacao`, `data_atualizacao` são preenchidos automaticamente.

---

## 6. Migrações Aplicadas

### Migration 0001_initial.py
- Criação inicial dos modelos Edital, Cronograma, EditalValor

### Migration 0002_edital_analise.py
- Adição do campo `analise` ao modelo Edital

### Migration 0003_alter_cronograma_options_alter_edital_options_and_more.py
- Ajustes em Meta options e verbose names

### Migration 0004_edital_idx_data_atualizacao_edital_idx_status_and_more.py
- Adição de índices iniciais (idx_data_atualizacao, idx_status, idx_entidade, idx_numero)

### Migration 0005_add_slug_and_dates.py
- Adição dos campos `slug`, `start_date`, `end_date`
- Adição do índice `idx_slug`

### Migration 0006_populate_slugs.py
- Data migration para popular slugs existentes

### Migration 0007_editalhistory_delete_editalfavorite_and_more.py
- Criação do modelo EditalHistory
- Remoção do modelo EditalFavorite (funcionalidade removida do MVP)

### Migration 0008_editalhistory_edital_titulo_and_more.py
- Adição do campo `edital_titulo` ao EditalHistory
- Tornar `edital` nullable em EditalHistory (SET_NULL)

### Migration 0009_improve_database_structure.py
- Adição de índices adicionais (idx_status_dates, idx_titulo)
- Adição de índices em Cronograma e EditalValor
- Melhorias na estrutura do banco

### Migration 0010_create_project_model.py
- Criação do modelo Project
- Adição de índices em Project

---

## 7. Validações

### Validações de Modelo

1. **Slug**: Único, gerado automaticamente, não editável, nunca pode ser None
2. **Datas**: `end_date` deve ser posterior a `start_date` (validado em `clean()`)
3. **Status**: Deve estar entre as opções válidas (draft, aberto, em_andamento, fechado, programado)
4. **Título**: Obrigatório, máximo 500 caracteres
5. **URL**: Obrigatória, máximo 1000 caracteres, deve ser uma URL válida

### Validações de Formulário

1. **Campos Obrigatórios**: título, url, status
2. **Campos Opcionais**: Todos os outros campos
3. **Sanitização**: Campos de texto HTML são sanitizados com bleach para prevenir XSS
4. **Validação de Datas**: Formulário valida que end_date >= start_date (em `clean()`)

### Validações de Segurança

1. **XSS Prevention**: Todos os campos HTML são sanitizados antes de salvar (views e admin)
2. **Permissões**: Apenas usuários staff podem criar/editar/deletar editais
3. **Rate Limiting**: Limitação de requisições em views de modificação (5 por minuto por IP)
4. **Cache Security**: Cache diferenciado por tipo de usuário (staff, auth, public) para prevenir cache poisoning

---

## 8. Referências

- [Django Models Documentation](https://docs.djangoproject.com/en/5.2/topics/db/models/)
- [Django Migrations Documentation](https://docs.djangoproject.com/en/5.2/topics/migrations/)
- Especificação completa: [spec.md](./spec.md)
- Clarificações: [clarifications.md](./clarifications.md)
- Plano de implementação: [plan.md](./plan.md)
- Pesquisa: [research.md](./research.md)
- Análise: [analysis.md](./analysis.md)
