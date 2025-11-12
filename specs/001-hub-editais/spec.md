# Feature Specification: Hub de Editais — Módulo "Editais" (AgroHub UniRV)

**Feature Branch**: `001-hub-editais`  
**Created**: 2025-11-11  
**Autor**: João Paulo  
**Status**: Draft  
**Input**: User description: "Criar o módulo Editais como parte do site AgroHub UniRV — um hub de editais de fomento direcionado a startups, professores e alunos da UniRV"

**Relacionado à Constituição**: Conformidade com Segurança, Localização (pt-BR), WhiteNoise, TDD, Django Best Practices, Database Migrations

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Visualizar Lista de Editais com Busca (Priority: P1)

Como visitante, quero ver a lista de editais com busca para encontrar editais relevantes para mim.

**Why this priority**: Esta é a funcionalidade principal do módulo. Sem a capacidade de listar e buscar editais, o sistema não tem valor para os usuários. É o ponto de entrada principal para todos os outros fluxos.

**Independent Test**: Pode ser totalmente testado acessando a rota pública `/editais/` e verificando que a lista de editais é exibida com paginação. O teste independente inclui verificar busca por título/organização e filtros por status.

**Acceptance Scenarios**:

1. **Given** que existem editais publicados no sistema, **When** um visitante acessa a página inicial `/editais/`, **Then** ele vê uma lista paginada de editais com título, organização, datas e status
2. **Given** que existem editais no sistema, **When** um visitante digita um termo de busca no campo de busca, **Then** a lista é filtrada para mostrar apenas editais que correspondem ao termo (título, organização, palavras-chave)
3. **Given** que existem editais com diferentes status, **When** um visitante seleciona um filtro de status (aberto/fechado), **Then** apenas editais com aquele status são exibidos
4. **Given** que existem mais de 20 editais, **When** um visitante acessa a lista, **Then** a paginação é exibida e ele pode navegar entre páginas

---

### User Story 2 - Visualizar Detalhes de um Edital (Priority: P1)

Como visitante, quero abrir a página de detalhe de um edital para ver todas as informações completas e acessar o link externo do edital.

**Why this priority**: Após encontrar um edital na lista, o usuário precisa ver todos os detalhes para decidir se é relevante. Esta é a segunda funcionalidade mais crítica após a listagem.

**Independent Test**: Pode ser totalmente testado acessando `/editais/<slug>/` e verificando que todos os campos do edital são exibidos, incluindo objetivo, critérios de elegibilidade, prazos, órgão fomentador, cronogramas e link externo (url).

**Acceptance Scenarios**:

1. **Given** que existe um edital publicado com slug conhecido, **When** um visitante acessa `/editais/<slug>/`, **Then** ele vê todos os detalhes do edital incluindo título, objetivo, critérios de elegibilidade, prazos, status, cronogramas e link externo (url)
2. **Given** que um edital tem link externo cadastrado, **When** um visitante visualiza a página de detalhe, **Then** ele vê link para acessar o edital externo
3. **Given** que um edital está em status "draft" (rascunho), **When** um visitante não-autenticado tenta acessar, **Then** ele recebe um erro 404 ou mensagem de não encontrado

---

### User Story 3 - Criar Novo Edital (Priority: P2)

Como administrador, quero criar um novo edital com metadados, prazos e link externo através da interface administrativa.

**Why this priority**: Administradores precisam da capacidade de adicionar novos editais ao sistema. Esta funcionalidade é essencial para manter o conteúdo atualizado, mas é secundária às funcionalidades públicas já que o sistema pode ser populado manualmente inicialmente.

**Independent Test**: Pode ser totalmente testado fazendo login como staff/admin, acessando a interface de criação de edital, preenchendo todos os campos obrigatórios (título, objetivo, datas), preenchendo o campo 'url' com link externo e verificando que o edital é criado com sucesso no banco de dados com slug gerado automaticamente.

**Acceptance Scenarios**:

1. **Given** que um administrador está autenticado, **When** ele acessa a página de criação de edital e preenche todos os campos obrigatórios (título, objetivo, datas), **Then** o edital é criado com slug gerado automaticamente e salvo no banco de dados
2. **Given** que um administrador está criando um edital, **When** ele preenche o campo 'url' com link externo, **Then** o link é salvo e exibido na página de detalhe do edital
3. **Given** que um administrador cria um edital com título que gera slug duplicado, **When** o sistema gera o slug, **Then** um sufixo numérico é adicionado automaticamente (-2, -3, etc.)
4. **Given** que um usuário sem permissão CRUD tenta acessar a página de criação, **When** ele acessa a URL, **Then** ele é redirecionado para login ou recebe erro de permissão

