# Revisão da Estrutura do Banco de Dados

## Resumo Executivo

Este documento fornece uma revisão abrangente dos modelos e estrutura de banco de dados da aplicação AgroHub. Em geral, a estrutura do banco de dados é bem projetada com bom índexing, relacionamentos apropriados e validação. No entanto, havia um problema crítico que foi resolvido.

## Histórico de Issues Críticas

### ✅ RESOLVIDO: Conflito de Related Name no Modelo Project

**Location:** `editais/models.py` (resolvido em migration 0024)

**Problema**: Ambos os campos ForeignKey `edital` e `proponente` no modelo `Project` tinha o mesmo `related_name='startups'`. Isso criava um conflito no sistema de relacionamento reverso do Django.

**Impacto**: 
- Django levantaria um `SystemCheckError` ao executar `python manage.py check`
- Relacionamentos reversos de `Edital.startups` e `User.startups` entravam em conflito

**Solução Implementada**: ✅ **Resolvido**
- `proponente.related_name` foi alterado para `'startups_owned'` na migration 0024
- Nenhum código usa as relações reversas, então a mudança foi segura

---

## Análise Modelo-por-Modelo

### 1. Modelo Edital ✅ **Bem Projetado**

**Pontos Fortes:**
- ✅ Cobertura abrangente de campos para oportunidades de fomento
- ✅ Geração apropriada de slug com constraint de unicidade
- ✅ Boa estratégia de índexing (8 índices cobrindo padrões comuns de query)
- ✅ Validação de datas em método `clean()`
- ✅ Determinação automática de status em `save()`
- ✅ Sanitização HTML para segurança (prevenção XSS)
- ✅ Trail de auditoria via `django-simple-history`
- ✅ Rastreamento de usuário (`created_by`, `updated_by`)
- ✅ QuerySet e Manager customizados para queries otimizadas
- ✅ Suporte full-text search PostgreSQL com fallback

**Campos:**
- `numero_edital`: CharField(100) - Opcional, bom para flexibilidade
- `titulo`: CharField(500) - Comprimento apropriado
- `slug`: SlugField(255) - Único, auto-gerado, indexado
- `url`: URLField(1000) - Bom comprimento máximo para URLs longas
- `status`: CharField(20) com choices - Estados bem definidos
- `start_date`/`end_date`: DateField - Manipulação apropriada de datas
- Campos de conteúdo: Todos TextField com blank/null=True - Flexível

**Índices:** ✅ Cobertura excelente
- `idx_data_atualizacao` - Para ordenação
- `idx_status` - Para filtragem
- `idx_entidade` - Para filtragem por entidade
- `idx_numero` - Para busca por número
- `idx_slug` - Para lookups de URL
- `idx_status_dates` - Composto para queries baseadas em data
- `idx_titulo` - Para buscas por título

**Relacionamentos:**
- ✅ `created_by` / `updated_by`: SET_NULL (preserva dados se usuário deletado)
- ✅ `valores`: One-to-many via EditalValor
- ✅ `cronogramas`: One-to-many via Cronograma
- ✅ `startups`: One-to-many via Project (relação reversa)

**Recomendações:**
- ✅ Considerar adicionar `db_index=True` no campo `status` diretamente (já tem índice em Meta)
- ✅ Considerar adicionar constraint único em `(numero_edital, entidade_principal)` se duplicatas não devem existir

---

### 2. Modelo EditalValor ✅ **Bem Projetado**

**Pontos Fortes:**
- ✅ Suporta múltiplas moedas (BRL, USD, EUR)
- ✅ DecimalField com precisão apropriada (15 dígitos, 2 decimais)
- ✅ MinValueValidator previne valores negativos
- ✅ Índice composto em (edital, moeda) para queries eficientes
- ✅ Delete CASCADE (valores deletados com edital)

**Campos:**
- `valor_total`: DecimalField(15,2) - ✅ Apropriado para valores grandes
- `moeda`: CharField(10) com choices - ✅ Bom suporte a moedas

**Índices:**
- ✅ `idx_edital_moeda` - Índice composto para filtragem por edital e moeda

**Melhorias Potenciais:**
- ⚠️ Considerar adicionar constraint único em `(edital, moeda)` se cada edital deve ter apenas um valor por moeda
- ⚠️ Considerar adicionar campo `tipo` se precisar distinguir entre "total", "por projeto", etc. (atualmente não está no modelo mas mencionado no README)

---

### 3. Modelo Cronograma ✅ **Bem Projetado**

**Pontos Fortes:**
- ✅ Campos de data flexíveis (inicio, fim, publicacao)
- ✅ Bom índexing para queries baseadas em data
- ✅ Delete CASCADE (cronograma deletado com edital)
- ✅ Ordenação apropriada por `data_inicio`

