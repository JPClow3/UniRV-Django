# Problems for Future Fixes

Recorded from test run on 2026-02-12. Use SQLite, pytest, no Redis.

**Removed:** `test_legacy.py`, `test_permissions.py`, legacy test classes from other files.

---

## 1. Admin Tests (`test_admin.py`)

| Test | Likely cause |
|------|--------------|
| `test_admin_can_access_create_page` | Template/context: `VariableDoesNotExist` (logo_template, logo_url, illustration, action_url_name, action_url, stats, meta_template) |
| `test_admin_can_create_edital` | Same template context issues |
| `test_admin_can_access_update_page` | Same |
| `test_admin_can_update_edital` | Same |
| `test_admin_can_access_delete_page` | Same |
| `test_admin_can_delete_edital` | Same |
| `test_admin_can_view_draft_edital` | Same |
| `test_created_by_tracked` | Same or admin form/save logic |
| `test_updated_by_tracked` | Same |

**Action:** Fix template context variables in dashboard/editais admin templates. Ensure `logo_template`, `logo_url`, `illustration`, `action_url_name`, `action_url`, `stats`, `meta_template` are passed or defined.

---

## 2. Form Validation (`test_form_validation.py`)

| Test | Likely cause |
|------|--------------|
| `test_register_password_mismatch` | Form validation or assertion mismatch |
| `test_register_duplicate_email` | Duplicate email detection in form/view |
| `test_edital_titulo_sanitised` | XSS sanitization (bleach) not behaving as expected |
| `test_edital_objetivo_sanitised` | Same |

**Action:** Align form validation expectations with actual behavior; verify bleach sanitization; check duplicate email handling.

---

## 3. Integration (`test_integration.py`)

| Test | Likely cause |
|------|--------------|
| `test_public_pages_reflect_data` | Dashboard stats or template context |
| `test_autocomplete_endpoint` | PostgreSQL `pg_trgm`/similarity; SQLite returns empty |
| `test_search_suggestions_with_query` | Same (PostgreSQL-only) |
| `test_notification_on_edital_creation` | Email/celery or signal wiring |
| `test_register_login_access_dashboard` | Registration/auth flow or redirect |
| `test_staff_only_endpoints` | Staff check or URL names |

**Action:** Autocomplete/suggestions: add SQLite skip or mock. Email/registration: trace signal and email flow.

---

## 4. Security (`test_security.py`)

| Test | Likely cause |
|------|--------------|
| `test_xss_in_titulo` | XSS sanitization or assertion |
| `test_staff_can_delete_edital` | Staff/auth wiring or URL |

**Action:** Re-run with verbose output; inspect XSS sanitization and staff delete flow.

---

## 5. Dashboard Views (`test_dashboard_views.py`)

| Test | Likely cause |
|------|--------------|
| `test_dashboard_query_efficiency` | Query count assertion under SQLite or fixture setup |

**Action:** Adjust N+1 assertion or fixture setup for SQLite.

---

## 6. Bug Hunt (`test_bug_hunt.py`)

| Test | Likely cause |
|------|--------------|
| `test_n1_queries_in_index_view` | Query count differs with SQLite vs PostgreSQL |

**Action:** Relax or parametrize query count for SQLite.

---

## 7. E2E User Journeys (`test_e2e_user_journeys.py`)

| Test | Likely cause |
|------|--------------|
| `test_complete_user_journey_registration_to_project` | Multi-step flow; registration or dashboard redirect |

**Action:** Trace full journey; fix registration or redirect steps.

---

## Template Variables (Recurring)

- `logo_template`, `logo_url`, `stats`, `illustration`, `action_url_name`, `action_url`, `meta_template` – missing in context for editais index/dashboard templates.
- Check `editais/index_partial.html`, `editais/index.html`, `dashboard/editais.html`, and related components.

---

## Environment Notes

- **SQLite:** Search uses `icontains` fallback (PostgreSQL full-text disabled).
- **Autocomplete/suggestions:** Return empty on SQLite (pg_trgm).
- **Redis:** Optional; health check skips Redis when not configured.
- **Coverage:** ~58% total; 85% threshold not met.

---

## 8. Docker Advanced (`test_docker_advanced.py`)

| Test | Likely cause |
|------|--------------|
| `test_docker_build_succeeds` | Docker build context, network, or Windows path |
| `test_docker_build_final_stage_created` | Same |
| `test_docker_build_caches_layers` | Same |
| `test_build_time_acceptable` | Build timeout or environment |

**Action:** Run `docker build -t unirv-django-test:latest .` manually; adjust timeouts or skip on Windows if needed.

---

## How to Reproduce

```powershell
$env:DATABASE_URL="sqlite:///test_db.sqlite3"
$env:REDIS_URL=""
$env:REDIS_HOST=""
pytest editais/tests -v --tb=short -n auto
```
