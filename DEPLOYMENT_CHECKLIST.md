# Deployment Checklist

This checklist ensures the UniRV Django application is properly configured and ready for production deployment.

## Pre-Deployment Requirements

### 1. Environment Variables Setup

- [ ] Copy `env.production.example` to `.env.production` (or set environment variables directly)
- [ ] Set `SECRET_KEY` (generate with: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
- [ ] Set `DJANGO_DEBUG=False`
- [ ] Set `ALLOWED_HOSTS` with your production domain(s)
- [ ] Configure database credentials (`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`)
- [ ] Configure Redis if using caching (`REDIS_HOST`, `REDIS_PORT`)
- [ ] Configure email settings (`EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, etc.)
- [ ] Set `COOKIE_DOMAIN` if using subdomains
- [ ] Set `SITE_URL` for absolute URLs in emails

### 2. Security Configuration

- [ ] Verify `SECRET_KEY` is set and secure (never use default value)
- [ ] Verify `DEBUG=False` in production
- [ ] Verify `ALLOWED_HOSTS` includes all valid domains
- [ ] Verify `CSRF_TRUSTED_ORIGINS` is automatically generated from `ALLOWED_HOSTS`
- [ ] Verify `SESSION_COOKIE_SECURE=True` (automatically set when `DEBUG=False` and `ALLOWED_HOSTS` is valid)
- [ ] Verify `CSRF_COOKIE_SECURE=True` (automatically set when `DEBUG=False` and `ALLOWED_HOSTS` is valid)
- [ ] Verify `SECURE_SSL_REDIRECT=True` (automatically set when `DEBUG=False` and `ALLOWED_HOSTS` is valid)
- [ ] Verify HSTS headers are enabled (automatically set when `DEBUG=False` and `ALLOWED_HOSTS` is valid)

### 3. Database Setup

- [ ] PostgreSQL database created (if using PostgreSQL)
- [ ] Database user created with appropriate permissions
- [ ] Database connection tested
- [ ] Run migrations: `python manage.py migrate`
- [ ] Create superuser if needed: `python manage.py createsuperuser`
- [ ] Verify database connection pooling is configured (`CONN_MAX_AGE=600`)

### 4. Static Files and Media

- [ ] Collect static files: `python manage.py collectstatic --noinput`
- [ ] Verify `STATIC_ROOT` directory exists and is writable
- [ ] Configure web server (nginx/apache) to serve static files from `STATIC_ROOT`
- [ ] Configure web server to serve media files from `MEDIA_ROOT` (never execute user-uploaded files)
- [ ] Verify `MEDIA_ROOT` directory exists and is writable
- [ ] Set appropriate file permissions for `STATIC_ROOT` and `MEDIA_ROOT`

### 5. Cache Configuration

- [ ] Redis server running (if using Redis)
- [ ] Redis connection tested (automatic validation on startup)
- [ ] Verify fallback to LocMemCache if Redis fails (automatic)
- [ ] Test cache functionality

### 6. Email Configuration

- [ ] SMTP server accessible
- [ ] Email credentials tested
- [ ] Verify fallback to console backend if SMTP fails (automatic)
- [ ] Test password reset email functionality
- [ ] Test notification emails

### 7. Logging Configuration

- [ ] Set `DJANGO_LOG_TO_FILE=true` if file logging is desired
- [ ] Set `DJANGO_LOG_DIR` to writable directory
- [ ] Verify log directory permissions
- [ ] Verify fallback to console logging if file logging fails (automatic)
- [ ] Configure log rotation (handled automatically by RotatingFileHandler)

### 8. Testing

- [ ] Run test suite: `python manage.py test`
- [ ] Verify all security tests pass
- [ ] Verify XSS prevention tests pass
- [ ] Test rate limiting on login endpoint
- [ ] Test CSRF protection
- [ ] Test authentication and authorization
- [ ] Test form validation
- [ ] Test error handling

### 9. Code Quality

- [ ] Run security audit: `pip-audit` (if installed)
- [ ] Check for outdated dependencies: `pip list --outdated`
- [ ] Review and update dependencies if needed
- [ ] Verify no hardcoded secrets in code
- [ ] Verify no debug code in production

### 10. Performance Optimization

- [ ] Enable static file compression (set `COMPRESS_ENABLED=true`)
- [ ] Run offline compression: `python manage.py compress` (if django-compressor is installed)
- [ ] Verify `COMPRESS_OFFLINE` is enabled only if `STATIC_ROOT` exists (automatic)
- [ ] Configure WhiteNoise cache headers (automatic based on `DEBUG` mode)
- [ ] Test page load times
- [ ] Verify database query optimization

### 11. Web Server Configuration

- [ ] Configure reverse proxy (nginx/apache) to forward requests to Django
- [ ] Configure SSL/TLS certificates
- [ ] Set up proper HTTP headers (security headers are handled by Django)
- [ ] Configure gzip compression
- [ ] Set up proper error pages (404, 500, etc.)
- [ ] Configure request timeouts
- [ ] Set up health check endpoint monitoring (`/health/`)

### 12. Monitoring and Logging

- [ ] Set up application monitoring (e.g., Sentry, New Relic)
- [ ] Configure log aggregation
- [ ] Set up alerts for errors
- [ ] Monitor database performance
- [ ] Monitor cache performance
- [ ] Set up uptime monitoring

### 13. Backup and Recovery

- [ ] Set up database backups (automated)
- [ ] Test database restore procedure
- [ ] Set up media files backup
- [ ] Document recovery procedures
- [ ] Set up backup retention policy

### 14. Final Verification

- [ ] Test all critical user flows
- [ ] Verify HTTPS is working correctly
- [ ] Test password reset functionality
- [ ] Test user registration
- [ ] Test admin dashboard access (staff only)
- [ ] Verify rate limiting is working
- [ ] Test error pages
- [ ] Verify all forms work correctly
- [ ] Test search and filtering
- [ ] Verify pagination works
- [ ] Test mobile responsiveness

## Post-Deployment

### Immediate Checks

- [ ] Monitor application logs for errors
- [ ] Verify all services are running
- [ ] Test critical functionality
- [ ] Monitor server resources (CPU, memory, disk)
- [ ] Check database connections
- [ ] Verify cache is working

### Ongoing Maintenance

- [ ] Regularly update dependencies
- [ ] Monitor security advisories
- [ ] Review and rotate secrets periodically
- [ ] Monitor application performance
- [ ] Review and optimize database queries
- [ ] Clean up old logs
- [ ] Review and update documentation

## Rollback Procedure

If issues are detected after deployment:

1. [ ] Identify the issue and document it
2. [ ] Stop the application server
3. [ ] Restore database from backup if needed
4. [ ] Restore code from previous version
5. [ ] Restart application server
6. [ ] Verify application is working
7. [ ] Document the issue and resolution

## Emergency Contacts

- [ ] Document emergency contact information
- [ ] Set up on-call rotation
- [ ] Document escalation procedures

## Notes

- All security settings are automatically enabled when `DEBUG=False` and `ALLOWED_HOSTS` is properly configured
- Fallback mechanisms are in place for Redis (LocMemCache), email (console backend), and logging (console logging)
- Rate limiting is configured on the login endpoint (5 requests per minute per IP)
- XSS prevention is implemented in forms and templates
- CSRF protection is enabled by default in Django
- All user-uploaded files should be served by the web server, not Django

## Quick Reference Commands

```bash
# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run tests
python manage.py test

# Compress static files (if django-compressor is installed)
python manage.py compress

# Check for security vulnerabilities
pip-audit

# Check for outdated packages
pip list --outdated
```

