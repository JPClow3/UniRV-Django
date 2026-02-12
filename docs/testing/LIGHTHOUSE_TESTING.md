# Lighthouse Testing Guide

**AgroHub (UniRV-Django)** — Unified Lighthouse test setup for cross-platform consistency and reproducibility.

## 📋 Quick Start

### Prerequisites

```bash
# 1. Install Node.js dependencies (includes Lighthouse CLI)
cd theme/static_src && npm install
cd ../..

# 2. Start Django server
python manage.py runserver

# 3. (Optional) Ensure PostgreSQL and Redis are running
# See: SETUP_POSTGRES_REDIS.md
```

### Run Audits

```bash
# Single URL
python scripts/lighthouse_runner.py --url http://localhost:8000/

# All public URLs
python scripts/lighthouse_runner.py --all

# All public URLs with score tracking
python scripts/lighthouse_runner.py --all --track

# Review latest reports
python scripts/lighthouse_runner.py --review

# CI-style runs (public pages)
npm run lhci:ci
```

---

## 🎯 Configuration

### `.lighthouserc.json`

Central configuration file for all Lighthouse settings:

```json
{
  "ci": {
    "collect": {
      "url": [...],                  // URLs to audit
      "numberOfRuns": 3,             // Runs per URL (LHCI mode)
      "chromeFlags": [...],          // Chrome launch flags
      "settings": {
        "maxWaitForFcp": 60000,      // Max wait for First Contentful Paint (60s)
        "maxWaitForLoad": 120000,    // Max wait for full page load (120s)
        "skipAudits": []             // Audits to skip (if any)
      }
    },
    "assert": {
      "assertions": {
        "categories:performance": { "minScore": 0.70 },
        "categories:accessibility": { "minScore": 0.70 },
        "categories:best-practices": { "minScore": 0.70 },
        "categories:seo": { "minScore": 0.70 }
      }
    }
  }
}
```

### URL Scope

**Public Pages** (no authentication required, covered in CI):
- `/` (home)
- `/editais/` (call list)
- `/login/`, `/register/` (auth pages)
- `/startups/`, `/ambientes-inovacao/` (info pages)
- `/password-reset/`, `/password-reset/done/`, `/password-reset-complete/`

Dashboard pages are intentionally excluded from CI. Use the management command (`python manage.py run_lighthouse --all-pages`) if you need to audit protected pages locally.

---

## 🚀 Usage

### `scripts/lighthouse_runner.py`

Unified Python CLI for Lighthouse operations:

#### Single URL Audit

```bash
python scripts/lighthouse_runner.py --url http://localhost:8000/
```

**Output:**
```
🔍 Auditing: http://localhost:8000/
   Output: localhost_8000.json
✅ Completed

📊 localhost_8000
------------------------------------------------------------
🟢 Performance          87.0
🟢 Accessibility        92.0
🟢 Best Practices       96.0
🟢 SEO                  89.0
------------------------------------------------------------
🟢 Average:            91.0

```

#### Batch Audit (All Public URLs)

```bash
python scripts/lighthouse_runner.py --all
```

- Runs 1 audit per URL (fast, local development mode)
- Skips dashboard URLs (requires auth)
- Displays scores for each URL
- Returns non-zero exit code if any URL fails to run

#### Batch Audit with Score Tracking

```bash
python scripts/lighthouse_runner.py --all --track
```

- Same as `--all` plus stores historical data in `lighthouse_reports/lighthouse_scores_history.json`
- Enables trend analysis and performance monitoring

#### Review Latest Reports

```bash
python scripts/lighthouse_runner.py --review
```

**Output:**
```
📋 Lighthouse Reports Review
============================================================
📊 localhost_8000
------------------------------------------------------------
🟢 Performance          87.0
🟢 Accessibility        92.0
...

============================================================
🎯 Overall Average:    91.0
============================================================
```

#### Clean Old Reports

```bash
python scripts/lighthouse_runner.py --clean --days 7
```

- Removes reports older than 7 days (customizable with `--days`)

#### CI Mode (Multiple Runs)

```bash
python scripts/lighthouse_runner.py --ci --runs 3
```

- Runs multiple audits per URL (for stability)
- Uses configured public URLs only
- Averages scores across runs
- For enforced thresholds, run `npx lhci autorun --config=.lighthouserc.json`

---

## 🔧 Parameters

All parameters are optional unless specified:

```
--url URL              Single URL to audit
--all                  Audit all public URLs (batch mode)
--review               Review latest reports
--clean                Clean old reports
--ci                   CI mode (configured URLs, multiple runs)
--runs N               Number of runs per URL (default: 1)
--track                Track scores in history (batch/CI modes)
--report-dir DIR       Report output directory (default: lighthouse_reports)
--config FILE          Config file path (default: .lighthouserc.json)
--days N               Days to keep for --clean (default: 7)
```

