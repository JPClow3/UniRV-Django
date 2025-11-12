# Pesquisa — Hub de Editais (AgroHub UniRV)

**Versão:** 0.1  
**Data:** 2025-11-11  
**Autor:** João Paulo G. Santos  
**Fase:** 0 – Pesquisa e Contexto  

---

## 1. Objetivo geral

Criar um portal unificado de editais de fomento da **AgroHub UniRV**, incubadora e centro de inovação da Universidade de Rio Verde.  

O sistema deve permitir que alunos, professores e startups descubram, acompanhem e se inscrevam em editais de pesquisa, inovação e empreendedorismo.

---

## 2. Problema identificado

Atualmente, os editais estão dispersos em PDFs e sites institucionais.  

Usuários precisam procurar manualmente oportunidades, o que gera:

- Perda de prazos;
- Falta de organização institucional;
- Dificuldade em acompanhar resultados e histórico.

---

## 3. Público-alvo

- **Professores** que submetem projetos de pesquisa.  
- **Estudantes** que participam de iniciação científica ou projetos de inovação.  
- **Startups** incubadas ou interessadas em programas de aceleração.  
- **Gestores da AgroHub/UniRV** (administração dos editais).  

---

## 4. Objetivos específicos

- Centralizar todos os editais em um único portal.  
- Permitir cadastro, edição e publicação de editais via painel admin.  
- Oferecer busca e filtros intuitivos (status, datas, palavras-chave).  
- Garantir segurança e localização em pt-BR.  
- No futuro: monitorar oportunidades e enviar notificações personalizadas.

---

## 5. Referências / Benchmarks

| Plataforma | Recurso observado | Observações |
|-------------|------------------|--------------|
| gov.br/editais | Busca e PDFs | Interface confusa; sem login. |
| FAPEG | Categorias e prazos claros | Pouca interação. |
| Finep | API pública | Estrutura complexa. |
| Startups.com | Notificações personalizadas | Modelo aspiracional para futuro. |

---

## 6. Restrições e premissas

- **Tecnologia:** Django 5.2.7+, SQLite/PostgreSQL, WhiteNoise, Gunicorn.  
- **Idioma:** Português (Brasil).  
- **Prazo:** MVP até Q1 2026.  
- **Infraestrutura:** Servidor UniRV ou container Docker.  
- **Sem upload de anexos** nesta fase.

---

## 7. Análise de modelos existentes

### Modelos Django Existentes

#### Edital (editais/models.py)
- **Campos existentes:**
  - `numero_edital`: CharField(max_length=100, blank=True, null=True)
  - `titulo`: CharField(max_length=500)
  - `url`: URLField(max_length=1000)
  - `entidade_principal`: CharField(max_length=200, blank=True, null=True)
  - `status`: CharField com choices: 'aberto', 'fechado', 'em_andamento'
  - `data_criacao`: DateTimeField(auto_now_add=True)
  - `data_atualizacao`: DateTimeField(auto_now=True)
  - `created_by`: ForeignKey(User, on_delete=models.SET_NULL, null=True)
  - `updated_by`: ForeignKey(User, on_delete=models.SET_NULL, null=True)
  - Campos de conteúdo: `analise`, `objetivo`, `etapas`, `recursos`, `itens_financiaveis`, `criterios_elegibilidade`, `criterios_avaliacao`, `itens_essenciais_observacoes`, `detalhes_unirv`

- **Índices existentes:**
  - `idx_data_atualizacao`: Index em `-data_atualizacao`
  - `idx_status`: Index em `status`
  - `idx_entidade`: Index em `entidade_principal`
  - `idx_numero`: Index em `numero_edital`

#### Cronograma (editais/models.py)
- **Campos existentes:**
  - `edital`: ForeignKey(Edital, on_delete=models.CASCADE, related_name='cronogramas')
  - `data_inicio`: DateField(blank=True, null=True)
  - `data_fim`: DateField(blank=True, null=True)
  - `data_publicacao`: DateField(blank=True, null=True)
  - `descricao`: CharField(max_length=300, blank=True)

#### EditalValor (editais/models.py)
- **Campos existentes:**
  - `edital`: ForeignKey(Edital, on_delete=models.CASCADE, related_name='valores')
  - `valor_total`: DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
  - `moeda`: CharField(max_length=10, default='BRL')

#### EditalFavorite (editais/models.py)
- **Campos existentes:**
  - `user`: ForeignKey(User, on_delete=models.CASCADE, related_name='favorited_editais')
  - `edital`: ForeignKey(Edital, on_delete=models.CASCADE, related_name='favorited_by')
  - `created_at`: DateTimeField(auto_now_add=True)
- **Nota:** Funcionalidade removida do MVP, mas modelo mantido no banco.

### Alterações Necessárias

1. **Adicionar campo `slug`** ao modelo Edital
   - Tipo: SlugField(unique=True, max_length=255)
   - Gerado automaticamente a partir do título
   - Não editável manualmente
   - Índice: `idx_slug`

2. **Adicionar campos `start_date` e `end_date`** ao modelo Edital
   - Tipo: DateField(blank=True, null=True)
   - `start_date` = data de abertura
   - `end_date` = data de encerramento geral
   - Índice: `idx_status_dates` (status, start_date, end_date)