**Campos:**
- `data_inicio`, `data_fim`, `data_publicacao`: Todos DateField com blank/null - ✅ Flexível
- `descricao`: CharField(300) - ✅ Comprimento apropriado

**Índices:**
- ✅ `idx_cronograma_edital_data` - Composto para filtragem por edital e data
- ✅ `idx_cronograma_data_inicio` - Para queries baseadas em data

**Melhorias Potenciais:**
- ⚠️ Considerar adicionar validação em `clean()` para garantir `data_fim >= data_inicio` se ambos fornecidos
- ⚠️ Considerar adicionar campo `ordem` se itens de cronograma precisam de ordenação explícita

---

### 4. Modelo Project (Startup) ✅ **Bem Projetado**

**Pontos Fortes:**
- ✅ Campos abrangentes para rastreamento de startup/projeto
- ✅ Boas choices de status e categoria
- ✅ Geração de slug para URLs amigáveis a SEO
- ✅ FileField para logo com validação
- ✅ Relacionamento edital opcional (SET_NULL)
- ✅ Boa estratégia de índexing
- ✅ Rastreamento de usuário (proponente)

**Campos:**
- `name`: CharField(200) - ✅ Apropriado
- `description`: TextField - ✅ Bom para descrições longas
- `category`: CharField(20) com choices - ✅ Categorias bem definidas
- `status`: CharField(20) com choices - ✅ Estados de ciclo de vida claros
- `contato`: TextField - ✅ Flexível para várias infos de contato
- `slug`: SlugField(255) - ✅ Único, indexado
- `logo`: FileField - ✅ Com validação em `clean()`

**Índices:** ✅ Boa cobertura
- `idx_project_submitted` - Para ordenação
- `idx_project_status` - Para filtragem
- `idx_project_edital_status` - Composto para filtragem
- `idx_project_proponente` - Para projetos do usuário
- `idx_project_category` - Para filtragem por categoria
- `idx_project_slug` - Para lookups de URL

**Issues:**
- ✅ **RESOLVIDO**: Conflito de related name (migration 0024)
- ✅ **RESOLVIDO**: Nome de tabela é `editais_startup` e modelo agora é `Startup`

**Relacionamentos:**
- `edital`: SET_NULL (bom - preserva projetos se edital deletado)
- `proponente`: CASCADE (bom - deleta projetos se usuário deletado)

**Melhorias Potenciais:**
- ⚠️ Considerar adicionar campo `website` separado de `contato` para dados estruturados
- ⚠️ Considerar adicionar `founded_date` ou `incubacao_start_date` para melhor rastreamento
- ⚠️ Considerar adicionar `tags` ManyToManyField para categorização flexível

---

## Configuração do Banco de Dados

### Análise de Configurações ✅ **Bem Configurado**

**Database Backend:**
- ✅ PostgreSQL para todos os ambientes (desenvolvimento e produção)
- ✅ PostgreSQL para produção (com connection pooling)
- ✅ Manipulação apropriada de fallback

**Configurações de Conexão:**
- ✅ `CONN_MAX_AGE=600` para connection pooling
- ✅ `connect_timeout=10` para gerenciamento de conexão

**Recomendações:**
- ✅ Considerar adicionar `ATOMIC_REQUESTS=True` para produção se necessário
- ✅ Considerar adicionar logging de database query em desenvolvimento

---

## Estratégia de Índexing

### Índices Atuais ✅ **Excelente**

**Modelo Edital:**
- 8 índices cobrindo todos os padrões comuns de query
- Índices compostos para queries multi-campo
- Índices apropriados de ordenação

**Modelo EditalValor:**
- 1 índice composto para (edital, moeda)

**Modelo Cronograma:**
- 2 índices para queries baseadas em data

**Modelo Project:**
- 6 índices cobrindo queries comuns

**Específico de PostgreSQL:**
- ✅ Índices full-text search (GIN)
- ✅ Índices trigram para busca fuzzy
- ✅ Uso apropriado de extensão (pg_trgm)

**Recomendações:**
- ✅ Índices são bem projetados
- ⚠️ Monitorar performance de queries e adicionar índices se necessário para novos padrões de query

---

## Integridade de Dados

### Constraints ✅ **Bom**

**Unicidade:**
- ✅ `Edital.slug` - Constraint única
- ✅ `Project.slug` - Constraint única

**Foreign Keys:**
- ✅ Todos ForeignKeys têm estratégias `on_delete` apropriadas
- ✅ SET_NULL para relacionamentos opcionais (preserva dados)
- ✅ CASCADE para relacionamentos obrigatórios (mantém integridade referencial)

