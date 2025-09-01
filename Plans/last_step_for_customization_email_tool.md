# Last Step for Email Customization Tool
## Copy Global Email Settings as Default for New Activities

### 📋 Task Overview
**Purpose**: Automatically populate email templates for new activities using the configured global email settings, ensuring every new activity has professional, working emails from day one.

**Duration**: 2-3 hours
**Assigned Agent**: backend-architect (for implementation) + js-code-reviewer (for testing)

---

## 🎯 The Problem Solved
Currently, when creating a new activity, the email templates start empty. Users must manually configure each template. This plan will automatically copy the global email settings (already configured in Settings > Email Templates) as the default for each new activity.

---

## 🔧 Implementation Plan

### Step 1: Create Copy Function (30 minutes)
**File**: `/home/kdresdell/Documents/DEV/minipass_env/app/utils.py`
**Agent**: backend-architect

Add new function around line 1935 (after `get_email_context`):

```python
def copy_global_email_templates_to_activity():
    """
    Copy all global email template settings to create default 
    activity-specific templates when creating a new activity
    
    Returns:
        dict: Email templates configuration for all 6 template types
    """
    from utils import get_setting
    
    # Map global settings to activity template structure
    return {
        'newPass': {
            'subject': get_setting('SUBJECT_pass_created', 'Your Digital Pass is Ready! 🎉'),
            'title': get_setting('HEADING_pass_created', 'Welcome!'),
            'intro_text': get_setting('INTRO_pass_created', 'Great news! Your digital pass has been created.'),
            'conclusion_text': get_setting('CONCLUSION_pass_created', 'We look forward to seeing you!'),
            'custom_message': get_setting('CUSTOM_MESSAGE_pass_created', ''),
            'cta_text': get_setting('CTA_TEXT_pass_created', 'View My Pass'),
            'cta_url': get_setting('CTA_URL_pass_created', 'https://minipass.me/my-passes'),
            # Hero image can be added if stored in settings
        },
        'paymentReceived': {
            'subject': get_setting('SUBJECT_payment_received', 'Payment Confirmed - Thank You!'),
            'title': get_setting('HEADING_payment_received', 'Payment Received'),
            'intro_text': get_setting('INTRO_payment_received', 'We have successfully received your payment.'),
            'conclusion_text': get_setting('CONCLUSION_payment_received', 'Thank you for your payment!'),
            'custom_message': get_setting('CUSTOM_MESSAGE_payment_received', ''),
        },
        'latePayment': {
            'subject': get_setting('SUBJECT_payment_late', 'Friendly Payment Reminder'),
            'title': get_setting('HEADING_payment_late', 'Payment Reminder'),
            'intro_text': get_setting('INTRO_payment_late', 'This is a friendly reminder about your pending payment.'),
            'conclusion_text': get_setting('CONCLUSION_payment_late', 'Please contact us if you have any questions.'),
            'custom_message': get_setting('CUSTOM_MESSAGE_payment_late', ''),
        },
        'signup': {
            'subject': get_setting('SUBJECT_signup', 'Registration Confirmed!'),
            'title': get_setting('HEADING_signup', 'Welcome Aboard!'),
            'intro_text': get_setting('INTRO_signup', 'Your registration has been confirmed.'),
            'conclusion_text': get_setting('CONCLUSION_signup', 'We are excited to have you join us!'),
            'custom_message': get_setting('CUSTOM_MESSAGE_signup', ''),
        },
        'redeemPass': {
            'subject': get_setting('SUBJECT_pass_redeemed', 'Pass Successfully Redeemed'),
            'title': get_setting('HEADING_pass_redeemed', 'Enjoy Your Activity!'),
            'intro_text': get_setting('INTRO_pass_redeemed', 'Your pass has been successfully redeemed.'),
            'conclusion_text': get_setting('CONCLUSION_pass_redeemed', 'Have a great time!'),
            'custom_message': get_setting('CUSTOM_MESSAGE_pass_redeemed', ''),
        },
        'survey_invitation': {
            'subject': get_setting('SUBJECT_survey_invitation', 'We Value Your Feedback'),
            'title': get_setting('HEADING_survey_invitation', 'Share Your Experience'),
            'intro_text': get_setting('INTRO_survey_invitation', 'We would love to hear about your experience.'),
            'conclusion_text': get_setting('CONCLUSION_survey_invitation', 'Thank you for helping us improve!'),
            'custom_message': get_setting('CUSTOM_MESSAGE_survey_invitation', ''),
            'cta_text': 'Take Survey',
            'cta_url': '{survey_url}'  # Will be replaced dynamically
        }
    }
```

### Step 2: Modify Activity Creation (15 minutes)
**File**: `/home/kdresdell/Documents/DEV/minipass_env/app/app.py`
**Line**: 1379-1388
**Agent**: backend-architect

