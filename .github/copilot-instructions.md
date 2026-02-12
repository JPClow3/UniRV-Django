# Copilot Instructions — AgroHub (UniRV-Django)

## Project Overview

Django 5.2+ web app for **AgroHub** — UniRV's Innovation Hub. Manages editais (funding calls), startups (YPETEC incubator), and innovation spaces (InovaLab). All UI text, comments and error messages are in **Portuguese (pt-BR)**. Timezone: `America/Sao_Paulo`. PostgreSQL required (raises `ImproperlyConfigured` without it).

## Architecture

Single Django app (`editais/`) with a service layer pattern:

- **Models** (`editais/models.py`): `Edital`, `EditalValor`, `Cronograma`, `Startup`, `Tag`. Use custom QuerySet methods (`.active()`, `.search()`, `.with_related()`, `.with_prefetch()`). Edital has `HistoricalRecords` via `django-simple-history`.
- **Views** (`editais/views/`): Split into `public.py`, `dashboard.py`, `editais_crud.py`, `mixins.py`. The top-level `editais/views.py` only re-exports — **never add views there directly**; add in the appropriate submodule and re-export.
- **Services** (`editais/services.py`): Business logic (`EditalService`) extracted from views. Use for multi-model operations.
- **Constants** (`editais/constants/`): `cache.py`, `limits.py`, `status.py` — flat re-exported via `__init__.py`. All magic numbers go here. Import from `editais.constants` directly.
- **Cache** (`editais/cache_utils.py`): Standardized key generation. Key format: `{prefix}_{key}:{value}`. Redis primary; LocMemCache fallback. Global prefix: `unirv_editais`.
- **Decorators** (`editais/decorators.py`): `@rate_limit` (custom, fail-open), `@staff_required` (returns 403 template).
- **Utils** (`editais/utils.py`): HTML sanitization via `bleach`, slug generation, cache clearing.

## Key Commands

```bash
python manage.py runserver                                      # Dev server
cd theme/static_src && npm run dev                              # Tailwind watch (separate terminal)
cd theme/static_src && npm run build                            # Full asset build (CSS + JS min + vendor)
python manage.py test editais                                   # Tests
coverage run --source='editais' manage.py test editais && coverage report  # Coverage (85% min)
ruff check editais/ UniRV_Django/                               # Lint
python manage.py seed_editais && python manage.py seed_startups # Seed data
```

## Code Patterns

### Models

- `SlugGenerationMixin` provides unique slug generation with DB-level retry logic for race conditions.
- HTML input sanitized via `bleach` in `save()` methods — see `sanitize_edital_fields()` in `utils.py`. Whitelisted tags defined in `ALLOWED_TAGS`.
- PostgreSQL full-text search with `SearchVector`/`SearchQuery`.
- All imports at module level. Use `TYPE_CHECKING` guard for circular import avoidance (see `utils.py` pattern).

### Views

- Function-based views with type annotations (`request: HttpRequest -> HttpResponse`).
- Dashboard views stack `@login_required` + `@staff_required`.
- Response caching only for **unauthenticated + unfiltered** requests — authenticated/filtered requests always hit DB.
- Cache invalidation via `clear_all_caches()` triggered by model save signals.

### Fail-Open Design

Both `@rate_limit` decorator and cache operations use fail-open: if Redis/cache is unavailable, requests proceed normally. Rate limiting is skipped entirely during tests (`settings.TESTING` flag).

### Frontend

- **Tailwind CSS v4** with theme tokens in `theme/static_src/src/styles.css` (`@theme` block).
- **No inline event handlers** — use external JS with `addEventListener`.
- JS files need `.min.js` production versions; build with `npm run build:js` (uses terser). Files: `main.js`, `animations.js`, `animations-native.js`, `editais-index.js`, `edital-form.js`.
- Icons: Material Icons Outlined (CDN) + FontAwesome 6.5.2 (self-hosted `static/vendor/fontawesome/`).
- Fonts: Inter (body, `font-body`) + Montserrat (headings, `font-display`), self-hosted in `static/fonts/`.
- Design tokens: `primary` (#2563EB), `darkblue` (#1e3a8a), `secondary` (#22c55e). Use modern names — legacy aliases (`unirvBlue`, `agrohubBlue`) exist but avoid in new code.
- Common patterns: glassmorphism (`bg-white/95 backdrop-blur-lg`), card hover (`hover:-translate-y-1 transition duration-300 shadow-xl`), hero gradient (`bg-gradient-to-r from-darkblue to-primary`).
- SEO blocks in `templates/base.html`: override `{% block title %}`, `{% block meta_description %}`, `{% block og_* %}` per page.

### Forms

- Centralized pt-BR error messages in `FIELD_ERROR_MESSAGES` dict in `forms.py` — use `get_field_error_message()` helper.
- File uploads validated against `MAX_LOGO_FILE_SIZE` from constants.

### Security

- `@rate_limit` on write endpoints. `bleach` sanitization on all user HTML. Never use bare `except Exception`.
- `@staff_required` logs unauthorized attempts with client IP.

## Testing

- Django `TestCase` (default) + `factory-boy` fixtures in `editais/tests/factories.py`.
- Factories: `UserFactory`, `StaffUserFactory`, `SuperUserFactory`, `EditalFactory`, `StartupFactory`, `TagFactory`, `EditalValorFactory`, `CronogramaFactory`.
- Factory traits: `EditalFactory(open_edital=True)`, `StartupFactory(active_startup=True)`, `StartupFactory(without_edital=True)`.
- **Critical**: `StartupFactory` has a `SubFactory(EditalFactory)` — always pass `edital=` explicitly to avoid creating extra editals.
- Use `TransactionTestCase` **only** for `transaction.on_commit()` tests (e.g., cache invalidation). Add cleanup in `setUp()`.
- File naming: `test_<feature>.py` — one file per feature area. 85% coverage enforced in CI.
- Template tags available: `editais_filters`, `image_helpers`, `thumbnail_safe` (loaded in `base.html`).

## CI/CD

GitHub Actions (`.github/workflows/test.yml`): ruff lint → bandit security → tests with coverage → 85% threshold → PR coverage comment.

## Environment & Deployment

| Variable        | Purpose                       | Default                 |
| --------------- | ----------------------------- | ----------------------- |
| `DATABASE_URL`  | PostgreSQL connection         | **Required**            |
| `REDIS_URL`     | Cache backend                 | LocMemCache fallback    |
| `SECRET_KEY`    | Django secret                 | Dev fallback (insecure) |
| `DJANGO_DEBUG`  | Debug mode                    | `True`                  |
| `ALLOWED_HOSTS` | Comma-separated               | localhost (dev)         |
| `CACHE_VERSION` | Bump to purge cache on deploy | `1`                     |

Docker: multi-stage `Dockerfile` (Node 20 → Python 3.12). `docker-compose.yml` orchestrates PostgreSQL 16 + Redis 7 + Gunicorn + Nginx. See `.env.docker` for required vars (`SECRET_KEY`, `DB_PASSWORD`, `ALLOWED_HOSTS`).