---

### User Story 4 - Editar e Gerenciar Editais (Priority: P2)

Como administrador, quero editar e despublicar um edital existente através da interface administrativa.

**Why this priority**: Administradores precisam atualizar informações de editais existentes e gerenciar seu status de publicação. Esta funcionalidade é essencial para manter a qualidade e atualidade do conteúdo.

**Independent Test**: Pode ser totalmente testado fazendo login como staff/admin, acessando a página de edição de um edital existente, modificando campos, alterando o status e verificando que as alterações são salvas corretamente.

**Acceptance Scenarios**:

1. **Given** que um administrador está autenticado, **When** ele acessa a página de edição de um edital e modifica campos, **Then** as alterações são salvas e refletidas na visualização pública
2. **Given** que um edital está publicado, **When** um administrador altera o status para "rascunho", **Then** o edital não é mais visível na lista pública
3. **Given** que um administrador está editando um edital, **When** ele modifica o campo 'url' com um novo link externo, **Then** o link é atualizado e exibido na página de detalhe do edital
4. **Given** que um administrador tenta editar um edital com dados inválidos (ex: end_date < start_date), **When** ele submete o formulário, **Then** ele recebe mensagens de erro de validação específicas

---

### User Story 5 - Filtrar e Paginar Editais na Interface Administrativa (Priority: P3)

Como administrador, quero filtrar e paginar a lista de editais na interface administrativa para gerenciar eficientemente grandes volumes de editais.

**Why this priority**: Esta funcionalidade melhora a experiência do administrador, mas não é crítica para o MVP. O sistema pode funcionar com uma lista simples inicialmente.

**Independent Test**: Pode ser totalmente testado fazendo login como staff/admin, acessando a lista administrativa de editais e verificando que os filtros (status, data, organização) funcionam corretamente e que a paginação é exibida quando há muitos editais.

**Acceptance Scenarios**:

1. **Given** que existem muitos editais no sistema, **When** um administrador acessa a lista administrativa, **Then** a lista é paginada e ele pode navegar entre páginas
2. **Given** que existem editais com diferentes status, **When** um administrador filtra por status na interface administrativa, **Then** apenas editais com aquele status são exibidos
3. **Given** que um administrador está na lista administrativa, **When** ele busca por título ou organização, **Then** a lista é filtrada dinamicamente

---

### Edge Cases

