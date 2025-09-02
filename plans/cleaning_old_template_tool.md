# Clean-up Plan: Remove Old Email Template System

**Date**: September 2, 2025  
**Purpose**: Remove the old global email template system and keep only the new activity-specific email customization builder

## Executive Summary

We are removing the old prototype email template system that was accessible under Settings → Email Templates. This system used global templates that applied to all activities. It's being replaced by the new activity-specific email customization builder located at `/activity/<id>/email-templates`, which allows each activity to have its own customized email templates.

## Current State Analysis

### New System (To Keep)
- **Location**: `/activity/<id>/email-templates`
- **Storage**: `Activity.email_templates` JSON column in database
- **Features**: 
  - Activity-specific customization
  - Image upload capability
  - Real-time preview
  - Per-activity branding
  - Test email functionality

### Old System (To Remove)
- **Location**: Settings → Email Templates submenu
- **Storage**: `Setting` table with key-value pairs
- **Limitations**:
  - Global templates only (one style for all)
  - No image customization
  - No activity-specific branding
  - Limited customization options

## Detailed Removal Plan

### Phase 1: Database Cleanup

#### 1.1 Backup Database
```bash
cp instance/minipass.db instance/minipass_backup_$(date +%Y%m%d_%H%M%S).db
```

#### 1.2 Settings Table Cleanup
Remove all email template related settings from the `Setting` table:

**Keys to Delete:**
- `SUBJECT_pass_created`
- `SUBJECT_pass_redeemed`
- `SUBJECT_payment_received`
- `SUBJECT_payment_late`
- `SUBJECT_signup`
- `SUBJECT_survey_invitation`
- `TITLE_pass_created`
- `TITLE_pass_redeemed`
- `TITLE_payment_received`
- `TITLE_payment_late`
- `TITLE_signup`
- `TITLE_survey_invitation`
- `INTRO_pass_created`
- `INTRO_pass_redeemed`
- `INTRO_payment_received`
- `INTRO_payment_late`
- `INTRO_signup`
- `INTRO_survey_invitation`
- `CONCLUSION_pass_created`
- `CONCLUSION_pass_redeemed`
- `CONCLUSION_payment_received`
- `CONCLUSION_payment_late`
- `CONCLUSION_signup`
- `CONCLUSION_survey_invitation`
- `THEME_pass_created`
- `THEME_pass_redeemed`
- `THEME_payment_received`
- `THEME_payment_late`
- `THEME_signup`
- `THEME_survey_invitation`
- `HEADING_pass_created` through `HEADING_survey_invitation`
- `CUSTOM_MESSAGE_pass_created` through `CUSTOM_MESSAGE_survey_invitation`
- `CTA_TEXT_pass_created` through `CTA_TEXT_survey_invitation`
- `CTA_URL_pass_created` through `CTA_URL_survey_invitation`

**SQL Command:**
```sql
DELETE FROM setting 
WHERE key LIKE 'SUBJECT_%' 
   OR key LIKE 'TITLE_%'
   OR key LIKE 'INTRO_%'
   OR key LIKE 'CONCLUSION_%'
   OR key LIKE 'THEME_%'
   OR key LIKE 'HEADING_%'
   OR key LIKE 'CUSTOM_MESSAGE_%'
   OR key LIKE 'CTA_TEXT_%'
   OR key LIKE 'CTA_URL_%';
```

### Phase 2: Frontend Cleanup

#### 2.1 Remove Settings Menu Item
**File**: `templates/base.html`
**Lines to Remove**: 521-524

```html
<!-- REMOVE THIS SECTION -->
<li class="nav-item">
  <a href="{{ url_for('setup') }}" class="nav-link" data-tab="email-templates">
    <i class="nav-icon ti ti-template"></i>
    <span class="nav-text">Email Templates</span>
  </a>
</li>
```

#### 2.2 Remove Email Notification Tab
**File**: `templates/setup.html`
**Lines to Remove**: 51-100+ (entire Email Notification tab section)

