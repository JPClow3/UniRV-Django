# UniRV-Django Constitution
<!-- Sistema de Gerenciamento de Editais de Fomento - AgroHub UniRV -->

## Core Principles

### I. Django Best Practices (NON-NEGOTIABLE)
- Follow Django conventions and patterns strictly
- Use Django's built-in features (models, views, forms, admin) before creating custom solutions
- Adhere to Django's project structure: apps in separate directories, templates organized by app
- Use Django's ORM for all database operations; raw SQL only when absolutely necessary
- Follow Django naming conventions: lowercase app names, snake_case for functions/variables
- Leverage Django's admin interface for content management when appropriate

### II. Security First
- **Never commit sensitive data**: SECRET_KEY, passwords, API keys must be in environment variables
- Use `.env` files for local development (with `.env` in `.gitignore`)
- Always validate and sanitize user input (use Django forms, bleach for HTML sanitization)
- Enable security settings in production (HTTPS, secure cookies, HSTS, CSRF protection)
- Use Django's built-in authentication and authorization mechanisms
- Follow OWASP Top 10 guidelines for web application security

### III. Test-Driven Development
- Write tests before implementing features (TDD: Red-Green-Refactor)
- Test coverage required for all new features
- Use Django's TestCase for unit and integration tests
- Test models, views, forms, and custom management commands
- Run tests before committing: `python manage.py test`
- Integration tests required for: database operations, user authentication, form submissions, API endpoints

### IV. Database Migrations
- **Always create migrations** for model changes: `python manage.py makemigrations`
- Review migration files before applying: `python manage.py migrate`
- Never edit existing migration files after they've been applied to production
- Use data migrations for complex data transformations
- Test migrations on a copy of production data before applying to production
- Keep migration files in version control

### V. Code Quality & Documentation
- Follow PEP 8 Python style guide
- Use type hints where appropriate (Python 3.9+)
- Write docstrings for all classes, functions, and methods
- Keep functions and classes focused and small (Single Responsibility Principle)
- Use meaningful variable and function names (preferably in Portuguese for user-facing code)
- Comment complex logic, but prefer self-documenting code
- Maintain README.md with setup instructions and project structure

### VI. Static Files & Media Management
- Use WhiteNoise for serving static files in production
- Collect static files before deployment: `python manage.py collectstatic`
- Organize static files by type (CSS, JS, images) in separate directories
- Use Django's static files framework for development
- Optimize images and assets before committing
- Use versioned static files (hashed filenames) for cache busting

### VII. Environment Configuration
- Use environment variables for all configuration that varies between environments
- Provide `.env.example` with all required variables (no sensitive values)
- Document all environment variables in README.md
- Use `python-decouple` or `django-environ` if needed for complex configurations
- Separate settings for development, testing, and production (if needed)

## Additional Constraints

### Technology Stack
- **Framework**: Django 5.2.7+ (LTS versions preferred)
- **Database**: SQLite for development, PostgreSQL recommended for production
- **Static Files**: WhiteNoise 6.7.0+
- **Python Version**: Python 3.9+ (specify in requirements or pyproject.toml)
- **Dependencies**: All dependencies must be pinned in `requirements.txt`
- **Web Server**: Gunicorn for production (WSGI), Uvicorn for ASGI if needed

### Language & Localization
- Primary language: Portuguese (Brazil) - `pt-br`
- Timezone: `America/Sao_Paulo`
- All user-facing text must be in Portuguese
- Use Django's internationalization (i18n) if multi-language support is needed
- Date and number formats must follow Brazilian conventions

### Performance Standards
- Database queries must be optimized (use `select_related` and `prefetch_related`)
- Implement pagination for list views (default: 12 items per page)
- Use database indexes for frequently queried fields
- Minimize database queries per page (use Django Debug Toolbar in development)
- Cache expensive operations when appropriate

## Development Workflow

### Branch Strategy
- `main` branch: production-ready code
- Feature branches: `feature/feature-name` for new features
- Bugfix branches: `bugfix/issue-description` for bug fixes
- Never commit directly to `main` branch

### Code Review Process
- All code must be reviewed before merging to `main`
- PRs must include: description, tests, migration files (if applicable)
- All tests must pass before merging
- Code must follow this constitution and Django best practices
- Security review required for authentication, authorization, and data handling changes

### Deployment Checklist
- [ ] All tests passing
- [ ] Migrations reviewed and tested
- [ ] Static files collected
- [ ] Environment variables configured
- [ ] DEBUG=False in production
- [ ] SECRET_KEY is secure and unique
- [ ] ALLOWED_HOSTS configured correctly
- [ ] HTTPS enabled
- [ ] Database backup configured
- [ ] Logging configured

### Quality Gates
- No linter errors (flake8, pylint, or similar)
- All tests passing with adequate coverage
- No security vulnerabilities (use `pip-audit` or `safety`)
- Migrations are reversible when possible
- Documentation updated for user-facing changes

## Governance

### Constitution Authority
- This constitution supersedes all other development practices
- All team members must follow these principles
- Exceptions require team discussion and documentation
- Amendments to this constitution require team approval and version update

### Compliance Verification
- All PRs must verify compliance with this constitution
- Code reviews must check adherence to core principles
- Automated checks (CI/CD) should verify: tests, migrations, static files, security settings
- Complexity must be justified; prefer Django's built-in solutions over custom implementations

### Amendment Process
- Propose amendments via PR to this file
- Require team discussion and consensus
- Update version number and date when amended
- Document rationale for changes

**Version**: 1.0.0 | **Ratified**: 2025-01-27 | **Last Amended**: 2025-01-27
