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

## Backend Data Requirements

**CRITICAL:** The backend must pass specific data structures to the template for filter counts to work correctly.

### Required: `statistics` Dictionary

The backend route MUST calculate and pass a `statistics` dict containing TOTAL counts from the database (NOT filtered page results).

```python
# Example from list_passports() in app.py (lines 3728-3743)
# Query ALL items from database first
all_passports = Passport.query.all()
all_passports_count = Passport.query.count()

# Calculate statistics using ALL items (not filtered results)
paid_passports = len([p for p in all_passports if p.paid])
unpaid_passports = len([p for p in all_passports if not p.paid])
active_passports = len([p for p in all_passports if p.uses_remaining > 0 or not p.paid])

# Create statistics dict
statistics = {
    'total_passports': all_passports_count,
    'paid_passports': paid_passports,
    'unpaid_passports': unpaid_passports,
    'active_passports': active_passports,
}

# Pass to template
return render_template("passports.html",
                     passports=filtered_passports,  # Filtered results for display
                     statistics=statistics,          # Total counts for filter buttons
                     current_filters={...})
```

### For Activities Page:

```python
# Example structure for activities
all_activities = Activity.query.all()

statistics = {
    'total_activities': len(all_activities),
    'active_activities': len([a for a in all_activities if a.status == 'active']),
    'inactive_activities': len([a for a in all_activities if a.status == 'inactive']),
    'draft_activities': len([a for a in all_activities if a.status == 'draft'])
}
```

### Why This Matters:

**WRONG:** Using filtered page results for counts
```jinja
<!-- This will show different counts depending on current filter - WRONG! -->
<span>({{ activities|selectattr('status', 'equalto', 'active')|list|length }})</span>
```

**CORRECT:** Using backend statistics
```jinja
<!-- This always shows total count from database - CORRECT! -->
<span>({{ statistics.active_activities }})</span>
```

### Required: `current_filters` Dictionary

Must pass current filter state to template:

```python
current_filters = {
    'q': search_query,           # Search term
    'status': status_filter,     # Current status filter
    'show_all': show_all_param   # Whether "All" is selected
}
```

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

### EXACT HTML Structure from Passports Page

**IMPORTANT:** Use this EXACT HTML including all inline styles. Do NOT simplify or use CSS classes alone.