- **What happens when** um visitante busca por um termo que não corresponde a nenhum edital? → Sistema deve exibir mensagem "Nenhum edital encontrado" e manter os filtros aplicados
- **What happens when** um edital tem data de fim no passado mas status ainda está como "aberto"? → Sistema deve atualizar status automaticamente para 'fechado' (via management command diário) e manter edital visível na lista pública
- **How does system handle** tentativa de criar edital com título que gera slug duplicado? → Sistema deve gerar slug automaticamente adicionando sufixo numérico (-2, -3, etc.) para garantir unicidade
- **What happens when** um administrador tenta deletar um edital? → Sistema deve exibir confirmação modal ("Tem certeza que deseja deletar este edital?") antes de deletar
- **How does system handle** busca com caracteres especiais ou SQL injection attempts? → Sistema deve sanitizar entrada e usar Django ORM (icontains) para prevenir SQL injection
- **What happens when** um visitante acessa um edital com slug inválido ou que não existe? → Sistema deve retornar erro 404 com página de erro customizada
- **What happens when** um edital é criado com data de início no futuro? → Sistema deve definir status como 'programado' automaticamente
- **How does system handle** editais com prazo próximo (últimos 7 dias)? → Sistema deve exibir aviso visual "Prazo próximo" na lista pública

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST exibir uma lista paginada de editais publicados na rota pública `/editais/`
- **FR-002**: System MUST permitir busca de editais por título, organização e palavras-chave através de campo de busca
- **FR-003**: System MUST permitir filtrar editais por status (aberto/fechado/encerrado) na interface pública
- **FR-004**: System MUST exibir detalhes completos de um edital na rota `/editais/<slug>/` incluindo todos os metadados (upload de anexos REMOVIDO do MVP)
- **FR-005**: System MUST permitir que administradores (staff) criem novos editais através de interface administrativa
- **FR-006**: System MUST permitir que administradores editem editais existentes, incluindo atualização de campos (upload de anexos REMOVIDO do MVP)
- **FR-007**: System MUST permitir que administradores deletem editais (confirmação antes de deletar)
- **FR-008**: System MUST validar que slugs de editais são únicos no banco de dados (gerados automaticamente, não editáveis)
- **FR-009**: System MUST manter campo 'url' no modelo Edital para links externos (upload de anexos REMOVIDO do MVP)
- **FR-010**: System MUST exibir editais com status 'aberto', 'em_andamento' e 'fechado' para visitantes não-autenticados (não exibir 'draft')
- **FR-011**: System MUST permitir que administradores e usuários com permissão CRUD vejam editais em status 'draft' (rascunho)
- **FR-012**: System MUST implementar paginação numérica com 5 páginas visíveis e permitir alterar itens por página (20, 50, 100)
- **FR-013**: System MUST validar datas de início e fim, garantindo que data de fim seja posterior à data de início (usar start_date/end_date do Edital)
- **FR-014**: System MUST armazenar informação de quem criou/atualizou cada edital (created_by, updated_by)
- **FR-015**: System MUST sanitizar conteúdo HTML em campos de texto para prevenir XSS attacks
- **FR-016**: System MUST usar localização pt-BR para templates, mensagens e formatos de data (todos os campos e rótulos em português)
- **FR-017**: System MUST configurar TIME_ZONE como "America/Sao_Paulo" no Django settings
- **FR-018**: System MUST gerar slugs automaticamente a partir do título usando slugify, removendo acentos, adicionando sufixo numérico se duplicado, e slugs NÃO podem ser editados manualmente
- **FR-019**: System MUST usar apenas campos em português (objetivo, criterios_elegibilidade, etc.) - NÃO adicionar campos em inglês (description, requirements)
- **FR-020**: System MUST implementar busca case-insensitive em título, objetivo, análise, número do edital e entidade principal, modo "contém", após submit do formulário
- **FR-021**: System MUST combinar filtros com operador AND, aplicar filtro de data a start_date e end_date, exibir todos os editais por padrão com opção "somente abertos", e persistir filtros na URL (query parameters)
- **FR-022**: System MUST migrar URLs de PK para slug, redirecionar URLs antigas (301) para novas URLs baseadas em slug, e gerar slugs automaticamente para todos os editais existentes
- **FR-023**: System MUST implementar sistema de permissões com múltiplos níveis (staff, editor, admin), onde usuários autenticados podem visualizar rascunhos conforme nível de permissão
- **FR-024**: System MUST atualizar status automaticamente conforme data (se end_date < hoje e status='aberto', atualizar para 'fechado'), adicionar status 'programado' para editais futuros, exibir aviso de "prazo próximo" para editais com prazo nos últimos 7 dias, e mostrar editais encerrados na lista pública
- **FR-025**: System MUST otimizar queries com select_related e prefetch_related, e habilitar cache para listagens públicas (TTL: 5 minutos)
- **FR-026**: System MUST usar Django Admin com mesmo layout visual do site, incluir preview antes de publicar, e suportar rascunhos automáticos (fase futura)
- **FR-027**: System MUST exibir mensagens amigáveis em português, mensagens de sucesso após operações CRUD, exibir erros no canto inferior direito (toast notifications), confirmar antes de deletar, e mensagens temporárias (desaparecem após 5 segundos)

### Key Entities *(include if feature involves data)*

- **Edital**: Representa um edital de fomento. Atributos principais: título, slug (único, gerado automaticamente), organização (entidade_principal), objetivo, critérios de elegibilidade, data de início (start_date), data de fim (end_date), status (draft/aberto/em_andamento/fechado/programado), criado por, datas de criação/atualização. Relacionamentos: tem muitos cronogramas (Cronograma), criado por usuário (User). **NOTA**: Upload de anexos REMOVIDO do MVP; manter campo 'url' para links externos.

- **Cronograma**: Representa etapas e cronogramas distintos de um edital. Atributos principais: data_inicio, data_fim, data_publicacao, descricao. Relacionamentos: pertence a um Edital (ForeignKey com CASCADE).

