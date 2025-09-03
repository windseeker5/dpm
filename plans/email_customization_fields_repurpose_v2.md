# Email Customization Fields Repurpose Plan (v2)

## Executive Summary
Transform unused email customization fields into functional features that allow activity-specific branding in automated emails, with proper default handling for new activities.

## Critical Clarifications
1. **Owner Card Logo**: Currently shows ORGANIZATION logo (not Minipass) in real emails. Preview bug shows Minipass logo.
2. **Default Images**: New activities must have default images copied, not empty fields.
3. **Owner Card Compilation**: Changing owner card logo requires recompiling the owner_card_inline.html template.

## Problem Statement
- Current fields (Activity Logo, Hero Image, CTA Text/URL, Custom Message) are stored but never used
- New activities have no default images, would result in broken emails
- Preview shows wrong logo (Minipass instead of organization)

## Solution Overview
1. **Hero Image** → Replace hardcoded ticket icon at email top (with default)
2. **Activity Logo** → Replace organization logo in owner card (with default)
3. **Remove** → CTA fields and Custom Message (dead code)
4. **Defaults** → Copy default images for new activities

## Implementation Tasks

### Task 0: Copy Default Images for New Activities
**Agent**: backend-architect  
**Estimated LOC**: ~40 lines  
**Files to modify**:
- `/app.py` (create_activity route, line ~1380)
- `/utils_email_defaults.py` (add default image handling)

**Work**:
```python
# When creating new activity, copy default images
def create_activity():
    # ... existing code ...
    
    # After creating activity with ID
    # Copy default hero image
    default_hero = "static/uploads/default_hero.png"
    activity_hero = f"static/uploads/{new_activity.id}_hero.png"
    shutil.copy(default_hero, activity_hero)
    
    # Copy default owner logo (use org logo as default)
    org_logo = get_setting('LOGO_FILENAME', 'logo.png')
    default_owner = f"static/uploads/{org_logo}"
    activity_owner = f"static/uploads/{new_activity.id}_owner_logo.png"
    shutil.copy(default_owner, activity_owner)
    
    # Update email_templates to reference these files
    for template_type in default_email_templates:
        default_email_templates[template_type]['hero_image'] = f"{new_activity.id}_hero.png"
        default_email_templates[template_type]['activity_logo'] = f"{new_activity.id}_owner_logo.png"
```

**Unit Test** (`test/test_activity_creation.py`):
```python
def test_new_activity_gets_default_images():
    # Create new activity
    # Verify hero image file exists
    # Verify owner logo file exists  
    # Verify database references files
```

---

### Task 1: Fix Email Preview to Show Correct Logo
**Agent**: backend-architect  
**Estimated LOC**: ~20 lines  
**Files to modify**:
- `/app.py` (preview_email route)

**Work**:
- Fix preview to show organization logo (not Minipass)
- Ensure preview matches actual email rendering

---

### Task 2: Fix File Upload in Email Customization Form
**Agent**: flask-ui-developer  
**Estimated LOC**: ~60 lines  
**Files to modify**:
- `/templates/email_template_customization.html`

**Work**:
- Fix broken file upload for Activity Logo
- Add file upload for Hero Image
- Show current images (since defaults exist)
- Add "Replace" button next to current image preview
- Remove CTA Text, CTA URL, Custom Message fields
- Rename "Activity Logo" to "Owner Card Logo"

**UI Flow**:
```
Hero Image: [current_hero_preview.png] [Replace button]
Owner Card Logo: [current_logo_preview.png] [Replace button]
```

---

### Task 3: Update Backend to Handle File Uploads/Replacements
**Agent**: backend-architect  
**Estimated LOC**: ~100 lines  
**Files to modify**:
- `/app.py` (update email customization route)

**Work**:
- Handle file replacements (not initial uploads since defaults exist)
- When user uploads new image, replace existing file
- Keep same filename pattern: `{activity_id}_hero.png`
- Update activity's email_templates JSON to track custom vs default

**Unit Test** (`test/test_email_customization.py`):
```python
def test_replace_hero_image():
    # Activity has default hero
    # Upload new hero image
    # Verify file replaced
    # Verify old file deleted

def test_replace_owner_logo():
    # Activity has default logo
    # Upload new logo
    # Verify file replaced
```

---

### Task 4: Recompile Owner Card When Logo Changes
**Agent**: backend-architect  
**Estimated LOC**: ~50 lines  
**Files to modify**:
- `/utils.py` (add function to recompile owner card)