```html
<!-- Main Table -->
<div class="card main-table-card" style="margin-top: 1.5rem !important;">
  <div class="card-header">
    <div class="d-flex justify-content-center align-items-center w-100">
      <!-- Filter Buttons -->
      <div class="github-filter-group" role="group" aria-label="Filter buttons" style="display: inline-flex; align-items: center; background: #f6f8fa; border: 1px solid #d1d5da; border-radius: 6px; padding: 0;">
        <a href="{{ url_for('list_passports', status='active') }}"
           class="github-filter-btn {% if current_filters.status == 'active' and not current_filters.show_all %}active{% endif %}"
           style="{% if current_filters.status == 'active' and not current_filters.show_all %}background: #ffffff; color: #24292e; font-weight: 600; border: 1px solid #d1d5da; margin: -1px; z-index: 1; border-radius: 6px; box-shadow: 0 1px 0 rgba(27,31,35,0.04);{% else %}background: rgba(0, 0, 0, 0.03); color: #586069; margin: 0; border-right: 1px solid transparent; background-clip: padding-box; background-image: linear-gradient(to right, transparent 0%, transparent 100%), linear-gradient(180deg, transparent 20%, #d1d5da 20%, #d1d5da 80%, transparent 80%); background-size: 100% 100%, 1px 100%; background-position: center, right center; background-repeat: no-repeat;{% endif %} padding: 5px 12px; font-size: 14px; line-height: 20px; text-decoration: none; display: inline-flex; align-items: center; white-space: nowrap; position: relative;">
          <i class="ti ti-activity" style="font-size: 16px; margin-right: 4px;"></i>Active <span style="opacity: 0.6; margin-left: 4px;">({{ statistics.active_passports|default(0) }})</span>
        </a>
        <a href="{{ url_for('list_passports', payment_status='unpaid') }}"
           class="github-filter-btn {% if current_filters.payment_status == 'unpaid' %}active{% endif %}"
           style="{% if current_filters.payment_status == 'unpaid' %}background: #ffffff; color: #24292e; font-weight: 600; border: 1px solid #d1d5da; margin: -1px; z-index: 1; border-radius: 6px; box-shadow: 0 1px 0 rgba(27,31,35,0.04);{% else %}background: rgba(0, 0, 0, 0.03); color: #586069; margin: 0; border-right: 1px solid transparent; background-clip: padding-box; background-image: linear-gradient(to right, transparent 0%, transparent 100%), linear-gradient(180deg, transparent 20%, #d1d5da 20%, #d1d5da 80%, transparent 80%); background-size: 100% 100%, 1px 100%; background-position: center, right center; background-repeat: no-repeat;{% endif %} padding: 5px 12px; font-size: 14px; line-height: 20px; text-decoration: none; display: inline-flex; align-items: center; white-space: nowrap; position: relative;">
          <i class="ti ti-clock" style="font-size: 16px; margin-right: 4px;"></i>Unpaid <span style="opacity: 0.6; margin-left: 4px;">({{ statistics.unpaid_passports|default(0) }})</span>
        </a>
        <a href="{{ url_for('list_passports', show_all='true') }}"
           class="github-filter-btn {% if current_filters.show_all %}active{% endif %}"
           style="{% if current_filters.show_all %}background: #ffffff; color: #24292e; font-weight: 600; border: 1px solid #d1d5da; margin: -1px; z-index: 1; border-radius: 6px; box-shadow: 0 1px 0 rgba(27,31,35,0.04);{% else %}background: rgba(0, 0, 0, 0.03); color: #586069; margin: 0; border-right: 1px solid transparent; background-clip: padding-box; background-image: linear-gradient(to right, transparent 0%, transparent 100%), linear-gradient(180deg, transparent 20%, #d1d5da 20%, #d1d5da 80%, transparent 80%); background-size: 100% 100%, 1px 100%; background-position: center, right center; background-repeat: no-repeat;{% endif %} padding: 5px 12px; font-size: 14px; line-height: 20px; text-decoration: none; display: inline-flex; align-items: center; white-space: nowrap; position: relative;">
          <i class="ti ti-list" style="font-size: 16px; margin-right: 4px;"></i>All <span style="opacity: 0.6; margin-left: 4px;">({{ statistics.total_passports|default(0) }})</span>
        </a>
      </div>
    </div>
  </div>
  <div class="table-responsive">
    <!-- Table goes here -->
  </div>
</div>
```

### Filter Active State Logic

**CRITICAL:** The conditional logic determines which filter has the white background (active state).

#### Pattern for Each Filter:

**First Filter (Active):**
```jinja
{% if current_filters.status == 'active' and not current_filters.show_all %}active{% endif %}
```
- Active when `status='active'` parameter AND NOT showing all
- This is usually the default when no parameters are set

**Second Filter (by category, e.g., Unpaid):**
```jinja
{% if current_filters.payment_status == 'unpaid' %}active{% endif %}
```
- Active when specific parameter is set

**Third Filter (All):**
```jinja
{% if current_filters.show_all %}active{% endif %}
```
- Active when `show_all='true'` parameter is set
- Links to base URL with `show_all='true'`

#### Common Mistake:
**WRONG:** Setting "All" active when there's no status
```jinja
{% if not current_filters.status %}active{% endif %}  <!-- This makes All and Active both active! -->
```

**CORRECT:** Using explicit `show_all` parameter
```jinja
{% if current_filters.show_all %}active{% endif %}
```

---

### ⚠️ CRITICAL WARNING: DO NOT MODIFY CONDITIONAL LOGIC

**This is where bugs happen. Read this carefully.**

#### Common Mistake That Causes Bugs

Developers often try to "simplify" or "improve" the filter conditionals by using logic like:

```jinja
<!-- WRONG - DON'T DO THIS -->
{% if current_filters.status == 'active' or not current_filters.status %}active{% endif %}
```

This seems logical at first: "show Active if status is 'active' OR if no status is set".

**BUT IT CREATES A CRITICAL BUG:**

1. When user clicks "All", the URL is `/activities?show_all=true`
2. This means `current_filters.status` is empty/None (no status parameter)
3. So BOTH "Active" (because of `not current_filters.status` being true) AND "All" (because of `show_all=true`) will have white backgrounds simultaneously!

