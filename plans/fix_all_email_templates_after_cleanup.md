# Comprehensive Fix Plan: Restore All Email Functionality with Activity-Specific Templates

**Created**: September 2, 2025  
**Issue**: All automated emails broken after old email template system cleanup  
**Impact**: All 6 email types sending with generic content instead of customized templates

## Problem Summary

After removing the old global email template system from the Settings table, ALL automated emails are broken:
- Emails ARE still being sent
- BUT they use generic/default content like "[Minipass] Pass_Created Notification"
- Activity-specific templates exist but aren't being used
- Functions still try to read from deleted Settings instead of new activity.email_templates

## Affected Email Types

1. **New passport creation** - "pass_created"
2. **Payment confirmation** - "payment_received"  
3. **Late payment reminders** - "payment_late"
4. **Pass redemption** - "pass_redeemed"
5. **Signup confirmation** - "signup"
6. **Survey invitations** - "survey_invitation"

## Root Cause Analysis

### Functions That Need Fixing:
1. **`notify_pass_event()`** (utils.py line 1546)
   - Still uses `get_setting()` to read from deleted Settings table
   - Needs to use `get_email_context()` to read from activity.email_templates

2. **`notify_signup_event()`** (utils.py line 1461)
   - Still uses `get_setting()` for templates
   - Already has activity parameter but doesn't use it properly

3. **`send_survey_invitations()`** (app.py line 6009)
   - Uses `get_setting()` for survey email templates
   - Has access to survey.activity but doesn't use it

## Mapping: Old Event Types → New Template Keys

| Old Event Type (Settings) | New Template Key (JSON) | Used By Function |
|--------------------------|-------------------------|------------------|
| `pass_created` | `newPass` | notify_pass_event() |
| `payment_received` | `paymentReceived` | notify_pass_event() |
| `payment_late` | `latePayment` | notify_pass_event() |
| `pass_redeemed` | `redeemPass` | notify_pass_event() |
| `signup` | `signup` | notify_signup_event() |
| `survey_invitation` | `survey_invitation` | send_survey_invitations() |

## Detailed Fix Implementation

### 1. Update `notify_pass_event()` function (utils.py line 1546)

**Changes needed:**
- Add `activity` parameter to function signature
- Replace all `get_setting()` calls with `get_email_context()`
- Map old event types to new template keys

**Current code pattern:**
```python
subject = get_setting("SUBJECT_pass_created", "default")
title = get_setting("TITLE_pass_created", "default")
```

**Should become:**
```python
# Map old event type to new template key
template_key_map = {
    "pass_created": "newPass",
    "payment_received": "paymentReceived",
    "payment_late": "latePayment",
    "pass_redeemed": "redeemPass"
}
template_key = template_key_map.get(event_type, event_type)

# Get customized context from activity
context = get_email_context(activity, template_key, base_context)
subject = context.get('subject', 'Minipass Notification')
```

### 2. Update `notify_signup_event()` function (utils.py line 1461)

**Changes needed:**
- Replace `get_setting()` calls with `get_email_context()`
- Use template key "signup"

**Current code:**
```python
subject = get_setting("SUBJECT_signup", "Confirmation d'inscription")
```

**Should become:**
```python
context = get_email_context(activity, "signup", base_context)
subject = context.get('subject', 'Signup Confirmation')
```

### 3. Update `send_survey_invitations()` function (app.py line 6009)

**Changes needed:**
- Use `survey.activity` to get templates
- Replace `get_setting()` with `get_email_context()`

**Current code (line 6081):**
```python
subject = get_setting('SUBJECT_survey_invitation', f"{survey.name} - Your Feedback Requested")
```

**Should become:**
```python
email_context = get_email_context(survey.activity, "survey_invitation", base_context)
subject = email_context.get('subject', f"{survey.name} - Your Feedback Requested")
```

### 4. Update all function callers to pass activity

#### Locations to update:

**app.py line 4984 (passport creation):**
```python
# Current
notify_pass_event(
    app=current_app._get_current_object(),
    event_type="pass_created",
    pass_data=passport,
    admin_email=session.get("admin"),
    timestamp=now_utc
)

# Should add activity
activity_obj = db.session.get(Activity, activity_id)
notify_pass_event(
    app=current_app._get_current_object(),
    activity=activity_obj,  # ADD THIS
    event_type="pass_created",
    pass_data=passport,
    admin_email=session.get("admin"),
    timestamp=now_utc
)
```

