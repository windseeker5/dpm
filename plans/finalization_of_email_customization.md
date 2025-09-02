# Plan: Finalization of Email Customization
**Created:** 2025-01-09  
**Objective:** Merge beautiful compiled email templates with user customization tool while preserving email blocks  
**Estimated Total Time:** 4-6 hours  

## Problem Statement
- Beautiful, professionally designed compiled email templates exist with QR codes, cards, easter eggs, and **email blocks**
- New customization tool bypasses these templates and generates ugly plain HTML
- Users must redefine everything from scratch instead of customizing existing designs
- **Critical: Email blocks (owner_html, history_html) must be preserved**

## Solution Overview
Use beautiful compiled templates as the foundation, with user customizations applied as variable replacements within the compiled template structure. Keep all design elements (QR codes, cards, styling, **email blocks**) intact while allowing text/image customization.

## ⚠️ CRITICAL ARCHITECTURE UNDERSTANDING
### Email Template Structure:
1. **Main Templates** (`templates/email_templates/*/index.html`) - Source designs
2. **Compiled Templates** (`templates/email_templates/*_compiled/index.html`) - Production-ready with inline images
3. **Email Blocks** (`templates/email_blocks/`) - Modular components:
   - `owner_card_inline.html` - Beautiful owner/activity card
   - `history_table_inline.html` - Pass history display
   - These are rendered separately and injected as `{{ owner_html | safe }}` and `{{ history_html | safe }}`

### Sacred Elements (NEVER MODIFY):
- Email blocks rendering logic
- Block template files
- Block injection points in compiled templates
- Inline image system

## Infrastructure & Credentials

### Available Servers
- **Flask Server:** `http://localhost:5000` (Always running in debug mode)
- **MCP Playwright:** Available for browser testing
- **Database:** SQLite at `instance/minipass.db`

### Test Credentials
- **Admin Login:** Check session for admin access
- **Test Email:** kdresdell@gmail.com (hardcoded for ALL email tests)
- **Test Activity ID:** 3 (from URL provided)

### Critical Constraints
- **NO JavaScript development** - Python-first approach only
- **Minimal JavaScript** - Only if absolutely necessary (<10 lines per function)
- **Use existing Flask server** - Never start new servers (already running on 5000)
- **Test with MCP Playwright** - For UI testing
- **Unit tests with unittest** - Python unittest framework
- **PRESERVE EMAIL BLOCKS** - Never modify block rendering

---

## Phase 1: Verification & Analysis
**Agent:** backend-architect  
**Time:** 30-45 minutes  

### Tasks:
1. **Verify compiled template structure with blocks**
   ```bash
   # Check for block placeholders in compiled templates
   grep -n "owner_html\|history_html" templates/email_templates/newPass_compiled/index.html
   grep -n "owner_html\|history_html" templates/email_templates/paymentReceived_compiled/index.html
   ```

2. **Verify email blocks rendering**
   ```python
   # Test block rendering in Python shell
   from flask import render_template
   from app import app
   
   with app.app_context():
       # Test owner block renders
       owner_html = render_template("email_blocks/owner_card_inline.html", 
                                   pass_data={"activity": {"name": "Test Activity"}})
       print("Owner block renders:", len(owner_html) > 0)
   ```

3. **Test current email flow with blocks**
   ```bash
   # Send test email to verify blocks appear
   curl -X POST http://localhost:5000/activity/3/email-test \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "template_type=newPass"
   # Check kdresdell@gmail.com for email with blocks
   ```

4. **Document template variables**
   - List all variables in each compiled template
   - Confirm block injection points: `{{ owner_html | safe }}`, `{{ history_html | safe }}`
   - Note which templates use which blocks

### Unit Test:
```python
# test/test_email_blocks.py
import unittest
from app import app
from flask import render_template

class TestEmailBlocks(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def test_owner_block_renders(self):
        """Test owner card block renders correctly"""
        pass_data = {
            "activity": {"name": "Soccer League"},
            "user": {"name": "John Doe", "email": "john@example.com"}
        }
        html = render_template("email_blocks/owner_card_inline.html", pass_data=pass_data)
        self.assertIn("Soccer League", html)
        self.assertIn("John Doe", html)
    
    def tearDown(self):
        self.app_context.pop()

# Run: python -m unittest test.test_email_blocks -v
```