#### Why The Design System Pattern Works

The passport page backend (app.py lines 3673-3674) sets a DEFAULT status:

```python
if not status and not payment_status and show_all_param != "true":
    status = "active"
```

This means:
- When you load `/activities` with NO parameters, backend sets `status='active'` automatically
- When you load `/activities?show_all=true`, backend does NOT set a default (show_all is true)
- So you DON'T need `or not current_filters.status` logic in the template

**THE RULE:**

✅ **DO:** Copy the exact conditionals from the design system
❌ **DON'T:** Try to simplify or improve them
❌ **DON'T:** Use `or not current_filters.status` logic
❌ **DON'T:** Think you know better than the pattern

**When in doubt:** Copy-paste from `templates/passports.html` directly.

---

### Filter Count Source

**CRITICAL:** Counts MUST come from `statistics` dict passed by backend.

```jinja
<!-- CORRECT - uses backend statistics -->
<span style="opacity: 0.6; margin-left: 4px;">({{ statistics.active_passports|default(0) }})</span>

<!-- WRONG - uses filtered page results -->
<span>({{ passports|selectattr('paid', 'equalto', true)|list|length }})</span>
```

### Styling Rules
- **DO NOT** simplify the inline styles - copy them exactly
- All the complex inline styles are REQUIRED for proper GitHub appearance
- Active button styling comes from the conditional inline styles
- Inactive buttons use the gradient divider technique in inline styles

---

## Search Component JavaScript Requirements

### Complete Implementation

The search component requires JavaScript for these features:
1. **Ctrl+K keyboard shortcut** to focus search
2. **Character counter** showing typed characters
3. **Clear (X) button** visibility logic
4. **Auto-search debounce** (500ms delay after typing stops)
5. **Mobile keyboard hint hiding** when focused

### Full JavaScript Code (from passports.html lines 324-361)

```javascript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize search component
    if (window.SearchComponent) {
        window.SearchComponent.init({
            formId: 'dynamicSearchForm',
            inputId: 'enhancedSearchInput',
            preserveParams: ['payment_status', 'status'] // Adjust based on your page
        });
    }

    // Initialize filter component
    if (window.FilterComponent) {
        window.FilterComponent.init({
            filterClass: 'github-filter-btn',
            mode: 'server',
            preserveScrollPosition: true,
            enableSearchPreservation: true
        });
    }

    // Validation for debugging
    console.log('🎫 Page loaded');
    console.log('🔧 Global dropdown fix available:', typeof window.dropdownFix !== 'undefined');
    console.log('📊 Bootstrap available:', typeof bootstrap !== 'undefined');
    console.log('🔍 Dropdown toggles found:', document.querySelectorAll('[data-bs-toggle="dropdown"]').length);

    // Debug: Check if Bootstrap is properly loaded
    if (typeof bootstrap === 'undefined') {
        console.error('Bootstrap is not loaded! Dropdown functionality may not work.');
    } else {
        console.log('Bootstrap is loaded. Dropdown functionality should work.');
    }
});
```

### Search Component Features Breakdown

**SearchComponent.init()** handles:
- **Ctrl+K shortcut**: Focuses search input when Ctrl+K is pressed
- **Character counter**: Shows "X chars" in gray text while typing
- **Clear button**: Shows when length > 0, hides when empty
- **Auto-search**: Submits form 500ms after typing stops (if length >= 3 or === 0)
- **Keyboard hint hiding**: Hides "Ctrl K" badges when focused

**FilterComponent.init()** handles:
- **Server-side filtering**: Links submit to backend routes
- **Scroll position preservation**: Maintains scroll after filter change
- **Search preservation**: Keeps search query when switching filters

### Required HTML Elements

For the JavaScript to work, your search HTML must have these IDs:

