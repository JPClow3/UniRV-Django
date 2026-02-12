# Environment Configuration Quick Reference

## Side-by-Side Comparison

| Setting | Development | Docker (Staging/Prod) |
|---------|-------------|-----------|
| **SECRET_KEY** | Fixed dev key | Strong random key |
| **DJANGO_DEBUG** | `True` | `False` |
| **ALLOWED_HOSTS** | localhost,127.0.0.1 | your-domain.com |
| **DATABASE** | Local PostgreSQL | Docker or external |
| **REDIS** | Local Redis | Docker or external |
| **EMAIL_BACKEND** | `console.EmailBackend` | `anymail` or `smtp` |
| **CELERY** | `False` | `True` |
| **TAILWIND** | Compile on-the-fly | Pre-compiled |
| **LOGGING** | `DEBUG` | `INFO` / `WARNING` |
| **WHITENOISE_MAX_AGE** | `0` | `31536000` |
| **ENABLE_SILK** | `False` | `False` |

## File Usage Guide

```bash
# Local Development
cp .env.development .env
docker-compose up -d db redis
python manage.py runserver

# Docker Deployment (any environment)
cp .env.docker.example .env
# Edit for your environment (staging or production)
docker-compose up --build -d

# Custom Configuration
cp .env.example .env
# Manually edit for specific needs
```

## Environment Variable Layering

When django-environ reads config, it checks in this order:

1. **OS Environment Variables** (highest priority)
   ```bash
   export SECRET_KEY="..."
   export DATABASE_URL="..."
   ```

2. **`.env` File** (middle priority)
   ```dotenv
   SECRET_KEY=your-secret-key
   DATABASE_URL=postgresql://...
   ```

3. **settings.py Defaults** (lowest priority)
   ```python
   env = environ.Env(
       DJANGO_DEBUG=(bool, True)
   )
   ```

## Example: Setting Up Different Environments

### Local Development Setup
```bash
# Initial setup
git clone <repo>
cd UniRV-Django
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

# Create local .env
cp .env.development .env

# Start services
docker-compose up -d db redis

# Run migrations
python manage.py migrate

# Start dev server
python manage.py runserver
```

### Docker Production-Like Testing
```bash
# Use Docker environment file
cp .env.docker.example .env

# Edit for your test values (don't use real production secrets!)
nano .env

# Build and start everything
docker-compose up --build -d

# Check if it's working
docker-compose ps
docker-compose logs web
```

### Production Deployment on Railway

```bash
# 1. Set environment variables in Railway dashboard
# 2. Or create .env from template and import
cp .env.production .env
# Edit with your actual production secrets

# 3. Connect repository to Railway
# 4. Railway automatically deploys

# 5. Set environment variables in Railway UI:
#    - SECRET_KEY
#    - ALLOWED_HOSTS
#    - DATABASE_URL (auto-provided)
#    - REDIS_URL (if using managed Redis)
#    - EMAIL credentials
#    - Other settings
```

## Common Tasks by Environment

### Development Workflow
```bash
# Edit .env if needed
# Make code changes
# Run tests
python manage.py test editais

# See console emails instead of real errors
python manage.py runserver
```

### Staging Testing
```bash
# Copy staging template
cp .env.staging .env

# Edit with staging credentials (not production!)
nano .env

# Deploy code + environment
git push staging-branch
# Webhook auto-deploys to staging server
```

### Production Deployment
```bash
# NEVER use .env files in production (use platform-managed secrets)
# Instead, use Railway dashboard / environment variables

# Example: Railway
# 1. Create .env.production with SECRET_KEY, passwords
# 2. Copy values to Railway environment variables UI
# 3. Don't commit secrets to git!
# 4. Push code to main branch
# 5. Railway auto-deploys
```

## Environment Variable Checklist

### ✅ Before Deploying to Staging
- [ ] `SECRET_KEY` is strong and unique
- [ ] `DJANGO_DEBUG=False`
- [ ] `ALLOWED_HOSTS` matches staging domain
- [ ] Database credentials set correctly
- [ ] Redis/Cache configured
- [ ] Email backend configured
- [ ] HTTPS enabled (SITE_URL=https://...)
- [ ] Logging configured
- [ ] Test email sending

### ✅ Before Deploying to Production
- [ ] All staging checks passed
- [ ] `SECRET_KEY` is strong and NOT shared
- [ ] External database backup configured
- [ ] Redis high availability configured (if critical)
- [ ] Production email service (MailerSend, SendGrid, etc.)
- [ ] CDN configured (optional but recommended)
- [ ] SSL/HTTPS certificates installed
- [ ] Monitoring and logging set up
- [ ] Database backups automated
- [ ] Load balancing configured (if needed)
- [ ] Environment variables are secrets (not in .env file)

## Troubleshooting by Environment

### Development Issues
**Problem:** `.env` file not being read
```bash
# Solution: Ensure .env is in project root
ls -la .env

# Or explicitly set it
export DATABASE_URL="postgresql://..."
python manage.py runserver
```

**Problem:** Can't connect to Redis
```bash
# Solution: Check if running
docker ps | grep redis

# Or start it
docker-compose up -d redis
```

### Docker Issues
**Problem:** "Connect to db:5432 refused"
```bash
# Solution: Container names must match
docker-compose ps  # Check service names

# Or try rebuilding
docker-compose down
docker-compose up --build -d db
```

### Production Issues
**Problem:** Can't read environment variables
```bash
# Solution: Check platform's environment variable settings
# Railway: Check dashboard → Variables
# Vercel: Check .vercelenv
# Heroku: Check Config Vars

# Or set via CLI
heroku config:set SECRET_KEY="..."
```

## Best Practices Summary

1. **Never commit `.env` files** (only templates)
2. **Use strong, unique `SECRET_KEY`** for each environment
3. **Copy from environment templates**, don't create by hand
4. **Test email configuration** before production
5. **Use production email service**, not SMTP
6. **Keep backups** of important credentials
7. **Rotate secrets periodically** in production
8. **Document custom variables** in `.env.example`
9. **Use platform-managed secrets** when possible (Railway, etc.)
10. **Version control templates**, not actual secrets