Update the activity creation to include email templates:

```python
# Import the new function at top of create_activity function
from utils import copy_global_email_templates_to_activity

# Modify the activity creation (line 1379)
new_activity = Activity(
    name=name,
    type=activity_type,
    description=description,
    start_date=start_date,
    end_date=end_date,
    status=status,
    created_by=session.get("admin"),
    image_filename=image_filename,
    email_templates=copy_global_email_templates_to_activity(),  # ADD THIS LINE
)
```

---

## 🧪 Testing Instructions

### Test Environment Setup
- **Server**: Flask debug server running on `localhost:5000`
- **Credentials**: 
  - Email: `kdresdell@gmail.com`
  - Password: `admin123`
- **Database**: SQLite at `instance/minipass.db`

### Unit Test (45 minutes)
**File**: `/home/kdresdell/Documents/DEV/minipass_env/app/test/test_email_template_defaults.py`
**Agent**: backend-architect

```python
#!/usr/bin/env python3
"""
Unit tests for email template default copying functionality
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Activity, Setting
from utils import copy_global_email_templates_to_activity

class TestEmailTemplateDefaults(unittest.TestCase):
    
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
    def tearDown(self):
        self.app_context.pop()
    
    def test_copy_global_templates_structure(self):
        """Test that copy function returns correct structure"""
        templates = copy_global_email_templates_to_activity()
        
        # Check all 6 template types exist
        expected_types = ['newPass', 'paymentReceived', 'latePayment', 
                         'signup', 'redeemPass', 'survey_invitation']
        for template_type in expected_types:
            self.assertIn(template_type, templates)
            
        # Check each template has required fields
        for template_type, config in templates.items():
            self.assertIn('subject', config)
            self.assertIn('title', config)
            self.assertIn('intro_text', config)
            self.assertIn('conclusion_text', config)
    
    def test_new_activity_gets_templates(self):
        """Test that new activities receive email templates"""
        # Login as admin
        self.client.post('/admin/login', data={
            'email': 'kdresdell@gmail.com',
            'password': 'admin123'
        })
        
        # Create new activity
        response = self.client.post('/create-activity', data={
            'name': 'Test Activity with Templates',
            'type': 'test',
            'description': 'Testing default templates',
            'status': 'active'
        })
        
        # Get the created activity
        activity = Activity.query.filter_by(name='Test Activity with Templates').first()
        if activity:
            # Check email_templates is populated
            self.assertIsNotNone(activity.email_templates)
            self.assertIn('newPass', activity.email_templates)
            self.assertIn('signup', activity.email_templates)
            
            # Clean up
            db.session.delete(activity)
            db.session.commit()

if __name__ == '__main__':
    unittest.main()
```

### Browser Test with MCP Playwright (30 minutes)
**File**: `/home/kdresdell/Documents/DEV/minipass_env/app/test/test_email_defaults_browser.py`
**Agent**: flask-ui-developer

1. Navigate to `http://localhost:5000/login`
2. Login with credentials above
3. Create new activity
4. Navigate to email templates for the new activity
5. Verify templates are pre-populated
6. Send test email to verify it works
7. Take screenshots at each step

### Manual Testing Checklist
1. ✅ Login to admin panel
2. ✅ Navigate to Settings > Email Templates
3. ✅ Verify global templates are configured
4. ✅ Create a new activity
5. ✅ Go to the new activity's email templates
6. ✅ Verify all 6 templates are pre-populated with settings values
7. ✅ Send a test email - should show styled content
8. ✅ Modify one template and save
9. ✅ Verify modification is saved per-activity

---

## 🚀 Deployment Notes

### Pre-deployment Checklist
- [ ] Run unit tests: `python test/test_email_template_defaults.py`
- [ ] Run browser tests with MCP Playwright
- [ ] Test on localhost:5000 with debug server
- [ ] Verify no existing activities are affected
- [ ] Backup database before deployment

### Rollback Plan
If issues occur, simply remove the `email_templates=copy_global_email_templates_to_activity()` line from activity creation. Existing activities won't be affected.

---

## 📊 Success Metrics
- New activities have email templates immediately
- Test emails send successfully with styling
- No manual template configuration needed
- Users can still customize if desired
- Zero impact on existing activities

---

## ⚠️ Important Notes
1. **Always use Flask debug server on port 5000** for testing
2. **Login credentials**: kdresdell@gmail.com / admin123
3. **Save all tests in `/test/` folder**
4. **Use backend-architect agent for Python code**
5. **Keep JavaScript minimal (<50 lines)**
6. **Test with real email sending to verify HTML formatting**

---

## 📝 Summary
This implementation ensures every new activity starts with professional, working email templates copied from your global settings. It's a one-time setup that saves hours of configuration for each new activity while maintaining full customization capability.