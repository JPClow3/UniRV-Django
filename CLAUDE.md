# CLAUDE.md - AgroHub Project Guide

## Project Overview
Django 5.2+ web application for **AgroHub** - the Innovation and Funding Hub of Universidade de Rio Verde (UniRV). The platform manages funding announcements (editais de fomento), showcases incubated startups, and presents the innovation ecosystem including:
- **YPETEC**: UniRV's startup incubator
- **InovaLab**: Technology development lab (software, 3D printing, prototyping)

Portuguese language interface (pt-BR).

## Quick Commands

```bash
# Setup
python -m venv .venv && .venv\Scripts\activate  # Windows
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
cd theme/static_src && npm ci && npm run build && cd ../..

# Database
python manage.py migrate
python manage.py createsuperuser

# Development
python manage.py runserver                    # Start server
cd theme/static_src && npm run dev           # Watch Tailwind CSS

# Build Assets
cd theme/static_src && npm run build         # Full build (CSS + JS + vendor)
npm run build:tailwind                       # Tailwind CSS only
npm run build:js                             # Minify all JS files
npm run build:vendor                         # Copy FontAwesome/GSAP

# Testing
python manage.py test editais                 # Run all tests
coverage run --source='editais' manage.py test editais && coverage report

# Linting & Security
ruff check editais/ UniRV_Django/            # Run linter
bandit -r editais/ UniRV_Django/ -ll -ii     # Security scan

# Seed Data
python manage.py seed_editais                 # Sample editais
python manage.py seed_startups                # Sample startups

# Docker Deployment
cp .env.docker .env && docker-compose up --build -d  # First time
docker-compose logs -f web                            # View logs
docker-compose exec web python manage.py createsuperuser
docker-compose down                                   # Stop
```

## Project Structure

```
editais/                  # Main Django app
├── models.py            # Edital, EditalValor, Cronograma, Startup, Tag models
├── views/               # Modular views
│   ├── public.py        # Public-facing views
│   ├── dashboard.py     # Admin dashboard views
│   ├── editais_crud.py  # CRUD operations
│   └── mixins.py        # Reusable view mixins
├── views.py             # Re-exports from views/ for backward compatibility
├── services.py          # Business logic layer
├── utils.py             # Helper functions (slug generation, sanitization)
├── decorators.py        # @rate_limit, @staff_required, caching
├── forms.py             # Form definitions with HTML sanitization
├── constants/           # App constants package
│   ├── cache.py         # Cache keys and TTLs
│   ├── limits.py        # Size limits, pagination, file upload limits
│   └── status.py        # Status choices, labels
└── tests/               # Test suite (85% coverage required)
    ├── factories.py     # factory-boy fixtures (User, Edital, Startup, Tag, EditalValor, Cronograma)
    ├── test_dashboard_views.py
    ├── test_startup_model.py
    └── test_*.py        # Feature-based test files

static/                   # Static assets
├── css/                  # Custom CSS
│   ├── animations.css   # Orbit, toast, carousel animations
│   ├── detail.css       # Edital detail page
│   └── print.css        # Print styles
├── js/                   # JavaScript
│   ├── main.js          # Core UI (menu, toast, modals, forms, scroll-to-error)
│   ├── animations.js    # GSAP-based page animations
│   ├── animations-native.js  # CSS/IntersectionObserver fallback
│   ├── editais-index.js # Editais listing page
│   ├── edital-form.js   # Form handling with autosave cleanup
│   └── *.min.js         # Minified versions (production)
├── fonts/                # Self-hosted Inter + Montserrat fonts
├── img/                  # Images and hero backgrounds
└── vendor/               # Third-party libraries
    ├── fontawesome/      # Font Awesome icons
    └── gsap/             # GSAP animation library

theme/static_src/         # Frontend build system
├── src/styles.css       # Tailwind CSS source
├── package.json         # npm scripts (build, dev)
└── scripts/             # Build utilities

templates/               # Global templates
├── base.html            # Base template
├── home.html            # Homepage
├── dashboard/           # Admin dashboard templates
├── editais/             # Edital CRUD templates
├── startups/            # Startup templates
└── components/          # Reusable components

UniRV_Django/            # Project configuration
├── settings.py          # Django settings
└── urls.py              # Root URL routing

docker/                   # Docker deployment
├── nginx/
│   ├── nginx.conf       # Main Nginx config
│   ├── conf.d/
│   │   └── default.conf # Site configuration
│   └── ssl/             # SSL certificates (gitignored)
└── postgres/
    └── init/            # DB initialization scripts
```