**Validação:**
- ✅ Validação de data em `Edital.clean()`
- ✅ Validação de arquivo em `Project.clean()`
- ✅ MinValueValidator em `EditalValor.valor_total`

**Melhorias Potenciais:**
- ⚠️ Considerar adicionar CHECK constraints no nível de banco para ranges de data
- ⚠️ Considerar adicionar constraint único em `(EditalValor.edital, EditalValor.moeda)` se necessário

---

## Considerações de Segurança

### Segurança Atual ✅ **Bom**

**Prevenção XSS:**
- ✅ Sanitização HTML em `Edital.save()`
- ✅ Uso de TextField (não HTMLField) previne renderização automática

**Rastreamento de Usuário:**
- ✅ `created_by` e `updated_by` para trail de auditoria
- ✅ `django-simple-history` para rastreamento de mudanças

**Uploads de Arquivo:**
- ✅ Validação de tamanho de arquivo (limite 5MB)
- ✅ Validação de extensão de arquivo
- ✅ Validação de tipo de conteúdo

**Recomendações:**
- ✅ Considerar adicionar varredura de vírus para uploads de arquivo em produção
- ✅ Considerar adicionar rate limiting para uploads de arquivo

---

## Considerações de Performance

### Otimização de Query ✅ **Excelente**

**Otimizações Atuais:**
- ✅ QuerySets customizados com `select_related()` e `prefetch_related()`
- ✅ Uso apropriado de `with_related()`, `with_prefetch()`, `with_full_prefetch()`
- ✅ Índices de banco em todos os campos frequentemente consultados
- ✅ Full-text search PostgreSQL com ranking

**Recomendações:**
- ✅ Continuar usando métodos de otimização de QuerySet
- ⚠️ Monitorar issues de query N+1 em views
- ⚠️ Considerar adicionar logging de database query em desenvolvimento

---

## Histórico de Migrações

### Análise de Migrações ✅ **Bem Gerenciado**

**Observações:**
- ✅ Migrações são bem estruturadas
- ✅ Manipulação apropriada de renomeação de tabelas (Project → Startup table)
- ✅ Data migrations para população de slugs
- ✅ Habilitação de extensão para features PostgreSQL

**Recent Changes:**
- Migration 0022: Table rename from `editais_project` to `editais_startup`
- Migration 0015: Removed `note` field, added `contato`, updated related names
- Migration 0018-0020: PostgreSQL-specific optimizations

---

## Recommendations Summary

### Immediate Actions Required

1. **🔴 CRITICAL**: Fix related_name conflict in Project model
   - Change `proponente.related_name` from `'startups'` to `'startups_owned'` or similar
   - Create migration to update the relationship

### High Priority Improvements

2. **Consider Model Renaming**: Rename `Project` model to `Startup` for consistency with table name and domain language

3. **Add Unique Constraint**: Consider `unique_together` on `(EditalValor.edital, EditalValor.moeda)` if one value per currency per edital is required

4. **Add Date Validation**: Add `clean()` method to `Cronograma` to validate `data_fim >= data_inicio`

### Medium Priority Improvements

5. **Add Missing Fields**: Consider adding structured fields like `website`, `founded_date` to Project model

6. **Enhance EditalValor**: Consider adding `tipo` field if different value types are needed

7. **Database Constraints**: Add CHECK constraints for date ranges at database level

### Low Priority / Future Considerations

8. **Tags System**: Consider ManyToManyField for flexible categorization

9. **Soft Deletes**: Consider adding `deleted_at` field for soft delete functionality

10. **Audit Fields**: Consider adding `deleted_by` field if soft deletes are implemented

---

## Testing Recommendations

### Database Tests Needed

1. ✅ Test related_name conflict fix
2. ✅ Test date validation in Cronograma
3. ✅ Test unique constraint on EditalValor if added
4. ✅ Test CASCADE/SET_NULL behaviors
5. ✅ Test slug generation uniqueness

---

## Conclusion

The database structure is **well-designed** with:
- ✅ Good indexing strategy
- ✅ Proper relationships and constraints
- ✅ Security considerations
- ✅ Performance optimizations
- ✅ Audit trail support

**Critical Issue:** One related_name conflict needs immediate attention, but it's easily fixable since the reverse relations aren't currently used.

**Overall Grade: A-** (would be A+ after fixing the related_name conflict)

---

## Action Items

- [ ] Fix related_name conflict in Project model
- [ ] Create migration for related_name change
- [ ] Test reverse relationships after fix
- [ ] Consider model renaming (Project → Startup)
- [ ] Review and implement high-priority improvements
- [ ] Add database-level constraints if needed
