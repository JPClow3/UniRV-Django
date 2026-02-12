# Multi-Environment Configuration with Django-Environ

## 📋 Overview

This project uses **django-environ** to manage environment variables across multiple deployment environments:

- **Development** - Local machine with console emails
- **Docker** - Containerized deployment (staging or production)
- **Other** - Manually edited `.env` for custom setups

All configuration is based on environment variables, making the app deploy-agnostic and secure.

## 🚀 Quick Start

### For Local Development (SQLite - No Docker)
```bash
# Copy development template (already has SQLite configured)
cp .env.development .env

# Run migrations
python manage.py migrate

# Run tests
pytest editais/tests/ -q

# Start server
python manage.py runserver
```

### For Local Development with Docker (PostgreSQL)
```bash
# Copy development template
cp .env.development .env

# Edit .env to use PostgreSQL (uncomment the DATABASE_URL line)
# nano .env

# Start services
docker-compose up -d db redis

# Run migrations
python manage.py migrate

# Run server
python manage.py runserver
```

### For Docker Deployment
```bash
# Copy Docker template
cp .env.docker.example .env

# Edit with your values
nano .env  # Edit SECRET_KEY, ALLOWED_HOSTS, DB_PASSWORD

# Start
docker-compose up --build -d
```

### Automatic Setup (Recommended)
```bash
# Linux/macOS
bash setup_env.sh

# Windows
setup_env.bat
```

## 📁 Environment Files Structure

| File | Committed? | Purpose |
|------|-----------|---------|
| `.env.example` | ✅ Yes | Complete reference with all variables documented |
| `.env.development` | ✅ Yes | Development defaults (local PostgreSQL, Redis, console email) |
| `.env.docker.example` | ✅ Yes | Docker defaults (container hostnames, production-ready) |
| `.env` | ❌ No | Your actual secrets (created locally, never committed) |

**Never commit `.env` file!** It contains secrets. Use version control for templates only.


## 🔑 Environment Variables

All variables have three sources of configuration (in priority order):

1. **OS Environment Variables** (highest)
   ```bash
   export SECRET_KEY="..."
   export DATABASE_URL="..."
   ```

2. **`.env` File** (middle)
   ```dotenv
   SECRET_KEY=your-secret-key
   DATABASE_URL=postgresql://...
   ```

3. **settings.py Defaults** (lowest)
   ```python
   env = environ.Env(
       SECRET_KEY=(str, "fallback-key"),
       DEBUG=(bool, True),
   )
   ```

### Critical Variables

