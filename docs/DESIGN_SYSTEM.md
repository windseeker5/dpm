# Minipass Design System Reference

**Version:** 1.0
**Last Updated:** October 27, 2025
**Purpose:** Master template for all page redesigns to ensure consistency

## Table of Contents
1. [Overview](#overview)
2. [Reference Pages](#reference-pages)
3. [Page Title Component](#page-title-component)
4. [Search Bar Component](#search-bar-component)
5. [GitHub-Style Filter Component](#github-style-filter-component)
6. [Table Component](#table-component)
7. [CSS Files to Include](#css-files-to-include)
8. [JavaScript Behavior](#javascript-behavior)
9. [Mobile Responsiveness Rules](#mobile-responsiveness-rules)
10. [Complete Page Template](#complete-page-template)

---

## Overview

This document defines the standard UI patterns used throughout Minipass. The **Activity Dashboard** (`templates/activity_dashboard.html`) and **Passports** page serve as the reference implementations.

### When to Use This Document
- When converting any existing page to the new design
- When creating new list/table pages
- When implementing search functionality
- When adding filter buttons to tables

### Key Principles
- **Consistency:** All pages should look and behave the same way
- **Mobile-First:** Always test on mobile (375px width)
- **No Hover Effects on Tables:** Per project constraints
- **Plain White Cards:** No gradients or fancy effects

---

## Reference Pages

### Master Templates (Copy These)
1. **Activity Dashboard:** `templates/activity_dashboard.html` (lines 1071-1220)
   - Search bar implementation
   - GitHub filter buttons
   - Responsive table layout

2. **Passports Page:** `templates/passports.html`
   - Another perfect implementation
   - Same patterns and styles

### What Makes These Perfect
- Clean, consistent styling
- Perfect mobile responsiveness
- GitHub-style embedded filters
- Enhanced search with Ctrl+K shortcut
- Keyboard hints that hide on mobile
- Proper table column hiding on smaller screens

---

## Page Title Component

### Visual Example
```
🔴 Activity Passport
```

### HTML Structure
```html
<h2 class="mt-4 mb-3">
  <i class="ti ti-activity-heartbeat me-2" style="color: #e03131;"></i>Activity Passport
</h2>
```

### Rules
- Use `<h2>` for page section titles
- Include a Tabler icon with `me-2` margin
- Color the icon (common: `#e03131` red, `#206bc4` blue)
- Keep title concise (2-3 words max)
- **Remove possessive words like "Your"** - use "Activity Passport" not "Your Activity Passport"

### Common Icons
- `ti-activity-heartbeat` - Activities, Passports
- `ti-user-check` - Signups
- `ti-clipboard-check` - Surveys
- `ti-chart-bar` - Reports
- `ti-list` - General lists

---

## Search Bar Component

### Visual Features
- Large rounded search input
- Search icon on the left
- **Ctrl+K keyboard hint on desktop (hidden on mobile)**
- Character counter (shows when typing)
- Clear button (×) when there's text
- Pink glow effect when Ctrl+K is pressed
- Blue pulse animation while searching

### HTML Structure
```html
<!-- Enhanced Dynamic Search -->
<form method="GET" action="{{ url_for('your_route_name') }}" class="mb-4" id="dynamicSearchForm">
  <div class="input-icon position-relative">
    <span class="input-icon-addon">
      <i class="ti ti-search fs-3"></i>
    </span>
    <input type="text"
           name="q"
           id="enhancedSearchInput"
           class="form-control form-control-lg shadow-sm"
           placeholder="Start typing to search"
           value="{{ request.args.get('q', '') }}"
           style="padding-right: 100px; border-radius: 0.5rem;"
           autocomplete="off"
           data-bs-toggle="false">
    <div class="position-absolute end-0 top-50 translate-middle-y me-3 d-flex align-items-center gap-2">
      <small id="searchCharCounter" class="text-muted" style="font-size: 0.75rem; display: none;"></small>
      <!-- IMPORTANT: Keyboard hints hidden on mobile with d-none d-md-inline -->
      <kbd id="searchKbdHint" class="text-muted d-none d-md-inline">Ctrl</kbd>
      <kbd class="text-muted d-none d-md-inline">K</kbd>
      <button id="searchClearBtn" type="button" class="btn btn-link p-0 border-0" style="display: none; width: 24px; height: 24px;" aria-label="Clear search">
        <i class="ti ti-x" style="font-size: 18px; color: #6c757d;"></i>
      </button>
    </div>
  </div>
</form>
```

### Critical Details
- **Keyboard hints:** Use `d-none d-md-inline` to hide on mobile
- **Form control:** Must have `form-control-lg` for proper size
- **Border radius:** `border-radius: 0.5rem` for rounded corners
- **Padding right:** `padding-right: 100px` to make room for controls
- **IDs must match:** `enhancedSearchInput`, `searchCharCounter`, `searchKbdHint`, `searchClearBtn`

### JavaScript Requirements
- Must implement Ctrl+K keyboard shortcut
- Character counter updates as you type
- Clear button appears/disappears dynamically
- Pink glow effect on Ctrl+K press
- Blue pulse while AJAX search is running

---

## GitHub-Style Filter Component

### Visual Features
- Light gray background (#f6f8fa)
- Rounded container (6px border-radius)
- Buttons side-by-side with subtle dividers
- Active button: white background with border
- Inactive buttons: gray background
- Hover effect: darker gray
- Icons with labels and counts

### HTML Structure
```html
<!-- Main Table -->
<div id="your-filters" class="scroll-anchor"></div>
<div class="card main-table-card" style="margin-top: 1.5rem !important;">
  <div class="card-header">
    <div class="d-flex justify-content-center align-items-center w-100">
      <!-- Filter Buttons -->
      <div class="github-filter-group" role="group" aria-label="Filter buttons">
        <a href="#"
           onclick="filterYourData('active'); return false;"
           class="github-filter-btn active"
           id="filter-active">
          <i class="ti ti-activity"></i>Active <span class="filter-count">(26)</span>
        </a>
        <a href="#"
           onclick="filterYourData('unpaid'); return false;"
           class="github-filter-btn"
           id="filter-unpaid">
          <i class="ti ti-clock"></i>Unpaid <span class="filter-count">(4)</span>
        </a>
        <a href="#"
           onclick="filterYourData('all'); return false;"
           class="github-filter-btn"
           id="filter-all">
          <i class="ti ti-list"></i>All <span class="filter-count">(39)</span>
        </a>
      </div>
    </div>
  </div>
  <div class="table-responsive">
    <!-- Table goes here -->
  </div>
</div>
```

### Critical CSS Classes
- **Card:** Must have `main-table-card` class
- **Filter container:** `github-filter-group` class
- **Filter buttons:** `github-filter-btn` class
- **Active state:** Add `active` class to selected filter
- **Filter counts:** Wrap count in `<span class="filter-count">`

### Styling Rules
- All styling comes from `static/css/filter-component.css`
- DO NOT add inline styles to filter buttons
- Active button automatically gets white background
- Inactive buttons automatically get gray background
- Dividers between buttons handled by CSS

### JavaScript Pattern
```javascript
function filterYourData(filterType) {
  // Remove active class from all buttons
  document.querySelectorAll('.github-filter-btn').forEach(btn => {
    btn.classList.remove('active');
  });

  // Add active class to clicked button
  document.getElementById('filter-' + filterType).classList.add('active');

  // Filter logic here
  // ...
}
```

---

## Table Component

### Desktop vs Mobile Behavior

**Desktop (≥768px):**
- All columns visible
- User avatar on left
- Full user email shown
- Dropdown shows "Actions" text

**Mobile (<768px):**
- Columns hide using `d-none d-md-table-cell`
- User column shows only name
- Activity logo replaces user avatar
- Uses remaining column shows as single number
- Dropdown shows icon only

### HTML Structure
```html
<div class="table-responsive">
  <table class="table table-hover">
    <thead>
      <tr>
        <th>User</th>
        <!-- Mobile: Shows # column -->
        <th class="d-md-none text-center">#</th>
        <!-- Desktop columns (hidden on mobile) -->
        <th class="d-none d-md-table-cell">Activity</th>
        <th class="d-none d-lg-table-cell">Passport Type</th>
        <th class="d-none d-md-table-cell text-center">Amount</th>
        <th class="d-none d-lg-table-cell text-center">Status</th>
        <th class="d-none d-md-table-cell text-center">Uses Remaining</th>
        <th class="d-none d-md-table-cell">Created</th>
        <th class="text-center">Actions</th>
      </tr>
    </thead>
    <tbody>
      {% for item in items %}
      <tr>
        <!-- User Column: Always visible -->
        <td style="vertical-align: middle;">
          <div class="d-flex align-items-center">
            <!-- Desktop: User Gravatar -->
            <img src="..." class="rounded-circle me-3 user-avatar d-none d-md-block" alt="Avatar">
            <!-- Mobile: Activity Logo -->
            <img src="..." class="rounded-circle me-3 user-avatar d-md-none" alt="Activity">
            <div>
              <div class="fw-bold">{{ user.name }}</div>
              <!-- Email only on desktop -->
              <div class="text-muted small d-none d-md-block">{{ user.email }}</div>
            </div>
          </div>
        </td>

        <!-- Mobile: Uses/Count Column -->
        <td class="d-md-none text-center" style="vertical-align: middle;">
          <span class="fw-bold" style="color: #6c757d;">{{ count }}</span>
        </td>

        <!-- Desktop: Full Details -->
        <td class="d-none d-md-table-cell" style="vertical-align: middle;">...</td>

        <!-- Actions Column: Always visible -->
        <td class="text-center" style="vertical-align: middle;">
          <div class="dropdown d-inline-block">
            <a href="#" class="btn btn-outline-secondary dropdown-toggle" data-bs-toggle="dropdown">
              <!-- Desktop: Show text -->
              <span class="d-none d-md-inline">Actions</span>
              <!-- Mobile: Show icon -->
              <i class="ti ti-menu-2 d-md-none"></i>
            </a>
            <div class="dropdown-menu dropdown-menu-end">
              <!-- Dropdown items -->
            </div>
          </div>
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>
```

### Column Visibility Classes

| Class | Behavior |
|-------|----------|
| No class | Always visible |
| `d-none d-md-table-cell` | Hidden on mobile, visible on tablet+ |
| `d-none d-lg-table-cell` | Hidden until large screens |
| `d-md-none` | Visible only on mobile |

### Table Styling Rules
- **NO hover effects:** Per CLAUDE.md constraints
- **Plain white cards:** `background-color: #fff !important;`
- **Vertical align:** All cells use `style="vertical-align: middle;"`
- **Text alignment:** Center numerical data, left-align text

### Badge Styling
```html
<!-- Paid -->
<span class="badge bg-green-lt text-green-lt-fg">Paid</span>

<!-- Unpaid -->
<span class="badge bg-yellow-lt text-yellow-lt-fg">Unpaid</span>

<!-- Active -->
<span class="badge bg-blue-lt text-blue-lt-fg">Active</span>
```

---

## CSS Files to Include

### Required CSS Files (In Order)
```html
<!-- 1. Global Dropdown Fix -->
<link href="{{ url_for('static', filename='css/dropdown-fix.css') }}?v=4.0" rel="stylesheet">

<!-- 2. Search Component -->
<link href="{{ url_for('static', filename='css/search-component.css') }}?v=1.0" rel="stylesheet">

<!-- 3. Filter Component -->
<link href="{{ url_for('static', filename='css/filter-component.css') }}?v=1.0" rel="stylesheet">
```

### What Each File Does
- **dropdown-fix.css:** Fixes z-index issues with Bootstrap dropdowns in tables
- **search-component.css:** Pink glow, loading animations, search styling
- **filter-component.css:** GitHub-style filter buttons, active states

### Mobile Z-Index Fix
If you experience mobile menu layering issues, ensure this CSS is in `static/minipass.css`:

```css
@media (max-width: 991px) {
  .minipass-main {
    display: flex;
    flex-direction: column;
    height: 100vh;
    margin-left: 0;
    overflow: hidden;
    position: relative;
    z-index: 1;  /* Ensures content stays below mobile menu */
  }
}
```

---

## JavaScript Behavior

### Search Functionality

**Required Features:**
1. Ctrl+K keyboard shortcut to focus search
2. Pink glow effect on Ctrl+K press
3. Character counter (shows after 1 character)
4. Clear button (shows when text exists)
5. Blue pulse animation during AJAX search
6. Hide keyboard hints on mobile

**JavaScript Template:**
```javascript
document.addEventListener('DOMContentLoaded', function() {
  const searchInput = document.getElementById('enhancedSearchInput');
  const searchClearBtn = document.getElementById('searchClearBtn');
  const searchCharCounter = document.getElementById('searchCharCounter');
  const kbdHint = document.getElementById('searchKbdHint');

  // Ctrl+K shortcut
  document.addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      searchInput.focus();

      // Add pink glow effect
      searchInput.classList.add('search-glow-active');
      setTimeout(() => {
        searchInput.classList.remove('search-glow-active');
      }, 800);
    }
  });

  // Character counter
  searchInput.addEventListener('input', function() {
    const length = this.value.length;

    if (length > 0) {
      searchCharCounter.textContent = `${length} character${length !== 1 ? 's' : ''}`;
      searchCharCounter.style.display = 'inline';
      searchClearBtn.style.display = 'inline-flex';
      kbdHint.style.display = 'none';
    } else {
      searchCharCounter.style.display = 'none';
      searchClearBtn.style.display = 'none';
      // Only show kbd hint on desktop
      if (window.innerWidth >= 768) {
        kbdHint.style.display = 'inline';
      }
    }
  });

  // Clear button
  searchClearBtn.addEventListener('click', function() {
    searchInput.value = '';
    searchInput.dispatchEvent(new Event('input'));
    searchInput.focus();
  });

  // Hide kbd hints on mobile
  function updateKbdVisibility() {
    if (window.innerWidth < 768) {
      kbdHint.style.display = 'none';
    } else if (searchInput.value.length === 0) {
      kbdHint.style.display = 'inline';
    }
  }

  window.addEventListener('resize', updateKbdVisibility);
  updateKbdVisibility();
});
```

### Filter Functionality

```javascript
function filterPassports(filterType) {
  // Remove active from all
  document.querySelectorAll('.github-filter-btn').forEach(btn => {
    btn.classList.remove('active');
  });

  // Add active to clicked
  document.getElementById('filter-' + filterType).classList.add('active');

  // Get all table rows
  const rows = document.querySelectorAll('tbody tr');

  rows.forEach(row => {
    const isPaid = row.dataset.paid === 'true';
    const isActive = row.dataset.active === 'true';

    let show = false;
    if (filterType === 'all') {
      show = true;
    } else if (filterType === 'active') {
      show = isActive || !isPaid;
    } else if (filterType === 'unpaid') {
      show = !isPaid;
    }

    row.style.display = show ? '' : 'none';
  });

  // Update URL with filter parameter
  const url = new URL(window.location);
  url.searchParams.set('passport_filter', filterType);
  window.history.pushState({}, '', url);
}
```

---

## Mobile Responsiveness Rules

### Breakpoints
- **Mobile:** <768px
- **Tablet:** 768px - 991px
- **Desktop:** ≥992px

### Common Patterns

#### Show on Desktop Only
```html
<span class="d-none d-md-inline">Desktop Text</span>
```

#### Show on Mobile Only
```html
<i class="d-md-none ti ti-icon"></i>
```

#### Table Columns
```html
<!-- Desktop only column -->
<th class="d-none d-md-table-cell">Column</th>
<td class="d-none d-md-table-cell">Data</td>

<!-- Mobile only column -->
<th class="d-md-none">#</th>
<td class="d-md-none">123</td>
```

### Mobile Checklist
When implementing on mobile, verify:
- [ ] Keyboard hints (Ctrl+K) are hidden
- [ ] Table columns collapse correctly
- [ ] Actions dropdown shows icon instead of text
- [ ] User email is hidden
- [ ] Activity logo replaces user avatar
- [ ] GitHub filters remain centered
- [ ] Search input is properly sized (16px font to prevent zoom)

---

## Complete Page Template

### Full HTML Example
```html
{% extends "base.html" %}

{% block title %}Your Page Title{% endblock %}

{% block content %}
<!-- CSS Imports -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/dropdown-fix.css') }}?v=4.0">
<link rel="stylesheet" href="{{ url_for('static', filename='css/search-component.css') }}?v=1.0">
<link rel="stylesheet" href="{{ url_for('static', filename='css/filter-component.css') }}?v=1.0">

<div class="container-xl">
  <div class="row">
    <div class="col-12">

      <!-- Page Title -->
      <h2 class="mt-4 mb-3">
        <i class="ti ti-your-icon me-2" style="color: #206bc4;"></i>Your Page Title
      </h2>

      <!-- Enhanced Search -->
      <form method="GET" action="{{ url_for('your_route') }}" class="mb-4" id="dynamicSearchForm">
        <div class="input-icon position-relative">
          <span class="input-icon-addon">
            <i class="ti ti-search fs-3"></i>
          </span>
          <input type="text"
                 name="q"
                 id="enhancedSearchInput"
                 class="form-control form-control-lg shadow-sm"
                 placeholder="Start typing to search"
                 value="{{ request.args.get('q', '') }}"
                 style="padding-right: 100px; border-radius: 0.5rem;"
                 autocomplete="off"
                 data-bs-toggle="false">
          <div class="position-absolute end-0 top-50 translate-middle-y me-3 d-flex align-items-center gap-2">
            <small id="searchCharCounter" class="text-muted" style="font-size: 0.75rem; display: none;"></small>
            <kbd id="searchKbdHint" class="text-muted d-none d-md-inline">Ctrl</kbd>
            <kbd class="text-muted d-none d-md-inline">K</kbd>
            <button id="searchClearBtn" type="button" class="btn btn-link p-0 border-0" style="display: none; width: 24px; height: 24px;">
              <i class="ti ti-x" style="font-size: 18px; color: #6c757d;"></i>
            </button>
          </div>
        </div>
      </form>

      <!-- Table with Filters -->
      <div id="your-filters" class="scroll-anchor"></div>
      <div class="card main-table-card" style="margin-top: 1.5rem !important;">
        <div class="card-header">
          <div class="d-flex justify-content-center align-items-center w-100">
            <div class="github-filter-group" role="group" aria-label="Filter buttons">
              <a href="#" onclick="filterData('active'); return false;" class="github-filter-btn active" id="filter-active">
                <i class="ti ti-activity"></i>Active <span class="filter-count">({{ active_count }})</span>
              </a>
              <a href="#" onclick="filterData('all'); return false;" class="github-filter-btn" id="filter-all">
                <i class="ti ti-list"></i>All <span class="filter-count">({{ total_count }})</span>
              </a>
            </div>
          </div>
        </div>
        <div class="table-responsive">
          <table class="table table-hover">
            <thead>
              <tr>
                <th>User</th>
                <th class="d-none d-md-table-cell">Details</th>
                <th class="text-center">Actions</th>
              </tr>
            </thead>
            <tbody>
              {% for item in items %}
              <tr>
                <td style="vertical-align: middle;">
                  <div class="d-flex align-items-center">
                    <img src="..." class="rounded-circle me-3 d-none d-md-block" alt="Avatar">
                    <div>
                      <div class="fw-bold">{{ item.name }}</div>
                      <div class="text-muted small d-none d-md-block">{{ item.email }}</div>
                    </div>
                  </div>
                </td>
                <td class="d-none d-md-table-cell" style="vertical-align: middle;">
                  {{ item.details }}
                </td>
                <td class="text-center" style="vertical-align: middle;">
                  <div class="dropdown">
                    <a href="#" class="btn btn-outline-secondary dropdown-toggle" data-bs-toggle="dropdown">
                      <span class="d-none d-md-inline">Actions</span>
                      <i class="ti ti-menu-2 d-md-none"></i>
                    </a>
                    <div class="dropdown-menu dropdown-menu-end">
                      <a href="#" class="dropdown-item">Edit</a>
                      <a href="#" class="dropdown-item text-danger">Delete</a>
                    </div>
                  </div>
                </td>
              </tr>
              {% endfor %}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  </div>
</div>

<script>
// Copy JavaScript from "JavaScript Behavior" section above
// Include: Ctrl+K shortcut, character counter, clear button, filter function
</script>

{% endblock %}
```

---

## Checklist for New Pages

When implementing this design on a new page, verify:

### HTML Structure
- [ ] Page title with icon (remove "Your" prefix)
- [ ] Search bar with all components (icon, input, Ctrl+K hints, counter, clear button)
- [ ] GitHub filter group with active state
- [ ] Table with proper responsive classes
- [ ] Actions dropdown with text/icon toggle

### CSS Includes
- [ ] dropdown-fix.css loaded
- [ ] search-component.css loaded
- [ ] filter-component.css loaded
- [ ] No custom styles that override component CSS

### JavaScript
- [ ] Ctrl+K keyboard shortcut working
- [ ] Pink glow effect on Ctrl+K
- [ ] Character counter updates
- [ ] Clear button shows/hides
- [ ] Keyboard hints hide on mobile
- [ ] Filter buttons toggle active class
- [ ] Filter function updates table visibility

### Mobile Testing
- [ ] Test on 375px width (iPhone SE size)
- [ ] Ctrl+K hints hidden
- [ ] Table columns hide/show correctly
- [ ] Actions show icon only
- [ ] Search input doesn't cause zoom (16px font)
- [ ] GitHub filters stay centered
- [ ] Mobile menu doesn't show content through it

### Desktop Testing
- [ ] Test on 1920px width
- [ ] All table columns visible
- [ ] Ctrl+K shortcut works
- [ ] Hover states working on filters
- [ ] Dropdowns positioned correctly

---

## Common Mistakes to Avoid

### ❌ DON'T
- Add custom CSS that overrides component styles
- Use different class names for similar components
- Add hover effects to tables
- Use gradients on white cards
- Forget to hide Ctrl+K hints on mobile
- Mix different table responsive patterns
- Add inline styles to filter buttons

### ✅ DO
- Use the exact HTML structure from this document
- Copy-paste component code blocks
- Test on mobile (375px) and desktop (1920px)
- Use the same CSS classes across all pages
- Keep keyboard hints hidden on mobile with `d-none d-md-inline`
- Follow the vertical-align: middle pattern for all table cells
- Reference activity_dashboard.html when in doubt

---

## Getting Help

### If Something Doesn't Work
1. Compare your code to `templates/activity_dashboard.html` (lines 1071-1220)
2. Check that all three CSS files are loaded in the correct order
3. Verify IDs match exactly (`enhancedSearchInput`, `searchKbdHint`, etc.)
4. Test JavaScript in browser console for errors
5. Check mobile view at 375px width

### Claude Code Sessions
When starting a new Claude Code session to convert a page:
1. Have Claude read this document first: `docs/DESIGN_SYSTEM.md`
2. Point Claude to the reference page: `templates/activity_dashboard.html`
3. Specify which page to convert
4. Claude will have all context needed to implement correctly

---

## Version History

**v1.0 - October 27, 2025**
- Initial design system documentation
- Based on Activity Dashboard and Passports pages
- Includes search, filters, and table components
- Mobile responsiveness patterns documented
- Complete code examples provided

---

**This document is the single source of truth for UI consistency across Minipass. When in doubt, refer to the reference pages and this guide.**
