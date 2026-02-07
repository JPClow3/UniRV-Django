"""
Testes para configurações Docker e validação de imagens.

Verifica:
- Sintaxe e estrutura do Dockerfile
- Validação YAML do docker-compose.yml
- Variáveis de ambiente obrigatórias
- Melhores práticas de segurança
- Scripts de entrada (entrypoint)
- Verificações de saúde (healthchecks)
"""

import os
import re
import subprocess
from pathlib import Path
from unittest import mock
import yaml
from django.test import TestCase


class DockerfileValidationTest(TestCase):
    """Testes de validação do Dockerfile"""

    @classmethod
    def setUpClass(cls):
        """Configuração inicial para todos os testes"""
        super().setUpClass()
        cls.project_root = Path(__file__).parent.parent.parent
        cls.dockerfile_path = cls.project_root / "Dockerfile"

        if cls.dockerfile_path.exists():
            with open(cls.dockerfile_path, "r") as f:
                cls.dockerfile_content = f.read()
        else:
            cls.dockerfile_content = None

    def test_dockerfile_exists(self):
        """Verifica se o Dockerfile existe"""
        self.assertTrue(
            self.dockerfile_path.exists(),
            f"Dockerfile não encontrado em {self.dockerfile_path}",
        )

    def test_dockerfile_is_readable(self):
        """Verifica se o Dockerfile é legível"""
        self.assertTrue(
            self.dockerfile_path.is_file() and os.access(self.dockerfile_path, os.R_OK),
            "Dockerfile não é legível",
        )

    def test_dockerfile_has_valid_syntax(self):
        """Verifica se o Dockerfile tem sintaxe válida básica"""
        self.assertIsNotNone(self.dockerfile_content, "Dockerfile não foi carregado")

        # Verificar instruções básicas
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
        content_upper = self.dockerfile_content.upper()

        has_valid_instruction = any(
            f"\n{instr} " in f"\n{content_upper}" for instr in valid_instructions
        )

        self.assertTrue(
            has_valid_instruction,
            f"Dockerfile não contém nenhuma instrução Docker válida",
        )

    def test_dockerfile_uses_multistage_build(self):
        """Verifica se o Dockerfile usa multi-stage build"""
        self.assertIsNotNone(self.dockerfile_content)

        # Contar quantos FROM statements há (multi-stage = múltiplo FROM)
        from_count = len(
            re.findall(r"^\s*FROM\s+", self.dockerfile_content, re.MULTILINE)
        )

        self.assertGreaterEqual(
            from_count,
            2,
            "Dockerfile deveria usar multi-stage build (pelo menos 2 FROM)",
        )

    def test_dockerfile_uses_nonroot_user(self):
        """Verifica se o Dockerfile usa usuário não-root"""
        self.assertIsNotNone(self.dockerfile_content)

        # Verificar se há criação de usuário não-root
        has_user_creation = (
            "useradd" in self.dockerfile_content or "USER " in self.dockerfile_content
        )

        self.assertTrue(
            has_user_creation, "Dockerfile deveria criar e usar um usuário não-root"
        )

    def test_dockerfile_disables_apt_recommends(self):
        """Verifica se apt-get usa --no-install-recommends"""
        self.assertIsNotNone(self.dockerfile_content)

        # Verificar se apt-get usa flag --no-install-recommends
        apt_lines = re.findall(
            r"apt-get install.*", self.dockerfile_content, re.IGNORECASE
        )

        if apt_lines:
            for line in apt_lines:
                self.assertIn(
                    "--no-install-recommends",
                    line,
                    "apt-get install deveria usar --no-install-recommends",
                )

    def test_dockerfile_cleans_apt_cache(self):
        """Verifica se o Dockerfile limpa o cache do apt"""
        self.assertIsNotNone(self.dockerfile_content)

        # Verificar limpeza de apt cache
        has_apt_cleanup = (
            "apt-get clean" in self.dockerfile_content
            and "/var/lib/apt/lists" in self.dockerfile_content
        )

        self.assertTrue(
            has_apt_cleanup,
            "Dockerfile deveria limpar cache do apt para reduzir tamanho",
        )

    def test_dockerfile_sets_python_env_vars(self):
        """Verifica se o Dockerfile configura variáveis Python"""
        self.assertIsNotNone(self.dockerfile_content)

        # Verificar variáveis essenciais
        required_env_vars = ["PYTHONDONTWRITEBYTECODE", "PYTHONUNBUFFERED"]

        for var in required_env_vars:
            self.assertIn(
                var, self.dockerfile_content, f"Dockerfile deveria definir {var}"
            )

    def test_dockerfile_uses_pip_cache_dir(self):
        """Verifica se o Dockerfile usa --no-cache-dir com pip"""
        self.assertIsNotNone(self.dockerfile_content)

        # Verificar se pip install usa --no-cache-dir
        pip_lines = re.findall(r"pip install.*", self.dockerfile_content, re.IGNORECASE)

        if pip_lines:
            for line in pip_lines:
                has_cache_optimization = "--no-cache-dir" in line or "--user" in line
                self.assertTrue(
                    has_cache_optimization,
                    "pip install deveria usar --no-cache-dir ou --user",
                )

    def test_dockerfile_no_sudo(self):
        """Verifica se o Dockerfile não usa sudo"""
        self.assertIsNotNone(self.dockerfile_content)

        self.assertNotIn(
            "sudo", self.dockerfile_content.lower(), "Dockerfile não deveria usar sudo"
        )