- **User** (Django built-in): Representa usuários do sistema. Sistema de permissões com múltiplos níveis (staff, editor, admin). Usuários com permissão CRUD podem ver/edit/criar/deletar editais. Visitantes não-autenticados só podem visualizar editais publicados (status: aberto, em_andamento, fechado).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Visitantes conseguem encontrar editais relevantes através de busca em menos de 3 cliques desde a página inicial
- **SC-002**: Sistema exibe lista de editais com paginação carregando em menos de 2 segundos mesmo com 100+ editais no banco
- **SC-003**: Administradores conseguem criar um novo edital completo (com metadados) em menos de 5 minutos
- **SC-004**: 100% dos editais criados são válidos (sem erros de validação que impeçam exibição pública)
- **SC-005**: Testes unitários e de integração alcançam cobertura mínima de 85% para o módulo de editais
- **SC-006**: Sistema previne completamente tentativas de SQL injection e XSS através de validação e sanitização
- **SC-007**: Sistema gera slugs únicos automaticamente com 100% de precisão (nunca cria slugs duplicados)
- **SC-008**: Interface administrativa permite gerenciar (criar/editar/deletar) editais sem erros para 100% das operações válidas, com confirmação antes de deletar
- **SC-009**: Todos os templates e mensagens do sistema estão em português brasileiro (pt-BR)
- **SC-010**: Sistema está pronto para produção com DEBUG=False, ALLOWED_HOSTS configurado, WhiteNoise para static files

## Technical Implementation Details

### Modelo de Dados (Django Models)

**Nota**: Esta é a estrutura alvo. Campos existentes serão mantidos durante migração. Ver seção "Migration Strategy" para detalhes.

```python
class Edital(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Rascunho'),  # NOVO - visível apenas para usuários com permissão CRUD
        ('aberto', 'Aberto'),  # EXISTENTE - edital aceitando submissões (público)
        ('em_andamento', 'Em Andamento'),  # EXISTENTE - edital fechado para submissões (público)
        ('fechado', 'Fechado'),  # EXISTENTE - encerrado (histórico) (público)
        ('programado', 'Programado'),  # NOVO - edital com data de início no futuro
    ]
    
    # Campos existentes (manter)
    numero_edital = models.CharField(max_length=100, blank=True, null=True)
    titulo = models.CharField(max_length=500)
    url = models.URLField(max_length=1000, blank=True)  # Link externo (upload de anexos REMOVIDO do MVP)
    entidade_principal = models.CharField(max_length=200, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='aberto')
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_editais')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='updated_editais')
    
    # Campos de conteúdo existentes (manter - todos em português)
    analise = models.TextField(blank=True)
    objetivo = models.TextField(blank=True)
    etapas = models.TextField(blank=True)
    recursos = models.TextField(blank=True)
    itens_financiaveis = models.TextField(blank=True)
    criterios_elegibilidade = models.TextField(blank=True)
    criterios_avaliacao = models.TextField(blank=True)
    itens_essenciais_observacoes = models.TextField(blank=True)
    detalhes_unirv = models.TextField(blank=True)
    
    # NOVOS campos a adicionar
    slug = models.SlugField(unique=True, max_length=255)  # Gerado automaticamente, não editável
    start_date = models.DateField(blank=True, null=True)  # Data de abertura
    end_date = models.DateField(blank=True, null=True)  # Data de encerramento geral
    
    def save(self, *args, **kwargs):
        # Gerar slug automaticamente apenas se não existir (slug não muda se título mudar)
        if not self.slug:
            self.slug = self._generate_unique_slug()
        # Definir status 'programado' se start_date > hoje
        from django.utils import timezone
        if self.start_date and self.start_date > timezone.now().date():
            if self.status == 'aberto':
                self.status = 'programado'
        super().save(*args, **kwargs)
    
    def _generate_unique_slug(self):
        """Gera slug único a partir do título"""
        from django.utils.text import slugify
        base_slug = slugify(self.titulo)
        slug = base_slug
        # Excluir o próprio objeto da verificação (se estiver editando)
        queryset = Edital.objects.filter(slug=slug)
        if self.pk:
            queryset = queryset.exclude(pk=self.pk)
        # Se slug base já existe, começar com -2, -3, etc.
        if queryset.exists():
            counter = 2
            slug = f"{base_slug}-{counter}"
            queryset = Edital.objects.filter(slug=slug)
            if self.pk:
                queryset = queryset.exclude(pk=self.pk)
            while queryset.exists():
                counter += 1
                slug = f"{base_slug}-{counter}"
                queryset = Edital.objects.filter(slug=slug)
                if self.pk:
                    queryset = queryset.exclude(pk=self.pk)
        return slug
    
    class Meta:
        ordering = ['-data_atualizacao']
        verbose_name = 'Edital'
        verbose_name_plural = 'Editais'
        indexes = [
            models.Index(fields=['-data_atualizacao'], name='idx_data_atualizacao'),
            models.Index(fields=['status'], name='idx_status'),
            models.Index(fields=['entidade_principal'], name='idx_entidade'),
            models.Index(fields=['numero_edital'], name='idx_numero'),
            models.Index(fields=['slug'], name='idx_slug'),  # NOVO
            models.Index(fields=['status', 'start_date', 'end_date'], name='idx_status_dates'),  # NOVO
            models.Index(fields=['titulo'], name='idx_titulo'),  # NOVO - para busca
        ]

# Modelos existentes a manter
class Cronograma(models.Model):
    """EXISTENTE - manter para cronogramas detalhados/múltiplas etapas"""
    edital = models.ForeignKey(Edital, on_delete=models.CASCADE, related_name='cronogramas')
    data_inicio = models.DateField(blank=True, null=True)
    data_fim = models.DateField(blank=True, null=True)
    data_publicacao = models.DateField(blank=True, null=True)
    descricao = models.CharField(max_length=300, blank=True)
    
    class Meta:
        ordering = ['data_inicio']
        verbose_name = 'Cronograma'
        verbose_name_plural = 'Cronogramas'

class EditalValor(models.Model):
    """EXISTENTE - manter para valores financeiros"""
    edital = models.ForeignKey(Edital, on_delete=models.CASCADE, related_name='valores')
    valor_total = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    moeda = models.CharField(max_length=10, default='BRL')
    
    class Meta:
        verbose_name = 'Valor do Edital'
        verbose_name_plural = 'Valores dos Editais'

# NOTA: EditalFavorite existe mas NÃO será usado no MVP (funcionalidade removida)
# Modelo mantido no banco para compatibilidade, mas não implementado na interface
```

