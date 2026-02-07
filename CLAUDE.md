# CLAUDE.md - Guia do Projeto AgroHub

## Visão Geral do Projeto
Aplicação web Django 5.2+ para o **AgroHub** - Hub de Inovação e Fomento da Universidade de Rio Verde (UniRV). A plataforma gerencia editais de fomento, apresenta startups incubadas e o ecossistema de inovação incluindo:
- **YPETEC**: Incubadora de startups da UniRV
- **InovaLab**: Laboratório de desenvolvimento tecnológico (software, impressoras 3D, prototipagem)

Interface em português (pt-BR).

## Comandos Rápidos

```bash
# Setup
python -m venv .venv && .venv\Scripts\activate  # Windows
pip install -r requirements.txt
cd theme/static_src && npm ci && npm run build && cd ../..

# Banco de Dados
python manage.py migrate
python manage.py createsuperuser

# Desenvolvimento
python manage.py runserver                    # Iniciar servidor
cd theme/static_src && npm run dev           # Monitorar CSS Tailwind

# Build dos Assets
cd theme/static_src && npm run build         # Build completo (CSS + JS + vendor)
npm run build:tailwind                       # Apenas Tailwind CSS
npm run build:js                             # Minificar arquivos JS
npm run build:vendor                         # Copiar FontAwesome/GSAP

# Testes
python manage.py test editais                 # Executar todos os testes
coverage run --source='editais' manage.py test editais && coverage report

# Linting & Segurança
ruff check editais/ UniRV_Django/            # Executar linter
bandit -r editais/ UniRV_Django/ -ll -ii     # Verificação de segurança

# Dados de Exemplo
python manage.py seed_editais                 # Popular editais de exemplo
python manage.py seed_startups                # Popular startups de exemplo

# Docker
docker-compose up --build -d  # Primeira vez
docker-compose logs -f web                   # Ver logs
docker-compose exec web python manage.py createsuperuser
docker-compose down                          # Parar
```

## Estrutura do Projeto

```
editais/                  # App principal Django
├── models.py            # Modelos Edital, EditalValor, Cronograma, Startup, Tag
├── views/               # Views organizadas
│   ├── public.py        # Views públicas
│   ├── dashboard.py     # Views do dashboard admin
│   ├── editais_crud.py  # Operações CRUD
│   └── mixins.py        # Mixins reutilizáveis
├── views.py             # Re-exports de views/ para compatibilidade reversa
├── services.py          # Camada de lógica de negócio
├── utils.py             # Funções auxiliares (slug, sanitização)
├── decorators.py        # Decoradores customizados (@rate_limit, @staff_required, cache)
├── forms.py             # Definições de formulários com sanitização HTML
├── constants/           # Pacote de constantes
│   ├── cache.py         # Chaves de cache e TTLs
│   ├── limits.py        # Limites de tamanho, paginação, upload
│   └── status.py        # Escolhas de status, rótulos
└── tests/               # Testes (85% cobertura obrigatória)
    ├── factories.py     # Fixtures factory-boy
    ├── test_dashboard_views.py
    ├── test_startup_model.py
    └── test_*.py        # Testes por feature

static/                   # Recursos estáticos
├── css/                  # CSS customizado
│   ├── animations.css   # Animações orbit, toast, carousel
│   ├── detail.css       # Página de detalhes
│   └── print.css        # Estilos para impressão
├── js/                   # JavaScript
│   ├── main.js          # UI principal (menu, toast, modals, forms, scroll-to-error)
│   ├── animations.js    # Animações GSAP
│   ├── animations-native.js  # Fallback CSS/IntersectionObserver
│   ├── editais-index.js # Página de listagem
│   ├── edital-form.js   # Manipulação de forms com autosave
│   └── *.min.js         # Versões minificadas (produção)
├── fonts/                # Fontes Inter + Montserrat
├── img/                  # Imagens e backgrounds herói
└── vendor/               # Bibliotecas terceiras
    ├── fontawesome/      # Ícones Font Awesome
    └── gsap/             # Biblioteca GSAP

theme/static_src/         # Sistema de build frontend
├── src/styles.css       # CSS Tailwind fonte
├── package.json         # Scripts npm (build, dev)
└── scripts/             # Utilitários de build

templates/               # Templates globais
├── base.html            # Template base
├── home.html            # Homepage
├── dashboard/           # Templates dashboard admin
├── editais/             # Templates CRUD editais
├── startups/            # Templates startups
└── components/          # Componentes reutilizáveis

UniRV_Django/            # Configuração do projeto
├── settings.py          # Configurações Django
└── urls.py              # Roteamento URL raiz

docker/                   # Deploy Docker
├── nginx/
│   ├── nginx.conf       # Config Nginx principal
│   ├── conf.d/
│   │   └── default.conf # Configuração do site
│   └── ssl/             # Certificados SSL (gitignore)
└── postgres/
    └── init/            # Scripts inicialização DB
```

## Dependências

### Runtime (`requirements.txt`)
- Dependências fixadas com versão menor (~) (ex: Django>=5.2.8,<6.0)
- PostgreSQL, Redis, Pillow, bleach, django-simple-history, etc.