class DockerComposeValidationTest(TestCase):
    """Testes de validação do docker-compose.yml"""

    @classmethod
    def setUpClass(cls):
        """Configuração inicial para todos os testes"""
        super().setUpClass()
        cls.project_root = Path(__file__).parent.parent.parent
        cls.compose_path = cls.project_root / "docker-compose.yml"

        cls.compose_data = None
        if cls.compose_path.exists():
            try:
                with open(cls.compose_path, "r") as f:
                    cls.compose_data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                cls.compose_data = None
                cls.yaml_error = str(e)

    def test_docker_compose_exists(self):
        """Verifica se docker-compose.yml existe"""
        self.assertTrue(
            self.compose_path.exists(),
            f"docker-compose.yml não encontrado em {self.compose_path}",
        )

    def test_docker_compose_valid_yaml(self):
        """Verifica se docker-compose.yml é YAML válido"""
        self.assertIsNotNone(self.compose_data, "docker-compose.yml não é YAML válido")

    def test_docker_compose_has_services(self):
        """Verifica se docker-compose.yml define serviços"""
        self.assertIsNotNone(self.compose_data)
        self.assertIn(
            "services",
            self.compose_data,
            "docker-compose.yml deveria definir 'services'",
        )

        self.assertGreater(
            len(self.compose_data["services"]),
            0,
            "docker-compose.yml deveria ter pelo menos um serviço",
        )

    def test_docker_compose_has_required_services(self):
        """Verifica se docker-compose.yml tem serviços necessários"""
        self.assertIsNotNone(self.compose_data)

        required_services = ["db", "redis", "web"]
        services = list(self.compose_data.get("services", {}).keys())

        for service in required_services:
            self.assertIn(
                service,
                services,
                f"docker-compose.yml deveria incluir serviço '{service}'",
            )

    def test_docker_compose_db_has_healthcheck(self):
        """Verifica se o serviço db tem healthcheck"""
        self.assertIsNotNone(self.compose_data)

        db_service = self.compose_data["services"].get("db", {})
        self.assertIn("healthcheck", db_service, "Serviço 'db' deveria ter healthcheck")

        healthcheck = db_service["healthcheck"]
        self.assertIn("test", healthcheck, "healthcheck deveria ter 'test'")
        self.assertIn("interval", healthcheck, "healthcheck deveria ter 'interval'")

    def test_docker_compose_redis_has_healthcheck(self):
        """Verifica se o serviço redis tem healthcheck"""
        self.assertIsNotNone(self.compose_data)

        redis_service = self.compose_data["services"].get("redis", {})
        self.assertIn(
            "healthcheck", redis_service, "Serviço 'redis' deveria ter healthcheck"
        )

    def test_docker_compose_web_depends_on_db_redis(self):
        """Verifica se o serviço web depende de db e redis"""
        self.assertIsNotNone(self.compose_data)

        web_service = self.compose_data["services"].get("web", {})
        self.assertIn(
            "depends_on", web_service, "Serviço 'web' deveria ter 'depends_on'"
        )

        depends_on = web_service["depends_on"]
        for service in ["db", "redis"]:
            self.assertIn(
                service, depends_on, f"Serviço 'web' deveria depender de '{service}'"
            )

    def test_docker_compose_web_build_configured(self):
        """Verifica se o serviço web tem build configurado"""
        self.assertIsNotNone(self.compose_data)

        web_service = self.compose_data["services"].get("web", {})
        self.assertIn(
            "build", web_service, "Serviço 'web' deveria ter 'build' configurado"
        )

        build_config = web_service["build"]
        self.assertIn("context", build_config, "build deveria ter 'context'")

    def test_docker_compose_volumes_defined(self):
        """Verifica se volumes estão definidos"""
        self.assertIsNotNone(self.compose_data)

        self.assertIn(
            "volumes", self.compose_data, "docker-compose.yml deveria definir 'volumes'"
        )

        required_volumes = ["postgres_data", "redis_data", "media_data", "static_data"]
        volumes = list(self.compose_data["volumes"].keys())

        for vol in required_volumes:
            self.assertIn(vol, volumes, f"Volume '{vol}' deveria ser definido")

    def test_docker_compose_networks_defined(self):
        """Verifica se redes estão definidas"""
        self.assertIsNotNone(self.compose_data)

        self.assertIn(
            "networks",
            self.compose_data,
            "docker-compose.yml deveria definir 'networks'",
        )

    def test_docker_compose_restart_policies(self):
        """Verifica se as políticas de restart são configuradas"""
        self.assertIsNotNone(self.compose_data)

        for service_name, service_config in self.compose_data["services"].items():
            self.assertIn(
                "restart",
                service_config,
                f"Serviço '{service_name}' deveria ter política de restart",
            )