---

## 📊 Reports & History

### Report Structure

Each audit generates a JSON report in `lighthouse_reports/`:

```
lighthouse_reports/
├── localhost_8000.json           # Home page
├── localhost_8000_editais.json   # Editais list
├── localhost_8000_login.json     # Login page
├── ... (other URLs)
├── lighthouse_scores_history.json # Score history (tracking enabled)
└── .gitkeep
```

### History File Format

`lighthouse_scores_history.json`:
```json
[
  {
    "timestamp": "2026-02-12T15:30:45.123456",
    "reports": {
      "localhost_8000": {
        "performance": 87.0,
        "accessibility": 92.0,
        "best_practices": 96.0,
        "seo": 89.0,
        "average": 91.0
      },
      ...
    },
    "overall_average": 90.5
  },
  ...
]
```

---

## 🔴 Troubleshooting

### "Lighthouse not found"

```bash
# Install dependencies
cd theme/static_src && npm install
cd ../..
```

### "Server not responding: http://localhost:8000"

```bash
# Start Django server
python manage.py runserver
```

### Dashboard URLs fail with 401/403

- Dashboard URLs require authentication
- Use `--all` (excludes dashboard) for local testing
- CI audits public pages only; protected pages are out of scope

### Accessibility score is 0.0

- Lighthouse may have no a11y violations detected
- Check `.lighthouserc.json` `skipAudits` array
- Run detailed accessibility audit: `npx lighthouse http://localhost:8000/ --output=json --output-path=/tmp/lh.json`

### Performance below threshold

- Large bundle sizes: Enable code splitting
- Unoptimized images: Use `<picture>` with WebP, compress PNG/JPG
- Render-blocking resources: Defer non-critical JS, inline critical CSS
- Missing cache headers: Set `Cache-Control: public, max-age=31536000` for static assets
- See [Lighthouse Performance Audit Ref](https://web.dev/performance/)

### Windows temp file permission errors

- Resolved! Python runner handles temp cleanup natively
- No more EPERM errors from Windows AV/EDR locking temp directories
- Temp files are automatically cleaned after run

---

## 🔗 Integration with CI/CD

### GitHub Actions Workflow

Use the provided `.github/workflows/lighthouse.yml`:

```yaml
- name: Run Lighthouse audits
  run: npm run lhci:ci

- name: Upload results
  uses: actions/upload-artifact@v4
  with:
    name: lighthouse-reports
    path: lighthouse_reports/

- name: Comment PR with scores
  if: github.event_name == 'pull_request'
  run: python scripts/comment_lighthouse_results.py
```

### Package.json Scripts

Add to `theme/static_src/package.json`:

```json
{
  "scripts": {
    "lhci:local": "python ../scripts/lighthouse_runner.py --all --track",
    "lhci:ci": "npx lhci autorun --config=../.lighthouserc.json"
  }
}
```

---

## 📈 Performance Targets

| Category | Target | Current |
|----------|--------|---------|
| Performance | ≥ 70 | 🟡 65-69 |
| Accessibility | ≥ 70 | 🟡 0 (no violations) |
| Best Practices | ≥ 70 | 🟢 85-90 |
| SEO | ≥ 70 | 🟢 75-85 |

ℹ️ Check the Lighthouse JSON reports in `lighthouse_reports/` for detailed scoring and issues.

---

## 🛠️ Scripts Reference

### `scripts/lighthouse_runner.py`
Primary unified runner (see above)

### `review_lighthouse.py`
Legacy review script (deprecated; use `--review` flag)

### `scripts/track_lighthouse_scores.py`
Legacy tracking script (deprecated; use `--track` flag)

### Removed Legacy Scripts
- `scripts/run_lighthouse_simple.py`
- `scripts/run_lighthouse_tests.ps1`

---

## 📚 Additional Resources

- [Lighthouse Docs](https://github.com/GoogleChrome/lighthouse)
- [LHCI Docs](https://github.com/GoogleChrome/lighthouse-ci)
- [Web.dev Performance](https://web.dev/performance/)
- [WCAG 2.2 Level AA](https://www.w3.org/TR/WCAG22/)
- [AgroHub Architecture](../architecture/system-architecture.md)

---

## ✅ Checklist: Before Running Audits

- [ ] Django server running on `http://localhost:8000`
- [ ] PostgreSQL + Redis running (for full features)
- [ ] Node.js dependencies installed (`npm install`)
- [ ] `.lighthouserc.json` configured with correct URLs
- [ ] `lighthouse_reports/` directory writable
- [ ] No other services running on port 8000

---

**Last Updated**: February 12, 2026  
**Maintainer**: AgroHub Development Team
