# syntax=docker/dockerfile:1

# ============================================================================
# Build arguments — override with: docker build --build-arg PYTHON_VERSION=3.13
# ============================================================================
ARG NODE_VERSION=20
ARG PYTHON_VERSION=3.12

# ============================================================================
# Stage 1: Node.js build — Compile Tailwind CSS & minify JavaScript
# ============================================================================
FROM node:${NODE_VERSION}-slim AS node-builder

WORKDIR /app/theme/static_src

# Copy only package files first for better layer caching
COPY theme/static_src/package*.json ./

# Install npm dependencies (dev deps required for Tailwind build)
RUN npm ci \
    && npm cache clean --force

# Copy static JavaScript files that need to be minified
COPY static/js/ /app/static/js/

# Copy theme source files (changes more often than package lock)
COPY theme/static_src/ ./

# Copy template files so Tailwind can scan them for class names.
# The @source directives in styles.css reference ../../../templates/ and
# ../../../editais/ relative to theme/static_src/src/.
COPY templates/ /app/templates/

# Build Tailwind CSS and minify JavaScript
RUN npm run build

# ============================================================================
# Stage 2: Python builder — Install deps, collect static assets
# ============================================================================
FROM python:${PYTHON_VERSION}-slim-bookworm AS python-builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install only build-time system dependencies (gcc for C extensions)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching; install with --user for easy copy later
COPY requirements.txt ./
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy application code
COPY . .

# Overlay built frontend assets from node-builder stage
COPY --from=node-builder /app/theme/static/ ./theme/static/
COPY --from=node-builder /app/static/ ./static/

# Collect static files with production settings (generates manifest hashes)
# DATABASE_URL placeholder required because settings enforce PostgreSQL;
# collectstatic does not actually connect to the database.
RUN DJANGO_DEBUG=False \
    SECRET_KEY=build-only-not-used-at-runtime \
    ALLOWED_HOSTS=* \
    DATABASE_URL=postgres://build:build@localhost/build \
    python manage.py collectstatic --noinput

# ============================================================================
# Stage 3: Runtime — Minimal production image
# ============================================================================
FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime

# OCI image metadata
LABEL org.opencontainers.image.title="AgroHub - UniRV Django" \
    org.opencontainers.image.description="Django application for UniRV Innovation Hub" \
    org.opencontainers.image.source="https://github.com/UniRV/UniRV-Django" \
    org.opencontainers.image.vendor="UniRV"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_DEBUG=False \
    PORT=8000 \
    PATH="/home/django-user/.local/bin:$PATH"

WORKDIR /app

# Install runtime-only system packages (no build tools) and create non-root user
# in a single layer to reduce image size
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r django-user \
    && useradd -r -g django-user -m -d /home/django-user django-user

# Copy Python packages from builder; --chown sets ownership in one step (no extra layer)
COPY --from=python-builder --chown=django-user:django-user /root/.local /home/django-user/.local

# Copy application code and collected static files
COPY --from=python-builder --chown=django-user:django-user /app /app

# Copy entrypoint, fix Windows CRLF line endings, and set permissions in one layer
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN sed -i 's/\r$//' /app/docker-entrypoint.sh \
    && chown django-user:django-user /app/docker-entrypoint.sh \
    && chmod +x /app/docker-entrypoint.sh

# Switch to non-root user
USER django-user

# EXPOSE requires a literal value (no variable interpolation)
EXPOSE 8000

# Health check — increased start-period for migrations on first boot
# Uses hardcoded port 8000 matching EXPOSE and ENV PORT default
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD []
