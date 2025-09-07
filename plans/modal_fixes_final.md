# Modal Fixes Final - Complete Implementation Plan

## Context
The email template modal has several critical issues that need to be fixed. The user has identified specific problems with functionality and organization.

## Critical Issues to Fix

### 1. Fix Save Changes Button (CRITICAL - NOT WORKING)
**Problem**: Save button shows "Save functionality coming soon!" alert instead of actually saving
**Solution**: 
- Remove placeholder JavaScript alerts 
- Implement real save functionality using existing backend endpoint `/activity/{id}/email-templates/save`
- Collect form data from modal (subject, title, intro_text, conclusion_text)
- Get TinyMCE rich text content properly
- Send POST request to backend with FormData
- Show proper success/error messages
- **TEST**: Click save button and verify data is actually saved to database

### 2. Fix Preview Changes Button (CRITICAL - NOT WORKING) 
**Problem**: Preview button shows "Preview functionality coming soon!" alert
**Solution**:
- Remove placeholder alert
- Connect to existing backend endpoint `/activity/{id}/email-preview`
- Open preview in new tab/window or modal iframe
- **TEST**: Click preview and verify email preview displays correctly

### 3. Fix Modal Title (Currently shows generic "Customize Email Template")
**Problem**: Title should show specific template name (e.g., "New Pass Created")
**Solution**:
- Debug why JavaScript `document.getElementById('modalTemplateName').textContent = templateName;` isn't working
- Ensure element exists and is being updated properly
- **TEST**: Open modal and verify title shows template name

### 4. Reorganize Modal Fields (User Request)
**Problem**: Fields don't match email structure order
**Current Order**: Email Subject → Email Title → Introduction Text → Conclusion Text → Global Settings (Hero Image, Logo)
**Requested Order**: Email Subject → Hero Image → Email Title → Introduction Text → Conclusion Text → Logo

**Solution**:
- Move Hero Image field to appear right after Email Subject
- Show actual current hero image (not placeholder)
- Allow user to select new image and preview it immediately
- Keep save functionality for hero image changes

### 5. Improve Hero Image Display
**Problem**: Hero image field doesn't show current image properly
**Solution**:
- Display actual current hero image in modal
- Add preview functionality when user selects new image
- Make image clickable to change it
- Show image filename/path

## Testing Requirements (MANDATORY)
**BEFORE marking anything as complete, you MUST test using MCP Playwright:**

1. **Login**: Use credentials `kdresdell@gmail.com` / `admin123`
2. **Navigate**: Go to Activity 5 email templates page
3. **Open Modal**: Click customize button for any template
4. **Test Save**: 
   - Modify some text in the rich text editors
   - Click "Save Changes" 
   - Verify success message (not "coming soon" alert)
   - Close and reopen modal to confirm changes were saved
5. **Test Preview**: 
   - Click "Preview Changes"
   - Verify preview opens (not "coming soon" alert)
6. **Test Title**: Verify modal title shows template name, not generic text
7. **Test Field Order**: Verify hero image appears after email subject

## Backend Endpoints (ALREADY EXIST - DO NOT CREATE NEW ONES)
- Save: `POST /activity/<int:activity_id>/email-templates/save`
- Preview: `GET /activity/<int:activity_id>/email-preview?type={template_type}`
- Preview Live: `POST /activity/<int:activity_id>/email-preview-live`

## Files to Modify
- `/home/kdresdell/Documents/DEV/minipass_env/app/templates/email_template_customization.html`
  - Fix JavaScript event handlers for save/preview buttons
  - Fix modal title update
  - Reorganize field order in hidden template forms
  - Improve hero image display

## Success Criteria
- ✅ Save button actually saves data to backend (no more placeholder alerts)
- ✅ Preview button opens real email preview (no more placeholder alerts)  
- ✅ Modal title shows specific template name
- ✅ Hero image field appears after email subject
- ✅ Hero image shows actual current image with preview functionality
- ✅ All functionality tested and verified working using MCP Playwright

## Notes
- Current modal centering, TinyMCE integration, and form pre-population are working correctly
- Blue info card removal is complete
- Focus on fixing JavaScript connectivity issues and field reorganization
- Test credentials: kdresdell@gmail.com / admin123
- Test URL: http://localhost:5000/activity/5/email-templates