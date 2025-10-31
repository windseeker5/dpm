# Email Template Customization Tool - Bug Fix Plan

**Date:** October 29, 2025
**Context:** Fixing multiple bugs in the email template customization interface at `/activity/{id}/email-templates`

---

## Issues Identified

After analyzing screenshots and codebase, the following bugs were identified:

### 1. **Hero Image Reset Not Working** ⭐ CRITICAL

**Problem:** When clicking reset button, the text content resets correctly to defaults, but the hero image shows the OLD hero image (from October 9) instead of the NEW fox mascot hero image (compiled October 29)

**Root Cause:** The `_original` folders contain OLD compiled templates from October 9, 2025, but the NEW fox mascot hero images were compiled to `_compiled` folders on October 29, 2025. When reset occurs, `get_activity_hero_image()` loads from `{template}_original/inline_images.json` which has the old images.

**Email Template System Architecture:**
- **Master templates:** `templateName/` folders - Source files you edit (HTML + images)
- **Compiled templates:** `templateName_compiled/` - Production versions with base64-embedded images in `inline_images.json`
- **Original backups:** `templateName_original/` - Pristine compiled versions used for reset functionality
- Hero images are stored as base64 strings in `inline_images.json`, NOT as separate files

**The Problem:**
1. New fox mascot images were added to master templates on October 29
2. Master templates were compiled to `_compiled/` folders (October 29)
3. BUT `_original/` folders were NOT updated (still contain October 9 versions)
4. Reset loads from outdated `_original/` folders

**Fix Location:**
- Copy ALL `_compiled/` folders to replace `_original/` folders to update reset defaults
- Templates affected: `newPass`, `paymentReceived`, `latePayment`, `signup`, `redeemPass`, `survey_invitation`

---

### 2. **Template Card Preview Shows Wrong Images**

**Problem:** On the main template grid view, the template preview cards show activity images instead of the default template hero images

**Root Cause:** Same underlying issue as #1 - the `get_hero_image()` route returns the activity image when no custom hero exists, instead of returning the template default hero

**Fix Location:**
- `templates/email_template_customization.html:50` (image src)
- Backend `get_hero_image()` route logic

---

### 3. **Preview Button Requires Multiple Clicks** ⭐ HIGH PRIORITY

**Problem:** When clicking the "Preview" button in the customization modal, user must click 3-5 times before the preview actually displays

**Root Cause:** JavaScript event handling issue - likely a race condition where:
- Modal is not fully loaded
- Iframe is not ready to receive content
- Event listeners are firing before DOM is ready

**Fix Location:** `templates/email_template_customization.html:575-629` (Preview button click handler in JavaScript)

---

### 4. **Preview Shows Wrong Hero After Reset**

**Problem:** After performing a reset, the preview modal shows the correct reset text content but still displays the wrong hero image

**Root Cause:** This is a manifestation of issue #1 - the reset doesn't fully clear all customizations, so preview continues to use wrong image source

**Fix Location:** Combined fix with issue #1

---

### 5. **Inconsistent UX: Custom Toast on Reset** ⭐ HIGH PRIORITY

**Problem:** When clicking reset button, a custom JavaScript-generated toast notification appears with "Success! Template reset to defaults. Refreshing..." message. This is inconsistent with the rest of the application.

**Root Cause:** Custom JavaScript alert/toast implementation in `email_template_customization.html` instead of using standard Flask flash messages

**Why This Matters:**
- Application uses Flask flash messages for passport operations (redeem, create, mark-as-paid)
- Inconsistent UX patterns confuse users and look unprofessional
- Standard flash messages have proper styling and dismissal behavior

**Fix Location:**
- `templates/email_template_customization.html` (reset click handler)
- Replace custom toast with Flask flash message in backend
- `app.py` reset_email_template endpoint should return flash message

**Reference Example:** Passport operations in app.py show proper flash message pattern

---

### 6. **Inconsistent UX: JavaScript Alert on Save** ⭐ HIGH PRIORITY

**Problem:** When clicking save button, a browser-native JavaScript `alert()` popup appears saying "127.0.0.1:5000 says Template saved successfully!" with an OK button. This is unprofessional and inconsistent.

**Root Cause:** JavaScript `alert()` call in save handler instead of using Flask flash messages

**Why This Matters:**
- JavaScript alerts are blocking and disruptive
- They show the domain/host in the popup (looks unprofessional)
- Cannot be styled to match application theme
- Inconsistent with rest of application UX

**Fix Location:**
- `templates/email_template_customization.html` (save click handler)
- Replace `alert()` with Flask flash message pattern
- Backend should flash message, frontend should reload to show it

**Reference Example:** Passport operations in app.py show proper flash message pattern

---

## Detailed Fix Plan