```html
<form method="GET" action="{{ url_for('your_list_route') }}" class="mb-4" id="dynamicSearchForm">
  <div class="input-icon position-relative">
    <span class="input-icon-addon">
      <i class="ti ti-search fs-3"></i>
    </span>
    <input type="text"
           name="q"
           id="enhancedSearchInput"
           class="form-control form-control-lg shadow-sm"
           placeholder="Start typing to search"
           value="{{ current_filters.q or '' }}"
           style="padding-right: 100px; border-radius: 0.5rem;"
           autocomplete="off"
           data-bs-toggle="false">
    <div class="position-absolute end-0 top-50 translate-middle-y me-3 d-flex align-items-center gap-2">
      <small id="searchCharCounter" class="text-muted" style="font-size: 0.75rem; display: none;"></small>
      <kbd id="searchKbdHint" class="text-muted d-none d-md-inline">Ctrl</kbd>
      <kbd class="text-muted d-none d-md-inline">K</kbd>
      <button id="searchClearBtn" type="button" class="btn btn-link p-0 border-0" style="display: none; width: 24px; height: 24px;" aria-label="Clear search">
        <i class="ti ti-x" style="font-size: 18px; color: #6c757d;"></i>
      </button>
    </div>
  </div>
</form>
```

### Critical IDs Required:
- `id="dynamicSearchForm"` - Form element for auto-submission
- `id="enhancedSearchInput"` - Input field for all event listeners
- `id="searchCharCounter"` - Character counter display
- `id="searchKbdHint"` - Keyboard hint (first kbd element)
- `id="searchClearBtn"` - Clear button that appears when typing

### Required CSS Files:
```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/search-component.css') }}?v=1.0">
```

This CSS file contains the SearchComponent global object and all related styles.

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

## Avatar Styling Rules

### User Avatars vs Activity Avatars

**CRITICAL DISTINCTION:**
- **User avatars**: Always circular (`rounded-circle`)
- **Activity avatars**: Always square with rounded corners (`rounded`)

This distinction helps users instantly understand the visual hierarchy:
- **Circular = Person** (user identity)
- **Square = Brand** (activity/organization identity)

### Desktop View (≥768px)
- Show user gravatar avatars
- Always use `rounded-circle` class
- Standard size: 40px × 40px

### Mobile View (<768px)
- Show activity logo/image instead of user avatar
- Always use `rounded` class (NOT `rounded-circle`)
- Standard size: 30px × 30px
- Use `object-fit: cover` to maintain aspect ratio

### HTML Pattern for Tables

```html
<td style="vertical-align: middle;">
  <div class="d-flex align-items-center">
    <!-- Desktop: User Gravatar (circular) -->
    <img src="https://www.gravatar.com/avatar/..."
         class="rounded-circle me-3 user-avatar d-none d-md-block"
         alt="Avatar">

    <!-- Mobile: Activity Logo (square with rounded corners) -->
    {% if activity.logo_filename %}
      <img src="{{ url_for('static', filename='uploads/activity_images/' + activity.logo_filename) }}"
           class="rounded me-3 user-avatar d-md-none"
           alt="{{ activity.name }}"
           style="width: 30px; height: 30px; object-fit: cover;">
    {% else %}
      <!-- Fallback: Activity initial in square container -->
      <div class="rounded me-3 d-md-none bg-light d-flex align-items-center justify-content-center"
           style="width: 30px; height: 30px; font-size: 10px; color: #6c757d;">
        {{ activity.name[0] if activity and activity.name else 'A' }}
      </div>
    {% endif %}

    <div>
      <div class="fw-bold">{{ user.name }}</div>
      <div class="text-muted small d-none d-md-block">{{ user.email }}</div>
    </div>
  </div>
</td>
```

### Why This Matters

1. **Universal Standards**: Circular avatars are the web standard for people, square logos are standard for brands
2. **Instant Recognition**: Users can immediately distinguish personal vs organizational context
3. **Visual Consistency**: Matches the passport card design where activity logos are square
4. **Design System Coherence**: Maintains consistency with other Minipass UI elements

### Reference Implementation

See `templates/passports.html` (lines 100-111) and `templates/signups.html` (lines 91-102) for complete working examples.

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

## Common Implementation Errors

### Error 1: Filter Counts Are Dynamic (Change When Clicking)

**Symptom**: Filter counts show "0" after clicking a filter button

**Wrong Implementation**:
```html
<!-- WRONG: Filters current page results -->
<span>({{ activities|selectattr('status', 'equalto', 'active')|list|length }})</span>
```

**Root Cause**: Using Jinja filters on the page's filtered results instead of backend statistics

**Correct Implementation**:
```html
<!-- CORRECT: Uses statistics from backend -->
<span>({{ statistics.active_activities|default(0) }})</span>
```

