# Email Template Customization Tool - Bug Fix Plan

**Date:** October 29, 2025
**Context:** Fixing multiple bugs in the email template customization interface at `/activity/{id}/email-templates`

---

## Issues Identified

After analyzing screenshots and codebase, the following bugs were identified:

### 1. **Hero Image Reset Not Working** ⭐ CRITICAL

**Problem:** When clicking reset button, the text content resets correctly to defaults, but the hero image shows the wrong image (activity image instead of default template hero image)

**Root Cause:** The reset endpoint (`app.py:7932`) successfully deletes the custom hero image file from disk, but does NOT properly handle the fallback logic. The `get_activity_hero_image()` function then falls back to using the activity's main `image_filename` field instead of loading the pristine template default from `{template}_original/inline_images.json`

**Fix Location:**
- `app.py:7982-8016` (reset_email_template endpoint)
- `utils.py:124-175` (get_activity_hero_image function)

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

## Detailed Fix Plan

### **Step 1: Fix Reset Functionality**
**File:** `app.py` (reset_email_template endpoint, lines ~7932-8032)

**Current behavior:**
- Deletes physical hero image file from `static/uploads/{activity_id}_{template_type}_hero.png` ✅
- Removes fields from `activity.email_templates[template_type]` dict ✅
- Does NOT prevent activity image from being used as fallback ❌

**Required changes:**
1. After deleting the custom hero file, ensure the system knows to use template default
2. Options:
   - **Option A:** Store explicit flag in database: `activity.email_templates[template_type]['use_template_default'] = True`
   - **Option B:** Modify `get_activity_hero_image()` to check if template entry is completely empty/missing

**Recommendation:** Option B - if template has no custom fields AND no custom hero file exists, skip activity image fallback entirely

---

### **Step 2: Fix Hero Image Resolution Logic**
**File:** `utils.py` (get_activity_hero_image function, lines ~124-175)

**Current priority order:**
1. Custom uploaded hero ✅ CORRECT
2. Original template default from `{template}_original/inline_images.json` ✅ CORRECT
3. Activity image as last resort ❌ WRONG for reset scenario

**Required changes:**
Add logic to skip step 3 (activity image fallback) when:
- No custom hero file exists AND
- Template has been reset (no customizations in `activity.email_templates[template_type]`)

**Pseudo-code:**
```python
# Priority 1: Custom hero
if custom_hero_exists:
    return custom_hero

# Priority 2: Template default
template_default = get_template_default_hero(template_type)
if template_default:
    return template_default

# Priority 3: Activity image ONLY if template has customizations
# (indicating user intentionally didn't upload hero)
if activity.email_templates.get(template_type):  # Has customizations
    if activity.image_filename:
        return activity_image

# Priority 4: Fallback to system default
return None
```

---

### **Step 3: Fix Template Card Previews**
**File:** `templates/email_template_customization.html` (lines ~38-147)

**Current behavior:**
- Cards use `url_for('get_hero_image', activity_id=activity.id, template_type=template_key)`
- No cache-busting, so browser may cache old images
- No visual feedback when reset completes

**Required changes:**
1. Add cache-busting to image URLs: `?t=${Date.now()}`
2. After reset completes, force reload of affected card image
3. Update "Custom" vs "Default" badge immediately

**JavaScript to add:**
```javascript
// After successful reset
const cardImage = document.querySelector(`[data-template="${template}"] .mini-hero-img`);
if (cardImage) {
    cardImage.src = cardImage.src.split('?')[0] + `?t=${Date.now()}`;
}
```

---

### **Step 4: Fix Preview Button Click Handler**
**File:** `templates/email_template_customization.html` (lines ~575-629)

**Current behavior:**
- Opens new tab with blob URL
- No loading state shown
- No check if content is ready

**Root cause analysis:**
- Possible iframe loading delay
- Modal animation timing issues
- Race condition with form data collection

**Required changes:**
1. Add loading state to button
2. Add proper event handling for content ready
3. Debounce multiple clicks
4. Add error handling