### Desenvolvimento (`requirements-dev.txt`)
- Testes: `factory_boy`, `coverage`
- Linting: `ruff`
- Segurança: `bandit`, `pip-audit`
- Debug: `django-debug-toolbar`

## Pipeline de Build

| Origem | Saída | Comando |
|--------|-------|---------|
| `theme/static_src/src/styles.css` | `theme/static/css/dist/styles.css` | `npm run build:tailwind` |
| `static/js/*.js` | `static/js/*.min.js` | `npm run build:js` |
| `node_modules/@fortawesome` | `static/vendor/fontawesome/` | `npm run build:vendor` |
| `node_modules/gsap` | `static/vendor/gsap/` | `npm run build:vendor` |

## Padrões de Código

### Models
- **QuerySets customizados** com métodos encadeáveis: `.active()`, `.search()`, `.with_related()`, `.with_prefetch()`
- **Rastreamento histórico** via `django-simple-history` no modelo Edital
- **Full-text search PostgreSQL** com fallback para `icontains` em SQLite
- **Sanitização HTML** usando `bleach` em métodos `save()`
- **Constantes** para números mágicos (ex: `MAX_LOGO_FILE_SIZE` em `constants/limits.py`)

### Views
- Organizadas em diretório `editais/views/`
- `editais/views.py` re-exporta para compatibilidade reversa
- Class-based views com mixins customizados para cache e filtros
- Todos os imports no nível de módulo (sem imports tardiços dentro de funções)

### Admin
- Otimização de query com `list_select_related` e `list_prefetch_related` em todas as classes
- Previne queries N+1 em list views

### Segurança
- Rate limiting via decorador customizado `@rate_limit` em `decorators.py`
- Prevenção XSS: sanitização `bleach` em entrada de usuário
- CSRF protection habilitado
- Decorador `@staff_required` para views admin
- Tratamento específico de exceções (nunca `except Exception`)

### Frontend
- Sem event handlers inline (`onclick`, `onload`) - usar JS externo com event listeners
- Autosave com prevenção apropriada de memory leak (cleanup em `beforeunload`/`pagehide`)
- Auto scroll-to-error em falhas de validação de form

### Testes
- Usar `factory-boy` para fixtures (ver `editais/tests/factories.py`)
- Factories disponíveis: `UserFactory`, `StaffUserFactory`, `EditalFactory`, `StartupFactory`, `TagFactory`, `EditalValorFactory`, `CronogramaFactory`
- Arquivos de teste nomeados por feature: `test_<feature>.py`
- CI força limite de 85% de cobertura

#### Considerações de Testes em SQLite
- Usar `TestCase` para maioria dos testes (mais rápido, isolamento apropriado de transações)
- Usar `TransactionTestCase` apenas ao testar callbacks `transaction.on_commit()` (ex: invalidação de cache)
- **Isolamento de conexão SQLite in-memory**: Alguns testes de redirect são pulados em SQLite por issues de isolamento de conexão entre TestCase do Django e test client. Esses testes passam em PostgreSQL.
- Ao usar `StartupFactory`, passar `edital=` explícito para evitar SubFactory criar editais extras
- Para `TransactionTestCase`, adicionar cleanup em `setUp()` para prevenir vazamento de dados entre testes

#### Padrões de Teste
```python
# Para testes de invalidação de cache - usar TransactionTestCase
class CacheInvalidationTest(TransactionTestCase):
    def setUp(self):
        # Limpar dados para prevenir vazamento de outros TransactionTestCase
        Edital.objects.all().delete()
        Startup.objects.all().delete()
        cache.clear()

# Para testes de redirect afetados por SQLite - usar skipIf
from unittest import skipIf
SKIP_SQLITE = 'sqlite' in settings.DATABASES['default']['ENGINE']

@skipIf(SKIP_SQLITE, "SQLite in-memory tem issues de isolamento de conexão")
def test_redirect_by_pk(self):
    ...

# Ao criar startups com contagem específica de edital
edital = EditalFactory(status='aberto')
StartupFactory(proponente=user, edital=edital)  # Edital explícito, sem extra criado
```

## Modelos Principais

| Modelo | Propósito |
|--------|-----------|
| `Edital` | Entidade principal de edital de fomento |
| `EditalValor` | Valores financeiros (min/máx) |
| `Cronograma` | Timeline/prazos |
| `Startup` | Showcase de startups registradas |
| `Tag` | Tags de categorização |

## JavaScript Principal

| Arquivo | Propósito |
|---------|-----------|
| `main.js` | UI principal: menu mobile, toasts, modals, validação forms, scroll-to-error |
| `animations.js` | Animações GSAP (home, startups, editais) |
| `animations-native.js` | Fallback CSS/IntersectionObserver quando GSAP indisponível |
| `editais-index.js` | Listagem editais: busca, filtros, carregamento AJAX |
| `edital-form.js` | Manipulação forms: campos dinâmicos, validação, autosave com cleanup |

## Sistema de Design

