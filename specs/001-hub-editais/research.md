# Pesquisa — Hub de Editais (AgroHub UniRV)

**Versão:** 1.0  
**Data:** 2025-11-27  
**Autor:** Sistema Spec Kit (Rebuild from Codebase)  
**Fase:** 0 – Pesquisa e Contexto  

---

## 1. Objetivo geral

Criar um portal unificado de editais de fomento da **AgroHub UniRV**, incubadora e centro de inovação da Universidade de Rio Verde.  

O sistema permite que alunos, professores e startups descubram, acompanhem e se inscrevam em editais de pesquisa, inovação e empreendedorismo.

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
- **Gestores da AgroHub/UniRV** (administração dos editais via dashboard e Django Admin).  

---

## 4. Objetivos específicos

- ✅ Centralizar todos os editais em um único portal.  
- ✅ Permitir cadastro, edição e publicação de editais via painel admin e dashboard.  
- ✅ Oferecer busca e filtros intuitivos (status, datas, palavras-chave, tipo).  
- ✅ Garantir segurança e localização em pt-BR.  
- ✅ Sistema de projetos para submissão de propostas aos editais.
- ✅ Histórico de alterações (auditoria) para rastreamento de mudanças.
- ⏳ No futuro: monitorar oportunidades e enviar notificações personalizadas.

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

- **Tecnologia:** Django 5.2.7+, SQLite/PostgreSQL, WhiteNoise, Gunicorn, Tailwind CSS.  
- **Idioma:** Português (Brasil).  
- **Prazo:** MVP implementado e funcional.  
- **Infraestrutura:** Servidor UniRV ou container Docker.  
- **Sem upload de anexos** nesta fase.
- **Sem sistema de favoritos** no MVP (modelo removido).

---

## 7. Análise de modelos implementados

### Modelos Django Implementados

#### Edital (editais/models.py)
- **Campos implementados:**
  - `numero_edital`: CharField(max_length=100, blank=True, null=True)
  - `titulo`: CharField(max_length=500) - obrigatório
  - `slug`: SlugField(max_length=255, unique=True, editable=False) - gerado automaticamente
  - `url`: URLField(max_length=1000) - obrigatório
  - `entidade_principal`: CharField(max_length=200, blank=True, null=True)
  - `status`: CharField com choices: 'draft', 'aberto', 'em_andamento', 'fechado', 'programado'
  - `start_date`: DateField(blank=True, null=True) - data de abertura
  - `end_date`: DateField(blank=True, null=True) - data de encerramento
  - `data_criacao`: DateTimeField(auto_now_add=True)
  - `data_atualizacao`: DateTimeField(auto_now=True)
  - `created_by`: ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
  - `updated_by`: ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
  - Campos de conteúdo: `analise`, `objetivo`, `etapas`, `recursos`, `itens_financiaveis`, `criterios_elegibilidade`, `criterios_avaliacao`, `itens_essenciais_observacoes`, `detalhes_unirv`

- **Índices implementados:**
  - `idx_data_atualizacao`: Index em `-data_atualizacao`
  - `idx_status`: Index em `status`
  - `idx_entidade`: Index em `entidade_principal`
  - `idx_numero`: Index em `numero_edital`
  - `idx_slug`: Index em `slug`
  - `idx_status_dates`: Index composto em `(status, start_date, end_date)`
  - `idx_titulo`: Index em `titulo`

- **Métodos implementados:**
  - `_generate_unique_slug()`: Geração de slug único com fallback
  - `clean()`: Validação de datas
  - `save()`: Auto-atualização de status e geração de slug
  - `get_summary()`, `is_open()`, `is_closed()`, `can_edit(user)`, `get_absolute_url()`
  - Propriedades: `days_until_deadline`, `is_deadline_imminent`

#### Cronograma (editais/models.py)
- **Campos implementados:**
  - `edital`: ForeignKey(Edital, on_delete=models.CASCADE, related_name='cronogramas')
  - `data_inicio`: DateField(blank=True, null=True)
  - `data_fim`: DateField(blank=True, null=True)
  - `data_publicacao`: DateField(blank=True, null=True)
  - `descricao`: CharField(max_length=300, blank=True)

