# Activity Header Simplification Plan

**Date:** 2025-09-03  
**Status:** Ready for Implementation  
**Flask Server:** localhost:5000 (Always running)  
**Test Credentials:** Admin login required for testing

## Executive Summary
Simplify and improve the activity header design for better mobile experience while maintaining all current functionality. Focus on reducing height, better integrating the activity picture (not logo), simplifying the revenue progress display, and implementing a dropdown menu for mobile actions.

## Important Clarification
- **Activity Picture** != Logo
- The image shown is the **activity's associated picture** (e.g., hockey team logo)
- This is NOT the platform logo (Fondation LHGI)
- Must integrate the **activity picture** better into the header flow

## Goals
1. Reduce header height by 40% on desktop, 70% on mobile
2. Better integrate **activity picture** into the header layout
3. Simplify revenue progress display (remove percentage and target)
4. Implement dropdown menu for mobile actions (reduce button clutter)
5. Improve mobile responsiveness to fit on single screen
6. Maintain all current functionality

## Design Specifications

### Desktop Layout (Keep All Buttons Visible)
```
┌─────────────────────────────────────────────────────────┐
│ [Activity Pic 30px]  Hockey du midi LHGI - 2025/2026  [Avatar]│
│                      Parties de la LHGI les Lundis...         │
│                                                               │
│ 👥 19 users  ⭐ 4.8  📍 Location  📋 2 types                 │
│                                                               │
│ Revenue Progress ████████░░░░░░░░  $419                      │
│                                                               │
│ [Edit] [Email] [Delete] [Scan] [Passport]  [QR Code]         │
└─────────────────────────────────────────────────────────┘
Height: ~180px
```

### Mobile Layout (With Dropdown Menu)
```
┌─────────────────────────┐
│ ☰  [Pic] LHGI    [⋮]    │
│ Hockey du midi          │
│ 2025/2026              │
│                        │
│ 👥19 ⭐4.8 📍 📋2      │
│                        │
│ Revenue Progress       │
│ ████████░░░░  $419     │
└────────────────────────┘
Height: ~200px

Dropdown Menu (⋮):
┌──────────────┐
│ ✏️ Edit      │
│ 📧 Email     │
│ 🗑️ Delete    │
│ 📷 Scan      │
│ 🎫 Passport  │
│ ▣ QR Code   │
└──────────────┘
```

## Agent Assignments & Testing Requirements

### Task 1: Analyze Current Implementation
**Agent:** backend-architect  
**Responsibilities:**
- Review current header implementation
- Analyze revenue calculation logic
- Document current button actions and dependencies
- Check for mobile/desktop conditionals

**Files to Review:**
- `templates/activity_detail.html`
- `utils.py` (get_kpi_data function)
- `static/css/custom.css`
- Check for any activity header components

**Testing Instructions:**
1. Login to Flask server at localhost:5000 with admin credentials
2. Navigate to activity detail page
3. Document all current functionality
4. Take baseline screenshots

**Unit Tests to Create:**
- `test/test_activity_header_revenue.py`
  - Test revenue progress calculation accuracy
  - Test with various revenue amounts
  - Test edge cases (0 revenue, exceeding target)

**Playwright Screenshots:**
- `/home/kdresdell/Pictures/Screenshots/test_activity_header_before_desktop.png`
- `/home/kdresdell/Pictures/Screenshots/test_activity_header_before_mobile.png`

### Task 2: Simplify Revenue Progress Component
**Agent:** flask-ui-developer  
**Responsibilities:**
- Modify revenue progress display
- Remove percentage text
- Remove target amount text
- Keep only progress bar and current amount

**Changes Required:**
- Remove "42.0% Complete" text
- Remove "$1,000 target" text
- Keep progress bar visualization
- Keep "$419" current amount display

**Testing Instructions:**
1. Login to localhost:5000 with admin credentials
2. Navigate to activity detail page
3. Verify revenue shows only amount and bar
4. Test with different revenue values

**Unit Tests:**
- `test/test_revenue_display.py`
  - Verify only amount is displayed
  - Verify progress bar calculation remains correct
  - Test formatting of currency