### **Step 1: Update _original Folders with New Fox Mascot Hero Images** ⭐ CRITICAL

**The Core Problem:**
The `_original` folders are used as the source for reset functionality, but they contain OLD hero images from October 9, 2025. The NEW fox mascot hero images were compiled on October 29, 2025 to `_compiled/` folders but were never copied to `_original/`.

**Solution:**
Copy all 6 `_compiled/` folders to replace their corresponding `_original/` folders.

**Commands to execute:**
```bash
cd /home/kdresdell/Documents/DEV/minipass_env/app/templates/email_templates/

# Backup old originals (just in case)
mv newPass_original newPass_original_old_oct9
mv paymentReceived_original paymentReceived_original_old_oct9
mv latePayment_original latePayment_original_old_oct9
mv signup_original signup_original_old_oct9
mv redeemPass_original redeemPass_original_old_oct9
mv survey_invitation_original survey_invitation_original_old_oct9

# Copy compiled versions to become new originals
cp -r newPass_compiled newPass_original
cp -r paymentReceived_compiled paymentReceived_original
cp -r latePayment_compiled latePayment_original
cp -r signup_compiled signup_original
cp -r redeemPass_compiled redeemPass_original
cp -r survey_invitation_compiled survey_invitation_original
```

**Expected outcome:**
- All `_original/inline_images.json` files now contain fox mascot hero images
- Reset functionality will load NEW default hero images
- Template system integrity maintained

---

### **Step 2: Replace Custom Toast with Flask Flash Message (Reset)**
**Files:**
- `templates/email_template_customization.html` (reset handler)
- `app.py` (reset_email_template endpoint, lines ~7932-8032)

**Current behavior:**
```javascript
// Custom toast notification
const alertDiv = document.createElement('div');
alertDiv.className = 'alert alert-success alert-dismissible position-fixed top-0 start-50 translate-middle-x mt-3';
alertDiv.innerHTML = `<i class="ti ti-check me-2"></i><strong>Success!</strong> Template reset to defaults. Refreshing...`;
document.body.appendChild(alertDiv);
```

**Required changes:**

1. **Backend (`app.py`):** Add flash message to reset endpoint
```python
from flask import flash

@app.route('/reset_email_template/<int:activity_id>/<template_type>', methods=['POST'])
def reset_email_template(activity_id, template_type):
    # ... existing reset logic ...

    flash('Template reset to defaults successfully!', 'success')
    return jsonify({'success': True})
```

2. **Frontend:** Remove custom toast, let page reload show Flask flash
```javascript
.then(data => {
    if (data.success) {
        // Close modal
        const resetModal = bootstrap.Modal.getInstance(document.getElementById('resetConfirmModal'));
        if (resetModal) resetModal.hide();

        // Reload page - Flask flash message will appear
        location.reload();
    }
})
```

---

### **Step 3: Replace JavaScript Alert with Flask Flash Message (Save)**
**Files:**
- `templates/email_template_customization.html` (save handler)
- `app.py` (save_email_template endpoint)

**Current behavior:**
```javascript
alert('Template saved successfully!');
```

**Required changes:**

1. **Backend (`app.py`):** Add flash message to save endpoint
```python
@app.route('/save_email_template/<int:activity_id>/<template_type>', methods=['POST'])
def save_email_template(activity_id, template_type):
    # ... existing save logic ...

    flash('Email template saved successfully!', 'success')
    return jsonify({'success': True})
```

2. **Frontend:** Remove alert, reload to show Flask flash
```javascript
.then(data => {
    if (data.success) {
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('customizeModal'));
        if (modal) modal.hide();

        // Reload page - Flask flash message will appear
        location.reload();
    }
})
```

**Reference:** Check passport operations (redeem/create/mark-as-paid) for exact flash message pattern used in app

---

## Implementation Order

### Phase 1: Update Template Defaults (CRITICAL) ⭐
1. **Backup old _original folders** - Rename to `_original_old_oct9`
2. **Copy _compiled to _original** - All 6 templates
3. **Verify inline_images.json** - Confirm fox mascot images present
4. **Test reset** - Verify shows NEW fox mascot hero images

### Phase 2: Fix UX Inconsistencies
5. **Add flash message to reset endpoint** - Backend `app.py`
6. **Remove custom toast from reset handler** - Frontend JavaScript
7. **Add flash message to save endpoint** - Backend `app.py`
8. **Remove JavaScript alert from save handler** - Frontend JavaScript
9. **Test UX consistency** - Verify flash messages appear correctly

### Phase 3: Integration Testing
10. **Test complete reset workflow** - Text + hero both reset to fox mascot
11. **Test customization workflow** - Upload custom hero, verify it appears
12. **Test save workflow** - Verify flash message appears (not alert)
13. **Test badge updates** - "Default" vs "Custom" display correctly
14. **Test preview after reset** - Verify shows correct fox mascot hero