This includes:
- Tab navigation item for Email Notification
- Tab pane with all 6 email template forms
- Associated form fields for each template type

### Phase 3: Backend Code Cleanup

#### 3.1 Clean Setup Route
**File**: `app.py`
**Lines to Modify**: 2111-2120

Remove the email notification template saving logic in the `/setup` route:
```python
# REMOVE THIS SECTION
# Step 8: Save email notification templates (including signup and survey_invitation)
for event in ["pass_created", "pass_redeemed", "payment_received", "payment_late", "signup", "survey_invitation"]:
    for key in ["SUBJECT", "TITLE", "INTRO", "CONCLUSION", "THEME"]:
        full_key = f"{key}_{event}"
        value = request.form.get(full_key, "").strip()
        if value:
            existing = Setting.query.filter_by(key=full_key).first()
            # ... rest of the logic
```

#### 3.2 Remove Utility Function
**File**: `utils.py`
**Lines to Remove**: 1951-2020+

Remove the entire `copy_global_email_templates_to_activity()` function and its references.

#### 3.3 Update Activity Creation
**File**: `app.py`
**Line to Modify**: 1389

Change from:
```python
email_templates=copy_global_email_templates_to_activity(),
```

To:
```python
email_templates={},  # Start with empty templates, user will customize
```

### Phase 4: Code References to Update

#### 4.1 Import Statements
Remove import of `copy_global_email_templates_to_activity` from utils where used:
- Line 1345 in app.py

#### 4.2 Email Sending Functions
Verify that all email sending functions use activity-specific templates:
- `notify_pass_event()` 
- `send_survey_invitation()`
- `send_signup_confirmation()`

These should already be using activity-specific templates through the new system.

### Phase 5: Testing Plan

#### 5.1 Pre-Removal Testing
1. Document current email template settings for reference
2. Test sending one email of each type with old system
3. Verify new email builder is working for all activities

#### 5.2 Post-Removal Testing
1. Verify Settings menu no longer shows Email Templates
2. Test creating a new activity (should work without `copy_global_email_templates_to_activity`)
3. Test email customization for existing activities
4. Send test emails for all 6 template types:
   - Pass Created
   - Pass Redeemed
   - Payment Received
   - Payment Late
   - Signup Confirmation
   - Survey Invitation

#### 5.3 Edge Cases to Test
- Activity with no email templates defined (should use defaults)
- Activity with partial templates defined
- Email sending when activity.email_templates is None or {}

### Phase 6: Rollback Plan

If issues arise:
1. Restore database from backup
2. Revert code changes using git
3. Restart Flask server

**Backup Commands:**
```bash
# Before starting
git status
git add .
git commit -m "Backup before removing old email template system"

# Create database backup
cp instance/minipass.db instance/minipass_pre_cleanup.db
```

## Files to Keep (DO NOT DELETE)

These files are still used by the new system:
- `templates/email_templates/` directory and all subdirectories
- `templates/email_template_customization.html` (new builder UI)
- Email template routes in app.py:
  - `/activity/<int:activity_id>/email-templates`
  - `/activity/<int:activity_id>/email-templates/save`
  - `/activity/<int:activity_id>/email-test`

## Success Criteria

✅ Old Email Templates menu item removed from Settings  
✅ Setup page no longer shows Email Notification tab  
✅ Database cleaned of old template settings  
✅ New email builder works for all activities  
✅ All email types send successfully  
✅ No broken references in codebase  
✅ User experience improved with single, powerful tool  

## Notes

- The core email template files in `templates/email_templates/` are shared between both systems
- The new system uses these as base templates and applies customizations on top
- Each activity can now have unique branding and messaging
- This change simplifies the codebase and improves user experience

## Timeline

Estimated time: 2-3 hours
1. Backup and preparation: 15 minutes
2. Database cleanup: 30 minutes
3. Code removal: 45 minutes
4. Testing: 60 minutes
5. Documentation: 30 minutes

---

*This plan ensures a clean removal of the old system while preserving all functionality in the new activity-specific email customization builder.*