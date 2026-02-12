# Lighthouse Setup — Quick Reference

**Status**: ✅ Modernized & Unified  
**Entry Point**: `python scripts/lighthouse_runner.py`  
**Config**: `.lighthouserc.json`

---

## 🚀 Quick Commands

```bash
# Audit all public URLs (local development)
python scripts/lighthouse_runner.py --all

# Audit with score tracking
python scripts/lighthouse_runner.py --all --track

# Review latest results
python scripts/lighthouse_runner.py --review

# Single URL
python scripts/lighthouse_runner.py --url http://localhost:8000/

# CI mode (multiple runs, public URLs)
python scripts/lighthouse_runner.py --ci

# Clean old reports (>7 days)
python scripts/lighthouse_runner.py --clean
```

## 📊 npm Shortcuts

```bash
# From theme/static_src/ or project root:
npm run lhci:local   # Audit all + track
npm run lhci:review  # Review results
npm run lhci:ci      # CI mode (multi-run)
```

---

## 📋 Configuration

**File**: `.lighthouserc.json`

- **URLs**: 9 public pages (home, editais, login, etc.)
- **Runs**: 3 per URL in CI, 1 in local mode
- **Thresholds**:
  - Performance: ≥ 70
  - Accessibility: ≥ 70
  - Best Practices: ≥ 70
  - SEO: ≥ 70

---

## 📁 File Structure

```
.lighthouserc.json                    # Configuration
scripts/lighthouse_runner.py          # Main CLI
.github/workflows/lighthouse.yml      # CI/CD
lighthouse_reports/
├── localhost_8000.json
├── localhost_8000_editais.json
├── ...
└── lighthouse_scores_history.json
```

---

## 🔧 Troubleshooting

| Issue | Fix |
|-------|-----|
| "Lighthouse not found" | `cd theme/static_src && npm install` |
| "Server not responding" | `python manage.py runserver` |
| "Permission denied" (Windows) | Python runner handles this natively (no workarounds needed) |
| "0.0 accessibility score" | Normal if no violations detected; check `.lighthouserc.json` |

---

## 📚 Full Docs

- **User Guide**: [LIGHTHOUSE_TESTING.md](LIGHTHOUSE_TESTING.md)

---

## ✨ What Changed

| Before | After |
|--------|-------|
| 4 scripts | 1 unified CLI |
| Windows only | All platforms |
| `.js` config | `.json` config |
| PowerShell entry | Python entry |
| Manual temp cleanup | Automatic |

**Result**: Simple, reproducible, cross-platform. ✅