### Endpoints / URLs

**URLs Públicas:**
- `GET /editais/` — Listagem pública (query params: `q`, `status`, `page`, `data_inicio`, `data_fim`, `somente_abertos`)
- `GET /editais/<slug>/` — Detalhe público (usar slug) - **NOVO**
- `GET /editais/<pk>/` — Detalhe público (usar PK) - **EXISTENTE** (redirecionar 301 para slug durante migração)

**URLs Administrativas:**
- `GET /admin/editais/` — Listagem administrativa (Django Admin ou custom)
- `POST /admin/editais/create/` — Criar edital (staff only)
- `GET /admin/editais/<slug>/edit/` — Formulário de edição (staff only) - **NOVO** (usar slug)
- `GET /admin/editais/<pk>/edit/` — Formulário de edição (staff only) - **EXISTENTE** (manter durante migração)
- `POST /admin/editais/<slug>/edit/` — Atualizar edital (staff only) - **NOVO**
- `POST /admin/editais/<pk>/edit/` — Atualizar edital (staff only) - **EXISTENTE** (manter durante migração)
- `POST /admin/editais/<slug>/delete/` — Deletar edital (staff only) - **NOVO**
- `POST /admin/editais/<pk>/delete/` — Deletar edital (staff only) - **EXISTENTE** (manter durante migração)

**Nota de Migração**: Durante a migração, suportar ambas as formas (PK e slug). Após período de transição, deprecar URLs baseadas em PK e redirecionar para URLs baseadas em slug.

### Templates (UX)

- `editais/list.html` — Search bar, filtros (status, datas, "somente abertos"), cards com resumo (título, organização, datas, status, aviso "prazo próximo"), paginação numérica (5 páginas visíveis), opção para alterar itens por página
- `editais/detail.html` — Header com título e status, metadados, objetivo formatado, critérios de elegibilidade, cronogramas, link externo (url), aviso "prazo próximo" se aplicável
- `admin/editais/create.html` — Formulário para criar edital com validação (Django Admin customizado)
- `admin/editais/update.html` — Formulário para editar edital existente (Django Admin customizado)
- `admin/editais/delete.html` — Confirmação de exclusão (modal ou página de confirmação)

### Security Requirements

