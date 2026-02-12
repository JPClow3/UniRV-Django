# Docker Tests - Quick Reference

## Test Files

| File | Type | Time | Purpose |
|------|------|------|---------|
| `editais/tests/test_docker.py` | File-based | ~1-2s | Configuration validation |
| `editais/tests/test_docker_advanced.py` | Integration | ~5-15m | Build, network, runtime tests |

## Quick Commands

### Run Only Fast Tests (File-Based)
```bash
# Configuration validation only - no Docker needed
python manage.py test editais.tests.test_docker -v 2
pytest editais/tests/test_docker.py -v
```

### Run Only Integration Tests (Advanced)
```bash
# Requires Docker daemon running
pytest editais/tests/test_docker_advanced.py -v
```

### Run All Docker Tests
```bash
pytest editais/tests/test_docker*.py -v
```

### Run Specific Test Classes

```bash
# File-based tests
pytest editais/tests/test_docker.py::TestDockerfileValidation -v
pytest editais/tests/test_docker.py::TestDockerComposeValidation -v
pytest editais/tests/test_docker.py::TestDockerSecurity -v

# Integration tests
pytest editais/tests/test_docker_advanced.py::TestDockerBuildVerification -v
pytest editais/tests/test_docker_advanced.py::TestImageLayerValidation -v
pytest editais/tests/test_docker_advanced.py::TestDockerComposeNetworkConnectivity -v
pytest editais/tests/test_docker_advanced.py::TestDockerPerformance -v
pytest editais/tests/test_docker_advanced.py::TestContainerRuntime -v
```

### Run with Verbose Output & Timing
```bash
pytest editais/tests/test_docker_advanced.py -v -s --durations=10
```

## What's Tested

### File-Based Tests (Fast)
- ✅ Dockerfile best practices (multi-stage, non-root user, minimal dependencies)
- ✅ docker-compose.yml syntax and required services
- ✅ Environment variable requirements
- ✅ Entrypoint script validity
- ✅ Security configuration (no hardcoded secrets)
- ✅ Nginx configuration

### Integration Tests (Advanced)
- ✅ **Build Verification**: Docker builds succeed with proper caching
- ✅ **Image Layers**: Optimal layer counts and image sizes
- ✅ **Network Tests**: PostgreSQL and Redis connectivity
- ✅ **Performance**: Build time and container startup metrics
- ✅ **Runtime**: Container execution, environment variables, non-root user

## CI/CD Integration

### GitHub Actions

```yaml
# Run file-based tests (always)
- run: python manage.py test editais.tests.test_docker -v 2

# Run integration tests (optional, longer)
- run: pytest editais/tests/test_docker_advanced.py -v
  continue-on-error: true  # Don't fail workflow
```

### Local Development Workflow

1. **Before committing**: `pytest editais/tests/test_docker.py` (fast)
2. **Before pushing**: `pytest editais/tests/test_docker*.py` (thorough)
3. **After Docker changes**: Run full suite to validate

## Troubleshooting

### Docker not found
```
ERROR: Docker not available
Solution: Install Docker or run file-based tests only
```
```bash
# Run only configuration tests
pytest editais/tests/test_docker.py -v
```

### Docker daemon not running
```
ERROR: Docker daemon not running
Solution: Start Docker:
- Linux: `sudo systemctl start docker`
- Windows: Start Docker Desktop
- macOS: Open Docker.app
```

### Slow tests timing out
```bash
# Run with longer timeout and verbose output
pytest editais/tests/test_docker_advanced.py -v -s --timeout=600
```

### Container build failures
Check logs in real-time:
```bash
docker build -t unirv-django-test:latest .
```

## Performance Tips

1. **First run**: Will build base images from scratch (slow)
2. **Subsequent runs**: Docker layer caching makes builds 50% faster
3. **Network tests**: Require 5-10 seconds for service startup
4. **Run locally first**: Check tests pass before pushing to CI/CD

## Key Test Classes

### 1. TestDockerBuildVerification (3 tests)
- Tests actual Docker image builds
- Validates multi-stage build success
- Verifies layer caching efficiency

### 2. TestImageLayerValidation (3 tests)
- Checks image has optimal layer count
- Validates image size is reasonable
- Ensures minimal base image usage

### 3. TestDockerComposeNetworkConnectivity (3 tests)
- Starts PostgreSQL and Redis services
- Verifies service health
- Tests inter-service networking

### 4. TestDockerPerformance (3 tests)
- Measures build time
- Tracks image size
- Measures container startup time

### 5. TestContainerRuntime (5 tests)
- Tests container startup
- Validates environment variables
- Checks required commands exist
- Ensures non-root execution
- Verifies Django commands work

## Dependencies

Install all required packages:
```bash
pip install -r requirements-dev.txt
```

Key packages:
- `pytest` - Test runner
- `docker` - Docker SDK for Python
- `pyyaml` - YAML parsing
- `requests` - HTTP client for runtime tests

## Coverage Report

```bash
# Run tests with coverage
coverage run -m pytest editais/tests/test_docker*.py
coverage report -m
coverage html  # Generate HTML report
```

## Documentation

- Full details: See [DOCKER_TESTS.md](./DOCKER_TESTS.md)
- Codebase structure: See [docs/architecture/system-architecture.md](./docs/architecture/system-architecture.md)
- Docker setup: See[ENVIRONMENT_SETUP.md](./docs/ENVIRONMENT_SETUP.md)
