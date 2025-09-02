# Fix Email Inline Images - Implementation Plan

**Created**: December 2, 2024
**Issue**: Email images appearing as attachments instead of inline
**Impact**: Poor user experience with broken image display in emails

## Problem Summary

Emails are being sent with correct French subjects BUT images (logo, checkmark, Facebook, Instagram icons) are appearing as attachments instead of displaying inline in the email body. The compiled templates use CID (Content-ID) references but the inline_images.json is not being loaded properly.

## Root Cause

The `notify_pass_event()` function is:
1. Using non-compiled template paths (`newPass/index.html` instead of `newPass_compiled/index.html`)
2. Not loading the `inline_images.json` file that contains properly encoded images with CID mappings
3. Only passing `qr_code` and `logo_image` instead of all required images (`ticket`, `facebook`, `instagram`)

## Solution: Smart On-Demand Approach

Use pre-compiled templates with their inline_images.json files while preserving activity-specific text customizations. This is the lightest solution with minimal resource usage.

## Agent Assignment

### Recommended Agent: **backend-architect**

**Why backend-architect is best:**
- Expert in Python/Flask backend logic
- Understands email systems and MIME encoding
- Can handle file I/O and JSON processing
- Familiar with template rendering

## Critical Environment Information

### MUST READ FIRST - Environment Setup:
- **Flask Server**: ALREADY RUNNING on `localhost:5000` in debug mode (DO NOT start a new one!)
- **Database**: SQLite at `instance/minipass.db`
- **Virtual Environment**: Already activated at `venv/`
- **MCP Playwright**: Available for browser testing

### Testing Credentials:
- **Admin Login URL**: `http://localhost:5000/login`
- **Admin Email**: `kdresdell@gmail.com`
- **Admin Password**: `admin123`
- **Test Email Recipient**: `kdresdell@gmail.com` (MUST use this for real email testing)
- **Test Activity**: Activity 4 (Tournois de Pocker - FLHGI) - Has French templates

## Implementation Tasks

### 1. Fix notify_pass_event() function (utils.py line ~1604-1652)

**Current Issue:**
```python
theme = template_mapping.get(event_type, 'newPass/index.html')
inline_images = {
    "qr_code": qr_data,
    "logo_image": open("static/uploads/logo.png", "rb").read()
}
```

**Fix Required:**
```python
# Use compiled template paths
template_mapping = {
    'pass_created': 'newPass_compiled/index.html',
    'payment_received': 'paymentReceived_compiled/index.html',
    'payment_late': 'latePayment_compiled/index.html',
    'pass_redeemed': 'redeemPass_compiled/index.html'
}
theme = template_mapping.get(event_type, 'newPass_compiled/index.html')

# Load compiled inline_images.json
import json
import base64
compiled_folder = theme.replace('/index.html', '')
json_path = os.path.join('templates/email_templates', compiled_folder, 'inline_images.json')

inline_images = {}
if os.path.exists(json_path):
    with open(json_path, 'r') as f:
        compiled_images = json.load(f)
        for cid, img_base64 in compiled_images.items():
            inline_images[cid] = base64.b64decode(img_base64)
    print(f"Loaded {len(inline_images)} inline images from compiled template")

# Add dynamic content (QR code must be generated per passport)
inline_images['qr_code'] = qr_data
inline_images['logo_image'] = open("static/uploads/logo.png", "rb").read()
```

### 2. Fix notify_signup_event() function (utils.py line ~1487)

**Current Issue:**
```python
theme = "signup/index.html"
```

**Fix Required:**
```python
theme = "signup_compiled/index.html"

# Load inline_images.json
compiled_folder = theme.replace('/index.html', '')
json_path = os.path.join('templates/email_templates', compiled_folder, 'inline_images.json')

inline_images = {}
if os.path.exists(json_path):
    with open(json_path, 'r') as f:
        compiled_images = json.load(f)
        for cid, img_base64 in compiled_images.items():
            inline_images[cid] = base64.b64decode(img_base64)
```

### 3. Fix send_survey_invitations() (app.py line ~6106)

**Current Issue:**
```python
template_name = 'email_survey_invitation/index.html'
```

**Fix Required:**
```python
template_name = 'email_survey_invitation_compiled/index.html'
# Similar inline_images.json loading logic
```

## Unit Test Requirements

### Create `/test/test_email_inline_images.py`:

```python
import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Activity, Passport, User
from utils import notify_pass_event
import json
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

class TestEmailInlineImages(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
    def test_compiled_template_path_used(self):
        """Test that compiled template paths are used"""
        with patch('utils.send_email_async') as mock_send:
            # Create test passport
            activity = Activity.query.get(4)  # Activity 4 has French templates
            user = User.query.filter_by(email='kdresdell@gmail.com').first()
            
            if user and activity:
                passport = Passport.query.filter_by(
                    user_id=user.id,
                    activity_id=activity.id
                ).first()
                
                if passport:
                    # Call notify_pass_event
                    notify_pass_event(
                        app=self.app,
                        activity=activity,
                        event_type='pass_created',
                        pass_data=passport,
                        admin_email='test@admin.com',
                        timestamp=datetime.now(timezone.utc)
                    )
                    
                    # Check that compiled template was used
                    mock_send.assert_called_once()
                    args = mock_send.call_args[1]
                    self.assertIn('compiled', args['template_name'])
                    
    def test_inline_images_loaded(self):
        """Test that inline_images.json is loaded"""
        json_path = 'templates/email_templates/newPass_compiled/inline_images.json'
        self.assertTrue(os.path.exists(json_path), "Compiled inline_images.json should exist")
        
        with open(json_path, 'r') as f:
            images = json.load(f)
            # Should have ticket, facebook, instagram
            self.assertIn('ticket', images)
            self.assertIn('facebook', images)
            self.assertIn('instagram', images)
            
    def test_cid_references_in_template(self):
        """Test that compiled template has CID references"""
        template_path = 'templates/email_templates/newPass_compiled/index.html'
        with open(template_path, 'r') as f:
            content = f.read()
            self.assertIn('cid:ticket', content)
            self.assertIn('cid:facebook', content)
            self.assertIn('cid:instagram', content)
            self.assertIn('cid:qr_code', content)

if __name__ == '__main__':
    unittest.main()
```

## MCP Playwright Integration Test

### Create `/test/test_email_images_playwright.py`:

```python
# This test will:
# 1. Login to Flask app at localhost:5000
# 2. Create a passport for Activity 4
# 3. Check database for email status
# 4. Take screenshot of success message

# IMPORTANT: Run this AFTER implementing the fix
# python test/test_email_images_playwright.py

# The test should:
# - Navigate to http://localhost:5000/login
# - Login with kdresdell@gmail.com / admin123
# - Go to create passport for Activity 4
# - Fill form with test user data
# - Submit and verify success
# - Check email_log table for SENT status
# - Save screenshot to /test/playwright/email_fix_success.png
```

## Testing Instructions for Agent

### Step 1: Implement the fixes
1. Update utils.py notify_pass_event() function
2. Update utils.py notify_signup_event() function  
3. Update app.py send_survey_invitations() function
4. Save all files

### Step 2: Run unit tests
```bash
cd /home/kdresdell/Documents/DEV/minipass_env/app
python test/test_email_inline_images.py -v
```

### Step 3: Test with real email
1. Use MCP Playwright to navigate to `http://localhost:5000/login`
2. Login with email: `kdresdell@gmail.com` password: `admin123`
3. Create a passport for Activity 4 (Tournois de Pocker - FLHGI)
4. Use email: `kdresdell@gmail.com` for the user
5. Submit the form
6. Check database: `sqlite3 instance/minipass.db "SELECT timestamp, subject, result FROM email_log ORDER BY timestamp DESC LIMIT 1;"`
7. Result should be "SENT" not "FAILED"

### Step 4: Verify email content
The email sent to kdresdell@gmail.com should:
- Have French subject: "LHGI 🎟️ Votre passe numérique est prête !"
- Display logo inline (not as attachment)
- Display checkmark icon inline
- Display QR code inline
- Display Facebook/Instagram icons inline at bottom
- Have ZERO attachments

## Common Pitfalls to Avoid

1. **DO NOT** start a new Flask server - use existing on port 5000
2. **DO NOT** forget to load inline_images.json
3. **DO NOT** overwrite compiled images with empty dict
4. **DO NOT** use non-compiled template paths
5. **MUST** decode base64 images from JSON before passing to send_email
6. **MUST** preserve dynamic QR code generation

## Expected Outcome

After implementation:
- ✅ All images display inline in email body
- ✅ No image attachments in email
- ✅ French customizations still work for Activity 4
- ✅ Email status is "SENT" not "FAILED"
- ✅ Professional looking emails with proper branding

## Rollback Plan

If issues occur:
1. Revert changes to utils.py and app.py
2. Touch app.py to trigger Flask reload
3. System returns to current state (working but with attachments)

---

*This plan ensures emails display beautifully with inline images as originally intended.*