- **Índices implementados:**
  - `idx_cronograma_edital_data`: Index composto em `(edital, data_inicio)`
  - `idx_cronograma_data_inicio`: Index em `data_inicio`

#### EditalValor (editais/models.py)
- **Campos implementados:**
  - `edital`: ForeignKey(Edital, on_delete=models.CASCADE, related_name='valores')
  - `valor_total`: DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
  - `moeda`: CharField(max_length=10, choices=[('BRL', 'Real Brasileiro'), ('USD', 'Dólar Americano'), ('EUR', 'Euro')], default='BRL')

- **Índices implementados:**
  - `idx_edital_moeda`: Index composto em `(edital, moeda)`

#### EditalHistory (editais/models.py)
- **Campos implementados:**
  - `edital`: ForeignKey(Edital, on_delete=models.SET_NULL, null=True, blank=True, related_name='history')
  - `edital_titulo`: CharField(max_length=500, blank=True, null=True) - preservado quando edital é deletado
  - `user`: ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
  - `action`: CharField(max_length=20, choices=[('create', 'Criado'), ('update', 'Atualizado'), ('delete', 'Excluído')])
  - `field_name`, `old_value`, `new_value`: Campos legados (TextField)
  - `timestamp`: DateTimeField(auto_now_add=True)
  - `changes_summary`: JSONField(default=dict) - resumo das mudanças em formato JSON

- **Índices implementados:**
  - `idx_timestamp`: Index em `-timestamp`
  - `idx_edital_timestamp`: Index composto em `(edital, -timestamp)`

#### Project (editais/models.py)
- **Campos implementados:**
  - `name`: CharField(max_length=200) - nome do projeto
  - `edital`: ForeignKey(Edital, on_delete=models.CASCADE, related_name='projetos')
  - `proponente`: ForeignKey(User, on_delete=models.CASCADE, related_name='projetos_submetidos')
  - `submitted_on`: DateTimeField(auto_now_add=True)
  - `status`: CharField(max_length=20, choices=[('em_avaliacao', 'Em Avaliação'), ('aprovado', 'Aprovado'), ('reprovado', 'Reprovado'), ('pendente', 'Pendente')], default='pendente')
  - `note`: DecimalField(max_digits=5, decimal_places=2, blank=True, null=True) - nota/score
  - `data_criacao`: DateTimeField(auto_now_add=True)
  - `data_atualizacao`: DateTimeField(auto_now=True)

- **Índices implementados:**
  - `idx_project_submitted`: Index em `-submitted_on`
  - `idx_project_status`: Index em `status`
  - `idx_project_edital_status`: Index composto em `(edital, status)`
  - `idx_project_proponente`: Index em `proponente`

---

## 8. Análise de URLs implementadas

### URLs Públicas
- `GET /` - Home page
- `GET /editais/` - Listagem pública com busca e filtros
- `GET /edital/<slug>/` - Detalhe público por slug
- `GET /edital/<pk>/` - Redirecionamento 301 para slug
- `GET /ambientes-inovacao/` - Página de ambientes de inovação
- `GET /projetos-aprovados/` - Página de projetos aprovados
- `GET /login/` - Página de login
- `GET /register/` - Página de registro
- `GET /password-reset/` - Recuperação de senha

### URLs Administrativas (requerem is_staff)
- `GET /dashboard/` - Dashboard administrativo
- `GET /dashboard/home/` - Dashboard home
- `GET /dashboard/editais/` - Gerenciamento de editais
- `GET /dashboard/editais/novo/` - Novo edital
- `GET /dashboard/projetos/` - Gerenciamento de projetos
- `GET /dashboard/projetos/submeter/` - Submeter projeto
- `GET /dashboard/avaliacoes/` - Avaliações
- `GET /dashboard/usuarios/` - Gerenciamento de usuários (staff only)
- `GET /dashboard/relatorios/` - Relatórios (staff only)
- `POST /cadastrar/` - Criar edital (staff only)
- `POST /edital/<pk>/editar/` - Editar edital (staff only)
- `POST /edital/<pk>/excluir/` - Deletar edital (staff only)

### URLs de API
- `GET /health/` - Health check endpoint (JSON)

---

## 9. Análise de views implementadas

