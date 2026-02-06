# Database Structure Review

## Executive Summary

This document provides a comprehensive review of the database models and structure for the AgroHub application. Overall, the database structure is well-designed with good indexing, proper relationships, and validation. However, there is **one critical issue** that needs immediate attention.

## Critical Issues

### 🔴 CRITICAL: Related Name Conflict in Project Model

**Location:** `editais/models.py` lines 582 and 591

**Issue:** Both `edital` and `proponente` ForeignKey fields in the `Project` model have the same `related_name='startups'`. This creates a conflict in Django's reverse relationship system.

```python
# Line 579-587
edital = models.ForeignKey(
    Edital,
    on_delete=models.SET_NULL,
    related_name='startups',  # ⚠️ CONFLICT
    ...
)

# Line 588-593
proponente = models.ForeignKey(
    User,
    on_delete=models.CASCADE,
    related_name='startups',  # ⚠️ CONFLICT
    ...
)
```

**Impact:** 
- Django will raise a `SystemCheckError` when running `python manage.py check`
- Reverse relationships from `Edital.startups` and `User.startups` will conflict
- This may cause runtime errors when accessing reverse relations

**Fix Required:**
- Change `proponente.related_name` to something unique like `'startups_owned'` or `'projetos_submetidos'`
- Verify no code uses the reverse relation before changing

**Status:** ✅ **Good news**: No code currently uses these reverse relations (verified via grep), so fixing this is safe.

---

## Model-by-Model Analysis

### 1. Edital Model ✅ **Well Designed**

**Strengths:**
- ✅ Comprehensive field coverage for funding opportunities
- ✅ Proper slug generation with uniqueness constraint
- ✅ Good indexing strategy (8 indexes covering common query patterns)
- ✅ Date validation in `clean()` method
- ✅ Automatic status determination in `save()`
- ✅ HTML sanitization for security (XSS prevention)
- ✅ Audit trail via `django-simple-history`
- ✅ User tracking (`created_by`, `updated_by`)
- ✅ Custom QuerySet and Manager for optimized queries
- ✅ PostgreSQL full-text search support with fallback

**Fields:**
- `numero_edital`: CharField(100) - Optional, good for flexibility
- `titulo`: CharField(500) - Appropriate length
- `slug`: SlugField(255) - Unique, auto-generated, indexed
- `url`: URLField(1000) - Good max length for long URLs
- `status`: CharField(20) with choices - Well-defined states
- `start_date`/`end_date`: DateField - Proper date handling
- Content fields: All TextField with blank/null=True - Flexible

**Indexes:** ✅ Excellent coverage
- `idx_data_atualizacao` - For ordering
- `idx_status` - For filtering
- `idx_entidade` - For entity filtering
- `idx_numero` - For number lookup
- `idx_slug` - For URL lookups
- `idx_status_dates` - Composite for date-based queries
- `idx_titulo` - For title searches

**Relationships:**
- ✅ `created_by` / `updated_by`: SET_NULL (preserves data if user deleted)
- ✅ `valores`: One-to-many via EditalValor
- ✅ `cronogramas`: One-to-many via Cronograma
- ✅ `startups`: One-to-many via Project (reverse relation)

**Recommendations:**
- ✅ Consider adding a `db_index=True` on `status` field directly (already has Meta index)
- ✅ Consider adding a unique constraint on `(numero_edital, entidade_principal)` if duplicates shouldn't exist

---

### 2. EditalValor Model ✅ **Well Designed**

**Strengths:**
- ✅ Supports multiple currencies (BRL, USD, EUR)
- ✅ DecimalField with proper precision (15 digits, 2 decimals)
- ✅ MinValueValidator prevents negative values
- ✅ Composite index on (edital, moeda) for efficient queries
- ✅ CASCADE delete (values deleted with edital)

**Fields:**
- `valor_total`: DecimalField(15,2) - ✅ Appropriate for large values
- `moeda`: CharField(10) with choices - ✅ Good currency support

**Indexes:**
- ✅ `idx_edital_moeda` - Composite index for filtering by edital and currency

**Potential Improvements:**
- ⚠️ Consider adding a unique constraint on `(edital, moeda)` if each edital should only have one value per currency
- ⚠️ Consider adding a `tipo` field if you need to distinguish between "total", "por projeto", etc. (currently not in model but mentioned in README)