## Dependencies

### Runtime (`requirements.txt`)
- Dependencies pinned with major version bounds (e.g., `Django>=5.2.8,<6.0`)
- PostgreSQL, Redis, Pillow, bleach, django-simple-history, etc.

### Development (`requirements-dev.txt`)
- Testing: `factory_boy`, `coverage`
- Linting: `ruff`
- Security: `bandit`, `pip-audit`
- Debug: `django-debug-toolbar`

## Build Pipeline

| Source | Output | Command |
|--------|--------|---------|
| `theme/static_src/src/styles.css` | `theme/static/css/dist/styles.css` | `npm run build:tailwind` |
| `static/js/*.js` | `static/js/*.min.js` | `npm run build:js` |
| `node_modules/@fortawesome` | `static/vendor/fontawesome/` | `npm run build:vendor` |
| `node_modules/gsap` | `static/vendor/gsap/` | `npm run build:vendor` |

## Code Patterns

### Models
- **Custom QuerySets** with chainable methods: `.active()`, `.search()`, `.with_related()`, `.with_prefetch()`
- **Historical tracking** via `django-simple-history` on Edital model
- **PostgreSQL full-text search** with fallback to `icontains` for SQLite
- **HTML sanitization** using `bleach` in model `save()` methods
- **Constants** for magic numbers (e.g., `MAX_LOGO_FILE_SIZE` in `constants/limits.py`)

### Views
- Organized in `editais/views/` directory
- `editais/views.py` re-exports for backward compatibility
- Class-based views with custom mixins for caching and filtering
- All imports at module level (no late imports inside functions)

### Admin
- Query optimization with `list_select_related` and `list_prefetch_related` on all admin classes
- Prevents N+1 queries in list views

### Security
- Rate limiting via custom `@rate_limit` decorator in `decorators.py`
- XSS prevention: `bleach` sanitization on user input
- CSRF protection enabled
- `@staff_required` decorator for admin views
- Specific exception handling (no broad `except Exception`)

### Frontend
- No inline event handlers (`onclick`, `onload`) - use external JS with event listeners
- Autosave with proper memory leak prevention (cleanup on `beforeunload`/`pagehide`)
- Auto scroll-to-error on form validation failures

### Testing
- Use `factory-boy` for fixtures (see `editais/tests/factories.py`)
- Factories available: `UserFactory`, `StaffUserFactory`, `EditalFactory`, `StartupFactory`, `TagFactory`, `EditalValorFactory`, `CronogramaFactory`
- Test files named by feature: `test_<feature>.py`
- CI enforces 85% coverage threshold

#### SQLite Test Considerations
- Use `TestCase` for most tests (faster, proper transaction isolation)
- Use `TransactionTestCase` only when testing `transaction.on_commit()` callbacks (e.g., cache invalidation)
- **SQLite in-memory connection isolation**: Some redirect tests are skipped on SQLite due to connection isolation issues between Django's TestCase and the test client. These tests pass on PostgreSQL.
- When using `StartupFactory`, pass explicit `edital=` to avoid SubFactory creating extra editais
- For `TransactionTestCase`, add cleanup in `setUp()` to prevent data leakage between tests

#### Test Patterns
```python
# For cache invalidation tests - use TransactionTestCase
class CacheInvalidationTest(TransactionTestCase):
    def setUp(self):
        # Clear data to prevent leakage from other TransactionTestCase tests
        Edital.objects.all().delete()
        Startup.objects.all().delete()
        cache.clear()

# For redirect tests affected by SQLite - use skipIf
from unittest import skipIf
SKIP_SQLITE = 'sqlite' in settings.DATABASES['default']['ENGINE']

@skipIf(SKIP_SQLITE, "SQLite in-memory has connection isolation issues")
def test_redirect_by_pk(self):
    ...

# When creating startups with specific edital counts
edital = EditalFactory(status='aberto')
StartupFactory(proponente=user, edital=edital)  # Explicit edital, no extra created
```

## Key Models

| Model | Purpose |
|-------|---------|
| `Edital` | Main funding announcement entity |
| `EditalValor` | Financial values (min/max amounts) |
| `Cronograma` | Timeline/deadlines |
| `Startup` | Registered startups showcase |
| `Tag` | Categorization tags |

## Key JavaScript

