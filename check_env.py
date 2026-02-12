#!/usr/bin/env python
"""
Environment Configuration Validator
Checks if your .env file is correctly set up for the current environment.
"""

import os
import sys
from pathlib import Path

# Add project to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

try:
    import django
    from django.conf import settings

    django.setup()
except Exception as e:
    print(f"❌ Error initializing Django: {e}")
    print("   Make sure Django is installed: pip install -r requirements-dev.txt")
    sys.exit(1)

import environ


def check_env_file():
    """Check if .env file exists"""
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return False, ".env file not found"
    return True, "✓ .env file found"


def check_django_core():
    """Check core Django settings"""
    issues = []

    # SECRET_KEY
    if not settings.SECRET_KEY or settings.SECRET_KEY.startswith("django-insecure"):
        issues.append(
            "⚠️  Using insecure SECRET_KEY (dev key). Generate for production!"
        )

    # DEBUG
    if settings.DEBUG:
        print("ℹ️  DEBUG=True (expected in development)")
    else:
        print("✓ DEBUG=False (production-ready)")

    # ALLOWED_HOSTS
    if not settings.ALLOWED_HOSTS:
        issues.append("❌ ALLOWED_HOSTS is empty!")
    elif settings.ALLOWED_HOSTS == ["localhost", "127.0.0.1", "[::1]"]:
        print("ℹ️  ALLOWED_HOSTS set to localhost (expected in development)")

    return issues


def check_database():
    """Check database configuration"""
    issues = []

    try:
        db_config = settings.DATABASES.get("default", {})
        engine = db_config.get("ENGINE", "")

        if "postgresql" not in engine and "sqlite" not in engine:
            issues.append(f"⚠️  Using {engine} (PostgreSQL recommended for production)")

        # Try connecting
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✓ Database connection successful")
    except Exception as e:
        issues.append(f"❌ Database connection failed: {e}")

    return issues


def check_redis():
    """Check Redis/Cache configuration"""
    issues = []

    redis_url = os.environ.get("REDIS_URL", "")
    redis_host = os.environ.get("REDIS_HOST", "")

    if not redis_url and not redis_host:
        print("ℹ️  Redis not configured (using LocMemCache fallback)")
        return issues

    try:
        import redis

        if redis_url:
            r = redis.from_url(redis_url)
        else:
            port = int(os.environ.get("REDIS_PORT", "6379"))
            password = os.environ.get("REDIS_PASSWORD", None)
            r = redis.Redis(
                host=redis_host, port=port, password=password, decode_responses=True
            )

        r.ping()
        print("✓ Redis connection successful")
    except Exception as e:
        issues.append(f"⚠️  Redis connection failed: {e}")

    return issues


def check_email():
    """Check email configuration"""
    email_backend = settings.EMAIL_BACKEND

    if "console" in email_backend:
        print("ℹ️  Using console email backend (emails print to terminal)")
    elif "smtp" in email_backend:
        print("ℹ️  Using SMTP backend")
    elif "mailersend" in email_backend or "anymail" in email_backend:
        print("✓ Using production email service")
    else:
        print(f"ℹ️  Using: {email_backend}")


def check_celery():
    """Check Celery configuration"""
    use_celery = settings.USE_CELERY

    if use_celery:
        print("✓ Celery enabled (async tasks)")
    else:
        print("ℹ️  Celery disabled (using synchronous tasks)")


def check_static_files():
    """Check static files configuration"""
    issues = []

    tailwind_compile = (
        os.environ.get("TAILWIND_COMPILE_ON_THE_FLY", "False").lower() == "true"
    )

    if tailwind_compile:
        print("ℹ️  Tailwind compiles on-the-fly (development mode)")
    else:
        print("✓ Tailwind pre-compiled (production mode)")

    return issues


def check_logging():
    """Check logging configuration"""
    log_level = os.environ.get("DJANGO_LOG_LEVEL", "INFO")
    print(f"ℹ️  Log level: {log_level}")


def main():
    """Run all checks"""
    print("=" * 50)
    print("Environment Configuration Validator")
    print("=" * 50)
    print()

    all_issues = []

    # Check .env file
    exists, msg = check_env_file()
    print(msg)
    if not exists:
        print("❌ Setup .env file first: cp .env.development .env")
        sys.exit(1)
    print()

    # Core Django
    print("Django Core Configuration:")
    print("-" * 50)
    issues = check_django_core()
    all_issues.extend(issues)
    print()

    # Database
    print("Database Configuration:")
    print("-" * 50)
    issues = check_database()
    all_issues.extend(issues)
    print()

    # Redis
    print("Cache Configuration (Redis):")
    print("-" * 50)
    issues = check_redis()
    all_issues.extend(issues)
    print()

    # Email
    print("Email Configuration:")
    print("-" * 50)
    check_email()
    print()

    # Celery
    print("Background Tasks (Celery):")
    print("-" * 50)
    check_celery()
    print()

    # Static Files
    print("Static Files & Assets:")
    print("-" * 50)
    check_static_files()
    print()

    # Logging
    print("Logging:")
    print("-" * 50)
    check_logging()
    print()

    # Summary
    print("=" * 50)
    if all_issues:
        print(f"⚠️  Found {len(all_issues)} issue(s):")
        for issue in all_issues:
            print(f"  {issue}")
        print()
        print("ℹ️  See ENV_SETUP.md for help resolving issues")
        sys.exit(1)
    else:
        print("✅ Environment configuration looks good!")
        print()
        print("Next steps:")
        print("  1. python manage.py migrate")
        print("  2. python manage.py runserver")
        print("  3. Visit http://localhost:8000")
        sys.exit(0)


if __name__ == "__main__":
    main()
