# WCAG Accessibility and UX Fixes Plan

## Overview
This plan addresses all WCAG 2.1 AA violations and UX improvements identified in the audit. Many fixes are already partially implemented; this plan ensures completeness and consistency.

## Implementation Tasks

### 1. Color Contrast Violations (WCAG AA)

**File: `theme/static_src/src/styles.css`**

- **A. Navigation CTA Button** (Lines 394-415)
  - ✅ Already has solid background on transparent headers
  - Verify contrast ratios meet 4.5:1 minimum
  - Ensure hover state maintains contrast

- **B. Auth Page Labels** (Lines 1986-2000)
  - ✅ Already uses white text with text-shadow on mobile
  - ✅ Desktop override with gray-800 exists
  - Verify implementation matches requirements

- **C. Toast Notifications** (Lines 677-683)
  - ✅ Warning toast already uses amber colors
  - Verify all toast types have sufficient contrast

- **D. Status Badges** (Lines 1009-1027)
  - ✅ Already uses darker colors (amber-900, green-900)
  - Verify border colors provide sufficient definition

### 2. Focus Indicators (WCAG 2.1 AA)

**File: `theme/static_src/src/styles.css`**

- **A. Global Focus Styles** (Lines 417-437)
  - ✅ Already implemented with `:focus-visible`
  - Verify all interactive elements are covered
  - Ensure outline is 3px solid with 2px offset

- **B. Filter Buttons** (Lines 432-437)
  - ✅ Already has focus styles
  - Verify pagination links have focus indicators

**File: `templates/editais/index.html`**

- **Pagination Links** (Lines 214-228)
  - Add `min-w-[44px] min-h-[44px]` classes for touch targets
  - Ensure focus indicators are visible

### 3. Touch Target Sizes (Mobile UX)

**File: `theme/static_src/src/styles.css`**

- **A. Pagination Links** (Lines 826-837)
  - ✅ Already has mobile touch target rules
  - Verify pagination links in template use proper classes

**File: `templates/editais/index.html`**

- **Pagination Links** (Lines 214, 225)
  - Update classes from `p-2` to `px-4 py-3 min-w-[44px] min-h-[44px]`
  - Ensure icons are properly centered

- **B. Toast Close Button** (Lines 656-664)
  - ✅ Already meets 44x44px requirement
  - Verify implementation

### 4. Form Validation (Accessibility)

**File: `editais/forms.py`**

- **A. ARIA Attributes** (Lines 164-169)
  - ✅ Already adds `aria-describedby` and `aria-invalid`
  - ✅ Already adds `aria-required` for required fields
  - Verify all form fields get proper attributes

**File: `templates/editais/create.html`**

- **A. Error Linking** (Lines 77-79, 104-106)
  - ✅ Already uses `id="{{ field.auto_id }}_error"` for error divs
  - ✅ Already has `role="alert"` and `aria-live="polite"`
  - Verify form widget renders `aria-describedby` correctly

- **B. Error Summary Navigation** (Lines 36-44)
  - ✅ Already has error links with proper hrefs
  - Verify JavaScript smooth scroll works (already in `main.js` lines 942-981)

### 5. Loading States (UX)

**File: `static/js/main.js`**

- **A. Search Input Loading** (Lines 165-186)
  - ✅ Already adds `searching` class to wrapper
  - ✅ CSS spinner already implemented (styles.css lines 960-981)

- **B. Filter Selects Loading** (Lines 239-293)
  - ✅ Already adds `loading` class and disables select
  - ✅ CSS loading state already implemented (styles.css lines 984-993)

### 6. Mobile Navigation (UX)

**File: `static/js/main.js`**

- **A. Menu Height Caching** (Lines 400-421)
  - ✅ Already implements caching with safety limits
  - ✅ Cache invalidation on resize already implemented

- **B. Swipe-to-Close** (Lines 453-472)
  - ✅ Already implemented with touch event handlers
  - Verify threshold and behavior

### 7. Empty States (UX)

**File: `templates/components/empty_state.html`**

- **Current Implementation**
  - Basic empty state with icon, title, description
  - Action button support

- **Enhancement Needed**
  - Add search-specific suggestions when search_query exists
  - Add helpful tips for users
  - Improve visual hierarchy

**File: `templates/editais/index.html`**

- **Empty State** (Lines 236-240)
  - Currently uses component include
  - May need custom empty state for search results with suggestions