| File | Purpose |
|------|---------|
| `main.js` | Core UI: mobile menu, toast notifications, modals, form validation, scroll-to-error |
| `animations.js` | GSAP-based page animations (home, startups, editais) |
| `animations-native.js` | CSS/IntersectionObserver fallback when GSAP unavailable |
| `editais-index.js` | Editais listing: search, filters, AJAX loading |
| `edital-form.js` | Form handling: dynamic fields, validation, autosave with cleanup |

## Design System

### Color Palette
| Token | Value | Usage |
|-------|-------|-------|
| `primary` | #2563EB | Buttons, links, accents |
| `primary-hover` | #1d4ed8 | Hover states |
| `darkblue` | #1e3a8a | Hero backgrounds, footer |
| `secondary` | #22c55e | Green accent (agro theme) |
| `background-light` | #F8FAFC | Page backgrounds |
| `surface-light` | #FFFFFF | Cards, panels |
| `text-light` | #1E293B | Body text |
| `text-muted` | #64748B | Secondary text |

Legacy aliases preserved: `unirvBlue` → `primary`, `agrohubBlue` → `primary-hover`

### Typography
- **Display/Headings**: Montserrat (weights: 400, 600, 700, 800)
- **Body Text**: Inter (weights: 300, 400, 500, 600, 700)
- Self-hosted fonts in `static/fonts/`

### Icon Systems
- **Material Icons Outlined**: CDN loaded in `base.html`, used for UI elements
- **FontAwesome 6.5.2**: Self-hosted in `static/vendor/fontawesome/`, used for feature icons

### CSS Patterns
- **Glassmorphism**: `bg-white/95 backdrop-blur-lg border-white/20`
- **Card hover**: `hover:-translate-y-1 transition duration-300 shadow-xl`
- **Gradient overlays**: `bg-gradient-to-r from-darkblue to-primary`
- **Theme tokens**: Defined in `@theme` block in `styles.css`

## Environment Variables
Copy `.env.example` to `.env` and configure:
- `DEBUG` - Set to False in production
- `SECRET_KEY` - Django secret key
- `DATABASE_URL` - PostgreSQL connection (optional, defaults to SQLite)
- `REDIS_URL` - Cache backend (optional)

## CI/CD Pipeline
GitHub Actions (`.github/workflows/test.yml`):
1. **Linting** - `ruff check` for code quality
2. **Security Scan** - `bandit` for vulnerability detection
3. **Tests** - Django test suite with coverage
4. **Coverage Check** - 85% threshold enforced
5. **PR Comments** - Automatic coverage reports on pull requests

## Docker Production Deployment

### Architecture
```
         [Internet]
              │
              ▼
       ┌─────────────┐
       │    Nginx    │ :80/:443
       │  (proxy)    │ Static/Media files
       └──────┬──────┘
              │
              ▼
       ┌─────────────┐
       │   Django    │ :8000 (internal)
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

### Docker Files
| File | Purpose |
|------|---------|
| `Dockerfile` | Multi-stage build (Node + Python), non-root user, HEALTHCHECK |
| `docker-compose.yml` | Production orchestration (db, redis, web, nginx) |
| `docker-entrypoint.sh` | DB/Redis wait, migrations, optimized Gunicorn |
| `.env.docker` | Environment template for Docker deployment |
| `docker/nginx/nginx.conf` | Nginx main config (gzip, rate limiting) |
| `docker/nginx/conf.d/default.conf` | Site config (proxy, static, security headers) |

### Quick Deploy
```bash
# First time
cp .env.docker .env
# Edit .env: SECRET_KEY, DB_PASSWORD, ALLOWED_HOSTS

# Build and start
docker-compose up --build -d

# View logs
docker-compose logs -f web

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Health check
curl http://localhost/health/
```

### Named Volumes
| Volume | Container | Purpose |
|--------|-----------|---------|
| `postgres_data` | db | Database persistence |
| `redis_data` | redis | Cache persistence |
| `media_data` | web, nginx | User uploads |
| `static_data` | web, nginx | Collected static files |
| `logs_data` | web | Application logs |

### Environment Variables (Docker)
**Required:**
- `SECRET_KEY` - Django secret key
- `ALLOWED_HOSTS` - Domain(s), comma-separated
- `DB_PASSWORD` - PostgreSQL password

**Auto-configured:**
- `DB_HOST=db` - Container hostname
- `REDIS_HOST=redis` - Container hostname

See `.env.docker` for full list with defaults.

## Important Notes
- Language: Portuguese (pt-BR)
- Timezone: America/Sao_Paulo
- Database: PostgreSQL (production), SQLite (development)
- CI: GitHub Actions runs linting, security scans, tests, and coverage checks on PRs
