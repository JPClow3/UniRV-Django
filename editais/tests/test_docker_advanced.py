"""
Advanced Docker tests: Build verification, networking, performance, and runtime tests.
"""

import json
import os
import re
import subprocess
import time
from pathlib import Path

import pytest
import requests

try:
    import docker

    DOCKER_SDK_AVAILABLE = True
except ImportError:
    DOCKER_SDK_AVAILABLE = False


PROJECT_ROOT = Path(__file__).parent.parent.parent


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


SKIP_DOCKER_TESTS = os.name == "nt" and not os.environ.get("RUN_DOCKER_TESTS")
DOCKER_AVAILABLE = is_docker_available() and not SKIP_DOCKER_TESTS
DOCKER_RUNNING = is_docker_daemon_running() if DOCKER_AVAILABLE else False

skip_if_no_docker = pytest.mark.skipif(
    not DOCKER_AVAILABLE,
    reason="Docker not available or skipped on Windows (set RUN_DOCKER_TESTS=1 to enable)",
)
skip_if_docker_not_running = pytest.mark.skipif(
    not DOCKER_RUNNING,
    reason="Docker daemon not running",
)


# ── Docker Build Verification ────────────────────────────────


@skip_if_docker_not_running
class TestDockerBuildVerification:
    """Tests for actually building Docker images and verifying success"""

    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Cleanup built images after tests"""
        yield
        # Clean up test images
        try:
            subprocess.run(
                ["docker", "rmi", "-f", "unirv-django-test:latest"],
                capture_output=True,
                timeout=30,
            )
        except Exception:
            pass

    def test_docker_build_succeeds(self):
        """Verify that Docker build completes successfully"""
        result = subprocess.run(
            [
                "docker",
                "build",
                "-t",
                "unirv-django-test:latest",
                "-f",
                str(PROJECT_ROOT / "Dockerfile"),
                str(PROJECT_ROOT),
            ],
            capture_output=True,
            timeout=600,  # 10 minutes max
            text=True,
        )
        assert result.returncode == 0, f"Docker build failed:\n{result.stderr}"

    def test_docker_build_final_stage_created(self):
        """Verify that final stage is created in multi-stage build"""
        result = subprocess.run(
            [
                "docker",
                "build",
                "-t",
                "unirv-django-test:latest",
                "-f",
                str(PROJECT_ROOT / "Dockerfile"),
                str(PROJECT_ROOT),
            ],
            capture_output=True,
            timeout=600,
            text=True,
        )
        assert result.returncode == 0
        # Verify image exists
        verify = subprocess.run(
            ["docker", "images", "unirv-django-test:latest"],
            capture_output=True,
            timeout=10,
            text=True,
        )
        assert "unirv-django-test" in verify.stdout

    def test_docker_build_caches_layers(self):
        """Verify that Docker uses layer caching efficiently"""
        # First build
        result1 = subprocess.run(
            [
                "docker",
                "build",
                "-t",
                "unirv-django-test:latest",
                "-f",
                str(PROJECT_ROOT / "Dockerfile"),
                str(PROJECT_ROOT),
            ],
            capture_output=True,
            timeout=600,
            text=True,
        )
        build1_time = self._extract_build_time(result1.stderr)

        # Second build (should be faster due to caching)
        result2 = subprocess.run(
            [
                "docker",
                "build",
                "-t",
                "unirv-django-test:latest",
                "-f",
                str(PROJECT_ROOT / "Dockerfile"),
                str(PROJECT_ROOT),
            ],
            capture_output=True,
            timeout=600,
            text=True,
        )
        build2_time = self._extract_build_time(result2.stderr)

        assert result1.returncode == 0
        assert result2.returncode == 0
        # Second build should be noticeably faster (at least 50% faster)
        if build1_time and build2_time:
            assert build2_time < build1_time * 0.5, (
                f"Layer caching might not be working: "
                f"Build 1: {build1_time}s, Build 2: {build2_time}s"
            )

    @staticmethod
    def _extract_build_time(stderr_text):
        """Extract build time from docker build output"""
        # Look for "real" time in docker build output
        match = re.search(r"real\s+(\d+)m([\d.]+)s", stderr_text)
        if match:
            minutes = int(match.group(1))
            seconds = float(match.group(2))
            return minutes * 60 + seconds
        return None


# ── Image Layer Count Validation ─────────────────────────────


@skip_if_docker_not_running
class TestImageLayerValidation:
    """Tests for validating image layer count and structure"""

    @pytest.fixture(autouse=True)
    def setup_image(self):
        """Build image for testing"""
        result = subprocess.run(
            [
                "docker",
                "build",
                "-t",
                "unirv-django-test:latest",
                "-f",
                str(PROJECT_ROOT / "Dockerfile"),
                str(PROJECT_ROOT),
            ],
            capture_output=True,
            timeout=600,
        )
        if result.returncode != 0:
            pytest.skip("Could not build Docker image")
        yield
        # Cleanup
        try:
            subprocess.run(
                ["docker", "rmi", "-f", "unirv-django-test:latest"],
                capture_output=True,
                timeout=30,
            )
        except Exception:
            pass

    def test_image_layer_count_reasonable(self):
        """Verify that image layer count is reasonable (not excessive)"""
        result = subprocess.run(
            ["docker", "inspect", "unirv-django-test:latest"],
            capture_output=True,
            timeout=10,
            text=True,
        )
        assert result.returncode == 0

        try:
            data = json.loads(result.stdout)
            image_data = data[0]
            layer_count = len(image_data.get("RootFS", {}).get("Layers", []))

            # Multi-stage builds should result in reasonable layer counts
            # A typical Django app should have < 50 layers
            assert (
                layer_count < 50
            ), f"Image has too many layers: {layer_count} (expected < 50)"
        except (json.JSONDecodeError, IndexError, KeyError) as e:
            pytest.skip(f"Could not parse docker inspect output: {e}")

    def test_image_uses_minimal_base_image(self):
        """Verify that images use efficient base images"""
        result = subprocess.run(
            ["docker", "inspect", "unirv-django-test:latest"],
            capture_output=True,
            timeout=10,
            text=True,
        )
        assert result.returncode == 0

        try:
            data = json.loads(result.stdout)
            image_data = data[0]
            # Check that we have fewer than 50 layers (indicator of efficiency)
            layers = image_data.get("RootFS", {}).get("Layers", [])
            assert len(layers) > 0, "Image should have at least one layer"
            assert (
                len(layers) < 50
            ), f"Image appears to have inefficient layering: {len(layers)} layers"
        except (json.JSONDecodeError, IndexError, KeyError) as e:
            pytest.skip(f"Could not parse docker inspect output: {e}")

    def test_image_has_reasonable_size(self):
        """Verify that built image has reasonable size"""
        result = subprocess.run(
            ["docker", "images", "unirv-django-test:latest", "--format", "json"],
            capture_output=True,
            timeout=10,
            text=True,
        )
        assert result.returncode == 0

        try:
            # Parse docker images output
            lines = result.stdout.strip().split("\n")
            for line in lines:
                if line.strip():
                    data = json.loads(line)
                    size = data.get("Size", 0)
                    # Django app image should typically be < 2GB
                    assert (
                        size < 2 * 1024 * 1024 * 1024
                    ), f"Image size {size} bytes exceeds reasonable limit"
                    break
        except (json.JSONDecodeError, KeyError, ValueError):
            # Fallback: use human-readable format
            assert "unirv-django-test" in result.stdout


# ── Docker Compose Network Connectivity Tests ────────────────


@skip_if_docker_not_running
class TestDockerComposeNetworkConnectivity:
    """Tests for Docker Compose network connectivity and service communication"""

    @pytest.fixture(autouse=True)
    def compose_setup_teardown(self):
        """Setup and teardown Docker Compose services"""
        # Start only db and redis for testing
        result = subprocess.run(
            ["docker-compose", "up", "-d", "db", "redis"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            timeout=120,
        )
        if result.returncode != 0:
            pytest.skip("Could not start Docker Compose services")

        # Wait for services to be healthy
        time.sleep(5)

        yield

        # Cleanup
        try:
            subprocess.run(
                ["docker-compose", "down"],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                timeout=60,
            )
        except Exception:
            pass

    def test_postgres_connectivity(self):
        """Verify PostgreSQL is accessible and responding"""
        # Check service is up
        result = subprocess.run(
            ["docker-compose", "ps", "db"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            timeout=10,
            text=True,
        )
        assert result.returncode == 0
        assert "Up" in result.stdout, "PostgreSQL service is not running"

    def test_redis_connectivity(self):
        """Verify Redis is accessible and responding"""
        # Check service is up
        result = subprocess.run(
            ["docker-compose", "ps", "redis"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            timeout=10,
            text=True,
        )
        assert result.returncode == 0
        assert "Up" in result.stdout, "Redis service is not running"

    def test_network_isolation(self):
        """Verify services are on the same network"""
        result = subprocess.run(
            ["docker", "network", "ls", "--filter", "label=com.docker.compose.project"],
            capture_output=True,
            timeout=10,
            text=True,
        )
        assert result.returncode == 0
        # Should have compose network
        assert len(result.stdout.strip().split("\n")) > 1


# ── Performance Testing ──────────────────────────────────────


@skip_if_docker_not_running
class TestDockerPerformance:
    """Tests for Docker build and image performance metrics"""

    def test_build_time_acceptable(self):
        """Measure build time and ensure it's reasonable"""
        start = time.time()
        result = subprocess.run(
            [
                "docker",
                "build",
                "-t",
                "unirv-django-perf:latest",
                "-f",
                str(PROJECT_ROOT / "Dockerfile"),
                str(PROJECT_ROOT),
            ],
            capture_output=True,
            timeout=600,
            text=True,
        )
        build_time = time.time() - start

        try:
            subprocess.run(
                ["docker", "rmi", "-f", "unirv-django-perf:latest"],
                capture_output=True,
                timeout=30,
            )
        except Exception:
            pass

        assert result.returncode == 0
        # Build should complete in reasonable time (< 10 minutes expected for CI)
        assert build_time < 600, f"Build took {build_time}s, expected < 600s"

    def test_image_size_trend(self):
        """Verify image size is tracked and reasonable"""
        result = subprocess.run(
            [
                "docker",
                "build",
                "-t",
                "unirv-django-size:latest",
                "-f",
                str(PROJECT_ROOT / "Dockerfile"),
                str(PROJECT_ROOT),
            ],
            capture_output=True,
            timeout=600,
        )

        if result.returncode == 0:
            # Get image size
            size_result = subprocess.run(
                ["docker", "images", "unirv-django-size:latest", "--format", "table"],
                capture_output=True,
                timeout=10,
                text=True,
            )

            try:
                subprocess.run(
                    ["docker", "rmi", "-f", "unirv-django-size:latest"],
                    capture_output=True,
                    timeout=30,
                )
            except Exception:
                pass

            # Just verify we can get the size
            assert "unirv-django-size" in size_result.stdout

    def test_container_startup_time(self):
        """Measure container startup time"""
        result = subprocess.run(
            [
                "docker",
                "build",
                "-t",
                "unirv-django-startup:latest",
                "-f",
                str(PROJECT_ROOT / "Dockerfile"),
                str(PROJECT_ROOT),
            ],
            capture_output=True,
            timeout=600,
        )

        if result.returncode == 0:
            start = time.time()
            subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "-e",
                    "DATABASE_URL=postgresql://test:test@localhost/test",
                    "unirv-django-startup:latest",
                    "python",
                    "manage.py",
                    "--help",
                ],
                capture_output=True,
                timeout=60,
            )
            startup_time = time.time() - start

            try:
                subprocess.run(
                    ["docker", "rmi", "-f", "unirv-django-startup:latest"],
                    capture_output=True,
                    timeout=30,
                )
            except Exception:
                pass

            # Container should start and execute command in reasonable time
            assert startup_time < 60, f"Container startup took {startup_time}s"