### Views Públicas
- `home()`: Página inicial com hero, stats, features
- `ambientes_inovacao()`: Página de ambientes de inovação
- `projetos_aprovados()`: Página de projetos aprovados
- `login_view()`: Login customizado
- `register_view()`: Registro de usuários
- `index()`: Listagem pública com busca, filtros (status, tipo, datas), paginação (12 itens), cache
- `edital_detail()`: Detalhe por slug ou PK, cache diferenciado por tipo de usuário, sanitização HTML
- `edital_detail_redirect()`: Redirecionamento 301 de PK para slug

### Views Administrativas (requerem login e is_staff)
- `dashboard_home()`: Dashboard home
- `dashboard_editais()`: Gerenciamento de editais com busca, filtros, estatísticas
- `dashboard_projetos()`: Gerenciamento de projetos com busca, filtros, ordenação, estatísticas
- `dashboard_avaliacoes()`: Página de avaliações
- `dashboard_usuarios()`: Gerenciamento de usuários (staff only)
- `dashboard_relatorios()`: Relatórios (staff only)
- `dashboard_novo_edital()`: Novo edital (staff only)
- `dashboard_submeter_projeto()`: Submeter projeto
- `admin_dashboard()`: Dashboard administrativo com estatísticas, cache
- `edital_create()`: Criar edital (staff only, rate limiting, sanitização, histórico)
- `edital_update()`: Editar edital (staff only, rate limiting, sanitização, histórico, rastreamento de mudanças)
- `edital_delete()`: Deletar edital (staff only, rate limiting, histórico)

### Views de Sistema
- `health_check()`: Health check para monitoramento (JSON)

### Funcionalidades Implementadas
- **Busca**: Busca case-insensitive em título, entidade_principal, numero_edital
- **Filtros**: Status, tipo (Fluxo Contínuo/Fomento), datas (start_date, end_date), "somente abertos"
- **Paginação**: 12 itens por página (configurável via settings)
- **Cache**: Cache versionado para listagens públicas (TTL: 5 minutos), cache de detalhes (TTL: 15 minutos)
- **Sanitização**: Todos os campos HTML são sanitizados com bleach antes de salvar
- **Rate Limiting**: 5 requisições por minuto por IP em views de modificação
- **Histórico**: Todas as ações (create, update, delete) são registradas em EditalHistory

---

## 10. Análise de templates implementados

### Templates Públicos
- `home.html` - Página inicial
- `ambientes_inovacao.html` - Ambientes de inovação
- `projetos_aprovados.html` - Projetos aprovados
- `editais/index.html` - Listagem de editais com busca e filtros
- `editais/detail.html` - Detalhe do edital
- `registration/login.html` - Login
- `registration/register.html` - Registro
- `registration/password_reset_*.html` - Recuperação de senha

### Templates Administrativos
- `dashboard/base.html` - Base do dashboard
- `dashboard/home.html` - Dashboard home
- `dashboard/editais.html` - Gerenciamento de editais
- `dashboard/projetos.html` - Gerenciamento de projetos
- `dashboard/avaliacoes.html` - Avaliações
- `dashboard/usuarios.html` - Usuários
- `dashboard/relatorios.html` - Relatórios
- `dashboard/novo_edital.html` - Novo edital
- `dashboard/submeter_projeto.html` - Submeter projeto
- `editais/create.html` - Criar edital
- `editais/update.html` - Editar edital
- `editais/delete.html` - Deletar edital
- `editais/dashboard.html` - Dashboard administrativo

### Templates de Erro
- `403.html` - Acesso negado
- `404.html` - Não encontrado
- `500.html` - Erro do servidor

### Tecnologias Utilizadas
- **Tailwind CSS**: Framework CSS utility-first para estilização
- **Font Awesome**: Ícones
- **Django Template Tags**: Filtros customizados, humanize

---

## 11. Análise de sistema de permissões implementado

### Sistema Implementado
- **Django's built-in authentication**: Sistema padrão do Django
- **Permissões baseadas em `is_staff`**: 
  - Usuários com `is_staff=True` podem criar, editar e deletar editais
  - Usuários com `is_staff=False` podem apenas visualizar editais públicos e submeter projetos
- **Verificação de permissões**: Implementada em todas as views administrativas
- **Rascunhos**: Editais com status 'draft' são visíveis apenas para usuários staff

