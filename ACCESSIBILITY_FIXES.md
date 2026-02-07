## ACCESSIBILITY FIXES REQUIRED
**Issue**: Lighthouse accessibility score of 0.0 indicates multiple critical violations

---

## STEPS TO DIAGNOSE AND FIX

### 1. **Generate Detailed Lighthouse Accessibility Report**
```bash
# Run Lighthouse with detailed accessibility output
npm install -g lighthouse
lighthouse http://localhost:8000/ --output-path=detailed-a11y-report.json --only-categories=accessibility

# Or use Chrome DevTools
# 1. Open Chrome DevTools (F12)
# 2. Go to Lighthouse tab
# 3. Click "Analyze page load"
# 4. Look at "Accessibility" section
```

### 2. **Common Accessibility Violations to Check**

#### ❌ Missing Main Content Landmark
```django-html
<!-- INCORRECT - no main landmark -->
<div class="bg-background-light">
  <header>...</header>
  <div class="content">...</div>
</div>

<!-- CORRECT - with main landmark -->
<div class="bg-background-light">
  <header>...</header>
  <main>...</main>
</div>
```

**Fix in `templates/base.html`**: Wrap main content in `<main>` tags

#### ❌ Missing or Incorrect Document Title
```html
<!-- Check if every page has unique, descriptive title -->
<title>AgroHub UniRV - Sector Specific Title</title>
```

#### ❌ Missing Form Labels
```django-html
<!-- INCORRECT -->
<input type="email" placeholder="Email">

<!-- CORRECT -->
<label for="email">Email</label>
<input type="email" id="email" name="email">
```

**Check**: `templates/registration/` and `templates/dashboard/` forms

#### ❌ Missing ARIA Attributes
```django-html
<!-- INCORRECT - button without description -->
<button class="close-btn" onclick="closeModal()">×</button>

<!-- CORRECT - with aria-label -->
<button class="close-btn" aria-label="Fechar modal" onclick="closeModal()">×</button>
```

#### ❌ Color Contrast Issues
```css
/* Check all text/background combinations meet WCAG AA standards (4.5:1) */
/* Examples of potentially low contrast:
   - White text on light gray background
   - Light gray text on white background
   - Light blue on lighter blue
*/
```

#### ❌ Missing Image Descriptions
```django-html
<!-- INCORRECT - decorative image without alt -->
<img src="decorative-line.svg">

<!-- CORRECT - for decorative images -->
<img src="decorative-line.svg" alt="">

<!-- CORRECT - for informative images -->
<img src="chart.svg" alt="Sales increased 25% in Q4">
```

#### ❌ Missing Page Landmarks
```django-html
<!-- Should include these semantic landmarks -->
<header>Navigation and site branding</header>
<nav>Major navigation</nav>
<main>Page content</main>
<footer>Site footer</footer>
```

#### ❌ Link and Button Names
```django-html
<!-- INCORRECT - non-descriptive link text -->
<a href="/edital/1">Clique aqui</a>

<!-- CORRECT - descriptive link text -->
<a href="/edital/1">Ver edital FINEP 2026</a>
```

#### ❌ Heading Hierarchy
```django-html
<!-- INCORRECT - skipped levels -->
<h1>Page Title</h1>
<h3>Subsection</h3>  <!-- Missing h2 -->
<h4>Sub-subsection</h4>

<!-- CORRECT - sequential hierarchy -->
<h1>Page Title</h1>
<h2>Subsection</h2>
<h3>Sub-subsection</h3>
```

#### ❌ Missing List Markup
```django-html
<!-- INCORRECT -->
<div>• Item 1</div>
<div>• Item 2</div>

<!-- CORRECT -->
<ul>
  <li>Item 1</li>
  <li>Item 2</li>
</ul>
```

#### ❌ Focus Indicators
```css
/* Ensure all interactive elements have visible focus indicators */
/* Remove default outlines only if you provide custom focus styles */

/* INCORRECT - removes focus indicator */
button:focus { outline: none; }

/* CORRECT - provides visible focus indicator */
button:focus { outline: 2px solid #2563EB; outline-offset: 2px; }
```

---

## SPECIFIC FIXES FOR THIS PROJECT

### Template Checklist
- [ ] `templates/base.html`
  - [ ] Wrap content in `<main>` tag
  - [ ] Check all links have descriptive text
  - [ ] Verify logo image has alt text ✓ (already has "AgroHub UniRV Logo")