### Status Tracking
- ⭐ Phase 1: NOT STARTED (critical priority)
- Phase 2: NOT STARTED
- Phase 3: NOT STARTED

---

## Files to Modify

1. **Template folders** (all 6 templates)
   - Backup: `newPass_original` → `newPass_original_old_oct9` (etc.)
   - Copy: `newPass_compiled` → `newPass_original` (etc.)

2. **`app.py`**
   - Lines ~7932-8032: `reset_email_template` endpoint - add flash message
   - Lines ~TBD: `save_email_template` endpoint - add flash message

3. **`templates/email_template_customization.html`**
   - Reset handler: Remove custom toast, rely on flash message + reload
   - Save handler: Remove JavaScript alert, rely on flash message + reload

---

## Testing Checklist

After implementation, verify:

### Hero Image Tests
- [ ] Reset button clears BOTH text and hero image to NEW fox mascot defaults
- [ ] Template cards on main grid show correct NEW fox mascot hero images
- [ ] Preview shows correct NEW fox mascot hero after reset
- [ ] All 6 templates (newPass, paymentReceived, latePayment, signup, redeemPass, survey_invitation) show fox mascot

### UX Consistency Tests
- [ ] Reset shows Flask flash message (not custom toast)
- [ ] Save shows Flask flash message (not JavaScript alert)
- [ ] Flash messages match style used in passport operations
- [ ] No JavaScript `alert()` popups anywhere
- [ ] No custom toast notifications

### General Tests
- [ ] "Default" vs "Custom" badges display correctly
- [ ] Preview button works on FIRST click (✅ already fixed)
- [ ] No console errors in browser
- [ ] Cache-busting works (images update without hard refresh)

---

## Expected Outcome

✅ **Reset button:** Clears BOTH text and hero image to NEW fox mascot defaults
✅ **Template cards:** Show correct NEW fox mascot hero images
✅ **Preview button:** Works on first click every time (already fixed)
✅ **Preview content:** Shows NEW fox mascot hero after reset
✅ **Badges:** Display "Default" vs "Custom" correctly
✅ **User experience:** Smooth, predictable, professional
✅ **UX consistency:** Flask flash messages used throughout (no alerts/toasts)

---

## Notes

### Root Cause Analysis (Updated October 29, 2025)

**Original misunderstanding:**
- I initially thought the issue was with fallback logic in `get_activity_hero_image()`
- I modified `utils.py` to prevent activity image fallback after reset
- This was NOT the real problem

**Actual root cause:**
- The `_original` folders are used as the source for reset defaults
- These folders contain OLD hero images from October 9, 2025
- NEW fox mascot hero images were compiled on October 29, 2025 to `_compiled/` folders
- The `_original/` folders were never updated with the new compiled versions
- Reset correctly loads from `_original/`, but gets OLD images

**Email template system architecture:**
- Master templates (`templateName/`): Source files with HTML + images
- Compiled templates (`templateName_compiled/`): Production with base64 in `inline_images.json`
- Original backups (`templateName_original/`): Pristine compiled versions for reset
- Hero images stored as base64 strings in `inline_images.json`

**The fix:**
- Copy `_compiled/` folders to `_original/` to update reset defaults
- Replace custom JavaScript alerts/toasts with Flask flash messages
- Maintain UX consistency across the application

---

**Plan created:** October 29, 2025
**Plan updated:** October 29, 2025 (with correct root cause understanding)
**Status:** ✅ COMPLETED - October 29, 2025
**Additional fix required:** Fixed incorrect hero_key_map in utils.py (keys didn't match actual JSON keys)

## CRITICAL FIX DISCOVERED DURING IMPLEMENTATION

The original plan identified copying `_compiled` to `_original` folders, but during testing we discovered an additional bug:

**Bug in `utils.py` - `get_template_default_hero()` function:**
- The `hero_key_map` dictionary had INCORRECT keys for most templates
- It was looking for keys like `'hero_late_payment'` but actual keys in JSON are `'thumb-down'`, `'currency-dollar'`, etc.
- This caused the function to fail finding hero images and fall back to activity images

**Fix applied to `utils.py:99-106`:**
- Fixed hero_key_map to use actual keys from inline_images.json files:
  - `'paymentReceived': 'currency-dollar'` (was: 'hero_payment_received')
  - `'latePayment': 'thumb-down'` (was: 'hero_late_payment')
  - `'signup': 'good-news'` (was: 'hero_signup')
  - `'redeemPass': 'hand-rock'` (was: 'hero_redeem_pass')
- Added missing `'redeemPass'` template mapping

**Actual time:** 2 hours
