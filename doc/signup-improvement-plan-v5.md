# Signup Form Improvement Plan v5 - With Agent Assignments

## Executive Summary
This plan outlines minimal, safe improvements to the signup form with specific agent assignments for each task. The URL structure `/signup/<activity_id>?passport_type_id=<id>` already determines which passport type the user is signing up for - NO selection needed.

## Critical Understanding - Passport Type System

### URL Structure
```
http://127.0.0.1:8890/signup/1?passport_type_id=1
                            ↑                    ↑
                      Activity ID         Passport Type ID
```

**KEY POINT**: The passport type is ALREADY DETERMINED by the URL parameter. Users DO NOT choose between passport types on this form.

### Current Implementation (app.py lines 1526-1530)
```python
passport_type_id = request.args.get('passport_type_id')
selected_passport_type = None
if passport_type_id:
    selected_passport_type = PassportType.query.get(passport_type_id)
```

## Logo Clarification
**CONFIRMED**: The logo displayed is the ORGANIZATION'S logo (stored in settings["LOGO_FILENAME"]), NOT a Minipass logo.

## Agent-Assigned Implementation Tasks

### Phase 1: Preparation & Analysis
**Agent: backend-architect**
- **Task 1.1**: Create backup of current signup form
  ```bash
  cp templates/signup_form.html templates/signup_form_backup_$(date +%Y%m%d_%H%M%S).html
  ```
- **Task 1.2**: Analyze current form structure and dependencies
- **Task 1.3**: Document all form field names and IDs that must be preserved
- **Time**: 15 minutes

### Phase 2: Remove Passport Type Selection
**Agent: flask-ui-developer**
- **Task 2.1**: Remove passport type selection UI (lines 313-364)
  - Remove mobile card selection (lines 321-346)
  - Remove desktop dropdown (lines 349-362)
  - Keep hidden passport_type_id field (line 309)
- **Task 2.2**: Remove JavaScript for passport type selection (lines 459-533)
  - Remove `selectPassportType()` function
  - Remove `updatePricing()` function
  - Remove `updatePricingDisplay()` function
- **Time**: 30 minutes

### Phase 3: Enhance Visual Structure
**Agent: ui-designer**
- **Task 3.1**: Design the new layout structure
  - Create split-screen layout for desktop
  - Design hero image section for mobile
  - Plan passport type info display (read-only)
- **Task 3.2**: Create CSS improvements using existing Tabler classes
  ```css
  /* Use existing classes: */
  .card, .card-body, .shadow-sm
  .bg-blue-lt, .text-blue
  .rounded-3, .mb-4, .p-4
  ```
- **Time**: 45 minutes

### Phase 4: Implement Desktop Layout
**Agent: flask-ui-developer**
- **Task 4.1**: Restructure desktop layout
  ```html
  <div class="row g-0">
    <div class="col-md-6"><!-- Form --></div>
    <div class="col-md-6"><!-- Activity Image --></div>
  </div>
  ```
- **Task 4.2**: Enhance form section
  - Add organization logo display
  - Implement passport type info card (read-only)
  - Apply Tabler form classes (.form-control-lg)
- **Task 4.3**: Implement activity image section
  - Use `activity.image_filename`
  - Apply background-image with cover
  - Ensure full height display
- **Time**: 1 hour

### Phase 5: Implement Mobile Layout
**Agent: flask-ui-developer**
- **Task 5.1**: Create hero image section for mobile
  ```html
  <div class="d-block d-md-none">
    <!-- Activity image as background with overlay -->
    <!-- Organization logo overlaid -->
    <!-- Activity name on image -->
  </div>
  ```
- **Task 5.2**: Optimize mobile form fields
  - Apply `.form-control-lg` for better touch targets
  - Ensure proper spacing with `.mb-4`
  - Test input focus doesn't zoom page
- **Time**: 45 minutes

### Phase 6: JavaScript Cleanup & Enhancement
**Agent: js-code-reviewer**
- **Task 6.1**: Review remaining JavaScript
  - Remove all passport type selection code
  - Keep form validation if exists
  - Ensure CSRF token handling intact
- **Task 6.2**: Add smooth transitions
  ```javascript
  // Add CSS transitions for hover states
  // Ensure mobile touch interactions work
  ```
- **Time**: 30 minutes

### Phase 7: Testing with Playwright
**Agent: Use Playwright MCP Tools directly**
- **Task 7.1**: Desktop testing
  ```javascript
  // Navigate to http://127.0.0.1:8890/signup/1?passport_type_id=1
  // Take screenshot at 1920x1080
  // Fill form and test submission
  ```
- **Task 7.2**: Mobile testing
  ```javascript
  // Resize to 375x667
  // Test hero image display
  // Test form inputs
  // Verify no zoom on input focus
  ```
