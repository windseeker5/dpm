# Ultimate Email Template Customization Plan

## Project: Activity Image as Default Hero with Custom Override

**Date**: September 3, 2025  
**Risk Level**: MEDIUM ⚠️  
**Estimated Time**: 1.5-2 hours  
**Test Email**: kdresdell@gmail.com (Ken's personal email - MUST use for ALL tests)

## Executive Summary

Transform email templates to use activity images as default hero images while maintaining custom override capability. This creates automatic personalization for every activity while preserving user control.

## Why This Is a Great Idea ✅

1. **Automatic Branding** - Every activity gets personalized emails without manual setup
2. **Professional Look** - Real images instead of generic icons (dollar signs, checkmarks)
3. **User Flexibility** - Can still upload custom heroes for specific templates
4. **Visual Consistency** - Activity branding consistent across all communications
5. **Better UX** - Zero configuration needed for good-looking emails

## Risk Assessment

| Component | Risk Level | Impact if Failed | Mitigation Strategy |
|-----------|------------|------------------|---------------------|
| Core Templates | LOW | Emails look wrong | Backup utils.py, test all 4 templates |
| Existing Customizations | MEDIUM | Lost custom settings | Test with Activities 1, 3, 4 |
| Email Delivery | LOW | Emails don't send | Only changing images, not flow |
| Database | ZERO | N/A | No schema changes |
| Attachments Bug | HIGH | Images show as attachments | Extensive inline image testing |

## Implementation Plan

### Phase 1: Backup & Documentation (5 mins)
**Agent**: general-purpose  
**Critical Tasks**:
```bash
# Create timestamped backup
cp utils.py /test/backup_utils_$(date +%Y%m%d_%H%M%S).py
cp -r templates/email_templates /test/backup_email_templates/

# Document current state
sqlite3 instance/minipass.db "SELECT id, name FROM activity;" > /test/current_activities.txt
```

### Phase 2: Core Implementation (30 mins)
**Agent**: backend-architect  
**Location**: `/home/kdresdell/Documents/DEV/minipass_env/app/utils.py`

#### 2.1 Create Hero Image Selection Function
```python
def get_activity_hero_image(activity, template_type):
    """
    Hero image selection with intelligent fallback:
    1. Custom uploaded hero (from email_templates JSON)
    2. Activity image (auto-styled as circle)
    3. Template default (current behavior)
    
    Returns: tuple (image_data, is_custom, needs_circle_style)
    """
    import os
    import json
    
    # Priority 1: Check for custom hero upload
    if activity and activity.email_templates:
        try:
            templates = json.loads(activity.email_templates) if isinstance(activity.email_templates, str) else activity.email_templates
            template_config = templates.get(template_type, {})
            
            # Check if custom hero was uploaded
            custom_hero_path = f"static/uploads/{activity.id}_{template_type}_hero.png"
            if os.path.exists(custom_hero_path):
                with open(custom_hero_path, "rb") as f:
                    print(f"✅ Using custom hero for {template_type}")
                    return f.read(), True, False
        except Exception as e:
            print(f"⚠️ Error checking custom hero: {e}")
    
    # Priority 2: Use activity image as hero
    if activity:
        activity_image_path = f"static/uploads/activity_{activity.id}.png"
        if os.path.exists(activity_image_path):
            with open(activity_image_path, "rb") as f:
                print(f"🎨 Using activity image as hero for {template_type}")
                return f.read(), False, True  # Needs circular styling
    
    # Priority 3: Return None to use template default
    print(f"📦 Using template default hero for {template_type}")
    return None, False, False
```

#### 2.2 Update notify_pass_event (Payment, New Pass, Late Payment)
- Lines ~1820-1830: Replace hardcoded hero with activity image
- Ensure 'ticket' CID gets replaced with activity hero
- Add circular styling CSS when using activity image

#### 2.3 Fix notify_signup_event (Signup Email)
- Line ~1691: Only add logo if not already in inline_images
- Keep celebration hero (don't replace for signup)
- Fix attachment issue

### Phase 3: Comprehensive Test Suite (20 mins)
**Agent**: general-purpose  
**Location**: `/test/test_ultimate_email_customization.py`

```python
"""
CRITICAL: All tests MUST send real emails to kdresdell@gmail.com
This is the ONLY way to verify attachments are fixed
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, Activity, Signup, Passport, User
from utils import notify_signup_event, notify_pass_event
from datetime import datetime, timezone

# Test configuration
TEST_EMAIL = "kdresdell@gmail.com"  # Ken's personal email - REQUIRED
TEST_USER_NAME = "Test User - Ultimate Email Test"

def test_all_email_templates():
    """
    Test ALL 4 email templates with real email delivery
    MUST verify NO ATTACHMENTS in any email
    """
    
    with app.app_context():
        print("\n" + "="*60)
        print("ULTIMATE EMAIL TEMPLATE TEST")
        print("Sending to: " + TEST_EMAIL)
        print("="*60)
        
        # Get test activities
        activities = Activity.query.filter(Activity.id.in_([1, 3, 4])).all()
        
        for activity in activities:
            print(f"\n📧 Testing Activity {activity.id}: {activity.name}")
            
            # Test 1: SIGNUP EMAIL
            print("  1️⃣ Testing Signup Email...")
            test_signup_email(activity)
            
            # Test 2: NEW PASS EMAIL  
            print("  2️⃣ Testing New Pass Email...")
            test_new_pass_email(activity)
            
            # Test 3: PAYMENT RECEIVED EMAIL
            print("  3️⃣ Testing Payment Received Email...")
            test_payment_email(activity)
            
            # Test 4: LATE PAYMENT EMAIL
            print("  4️⃣ Testing Late Payment Email...")
            test_late_payment_email(activity)
            
        print("\n" + "="*60)
        print("✅ ALL EMAILS SENT TO: " + TEST_EMAIL)
        print("CHECK FOR:")
        print("  - NO attachments (all images inline)")
        print("  - Activity images as heroes (except signup)")
        print("  - Professional circular styling")
        print("="*60)

def test_signup_email(activity):
    # Create test signup
    user = get_or_create_test_user()
    signup = Signup(
        user_id=user.id,
        activity_id=activity.id,
        subject=f"Ultimate Test - Signup - {activity.name}",
        signed_up_at=datetime.now(timezone.utc)
    )
    db.session.add(signup)
    db.session.commit()
    
    # Send email
    with app.test_request_context():
        notify_signup_event(app, signup=signup, activity=activity)
    print(f"    ✅ Signup email sent for {activity.name}")

def test_new_pass_email(activity):
    user = get_or_create_test_user()
    pass_data = create_test_passport(user, activity)
    
    # Send new pass email
    notify_pass_event(
        pass_data, activity, 
        app.config.get('ADMIN_EMAIL'), 
        event_type='pass_created'
    )
    print(f"    ✅ New Pass email sent for {activity.name}")

def test_payment_email(activity):
    user = get_or_create_test_user()
    pass_data = create_test_passport(user, activity, paid=True)
    
    # Send payment received email
    notify_pass_event(
        pass_data, activity,
        app.config.get('ADMIN_EMAIL'),
        event_type='payment_received'
    )
    print(f"    ✅ Payment Received email sent for {activity.name}")

def test_late_payment_email(activity):
    user = get_or_create_test_user()
    pass_data = create_test_passport(user, activity, paid=False)
    
    # Send late payment email
    notify_pass_event(
        pass_data, activity,
        app.config.get('ADMIN_EMAIL'),
        event_type='payment_late'
    )
    print(f"    ✅ Late Payment email sent for {activity.name}")

def get_or_create_test_user():
    user = User.query.filter_by(email=TEST_EMAIL).first()
    if not user:
        user = User(
            name=TEST_USER_NAME,
            email=TEST_EMAIL,
            phone_number="+1(514)555-0001"
        )
        db.session.add(user)
        db.session.commit()
    return user

def create_test_passport(user, activity, paid=False):
    # Implementation creates test passport
    pass

if __name__ == "__main__":
    test_all_email_templates()
```

### Phase 4: MCP Playwright Browser Testing (15 mins)
**Agent**: flask-ui-developer  
**Server**: localhost:5000  
**Credentials**: kdresdell@gmail.com / admin123  

#### Browser Test Scenarios:
1. **Upload Custom Hero Test**
   - Navigate to Activity 4 email templates
   - Upload custom hero for payment template
   - Trigger payment email
   - Screenshot: `/test/playwright/custom_hero_test.png`

2. **Remove Custom Hero Test**
   - Remove custom hero image
   - Trigger payment email again
   - Verify activity image used instead
   - Screenshot: `/test/playwright/activity_hero_fallback.png`

3. **All Templates Visual Test**
   - Trigger all 4 email types
   - Capture screenshots of each
   - Save to: `/test/playwright/email_[template]_[activity].png`

### Phase 5: Validation Checklist (10 mins)

#### CRITICAL SUCCESS CRITERIA - ALL MUST PASS:
- [ ] ✅ **NO ATTACHMENTS** in ANY email sent to kdresdell@gmail.com
- [ ] ✅ Signup email shows celebration hero (not activity image)
- [ ] ✅ Payment email shows activity image as circle (or custom if uploaded)
- [ ] ✅ New Pass email shows activity image as circle (or custom)
- [ ] ✅ Late Payment email shows activity image as circle (or custom)
- [ ] ✅ All inline images render correctly
- [ ] ✅ Organization logo is inline (not attached)
- [ ] ✅ Activity 1 (Hockey) - all emails perfect
- [ ] ✅ Activity 3 (Golf) - all emails perfect  
- [ ] ✅ Activity 4 (Poker) - all emails perfect
- [ ] ✅ Custom hero upload works when configured
- [ ] ✅ Fallback to activity image works
- [ ] ✅ No regression in existing functionality

### Phase 6: Rollback Plan

If ANY test fails:
```bash
# Immediate rollback
cp /test/backup_utils_[timestamp].py utils.py
# Restart Flask (already running in debug mode, will auto-reload)
# All emails return to previous behavior instantly
```

## Test Execution Instructions

### Automated Test Runner
```bash
# Run from app directory
cd /home/kdresdell/Documents/DEV/minipass_env/app

# Activate environment
source venv/bin/activate

# Run comprehensive test suite
python test/test_ultimate_email_customization.py

# This will send 12 test emails to kdresdell@gmail.com:
# - 3 activities × 4 email types = 12 emails
# Check each one for attachments and correct rendering
```

### Manual Verification
1. Check kdresdell@gmail.com inbox
2. Open each of the 12 test emails
3. Verify NO attachments (especially no .png files)
4. Verify heroes display correctly:
   - Signup: Celebration image
   - Others: Activity image in circle (or custom)
5. Take screenshots of any issues

## Agent Responsibilities

| Agent | Tasks | Time | Success Metrics |
|-------|-------|------|-----------------|
| general-purpose | Backup, test suite creation | 25 min | All files backed up, tests run |
| backend-architect | Core implementation | 30 min | Functions created, logic updated |
| flask-ui-developer | Browser testing with MCP | 15 min | Screenshots captured, UI verified |
| code-security-reviewer | Final review | 10 min | No vulnerabilities introduced |

## Risk Mitigation

1. **Backup Everything** - Full utils.py and templates backup before starting
2. **Test Incrementally** - Test each change before moving to next
3. **Use Real Email** - MUST test with kdresdell@gmail.com to verify attachments
4. **Activity Variety** - Test with different activity types (sports, events)
5. **Rollback Ready** - One command rollback if needed

## Expected Outcome

After implementation:
- **Professional Emails** - Every activity has branded emails automatically
- **Zero Configuration** - Works out of the box for new activities
- **Full Customization** - Users can still override with custom heroes
- **No Attachments** - All images inline, clean email experience
- **Better UX** - Activity managers see their branding, not generic icons

## Final Notes

- **CRITICAL**: All tests MUST use kdresdell@gmail.com
- **CRITICAL**: Verify NO attachments in any email
- **CRITICAL**: Test all 4 email templates for each activity
- **Server**: Flask running on localhost:5000 (already up)
- **Total emails to check**: 12 (3 activities × 4 templates)

This plan ensures we enhance the email system while maintaining stability and providing immediate rollback capability if needed.