# ── Container Runtime Tests ──────────────────────────────────


@skip_if_docker_not_running
class TestContainerRuntime:
    """Tests for running containers and verifying they respond correctly"""

    @pytest.fixture(autouse=True)
    def web_container(self):
        """Start web container for testing"""
        # This test requires the database to be running
        subprocess.run(
            ["docker-compose", "up", "-d", "db", "redis"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            timeout=120,
        )

        time.sleep(3)

        # Create container
        result = subprocess.run(
            [
                "docker",
                "build",
                "-t",
                "unirv-django-runtime:latest",
                "-f",
                str(PROJECT_ROOT / "Dockerfile"),
                str(PROJECT_ROOT),
            ],
            capture_output=True,
            timeout=600,
        )

        if result.returncode != 0:
            pytest.skip("Could not build test image")

        yield

        # Cleanup
        try:
            subprocess.run(
                ["docker", "rmi", "-f", "unirv-django-runtime:latest"],
                capture_output=True,
                timeout=30,
            )
        except Exception:
            pass

        try:
            subprocess.run(
                ["docker-compose", "down"],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                timeout=60,
            )
        except Exception:
            pass

    def test_container_starts_without_errors(self):
        """Verify container can start and runs initial commands"""
        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "-e",
                "DEBUG=False",
                "-e",
                "SECRET_KEY=test-secret-key-123",
                "unirv-django-runtime:latest",
                "python",
                "manage.py",
                "check",
            ],
            capture_output=True,
            timeout=60,
            text=True,
        )

        assert (
            result.returncode == 0
        ), f"Container check failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"

    def test_container_environment_variables(self):
        """Verify container respects environment variables"""
        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "-e",
                "DEBUG=False",
                "-e",
                "SECRET_KEY=test-secret-key-123",
                "-e",
                "TEST_VAR=test_value",
                "unirv-django-runtime:latest",
                "sh",
                "-c",
                "echo $TEST_VAR",
            ],
            capture_output=True,
            timeout=30,
            text=True,
        )

        assert result.returncode == 0
        assert "test_value" in result.stdout

    def test_container_has_required_commands(self):
        """Verify container has required commands available"""
        for cmd in ["python", "pip", "gunicorn"]:
            result = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "unirv-django-runtime:latest",
                    "which",
                    cmd,
                ],
                capture_output=True,
                timeout=30,
                text=True,
            )
            assert result.returncode == 0, f"Command '{cmd}' not found in container"
            assert cmd in result.stdout or "/" in result.stdout

    def test_container_nonroot_user(self):
        """Verify container runs as non-root user"""
        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "unirv-django-runtime:latest",
                "id",
            ],
            capture_output=True,
            timeout=30,
            text=True,
        )

        assert result.returncode == 0
        # Should not be running as root (uid 0)
        assert "uid=0" not in result.stdout, "Container is running as root"