### Deliverables:
- Confirmation all blocks render correctly
- List of templates using blocks
- Verification blocks appear in test emails

---

## Phase 2: Core Implementation
**Agent:** backend-architect  
**Time:** 2-3 hours  

### Task A: Update Email Context Building (utils.py)
**File:** `utils.py`  
**Lines:** 1893-1932 (get_email_context function)  

```python
def get_email_context(activity, template_type, base_context=None):
    """
    Merge activity email template customizations with default values
    PRESERVING EMAIL BLOCKS
    """
    # ... existing defaults code ...
    
    # CRITICAL: Preserve email blocks if they exist in base_context
    if base_context:
        # These must NEVER be overwritten by customizations
        if 'owner_html' in base_context:
            context['owner_html'] = base_context['owner_html']
        if 'history_html' in base_context:
            context['history_html'] = base_context['history_html']
    
    # Apply activity customizations (but never override blocks)
    if activity and activity.email_templates:
        template_customizations = activity.email_templates.get(template_type, {})
        for key, value in template_customizations.items():
            # NEVER override email blocks
            if key not in ['owner_html', 'history_html']:
                if value is not None and value != '':
                    context[key] = value
    
    return context
```

### Task B: Fix Test Email Function (app.py)
**File:** `app.py`  
**Lines:** 6646-6786 (test_email_template function)  

```python
# Around line 6700, build proper context with blocks
from flask import render_template
from utils import get_email_context, send_email

# Create base context with sample data
base_context = {
    'user_name': 'Test User',
    'user_email': 'test@example.com',
    'activity_name': activity.name,
    'pass_code': 'TEST123',
}

# Add email blocks if needed for this template type
if template_type in ['newPass', 'paymentReceived', 'redeemPass']:
    # Render email blocks with test data
    pass_data = {
        'activity': activity,
        'user': {'name': 'Test User', 'email': 'test@example.com'},
        'pass_code': 'TEST123'
    }
    base_context['owner_html'] = render_template("email_blocks/owner_card_inline.html", 
                                                 pass_data=pass_data)
    
    # Add history if needed
    if template_type == 'redeemPass':
        history = [{'date': '2025-01-09', 'action': 'Pass Created'}]
        base_context['history_html'] = render_template("email_blocks/history_table_inline.html", 
                                                       history=history)

# Merge with activity customizations
context = get_email_context(activity, template_type, base_context)

# Send using compiled template
result = send_email(
    subject=context.get('subject', f'Test: {template_type}'),
    to_email="kdresdell@gmail.com",
    template_name=template_type,  # Will auto-select compiled version
    context=context,
    inline_images=inline_images  # Load from compiled template
)
```

### Task C: Fix Email Preview (app.py)
**File:** `app.py`  
**Lines:** 6566-6643 (email_preview function)  

```python
# Around line 6576, create proper preview with blocks
from flask import render_template
from utils import safe_template, get_email_context

# Build base context with sample data
base_context = {
    'user_name': 'John Doe',
    'user_email': 'john.doe@example.com',
    'activity_name': activity.name,
    'pass_code': 'SAMPLE123',
    'amount': '$50.00'
}

# Add email blocks for preview
if template_type in ['newPass', 'paymentReceived', 'redeemPass']:
    pass_data = {
        'activity': activity,
        'user': {'name': 'John Doe', 'email': 'john.doe@example.com'},
        'pass_code': 'SAMPLE123'
    }
    base_context['owner_html'] = render_template("email_blocks/owner_card_inline.html", 
                                                 pass_data=pass_data)
    
    if template_type == 'redeemPass':
        history = [
            {'date': '2025-01-09', 'action': 'Pass Created'},
            {'date': '2025-01-10', 'action': 'Pass Redeemed'}
        ]
        base_context['history_html'] = render_template("email_blocks/history_table_inline.html", 
                                                       history=history)

# Get merged context with customizations
context = get_email_context(activity, template_type, base_context)

# Use actual compiled template for preview
template_path = safe_template(template_type)
preview_html = render_template(template_path, **context)

return preview_html
```