### Níveis de Acesso Implementados
- **Visitante (não autenticado)**: Pode visualizar editais públicos (exceto draft)
- **Usuário autenticado (não-staff)**: Pode visualizar editais públicos e submeter projetos
- **Staff (`is_staff=True`)**: Pode criar, editar, deletar editais e acessar dashboard completo
- **Superusuário (`is_superuser=True`)**: Acesso total ao sistema e Django Admin

---

## 12. Análise de performance implementada

### Requisitos de Performance Atendidos
- ✅ Listagem pública carrega em menos de 2 segundos com 100+ editais (cache + otimizações)
- ✅ Busca case-insensitive em múltiplos campos (implementada)
- ✅ Cache de listagens públicas (TTL: 5 minutos, cache versionado)
- ✅ Queries otimizadas com select_related/prefetch_related (implementado)

### Estratégias de Otimização Implementadas
- ✅ **Índices**: Índices em todos os campos de busca e filtros frequentes
- ✅ **Cache**: Cache versionado para listagens públicas, cache de detalhes diferenciado por tipo de usuário
- ✅ **Paginação**: 12 itens por página (configurável)
- ✅ **select_related**: Para created_by/updated_by (ForeignKeys)
- ✅ **prefetch_related**: Para cronogramas, valores, history (reverse ForeignKeys)
- ✅ **only()**: Limitação de campos retornados em listagens
- ✅ **Query optimization**: Queries agregadas para estatísticas

---

## 13. Análise de segurança implementada

### Requisitos de Segurança Implementados
- ✅ **SECRET_KEY**: Gerenciado via variável de ambiente
- ✅ **CSRF**: Habilitado para todas as operações de escrita (testado)
- ✅ **Validação e sanitização**: Django forms + bleach para sanitização de HTML (implementado em views e admin)
- ✅ **Proteção contra SQL injection**: Django ORM exclusivamente (testado)
- ✅ **Proteção contra XSS**: Sanitização de HTML com bleach em todos os campos HTML (implementado e testado)
- ✅ **Rate Limiting**: Implementado via decorator em views de modificação (5 requisições/minuto por IP)
- ✅ **Permissões**: Verificação `is_staff` em todas as views administrativas (implementado e testado)
- ✅ **Cache Security**: Cache diferenciado por tipo de usuário (staff, auth, public) para prevenir cache poisoning

### Implementações de Segurança
- **Sanitização HTML**: Todos os campos HTML são sanitizados antes de salvar (views web e Django Admin)
- **Validação de dados**: Validação de datas, slugs, campos obrigatórios
- **Tratamento de erros**: Logging de erros, mensagens de erro amigáveis
- **Auditoria**: Histórico de todas as ações (create, update, delete) para rastreamento

---

## 14. Análise de testes implementados

### Cobertura de Testes
- **Total de testes**: 169+ métodos de teste
- **Arquivos de teste**:
  - `test_admin.py`: Testes de Django Admin (570 linhas)
  - `test_dashboard_views.py`: Testes de views do dashboard (280 linhas)
  - `test_public_views.py`: Testes de views públicas
  - `test_security.py`: Testes de segurança (CSRF, XSS, SQL injection, autenticação/autorização)
  - `test_permissions.py`: Testes de permissões
  - `test_integration.py`: Testes de integração
  - `test_management_commands.py`: Testes de management commands (608 linhas)
  - `test_views_dashboard.py`: Testes adicionais do dashboard
  - `test_legacy.py`: Testes legados de CRUD

### Cenários Testados
- ✅ Autenticação e autorização
- ✅ Permissões (staff vs não-staff)
- ✅ CRUD de editais
- ✅ Busca e filtros
- ✅ Paginação
- ✅ Slug generation e redirecionamento
- ✅ Validação de dados
- ✅ Sanitização HTML (XSS prevention)
- ✅ CSRF protection
- ✅ SQL injection prevention
- ✅ Rate limiting
- ✅ Cache
- ✅ Management commands
- ✅ Dashboard e estatísticas
- ✅ Projetos

### Status dos Testes
- ✅ **Todos os testes passando**: 169 testes executados com sucesso
- ⚠️ **Cobertura**: Meta de 85% ainda não verificada (executar `coverage`)