**Improved code:**
```javascript
let previewInProgress = false;

document.addEventListener('click', function(e) {
    if (e.target.id === 'previewInModal') {
        // Prevent multiple clicks
        if (previewInProgress) {
            console.log('Preview already in progress, ignoring click');
            return;
        }

        previewInProgress = true;

        // Show loading state
        e.target.disabled = true;
        e.target.innerHTML = '<i class="ti ti-loader ti-spin me-2"></i>Loading...';

        // ... existing fetch logic ...

        .then(html => {
            // Create and open preview
            const blob = new Blob([html], { type: 'text/html; charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const newTab = window.open(url, '_blank');

            // Reset button state
            e.target.disabled = false;
            e.target.innerHTML = '<i class="ti ti-eye me-2"></i>Preview';
            previewInProgress = false;

            // Cleanup
            if (newTab) {
                setTimeout(() => URL.revokeObjectURL(url), 1000);
            }
        })
        .catch(error => {
            console.error('Preview error:', error);
            alert('Error generating preview: ' + error.message);

            // Reset button state
            e.target.disabled = false;
            e.target.innerHTML = '<i class="ti ti-eye me-2"></i>Preview';
            previewInProgress = false;
        });
    }
});
```

---

### **Step 5: Ensure Consistent State After Reset**

**Required changes:**
1. After reset API call succeeds, reload page to refresh ALL images
2. Clear any client-side caches
3. Update badge from "Custom" to "Default"
4. Show success message to user

**Current code (lines ~509-523):**
```javascript
.then(data => {
    if (data.success) {
        // Close modal
        const resetModal = bootstrap.Modal.getInstance(document.getElementById('resetConfirmModal'));
        if (resetModal) resetModal.hide();
        // Reload page to show updated badge
        location.reload();  // ✅ This is good
    }
})
```

**Improvement:** Add loading indicator before reload:
```javascript
if (data.success) {
    // Show success message
    const alert = document.createElement('div');
    alert.className = 'alert alert-success';
    alert.innerHTML = '<i class="ti ti-check me-2"></i>Template reset successfully! Refreshing...';
    document.body.prepend(alert);

    // Close modal
    const resetModal = bootstrap.Modal.getInstance(document.getElementById('resetConfirmModal'));
    if (resetModal) resetModal.hide();

    // Reload after brief delay
    setTimeout(() => location.reload(), 500);
}
```

---

## Implementation Order

### Phase 1: Backend Fixes
1. ✅ **Fix `reset_email_template()` endpoint** - Properly clear database entry
2. ✅ **Fix `get_activity_hero_image()` logic** - Don't use activity image for reset templates
3. ✅ **Test reset workflow** - Verify hero image returns to default

### Phase 2: Frontend Fixes
4. ✅ **Fix template card image URLs** - Add cache-busting
5. ✅ **Fix preview button** - Add loading state and debouncing
6. ✅ **Test preview workflow** - Verify works on first click

### Phase 3: Integration Testing
7. ✅ **Test complete reset workflow** - Text + hero both reset correctly
8. ✅ **Test customization workflow** - Upload custom hero, verify it appears
9. ✅ **Test preview after reset** - Verify shows correct defaults
10. ✅ **Test badge updates** - "Default" vs "Custom" display correctly

---

## Files to Modify

1. **`app.py`** (lines ~7932-8032) - `reset_email_template` endpoint
2. **`utils.py`** (lines ~124-175) - `get_activity_hero_image` function
3. **`templates/email_template_customization.html`** (lines ~432-763) - JavaScript handlers
4. **Possibly `app.py`** (lines ~8541-8581) - `get_hero_image` route

---

## Testing Checklist

After implementation, verify:

- [ ] Reset button clears BOTH text and hero image to pristine defaults
- [ ] Template cards on main grid show correct default hero images
- [ ] Preview button works on FIRST click (no multiple clicks needed)
- [ ] Preview shows correct content immediately after reset
- [ ] "Default" vs "Custom" badges display correctly
- [ ] No console errors in browser
- [ ] Hero image fallback logic works correctly:
  - Custom hero (if uploaded) → Template default → System default
  - Does NOT use activity image after reset
- [ ] Cache-busting works (images update without hard refresh)
- [ ] Loading states provide user feedback

---

## Expected Outcome

✅ **Reset button:** Clears BOTH text and hero image to defaults
✅ **Template cards:** Show correct default hero images
✅ **Preview button:** Works on first click every time
✅ **Preview content:** Shows correct content after reset
✅ **Badges:** Display "Default" vs "Custom" correctly
✅ **User experience:** Smooth, predictable, professional

---

## Notes

- The root cause of most issues is the hero image fallback logic treating "reset" and "never customized" as the same state
- Need to distinguish between:
  - **Never customized:** Can use activity image as reasonable default
  - **Reset to default:** Must use template default, NOT activity image
- Current implementation lacks this distinction
- Fix requires coordinating backend (database state) with frontend (image URLs)

---

**Plan created:** October 29, 2025
**Status:** Ready for implementation
**Estimated time:** 2-3 hours