class DockerEnvironmentVariablesTest(TestCase):
    """Testes para validação de variáveis de ambiente"""

    @classmethod
    def setUpClass(cls):
        """Configuração inicial para todos os testes"""
        super().setUpClass()
        cls.project_root = Path(__file__).parent.parent.parent
        cls.entrypoint_path = cls.project_root / "docker-entrypoint.sh"
        cls.compose_path = cls.project_root / "docker-compose.yml"
        cls.dockerfile_path = cls.project_root / "Dockerfile"

    def test_required_env_vars_in_compose(self):
        """Verifica se variáveis obrigatórias estão no docker-compose.yml"""
        with open(self.compose_path, "r") as f:
            compose_content = f.read()

        required_vars = [
            "SECRET_KEY",
            "DB_PASSWORD",
            "ALLOWED_HOSTS",
            "DB_NAME",
            "DB_USER",
        ]

        for var in required_vars:
            self.assertIn(
                var,
                compose_content,
                f"docker-compose.yml deveria referenciar variável '{var}'",
            )

    def test_env_var_defaults_documented(self):
        """Verifica se variáveis de ambiente têm valores padrão documentados"""
        with open(self.compose_path, "r") as f:
            compose_content = f.read()

        # Verificar se há documentação de valores padrão (${VAR:-default})
        default_pattern = r"\$\{[A-Z_]+:-[^}]*\}"
        defaults = re.findall(default_pattern, compose_content)

        self.assertGreater(
            len(defaults),
            0,
            "docker-compose.yml deveria ter valores padrão para variáveis",
        )

    def test_no_hardcoded_secrets(self):
        """Verifica se não há segredos hardcodificados"""
        files_to_check = [self.dockerfile_path, self.compose_path]

        for filepath in files_to_check:
            if filepath.exists():
                with open(filepath, "r") as f:
                    content = f.read()

                # Check for hardcoded secrets - look for actual secret values, not variable references
                # Pattern: SECRET_KEY=somevalue (not SECRET_KEY=${...})
                secret_patterns = [
                    r'SECRET_KEY\s*=\s*["\']([^${}][a-zA-Z0-9]+)["\']',
                    r'PASSWORD\s*=\s*["\']([^${}][a-zA-Z0-9]+)["\']',
                    r'DB_PASSWORD\s*=\s*["\']([^${}][a-zA-Z0-9]+)["\']',
                ]

                for pattern in secret_patterns:
                    matches = re.findall(pattern, content)
                    # These should be variable references only, not actual secrets
                    self.assertEqual(
                        len(matches),
                        0,
                        f"{filepath.name} não deveria ter segredos hardcodificados",
                    )


