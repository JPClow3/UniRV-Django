# Testing Documentation

This directory contains comprehensive testing documentation for the AgroHub project.

## 📄 Available Documents

### [TEST_REPORT.md](./TEST_REPORT.md)
**Status**: Up to date as of February 7, 2026

Comprehensive test execution report covering:
- **31+ passing tests** across all test suites
- Admin Dashboard Tests (8 tests)
- Edital Admin Filters Tests (11 tests)
- Edital Admin CRUD Tests (11+ tests)
- Security validation tests
- Performance observations

**Key Metrics**:
- ✅ All tests passing
- ✅ Coverage threshold: 85% enforced
- ✅ Zero failures or errors detected

## 🧪 Running Tests

### Full Test Suite (SQLite — no PostgreSQL/Redis required)
```powershell
# Windows PowerShell
$env:DATABASE_URL="sqlite:///test_db.sqlite3"; $env:REDIS_URL=""; $env:REDIS_HOST=""
pytest editais/tests -v -n auto --cov=editais --cov-report=term -q --ignore=editais/tests/test_docker_advanced.py
```

```bash
# Linux/macOS
DATABASE_URL=sqlite:///test_db.sqlite3 REDIS_URL= REDIS_HOST= pytest editais/tests -v -n auto --cov=editais --cov-report=term -q --ignore=editais/tests/test_docker_advanced.py
```

### Run-All Script (PowerShell)
```powershell
.\scripts\run_all_tests.ps1
# Skip Docker advanced (requires Docker daemon):
.\scripts\run_all_tests.ps1 -SkipDockerAdvanced
```

### Full Test Suite (with PostgreSQL/Redis)
```bash
# Run all tests with coverage
pytest -n auto --cov=editais --cov-report=term -q

# Run with HTML coverage report
pytest -n auto --cov=editais --cov-report=html --cov-report=term -q

# Check coverage threshold (85%)
coverage report --fail-under=85
```

### Lighthouse Audits
```bash
# Start server first, then:
python scripts/lighthouse_runner.py --all
# Or from theme: npm run lhci:local
```

### Specific Test Files
```bash
# Run dashboard tests
pytest editais/tests/test_dashboard_views.py -v

# Run security tests  
pytest editais/tests/test_security.py -v

# Run cache invalidation tests
pytest editais/tests/test_e2e_cache_invalidation.py -v
```

### Using Django Test Runner
```bash
# Run all editais tests
python manage.py test editais

# Run specific test class
python manage.py test editais.tests.test_edital_model.EditalModelTest

# Run with verbosity
python manage.py test editais -v 2
```

## 📊 Coverage Reports

After running tests with coverage, view HTML reports:
```bash
# Generate reports (automatically created by pytest)
# Open in browser
start htmlcov/index.html  # Windows
open htmlcov/index.html   # macOS
xdg-open htmlcov/index.html  # Linux
```

## 🔍 Test Organization

Tests are organized by feature area in `editais/tests/`:
- `test_edital_model.py` - Edital model logic and validation
- `test_startup_model.py` - Startup model tests
- `test_forms.py` - Form validation and sanitization
- `test_views_*.py` - View layer tests
- `test_services.py` - Business logic layer
- `test_cache_*.py` - Cache behavior and invalidation
- `test_security.py` - Security (XSS, CSRF, SQL injection)

## 🎯 Test Quality Guidelines

1. **Coverage**: Maintain ≥85% coverage (enforced in CI)
2. **Isolation**: Each test should be independent
3. **Speed**: Use `pytest-xdist` for parallel execution
4. **Fixtures**: Use factory_boy fixtures from `conftest.py`
5. **Naming**: Follow `test_<feature>_<scenario>` convention

## 🚀 CI/CD Integration

Tests run automatically on:
- Pull requests to main/master
- Pushes to main/master  
- Manual workflow dispatch

**CI Checks**:
1. ✅ Ruff linting
2. ✅ Bandit security scan
3. ✅ Database migrations
4. ✅ pytest with coverage
5. ✅ Coverage threshold (85%)

## 📖 Related Documentation

- [Main Testing Guide](../../README.md#-testes) - Setup and basic testing
- [Architecture Docs](../architecture/) - System architecture
- [Database Review](../database/DATABASE_REVIEW.md) - Database structure
- [Migration Review](../migrations/MIGRATION_REVIEW.md) - Migration history

---

**Last Updated**: February 12, 2026