**Work**:
```python
def recompile_owner_card_for_activity(activity_id):
    """Recompile owner_card_inline.html with activity-specific logo"""
    # This is the tricky part - owner card is currently static HTML
    # We need to make it dynamic per activity
    # Option 1: Generate at email send time (current approach)
    # Option 2: Pre-compile per activity (more complex)
    
    # Recommended: Stick with Option 1
    # At email send time, check for activity-specific logo
    pass
```

---

### Task 5: Modify Email Rendering to Use Custom Images  
**Agent**: backend-architect  
**Estimated LOC**: ~75 lines  
**Files to modify**:
- `/utils.py` (send_email_for_passport_event function, lines ~1800-1830)

**Work**:
```python
# Line ~1806: Use activity hero image (always exists due to defaults)
hero_filename = f"{activity.id}_hero.png"
hero_path = f"static/uploads/{hero_filename}"
if os.path.exists(hero_path):
    inline_images['ticket'] = open(hero_path, "rb").read()
else:
    # This shouldn't happen if defaults work correctly
    # Use compiled template default

# Line ~1820: Use activity owner card logo (always exists due to defaults)
owner_logo_filename = f"{activity.id}_owner_logo.png"
owner_logo_path = f"static/uploads/{owner_logo_filename}"
if os.path.exists(owner_logo_path):
    inline_images['logo'] = open(owner_logo_path, "rb").read()
else:
    # Fallback to organization logo
    inline_images['logo'] = open(org_logo_path, "rb").read()
```

**Unit Test** (`test/test_email_rendering.py`):
```python
def test_email_uses_activity_images():
    # Create activity (gets defaults)
    # Send email
    # Verify uses activity's hero and logo files

def test_email_fallback_if_files_missing():
    # Delete activity's image files
    # Send email
    # Verify falls back gracefully
```

---

### Task 6: Create Default Images
**Agent**: ui-designer  
**Estimated LOC**: 0 (just create files)  
**Files to create**:
- `/static/uploads/default_hero.png` (blue circle with white ticket icon)
- Extract from existing compiled template

---

## Testing Strategy

### Manual Testing (Using MCP Playwright)
```python
# Test Flow 1: New Activity
1. Create new activity "Test Hockey League"
2. Navigate to Email Customization
3. Verify default images are shown
4. Send test email - verify images appear
5. Replace hero image with hockey stick icon
6. Replace owner logo with hockey league logo
7. Send test email - verify new images appear

# Test Flow 2: Existing Activity
1. Use "Competition de Kite" (Activity 5)
2. Go to Email Customization
3. Upload custom images
4. Create passport and send email
5. Verify custom images in email
```

### Key Test: Owner Card Logo
```python
# CRITICAL: Verify owner card shows correct logo
1. Default: Shows organization logo (not Minipass)
2. After upload: Shows activity-specific logo
3. In preview: Must match actual email (fix preview bug)
```

---

## Risk Mitigation

### Default Image Strategy
- **Problem**: New activities need images or emails break
- **Solution**: Copy defaults on creation
- **Fallback**: Multiple fallback layers in email sending

### Owner Card Compilation
- **Problem**: Owner card is inline HTML, not easily customizable
- **Solution**: Modify at render time (already happening)
- **Test**: Ensure logo CID replacement works

---

## Implementation Order
1. Create default images (Task 6) - 10 min
2. Add default copying for new activities (Task 0) - 30 min
3. Fix preview bug (Task 1) - 20 min
4. Fix upload form UI (Task 2) - 45 min
5. Handle file replacements (Task 3) - 45 min  
6. Update email rendering (Task 5) - 45 min
7. Write tests - 45 min
8. Manual testing - 45 min

**Total estimate**: 4-5 hours

---

## Success Criteria
✅ New activities get default images automatically  
✅ Users see current images in customization form  
✅ Can replace (not upload) images easily  
✅ Owner card shows activity logo (not org logo) when customized  
✅ Preview matches actual email (fix Minipass logo bug)  
✅ Emails never break due to missing images  
✅ All email types use custom images consistently  
✅ Unit tests pass  

---

## Critical Notes
- **Owner Card**: Currently uses org logo (preview bug shows Minipass)
- **Defaults Required**: Without defaults, new activities = broken emails
- **File Pattern**: `{activity_id}_hero.png` and `{activity_id}_owner_logo.png`
- **No Restart**: Flask already running on port 5000
- **Test Carefully**: Owner card logo change is most complex part