- SECRET_KEY em variável de ambiente (.env)
- CSRF habilitado para todas as operações de escrita
- Permissões: CRUD apenas para usuários com permissão (sistema de permissões com múltiplos níveis: staff, editor, admin)
- Sanitização de HTML em campos de texto (usar bleach)
- Validação de slugs: gerados automaticamente com slugify (previne caracteres perigosos)
- Proteção contra SQL injection (usar Django ORM exclusivamente - icontains para busca)
- Validação de datas: end_date deve ser posterior a start_date

### Performance Requirements

- Paginação: 20 itens por página (padrão), opção para alterar (20, 50, 100)
- Indexação de campos de busca: titulo, start_date, end_date, status, slug, entidade_principal
- Otimização de queries: usar select_related para created_by/updated_by, prefetch_related para cronogramas
- Minimizar database queries por página (usar Django Debug Toolbar em development)
- Cache de listagens públicas: habilitado com TTL de 5 minutos (configurável)

### Quality Requirements

- PEP 8 compliance
- Cobertura de testes: mínimo 85%
- Linting: flake8, black (opcional)
- Type hints: mypy (opcional)
- Testes unitários para models, views, forms
- Testes de integração para fluxos completos (criar, editar, deletar, visualizar)

### Localization Requirements

- LANGUAGE_CODE = 'pt-br'
- TIME_ZONE = 'America/Sao_Paulo'
- Templates em português brasileiro
- Mensagens de erro e validação em português
- Formatos de data e número seguindo padrões brasileiros

### Production Readiness

- DEBUG = False em produção
- ALLOWED_HOSTS configurado
- WhiteNoise para servir arquivos estáticos
- Gunicorn como WSGI server
- Nginx como reverse proxy (documentar)
- Backup de banco de dados configurado
- Logging configurado para produção

## Out of Scope (Futuras Fases)

- Sistema de notificações personalizadas (email / in-app) — planejar apenas
- Acompanhamento personalizado de editais e recomendação (ML)
- Integração SSO institucional (apenas autenticação Django por ora)
- Upload de anexos — REMOVIDO do MVP, será implementado em fase futura
- Sistema de "salvar" (antigo favoritos) para usuários autenticados — será implementado em fase futura com nova nomenclatura
- Campo de localização e filtro por localização — REMOVIDO do MVP, será implementado em fase futura se necessário
- API REST completa (/api/v1/editais/) — pode ser adicionada em fase futura
- Comentários e avaliações de editais — pode ser adicionado em fase futura
- Rascunhos automáticos no Django Admin — pode ser implementado em fase futura

## Dependencies

- Django >= 5.2.7
- WhiteNoise >= 6.7.0 (para static files)
- bleach >= 6.1.0 (para sanitização de HTML)
- Pillow (opcional, para processamento de imagens se necessário no futuro)
- python-decouple ou django-environ (para gerenciamento de variáveis de ambiente)

## Migration Strategy

### Estado Atual vs. Especificação

**Modelos Existentes:**
- `Edital` com campos: `numero_edital`, `titulo`, `url`, `entidade_principal`, `status` ('aberto', 'fechado', 'em_andamento'), campos de conteúdo detalhados (`analise`, `objetivo`, `etapas`, etc.)
- `Cronograma` (separado, relacionado a Edital) com `data_inicio`, `data_fim`, `data_publicacao`
- `EditalValor` para valores financeiros
- `EditalFavorite` para favoritos de usuários
- URLs usam PK (`/editais/<pk>/`) ao invés de slug

**Alterações Necessárias:**
1. Adicionar campo `slug` ao modelo Edital (único, gerado automaticamente a partir do título, não editável)
2. Adicionar campos `start_date` e `end_date` diretamente ao Edital (manter relação com Cronograma para cronogramas detalhados)
3. Atualizar status choices para incluir 'draft' (rascunho) e 'programado' (editais futuros)
4. Migrar URLs de PK para slug (com redirecionamento 301)
5. Manter compatibilidade com dados existentes durante migração (base vazia - nenhuma migração de dados necessária)
6. **NÃO adicionar campo `location`** (removido do MVP - será implementado em fase futura se necessário)
7. **NÃO adicionar campos em inglês** (`description`, `requirements`) - usar apenas campos em português existentes
8. **NÃO criar modelo `EditalAttachment`** (upload de anexos removido do MVP - manter apenas campo 'url' para links externos)

### Plano de Implementação

