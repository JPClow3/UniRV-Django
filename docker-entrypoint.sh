#!/bin/bash
# Docker entrypoint script for UniRV-Django
# Handles database migrations and starts the application server

set -e  # Exit on any error

echo "Starting UniRV-Django application..."

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput || {
    echo "ERROR: Database migrations failed!"
    echo "This could be due to:"
    echo "  - Database connection issues"
    echo "  - Invalid migration files"
    echo "  - Database permissions"
    exit 1
}

echo "Database migrations completed successfully."

# Start the application server
echo "Starting Gunicorn server..."
exec gunicorn UniRV_Django.wsgi:application --bind 0.0.0.0:8000 "$@"