**Fix Checklist**:
1. ✅ Backend queries ALL records before filtering
2. ✅ Backend calculates statistics dict from ALL records
3. ✅ Backend passes both `filtered_items` and `statistics` to template
4. ✅ Template uses `statistics.xxx` for filter counts
5. ✅ Template uses `filtered_items` for table display

---

### Error 2: "All" Filter Never Gets Active State

**Symptom**: Clicking "All" doesn't show it as active (no white background)

**Wrong Implementation**:
```html
<!-- WRONG: show_all parameter not set in link -->
<a href="{{ url_for('list_items') }}"
   class="github-filter-btn {% if current_filters.show_all %}active{% endif %}">
```

**Root Cause**: The conditional checks for `current_filters.show_all` but the link doesn't set this parameter

**Correct Implementation - Option 1** (Add parameter to link):
```html
<a href="{{ url_for('list_items', show_all='true') }}"
   class="github-filter-btn {% if current_filters.show_all %}active{% endif %}">
```

**Correct Implementation - Option 2** (Change conditional logic):
```html
<a href="{{ url_for('list_items') }}"
   class="github-filter-btn {% if not current_filters.status and not current_filters.payment_status %}active{% endif %}">
```

**Choose Option 1** if you want explicit `show_all='true'` in URL
**Choose Option 2** if you want clean URL like `/activities` when showing all

---

### Error 3: Clear (X) Button Not Appearing

**Symptom**: Typing in search doesn't show the clear button

**Root Cause**: Missing or incorrect JavaScript initialization

**Debug Checklist**:
1. ✅ Check `search-component.css` is loaded
2. ✅ Verify `window.SearchComponent` exists (check browser console)
3. ✅ Confirm `SearchComponent.init()` is called on DOMContentLoaded
4. ✅ Check element ID is exactly `searchClearBtn`
5. ✅ Verify button has `style="display: none;"` initially
6. ✅ Test in browser console: `document.getElementById('searchClearBtn')`

**Quick Test**:
```javascript
// In browser console:
console.log(typeof window.SearchComponent); // Should show "object" not "undefined"
console.log(document.getElementById('searchClearBtn')); // Should show button element
```

**Fix**: Ensure this CSS file is loaded BEFORE your page's `<script>` section:
```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/search-component.css') }}?v=1.0">
```

---

### Error 4: GitHub Filter Buttons Have Black Borders

**Symptom**: Filter buttons show ugly black borders instead of GitHub-style subtle dividers

**Wrong Implementation**:
```html
<!-- WRONG: Simplified classes without inline styles -->
<a href="..." class="github-filter-btn">Active</a>
```

**Correct Implementation**:
```html
<!-- CORRECT: Full inline styles from passport page -->
<a href="{{ url_for('list_items', status='active') }}"
   class="github-filter-btn {% if current_filters.status == 'active' %}active{% endif %}"
   style="{% if current_filters.status == 'active' %}background: #ffffff; color: #24292e; font-weight: 600; border: 1px solid #d1d5da; margin: -1px; z-index: 1; border-radius: 6px; box-shadow: 0 1px 0 rgba(27,31,35,0.04);{% else %}background: rgba(0, 0, 0, 0.03); color: #586069; margin: 0; border-right: 1px solid transparent; background-clip: padding-box; background-image: linear-gradient(to right, transparent 0%, transparent 100%), linear-gradient(180deg, transparent 20%, #d1d5da 20%, #d1d5da 80%, transparent 80%); background-size: 100% 100%, 1px 100%; background-position: center, right center; background-repeat: no-repeat;{% endif %} padding: 5px 12px; font-size: 14px; line-height: 20px; text-decoration: none; display: inline-flex; align-items: center; white-space: nowrap; position: relative;">
  <i class="ti ti-activity" style="font-size: 16px; margin-right: 4px;"></i>Active <span style="opacity: 0.6; margin-left: 4px;">({{ statistics.active_items }})</span>
</a>
```

**Key Point**: The inline styles are NOT optional - they create the GitHub appearance

---

### Error 5: Search Requires Pressing Enter

**Symptom**: Typing doesn't trigger search automatically

**Root Cause**: Auto-search logic not implemented or debounce not working

