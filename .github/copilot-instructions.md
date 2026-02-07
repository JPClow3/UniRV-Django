# Copilot Instructions — AgroHub (UniRV-Django)

## Project Overview

Django 5.2+ web app for **AgroHub** — UniRV's Innovation Hub. Manages editais (funding calls), startups (YPETEC incubator), and innovation spaces (InovaLab). All UI text and comments are in **Portuguese (pt-BR)**. Timezone: `America/Sao_Paulo`.

## Architecture

Single Django app (`editais/`) with a service layer pattern:

- **Models** (`editais/models.py`): `Edital`, `EditalValor`, `Cronograma`, `Startup`, `Tag`. Use custom QuerySet methods (`.active()`, `.search()`, `.with_related()`, `.with_prefetch()`). Edital has `HistoricalRecords` via `django-simple-history`.
- **Views** (`editais/views/`): Split into `public.py`, `dashboard.py`, `editais_crud.py`, `mixins.py`. The top-level `editais/views.py` re-exports everything for backward compatibility — never add views there directly.
- **Services** (`editais/services.py`): Business logic (`EditalService`) extracted from views. Use this layer for complex operations.
- **Constants** (`editais/constants/`): `cache.py`, `limits.py`, `status.py` — re-exported via `__init__.py`. All magic numbers must be defined here.
- **Cache** (`editais/cache_utils.py`): Standardized key generation (`get_cache_key()`, `get_detail_cache_key()`). Key format: `{prefix}_{key}:{value}`. Redis is the primary cache backend; LocMemCache is fallback when Redis is not configured.
- **Decorators** (`editais/decorators.py`): `@rate_limit`, `@staff_required`, cache decorators.

## Key Commands

```bash
# Dev server
python manage.py runserver

# Tailwind CSS (separate terminal)
cd theme/static_src && npm run dev

# Full asset build (CSS + JS minification + vendor copy)
cd theme/static_src && npm run build

# Tests
python manage.py test editais
coverage run --source='editais' manage.py test editais && coverage report

# Linting & security
ruff check editais/ UniRV_Django/
bandit -r editais/ UniRV_Django/ -ll -ii

# Seed data
python manage.py seed_editais
python manage.py seed_startups
```

## Code Patterns

### Models

- Use `SlugGenerationMixin` for models needing unique slugs — implements retry logic for race conditions.
- HTML input is sanitized via `bleach` in `save()` methods (see `sanitize_edital_fields()` in `utils.py`).
- PostgreSQL full-text search with `SearchVector`/`SearchQuery` (PostgreSQL required for all environments).
- All module-level imports — no lazy imports inside functions.

### Views

- Add new views in the appropriate file under `editais/views/`, then re-export in `editais/views.py`.
- Dashboard views require `@staff_required` decorator.
- Cache invalidation uses `clear_all_caches()` from `utils.py` on model save signals.

### Frontend

- **Tailwind CSS v4** with theme tokens defined in `theme/static_src/src/styles.css` (`@theme` block).
- No inline event handlers (`onclick`, `onload`) — use external JS with `addEventListener`.
- JS files must have `.min.js` production versions; build with `npm run build:js`.
- Icons: Material Icons Outlined (CDN in `base.html`) + FontAwesome 6.5.2 (self-hosted in `static/vendor/fontawesome/`).
- Fonts: Inter (body) + Montserrat (headings), self-hosted in `static/fonts/`.

### Design System

All tokens are in the `@theme` block of `theme/static_src/src/styles.css`. Use Tailwind classes with these tokens.

**Colors** — use the token names as Tailwind classes (e.g., `bg-primary`, `text-darkblue`):
| Token | Hex | Usage |
|-------|-----|-------|
| `primary` | `#2563EB` | Buttons, links, brand accents |
| `primary-hover` | `#1d4ed8` | Hover states |
| `secondary` | `#22c55e` | Green accent (agro theme) |
| `darkblue` | `#1e3a8a` | Hero sections, footer backgrounds |
| `background-light` | `#F8FAFC` | Page backgrounds |
| `surface-light` | `#FFFFFF` | Cards, panels |
| `text-light` | `#1E293B` | Body text |
| `text-muted-light` | `#64748B` | Secondary/muted text |