- **Task 7.3**: Multiple passport type testing
  ```javascript
  // Test with passport_type_id=1
  // Test with passport_type_id=2
  // Verify correct type displays each time
  ```
- **Time**: 45 minutes

### Phase 8: Security & Functionality Review
**Agent: code-security-reviewer**
- **Task 8.1**: Security verification
  - Verify CSRF token preserved
  - Check form action unchanged
  - Ensure passport_type_id hidden field works
- **Task 8.2**: Functionality verification
  - Test form submission
  - Verify data saved correctly
  - Check all required fields captured
- **Task 8.3**: Cross-browser testing
  - Test on Chrome
  - Test on Firefox
  - Test on Safari (if available)
- **Time**: 30 minutes

### Phase 9: Documentation & Screenshots
**Agent: backend-architect**
- **Task 9.1**: Document changes made
  - List all modified lines
  - Document removed code sections
  - Note any potential issues
- **Task 9.2**: Create before/after comparison
  - Screenshot current form
  - Screenshot improved form
  - Save to `/playwright/` directory
- **Time**: 20 minutes

## Wireframes v5

### Desktop Version (1920x1080)
```
┌────────────────────────────────────────────────────────────────┐
│                          Browser Window                          │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Signup Card Container                  │  │
│  │  ┌─────────────────────────┬───────────────────────────┐ │  │
│  │  │                          │                           │ │  │
│  │  │      Form Section        │    Activity Image         │ │  │
│  │  │       (Left 50%)         │      (Right 50%)         │ │  │
│  │  │                          │                           │ │  │
│  │  │  [Organization Logo]     │   [activity.image_       │ │  │
│  │  │  (60px height)           │    filename]             │ │  │
│  │  │                          │                           │ │  │
│  │  │  Activity Name (h2)      │   Full height image      │ │  │
│  │  │  ─────────────           │   background with        │ │  │
│  │  │                          │   object-fit: cover      │ │  │
│  │  │  ┌──────────────────┐    │                           │ │  │
│  │  │  │ Registration Info │    │                           │ │  │
│  │  │  │ Type: Regular     │    │                           │ │  │
│  │  │  │ Price: $45.00     │    │                           │ │  │
│  │  │  │ Sessions: 10      │    │                           │ │  │
│  │  │  └──────────────────┘    │                           │ │  │
│  │  │  (READ-ONLY INFO)        │                           │ │  │
│  │  │                          │                           │ │  │
│  │  │  Full Name               │                           │ │  │
│  │  │  ┌────────────────────┐  │                           │ │  │
│  │  │  │                    │  │                           │ │  │
│  │  │  └────────────────────┘  │                           │ │  │
│  │  │                          │                           │ │  │
│  │  │  Email Address           │                           │ │  │
│  │  │  ┌────────────────────┐  │                           │ │  │
│  │  │  │                    │  │                           │ │  │
│  │  │  └────────────────────┘  │                           │ │  │
│  │  │                          │                           │ │  │
│  │  │  Phone Number            │                           │ │  │
│  │  │  ┌────────────────────┐  │                           │ │  │
│  │  │  │                    │  │                           │ │  │
│  │  │  └────────────────────┘  │                           │ │  │
│  │  │                          │                           │ │  │
│  │  │  Additional Notes        │                           │ │  │
│  │  │  ┌────────────────────┐  │                           │ │  │
│  │  │  │                    │  │                           │ │  │
│  │  │  │                    │  │                           │ │  │
│  │  │  └────────────────────┘  │                           │ │  │
│  │  │                          │                           │ │  │
│  │  │  ☐ Accept Terms          │                           │ │  │
│  │  │                          │                           │ │  │
│  │  │  ┌────────────────────┐  │                           │ │  │
│  │  │  │ Submit Registration │  │                           │ │  │
│  │  │  └────────────────────┘  │                           │ │  │
│  │  │                          │                           │ │  │
│  │  └─────────────────────────┴───────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

### Mobile Version (375x667) - Enhanced
```
┌─────────────────┐
│  Mobile Browser │
├─────────────────┤
│                 │
│ ┌─────────────┐ │
│ │  Activity   │ │
│ │   Image     │ │
│ │ Background  │ │
│ │             │ │
│ │  [Org Logo] │ │
│ │             │ │
│ │  Activity   │ │
│ │    Name     │ │
│ └─────────────┘ │
│                 │
│ ┌─────────────┐ │
│ │Registration │ │
│ │    Info     │ │
│ │ Type: Regular│ │
│ │ $45 | 10 sess│ │
│ └─────────────┘ │
│                 │
│  Full Name      │
│  ┌───────────┐  │
│  │           │  │
│  └───────────┘  │
│                 │
│  Email          │
│  ┌───────────┐  │
│  │           │  │
│  └───────────┘  │
│                 │
│  Phone          │
│  ┌───────────┐  │
│  │           │  │
│  └───────────┘  │
│                 │
│  Notes          │
│  ┌───────────┐  │
│  │           │  │
│  │           │  │
│  └───────────┘  │
│                 │
│  ☐ Accept Terms │
│                 │
│  ┌───────────┐  │
│  │  Submit   │  │
│  └───────────┘  │
│                 │
└─────────────────┘
```

## Implementation Timeline by Agent

| Time | Agent | Tasks | Duration |
|------|-------|-------|----------|
| 0:00 | backend-architect | Backup & analysis (Tasks 1.1-1.3) | 15 min |
| 0:15 | flask-ui-developer | Remove passport selection (Tasks 2.1-2.2) | 30 min |
| 0:45 | ui-designer | Design new layout (Tasks 3.1-3.2) | 45 min |
| 1:30 | flask-ui-developer | Implement desktop (Tasks 4.1-4.3) | 60 min |
| 2:30 | flask-ui-developer | Implement mobile (Tasks 5.1-5.2) | 45 min |
| 3:15 | js-code-reviewer | JavaScript cleanup (Tasks 6.1-6.2) | 30 min |
| 3:45 | Playwright MCP | Testing (Tasks 7.1-7.3) | 45 min |
| 4:30 | code-security-reviewer | Security review (Tasks 8.1-8.3) | 30 min |
| 5:00 | backend-architect | Documentation (Tasks 9.1-9.2) | 20 min |

**Total Time: 5 hours 20 minutes**

## Key Files to Modify

1. **templates/signup_form.html**
   - Remove lines 313-364 (passport type selection)
   - Remove lines 459-533 (JavaScript)
   - Enhance remaining structure

2. **No changes to:**
   - app.py
   - models.py
   - static/minipass.css
   - Any other files

## Testing Commands for Agents

### For Playwright Testing Agent:
```javascript
// Desktop test
await page.goto('http://127.0.0.1:8890/signup/1?passport_type_id=1');
await page.setViewportSize({ width: 1920, height: 1080 });
await page.screenshot({ path: '/playwright/signup-desktop-new.png' });