3. **Adicionar status 'draft' e 'programado'** aos STATUS_CHOICES
   - 'draft' = Rascunho (visível apenas para usuários com permissão CRUD)
   - 'programado' = Edital com data de início no futuro
   - Status existentes mantidos: 'aberto', 'em_andamento', 'fechado'

4. **Adicionar índice em `titulo`** para busca
   - Índice: `idx_titulo`

5. **NÃO criar modelo EditalAttachment** (upload de anexos removido do MVP)
6. **NÃO adicionar campo `location`** (filtro de localização removido do MVP)
7. **NÃO adicionar campos em inglês** (description, requirements) - usar apenas campos em português

---

## 8. Análise de URLs existentes

### URLs Atuais
- `GET /editais/` - Listagem pública (usa PK)
- `GET /editais/<pk>/` - Detalhe público (usa PK)
- URLs administrativas via Django Admin

### Alterações Necessárias
- Migrar para URLs baseadas em slug: `/editais/<slug>/`
- Manter compatibilidade com URLs antigas (PK) com redirecionamento 301
- Atualizar `get_absolute_url()` no modelo Edital para usar slug

---

## 9. Análise de views existentes

### Views Existentes
- Views públicas para listagem e detalhe
- Views administrativas via Django Admin

### Alterações Necessárias
- Adicionar busca e filtros na view de listagem
- Adicionar suporte a slug na view de detalhe
- Implementar redirecionamento de URLs PK para slug
- Adicionar cache para listagens públicas
- Implementar paginação numérica com opção para alterar itens por página

---

## 10. Análise de templates existentes

### Templates Existentes
- `editais/index.html` - Listagem
- `editais/detail.html` - Detalhe
- `editais/create.html`, `editais/update.html`, `editais/delete.html` - CRUD
- `editais/favorites.html` - Favoritos (removido do MVP)

### Alterações Necessárias
- Atualizar template de listagem com busca e filtros
- Adicionar aviso "prazo próximo" na listagem
- Adicionar paginação numérica
- Adicionar opção para alterar itens por página
- Remover referências a anexos e favoritos
- Customizar Django Admin para preview e mensagens toast

---

## 11. Análise de sistema de permissões

### Sistema Atual
- Django's built-in authentication
- Permissões básicas (is_staff, is_superuser)

### Alterações Necessárias
- Implementar sistema de permissões com múltiplos níveis:
  - **staff**: Acesso básico ao Django Admin
  - **editor**: Pode criar e editar editais
  - **admin**: Pode criar, editar e deletar editais
- Usar Django Groups ou campo customizado no User model
- Rascunhos visíveis apenas para usuários com permissão CRUD

---

## 12. Análise de performance

### Requisitos de Performance
- Listagem pública carrega em menos de 2 segundos com 100+ editais
- Busca case-insensitive em múltiplos campos
- Cache de listagens públicas (TTL: 5 minutos)
- Queries otimizadas com select_related/prefetch_related

### Estratégias de Otimização
- Índices em campos de busca (titulo, status, start_date, end_date)
- Cache para listagens públicas (Django cache framework)
- Paginação (20 itens por página padrão)
- select_related para created_by/updated_by
- prefetch_related para cronogramas

---

## 13. Análise de segurança

### Requisitos de Segurança
- SECRET_KEY em variável de ambiente
- CSRF habilitado para todas as operações de escrita
- Validação e sanitização de input do usuário (Django forms, bleach)
- Proteção contra SQL injection (Django ORM exclusivamente)
- Proteção contra XSS (sanitização de HTML com bleach)

### Implementações Necessárias
- Validar variáveis de ambiente em produção
- Sanitizar conteúdo HTML em campos de texto
- Validar datas (end_date deve ser posterior a start_date)
- Validar slugs (gerados automaticamente com slugify)

---

## 14. Conclusões

### Decisões Tomadas
1. ✅ Manter modelos existentes (Edital, Cronograma, EditalValor)
2. ✅ Adicionar campos `slug`, `start_date`, `end_date` ao modelo Edital
3. ✅ Adicionar status 'draft' e 'programado'
4. ✅ Remover upload de anexos do MVP
5. ✅ Remover sistema de favoritos do MVP
6. ✅ Remover filtro de localização do MVP
7. ✅ Usar apenas campos em português
8. ✅ Migrar URLs de PK para slug
9. ✅ Implementar sistema de permissões com múltiplos níveis
10. ✅ Implementar cache para listagens públicas

### Próximos Passos
1. ✅ Definir modelo de dados (Phase 1) - Ver `data-model.md`
2. ✅ Gerar plano de implementação (`plan.md`)
3. ⏳ Validar com stakeholders da AgroHub
4. ⏳ Criar lista de tarefas detalhada (`tasks.md`)
5. ⏳ Iniciar implementação (Phase 2)

---

## 15. Referências

- [Django Documentation](https://docs.djangoproject.com/)
- [Django Best Practices](https://docs.djangoproject.com/en/5.2/misc/design-philosophies/)
- [AgroHub UniRV](https://agrohub.unirv.edu.br/) (referência do projeto)
- Especificação completa: [spec.md](./spec.md)
- Clarificações: [clarifications.md](./clarifications.md)
- Plano de implementação: [plan.md](./plan.md)