Legacy aliases exist (`unirvBlue` → `primary`, `agrohubBlue` → `primary-hover`) — use the modern names for new code.

**Typography**: Montserrat (`font-display`) for `h1`–`h3` and display text; Inter (`font-body`) for body. Both self-hosted.

**Z-index scale**: `--z-dropdown: 10`, `--z-sticky: 50`, `--z-modal: 100`, `--z-popover: 200`, `--z-tooltip: 300`, `--z-skip-link: 10000`.

**Common CSS patterns**:

- Glassmorphism: `bg-white/95 backdrop-blur-lg border-white/20`
- Card hover lift: `hover:-translate-y-1 transition duration-300 shadow-xl`
- Hero overlays: `bg-gradient-to-r from-darkblue to-primary`

### Security

- `@rate_limit` decorator on write endpoints (uses `editais/constants/` for `RATE_LIMIT_REQUESTS`, `RATE_LIMIT_WINDOW`).
- `bleach` sanitization for all user HTML inputs.
- Never use bare `except Exception` — use specific exception types.

## Testing

- **Framework**: Django `TestCase` (default) with `factory-boy` fixtures in `editais/tests/factories.py`.
- **Factories**: `UserFactory`, `StaffUserFactory`, `EditalFactory`, `StartupFactory`, `TagFactory`, `EditalValorFactory`, `CronogramaFactory`.
- **Coverage minimum**: 85% enforced in CI.
- **File naming**: `test_<feature>.py` — one file per feature area.
- Use `TransactionTestCase` **only** for testing `transaction.on_commit()` callbacks (e.g., cache invalidation). Add cleanup in `setUp()` to prevent data leakage.
- When creating `StartupFactory`, pass `edital=` explicitly to avoid SubFactory creating extra editals.

## Database

- **All environments**: PostgreSQL via `DATABASE_URL` env var (parsed by `dj-database-url`) or `DB_NAME`/`DB_USER`/`DB_PASSWORD`.
- SQLite is **not supported**. The app will raise `ImproperlyConfigured` if no PostgreSQL connection is configured.
- Migrations are in `editais/migrations/`. Run `python manage.py makemigrations` then `python manage.py migrate`.

## CI/CD

GitHub Actions (`.github/workflows/test.yml`): ruff lint → bandit security → tests with coverage → 85% threshold check → PR coverage comments.

## Environment Variables

| Variable        | Purpose               | Default                 |
| --------------- | --------------------- | ----------------------- |
| `SECRET_KEY`    | Django secret         | Dev fallback (insecure) |
| `DJANGO_DEBUG`  | Debug mode            | `True`                  |
| `DATABASE_URL`  | PostgreSQL connection | **Required**            |
| `REDIS_URL`     | Cache backend (Redis) | LocMemCache fallback    |
| `ALLOWED_HOSTS` | Comma-separated hosts | localhost (dev)         |

## Docker Deployment

Multi-stage `Dockerfile` (Node 20 → Python 3.12). `docker-compose.yml` orchestrates: PostgreSQL 16, Redis 7, Django/Gunicorn, Nginx reverse proxy.

```bash
cp .env.docker .env          # Edit: SECRET_KEY, DB_PASSWORD, ALLOWED_HOSTS
docker-compose up --build -d
docker-compose exec web python manage.py createsuperuser
curl http://localhost/health/ # Verify
```

Docker env vars auto-set `DB_HOST=db` and `REDIS_HOST=redis`. Required: `SECRET_KEY`, `ALLOWED_HOSTS`, `DB_PASSWORD`. See `.env.docker` template for full list.

Named volumes: `postgres_data`, `redis_data`, `media_data`, `static_data`, `logs_data`.
