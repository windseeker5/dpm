# Email Template Frontend Customization Tool - Technical Guide

**Last Updated:** 2025-10-30
**Related Documentation:** `EMAIL_TEMPLATE_SYSTEM_GUIDE.md` (Backend compilation system)

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Components](#architecture-components)
3. [Reset to Default - Deep Dive](#reset-to-default---deep-dive)
4. [Hero Image Resolution System](#hero-image-resolution-system)
5. [Frontend-Backend Integration](#frontend-backend-integration)
6. [Complete User Workflow](#complete-user-workflow)
7. [Database Schema](#database-schema)
8. [Issues and Recommendations](#issues-and-recommendations)
9. [Testing and Validation](#testing-and-validation)

---

## System Overview

### Purpose
The Email Template Customization Tool allows activity managers to customize the six default email templates that Minipass sends to users. This frontend tool provides a visual interface for:

- Viewing all six email templates as cards
- Customizing text content (subject, title, intro, conclusion)
- Uploading custom hero images per template
- Uploading organization logo (shared across templates)
- Previewing changes before saving
- Sending test emails
- Resetting templates back to defaults

### The Six Email Templates

| Template Key | Display Name | Trigger Event |
|--------------|--------------|---------------|
| `newPass` | New Pass Created | When a digital pass is created for a user |
| `paymentReceived` | Payment Received | When payment is confirmed |
| `latePayment` | Late Payment Reminder | When payment is overdue |
| `signup` | Signup Confirmation | When user registers for an activity |
| `redeemPass` | Pass Redeemed | When user uses their pass |
| `survey_invitation` | Survey Invitation | When survey is sent to user |

### Frontend URL
```
/activity/<activity_id>/email-templates
```

Example: `http://localhost:5000/activity/1/email-templates`

---

## Architecture Components

### 1. Frontend Layer

#### Template File
**Location:** `templates/email_template_customization.html`

**Key Elements:**

```html
<!-- Template Cards Grid (Lines 39-147) -->
<div class="email-templates-grid" id="templateCardsGrid">
  - Displays 6 template cards
  - Shows mini preview with hero image
  - Shows "Custom" or "Default" status badge
  - Has "Customize" and "Reset" action buttons
</div>

<!-- Customize Modal (Lines 263-311) -->
<div class="modal fade" id="customizeModal">
  - Form fields for subject, title, intro, conclusion
  - Hero image upload with preview
  - Owner logo upload (shown only for first template)
  - TinyMCE rich text editors for intro/conclusion
  - Preview, Save, and Send Test buttons
</div>

<!-- Reset Confirmation Modal (Lines 164-188) -->
<div class="modal fade" id="resetConfirmModal">
  - Confirms reset action before proceeding
  - Shows template name being reset
  - Sends AJAX request to reset endpoint
</div>
```

#### JavaScript Logic
**Location:** Embedded in `email_template_customization.html` (Lines 432-817)

**Key Functions:**

1. **Customize Button Handler** (Lines 445-501)
   - Loads template-specific form content into modal
   - Initializes TinyMCE editors
   - Adds cache-busting to hero images
   - Updates modal title with template name

2. **Reset Button Handler** (Lines 495-543)
   - Shows confirmation modal
   - Sends POST request to `/activity/{id}/email-templates/reset`
   - Reloads page on success (displays Flask flash message)

3. **Save Button Handler** (Lines 688-750)
   - Collects form data including file uploads
   - Sends to `/activity/{id}/email-templates/save`
   - Reloads page on success

4. **Preview Button Handler** (Lines 596-684)
   - Sends current form data to `/activity/{id}/email-preview-live`
   - Opens preview HTML in new tab
   - Supports viewing changes before saving

5. **Test Email Handler** (Lines 753-815)
   - Sends test email with current unsaved changes
   - Posts to `/activity/{id}/email-test`

### 2. Backend Layer

#### Flask Routes
**Location:** `app.py`

##### Route 1: Display Customization Interface
```python
@app.route("/activity/<int:activity_id>/email-templates")
def email_template_customization(activity_id):
    # Lines 7667-7713
```

**What it does:**
1. Loads activity from database
2. Gets activity's `email_templates` JSON data (or empty dict)
3. Loads default values from `utils_email_defaults.py`
4. Merges custom values with defaults (custom takes priority)
5. Renders template with merged data

##### Route 2: Save Template Customizations
```python
@app.route("/activity/<int:activity_id>/email-templates/save", methods=["POST"])
def save_email_templates(activity_id):
    # Lines 7719-7932
```

**What it does:**
1. Validates admin session
2. Accepts either individual template save or bulk save
3. Processes hero image uploads:
   - Saves as `static/uploads/{activity_id}_{template_type}_hero.png`
   - Resizes to match template dimensions (uses `resize_hero_image()`)
4. Processes owner logo upload:
   - Saves as `static/uploads/{activity_id}_owner_logo.png`
   - Shared across all templates
5. Sanitizes text content (removes dangerous HTML)
6. Updates `activity.email_templates` JSON column
7. Marks SQLAlchemy JSON field as modified
8. Commits to database
9. Returns JSON response for AJAX or redirects for form submit

##### Route 3: Reset Template to Default
```python
@app.route("/activity/<int:activity_id>/email-templates/reset", methods=["POST"])
def reset_email_template(activity_id):
    # Lines 7934-8033
```

**What it does:** (See detailed investigation in next section)

##### Route 4: Get Hero Image
```python
@app.route('/activity/<int:activity_id>/hero-image/<template_type>')
def get_hero_image(activity_id, template_type):
    # Lines 8546-8588
```

**What it does:**
1. Calls `get_activity_hero_image(activity, template_type)` from utils
2. Returns image data with `Cache-Control: no-cache` header
3. Falls back to default hero if none found

##### Route 5: Live Preview
```python
@app.route('/activity/<int:activity_id>/email-preview-live', methods=['POST'])
def email_preview_live(activity_id):
    # Lines 8262+
```

**What it does:**
1. Accepts form data with unsaved changes
2. Temporarily saves uploaded hero image
3. Renders compiled email template with changes
4. Returns HTML for preview in new tab
5. Does NOT save to database

##### Route 6: Send Test Email
```python
@app.route("/activity/<int:activity_id>/email-test", methods=["POST"])
def test_email_template(activity_id):
    # Lines 8591+
```

**What it does:**
1. Accepts form data with unsaved changes
2. Renders compiled template with changes
3. Sends actual email to specified test address
4. Does NOT save to database

### 3. Utility Functions

#### Location: `utils.py`

##### Function: `get_activity_hero_image(activity, template_type)`
**Lines:** 124-189

**Purpose:** Resolves which hero image to display based on priority hierarchy

**Returns:** `(image_data, is_custom, is_template_default)`

(See detailed explanation in Hero Image Resolution System section)

##### Function: `get_email_context(activity, template_type, base_context)`
**Lines:** 3223-3273

**Purpose:** Merges activity customizations with default template values

**How it works:**
1. Starts with base context (if provided)
2. Applies default values for missing keys
3. Preserves protected email blocks (`owner_html`, `history_html`)
4. Overlays activity-specific customizations from `activity.email_templates`
5. Returns merged context for template rendering

##### Function: `get_template_default_hero(template_type)`
**Lines:** 58-118

**Purpose:** Loads pristine default hero image from original template

**How it works:**
1. Maps template type to `{template}_original` folder
2. Loads `inline_images.json` from original folder
3. Maps template type to hero key (e.g., 'newPass' → 'hero_new_pass')
4. Decodes base64 image data
5. Returns raw image bytes

#### Location: `utils_email_defaults.py`

##### Function: `get_default_email_templates()`
**Lines:** 9-76

**Purpose:** Loads default text content for all templates

**How it works:**
1. Tries to load from `config/email_defaults.json`
2. Falls back to hardcoded defaults if file missing
3. Returns dict with default subject, title, intro_text, conclusion_text for each template

### 4. Database Storage

#### Table: `activity`
**Column:** `email_templates` (JSON, nullable)

**Structure:**
```json
{
  "newPass": {
    "subject": "Your Digital Pass is Ready!",
    "title": "Welcome to Hockey League!",
    "intro_text": "<p>Your digital pass has been created...</p>",
    "conclusion_text": "<p>See you on the ice!</p>",
    "hero_image": "1_newPass_hero.png",
    "activity_logo": "1_owner_logo.png"
  },
  "paymentReceived": {
    "subject": "Payment Confirmed",
    ...
  },
  ...
}
```

**Notes:**
- Only stores CUSTOMIZED values
- Empty/null fields fall back to defaults
- Images stored as filenames (actual files in `static/uploads/`)
- JSON field must be flagged as modified for SQLAlchemy to detect changes

### 5. File System Storage

#### Hero Images (Template-Specific)
**Location:** `static/uploads/{activity_id}_{template_type}_hero.png`

**Examples:**
- `static/uploads/1_newPass_hero.png`
- `static/uploads/1_signup_hero.png`
- `static/uploads/1_survey_invitation_hero.png`

**Lifecycle:**
- Created when user uploads custom hero image
- Deleted when user clicks "Reset to Default"
- Resized to match template dimensions on upload

#### Owner Logo (Shared Across Templates)
**Location:** `static/uploads/{activity_id}_owner_logo.png`

**Example:**
- `static/uploads/1_owner_logo.png`

**Lifecycle:**
- Created when user uploads logo
- Overwrites existing file (no versioning)
- Deleted when resetting `newPass` template (first template with global settings)

#### Default Hero Images (Pristine)
**Location:** `templates/email_templates/{template}_original/inline_images.json`

**Examples:**
- `templates/email_templates/newPass_original/inline_images.json`
- `templates/email_templates/signup_original/inline_images.json`

**Format:** Base64-encoded images in JSON
```json
{
  "hero_new_pass": "iVBORw0KGgoAAAANS...",
  "currency-dollar": "iVBORw0KGgoAAAANS...",
  ...
}
```

---

## Reset to Default - Deep Dive

### What Users See

When a user clicks the "Reset to Default" button:
1. Confirmation modal appears: "Reset [Template Name] to default values?"
2. User clicks "Reset" button
3. Loading spinner appears
4. Page reloads with success message: "Template reset to defaults successfully!"
5. Template card shows "Default" badge instead of "Custom"
6. Hero image reverts to original template default

### What Happens Behind the Scenes

#### Frontend JavaScript (Lines 504-543)
```javascript
document.getElementById('confirmResetBtn').addEventListener('click', function() {
    const template = this.dataset.template;

    // Send reset request
    fetch(`/activity/{{ activity.id }}/email-templates/reset`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': '{{ csrf_token() }}'
        },
        body: JSON.stringify({template_type: template})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload(); // Reload page to show changes
        }
    });
});
```

#### Backend Route (app.py:7934-8033)

**Step-by-step execution:**

**Step 1: Validate Request** (Lines 7943-7962)
```python
activity = Activity.query.get_or_404(activity_id)
data = request.get_json()
template_type = data['template_type']

# Valid template types
valid_templates = ['newPass', 'paymentReceived', 'latePayment',
                   'signup', 'redeemPass', 'survey_invitation']
if template_type not in valid_templates:
    return jsonify({'success': False, 'message': 'Invalid template type'}), 400
```

**Step 2: Clear Database Customizations** (Lines 7968-7982)
```python
if template_type in activity.email_templates:
    template_data = activity.email_templates[template_type]

    # Clear the customizable fields while preserving any system fields
    fields_to_reset = ['subject', 'title', 'intro_text', 'conclusion_text',
                       'hero_image', 'activity_logo']
    for field in fields_to_reset:
        if field in template_data:
            del template_data[field]

    # If template data is now empty, remove the entire template entry
    if not template_data:
        del activity.email_templates[template_type]
```

**What this does:**
- Removes all custom text fields from database
- Removes image references from database
- Deletes entire template entry if no data left
- Template will now fall back to defaults from `utils_email_defaults.py`

**Step 3: Delete Physical Hero Image File** (Lines 7984-7993)
```python
import os
hero_file_path = f"static/uploads/{activity_id}_{template_type}_hero.png"
if os.path.exists(hero_file_path):
    try:
        os.remove(hero_file_path)
        print(f"✅ Deleted custom hero image file: {hero_file_path}")
    except Exception as e:
        print(f"⚠️ Could not delete hero image file {hero_file_path}: {e}")
```

**What this does:**
- Deletes the custom hero image file from disk
- Example: Deletes `static/uploads/1_newPass_hero.png`
- After deletion, hero image resolution falls back to original template default
- Errors are logged but don't stop the reset process

**Step 4: Delete Owner Logo (newPass Only)** (Lines 7995-8002)
```python
owner_logo_path = f"static/uploads/{activity_id}_owner_logo.png"
if template_type == 'newPass' and os.path.exists(owner_logo_path):
    try:
        os.remove(owner_logo_path)
        print(f"✅ Deleted custom owner logo file: {owner_logo_path}")
    except Exception as e:
        print(f"⚠️ Could not delete owner logo file {owner_logo_path}: {e}")
```

**What this does:**
- Only runs when resetting `newPass` (first template with global settings)
- Deletes shared owner logo file
- Example: Deletes `static/uploads/1_owner_logo.png`
- Logo affects all templates but is only deleted once

**Step 5: Restore Original Compiled Template** (Lines 8004-8018)
```python
original_dir = f"templates/email_templates/{template_type}_original"
compiled_dir = f"templates/email_templates/{template_type}_compiled"

if os.path.exists(original_dir):
    try:
        # Copy original files back to compiled directory
        if os.path.exists(compiled_dir):
            shutil.rmtree(compiled_dir)
        shutil.copytree(original_dir, compiled_dir)
        print(f"✅ Restored original template files: {original_dir} → {compiled_dir}")
    except Exception as e:
        print(f"⚠️ Could not restore original template files: {e}")
```

**What this does:**
- Deletes entire `{template}_compiled/` folder
- Copies pristine files from `{template}_original/` to `{template}_compiled/`
- Restores compiled HTML, inline_images.json, and all template assets
- Ensures email rendering uses pristine template structure

**Why this matters:**
- Compiled templates contain the actual HTML used for emails
- User customizations might have triggered recompilation
- Reset ensures pristine template structure is restored
- This is the "nuclear option" - complete template restoration

**Step 6: Commit Database Changes** (Lines 8020-8024)
```python
from sqlalchemy.orm.attributes import flag_modified
flag_modified(activity, 'email_templates')
db.session.commit()
```

**What this does:**
- Tells SQLAlchemy that JSON column changed (required for JSON fields)
- Commits transaction to database
- Makes changes permanent

**Step 7: Return Success Response** (Lines 8026-8032)
```python
flash('Template reset to defaults successfully!', 'success')

return jsonify({
    'success': True,
    'message': f'Template "{template_type}" has been reset to default values'
})
```

**What this does:**
- Sets Flask flash message for user feedback
- Returns JSON success response
- Frontend reloads page and displays flash message

### Reset Summary

**Files Deleted:**
1. Custom hero image: `static/uploads/{activity_id}_{template_type}_hero.png`
2. Owner logo (newPass only): `static/uploads/{activity_id}_owner_logo.png`
3. Compiled template folder: `templates/email_templates/{template_type}_compiled/`

**Files Restored:**
1. Compiled template folder: Copied from `{template}_original/` to `{template}_compiled/`

**Database Changes:**
1. Removed custom fields: subject, title, intro_text, conclusion_text, hero_image, activity_logo
2. Deleted template entry if no data remains

**Result:**
- Template reverts to pristine defaults
- Text content from `utils_email_defaults.py`
- Hero image from `{template}_original/inline_images.json`
- Compiled HTML from `{template}_original/index.html`
- No custom images or text remain

---

## Hero Image Resolution System

### The Three-Tier Priority System

When displaying or sending an email template, the system determines which hero image to use based on a **three-tier priority hierarchy**.

### Priority Order (Highest to Lowest)

#### Priority 1: Custom Uploaded Hero ⭐
**Location:** `static/uploads/{activity_id}_{template_type}_hero.png`

**When used:**
- User uploaded a custom hero image via the customization tool
- File exists on disk

**Code:** `utils.py:138-151`
```python
custom_hero_path = f"static/uploads/{activity.id}_{template_type}_hero.png"
if os.path.exists(custom_hero_path):
    with open(custom_hero_path, "rb") as f:
        hero_data = f.read()
        return hero_data, True, False  # is_custom=True
```

**Visual indicator:** Template card shows "Custom" badge

**When cleared:** User clicks "Reset to Default"

---

#### Priority 2: Original Template Default 📦
**Location:** `templates/email_templates/{template}_original/inline_images.json`

**When used:**
- No custom hero image exists (Priority 1 not available)
- Template is in default state

**Code:** `utils.py:153-157`
```python
template_hero_data = get_template_default_hero(template_type)
if template_hero_data:
    return template_hero_data, False, True  # is_template_default=True
```

**Image resolution:** `utils.py:58-118`
```python
def get_template_default_hero(template_type):
    # Map to original folder
    template_map = {
        'newPass': 'newPass_original',
        'paymentReceived': 'paymentReceived_original',
        ...
    }

    # Load inline_images.json from ORIGINAL template
    json_path = f'templates/email_templates/{original_folder}/inline_images.json'

    with open(json_path, 'r') as f:
        compiled_images = json.load(f)

    # Map to hero key
    hero_key_map = {
        'newPass': 'hero_new_pass',
        'paymentReceived': 'currency-dollar',
        'latePayment': 'thumb-down',
        'signup': 'good-news',
        'redeemPass': 'hand-rock',
        'survey_invitation': 'sondage'
    }

    hero_key = hero_key_map.get(template_type)
    hero_base64 = compiled_images[hero_key]
    return base64.b64decode(hero_base64)
```

**Visual indicator:** Template card shows "Default" badge

**These are the pristine images included in the original templates**

---

#### Priority 3: Activity Image (Conditional Fallback) 🎯
**Location:** `static/uploads/{activity.image_filename}` or `static/uploads/activity_images/{activity.image_filename}`

**When used:**
- No custom hero exists (Priority 1 not available)
- No original template default loaded (Priority 2 failed)
- **AND template has active customizations** (key condition!)

**Code:** `utils.py:161-185`
```python
# Priority 3: Fall back to activity image ONLY if template has active customizations
if activity and activity.image_filename:
    # Check if this template has any customizations in the database
    has_customizations = False
    if activity.email_templates and template_type in activity.email_templates:
        template_data = activity.email_templates[template_type]
        customizable_fields = ['subject', 'title', 'intro_text',
                               'conclusion_text', 'hero_image', 'activity_logo']
        has_customizations = any(field in template_data and template_data[field]
                                for field in customizable_fields)

    # Only use activity image if template was customized
    if has_customizations:
        activity_image_paths = [
            f"static/uploads/{activity.image_filename}",
            f"static/uploads/activity_images/{activity.image_filename}"
        ]

        for activity_image_path in activity_image_paths:
            if os.path.exists(activity_image_path):
                with open(activity_image_path, "rb") as f:
                    return f.read(), False, False
```

**Important conditions:**
1. Activity must have an image file
2. Template must have active customizations in database
3. This prevents showing activity image after reset

**Visual indicator:** Template card shows "Custom" badge

**Why this exists:** When user customizes a template but doesn't upload a hero, use activity image instead of leaving it blank

---

### Priority System Examples

#### Example 1: Fresh Activity (Never Customized)
```
User hasn't touched email templates yet
Result: Priority 2 (Original Template Default)
Hero: templates/email_templates/newPass_original/inline_images.json → hero_new_pass
Badge: "Default"
```

#### Example 2: User Uploads Custom Hero
```
User clicks Customize → Uploads hero.jpg → Saves
Result: Priority 1 (Custom Uploaded Hero)
Hero: static/uploads/1_newPass_hero.png
Badge: "Custom"
```

#### Example 3: User Customizes Text But No Hero
```
User clicks Customize → Changes title → Saves (no hero upload)
Result: Priority 3 (Activity Image Fallback)
Hero: static/uploads/activity_images/hockey_league.png
Badge: "Custom"
Reason: Template has customizations, so show activity branding
```

#### Example 4: User Resets After Customization
```
User had uploaded hero → Clicks Reset to Default
Result: Priority 2 (Original Template Default)
Hero: templates/email_templates/newPass_original/inline_images.json → hero_new_pass
Badge: "Default"
Reason: Reset deleted custom hero file AND database customizations
```

#### Example 5: Complex Scenario
```
Activity has activity image: hockey_league.png
User customizes newPass text (no hero upload)
  → Shows hockey_league.png (Priority 3)
User resets newPass
  → Shows original default hero (Priority 2)
  → Does NOT show hockey_league.png (no customizations)
User customizes signup text (no hero upload)
  → Shows hockey_league.png (Priority 3)
```

### Why This Complexity?

**Problem:** Users expect different behavior in different contexts:

1. **Default state:** Show professional template defaults
2. **Customizing:** Show activity branding if no hero uploaded
3. **After reset:** Show pristine defaults, NOT activity image

**Solution:** Three-tier priority with conditional fallback

**Key insight:** Priority 3 checks for `has_customizations` to avoid showing activity image after reset

---

## Frontend-Backend Integration

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER ACTIONS                             │
└─────────────────────────────────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
           ┌────────▼────────┐      ┌────────▼────────┐
           │   Customize     │      │  Reset to       │
           │   Template      │      │  Default        │
           └────────┬────────┘      └────────┬────────┘
                    │                         │
                    │                         │
┌───────────────────▼─────────────────────────▼───────────────────┐
│                     FRONTEND (HTML + JavaScript)                 │
│  - email_template_customization.html                            │
│  - Bootstrap modals for UI                                      │
│  - AJAX handlers for save/reset/preview                         │
│  - TinyMCE editors for rich text                                │
└───────────────────┬─────────────────────────┬───────────────────┘
                    │                         │
         ┌──────────▼──────────┐   ┌──────────▼──────────┐
         │  POST /save         │   │  POST /reset        │
         │  (FormData)         │   │  (JSON)             │
         └──────────┬──────────┘   └──────────┬──────────┘
                    │                         │
┌───────────────────▼─────────────────────────▼───────────────────┐
│                     BACKEND ROUTES (Flask)                       │
│  app.py:7719  save_email_templates()                            │
│  app.py:7934  reset_email_template()                            │
│  app.py:8546  get_hero_image()                                  │
└───────────────────┬─────────────────────────┬───────────────────┘
                    │                         │
         ┌──────────▼──────────┐   ┌──────────▼──────────┐
         │  1. Process files   │   │  1. Clear DB fields │
         │  2. Sanitize text   │   │  2. Delete files    │
         │  3. Update DB       │   │  3. Restore files   │
         └──────────┬──────────┘   └──────────┬──────────┘
                    │                         │
┌───────────────────▼─────────────────────────▼───────────────────┐
│                     PERSISTENCE LAYER                            │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Database (SQLite/PostgreSQL)                              │ │
│  │  - activity.email_templates (JSON column)                  │ │
│  │  - Stores only customizations                              │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  File System (static/uploads/)                             │ │
│  │  - {activity_id}_{template}_hero.png (custom heroes)       │ │
│  │  - {activity_id}_owner_logo.png (shared logo)              │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Template Files (templates/email_templates/)               │ │
│  │  - {template}_original/ (pristine defaults)                │ │
│  │  - {template}_compiled/ (active templates)                 │ │
│  └────────────────────────────────────────────────────────────┘ │
└───────────────────┬─────────────────────────┬───────────────────┘
                    │                         │
┌───────────────────▼─────────────────────────▼───────────────────┐
│                     UTILITY FUNCTIONS                            │
│  utils.py:124     get_activity_hero_image()                     │
│  utils.py:58      get_template_default_hero()                   │
│  utils.py:3223    get_email_context()                           │
│  utils_email_defaults.py:9  get_default_email_templates()       │
└───────────────────┬─────────────────────────┬───────────────────┘
                    │                         │
┌───────────────────▼─────────────────────────▼───────────────────┐
│                     EMAIL RENDERING                              │
│  - Compiled templates in {template}_compiled/index.html         │
│  - Merged context (defaults + customizations)                   │
│  - Hero images resolved via priority system                     │
│  - Sent via utils.send_email()                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Integration Points

#### Point 1: Template Loading (GET /email-templates)
```
Frontend Request → Backend Route → Database Query → Utils (get defaults)
→ Merge custom + defaults → Render HTML → Show to user
```

**Files involved:**
- `templates/email_template_customization.html` (UI)
- `app.py:7667` (route)
- `models.py` (Activity.email_templates)
- `utils_email_defaults.py:9` (defaults)

#### Point 2: Save Customizations (POST /save)
```
Form Submit → AJAX Request → Backend Validation → File Upload Processing
→ Text Sanitization → Database Update → File System Write → JSON Response
```

**Files involved:**
- `email_template_customization.html:730` (AJAX)
- `app.py:7719` (route)
- `utils.py:192` (ContentSanitizer)
- `utils.py:resize_hero_image()` (image processing)

#### Point 3: Reset to Default (POST /reset)
```
Button Click → Confirmation Modal → AJAX Request → Backend Processing
→ Clear Database → Delete Files → Restore Original → Reload Page
```

**Files involved:**
- `email_template_customization.html:515` (AJAX)
- `app.py:7934` (route)
- File system operations (delete + restore)

#### Point 4: Hero Image Display (GET /hero-image)
```
<img src="/activity/1/hero-image/newPass"> → Backend Route
→ Hero Resolution Logic (3-tier priority) → Return Image Data
```

**Files involved:**
- `email_template_customization.html:50` (img tag)
- `app.py:8546` (route)
- `utils.py:124` (get_activity_hero_image)
- `utils.py:58` (get_template_default_hero)

#### Point 5: Email Sending (Production)
```
Trigger Event (e.g., pass created) → Build Context → Merge Customizations
→ Resolve Hero Image → Render Compiled Template → Send Email
```

**Files involved:**
- Various triggers throughout `app.py`
- `utils.py:3223` (get_email_context)
- `utils.py:124` (get_activity_hero_image)
- `utils.py:2090` (send_email)
- `templates/email_templates/{template}_compiled/index.html`

---

## Complete User Workflow

### Workflow 1: Customizing a Template

**Step 1: Navigate to Email Templates**
```
Activity Dashboard → "Email Templates" button → /activity/1/email-templates
```

**Step 2: View Template Cards**
- User sees 6 template cards in grid layout
- Each card shows:
  - Mini hero image preview
  - Placeholder text lines
  - Mini owner card (for pass templates)
  - Template name
  - Status badge ("Custom" or "Default")

**Step 3: Click "Customize" Button**
- Customize modal opens
- Form fields pre-populated with current values
- TinyMCE editors initialized for intro/conclusion
- Hero image shows current hero (with cache-busting)

**Step 4: Make Changes**
- User edits subject line
- User edits title
- User edits intro text (rich text editor)
- User edits conclusion text (rich text editor)
- User uploads new hero image → Preview shows immediately
- User uploads owner logo (only for first template)

**Step 5: Preview Changes (Optional)**
- User clicks "Preview" button
- System sends current form data (including unsaved changes) to backend
- Backend renders compiled template with changes
- New tab opens with preview HTML
- User can close preview and continue editing

**Step 6: Send Test Email (Optional)**
- User clicks "Send Test" dropdown
- Selects email address (kdresdell@gmail.com or jf@jfgoulet.com)
- System sends actual email with unsaved changes
- Alert confirms: "Test email sent successfully!"

**Step 7: Save Changes**
- User clicks "Save" button
- System collects all form data
- AJAX POST to `/activity/1/email-templates/save`
- Backend:
  - Validates data
  - Sanitizes HTML
  - Saves uploaded files to disk
  - Updates database JSON column
  - Commits transaction
- Page reloads with success message
- Template card now shows "Custom" badge

### Workflow 2: Resetting to Defaults

**Step 1: Click "Reset" Button**
- User hovers over template card
- Clicks reset icon (refresh symbol)
- Reset confirmation modal opens

**Step 2: Confirm Reset**
- Modal shows: "Reset [Template Name] to default values?"
- User clicks "Reset" button (red)
- Button shows loading spinner

**Step 3: Backend Processing**
- AJAX POST to `/activity/1/email-templates/reset`
- Backend:
  1. Clears database customizations
  2. Deletes custom hero image file
  3. Deletes owner logo (if newPass)
  4. Deletes compiled template folder
  5. Copies original files to compiled folder
  6. Commits database changes
- Returns success JSON

**Step 4: Page Reload**
- Frontend reloads page
- Flash message: "Template reset to defaults successfully!"
- Template card shows "Default" badge
- Hero image shows original template default

### Workflow 3: Viewing Email in Production

**Trigger:** User receives pass, payment confirmed, etc.

**Step 1: Event Occurs**
```python
# Example: New pass created
from utils import send_new_pass_email
send_new_pass_email(passport, user)
```

**Step 2: Build Email Context**
```python
from utils import get_email_context

base_context = {
    'user_name': user.name,
    'pass_code': passport.pass_code,
    'owner_html': '...',  # Generated HTML block
    'history_html': '...'  # Generated HTML block
}

context = get_email_context(
    activity=passport.activity,
    template_type='newPass',
    base_context=base_context
)
```

**Step 3: Resolve Hero Image**
```python
from utils import get_activity_hero_image

hero_data, is_custom, is_template_default = get_activity_hero_image(
    activity=passport.activity,
    template_type='newPass'
)
```

**Step 4: Render Compiled Template**
```python
from flask import render_template

html = render_template(
    'email_templates/newPass_compiled/index.html',
    **context
)
```

**Step 5: Embed Hero Image**
- Hero image embedded as inline CID attachment
- Ensures image displays in email clients
- Uses data from Priority 1, 2, or 3

**Step 6: Send Email**
```python
from utils import send_email

send_email(
    subject=context['subject'],
    to_email=user.email,
    html_body=html,
    inline_images={'hero_image': hero_data}
)
```

**Result:** User receives email with:
- Custom text (if customized) or defaults
- Custom hero (if uploaded) or original default
- Activity branding (owner logo, etc.)
- Dynamic content (pass code, history, etc.)

---

## Database Schema

### Activity Table

```sql
CREATE TABLE activity (
    id INTEGER PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    type VARCHAR(50),
    description TEXT,
    start_date DATETIME,
    end_date DATETIME,
    image_filename VARCHAR(255),
    logo_filename VARCHAR(255),
    created_by INTEGER REFERENCES admin(id),
    created_dt DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active',

    -- Email template customizations
    email_templates JSON,

    organization_id INTEGER REFERENCES organizations(id),
    location_address_raw TEXT,
    location_address_formatted TEXT,
    location_coordinates VARCHAR(100),
    goal_revenue FLOAT DEFAULT 0.0
);
```

### email_templates JSON Structure

**When NULL/Empty:**
```json
null
```
- Template is in default state
- All values come from `utils_email_defaults.py`

**When Customized (Example):**
```json
{
  "newPass": {
    "subject": "Your Hockey Pass is Ready! 🏒",
    "title": "Welcome to the League!",
    "intro_text": "<p>Your digital pass for <strong>Winter Hockey League 2025</strong> has been created and is ready to use!</p><p>Show this pass at the rink entrance to check in.</p>",
    "conclusion_text": "<p>We're excited to see you on the ice!</p><p>If you have any questions, reply to this email.</p>",
    "hero_image": "1_newPass_hero.png",
    "activity_logo": "1_owner_logo.png"
  },
  "signup": {
    "subject": "Registration Confirmed ✓",
    "title": "You're all set!",
    "intro_text": "<p>Thank you for registering for Winter Hockey League 2025.</p>",
    "conclusion_text": "<p>Check your email for next steps!</p>"
  }
}
```

**Field Descriptions:**

| Field | Type | Description | Customizable? |
|-------|------|-------------|---------------|
| `subject` | String | Email subject line (plain text) | Yes |
| `title` | String | Main heading in email (plain text) | Yes |
| `intro_text` | String | Opening paragraph (HTML allowed) | Yes |
| `conclusion_text` | String | Closing paragraph (HTML allowed) | Yes |
| `hero_image` | String | Filename of custom hero (not full path) | Indirect (via file upload) |
| `activity_logo` | String | Filename of owner logo (not full path) | Indirect (via file upload) |

**Fields NOT Stored (Always Dynamic):**
- `owner_html` - Generated from activity/organization data
- `history_html` - Generated from passport/payment records
- `user_name`, `pass_code`, etc. - Context variables

**SQLAlchemy Gotcha:**
```python
# ❌ WRONG - SQLAlchemy won't detect change
activity.email_templates['newPass']['subject'] = 'New Subject'
db.session.commit()  # Nothing happens!

# ✅ CORRECT - Must flag as modified
activity.email_templates['newPass']['subject'] = 'New Subject'
from sqlalchemy.orm.attributes import flag_modified
flag_modified(activity, 'email_templates')
db.session.commit()  # Now it saves!
```

---

## Issues and Recommendations

### Current Issues Identified

#### Issue 1: User Confusion About Reset Scope
**Problem:**
- "Reset to Default" button is ambiguous
- Users don't know what will be reset
- No indication of what "default" means (original template vs activity image)

**Evidence:**
- User reported: "I'm not sure what it is doing"
- Three-tier hero image system is invisible to users

**Recommendation:**
```html
<!-- Instead of just "Reset to Default" -->
<button title="Reset to Default">
    <i class="ti ti-refresh"></i>Visual indicator: Template card shows "Custom" badge


</button>

<!-- Add informative tooltip -->
<button title="Reset to defaults: Remove custom text, images, and restore original template">
    <i class="ti ti-refresh"></i>
</button>

<!-- Or modal with explanation -->
<div class="modal-body">
    <p>This will:</p>
    <ul>
        <li>Remove all custom text</li>
        <li>Delete uploaded hero image</li>
        <li>Restore original template design</li>
    </ul>
    <p><strong>This cannot be undone.</strong></p>
</div>
```

#### Issue 2: No Visual Feedback for Reset Scope
**Problem:**
- Users can't see the difference between:
  - Custom uploaded hero
  - Original template default hero
  - Activity image fallback

**Evidence:**
- All three states show "Custom" or "Default" badge
- No indication of which hero image source is active

**Recommendation:**
Add visual indicators:
```html
<!-- Show hero image source -->
<div class="template-status">
    <span v-if="has_custom_hero" class="badge bg-blue">
        <i class="ti ti-upload"></i> Custom Hero
    </span>
    <span v-else-if="using_activity_image" class="badge bg-yellow">
        <i class="ti ti-photo"></i> Activity Image
    </span>
    <span v-else class="badge bg-gray">
        <i class="ti ti-template"></i> Default
    </span>
</div>
```

#### Issue 3: Owner Logo Deletion Tied to newPass Reset
**Problem:**
- Owner logo is shared across all templates
- Deleting it only when resetting `newPass` is confusing
- Users might reset `newPass` expecting to keep logo for other templates

**Evidence:**
```python
# app.py:7995-8002
if template_type == 'newPass' and os.path.exists(owner_logo_path):
    os.remove(owner_logo_path)
```

**Recommendation:**
- Option A: Never auto-delete owner logo (require separate action)
- Option B: Show warning: "This will also reset the organization logo for all templates"
- Option C: Add separate "Reset Logo" button outsideVisual indicator: Template card shows "Custom" badge

 individual templates

#### Issue 4: No Undo for Reset
**Problem:**
- Reset permanently deletes custom content
- No backup or recovery option
- Users might accidentally click reset

**Evidence:**
- Confirmation modal is only safeguard
- Files deleted immediately
- No version history

**Recommendation:**
Add backup before reset:
```python
# Before deleting, save backup
backup_dir = f"static/uploads/backups/{activity_id}/"
os.makedirs(backup_dir, exist_ok=True)

if os.path.exists(hero_file_path):
    import shutil
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{backup_dir}{template_type}_hero_{timestamp}.png"
    shutil.copy2(hero_file_path, backup_path)
    os.remove(hero_file_path)
```

#### Issue 5: Template Compilation Not Always Triggered
**Problem:**
- Reset copies `_original` → `_compiled` (good)
- Save might not trigger recompilation
- Compiled templates might get out of sync

**Evidence:**
```python
# app.py:7884-7901
# AUTO-COMPILE only for survey_invitation
if is_individual_save and single_template == 'survey_invitation':
    # Compile script called
```

**Recommendation:**
- Trigger compilation for all templates after save
- Or document when manual compilation is needed
- Or prevent direct editing of compiled templates

#### Issue 6: No Preview of Default Before Reset
**Problem:**
- Users can't see what "default" looks like before resetting
- Might reset expecting one thing, get another

**Recommendation:**
Add "Preview Default" option:
```html
<button class="btn btn-sm btn-outline-secondary"
        onclick="previewDefault('newPass')">
    <i class="ti ti-eye"></i> Preview Default
</button>
```

### Potential Improvements

#### Improvement 1: Version History
**Feature:** Track template customization history
```json
{
  "newPass": {
    "current": {
      "subject": "Current subject",
      ...
    },
    "history": [
      {
        "timestamp": "2025-10-29T10:30:00Z",
        "changed_by": "admin@example.com",
        "changes": { "subject": "Old subject" }
      }
    ]
  }
}
```

#### Improvement 2: Template Duplication
**Feature:** "Duplicate template to other activities"
- Save time for multi-activity admins
- Consistent branding across activities

#### Improvement 3: Bulk Operations
**Feature:** "Apply to all templates"
- Upload one hero, apply to all
- Change organization logo once, update all

#### Improvement 4: Template Preview Mode
**Feature:** Side-by-side comparison
- Show current vs default
- Show desktop vs mobile
- Show with real data vs placeholder data

#### Improvement 5: Better File Management
**Feature:** Media library for uploaded images
- Reuse images across templates
- See all uploaded files
- Delete unused files

### Security Considerations

#### Current Security Measures ✅

1. **Admin Authentication Required**
```python
if "admin" not in session:
    return redirect(url_for("login"))
```

2. **HTML Sanitization**
```python
from utils import ContentSanitizer
subject = ContentSanitizer.sanitize_html(request.form.get('subject'))
```

3. **File Upload Validation**
```python
hero_file = request.files.get(f'{template_type}_hero_image')
if hero_file and hero_file.filename:
    # Only accepts image/* mime types
```

4. **CSRF Protection**
```javascript
headers: {
    'X-CSRFToken': '{{ csrf_token() }}'
}
```

#### Potential Security Issues ⚠️

1. **No File Size Limits**
- Users could upload very large images
- Could fill disk space

**Fix:**
```python
MAX_HERO_SIZE = 5 * 1024 * 1024  # 5MB
if len(hero_file.read()) > MAX_HERO_SIZE:
    return jsonify({'success': False, 'message': 'File too large'})
```

2. **No File Type Validation**
- Only checks mime type from browser
- Could be spoofed

**Fix:**
```python
from PIL import Image
try:
    img = Image.open(hero_file)
    img.verify()  # Verify it's a real image
except:
    return jsonify({'success': False, 'message': 'Invalid image file'})
```

3. **Path Traversal Risk**
- Template type comes from user input
- Could potentially access other files

**Current mitigation:**
```python
valid_templates = ['newPass', 'paymentReceived', 'latePayment',
                   'signup', 'redeemPass', 'survey_invitation']
if template_type not in valid_templates:
    return jsonify({'success': False})
```
This is good! ✅

---

## Testing and Validation

### Manual Testing Checklist

#### Test 1: Customize Template
- [ ] Navigate to email templates page
- [ ] Click customize on newPass template
- [ ] Change subject line
- [ ] Change title
- [ ] Edit intro text with rich text formatting
- [ ] Upload custom hero image
- [ ] Preview shows changes correctly
- [ ] Save successfully
- [ ] Page reloads with success message
- [ ] Template card shows "Custom" badge
- [ ] Hero image displays correctly

#### Test 2: Reset Template
- [ ] Customize newPass template (see Test 1)
- [ ] Click reset button
- [ ] Confirmation modal appears
- [ ] Click cancel - nothing happens
- [ ] Click reset again
- [ ] Click confirm
- [ ] Page reloads with success message
- [ ] Template card shows "Default" badge
- [ ] Hero image shows original default
- [ ] Subject/title/text reverted to defaults
- [ ] Custom hero image file deleted from uploads/

#### Test 3: Owner Logo
- [ ] Customize newPass template
- [ ] Upload owner logo
- [ ] Save
- [ ] Check other templates - logo should appear in mini preview
- [ ] Reset newPass template
- [ ] Check other templates - logo should be gone

#### Test 4: Test Email
- [ ] Customize template (don't save)
- [ ] Click "Send Test" dropdown
- [ ] Select email address
- [ ] Check email inbox
- [ ] Email should show unsaved changes
- [ ] Hero image should display correctly
- [ ] Text formatting should be preserved

#### Test 5: Live Preview
- [ ] Customize template (don't save)
- [ ] Click "Preview" button
- [ ] New tab should open
- [ ] Should show rendered email
- [ ] Should include unsaved changes
- [ ] Close tab, continue editing
- [ ] Changes should still be in form

#### Test 6: Multiple Templates
- [ ] Customize newPass
- [ ] Customize signup
- [ ] Customize survey_invitation
- [ ] Each should save independently
- [ ] Reset newPass - others should stay customized
- [ ] Each should maintain own hero image

#### Test 7: Hero Image Priority
- [ ] Fresh activity, never customized
  - [ ] Should show original template default hero
- [ ] Upload custom hero
  - [ ] Should show custom hero
- [ ] Reset template
  - [ ] Should show original default hero
  - [ ] Should NOT show activity image
- [ ] Customize text only (no hero upload)
  - [ ] Should show activity image (if activity has one)
- [ ] Reset again
  - [ ] Should show original default hero

#### Test 8: Error Handling
- [ ] Try uploading non-image file
  - [ ] Should reject gracefully
- [ ] Try uploading very large image
  - [ ] Should process or show error
- [ ] Try accessing without login
  - [ ] Should redirect to login
- [ ] Try invalid template type
  - [ ] Should show 400 error

### Automated Testing Scenarios

```python
# test_email_templates.py

def test_customize_template(client, admin_session):
    """Test customizing email template"""
    response = client.post('/activity/1/email-templates/save', data={
        'single_template': 'newPass',
        'newPass_subject': 'Custom Subject',
        'newPass_title': 'Custom Title',
        'csrf_token': get_csrf_token()
    })

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True

    # Verify database
    activity = Activity.query.get(1)
    assert activity.email_templates['newPass']['subject'] == 'Custom Subject'

def test_reset_template(client, admin_session):
    """Test resetting template to defaults"""
    # First customize
    client.post('/activity/1/email-templates/save', data={
        'single_template': 'newPass',
        'newPass_subject': 'Custom Subject',
        'csrf_token': get_csrf_token()
    })

    # Then reset
    response = client.post('/activity/1/email-templates/reset',
                          json={'template_type': 'newPass'},
                          headers={'X-CSRFToken': get_csrf_token()})

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True

    # Verify database cleared
    activity = Activity.query.get(1)
    assert 'newPass' not in activity.email_templates or \
           'subject' not in activity.email_templates.get('newPass', {})

def test_hero_image_priority(client, admin_session):
    """Test hero image resolution priority"""
    activity = Activity.query.get(1)

    # Test priority 2: Original template default
    hero_data, is_custom, is_template_default = \
        get_activity_hero_image(activity, 'newPass')
    assert is_template_default == True
    assert is_custom == False

    # Upload custom hero (priority 1)
    with open('test_hero.png', 'rb') as f:
        client.post('/activity/1/email-templates/save', data={
            'single_template': 'newPass',
            'newPass_hero_image': f,
            'csrf_token': get_csrf_token()
        })

    hero_data, is_custom, is_template_default = \
        get_activity_hero_image(activity, 'newPass')
    assert is_custom == True
    assert is_template_default == False
```

---

## Related Documentation

### Companion Guides

1. **EMAIL_TEMPLATE_SYSTEM_GUIDE.md** (Backend)
   - How to create/modify default templates
   - Compilation process with `compileEmailTemplate.py`
   - Base64 encoding for inline images
   - Template structure and requirements

2. **CLAUDE.md** (Project Overview)
   - Development environment setup
   - Technology constraints
   - Architecture overview

3. **CONSTRAINTS.md** (Development Rules)
   - Agent delegation patterns
   - Testing requirements
   - Python-first policy

### Cross-References

**From Backend Guide to Frontend Guide:**
- After compiling templates → Templates available in frontend tool
- Original templates → Used as defaults in reset operation
- inline_images.json → Used in hero image resolution (Priority 2)

**From Frontend Guide to Backend Guide:**
- Need to update defaults? → See backend guide for compilation
- Broken compiled templates? → Re-run compilation process
- Adding new template type? → Update both systems

---

## Appendix: Key File Locations

### Frontend
```
templates/
├── email_template_customization.html     # Main UI template
└── base.html                             # Layout wrapper

static/
├── css/
│   └── email-template-customization.css  # Styling
└── js/
    ├── email-template-editor.js          # Core editor logic
    └── email-template-enhanced.js        # Enhanced features
```

### Backend
```
app.py
├── Line 7667: email_template_customization()    # View route
├── Line 7719: save_email_templates()            # Save route
├── Line 7934: reset_email_template()            # Reset route
├── Line 8042: email_preview()                   # Preview route
├── Line 8262: email_preview_live()              # Live preview route
├── Line 8546: get_hero_image()                  # Hero image route
└── Line 8591: test_email_template()             # Test email route

utils.py
├── Line 58:   get_template_default_hero()       # Load original hero
├── Line 124:  get_activity_hero_image()         # Hero resolution
└── Line 3223: get_email_context()               # Context merging

utils_email_defaults.py
└── Line 9:    get_default_email_templates()     # Default text values

models.py
└── Line 100:  Activity.email_templates          # JSON storage
```

### Templates
```
templates/email_templates/
├── newPass_original/                     # Pristine defaults
│   ├── index.html
│   └── inline_images.json
├── newPass_compiled/                     # Active templates
│   ├── index.html
│   └── inline_images.json
├── paymentReceived_original/
├── paymentReceived_compiled/
├── latePayment_original/
├── latePayment_compiled/
├── signup_original/
├── signup_compiled/
├── redeemPass_original/
├── redeemPass_compiled/
├── survey_invitation_original/
└── survey_invitation_compiled/
```

### Uploads
```
static/uploads/
├── {activity_id}_{template}_hero.png    # Custom hero images
├── {activity_id}_owner_logo.png         # Organization logos
└── activity_images/
    └── {activity_image_filename}        # Activity images (fallback)
```

---

## Questions & Answers

### Q: What happens if I reset a template that was never customized?
**A:** Nothing changes visually, but the backend still runs the full reset process (clears DB fields, attempts file deletion, restores compiled folder). Safe but redundant.

### Q: Can I customize only the hero image without changing text?
**A:** Yes! Upload a hero image and save. Text fields will remain at default values. Template will show "Custom" badge because hero_image is stored in database.

### Q: What happens if I delete the compiled template folder manually?
**A:** Emails will fail to render until you either:
1. Click "Reset to Default" (restores from original)
2. Re-run compilation script manually

### Q: Can I revert to a previous customization?
**A:** No, there's no version history. Once you save or reset, previous values are lost. Consider adding backups (see Issue #4).

### Q: Why does the activity image sometimes show after customizing?
**A:** This is Priority 3 behavior. If you customize text but don't upload a hero, the system shows your activity image for branding. After reset, it goes back to original template default.

### Q: Can I use the same hero image for multiple templates?
**A:** Not currently. You must upload separately for each template. Consider adding bulk operations (see Improvement #3).

### Q: What if two templates have different hero image sizes?
**A:** The `resize_hero_image()` function automatically resizes uploads to match template dimensions. Each template type may have different dimensions defined.

### Q: Can I preview the default template before resetting?
**A:** Not currently. The reset confirmation modal doesn't show a preview. Consider adding this feature (see Issue #6).

---

**End of Guide**

For questions or issues, see:
- GitHub Issues: (your repo)
- Developer: kdresdell@gmail.com
- Documentation Updates: Edit this file and commit to repo
