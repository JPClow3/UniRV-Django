"""
Testes para configurações Docker e validação de imagens.
"""

import json
import os
import re
import subprocess
import time
from pathlib import Path

import pytest
import requests
import yaml

try:
    import docker
    DOCKER_SDK_AVAILABLE = True
except ImportError:
    DOCKER_SDK_AVAILABLE = False


PROJECT_ROOT = Path(__file__).parent.parent.parent


@pytest.fixture(scope="module")
def dockerfile_content():
    path = PROJECT_ROOT / "Dockerfile"
    if path.exists():
        return path.read_text()
    return None


@pytest.fixture(scope="module")
def compose_data():
    path = PROJECT_ROOT / "docker-compose.yml"
    if path.exists():
        return yaml.safe_load(path.read_text())
    return None


@pytest.fixture(scope="module")
def compose_content():
    path = PROJECT_ROOT / "docker-compose.yml"
    if path.exists():
        return path.read_text()
    return None


@pytest.fixture(scope="module")
def entrypoint_content():
    path = PROJECT_ROOT / "docker-entrypoint.sh"
    if path.exists():
        return path.read_text()
    return None


# ── Docker availability and helper functions ─────────────────


def is_docker_available():
    """Check if Docker is available on the system"""
    try:
        subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            timeout=5,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return False