### Paleta de Cores
| Token | Valor | Uso |
|-------|-------|-----|
| `primary` | #2563EB | Botões, links, destaques |
| `primary-hover` | #1d4ed8 | Estados hover |
| `darkblue` | #1e3a8a | Backgrounds herói, footer |
| `secondary` | #22c55e | Destaque verde (tema agro) |
| `background-light` | #F8FAFC | Backgrounds página |
| `surface-light` | #FFFFFF | Cards, painéis |
| `text-light` | #1E293B | Texto corpo |
| `text-muted` | #64748B | Texto secundário |

Aliases legadas preservados: `unirvBlue` → `primary`, `agrohubBlue` → `primary-hover`

### Tipografia
- **Display/Headings**: Montserrat (pesos: 400, 600, 700, 800)
- **Texto Corpo**: Inter (pesos: 300, 400, 500, 600, 700)
- Fontes auto-hospedadas em `static/fonts/`

### Sistemas de Ícones
- **Material Icons Outlined**: Carregado via CDN em `base.html`, usado para elementos UI
- **FontAwesome 6.5.2**: Auto-hospedado em `static/vendor/fontawesome/`, usado para ícones de features

### Padrões CSS
- **Glassmorphism**: `bg-white/95 backdrop-blur-lg border-white/20`
- **Card hover**: `hover:-translate-y-1 transition duration-300 shadow-xl`
- **Overlays gradiente**: `bg-gradient-to-r from-darkblue to-primary`
- **Tokens de tema**: Definidos em bloco `@theme` em `styles.css`

## Variáveis de Ambiente
Copiar `.env.example` para `.env` e configurar:
- `DEBUG` - Definir como False em produção
- `SECRET_KEY` - Chave secreta Django
- `DATABASE_URL` - Conexão PostgreSQL (opcional, padrão SQLite)
- `REDIS_URL` - Backend de cache (opcional)

## Pipeline CI/CD
GitHub Actions (`.github/workflows/test.yml`):
1. **Linting** - `ruff check` para qualidade de código
2. **Verificação de Segurança** - `bandit` para detecção de vulnerabilidades
3. **Testes** - Suite de testes Django com cobertura
4. **Verificação de Cobertura** - Limite de 85% enforçado
5. **Comentários em PR** - Relatórios automáticos de cobertura

## Deploy em Produção com Docker

### Arquitetura
```
         [Internet]
              │
              ▼
       ┌─────────────┐
       │    Nginx    │ :80/:443
       │  (proxy)    │ Arquivos estáticos/mídia
       └──────┬──────┘
              │
              ▼
       ┌─────────────┐
       │   Django    │ :8000 (interno)
       │  (Gunicorn) │
       └──────┬──────┘
              │
       ┌──────┴──────┐
       ▼             ▼
┌───────────┐  ┌───────────┐
│ PostgreSQL│  │   Redis   │
│  :5432    │  │   :6379   │
└───────────┘  └───────────┘
```

### Arquivos Docker
| Arquivo | Propósito |
|---------|-----------|
| `Dockerfile` | Build multi-estágio (Node + Python), usuário não-root, HEALTHCHECK |
| `docker-compose.yml` | Orquestração produção (db, redis, web, nginx) |
| `docker-entrypoint.sh` | Espera DB/Redis, migrações, Gunicorn otimizado |
| `.env.docker` | Template ambiente para deploy Docker |
| `docker/nginx/nginx.conf` | Config Nginx principal (gzip, rate limiting) |
| `docker/nginx/conf.d/default.conf` | Config site (proxy, estático, headers segurança) |

### Deploy Rápido
```bash
# Primeira vez
cp .env.docker .env
# Editar .env: SECRET_KEY, DB_PASSWORD, ALLOWED_HOSTS

# Build e start
docker-compose up --build -d

# Ver logs
docker-compose logs -f web

# Criar superusuário
docker-compose exec web python manage.py createsuperuser

# Health check
curl http://localhost/health/
```

### Named Volumes
| Volume | Container | Propósito |
|--------|-----------|-----------|
| `postgres_data` | db | Persistência database |
| `redis_data` | redis | Persistência cache |
| `media_data` | web, nginx | Uploads do usuário |
| `static_data` | web, nginx | Arquivos estáticos coletados |
| `logs_data` | web | Logs de aplicação |

### Variáveis de Ambiente (Docker)
**Obrigatórias:**
- `SECRET_KEY` - Chave secreta Django
- `ALLOWED_HOSTS` - Domínio(s), separados por vírgula
- `DB_PASSWORD` - Senha PostgreSQL

**Auto-configuradas:**
- `DB_HOST=db` - Nome de host container
- `REDIS_HOST=redis` - Nome de host container

Ver `.env.docker` para lista completa com padrões.

## Notas Importantes
- Idioma: Português (pt-BR)
- Fuso Horário: America/Sao_Paulo
- Banco de Dados: PostgreSQL (produção), SQLite (desenvolvimento)
- CI: GitHub Actions executa linting, verificação de segurança, testes e cobertura em PRs
