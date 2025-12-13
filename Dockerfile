# syntax=docker/dockerfile:1

# ============================================================================
# Stage 1: Node.js build stage - Build Tailwind CSS assets
# ============================================================================
FROM node:20-slim AS node-builder

WORKDIR /app

# Copy only package files for better layer caching
COPY theme/static_src/package*.json ./theme/static_src/

# Install npm dependencies (including dev dependencies for building Tailwind)
WORKDIR /app/theme/static_src
RUN npm ci

# Copy theme source files
COPY theme/static_src/ ./

# Build Tailwind CSS
RUN npm run build

# ============================================================================
# Stage 2: Python builder stage - Install dependencies and collect static
# ============================================================================
FROM python:3.12-slim-bookworm AS python-builder

# Environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies needed for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --user -r /app/requirements.txt

# Copy application code
COPY . /app

# Copy built Tailwind assets from node-builder stage
COPY --from=node-builder /app/theme/static_src/dist ./theme/static_src/dist

# Collect static files
RUN python manage.py collectstatic --noinput

# ============================================================================
# Stage 3: Final runtime stage - Slim production image
# ============================================================================
FROM python:3.12-slim-bookworm

# Environment variables for Python and Django
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_DEBUG=False \
    PATH="/home/django-user/.local/bin:$PATH"

WORKDIR /app

# Install runtime dependencies only (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security (with home directory)
RUN groupadd -r django-user && useradd -r -g django-user -m -d /home/django-user django-user

# Copy Python dependencies from builder stage
COPY --from=python-builder /root/.local /home/django-user/.local

# Ensure proper ownership of home directory
RUN chown -R django-user:django-user /home/django-user

# Copy application code and collected static files from builder stage
COPY --from=python-builder /app /app

# Copy entrypoint script
COPY docker-entrypoint.sh /app/docker-entrypoint.sh

# Set ownership of app directory to django-user and make entrypoint executable
RUN chown -R django-user:django-user /app && \
    chmod +x /app/docker-entrypoint.sh

# Switch to non-root user
USER django-user

# Expose port
EXPOSE 8000

# Set entrypoint script
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Default command (can be overridden)
CMD []
