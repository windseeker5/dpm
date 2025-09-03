# Activity Dashboard Signup Table Improvements - Implementation Plan

**Date:** 2025-09-03  
**Project:** Minipass Activity Dashboard  
**Priority:** High  
**Flask Server:** `localhost:5000` (ALREADY RUNNING - DO NOT START NEW INSTANCE)

## CRITICAL ENVIRONMENT INFORMATION
- **Flask Server:** Always running on `localhost:5000` in debug mode
- **MCP Playwright:** Available for browser testing
- **Test Credentials:**
  - Admin Login: `jf@jfgoulet.com` / `NewBrunswick2020!`
  - Test Activity: Tournoi Golf Fondation LHGI - 2025
  - Activity ID: Available in dashboard URL after login

## Overview
Improve the activity dashboard signup table to focus on pending signups by default, hide the section when no pending signups exist, and simplify the filter buttons.

## Agent Assignments

### 1. Backend Implementation - `backend-architect` Agent
**Why this agent:** Specializes in server-side logic, API design, and database optimization. Best suited for modifying Flask routes and backend logic.

**Tasks:**
1. Modify `/activity_dashboard/<int:activity_id>` route in `app.py` (lines 3972-4168)
2. Change default signup filter from 'all' to 'pending'
3. Add `has_pending_signups` flag to template context
4. Ensure backward compatibility with existing filter parameters

**Implementation Details:**
```python
# In app.py, activity_dashboard function
signup_filter = request.args.get('signup_filter', 'pending')  # Changed from 'all'

# Calculate pending signups
pending_signups = [s for s in all_signups if s.status == 'pending']
has_pending_signups = len(pending_signups) > 0

# Add to template context
return render_template(
    "activity_dashboard.html",
    ...
    has_pending_signups=has_pending_signups,
    pending_signups_count=len(pending_signups),
    ...
)
```

### 2. Frontend Implementation - `flask-ui-developer` Agent
**Why this agent:** Expert in Flask templates, Tabler.io components, and responsive design. Perfect for modifying Jinja2 templates and UI components.

**Tasks:**
1. Update `templates/activity_dashboard.html`
2. Wrap signup section in conditional display
3. Simplify filter buttons
4. Update JavaScript filter functions

**Implementation Details:**

#### A. Conditional Display (lines 1437-1674)
```html
<!-- Only show signup section if there are pending signups -->
{% if has_pending_signups %}
  <!-- Signups Section -->
  <h2 class="mt-5 mb-3">
    <i class="ti ti-edit text-orange me-2"></i>Signups
  </h2>
  
  <!-- Rest of signup table code -->
  ...
{% endif %}
```

#### B. Simplified Filter Buttons (lines 1496-1517)
```html
<div class="github-filter-group" role="group">
  <a href="#" onclick="filterSignups('all'); return false;"
     class="github-filter-btn {% if request.args.get('signup_filter', 'pending') == 'all' %}active{% endif %}" 
     id="signup-filter-all">
    <i class="ti ti-list"></i>All Signups <span class="filter-count">({{ all_signups|length }})</span>
  </a>
  <!-- REMOVED: Unpaid and Paid filters -->
  <a href="#" onclick="filterSignups('pending'); return false;"
     class="github-filter-btn {% if request.args.get('signup_filter', 'pending') == 'pending' %}active{% endif %}" 
     id="signup-filter-pending">
    <i class="ti ti-alert-circle"></i>Pending <span class="filter-count">({{ pending_signups_count }})</span>
  </a>
  <a href="#" onclick="filterSignups('approved'); return false;"
     class="github-filter-btn {% if request.args.get('signup_filter', 'pending') == 'approved' %}active{% endif %}" 
     id="signup-filter-approved">
    <i class="ti ti-thumb-up"></i>Approved <span class="filter-count">({{ all_signups|selectattr('status', 'equalto', 'approved')|list|length }})</span>
  </a>
</div>
```

#### C. JavaScript Updates (lines 2509-2519)
```javascript
function filterSignups(filterType) {
  // Remove references to 'unpaid' and 'paid' filters
  document.querySelectorAll('#signup-filter-all, #signup-filter-pending, #signup-filter-approved').forEach(btn => {
    btn.classList.remove('active');
  });
  document.getElementById('signup-filter-' + filterType).classList.add('active');
  loadFilteredData('signup', filterType);
}
```

## Testing Requirements

### 3. Testing Implementation - `code-security-reviewer` + `js-code-reviewer` Agents
**Why these agents:** Specialized in code review, security analysis, and testing best practices.

### Unit Test Requirements

**File Location:** `/home/kdresdell/Documents/DEV/minipass_env/app/test/test_activity_dashboard_signups.py`

