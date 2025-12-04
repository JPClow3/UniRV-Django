# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Environment variables for Python and Django
# PYTHONDONTWRITEBYTECODE: Prevent Python from writing .pyc files
# PYTHONUNBUFFERED: Ensure Python output is sent straight to terminal
# DJANGO_DEBUG: Django debug mode (default: False for production)
#   Override with: docker run -e DJANGO_DEBUG=True ...
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_DEBUG=False

WORKDIR /app

# Install Node.js and npm (required for Tailwind CSS)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

# Install npm dependencies for Tailwind CSS
WORKDIR /app/theme/static_src
RUN npm install

# Build Tailwind CSS before collecting static files
WORKDIR /app
RUN python manage.py tailwind build

# Collect static assets
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Simple entrypoint: run DB migrations then server
CMD ["sh", "-c", "python manage.py migrate && gunicorn UniRV_Django.wsgi:application --bind 0.0.0.0:8000"]
