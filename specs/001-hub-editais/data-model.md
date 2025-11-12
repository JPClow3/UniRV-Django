# Modelo de Dados — Hub de Editais

**Versão:** 0.1  
**Data:** 2025-11-11  
**Autor:** João Paulo G. Santos  
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
| url | URLField(1000) | Link externo do edital | Não | Não | Não |
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
| draft | Rascunho | Edital em rascunho | Não (apenas usuários com permissão CRUD) |
| aberto | Aberto | Edital aceitando submissões | Sim |
| em_andamento | Em Andamento | Edital fechado para submissões | Sim |
| fechado | Fechado | Edital encerrado (histórico) | Sim |
| programado | Programado | Edital com data de início no futuro | Sim |

#### Regras de Negócio

1. **Slug**: Gerado automaticamente a partir do título usando `slugify()`, removendo acentos. Se duplicado, adicionar sufixo numérico (-2, -3, etc.). Não editável manualmente.

2. **Status Automático**: 
   - Se `start_date > hoje` e status='aberto', definir status='programado' automaticamente
   - Management command diário atualiza status: se `end_date < hoje` e status='aberto', atualizar para 'fechado'

3. **Validação de Datas**: `end_date` deve ser posterior a `start_date`

4. **Auditoria**: Campos `created_by` e `updated_by` rastreiam quem criou e atualizou cada edital

---

### 📅 Cronograma

| Campo | Tipo | Descrição | Obrigatório | Único | Índice |
|--------|------|-----------|-------------|-------|--------|
| id | AutoField | Identificador único | Sim | Sim | PK |
| edital | FK(Edital) | Relação com edital | Sim | Não | Não |
| data_inicio | DateField | Início da etapa | Não | Não | Não |
| data_fim | DateField | Fim da etapa | Não | Não | Não |
| data_publicacao | DateField | Data de publicação | Não | Não | Não |
| descricao | CharField(300) | Descrição da etapa | Não | Não | Não |

#### Regras de Negócio

1. **Relacionamento**: Um Edital pode ter múltiplos Cronogramas (um para muitos)
2. **Cascata**: Ao deletar um Edital, todos os Cronogramas associados são deletados (CASCADE)
3. **Ordenação**: Cronogramas ordenados por `data_inicio` (crescente)

---

### 💰 EditalValor

| Campo | Tipo | Descrição | Obrigatório | Único | Índice |
|--------|------|-----------|-------------|-------|--------|
| id | AutoField | Identificador único | Sim | Sim | PK |
| edital | FK(Edital) | Relação com edital | Sim | Não | Não |
| valor_total | DecimalField(15,2) | Valor total do edital | Não | Não | Não |
| moeda | CharField(10) | Moeda (padrão: BRL) | Sim | Não | Não |

#### Regras de Negócio

1. **Relacionamento**: Um Edital pode ter múltiplos EditalValor (um para muitos)
2. **Cascata**: Ao deletar um Edital, todos os EditalValor associados são deletados (CASCADE)
3. **Moeda**: Padrão é 'BRL' (Real Brasileiro)

---

### 👤 User (Django User + Perfil)

| Campo | Tipo | Descrição | Obrigatório | Único | Índice |
|--------|------|-----------|-------------|-------|--------|
| id | AutoField | Identificador único | Sim | Sim | PK |
| username | CharField(150) | Nome de usuário | Sim | Sim | Sim |
| email | EmailField | Email do usuário | Não | Não | Não |
| is_staff | BooleanField | É staff? | Sim | Não | Não |
| is_superuser | BooleanField | É superusuário? | Sim | Não | Não |
| date_joined | DateTimeField | Data de cadastro | Sim | Não | Não |

#### Níveis de Acesso

| Nível | Permissões | Descrição |
|-------|------------|-----------|
| staff | Acesso básico ao Django Admin | Pode visualizar editais no admin |
| editor | add_edital, change_edital | Pode criar e editar editais |
| admin | add_edital, change_edital, delete_edital | Pode criar, editar e deletar editais |

#### Regras de Negócio

1. **Permissões**: Usar Django Groups ou campo customizado no User model
2. **Rascunhos**: Apenas usuários com permissão CRUD podem visualizar editais em status 'draft'
3. **Auditoria**: Campos `created_by` e `updated_by` em Edital referenciam User

---

### ❤️ EditalFavorite (Mantido no banco, não usado no MVP)

| Campo | Tipo | Descrição | Obrigatório | Único | Índice |
|--------|------|-----------|-------------|-------|--------|
| id | AutoField | Identificador único | Sim | Sim | PK |
| user | FK(User) | Usuário que favoritou | Sim | Não | Não |
| edital | FK(Edital) | Edital favoritado | Sim | Não | Não |
| created_at | DateTimeField | Data de favoritação | Sim | Não | Não |