```python
import unittest
from app import app, db
from models import Activity, Signup, Admin
from datetime import datetime

class TestActivityDashboardSignups(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        
    def test_pending_filter_is_default(self):
        """Test that pending filter is selected by default"""
        # Login as admin
        self.app.post('/login', data={
            'email': 'jf@jfgoulet.com',
            'password': 'NewBrunswick2020!'
        })
        
        # Navigate to activity dashboard
        response = self.app.get('/activity_dashboard/1')
        self.assertIn(b'signup-filter-pending', response.data)
        self.assertIn(b'active', response.data)
        
    def test_signup_section_hidden_when_no_pending(self):
        """Test that signup section is hidden when no pending signups"""
        # Test with activity that has no pending signups
        response = self.app.get('/activity_dashboard/2')  
        self.assertNotIn(b'<h2 class="mt-5 mb-3">', response.data)
        self.assertNotIn(b'ti-edit text-orange', response.data)

if __name__ == '__main__':
    unittest.main()
```

### Integration Test with MCP Playwright

**File Location:** `/home/kdresdell/Documents/DEV/minipass_env/app/test/test_activity_dashboard_ui.py`

```python
"""
MCP Playwright Integration Test for Activity Dashboard Signup Improvements
Server: localhost:5000 (already running - DO NOT start new instance)
"""

# Test Credentials - USE THESE EXACTLY
ADMIN_EMAIL = "jf@jfgoulet.com"
ADMIN_PASSWORD = "NewBrunswick2020!"
TEST_URL = "http://localhost:5000"

# Test Steps for MCP Playwright:
# 1. Navigate to http://localhost:5000/login
# 2. Login with credentials above
# 3. Navigate to activity dashboard for "Tournoi Golf Fondation LHGI - 2025"
# 4. Verify "Pending" filter is active by default
# 5. Verify only pending signups are shown
# 6. Click "All Signups" filter
# 7. Verify all signups are shown
# 8. Take screenshot: /home/kdresdell/Documents/DEV/minipass_env/app/test/screenshots/activity_dashboard_filters.png

# Test for hidden signup section:
# 1. Create or find activity with no pending signups
# 2. Navigate to that activity dashboard
# 3. Verify signup section is completely hidden
# 4. Take screenshot: /home/kdresdell/Documents/DEV/minipass_env/app/test/screenshots/no_pending_signups.png
```

### Manual Testing Checklist

**For the executing agent to verify:**

1. **Login Test:**
   ```bash
   # Navigate to: http://localhost:5000/login
   # Use credentials: jf@jfgoulet.com / NewBrunswick2020!
   ```

2. **Pending Filter Default Test:**
   - Navigate to any activity dashboard
   - Verify "Pending" button is highlighted by default
   - Verify only pending signups are shown in the table

3. **No Pending Signups Test:**
   - Find or create activity with no pending signups
   - Navigate to that activity dashboard  
   - Verify entire signup section is hidden (no title, no table)

4. **Filter Simplification Test:**
   - Verify only 3 filter buttons exist: "All Signups", "Pending", "Approved"
   - Verify "Unpaid" and "Paid" filters are removed

5. **Screenshot Documentation:**
   - Save all test screenshots to: `/home/kdresdell/Documents/DEV/minipass_env/app/test/screenshots/`
   - Naming convention: `test_[feature]_[date]_[result].png`

## Execution Order

1. **First:** `backend-architect` agent implements backend changes
2. **Second:** `flask-ui-developer` agent implements frontend changes
3. **Third:** `code-security-reviewer` reviews all changes for security
4. **Fourth:** `js-code-reviewer` reviews JavaScript changes
5. **Finally:** Run all tests using MCP Playwright

## Success Criteria

- [ ] Pending filter is active by default on activity dashboard
- [ ] Signup section completely hidden when no pending signups exist
- [ ] Filter buttons simplified (only All, Pending, Approved)
- [ ] All existing functionality maintained
- [ ] Unit tests passing
- [ ] MCP Playwright integration tests passing
- [ ] Screenshots saved in test folder

## Important Notes for All Agents

1. **DO NOT** start a new Flask server - use existing one on `localhost:5000`
2. **DO NOT** create new virtual environments - use existing `venv/`
3. **ALWAYS** use provided credentials for testing
4. **ALWAYS** save test files in `/home/kdresdell/Documents/DEV/minipass_env/app/test/`
5. **ALWAYS** save screenshots in `/home/kdresdell/Documents/DEV/minipass_env/app/test/screenshots/`
6. **READ** `/home/kdresdell/Documents/DEV/minipass_env/app/docs/CONSTRAINTS.md` before starting

## Rollback Plan

If issues occur:
1. Backup files are in `templates/activity_dashboard_backup_*.html`
2. Git reset to commit `bfe299a` if needed
3. Database is SQLite - backup in `instance/` folder

---

**End of Plan**

Generated: 2025-09-03
Status: Ready for execution