**Playwright Testing:**
- Screenshot: `/home/kdresdell/Pictures/Screenshots/test_revenue_simplified.png`
- Verify across multiple activities with different revenue levels

### Task 3: Implement Dropdown Menu Component
**Agent:** ui-designer  
**Responsibilities:**
- Design dropdown menu component using Tabler.io
- Create responsive behavior (mobile-only dropdown)
- Ensure accessibility standards
- Maintain all action functionality

**Specifications:**
- Use Tabler.io dropdown component
- Three-dots icon (⋮) for trigger
- Mobile breakpoint: < 768px
- Desktop: show all buttons
- Mobile: show only dropdown

**Implementation Details:**
```html
<!-- Mobile Only (CSS hidden on desktop) -->
<div class="dropdown d-md-none">
  <button class="btn btn-icon" data-bs-toggle="dropdown">
    <svg><!-- three dots icon --></svg>
  </button>
  <div class="dropdown-menu">
    <a class="dropdown-item" href="#edit">✏️ Edit</a>
    <a class="dropdown-item" href="#email">📧 Email Templates</a>
    <a class="dropdown-item" href="#delete">🗑️ Delete</a>
    <a class="dropdown-item" href="#scan">📷 Scan</a>
    <a class="dropdown-item" href="#passport">🎫 Passport</a>
    <a class="dropdown-item" href="#qr">▣ QR Code</a>
  </div>
</div>

<!-- Desktop Only (CSS hidden on mobile) -->
<div class="btn-group d-none d-md-flex">
  <!-- Original buttons -->
</div>
```

**Testing Instructions:**
1. Login to localhost:5000
2. Test dropdown on mobile viewport (375px)
3. Verify all actions work from dropdown
4. Test desktop shows regular buttons

**Playwright Tests:**
- `test/test_dropdown_menu.py`
  - Test dropdown opens/closes
  - Test all menu items functional
  - Test responsive behavior

### Task 4: Redesign Desktop Header Layout
**Agent:** flask-ui-developer  
**Responsibilities:**
- Implement compact desktop header
- Integrate activity picture inline with title
- Reduce padding and margins
- Use CSS Grid for layout

**Changes:**
- Activity picture: 30px height, inline left of title
- Total header height: max 180px
- Remove excessive vertical spacing
- Maintain button row at bottom

**Testing Instructions:**
1. Login to localhost:5000
2. Navigate to activity page on desktop
3. Measure header height (should be < 200px)
4. Verify all elements properly aligned

**Playwright Tests:**
- `test/test_desktop_header_layout.py`
  - Measure header dimensions
  - Verify all elements visible
  - Test different activity names/lengths
  - Screenshot: `/home/kdresdell/Pictures/Screenshots/test_header_desktop_after.png`

### Task 5: Optimize Mobile Layout
**Agent:** flask-ui-developer  
**Responsibilities:**
- Create mobile-optimized header
- Implement dropdown menu integration
- Ensure single-screen fit
- Optimize touch targets

**Changes:**
- Activity picture: 20px height, inline with "LHGI"
- Title split into readable lines
- Compact stats row
- Dropdown menu instead of button grid
- Total height: max 200px

**Testing Instructions:**
1. Login to localhost:5000
2. Set viewport to mobile (375x667)
3. Navigate to activity page
4. Verify header fits on single screen
5. Test dropdown menu functionality

**Playwright Tests:**
- `test/test_mobile_header_layout.py`
  - Test on multiple mobile viewports
  - Verify dropdown menu works
  - Verify touch targets (44px minimum)
  - Screenshot: `/home/kdresdell/Pictures/Screenshots/test_header_mobile_after.png`

### Task 6: Cross-Browser Testing & Integration
**Agent:** js-code-reviewer + code-security-reviewer  
**Responsibilities:**
- Full integration testing
- Cross-browser compatibility
- Performance validation
- Security review

**Testing Requirements:**

1. **Browser Testing (Using localhost:5000):**
   - Chrome, Firefox, Safari
   - Test viewports: 320px, 375px, 768px, 1024px, 1440px
   - Login with admin credentials for each test

2. **Functionality Testing:**
   - All buttons/menu items work
   - Revenue updates correctly
   - Activity picture loads properly
   - QR code displays
   - Dropdown menu on mobile only