### Unit Tests:
```python
# test/test_email_customization.py
import unittest
from app import app, db
from models import Activity
from utils import get_email_context
from flask import render_template

class TestEmailCustomization(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def test_blocks_preserved_in_context(self):
        """Test email blocks are never overwritten by customizations"""
        activity = Activity.query.get(3)
        
        # Set up base context with blocks
        base_context = {
            'owner_html': '<div>OWNER BLOCK</div>',
            'history_html': '<div>HISTORY BLOCK</div>',
            'title': 'Original Title'
        }
        
        # Add customizations to activity
        activity.email_templates = {
            'newPass': {
                'title': 'Custom Title',
                'owner_html': 'SHOULD NOT OVERRIDE',  # This should be ignored
                'intro_text': 'Custom intro'
            }
        }
        
        # Get merged context
        context = get_email_context(activity, 'newPass', base_context)
        
        # Verify blocks preserved, other customizations applied
        self.assertEqual(context['owner_html'], '<div>OWNER BLOCK</div>')
        self.assertEqual(context['history_html'], '<div>HISTORY BLOCK</div>')
        self.assertEqual(context['title'], 'Custom Title')
        self.assertEqual(context['intro_text'], 'Custom intro')
    
    def test_email_preview_includes_blocks(self):
        """Test email preview renders with blocks"""
        with self.client.session_transaction() as sess:
            sess['admin'] = 1
        
        response = self.client.get('/activity/3/email-preview?type=newPass')
        self.assertEqual(response.status_code, 200)
        # Check for owner card class from block
        self.assertIn('owner_card', response.data.decode())
    
    def tearDown(self):
        self.app_context.pop()

# Run: python -m unittest test.test_email_customization -v
```

---

## Phase 3: Send Email Function Updates
**Agent:** backend-architect  
**Time:** 1 hour  

### Task: Ensure send_email uses compiled templates correctly
**File:** `utils.py`  
**Lines:** 1178-1312 (send_email function)  

```python
def send_email(subject, to_email, template_name=None, context=None, inline_images=None, html_body=None, timestamp_override=None, email_config=None):
    # ... existing setup code ...
    
    if html_body:
        final_html = html_body
    else:
        if template_name and context:
            # ALWAYS use safe_template to get compiled version
            actual_template = safe_template(template_name)
            
            # Load inline images if using compiled template
            if '_compiled' in actual_template and not inline_images:
                compiled_dir = actual_template.replace('/index.html', '')
                json_path = os.path.join('templates', compiled_dir, 'inline_images.json')
                if os.path.exists(json_path):
                    with open(json_path, 'r') as f:
                        inline_images = json.load(f)
            
            # Render with full context including blocks
            final_html = render_template(actual_template, **context)
        else:
            final_html = "No content."
    
    # ... rest of function ...
```

### Testing Script:
```bash
#!/bin/bash
# test_email_flow.sh

echo "Testing Email Customization Flow"
echo "================================"

# 1. Test default email (no customizations)
echo "1. Testing default email..."
curl -X POST http://localhost:5000/activity/3/email-test \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "template_type=newPass" \
     -w "\nStatus: %{http_code}\n"

echo "Check kdresdell@gmail.com for email with:"
echo "  - Beautiful compiled template"
echo "  - Owner card block"
echo "  - QR code"
echo ""

# 2. Test customized email
echo "2. Adding customizations..."
curl -X POST http://localhost:5000/activity/3/email-templates/save \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "newPass_title=Welcome to Soccer 2025!&newPass_intro_text=Your season starts soon!" \
     -w "\nStatus: %{http_code}\n"

# 3. Test customized email
echo "3. Testing customized email..."
curl -X POST http://localhost:5000/activity/3/email-test \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "template_type=newPass" \
     -w "\nStatus: %{http_code}\n"

echo "Check kdresdell@gmail.com for email with:"
echo "  - Custom title: 'Welcome to Soccer 2025!'"
echo "  - Custom intro: 'Your season starts soon!'"
echo "  - Owner card block (unchanged)"
echo "  - QR code (unchanged)"
```

---

## Phase 4: Browser Testing with MCP Playwright
**Agent:** js-code-reviewer (ONLY for testing, NO JavaScript development)  
**Time:** 1 hour  