---

### 3. Cronograma Model ✅ **Well Designed**

**Strengths:**
- ✅ Flexible date fields (inicio, fim, publicacao)
- ✅ Good indexing for date-based queries
- ✅ CASCADE delete (cronograma deleted with edital)
- ✅ Proper ordering by `data_inicio`

**Fields:**
- `data_inicio`, `data_fim`, `data_publicacao`: All DateField with blank/null - ✅ Flexible
- `descricao`: CharField(300) - ✅ Appropriate length

**Indexes:**
- ✅ `idx_cronograma_edital_data` - Composite for filtering by edital and date
- ✅ `idx_cronograma_data_inicio` - For date-based queries

**Potential Improvements:**
- ⚠️ Consider adding validation in `clean()` to ensure `data_fim >= data_inicio` if both are provided
- ⚠️ Consider adding an `ordem` field if cronograma items need explicit ordering

---

### 4. Project Model ⚠️ **Needs Fix**

**Strengths:**
- ✅ Comprehensive fields for startup/project tracking
- ✅ Good status and category choices
- ✅ Slug generation for SEO-friendly URLs
- ✅ FileField for logo with validation
- ✅ Optional edital relationship (SET_NULL)
- ✅ Good indexing strategy
- ✅ User tracking (proponente)

**Fields:**
- `name`: CharField(200) - ✅ Appropriate
- `description`: TextField - ✅ Good for long descriptions
- `category`: CharField(20) with choices - ✅ Well-defined categories
- `status`: CharField(20) with choices - ✅ Clear lifecycle states
- `contato`: TextField - ✅ Flexible for various contact info
- `slug`: SlugField(255) - ✅ Unique, indexed
- `logo`: FileField - ✅ With validation in `clean()`

**Indexes:** ✅ Good coverage
- `idx_project_submitted` - For ordering
- `idx_project_status` - For filtering
- `idx_project_edital_status` - Composite for filtering
- `idx_project_proponente` - For user's projects
- `idx_project_category` - For category filtering
- `idx_project_slug` - For URL lookups

**Issues:**
- 🔴 **CRITICAL**: Related name conflict (see Critical Issues above)
- ⚠️ Table name is `editais_startup` but model is `Project` - Consider renaming model to `Startup` for consistency

**Relationships:**
- `edital`: SET_NULL (good - preserves projects if edital deleted)
- `proponente`: CASCADE (good - deletes projects if user deleted)

**Potential Improvements:**
- ⚠️ Consider adding `website` field separately from `contato` for structured data
- ⚠️ Consider adding `founded_date` or `incubacao_start_date` for better tracking
- ⚠️ Consider adding `tags` ManyToManyField for flexible categorization

---

## Database Configuration

### Settings Analysis ✅ **Well Configured**

**Database Backend:**
- ✅ SQLite for development (default)
- ✅ PostgreSQL for production (with connection pooling)
- ✅ Proper fallback handling

**Connection Settings:**
- ✅ `CONN_MAX_AGE=600` for connection pooling
- ✅ `connect_timeout=10` for connection management

**Recommendations:**
- ✅ Consider adding `ATOMIC_REQUESTS=True` for production if needed
- ✅ Consider adding database query logging in development

---

## Indexing Strategy

### Current Indexes ✅ **Excellent**

**Edital Model:**
- 8 indexes covering all common query patterns
- Composite indexes for multi-field queries
- Proper ordering indexes

**EditalValor Model:**
- 1 composite index for (edital, moeda)

**Cronograma Model:**
- 2 indexes for date-based queries

**Project Model:**
- 6 indexes covering common queries

**PostgreSQL-Specific:**
- ✅ Full-text search indexes (GIN)
- ✅ Trigram indexes for fuzzy search
- ✅ Proper extension usage (pg_trgm)

**Recommendations:**
- ✅ Indexes are well-designed
- ⚠️ Monitor query performance and add indexes if needed for new query patterns

---

## Data Integrity

### Constraints ✅ **Good**

**Uniqueness:**
- ✅ `Edital.slug` - Unique constraint
- ✅ `Project.slug` - Unique constraint

**Foreign Keys:**
- ✅ All ForeignKeys have proper `on_delete` strategies
- ✅ SET_NULL for optional relationships (preserves data)
- ✅ CASCADE for required relationships (maintains referential integrity)

