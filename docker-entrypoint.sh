#!/bin/bash
# ============================================
# AgroHub - Docker Entrypoint Script
# ============================================
# Handles:
#   - Waiting for PostgreSQL to be ready
#   - Verifying Redis connection (optional)
#   - Running database migrations
#   - Starting Gunicorn with optimized settings

set -e  # Exit on any error

# ============================================
# Configuration
# ============================================
MAX_DB_RETRIES=${MAX_DB_RETRIES:-60}
DB_RETRY_INTERVAL=${DB_RETRY_INTERVAL:-2}
MAX_REDIS_RETRIES=${MAX_REDIS_RETRIES:-10}
REDIS_RETRY_INTERVAL=${REDIS_RETRY_INTERVAL:-1}

# Skip PostgreSQL check if SKIP_DB_WAIT is set (useful for Railway builds)
SKIP_DB_WAIT=${SKIP_DB_WAIT:-false}

# ============================================
# Logging Functions
# ============================================
log_info() {
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo "[WARN] $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1" >&2
}

# ============================================
# Cleanup on exit
# ============================================
cleanup() {
    log_info "Shutting down..."
    # Kill any background processes
    jobs -p | xargs -r kill 2>/dev/null || true
}
trap cleanup EXIT

# ============================================
# Wait for PostgreSQL
# ============================================
wait_for_postgres() {
    log_info "Waiting for database via Django..."

    local retries=0
    local host="${DB_HOST:-db}"
    local port="${DB_PORT:-5432}"
    local user="${DB_USER:-agrohub_user}"
    local db="${DB_NAME:-agrohub_production}"

    while [ $retries -lt $MAX_DB_RETRIES ]; do
        if python - <<EOF
import os, django, sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "UniRV_Django.settings")
django.setup()
from django.db import connection
connection.ensure_connection()
EOF
        then
            log_info "Database is ready!"
            return 0
        fi

        retries=$((retries + 1))
        log_info "Database not ready ($retries/$MAX_DB_RETRIES). Retrying in ${DB_RETRY_INTERVAL}s..."
        sleep $DB_RETRY_INTERVAL
    done

    log_error "Database never became ready!"
    log_error "Connection details: host=$host, port=$port, user=$user, db=$db"
    log_error "DATABASE_URL present: $([ -n "$DATABASE_URL" ] && echo 'yes' || echo 'no')"
    return 1
}

# ============================================
# Wait for Redis (optional)
# ============================================
wait_for_redis() {
    local redis_url="${REDIS_URL:-}"
    local host="${REDIS_HOST:-}"
    local port="${REDIS_PORT:-6379}"

    # Skip if Redis is not configured
    if [ -z "$redis_url" ] && [ -z "$host" ]; then
        log_info "Redis not configured, skipping Redis check."
        return 0
    fi

    local retries=0
    if [ -n "$redis_url" ]; then
        log_info "Waiting for Redis at $redis_url..."
    else
        log_info "Waiting for Redis at $host:$port..."
    fi

    # Check if redis-cli is available
    if ! command -v redis-cli &> /dev/null; then
        log_warn "redis-cli not available, skipping Redis check."
        return 0
    fi

    while [ $retries -lt $MAX_REDIS_RETRIES ]; do
        if [ -n "$redis_url" ]; then
            if redis-cli -u "$redis_url" ping 2>/dev/null | grep -q "PONG"; then
                log_info "Redis is ready!"
                return 0
            fi
        elif redis-cli -h "$host" -p "$port" ping 2>/dev/null | grep -q "PONG"; then
            log_info "Redis is ready!"
            return 0
        fi

        retries=$((retries + 1))
        log_info "Redis not ready (attempt $retries/$MAX_REDIS_RETRIES). Retrying in ${REDIS_RETRY_INTERVAL}s..."
        sleep $REDIS_RETRY_INTERVAL
    done

    log_warn "Redis did not become ready in time. Continuing anyway (cache will use fallback)."
    return 0
}

# ============================================
# Run Database Migrations
# ============================================
run_migrations() {
    log_info "Running database migrations..."

    local retries=0
    local max_retries=5

    until python manage.py migrate --noinput; do
        retries=$((retries + 1))

        if [ $retries -ge $max_retries ]; then
            log_error "Database migrations failed after $max_retries attempts!"
            return 1
        fi

        log_warn "Migration failed (attempt $retries/$max_retries). Retrying in 5 seconds..."
        sleep 5
    done

    log_info "Database migrations completed successfully."
}

# ============================================
# Collect Static Files (if needed)
# ============================================
collect_static() {
    if [ ! -d "/app/staticfiles" ] || [ -z "$(ls -A /app/staticfiles 2>/dev/null)" ]; then
        log_info "Collecting static files..."

        python manage.py collectstatic --noinput || {
            log_error "collectstatic failed"
            return 1
        }

        log_info "Static files collected."
    else
        log_info "Static files already collected, skipping."
    fi
}

# ============================================
# Calculate Gunicorn Workers
# ============================================
get_workers() {
    local workers="${GUNICORN_WORKERS:-}"

    if [ -z "$workers" ] || [ "$workers" = "auto" ]; then
        # Formula: (2 * CPU cores) + 1
        local cpu_count
        cpu_count=$(nproc 2>/dev/null || echo 1)
        workers=$((cpu_count * 2 + 1))

        # Cap at reasonable maximum for most deployments
        if [ $workers -gt 9 ]; then
            workers=9
        fi
    fi

    echo "$workers"
}

# ============================================
# Start Gunicorn
# ============================================
start_gunicorn() {
    local workers
    workers=$(get_workers)
    local port="${PORT:-8000}"

    log_info "Starting Gunicorn with $workers workers..."
    log_info "Configuration:"
    log_info "  - Bind: 0.0.0.0:$port"
    log_info "  - Workers: $workers"
    log_info "  - Threads: 2"
    log_info "  - Timeout: 30s"

    exec gunicorn UniRV_Django.wsgi:application \
        --bind 0.0.0.0:$port \
        --workers "$workers" \
        --threads 2 \
        --worker-class gthread \
        --timeout 30 \
        --keep-alive 5 \
        --max-requests 1000 \
        --max-requests-jitter 50 \
        --access-logfile - \
        --error-logfile - \
        --capture-output \
        --enable-stdio-inheritance \
        "$@"
}

# ============================================
# Main Entrypoint
# ============================================
main() {
    log_info "============================================"
    log_info "Starting AgroHub Application"
    log_info "============================================"
    log_info "Environment: ${RAILWAY_ENVIRONMENT:-local}"
    log_info "PORT: ${PORT:-8000}"
    log_info "DATABASE_URL configured: $([ -n "$DATABASE_URL" ] && echo 'yes' || echo 'no')"
    log_info "REDIS_URL configured: $([ -n "$REDIS_URL" ] && echo 'yes' || echo 'no')"

    # Wait for dependencies
    if [ "$SKIP_DB_WAIT" = "true" ]; then
        log_warn "Skipping PostgreSQL wait (SKIP_DB_WAIT=true)"
    else
        wait_for_postgres || exit 1
    fi
    wait_for_redis

    # Run migrations
    run_migrations || exit 1

    # Collect static files if needed
    collect_static

    # Start the application server
    start_gunicorn "$@"
}

# Run main function with all arguments
main "$@"