class DockerEntrypointValidationTest(TestCase):
    """Testes de validação do script de entrada (entrypoint)"""

    @classmethod
    def setUpClass(cls):
        """Configuração inicial para todos os testes"""
        super().setUpClass()
        cls.project_root = Path(__file__).parent.parent.parent
        cls.entrypoint_path = cls.project_root / "docker-entrypoint.sh"

        if cls.entrypoint_path.exists():
            with open(cls.entrypoint_path, "r") as f:
                cls.entrypoint_content = f.read()
        else:
            cls.entrypoint_content = None

    def test_entrypoint_exists(self):
        """Verifica se docker-entrypoint.sh existe"""
        self.assertTrue(
            self.entrypoint_path.exists(),
            f"docker-entrypoint.sh não encontrado em {self.entrypoint_path}",
        )

    def test_entrypoint_is_executable(self):
        """Verifica se docker-entrypoint.sh é executável"""
        self.assertTrue(
            os.access(self.entrypoint_path, os.X_OK),
            "docker-entrypoint.sh deveria ser executável",
        )

    def test_entrypoint_has_shebang(self):
        """Verifica se o script tem shebang bash"""
        self.assertIsNotNone(self.entrypoint_content)
        self.assertTrue(
            self.entrypoint_content.startswith("#!/bin/bash"),
            "Script deveria começar com #!/bin/bash",
        )

    def test_entrypoint_has_set_commands(self):
        """Verifica se o script tem configurações de segurança"""
        self.assertIsNotNone(self.entrypoint_content)

        # Verificar se tem set -e (exit on error)
        self.assertIn(
            "set -e",
            self.entrypoint_content,
            "Script deveria usar 'set -e' para sair em caso de erro",
        )

    def test_entrypoint_handles_db_connection(self):
        """Verifica se o script trata conexão com banco de dados"""
        self.assertIsNotNone(self.entrypoint_content)

        db_checks = [
            "pg_isready" in self.entrypoint_content
            or "DB_" in self.entrypoint_content
            or "database" in self.entrypoint_content.lower()
        ]

        self.assertTrue(
            any(db_checks), "Script deveria verificar conexão com banco de dados"
        )

    def test_entrypoint_handles_migrations(self):
        """Verifica se o script executa migrações"""
        self.assertIsNotNone(self.entrypoint_content)

        self.assertIn(
            "migrate",
            self.entrypoint_content.lower(),
            "Script deveria executar migrações do Django",
        )

    def test_entrypoint_starts_gunicorn(self):
        """Verifica se o script inicia o Gunicorn"""
        self.assertIsNotNone(self.entrypoint_content)

        # Verificar se gunicorn é iniciado
        has_gunicorn = (
            "gunicorn" in self.entrypoint_content.lower()
            or "exec" in self.entrypoint_content
        )

        self.assertTrue(has_gunicorn, "Script deveria iniciar o Gunicorn")

    def test_entrypoint_has_logging_functions(self):
        """Verifica se o script tem funções de logging"""
        self.assertIsNotNone(self.entrypoint_content)

        logging_functions = ["log_info", "log_warn", "log_error"]

        for func in logging_functions:
            self.assertIn(
                func,
                self.entrypoint_content,
                f"Script deveria ter função '{func}' para logging",
            )