**utils.py line 717 (late payment reminders):**
```python
# Current
notify_pass_event(
    app=current_app._get_current_object(),
    event_type="payment_late",
    pass_data=p,
    admin_email="auto-reminder@system",
    timestamp=datetime.now()
)

# Should add activity
notify_pass_event(
    app=current_app._get_current_object(),
    activity=p.activity,  # ADD THIS
    event_type="payment_late",
    pass_data=p,
    admin_email="auto-reminder@system",
    timestamp=datetime.now()
)
```

**utils.py line 849 (payment matching):**
```python
# Current
notify_pass_event(
    app=current_app._get_current_object(),
    event_type="payment_received",
    pass_data=best_passport,
    admin_email="gmail-bot@system",
    timestamp=now_utc
)

# Should add activity
notify_pass_event(
    app=current_app._get_current_object(),
    activity=best_passport.activity,  # ADD THIS
    event_type="payment_received",
    pass_data=best_passport,
    admin_email="gmail-bot@system",
    timestamp=now_utc
)
```

### 5. Implement Fallback Mechanism

For activities without email_templates or missing specific templates:

```python
def get_email_context(activity, template_type, base_context=None):
    # Default fallbacks
    defaults = {
        'newPass': {
            'subject': 'Your Digital Pass is Ready!',
            'title': 'Welcome!',
            'intro_text': 'Your digital pass has been created.',
            'conclusion_text': 'Thank you for your participation!'
        },
        'paymentReceived': {
            'subject': 'Payment Confirmed',
            'title': 'Payment Received',
            'intro_text': 'We have received your payment.',
            'conclusion_text': 'Thank you for your payment!'
        },
        # ... other defaults
    }
    
    # Start with type-specific defaults
    context = defaults.get(template_type, {}).copy()
    
    # Override with base_context if provided
    if base_context:
        context.update(base_context)
    
    # Override with activity-specific customizations if they exist
    if activity and activity.email_templates:
        template_customizations = activity.email_templates.get(template_type, {})
        for key, value in template_customizations.items():
            if value is not None and value != '':
                context[key] = value
    
    return context
```

## Agent Assignment & Execution Strategy

### Recommended Agent: backend-architect

**Why backend-architect is the best choice:**
- Specializes in server-side logic and API implementation
- Expert in Python/Flask architecture
- Can handle complex function refactoring
- Understands database relationships and data flow

### Critical Information for Agent:

#### Environment Setup:
- **Flask Server**: Already running on `localhost:5000` in debug mode (DO NOT START A NEW ONE)
- **MCP Playwright**: Available and configured for browser testing
- **Database**: SQLite at `instance/minipass.db`
- **Virtual Environment**: Already activated at `venv/`

#### Testing Credentials:
- **Admin Login**: 
  - URL: `http://localhost:5000/login`
  - Email: `kdresdell@gmail.com`
  - Password: `admin123`
- **Test Email**: Use `kdresdell@gmail.com` for all email tests
- **Test Activity**: Use Activity 4 (Tournois de Pocker - FLHGI) which has French templates

## Testing Plan

### Test Cases:

1. **Activity 4 (Poker Tournament) - Has French templates**
   - Create passport → Should send French email "LHGI 🎟️ Votre passe numérique est prête !"
   - Process payment → Should send "LHGI ✅ Paiement confirmé !"
   - Create signup → Should send "LHGI ✍️ Votre Inscription est confirmée"

2. **Activity with NO email_templates**
   - Create new activity with empty email_templates
   - Create passport → Should send with English defaults
   - Verify fallback mechanism works

3. **All email types**
   - Test each of the 6 email types
   - Verify correct subject and content
   - Check email logs for successful delivery

### Unit Test Requirements:

**Location**: Save all tests in `/test/` directory

**Test File**: `/test/test_email_template_fix.py`

```python
import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Activity, Passport, User, Signup
from utils import notify_pass_event, notify_signup_event, get_email_context
import json
from datetime import datetime, timezone

class TestEmailTemplateFix(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
    def test_activity_4_french_templates(self):
        """Test that Activity 4 uses French email templates"""
        activity = Activity.query.get(4)
        context = get_email_context(activity, 'newPass', {})
        self.assertIn('LHGI', context.get('subject', ''))
        self.assertIn('prête', context.get('subject', ''))
        
    def test_fallback_to_defaults(self):
        """Test fallback when activity has no templates"""
        # Create mock activity without templates
        mock_activity = Activity()
        mock_activity.email_templates = None
        context = get_email_context(mock_activity, 'newPass', {})
        self.assertEqual(context.get('subject'), 'Your Digital Pass is Ready!')
        
    def test_all_email_types_mapping(self):
        """Test mapping of all 6 email types"""
        mappings = {
            'pass_created': 'newPass',
            'payment_received': 'paymentReceived',
            'payment_late': 'latePayment',
            'pass_redeemed': 'redeemPass',
            'signup': 'signup',
            'survey_invitation': 'survey_invitation'
        }
        # Test each mapping works correctly
        for old_type, new_type in mappings.items():
            # Your test logic here
            pass

if __name__ == '__main__':
    unittest.main()
```