// Mobile test
await page.setViewportSize({ width: 375, height: 667 });
await page.screenshot({ path: '/playwright/signup-mobile-new.png' });

// Form submission test
await page.fill('input[name="name"]', 'Test User');
await page.fill('input[name="email"]', 'test@example.com');
await page.fill('input[name="phone"]', '514-555-0123');
await page.fill('textarea[name="notes"]', 'Test notes');
await page.check('input[name="accept_terms"]');
await page.click('button[type="submit"]');
```

## Common Mistakes Each Agent Should Avoid

### flask-ui-developer:
- ❌ DON'T add passport type selection back
- ❌ DON'T create new CSS files
- ❌ DON'T break the hidden passport_type_id field

### ui-designer:
- ❌ DON'T use placeholder images
- ❌ DON'T create Minipass branding
- ❌ DON'T overcomplicate the design

### js-code-reviewer:
- ❌ DON'T remove CSRF token handling
- ❌ DON'T break form validation
- ❌ DON'T add complex interactions

### code-security-reviewer:
- ❌ DON'T modify backend endpoints
- ❌ DON'T change form field names
- ❌ DON'T alter security tokens

## Success Metrics

1. **Functionality** (code-security-reviewer to verify)
   - Form submits successfully
   - Correct passport_type_id saved
   - All fields captured properly

2. **Visual** (ui-designer to verify)
   - Clean, modern appearance
   - Proper use of activity image
   - Organization logo displays correctly

3. **Performance** (backend-architect to verify)
   - Page loads quickly
   - No console errors
   - Mobile responsive

4. **User Experience** (flask-ui-developer to verify)
   - Clear passport type information
   - Easy form completion
   - Professional appearance

## Final Checklist

- [ ] Backup created (backend-architect)
- [ ] Passport selection removed (flask-ui-developer)
- [ ] Desktop layout implemented (flask-ui-developer)
- [ ] Mobile layout implemented (flask-ui-developer)
- [ ] JavaScript cleaned up (js-code-reviewer)
- [ ] Playwright tests passed (Playwright MCP)
- [ ] Security verified (code-security-reviewer)
- [ ] Documentation complete (backend-architect)
- [ ] Screenshots saved to /playwright/ (Playwright MCP)

---
*Plan v5 - With specific agent assignments for each task*
*Total implementation time: ~5 hours with proper agent coordination*