def is_docker_daemon_running():
    """Check if Docker daemon is actually running"""
    try:
        subprocess.run(
            ["docker", "ps"],
            capture_output=True,
            timeout=5,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return False


@pytest.fixture(scope="module")
def docker_client():
    """Get Docker SDK client if available and daemon is running"""
    if not DOCKER_SDK_AVAILABLE or not is_docker_available():
        return None
    try:
        client = docker.from_env()
        # Test connection
        client.ping()
        return client
    except Exception:
        return None


@pytest.fixture(scope="module")
def docker_available():
    """Fixture to check if Docker is available"""
    return is_docker_available() and is_docker_daemon_running()


skip_if_no_docker = pytest.mark.skipif(
    not is_docker_available(),
    reason="Docker not available",
)
skip_if_docker_not_running = pytest.mark.skipif(
    not is_docker_daemon_running(),
    reason="Docker daemon not running",
)


# ── Dockerfile ───────────────────────────────────────────────


class TestDockerfileValidation:
    """Testes de validação do Dockerfile"""

    def test_dockerfile_exists(self):
        assert (PROJECT_ROOT / "Dockerfile").exists()

    def test_dockerfile_has_valid_syntax(self, dockerfile_content):
        assert dockerfile_content is not None
        valid_instructions = [
            "FROM",
            "RUN",
            "COPY",
            "WORKDIR",
            "ENV",
            "EXPOSE",
            "ENTRYPOINT",
            "CMD",
        ]
        content_upper = dockerfile_content.upper()
        assert any(f"\n{i} " in f"\n{content_upper}" for i in valid_instructions)

    def test_dockerfile_uses_multistage_build(self, dockerfile_content):
        assert dockerfile_content is not None
        from_count = len(re.findall(r"^\s*FROM\s+", dockerfile_content, re.MULTILINE))
        assert from_count >= 2

    def test_dockerfile_uses_nonroot_user(self, dockerfile_content):
        assert dockerfile_content is not None
        assert "useradd" in dockerfile_content or "USER " in dockerfile_content

    def test_dockerfile_disables_apt_recommends(self, dockerfile_content):
        assert dockerfile_content is not None
        apt_lines = re.findall(r"apt-get install.*", dockerfile_content, re.IGNORECASE)
        for line in apt_lines:
            assert "--no-install-recommends" in line

    def test_dockerfile_cleans_apt_cache(self, dockerfile_content):
        assert dockerfile_content is not None
        assert "apt-get clean" in dockerfile_content
        assert "/var/lib/apt/lists" in dockerfile_content

    def test_dockerfile_sets_python_env_vars(self, dockerfile_content):
        assert dockerfile_content is not None
        for var in ["PYTHONDONTWRITEBYTECODE", "PYTHONUNBUFFERED"]:
            assert var in dockerfile_content

    def test_dockerfile_uses_pip_no_cache(self, dockerfile_content):
        assert dockerfile_content is not None
        pip_lines = re.findall(r"pip install.*", dockerfile_content, re.IGNORECASE)
        for line in pip_lines:
            assert "--no-cache-dir" in line or "--user" in line

    def test_dockerfile_no_sudo(self, dockerfile_content):
        assert dockerfile_content is not None
        assert "sudo" not in dockerfile_content.lower()


# ── docker-compose.yml ───────────────────────────────────────


class TestDockerComposeValidation:
    """Testes de validação do docker-compose.yml"""

    def test_docker_compose_exists(self):
        assert (PROJECT_ROOT / "docker-compose.yml").exists()

    def test_docker_compose_valid_yaml(self, compose_data):
        assert compose_data is not None

    def test_docker_compose_has_services(self, compose_data):
        assert compose_data is not None
        assert "services" in compose_data
        assert len(compose_data["services"]) > 0

    def test_docker_compose_has_required_services(self, compose_data):
        assert compose_data is not None
        services = list(compose_data.get("services", {}).keys())
        for svc in ["db", "redis", "web"]:
            assert svc in services

    def test_docker_compose_db_has_healthcheck(self, compose_data):
        assert compose_data is not None
        db = compose_data["services"].get("db", {})
        assert "healthcheck" in db
        assert "test" in db["healthcheck"]
        assert "interval" in db["healthcheck"]

    def test_docker_compose_redis_has_healthcheck(self, compose_data):
        assert compose_data is not None
        redis = compose_data["services"].get("redis", {})
        assert "healthcheck" in redis

    def test_docker_compose_web_depends_on_db_redis(self, compose_data):
        assert compose_data is not None
        web = compose_data["services"].get("web", {})
        assert "depends_on" in web
        for svc in ["db", "redis"]:
            assert svc in web["depends_on"]

    def test_docker_compose_volumes_defined(self, compose_data):
        assert compose_data is not None
        assert "volumes" in compose_data
        volumes = list(compose_data["volumes"].keys())
        for vol in ["postgres_data", "redis_data", "media_data", "static_data"]:
            assert vol in volumes

    def test_docker_compose_networks_defined(self, compose_data):
        assert compose_data is not None
        assert "networks" in compose_data

    def test_docker_compose_restart_policies(self, compose_data):
        assert compose_data is not None
        for name, cfg in compose_data["services"].items():
            assert "restart" in cfg, f"Service '{name}' should have restart policy"


# ── Environment variables ────────────────────────────────────


class TestDockerEnvironmentVariables:

    def test_required_env_vars_in_compose(self, compose_content):
        for var in ["SECRET_KEY", "DB_PASSWORD", "ALLOWED_HOSTS", "DB_NAME", "DB_USER"]:
            assert var in compose_content

    def test_env_var_defaults_documented(self, compose_content):
        defaults = re.findall(r"\$\{[A-Z_]+:-[^}]*\}", compose_content)
        assert len(defaults) > 0

    def test_no_hardcoded_secrets(self, compose_content, dockerfile_content):
        for content in [compose_content, dockerfile_content]:
            if content:
                for pattern in [
                    r'SECRET_KEY\s*=\s*["\']([^${}][a-zA-Z0-9]+)["\']',
                    r'PASSWORD\s*=\s*["\']([^${}][a-zA-Z0-9]+)["\']',
                ]:
                    assert len(re.findall(pattern, content)) == 0


# ── docker-entrypoint.sh ─────────────────────────────────────


class TestDockerEntrypointValidation:

    def test_entrypoint_exists(self):
        assert (PROJECT_ROOT / "docker-entrypoint.sh").exists()

    def test_entrypoint_is_executable(self):
        assert os.access(PROJECT_ROOT / "docker-entrypoint.sh", os.X_OK)

    def test_entrypoint_has_shebang(self, entrypoint_content):
        assert entrypoint_content is not None
        assert entrypoint_content.startswith("#!/bin/bash")

    def test_entrypoint_has_set_e(self, entrypoint_content):
        assert entrypoint_content is not None
        assert "set -e" in entrypoint_content

    def test_entrypoint_handles_migrations(self, entrypoint_content):
        assert entrypoint_content is not None
        assert "migrate" in entrypoint_content.lower()

    def test_entrypoint_starts_gunicorn(self, entrypoint_content):
        assert entrypoint_content is not None
        assert "gunicorn" in entrypoint_content.lower() or "exec" in entrypoint_content

    def test_entrypoint_has_logging_functions(self, entrypoint_content):
        assert entrypoint_content is not None
        for func in ["log_info", "log_warn", "log_error"]:
            assert func in entrypoint_content


# ── Security ─────────────────────────────────────────────────


class TestDockerSecurity:

    def test_dockerfile_no_curl_pipe_bash(self, dockerfile_content):
        assert dockerfile_content is not None
        assert (
            re.search(r"curl\s+.*\|\s*bash", dockerfile_content, re.IGNORECASE) is None
        )

    def test_docker_compose_db_password_required(self, compose_content):
        assert "DB_PASSWORD:?" in compose_content

    def test_docker_compose_secret_key_required(self, compose_content):
        assert "SECRET_KEY:?" in compose_content


# ── Nginx ────────────────────────────────────────────────────


class TestDockerNginxConfig:

    def test_nginx_conf_exists(self):
        assert (PROJECT_ROOT / "docker" / "nginx" / "nginx.conf").exists()

    def test_nginx_default_conf_exists(self):
        assert (PROJECT_ROOT / "docker" / "nginx" / "conf.d" / "default.conf").exists()

    def test_nginx_hides_server_tokens(self):
        content = (PROJECT_ROOT / "docker" / "nginx" / "nginx.conf").read_text()
        assert "server_tokens off" in content

    def test_nginx_has_gzip(self):
        content = (PROJECT_ROOT / "docker" / "nginx" / "nginx.conf").read_text()
        assert "gzip" in content.lower()


# ── Integration ──────────────────────────────────────────────


class TestDockerIntegration:

    def test_docker_directory_structure(self):
        for d in [
            PROJECT_ROOT / "docker",
            PROJECT_ROOT / "docker" / "nginx",
            PROJECT_ROOT / "docker" / "postgres",
        ]:
            assert d.exists() and d.is_dir()

    def test_docker_env_file_mentions_in_docs(self):
        readme = PROJECT_ROOT / "README.md"
        if readme.exists():
            content = readme.read_text(encoding="utf-8").lower()
            assert "env" in content or "docker" in content