**All Environments:**
- `SECRET_KEY` - Django secret (generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
- `DJANGO_DEBUG` - Must be `False` in production
- `ALLOWED_HOSTS` - Comma-separated domain list
- `SITE_URL` - Base URL for absolute links

**Database:**
- Either `DATABASE_URL=postgresql://user:pass@host:port/db`
- Or individual: `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`

**Cache/Queue:**
- Either `REDIS_URL=redis://[:password]@host:port/db`
- Or individual: `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`

**Email:**
- `EMAIL_BACKEND` - Backend to use (console, smtp, anymail)
- `DEFAULT_FROM_EMAIL` - Sender address
- Service-specific: `MAILERSEND_API_TOKEN`, `EMAIL_HOST`, etc.

See `.env.example` for complete list (40+ variables).

## 📊 Environment Comparison

| Feature | Local (SQLite) | Local (Docker) | Docker (Staging/Production) |
|---------|-------------|----------|-----------|
| Debug Mode | ✅ On | ✅ On | ❌ Off |
| Database | SQLite | PostgreSQL | PostgreSQL or managed DB |
| Email | Console | Console | Production service |
| Cache | LocMemCache | Redis | Redis or managed |
| Docker Required | ❌ No | ✅ Yes | ✅ Yes |
| Startup Time | ⚡ Instant | ~10s | ~10s |
| Test Speed | ⚡ Fast | Fast | N/A |

## 🛠️ Setup by Scenario

### Scenario 1: Local Development (SQLite - Fast & No Docker)

```bash
# Initial setup
git clone <repo>
cd UniRV-Django
python -m venv .venv
source .venv/bin/activate          # On Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

# Setup environment (SQLite by default)
cp .env.development .env

# Initialize database
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Run tests
pytest editais/tests/ -q

# Run dev server
python manage.py runserver

# Visit http://localhost:8000
```

**Benefits:**
- ⚡ Instant startup (no Docker)
- 🚀 Fast tests (~75 seconds for full suite)
- 🔧 Simple debugging
- 📦 Minimal dependencies

---

### Scenario 1b: Local Development with Docker (PostgreSQL)

```bash
# Initial setup
git clone <repo>
cd UniRV-Django
python -m venv .venv
source .venv/bin/activate          # On Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

# Setup environment
cp .env.development .env

# Edit .env to use PostgreSQL
sed -i 's|sqlite:///db.sqlite3|postgresql://postgres:postgres@localhost:5432/agrohub_dev|' .env

# Start database services
docker-compose up -d db redis

# Initialize database
python manage.py migrate

# Run tests
pytest editais/tests/ -q

# Run dev server
python manage.py runserver

# Visit http://localhost:8000
```

**When to use:**
- Testing production PostgreSQL features locally
- Running full integration tests
- Preparing for production deployment

---

**What you get:**
- Local PostgreSQL database
- Local Redis cache
- Console email backend (emails print to terminal)
- Tailwind compiles on-the-fly
- Debug mode enabled
- Browser reload available

### Scenario 2: Docker Deployment (Staging or Production)

```bash
# Copy Docker template
cp .env.docker.example .env

# Edit with your values - IMPORTANT!
nano .env
# Update:
# - SECRET_KEY (generate new one)
# - ALLOWED_HOSTS (your domain)
# - DB_PASSWORD (secure password)
# - EMAIL_* (production email service)

# Build and run
docker-compose up --build -d

# Run migrations in container
docker-compose exec web python manage.py migrate

# Create superuser in container (optional)
docker-compose exec web python manage.py createsuperuser

# Check logs
docker-compose logs -f web

# Visit http://localhost:8000 (or your domain)
```

**What you get:**
- Everything runs in Docker
- Production-like setup (no debug, production email, pre-compiled CSS)
- Easy to deploy anywhere (Railway, Heroku, VPS, etc.)
- Close approximation of production environment

### Scenario 3: Custom Environment (Manual)

```bash
# For environments not covered by templates
cp .env.example .env

# Edit with your specific values
nano .env

# Configure manually based on your environment
```

## 🔐 Security Best Practices

✅ **DO:**
- ✓ Generate unique `SECRET_KEY` for each environment
- ✓ Use strong passwords (32+ chars, random)
- ✓ Use production email service (MailerSend, SendGrid)
- ✓ Keep `.env` in `.gitignore`
- ✓ Use platform-managed secrets when possible
- ✓ Rotate secrets periodically
- ✓ Use https://siteurl

❌ **DON'T:**
- ✗ Commit `.env` file to git
- ✗ Reuse production secrets across environments
- ✗ Use simple passwords
- ✗ Use DEBUG=True in production
- ✗ Use console email backend in production
- ✗ Share secrets in messages/emails

## 🐛 Troubleshooting

### `.env` not being read
```bash
# Verify file exists and is in project root
ls -la .env

# Check it's readable
cat .env | head

# Verify django-environ is installed
pip show django-environ
```

### "ALLOWED_HOSTS is empty" error
```bash
# Solution: Set ALLOWED_HOSTS in .env
echo "ALLOWED_HOSTS=localhost,127.0.0.1" >> .env

# Or for production
echo "ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com" >> .env
```

### Database connection refused
```bash
# Check if PostgreSQL is running
docker-compose ps db

# Start it
docker-compose up -d db

# Verify connection
psql $DATABASE_URL -c "SELECT 1"
```

### Redis connection refused
```bash
# Check if Redis is running
docker-compose ps redis

# Start it
docker-compose up -d redis

# Test connection
redis-cli ping
```

## 📚 Documentation

- **`ENV_SETUP.md`** - Detailed setup guide for all environments
- **`ENV_QUICK_REFERENCE.md`** - Side-by-side environment comparison
- **`.env.example`** - All variables with documentation

## 🚀 Deployment Guides

- **Docker** - See `docs/DEPLOY_GUIDE.md`
- **Railway** - See `railway.toml`
- **Heroku** - See `Procfile`
- **AWS/DigitalOcean** - See Django deployment docs

## 📖 Django-Environ Documentation

- [django-environ GitHub](https://github.com/joke2k/django-environ)
- [Django Settings Documentation](https://docs.djangoproject.com/en/5.2/topics/settings/)

## 💡 Tips

### Generate credentials safely

```bash
# Generate SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Generate random password
openssl rand -base64 32

# Generate on Windows (PowerShell)
[System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((New-Guid).Guid))
```

### Use environment-specific logging

```bash
# Development: verbose logs
DJANGO_LOG_LEVEL=DEBUG

# Production: minimal logs
DJANGO_LOG_LEVEL=WARNING
```

### Test environment configuration

```bash
# Start Django shell
python manage.py shell

# Check if variables loaded correctly
>>> from django.conf import settings
>>> settings.DEBUG
>>> settings.DATABASES
>>> settings.REDIS_URL
```

## 🎓 Learning Resources

- django-environ: Variable typing and conversion
- 12-factor app: Environment-based configuration
- Docker: Container environment variables
- Platform docs: Railway, Heroku, etc.

## ❓ Common Questions

**Q: Can I use `.env` in production?**
A: No. Use platform-managed secrets (Railway dashboard, environment variables, etc.). `.env` is for development only.

**Q: Do I need to regenerate SECRET_KEY?**
A: Only once per environment. Don't change it after deployment (existing sessions become invalid).

**Q: Should I commit `.env.example`?**
A: Yes! It's the template. It should NOT contain real secrets, only empty values and documentation.

**Q: Can I use DATABASE_URL and individual DB_* variables together?**
A: No. `DATABASE_URL` takes precedence. Use one or the other, not both.

**Q: How do I switch environments locally?**
A: Just copy a different template: `cp .env.staging .env` or edit `.env` directly.

---

Need help? See `ENV_SETUP.md` or `ENV_QUICK_REFERENCE.md` for more details.