class DockerSecurityTest(TestCase):
    """Testes de segurança para configuração Docker"""

    @classmethod
    def setUpClass(cls):
        """Configuração inicial para todos os testes"""
        super().setUpClass()
        cls.project_root = Path(__file__).parent.parent.parent
        cls.dockerfile_path = cls.project_root / "Dockerfile"
        cls.compose_path = cls.project_root / "docker-compose.yml"

        with open(cls.dockerfile_path, "r") as f:
            cls.dockerfile_content = f.read()

        with open(cls.compose_path, "r") as f:
            cls.compose_content = f.read()

    def test_dockerfile_no_curl_as_install_method(self):
        """Verifica se Dockerfile não usa curl para instalar pacotes via pipe"""
        # curl | bash é inseguro. curl para healthcheck é ok.
        # Procura por padrão perigoso: curl ... | bash
        dangerous_curl = re.search(
            r"curl\s+.*\|\s*bash", self.dockerfile_content, re.IGNORECASE
        )

        self.assertIsNone(
            dangerous_curl,
            "Dockerfile não deveria usar 'curl | bash' para instalar pacotes",
        )

    def test_docker_compose_db_password_required(self):
        """Verifica se docker-compose.yml exige DB_PASSWORD"""
        self.assertIn(
            "DB_PASSWORD:?",
            self.compose_content,
            "docker-compose.yml deve exigir DB_PASSWORD (usando :?)",
        )

    def test_docker_compose_secret_key_required(self):
        """Verifica se docker-compose.yml exige SECRET_KEY"""
        self.assertIn(
            "SECRET_KEY:?",
            self.compose_content,
            "docker-compose.yml deve exigir SECRET_KEY (usando :?)",
        )


class DockerNginxConfigValidationTest(TestCase):
    """Testes de validação da configuração Nginx"""

    @classmethod
    def setUpClass(cls):
        """Configuração inicial para todos os testes"""
        super().setUpClass()
        cls.project_root = Path(__file__).parent.parent.parent
        cls.nginx_conf_path = cls.project_root / "docker" / "nginx" / "nginx.conf"
        cls.nginx_default_conf_path = (
            cls.project_root / "docker" / "nginx" / "conf.d" / "default.conf"
        )

    def test_nginx_conf_exists(self):
        """Verifica se nginx.conf existe"""
        self.assertTrue(
            self.nginx_conf_path.exists(),
            f"nginx.conf não encontrado em {self.nginx_conf_path}",
        )

    def test_nginx_default_conf_exists(self):
        """Verifica se default.conf existe in conf.d"""
        self.assertTrue(
            self.nginx_default_conf_path.exists(),
            f"default.conf não encontrado em {self.nginx_default_conf_path}",
        )

    def test_nginx_conf_contains_server_tokens_off(self):
        """Verifica se nginx desabilita exposição de versão"""
        with open(self.nginx_conf_path, "r") as f:
            content = f.read()

        self.assertIn(
            "server_tokens off",
            content,
            "nginx deveria desabilitar server_tokens para não expor versão",
        )

    def test_nginx_has_gzip_compression(self):
        """Verifica se nginx tem compressão gzip configurada"""
        with open(self.nginx_conf_path, "r") as f:
            content = f.read()

        # Procura por configuração de gzip
        has_gzip = "gzip" in content.lower()
        self.assertTrue(has_gzip, "nginx deveria ter gzip configurado para compressão")


class DockerIntegrationTest(TestCase):
    """Testes de integração geral da configuração Docker"""

    @classmethod
    def setUpClass(cls):
        """Configuração inicial para todos os testes"""
        super().setUpClass()
        cls.project_root = Path(__file__).parent.parent.parent
        cls.docker_dir = cls.project_root / "docker"

    def test_docker_directory_structure(self):
        """Verifica se a estrutura de diretório Docker está completa"""
        required_dirs = [
            self.docker_dir,
            self.docker_dir / "nginx",
            self.docker_dir / "postgres",
        ]

        for dir_path in required_dirs:
            self.assertTrue(
                dir_path.exists() and dir_path.is_dir(),
                f"Diretório Docker '{dir_path.name}' não encontrado",
            )

    def test_docker_env_file_mentions_in_docs(self):
        """Verifica se há documentação sobre .env.docker"""
        readme_path = self.project_root / "README.md"

        if readme_path.exists():
            try:
                with open(readme_path, "r", encoding="utf-8") as f:
                    content = f.read().lower()
            except UnicodeDecodeError:
                # Se encontrar erro de encoding, tentar com encoding diferente
                with open(readme_path, "r", encoding="latin-1") as f:
                    content = f.read().lower()

            # Verificar se tem instruções sobre .env ou docker
            has_env_docs = "env" in content or "docker" in content
            self.assertTrue(
                has_env_docs,
                "README deveria mencionar configuração de ambiente para Docker",
            )