**Fix**: Ensure `SearchComponent.init()` is called with correct parameters:
```javascript
if (window.SearchComponent) {
    window.SearchComponent.init({
        formId: 'dynamicSearchForm',
        inputId: 'enhancedSearchInput',
        preserveParams: ['status', 'payment_status'] // Adjust to your filters
    });
}
```

The `SearchComponent` handles auto-search with 500ms debounce automatically.

---

### Error 6: Mobile "#" Column Makes Avatars Too Narrow

**Symptom**: On mobile, user avatars are squeezed

**Root Cause**: Having a mobile-only column that wasn't in the original design

**Fix**: Remove the mobile "#" column if it's not essential:
```html
<!-- REMOVE THIS: -->
<th class="d-md-none text-center">#</th>

<!-- AND REMOVE CORRESPONDING DATA CELL: -->
<td class="d-md-none text-center" style="vertical-align: middle;">
  <span class="fw-bold" style="color: #6c757d;">{{ count }}</span>
</td>
```

**Note**: The passport page does have this column and it works. Only remove if it's causing layout issues on your specific page.

---

## Verification Checklist

Use this checklist when implementing or reviewing a page conversion:

### Backend Requirements ✅
- [ ] Route queries ALL records before applying filters
- [ ] Statistics dict calculated from ALL records (not filtered results)
- [ ] Both `statistics` and `filtered_items` passed to template
- [ ] `current_filters` dict passed with all active filter states

**Example Backend Code**:
```python
# 1. Query ALL records first
all_items = YourModel.query.all()
all_items_count = YourModel.query.count()

# 2. Calculate statistics from ALL
active_items = len([i for i in all_items if i.status == 'active'])
inactive_items = len([i for i in all_items if i.status == 'inactive'])

statistics = {
    'total_items': all_items_count,
    'active_items': active_items,
    'inactive_items': inactive_items,
}

# 3. Apply filters for display
query = YourModel.query
if status_filter:
    query = query.filter_by(status=status_filter)
filtered_items = query.all()

# 4. Pass both to template
return render_template('your_page.html',
                     items=filtered_items,
                     statistics=statistics,
                     current_filters={'status': status_filter, ...})
```

### Frontend HTML Requirements ✅
- [ ] CSS files loaded in correct order (dropdown-fix, search-component, filter-component)
- [ ] Search form has `id="dynamicSearchForm"`
- [ ] Search input has `id="enhancedSearchInput"`
- [ ] Clear button has `id="searchClearBtn"` and `style="display: none;"`
- [ ] Keyboard hints have `d-none d-md-inline` classes
- [ ] Filter buttons use FULL inline styles from passport (not simplified)
- [ ] Filter counts use `{{ statistics.xxx }}` not Jinja filters
- [ ] Filter active state conditionals match link parameters
- [ ] Table uses responsive classes (`d-none d-md-table-cell`, etc.)
- [ ] Mobile view tested at 375px width

### JavaScript Requirements ✅
- [ ] `SearchComponent.init()` called with correct IDs
- [ ] `FilterComponent.init()` called with correct class
- [ ] `preserveParams` array includes all your filter parameters
- [ ] Console logs show no errors
- [ ] Ctrl+K shortcut focuses search
- [ ] Character counter appears when typing
- [ ] Clear button appears when typing
- [ ] Auto-search triggers after 500ms
- [ ] Search submits with 3+ characters or 0 characters

### Behavioral Testing ✅
- [ ] **Filter counts remain static** when clicking different filters
- [ ] **"All" filter shows active state** when clicked
- [ ] **Clear button appears** when typing in search
- [ ] **Auto-search works** without pressing Enter (500ms delay)
- [ ] **Keyboard shortcut Ctrl+K** focuses search
- [ ] **Mobile keyboard hints hide** when focused
- [ ] **Mobile view** shows correct columns at 375px width
- [ ] **Desktop view** shows all columns at 1920px width
- [ ] **Filter buttons** have GitHub-style appearance (no black borders)
- [ ] **Search preserves** active filter when typing

### Cross-Reference Testing ✅
- [ ] Compare behavior to `templates/passports.html`
- [ ] Filter counts match behavior in passport page
- [ ] Search behavior matches passport page
- [ ] Filter button styling matches passport page
- [ ] Mobile layout matches passport page

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