3. **Performance Testing:**
   - Page load time < 2s
   - Header render < 100ms
   - Dropdown animation smooth

4. **Security Review:**
   - XSS prevention in dropdown
   - CSRF tokens maintained
   - No exposed sensitive data

**Integration Tests:**
- `test/test_activity_header_integration.py`
  - End-to-end workflow testing
  - All user actions from header
  - Mobile and desktop flows

**Screenshot Documentation:**
- Create comparison folder: `/home/kdresdell/Pictures/Screenshots/test_activity_header/`
- Before/after for all viewports
- Dropdown menu states

## Files to Modify

1. **Primary Files:**
   - `templates/activity_detail.html` - Header HTML structure
   - `static/css/custom.css` - Styling and responsive rules

2. **Potential Files:**
   - `templates/components/activity_header.html` (if exists)
   - `templates/base.html` (for dropdown script inclusion)

3. **Verification Only:**
   - `utils.py` - Verify revenue calculation logic

## Test Files to Create

All tests must use localhost:5000 with admin login:

1. `test/test_activity_header_revenue.py` - Revenue calculation tests
2. `test/test_revenue_display.py` - Display formatting tests
3. `test/test_dropdown_menu.py` - Dropdown functionality tests
4. `test/test_desktop_header_layout.py` - Desktop layout tests
5. `test/test_mobile_header_layout.py` - Mobile layout tests
6. `test/test_activity_header_integration.py` - Full integration tests

## CSS Implementation Strategy

```css
/* Mobile-first approach */
.activity-header {
  max-height: 200px;
}

.activity-picture {
  height: 20px;
  width: 20px;
}

.action-buttons {
  display: none; /* Hidden on mobile */
}

.dropdown-menu-mobile {
  display: block; /* Visible on mobile */
}

/* Desktop overrides */
@media (min-width: 768px) {
  .activity-header {
    max-height: 180px;
  }
  
  .activity-picture {
    height: 30px;
    width: 30px;
  }
  
  .action-buttons {
    display: flex; /* Visible on desktop */
  }
  
  .dropdown-menu-mobile {
    display: none; /* Hidden on desktop */
  }
}
```

## Success Criteria

- [ ] Header height reduced: Desktop ≤180px, Mobile ≤200px
- [ ] Activity picture integrated inline (not centered above)
- [ ] Revenue shows only amount and progress bar (no % or target)
- [ ] Mobile dropdown menu functional with all actions
- [ ] Desktop shows all buttons directly
- [ ] All existing functionality maintained
- [ ] Unit tests pass (6 test files)
- [ ] Playwright visual tests pass
- [ ] Screenshots saved in designated folders
- [ ] Tested on localhost:5000 with admin login

## Rollback Plan

1. Git commit before changes: `git commit -m "Backup before header redesign"`
2. Keep backup of original files:
   - `cp templates/activity_detail.html templates/activity_detail.html.backup`
   - `cp static/css/custom.css static/css/custom.css.backup`
3. If issues arise: `git revert HEAD`

## Timeline

- Task 1: 30 minutes (Analysis)
- Task 2: 45 minutes (Revenue simplification)
- Task 3: 1 hour (Dropdown menu component)
- Task 4: 1 hour (Desktop redesign)
- Task 5: 1 hour (Mobile optimization)
- Task 6: 45 minutes (Integration testing)
- **Total: ~5 hours**

## Important Notes

1. **Flask Server:** Always use localhost:5000 (already running)
2. **Testing:** Login with admin credentials for all tests
3. **Constraints:** Follow CONSTRAINTS.md guidelines
4. **Framework:** Use Tabler.io components (dropdown already available)
5. **JavaScript:** Minimal JS, use Tabler.io dropdown functionality
6. **Python-first:** Business logic stays in Python
7. **Screenshots:** Save all test screenshots in designated folders

## Communication to Agents

Each agent must:
1. Acknowledge reading this plan
2. Acknowledge reading CONSTRAINTS.md
3. Use localhost:5000 for all testing
4. Login with admin credentials
5. Create specified unit tests
6. Take Playwright screenshots
7. Report completion with test results