#### Regras de Negócio

1. **Relacionamento**: Um User pode favoritar múltiplos Editais (muitos para muitos através de EditalFavorite)
2. **Unicidade**: Um User não pode favoritar o mesmo Edital duas vezes (unique_together: user, edital)
3. **Status MVP**: Modelo mantido no banco, mas funcionalidade removida do MVP. Será implementado como "salvar" em fase futura.

---

## 2. Relacionamentos

### Diagrama de Relacionamentos

```
User (1) ────< (N) Edital (created_by, updated_by)
User (1) ────< (N) EditalFavorite (user) [REMOVIDO DO MVP]
Edital (1) ────< (N) Cronograma (edital)
Edital (1) ────< (N) EditalValor (edital)
Edital (1) ────< (N) EditalFavorite (edital) [REMOVIDO DO MVP]
```

### Descrição dos Relacionamentos

1. **User → Edital (created_by)**: Um usuário pode criar múltiplos editais. Se o usuário for deletado, `created_by` é definido como NULL (SET_NULL).

2. **User → Edital (updated_by)**: Um usuário pode atualizar múltiplos editais. Se o usuário for deletado, `updated_by` é definido como NULL (SET_NULL).

3. **Edital → Cronograma**: Um edital pode ter múltiplos cronogramas (etapas). Ao deletar um edital, todos os cronogramas são deletados (CASCADE).

4. **Edital → EditalValor**: Um edital pode ter múltiplos valores (diferentes moedas ou valores parciais). Ao deletar um edital, todos os valores são deletados (CASCADE).

5. **User → EditalFavorite → Edital**: Um usuário pode favoritar múltiplos editais. **NOTA**: Funcionalidade removida do MVP, mas modelo mantido no banco.

---

## 3. Regras de negócio

### Geração de Slug

1. **Algoritmo**: Usar `django.utils.text.slugify()` para gerar slug a partir do título
2. **Remoção de Acentos**: Acentos são removidos automaticamente pelo slugify
3. **Unicidade**: Se o slug gerado já existe, adicionar sufixo numérico (-2, -3, etc.)
4. **Edição**: Slug não pode ser editado manualmente (gerado apenas na criação)
5. **Persistência**: Se o título mudar, o slug não muda (para preservar links existentes)

### Atualização Automática de Status

1. **Status 'programado'**: Se `start_date > hoje` e status='aberto', definir status='programado' automaticamente no método `save()`
2. **Status 'fechado'**: Management command diário verifica se `end_date < hoje` e status='aberto', atualizando para 'fechado'
3. **Aviso "Prazo Próximo"**: Editais com `end_date` nos últimos 7 dias exibem aviso visual na listagem pública

### Validação de Datas

1. **Validação**: `end_date` deve ser posterior a `start_date`
2. **Campos Opcionais**: `start_date` e `end_date` são opcionais (blank=True, null=True)
3. **Cronograma**: Datas de cronograma são independentes das datas do edital

### Permissões e Visibilidade

1. **Rascunhos**: Editais com status 'draft' são visíveis apenas para usuários com permissão CRUD
2. **Público**: Editais com status 'aberto', 'em_andamento', 'fechado', 'programado' são visíveis publicamente
3. **Administração**: Usuários com permissão apropriada podem ver todos os editais (incluindo rascunhos) no Django Admin

### Auditoria

1. **Criação**: Campo `created_by` rastreia quem criou o edital
2. **Atualização**: Campo `updated_by` rastreia quem atualizou o edital pela última vez
3. **Timestamps**: Campos `data_criacao` e `data_atualizacao` rastreiam quando o edital foi criado e atualizado

### Exclusão em Cascata

1. **Cronograma**: Ao deletar um Edital, todos os Cronogramas associados são deletados (CASCADE)
2. **EditalValor**: Ao deletar um Edital, todos os EditalValor associados são deletados (CASCADE)
3. **EditalFavorite**: Ao deletar um Edital, todos os EditalFavorite associados são deletados (CASCADE)

---

## 4. Índices e otimização

### Índices Existentes

| Índice | Campos | Descrição |
|--------|--------|-----------|
| idx_data_atualizacao | -data_atualizacao | Ordenação por data de atualização (decrescente) |
| idx_status | status | Filtro por status |
| idx_entidade | entidade_principal | Busca por entidade fomentadora |
| idx_numero | numero_edital | Busca por número do edital |

### Índices Novos (a adicionar)