- [ ] `templates/home.html`
  - [ ] Hero image already has descriptive alt ✓
  - [ ] Check all buttons have aria-labels for icon buttons
  - [ ] Verify heading hierarchy (h1 → h2 → h3)

- [ ] `templates/registration/login.html`
  - [ ] Add labels to form inputs
  - [ ] Ensure inputs have associated labels with `for` attribute

- [ ] `templates/registration/register.html`
  - [ ] Add labels to all form fields
  - [ ] Ensure password requirements are announced
  - [ ] Add aria-required="true" to required fields

- [ ] `templates/editais/index.html`
  - [ ] Add aria-label to filter buttons
  - [ ] Verify search input accessibility
  - [ ] Check pagination link descriptions

- [ ] `templates/dashboard/` files
  - [ ] Audit all form elements for labels
  - [ ] Check modal dialogs have proper role and focus management
  - [ ] Verify table accessibility (headers, scope)

### CSS/Contrast Fixes
- [ ] Review color palette in `.lighthouserc.js` and verify WCAG AA compliance
- [ ] Test with Accessibility Insights tool to identify contrast issues
- [ ] Ensure focus visible states on all interactive elements

### Form Accessibility
```django-html
<!-- Current state - potentially missing labels -->
<!-- Need to add:
<label for="field-id">Field Name</label>
before each input
-->

<!-- For checkboxes/radio buttons -->
<fieldset>
  <legend>Group legend</legend>
  <label><input type="radio" name="group"> Option 1</label>
  <label><input type="radio" name="group"> Option 2</label>
</fieldset>
```

---

## TESTING & VALIDATION

### Tools to Use
1. **Lighthouse CI**: Already configured
   ```bash
   npm run test:lighthouse
   ```

2. **axe DevTools** (Chrome Extension)
   - Install from Chrome Web Store
   - Run scan on each page
   - Fix violations

3. **WAVE** (Web Accessibility Evaluation Tool)
   - Wave.webaim.org
   - Browser extension available

4. **Color Contrast Analyzer**
   - Verify 4.5:1 ratio for normal text
   - Verify 3:1 ratio for large text

### Automated Testing
Add accessibility tests to test suite:
```python
# In editais/tests/test_accessibility.py
from django.test import TestCase, Client

class AccessibilityTests(TestCase):
    def setUp(self):
        self.client = Client()
    
    def test_home_page_has_main_landmark(self):
        response = self.client.get('/')
        self.assertContains(response, '<main')
    
    def test_all_images_have_alt_text(self):
        response = self.client.get('/')
        # Parse HTML and check all images have non-empty alt
        # This would require BeautifulSoup
```

---

## PRIORITY FIXES (Before CI can pass)

### Must Have (Blocking)
1. [ ] Ensure at least one `<main>` landmark exists
2. [ ] All form inputs have associated labels
3. [ ] All images have alt text (non-empty)
4. [ ] No color contrast violations (4.5:1 minimum)
5. [ ] Proper heading hierarchy (h1 without skip)
6. [ ] All interactive elements keyboard accessible
7. [ ] Focus indicators visible on all elements

### Should Have (Recommended)
8. [ ] ARIA attributes for complex components
9. [ ] Skip links for repeating content
10. [ ] Semantic HTML (nav, article, section)
11. [ ] Lang attribute on HTML ✓ (already present)
12. [ ] Meta viewport for responsive ✓ (already present)

---

## EXPECTED RESULTS AFTER FIXES

Once accessibility issues are fixed, expect:
```
Changes:
Accessibility: 0.0 → 90+ ✅ (will unblock CI)
Performance: 65-69 → [TBD after fixes]
Best Practices: 100 → 100 ✅
SEO: 100 → 100 ✅
PWA: 33 → [improvement expected]
```

---

## ADDITIONAL RESOURCES

- [WCAG 2.2 Official](https://www.w3.org/WAI/WCAG22/quickref/)
- [MDN Accessibility](https://developer.mozilla.org/en-US/docs/Web/Accessibility)
- [WebAIM](https://webaim.org/)
- [Lighthouse Accessibility Audits](https://developer.chrome.com/docs/lighthouse/accessibility/)

---

**Status**: 🔴 CRITICAL - Requires immediate attention before CI/CD can complete