### MCP Playwright Test Requirements:

**Location**: Save screenshots in `/test/playwright/`

**Test File**: `/test/test_email_sending_playwright.py`

```python
# Test actual email sending through the UI
# 1. Navigate to http://localhost:5000/login
# 2. Login with kdresdell@gmail.com / admin123
# 3. Create a new passport for Activity 4
# 4. Take screenshot of success message
# 5. Check email_log table for correct subject
# 6. Navigate to email preview if available
# 7. Take screenshot of email preview
```

### Verification SQL Queries:
```sql
-- Check recent emails
SELECT timestamp, to_email, subject FROM email_log 
ORDER BY timestamp DESC LIMIT 10;

-- Check activity email templates
SELECT id, name, 
       json_extract(email_templates, '$.newPass.subject') as newpass_subject,
       json_extract(email_templates, '$.paymentReceived.subject') as payment_subject
FROM activity;

-- Check recent passport creations
SELECT p.created_dt, u.name, u.email, a.name as activity_name
FROM passport p 
JOIN user u ON p.user_id = u.id
JOIN activity a ON p.activity_id = a.id
ORDER BY p.created_dt DESC LIMIT 5;
```

## Risk Assessment & Mitigation

### Risks:
1. **Email delivery interruption** - LOW (emails still being sent, just content issue)
2. **Data loss** - NONE (no database changes required)
3. **Rollback complexity** - LOW (can revert code changes easily)

### Mitigation:
- Test on one email type first before applying to all
- Keep backup of current code before changes
- Monitor email logs during implementation
- Have fallback defaults for all template types

## Expected Outcomes

After implementation:
- ✅ All 6 email types working with activity-specific templates
- ✅ French emails for Activity 4 (Tournois de Pocker - FLHGI)
- ✅ English defaults for activities without customization
- ✅ No more generic "[Minipass] Pass_Created Notification" subjects
- ✅ Email customization builder continues to work for future changes

## Files to Modify

1. **utils.py**
   - Line 1546: `notify_pass_event()` function
   - Line 1461: `notify_signup_event()` function
   - Line 717: Late payment reminder caller
   - Line 849: Payment matching caller

2. **app.py**
   - Line 4984: Passport creation route
   - Line 6009: Survey invitation route

## Rollback Plan

If issues arise:
1. Git revert the changes to utils.py and app.py
2. Restart Flask server
3. Emails will return to current state (sending with generic content)

## Implementation Instructions for Agent

### Step-by-Step Execution:

1. **Start with notify_pass_event() fix**:
   - Add `activity` parameter
   - Implement template key mapping
   - Replace get_setting() calls
   - Test with Activity 4

2. **Fix all callers of notify_pass_event()**:
   - Search for all occurrences
   - Add activity parameter to each call
   - Use pass_data.activity when available

3. **Fix notify_signup_event()**:
   - Already has activity parameter
   - Just replace get_setting() calls
   - Test signup flow

4. **Fix send_survey_invitations()**:
   - Use survey.activity
   - Replace get_setting() calls
   - Test survey email sending

5. **Create unit tests**:
   - Save in /test/ directory
   - Test all 6 email types
   - Test with and without templates
   - Run tests: `python test/test_email_template_fix.py`

6. **MCP Playwright testing**:
   - Use existing Flask server on port 5000
   - Login with provided credentials
   - Test actual email sending flow
   - Save screenshots in /test/playwright/

### Common Pitfalls to Avoid:

1. **DO NOT start a new Flask server** - Use the existing one on port 5000
2. **DO NOT forget to pass activity parameter** - This is the root cause of the issue
3. **DO NOT remove fallback defaults** - Activities without templates need them
4. **DO NOT test with fake emails** - Use kdresdell@gmail.com for real testing
5. **DO NOT skip unit tests** - They ensure the fix works for all scenarios

## Notes

- This fix completes the migration from old global templates to new activity-specific templates
- The get_email_context() function already exists and is tested
- Activity 4 already has properly configured French templates
- This is the final step to complete the email template system modernization
- Agent must acknowledge reading CONSTRAINTS.md before starting
- Agent must use Python-first approach (minimal JavaScript)

---

*This plan ensures all email functionality is restored while maintaining the benefits of activity-specific customization.*