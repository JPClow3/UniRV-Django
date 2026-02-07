# Docker Tests Documentation

## Overview

Comprehensive test suite for Docker configuration and images. All tests validate Docker best practices, security, and proper configuration.

**Location**: `editais/tests/test_docker.py`  
**Tests Count**: 41 ✅  
**Status**: All passing

## Test Classes

### 1. **DockerfileValidationTest** (12 tests)
Validates the Dockerfile structure and best practices:

- ✅ `test_dockerfile_exists` - Dockerfile file exists
- ✅ `test_dockerfile_is_readable` - File has proper read permissions
- ✅ `test_dockerfile_has_valid_syntax` - Contains valid Docker instructions
- ✅ `test_dockerfile_uses_multistage_build` - Uses multi-stage build (≥2 FROM statements)
- ✅ `test_dockerfile_uses_nonroot_user` - Creates and uses non-root user
- ✅ `test_dockerfile_disables_apt_recommends` - Uses `--no-install-recommends` flag
- ✅ `test_dockerfile_cleans_apt_cache` - Cleans apt cache to reduce image size
- ✅ `test_dockerfile_sets_python_env_vars` - Sets `PYTHONDONTWRITEBYTECODE` and `PYTHONUNBUFFERED`
- ✅ `test_dockerfile_uses_pip_cache_dir` - Uses `--no-cache-dir` with pip
- ✅ `test_dockerfile_no_sudo` - No sudo commands in Dockerfile

### 2. **DockerComposeValidationTest** (12 tests)
Validates docker-compose.yml YAML syntax and services:

- ✅ `test_docker_compose_exists` - docker-compose.yml exists
- ✅ `test_docker_compose_valid_yaml` - Valid YAML syntax
- ✅ `test_docker_compose_has_services` - Services are defined
- ✅ `test_docker_compose_has_required_services` - Has `db`, `redis`, and `web` services
- ✅ `test_docker_compose_db_has_healthcheck` - PostgreSQL has healthcheck configured
- ✅ `test_docker_compose_redis_has_healthcheck` - Redis has healthcheck configured
- ✅ `test_docker_compose_web_depends_on_db_redis` - Web service depends on DB and Redis
- ✅ `test_docker_compose_web_build_configured` - Web service build configuration exists
- ✅ `test_docker_compose_volumes_defined` - Required volumes are defined
- ✅ `test_docker_compose_networks_defined` - Network configuration exists
- ✅ `test_docker_compose_restart_policies` - All services have restart policies

### 3. **DockerEnvironmentVariablesTest** (3 tests)
Validates environment variable configuration:

- ✅ `test_required_env_vars_in_compose` - All required variables present
- ✅ `test_env_var_defaults_documented` - Variables have default values documented
- ✅ `test_no_hardcoded_secrets` - No secrets are hardcoded in configuration

### 4. **DockerEntrypointValidationTest** (8 tests)
Validates docker-entrypoint.sh script:

- ✅ `test_entrypoint_exists` - Script file exists
- ✅ `test_entrypoint_is_executable` - File has execute permissions
- ✅ `test_entrypoint_has_shebang` - Script starts with `#!/bin/bash`
- ✅ `test_entrypoint_has_set_commands` - Uses `set -e` for error handling
- ✅ `test_entrypoint_handles_db_connection` - Verifies database connectivity
- ✅ `test_entrypoint_handles_migrations` - Runs Django migrations
- ✅ `test_entrypoint_starts_gunicorn` - Starts Gunicorn application server
- ✅ `test_entrypoint_has_logging_functions` - Has proper logging functions

### 5. **DockerSecurityTest** (3 tests)
Security-focused validation:

- ✅ `test_dockerfile_no_curl_as_install_method` - No dangerous `curl | bash` patterns
- ✅ `test_docker_compose_db_password_required` - DB_PASSWORD is required (not optional)
- ✅ `test_docker_compose_secret_key_required` - SECRET_KEY is required (not optional)

### 6. **DockerNginxConfigValidationTest** (3 tests)
Validates Nginx reverse proxy configuration:

- ✅ `test_nginx_conf_exists` - nginx.conf file exists
- ✅ `test_nginx_default_conf_exists` - default.conf exists in conf.d directory
- ✅ `test_nginx_conf_contains_server_tokens_off` - Version information is hidden
- ✅ `test_nginx_has_gzip_compression` - Gzip compression is configured

### 7. **DockerIntegrationTest** (2 tests)
Integration and documentation validation:

- ✅ `test_docker_directory_structure` - Docker directory structure is complete
- ✅ `test_docker_env_file_mentions_in_docs` - Documentation mentions .env configuration

## Running the Tests

```bash
# Run all Docker tests
python manage.py test editais.tests.test_docker -v 2

# Run specific test class
python manage.py test editais.tests.test_docker.DockerfileValidationTest -v 2

# Run specific test
python manage.py test editais.tests.test_docker.DockerfileValidationTest.test_dockerfile_exists -v 2

# Run with coverage
coverage run --source='editais' manage.py test editais.tests.test_docker
coverage report
```

## What's Tested

### Dockerfile Best Practices
- ✅ Multi-stage builds for optimized image size
- ✅ Non-root user for security
- ✅ Minimal dependencies (only runtime needed)
- ✅ Proper apt cache cleanup
- ✅ Environment variables for Python runtime

### docker-compose.yml Configuration
- ✅ Valid YAML syntax
- ✅ All required services (PostgreSQL, Redis, Django, Nginx)
- ✅ Health checks for auto-recovery
- ✅ Proper service dependencies
- ✅ Volume management
- ✅ Network isolation

### Security
- ✅ Non-root user execution
- ✅ Required environment variables cannot be omitted
- ✅ No hardcoded secrets
- ✅ No dangerous installation patterns

### Database & Cache
- ✅ PostgreSQL configured with health checks
- ✅ Redis configured with health checks
- ✅ Proper connection parameters

### Entrypoint Script
- ✅ Proper error handling
- ✅ Database connectivity verification
- ✅ Django migrations execution
- ✅ Gunicorn startup
- ✅ Comprehensive logging

### Nginx Configuration
- ✅ Security headers (version hiding)
- ✅ Compression enabled
- ✅ Proper reverse proxy setup

## Coverage

The Docker tests ensure:
- **File Integrity**: All Docker files exist and are properly configured
- **Syntax Validation**: YAML and shell script syntax is correct
- **Security**: Best practices for container security are followed
- **Performance**: Image optimization is done properly
- **Reliability**: Health checks and dependencies are configured
- **Documentation**: Configuration is properly documented

## Dependencies

The tests require:
- `pyyaml` - For YAML parsing and validation

Install it with:
```bash
pip install pyyaml
```

## Integration with CI/CD

These tests are automatically run as part of the test suite:

```bash
# Full test suite including Docker tests
python manage.py test
```

They integrate with the GitHub Actions workflow in `.github/workflows/test.yml`.

## Maintenance

When updating Docker configuration:

1. **Dockerfile changes**: Verify tests pass after modifications
2. **docker-compose.yml changes**: Ensure new services have health checks
3. **Environment variables**: Update tests if new required variables are added
4. **entrypoint.sh changes**: Verify startup sequence is correct

## Notes

- Tests use file-based validation - they don't actually build or run Docker images
- For integration tests that build and run images, consider using Docker Compose directly
- Tests respect the project structure and don't modify any files
- All tests are stateless and can run in any order

## Future Enhancements

Potential additions:
- Docker build verification (actually building images)
- Image layer count validation
- Docker Compose network connectivity tests
- Performance testing (image size, build time)
- Container runtime tests (POST requests to running containers)