1. **Fase 1: Preparação**
   - Analisar dados existentes (base vazia - nenhuma migração de dados necessária)
   - Criar migration para adicionar novos campos (slug, start_date, end_date)
   - Criar data migration para popular slugs a partir de títulos existentes (se houver dados)
   - Adicionar status 'draft' e 'programado' aos STATUS_CHOICES

2. **Fase 2: Modelos**
   - Adicionar campos faltantes ao modelo `Edital` (slug, start_date, end_date)
   - Implementar método `_generate_unique_slug()` no modelo Edital
   - Implementar lógica de status automático no método `save()`
   - Atualizar índices conforme especificação
   - Manter modelos existentes (Cronograma, EditalValor) para compatibilidade
   - **NÃO criar modelo EditalAttachment** (upload de anexos REMOVIDO do MVP)

3. **Fase 3: Migração de URLs**
   - Adicionar suporte a slug nas URLs
   - Manter compatibilidade com URLs antigas (PK) durante período de transição
   - Atualizar `get_absolute_url()` para usar slug

4. **Fase 4: Views e Templates**
   - Implementar views públicas (list, detail) com busca e filtros
   - Implementar views administrativas (create, update, delete) usando Django Admin
   - Criar templates públicos e administrativos
   - Implementar sistema de permissões (staff, editor, admin)
   - Implementar redirecionamento de URLs PK para slug (301)
   - **NÃO implementar upload de anexos** (REMOVIDO do MVP)

5. **Fase 5: Testes e Qualidade**
   - Adicionar testes unitários e de integração
   - Alcançar cobertura mínima de 85%
   - Configurar permissões e segurança
   - Implementar management command para atualizar status automaticamente
   - Implementar cache para listagens públicas
   - Validar conformidade com Constituição

6. **Fase 6: Deploy**
   - Testar em ambiente de desenvolvimento
   - Revisar migrações em ambiente de staging
   - Deploy em produção

## Notes

- Este módulo é a base do sistema AgroHub UniRV
- Focar em MVP inicial: funcionalidades públicas de listagem/detalhe e CRUD administrativo
- Planejar extensibilidade para funcionalidades futuras (notificações, ML, etc.)
- Manter conformidade com a Constituição do projeto (segurança, TDD, Django best practices)
- **IMPORTANTE**: O sistema já possui modelos e estrutura básica. Esta especificação define a estrutura alvo e o caminho de migração deve ser cuidadosamente planejado para manter compatibilidade com dados existentes.
- Considerar manter campos existentes (`numero_edital`, `url`, campos detalhados) e adicionar novos campos gradualmente
- Sistema de favoritos (`EditalFavorite`) já existe mas está marcado como "out of scope" - considerar manter funcionalidade existente

## Clarifications Status

**✅ TODAS AS CLARIFICAÇÕES RESOLVIDAS** (2025-11-11)

Ver documento **`clarifications.md`** para detalhes completos de todas as decisões tomadas.

**Resumo das principais decisões:**
1. ✅ **Status**: draft (rascunho), aberto, em_andamento, fechado, programado (novo)
2. ✅ **Datas**: Manter Cronograma + adicionar start_date/end_date ao Edital
3. ✅ **Campos**: Usar apenas campos em português (remover description, requirements)
4. ✅ **Slug**: Gerar automaticamente, não editável, adicionar sufixo se duplicado
5. ✅ **Busca**: Case-insensitive, modo "contém", após submit
6. ✅ **Filtros**: Combinados com AND, persistir na URL, opção "somente abertos"
7. ✅ **Upload**: REMOVIDO do MVP (manter apenas campo 'url' para links externos)
8. ✅ **Status automático**: Atualizar automaticamente baseado em datas, aviso "prazo próximo"
9. ✅ **Favoritos**: REMOVIDO do MVP (será "salvar" em fase futura)
10. ✅ **Localização**: REMOVIDO do MVP
11. ✅ **Permissões**: Múltiplos níveis (staff, editor, admin)
12. ✅ **Paginação**: Numérica, 5 páginas visíveis, opção para alterar itens por página
13. ✅ **Cache**: Habilitado para listagens públicas (TTL: 5 minutos)
14. ✅ **Admin**: Django Admin customizado, preview antes de publicar
15. ✅ **Mensagens**: Toast notifications, mensagens amigáveis, confirmação antes de deletar

**Status**: Pronto para implementação. Todas as decisões foram documentadas.