**Validation:**
- ✅ Date validation in `Edital.clean()`
- ✅ File validation in `Project.clean()`
- ✅ MinValueValidator on `EditalValor.valor_total`

**Potential Improvements:**
- ⚠️ Consider adding database-level CHECK constraints for date ranges
- ⚠️ Consider adding unique constraint on `(EditalValor.edital, EditalValor.moeda)` if needed

---

## Security Considerations

### Current Security ✅ **Good**

**XSS Prevention:**
- ✅ HTML sanitization in `Edital.save()`
- ✅ TextField usage (not HTMLField) prevents automatic rendering

**User Tracking:**
- ✅ `created_by` and `updated_by` for audit trail
- ✅ `django-simple-history` for change tracking

**File Uploads:**
- ✅ File size validation (5MB limit)
- ✅ File extension validation
- ✅ Content type validation

**Recommendations:**
- ✅ Consider adding virus scanning for file uploads in production
- ✅ Consider adding rate limiting for file uploads

---

## Performance Considerations

### Query Optimization ✅ **Excellent**

**Current Optimizations:**
- ✅ Custom QuerySets with `select_related()` and `prefetch_related()`
- ✅ Proper use of `with_related()`, `with_prefetch()`, `with_full_prefetch()`
- ✅ Database indexes on all frequently queried fields
- ✅ PostgreSQL full-text search with ranking

**Recommendations:**
- ✅ Continue using QuerySet optimization methods
- ⚠️ Monitor N+1 query issues in views
- ⚠️ Consider adding database query logging in development

---

## Migration History

### Migration Analysis ✅ **Well Managed**

**Observations:**
- ✅ Migrations are well-structured
- ✅ Proper handling of table renames (Project → Startup table)
- ✅ Data migrations for slug population
- ✅ Extension enabling for PostgreSQL features

**Recent Changes:**
- Migration 0022: Table rename from `editais_project` to `editais_startup`
- Migration 0015: Removed `note` field, added `contato`, updated related names
- Migration 0018-0020: PostgreSQL-specific optimizations

---

## Recommendations Summary

### Immediate Actions Required

1. **🔴 CRITICAL**: Fix related_name conflict in Project model
   - Change `proponente.related_name` from `'startups'` to `'startups_owned'` or similar
   - Create migration to update the relationship

### High Priority Improvements

2. **Consider Model Renaming**: Rename `Project` model to `Startup` for consistency with table name and domain language

3. **Add Unique Constraint**: Consider `unique_together` on `(EditalValor.edital, EditalValor.moeda)` if one value per currency per edital is required

4. **Add Date Validation**: Add `clean()` method to `Cronograma` to validate `data_fim >= data_inicio`

### Medium Priority Improvements

5. **Add Missing Fields**: Consider adding structured fields like `website`, `founded_date` to Project model

6. **Enhance EditalValor**: Consider adding `tipo` field if different value types are needed

7. **Database Constraints**: Add CHECK constraints for date ranges at database level

### Low Priority / Future Considerations

8. **Tags System**: Consider ManyToManyField for flexible categorization

9. **Soft Deletes**: Consider adding `deleted_at` field for soft delete functionality

10. **Audit Fields**: Consider adding `deleted_by` field if soft deletes are implemented

---

## Testing Recommendations

### Database Tests Needed

1. ✅ Test related_name conflict fix
2. ✅ Test date validation in Cronograma
3. ✅ Test unique constraint on EditalValor if added
4. ✅ Test CASCADE/SET_NULL behaviors
5. ✅ Test slug generation uniqueness

---

## Conclusion

The database structure is **well-designed** with:
- ✅ Good indexing strategy
- ✅ Proper relationships and constraints
- ✅ Security considerations
- ✅ Performance optimizations
- ✅ Audit trail support

**Critical Issue:** One related_name conflict needs immediate attention, but it's easily fixable since the reverse relations aren't currently used.

**Overall Grade: A-** (would be A+ after fixing the related_name conflict)

---

## Action Items

- [ ] Fix related_name conflict in Project model
- [ ] Create migration for related_name change
- [ ] Test reverse relationships after fix
- [ ] Consider model renaming (Project → Startup)
- [ ] Review and implement high-priority improvements
- [ ] Add database-level constraints if needed