| Índice | Campos | Descrição |
|--------|--------|-----------|
| idx_slug | slug | Busca por slug (único) |
| idx_status_dates | status, start_date, end_date | Filtro por status e datas |
| idx_titulo | titulo | Busca por título |

### Estratégias de Otimização

1. **Queries Otimizadas**:
   - Usar `select_related()` para `created_by` e `updated_by`
   - Usar `prefetch_related()` para `cronogramas` e `valores`
   - Usar índices para campos de busca e filtros

2. **Cache**:
   - Cache de listagens públicas (TTL: 5 minutos)
   - Invalidar cache quando editais são criados/editados/deletados

3. **Paginação**:
   - Paginação de 20 itens por página (padrão)
   - Opção para alterar itens por página (20, 50, 100)

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
  ]
}
```

### Edital Mínimo (Campos Obrigatórios)

```json
{
  "titulo": "Edital de Inovação Agro 2025",
  "status": "aberto"
}
```

**Nota**: Campos `slug`, `data_criacao`, `data_atualizacao` são preenchidos automaticamente.

---

## 6. Migrações Necessárias

### Migration 1: Adicionar campos slug, start_date, end_date

```python
# 0005_add_slug_start_date_end_date.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('editais', '0004_edital_idx_data_atualizacao_edital_idx_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='edital',
            name='slug',
            field=models.SlugField(max_length=255, unique=True, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='edital',
            name='start_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='edital',
            name='end_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
```

### Migration 2: Adicionar status draft e programado

```python
# 0006_add_status_draft_programado.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('editais', '0005_add_slug_start_date_end_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='edital',
            name='status',
            field=models.CharField(
                choices=[
                    ('draft', 'Rascunho'),
                    ('aberto', 'Aberto'),
                    ('em_andamento', 'Em Andamento'),
                    ('fechado', 'Fechado'),
                    ('programado', 'Programado'),
                ],
                default='aberto',
                max_length=20
            ),
        ),
    ]
```

### Migration 3: Adicionar índices

```python
# 0007_add_indexes.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('editais', '0006_add_status_draft_programado'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='edital',
            index=models.Index(fields=['slug'], name='idx_slug'),
        ),
        migrations.AddIndex(
            model_name='edital',
            index=models.Index(fields=['status', 'start_date', 'end_date'], name='idx_status_dates'),
        ),
        migrations.AddIndex(
            model_name='edital',
            index=models.Index(fields=['titulo'], name='idx_titulo'),
        ),
    ]
```

### Migration 4: Data migration para popular slugs

```python
# 0008_populate_slugs.py
from django.db import migrations
from django.utils.text import slugify

def populate_slugs(apps, schema_editor):
    Edital = apps.get_model('editais', 'Edital')
    for edital in Edital.objects.all():
        if not edital.slug:
            base_slug = slugify(edital.titulo)
            slug = base_slug
            counter = 1
            while Edital.objects.filter(slug=slug).exists():
                counter += 1
                slug = f"{base_slug}-{counter}"
            edital.slug = slug
            edital.save()

class Migration(migrations.Migration):
    dependencies = [
        ('editais', '0007_add_indexes'),
    ]

    operations = [
        migrations.RunPython(populate_slugs),
    ]
```

---

## 7. Validações

### Validações de Modelo

1. **Slug**: Único, gerado automaticamente, não editável
2. **Datas**: `end_date` deve ser posterior a `start_date`
3. **Status**: Deve estar entre as opções válidas (draft, aberto, em_andamento, fechado, programado)
4. **Título**: Obrigatório, máximo 500 caracteres
5. **URL**: Deve ser uma URL válida (se fornecida)

### Validações de Formulário

1. **Campos Obrigatórios**: título, status
2. **Campos Opcionais**: Todos os outros campos
3. **Sanitização**: Campos de texto devem ser sanitizados com bleach para prevenir XSS
4. **Validação de Datas**: Formulário deve validar que end_date > start_date

---

## 8. Próximos Passos

1. ✅ Modelo de dados definido
2. ✅ Migrações planejadas
3. ⏳ Implementar modelos atualizados
4. ⏳ Criar e aplicar migrações
5. ⏳ Implementar validações
6. ⏳ Implementar sistema de permissões
7. ⏳ Testar modelo de dados

---

## 9. Referências

- [Django Models Documentation](https://docs.djangoproject.com/en/5.2/topics/db/models/)
- [Django Migrations Documentation](https://docs.djangoproject.com/en/5.2/topics/migrations/)
- Especificação completa: [spec.md](./spec.md)
- Clarificações: [clarifications.md](./clarifications.md)
- Plano de implementação: [plan.md](./plan.md)
- Pesquisa: [research.md](./research.md)