---

## 15. Management Commands Implementados

### update_edital_status
- **Função**: Atualiza automaticamente o status dos editais baseado em datas
- **Opções**: `--dry-run`, `--verbose`
- **Lógica**: Fecha editais com `end_date <= hoje`, programa editais com `start_date > hoje`, abre editais com datas atuais
- **Cache**: Invalida cache após atualizações
- **Logging**: Registra todas as ações e erros

### populate_from_pdfs
- **Função**: Popula editais a partir de PDFs (se implementado)

### seed_editais
- **Função**: Cria editais de exemplo para desenvolvimento/testes

---

## 16. Serviços Implementados

### EditalService (editais/services.py)
- `get_editais_by_deadline(days)`: Retorna editais que expiram dentro de N dias
- `get_recent_editais(days)`: Retorna editais criados nos últimos N dias
- `get_recent_activities(days)`: Retorna editais criados ou atualizados nos últimos N dias
- `update_status_by_dates()`: Atualiza status em lote baseado em datas (usado pelo management command)

---

## 17. Utilitários Implementados

### utils.py
- `sanitize_html(text)`: Sanitiza conteúdo HTML com bleach
- `sanitize_edital_fields(edital)`: Sanitiza todos os campos HTML de um edital
- `mark_edital_fields_safe(edital)`: Marca campos sanitizados como seguros para renderização

### decorators.py
- `rate_limit()`: Decorator para rate limiting usando cache
- `get_client_ip(request)`: Obtém IP real do cliente (considera proxies)

### exceptions.py
- `EditalException`: Exceção base
- `EditalNotFoundError`: Exceção quando edital não é encontrado

### constants.py
- `DEADLINE_WARNING_DAYS = 7`: Dias para aviso de prazo próximo
- `PAGINATION_DEFAULT = 12`: Paginação padrão
- `CACHE_TTL_INDEX = 300`: TTL do cache de listagens (5 minutos)
- `RATE_LIMIT_REQUESTS = 5`: Número de requisições permitidas
- `RATE_LIMIT_WINDOW = 60`: Janela de tempo em segundos
- `HTML_FIELDS`: Lista de campos que precisam de sanitização

---

## 18. Conclusões

### Decisões Implementadas
1. ✅ Modelos existentes mantidos e expandidos (Edital, Cronograma, EditalValor)
2. ✅ Campos `slug`, `start_date`, `end_date` adicionados ao modelo Edital
3. ✅ Status 'draft' e 'programado' adicionados
4. ✅ Modelo EditalHistory implementado para auditoria
5. ✅ Modelo Project implementado para submissão de projetos
6. ✅ Sistema de permissões baseado em `is_staff` implementado
7. ✅ URLs baseadas em slug com redirecionamento 301 de PK
8. ✅ Cache implementado para listagens públicas
9. ✅ Sanitização HTML implementada (views e admin)
10. ✅ Rate limiting implementado
11. ✅ Management command para atualização automática de status
12. ✅ Dashboard administrativo completo
13. ✅ Sistema de projetos para submissão

### Funcionalidades Removidas do MVP
- ❌ Upload de anexos (removido)
- ❌ Sistema de favoritos (modelo EditalFavorite removido)
- ❌ Filtro de localização (removido)

### Próximos Passos (Backlog)
1. ⏳ Verificar cobertura de testes (executar `coverage`)
2. ⏳ Notificações personalizadas
3. ⏳ Opção de alterar itens por página
4. ⏳ Níveis adicionais de permissão (editor/admin além de staff)
5. ⏳ API REST para integração externa

---

## 19. Referências

- [Django Documentation](https://docs.djangoproject.com/)
- [Django Best Practices](https://docs.djangoproject.com/en/5.2/misc/design-philosophies/)
- [Tailwind CSS Documentation](https://tailwindcss.com/)
- [Bleach Documentation](https://bleach.readthedocs.io/)
- Especificação completa: [spec.md](./spec.md)
- Clarificações: [clarifications.md](./clarifications.md)
- Plano de implementação: [plan.md](./plan.md)
- Modelo de dados: [data-model.md](./data-model.md)
- Análise: [analysis.md](./analysis.md)
