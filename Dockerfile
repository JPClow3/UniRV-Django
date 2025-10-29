# syntax=docker/dockerfile:1
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_DEBUG=False

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

# Collect static assets
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Simple entrypoint: run DB migrations then server
CMD ["sh", "-c", "python manage.py migrate && gunicorn UniRV_Django.wsgi:application --bind 0.0.0.0:8000"]