### MCP Playwright Test Sequence:
```python
# Navigate to email customization page
mcp_playwright.browser_navigate("http://localhost:5000/activity/3/email-templates")

# Take screenshot of current state
mcp_playwright.browser_take_screenshot("email_customization_before.png")

# Fill in customization form
mcp_playwright.browser_fill_form([
    {"name": "newPass_title", "type": "textbox", "ref": "[id='newPass_title']", "value": "Welcome to Soccer League 2025!"},
    {"name": "newPass_intro_text", "type": "textbox", "ref": "[id='newPass_intro_text']", "value": "Get ready for an amazing season!"},
    {"name": "newPass_custom_message", "type": "textbox", "ref": "[id='newPass_custom_message']", "value": "Remember to bring your gear!"}
])

# Save customizations
mcp_playwright.browser_click("Save Templates", "[type='submit']")

# Wait for success message
mcp_playwright.browser_wait_for(text="Email templates saved successfully")

# Test preview
mcp_playwright.browser_navigate("http://localhost:5000/activity/3/email-preview?type=newPass")

# Take screenshot of preview
mcp_playwright.browser_take_screenshot("email_preview_customized.png")

# Verify blocks appear in preview
mcp_playwright.browser_snapshot()  # Check for owner card and design elements

# Send test email
mcp_playwright.browser_navigate("http://localhost:5000/activity/3/email-templates")
mcp_playwright.browser_click("Send Test Email", "[onclick*='newPass']")

# Verify success
mcp_playwright.browser_wait_for(text="Test email sent")
```

---

## Phase 5: Full Integration Testing
**Agent:** backend-architect  
**Time:** 30 minutes  

### Complete Test Checklist:
1. ✅ All 6 email types working with compiled templates
2. ✅ Email blocks (owner_html, history_html) render correctly
3. ✅ Customizations apply without breaking blocks
4. ✅ QR codes and inline images work
5. ✅ Default templates look professional
6. ✅ Preview shows actual compiled template
7. ✅ Test emails arrive at kdresdell@gmail.com
8. ✅ No JavaScript added (Python-only solution)

### Final Validation Script:
```python
# test/test_complete_email_flow.py
import unittest
from app import app, db
from models import Activity
import time

class TestCompleteEmailFlow(unittest.TestCase):
    def test_all_email_types(self):
        """Test all 6 email types with blocks and customizations"""
        
        templates = ['newPass', 'paymentReceived', 'latePayment', 
                    'signup', 'redeemPass', 'survey_invitation']
        
        for template_type in templates:
            with self.subTest(template=template_type):
                # Test email sends successfully
                response = self.client.post(f'/activity/3/email-test',
                                           data={'template_type': template_type})
                self.assertEqual(response.status_code, 302)  # Redirect after success
                
                print(f"✅ {template_type} email sent to kdresdell@gmail.com")
                time.sleep(2)  # Avoid rate limiting

# Run: python -m unittest test.test_complete_email_flow -v
```

---

## Success Criteria
✅ Beautiful compiled templates used by default  
✅ Email blocks preserved and working  
✅ User customizations work without breaking design  
✅ QR codes, cards, easter eggs preserved  
✅ Zero effort required for basic use  
✅ No JavaScript implementation (Python-only)  
✅ All tests passing  
✅ Emails arrive at kdresdell@gmail.com with correct content  

## Rollback Plan
If issues arise:
1. Git revert to previous commit
2. Original templates remain untouched in `email_templates/*/`
3. Email blocks remain untouched in `email_blocks/`
4. Customization data stored separately in database

## ⚠️ CRITICAL REMINDERS
- **NEVER modify email blocks** (`owner_card_inline.html`, `history_table_inline.html`)
- **NEVER override block variables** (`owner_html`, `history_html`) with customizations
- **ALWAYS preserve block rendering logic** in context building
- **NO JavaScript development** - Python only
- **Use existing Flask server** on port 5000
- **ALL test emails** go to kdresdell@gmail.com
- **Test with real activity** (ID: 3)

## Command Reference
```bash
# Virtual environment
source venv/bin/activate

# Run all email tests
python -m unittest discover test -p "test_email*.py" -v

# Check Flask server
curl http://localhost:5000/

# View email customization UI
open http://localhost:5000/activity/3/email-templates

# Database check for customizations
sqlite3 instance/minipass.db "SELECT email_templates FROM activity WHERE id=3;"

# Grep for block usage
grep -r "owner_html\|history_html" templates/email_templates/*_compiled/

# Test single email type
curl -X POST http://localhost:5000/activity/3/email-test \
     -d "template_type=newPass"
```

---

**End of Plan**  
*Estimated Total Time: 4-6 hours*  
*Priority: High - Core functionality improvement*  
*Critical: Preserve email blocks architecture*