### 8. Performance - Layout Shifts

**File: `templates/base.html`**

- **A. Images** (Lines 148-157, 324-331)
  - ✅ Already has width/height attributes
  - ✅ Already has loading="lazy" and decoding="async"
  - Verify all images across templates have dimensions

- **B. Font Loading** (Lines 12-28 in styles.css)
  - ✅ Already uses `font-display: swap`
  - ✅ Already has `size-adjust: 100.06%`
  - No changes needed

- **C. GSAP Animations** (static/js/animations.js)
  - **Lines 40-48, 122-130, 260-290**: Uses `y` property which triggers layout
  - **Fix**: Use `transform: translateY()` with `will-change` hint
  - Add `will-change: transform, opacity` before animation
  - Remove `will-change` after animation completes

### 9. Horizontal Scroll (Mobile)

**File: `theme/static_src/src/styles.css`**

- **Lines 142-160**
  - ✅ Already uses `overflow-x: hidden` and `max-width: 100vw`
  - ✅ Container elements have `overflow-x: auto` for internal scrolling
  - No changes needed

### 10. Typography (Readability)

**File: `theme/static_src/src/styles.css`**

- **A. Prose Line Length** (Lines 460-526)
  - ✅ Already uses `max-width: 65ch`
  - ✅ Responsive font sizes already implemented

- **B. Mobile Font Sizes** (Lines 78-82)
  - ✅ Already increases base font size to 17px on mobile
  - No changes needed

### 11. Micro-interactions (Polish)

**File: `theme/static_src/src/styles.css`**

- **A. Card Hover Effects** (Lines 1172-1185)
  - ✅ Already implemented with transform and box-shadow
  - Verify animation performance

- **B. Button Press Animation** (Lines 322-324)
  - ✅ Already has `:active` scale effect
  - No changes needed

- **C. Input Focus Glow** (Lines 995-1002)
  - ✅ Already implemented
  - No changes needed

- **D. Nav Link Underline** (Lines 1347-1366)
  - ✅ Already implemented
  - No changes needed

### 12. Skeleton Loaders

**File: `theme/static_src/src/styles.css`**

- **Lines 1116-1169**
  - ✅ Already uses improved gradient and shimmer animation
  - ✅ Already has pulse effect for skeleton-card
  - No changes needed

### 13. Dark Mode Support

**File: `theme/static_src/src/styles.css`**

- **Lines 2184-2205**
  - ✅ Already implements dark mode with system preference detection
  - ✅ Theme toggle already in main.js (lines 1030-1054)
  - Verify theme toggle button exists in base.html

**File: `templates/base.html`**

- Check if theme toggle button is present in header
- If missing, add button with proper ARIA labels

## Files to Modify

1. **theme/static_src/src/styles.css**
   - Verify all contrast fixes are complete
   - Ensure pagination touch targets are covered

2. **templates/editais/index.html**
   - Update pagination link classes for proper touch targets
   - Enhance empty state for search results (if needed)

3. **static/js/animations.js**
   - Optimize GSAP animations to use transform instead of y
   - Add will-change hints and cleanup

4. **templates/components/empty_state.html**
   - Enhance with search suggestions and tips (optional)

5. **templates/base.html**
   - Verify theme toggle button exists

## Testing Checklist

- [ ] Run Lighthouse audit on all pages
- [ ] Test color contrast with WebAIM Contrast Checker
- [ ] Keyboard navigation test (Tab through entire site)
- [ ] Screen reader test (NVDA/VoiceOver)
- [ ] Touch target size verification on mobile devices
- [ ] Test form validation with screen reader
- [ ] Verify loading states are visible
- [ ] Test mobile menu swipe gesture
- [ ] Check empty states with various scenarios
- [ ] Performance testing (Core Web Vitals)
- [ ] Test dark mode toggle functionality

## Priority Order

1. **High Priority** (WCAG AA violations):
   - Color contrast fixes (verify all are complete)
   - Focus indicators (verify coverage)
   - Touch target sizes (verify pagination)
   - Form validation ARIA (verify implementation)

2. **Medium Priority** (UX improvements):
   - Empty state enhancements
   - GSAP animation optimization
   - Loading state verification

3. **Low Priority** (Polish):
   - Micro-interactions (already implemented)
   - Dark mode verification

