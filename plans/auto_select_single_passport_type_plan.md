# Auto-Select Single Passport Type - Implementation Plan

## 📋 Overview
**Objective:** When creating a passport with a pre-selected activity that has only ONE passport type, automatically select it. If multiple passport types exist, user must choose manually.

**Date Created:** 2025-09-05  
**Risk Level:** LOW  
**Estimated Code Addition:** ~15-20 lines total  
**Breaking Changes:** None  

## 🔐 IMPORTANT: Testing Environment & Credentials

### Flask Server Information
- **Server Status:** ✅ ALREADY RUNNING IN DEBUG MODE
- **URL:** http://localhost:5000
- **Port:** 5000
- **Mode:** Debug (auto-reloads on file changes)
- **DO NOT START A NEW SERVER - USE THE EXISTING ONE**

### Login Credentials
```
Email: kdresdell@gmail.com
Password: admin123
```

### Test Activities (IDs for testing)
- Activity ID 5: Kitesurf training (check how many passport types it has)
- Activity ID 1: Hockey du midi LHGI
- Activity ID 3: Tournoi Golf Fondation LHGI

## 👥 Agent Task Assignments

### Task 1: Backend Implementation
**Assigned to:** `backend-architect`

**Files to modify:** 
- `/home/kdresdell/Documents/DEV/minipass_env/app/app.py`

**Location in code:** 
- Function: `create_passport()` route (around line 5006)
- Specifically after line 5104 where passport_types are loaded

**Code to add:**
```python
# After line 5104 where passport_types are loaded
# ADD these lines to detect single passport type:
single_passport_type_id = None
if selected_activity_id and len(passport_types) == 1:
    single_passport_type_id = passport_types[0].id

# Then at line ~5113 in render_template(), ADD:
single_passport_type_id=single_passport_type_id,
```

**Testing instructions:**
1. Navigate to http://localhost:5000/login
2. Login with: kdresdell@gmail.com / admin123
3. Go to: http://localhost:5000/create-passport?activity_id=5
4. Verify the single_passport_type_id is passed to template (check Flask debug output)

---

### Task 2: Frontend JavaScript Implementation
**Assigned to:** `flask-ui-developer`

**Files to modify:**
- `/home/kdresdell/Documents/DEV/minipass_env/app/templates/passport_form.html`

**Location in code:**
- Function: `updateActivityDetails()` (around line 397)
- After the passport type filtering logic (after line 411)

**Code to add:**
```javascript
// Add this AFTER line 411 (passportTypeSelect.value = "";)
// Auto-select if only one passport type available
let visibleOptions = 0;
let singleOptionValue = null;

for (let option of passportTypeSelect.options) {
    if (option.value !== "" && option.style.display !== "none") {
        visibleOptions++;
        singleOptionValue = option.value;
    }
}

// If only one passport type exists, auto-select it
if (visibleOptions === 1 && singleOptionValue) {
    passportTypeSelect.value = singleOptionValue;
    updatePassportTypeDetails(passportTypeSelect);
}
```

**Testing instructions:**
1. Server already running on http://localhost:5000
2. Login with: kdresdell@gmail.com / admin123
3. Test scenarios:
   - Navigate to: http://localhost:5000/create-passport?activity_id=5
   - Check if passport type auto-selects when only one option
   - Change activity dropdown to one with multiple passport types
   - Verify it resets to "-- Select Passport Type --"
4. Open browser console (F12) to check for any JavaScript errors

---

### Task 3: Comprehensive Testing with MCP Playwright
**Assigned to:** `flask-ui-developer`

**Testing checklist:**
1. **Login to application:**
   ```
   URL: http://localhost:5000
   Email: kdresdell@gmail.com
   Password: admin123
   ```

2. **Test Case 1: Activity with single passport type**
   - Navigate to: http://localhost:5000/create-passport?activity_id=5
   - Verify passport type is auto-selected
   - Verify price and sessions are auto-populated
   - Take screenshot: `/test/playwright/single-passport-auto-selected.png`

3. **Test Case 2: Activity with multiple passport types**
   - Change activity dropdown to different activity
   - Verify passport type shows "-- Select Passport Type --"
   - Verify user must manually select
   - Take screenshot: `/test/playwright/multiple-passport-manual-select.png`

4. **Test Case 3: Form submission**
   - Fill in user details
   - Submit form with auto-selected passport type
   - Verify form submits successfully
   - Check database for created passport

5. **Test Case 4: Mobile responsiveness**
   - Resize viewport to 375x812
   - Test auto-selection works on mobile
   - Take screenshot: `/test/playwright/mobile-auto-select.png`

## 📝 Implementation Notes

### JavaScript Constraints
- Keep JavaScript additions under 20 lines
- No global event listeners
- No complex patterns or frameworks
- Only modify the existing `updateActivityDetails()` function

### Python/Flask Preferences
- Minimal backend changes (3-5 lines)
- Use existing data structures
- No new database queries
- Leverage existing passport_types query

## ✅ Success Criteria

1. **Auto-selection works:** When activity has one passport type, it's automatically selected
2. **Manual selection preserved:** Multiple passport types require manual selection  
3. **Price/sessions update:** Auto-selected passport type updates price and sessions
4. **No console errors:** Clean JavaScript execution
5. **Form submission:** Works with auto-selected values
6. **Non-breaking:** All existing functionality preserved

## 🚫 What NOT to Do

1. DO NOT start a new Flask server (use existing on port 5000)
2. DO NOT modify database schema
3. DO NOT add more than 50 lines of JavaScript
4. DO NOT break existing manual selection functionality
5. DO NOT forget to test with the provided credentials

## 📊 Risk Mitigation

- If auto-selection fails, form still works manually
- No data loss possible (read-only operation)
- Changes are additive only (no removal of existing code)
- Easy rollback: just remove the added lines

## 🎯 Final Verification

After implementation, verify:
1. Login works with provided credentials
2. Navigate from activity dashboard to create-passport
3. Single passport type auto-selects
4. Multiple passport types don't auto-select
5. Form submits successfully
6. No errors in browser console
7. No errors in Flask debug output

## 📌 Remember

**CRITICAL REMINDERS FOR AGENTS:**
- Flask server is ALREADY RUNNING on localhost:5000
- Use credentials: kdresdell@gmail.com / admin123
- DO NOT start new servers
- DO NOT use npm/node/webpack
- Test on the EXISTING Flask debug server
- Take screenshots for verification