# Email Customization Fields Repurpose Plan

## Executive Summary
Transform unused email customization fields (Activity Logo, Hero Image, CTA fields) into functional features that allow activity-specific branding in automated emails.

## Problem Statement
- Current fields (Activity Logo, Hero Image, CTA Text/URL, Custom Message) are stored but never used
- Activities cannot customize their email branding beyond text content
- Dead code creates confusion in the UI

## Solution Overview
1. **Hero Image** → Replace hardcoded ticket icon at email top
2. **Activity Logo** → Replace Minipass logo in owner card
3. **Remove** → CTA fields and Custom Message (dead code)

## Implementation Tasks

### Task 1: Fix File Upload in Email Customization Form
**Agent**: flask-ui-developer  
**Estimated LOC**: ~50 lines  
**Files to modify**:
- `/templates/email_template_customization.html`

**Work**:
- Fix broken file upload for Activity Logo
- Add file upload for Hero Image
- Remove CTA Text, CTA URL, Custom Message fields
- Rename "Activity Logo" to "Owner Card Logo"

**Testing**:
- Manual test via browser at http://localhost:5000
- Upload test images and verify they save

---

### Task 2: Update Backend to Handle File Uploads
**Agent**: backend-architect  
**Estimated LOC**: ~100 lines  
**Files to modify**:
- `/app.py` (update email customization route)

**Work**:
- Handle file uploads in POST request
- Save files as: `{activity_id}_hero.png` and `{activity_id}_owner_logo.png`
- Update activity's email_templates JSON with file references
- Ensure proper file validation (image types only)

**Unit Test** (`test/test_email_customization.py`):
```python
def test_hero_image_upload():
    # Test uploading hero image for activity
    # Verify file saved correctly
    # Verify database updated

def test_owner_logo_upload():
    # Test uploading owner card logo
    # Verify file saved correctly
    # Verify database updated
```

---

### Task 3: Modify Email Rendering to Use Custom Images
**Agent**: backend-architect  
**Estimated LOC**: ~75 lines  
**Files to modify**:
- `/utils.py` (send_email_for_passport_event function, lines ~1800-1830)

**Work**:
```python
# Line ~1806: Check for custom hero image
if activity and activity.email_templates.get(template_type, {}).get('hero_image'):
    hero_path = f"static/uploads/{activity.id}_hero.png"
    if os.path.exists(hero_path):
        inline_images['ticket'] = open(hero_path, "rb").read()
# else use default ticket from compiled template

# Line ~1820: Check for custom owner card logo  
if activity and activity.email_templates.get(template_type, {}).get('activity_logo'):
    logo_path = f"static/uploads/{activity.id}_owner_logo.png"
    if os.path.exists(logo_path):
        inline_images['logo'] = open(logo_path, "rb").read()
# else use organization logo as current
```

**Unit Test** (`test/test_email_rendering.py`):
```python
def test_custom_hero_image_in_email():
    # Create activity with custom hero
    # Send email
    # Verify inline_images['ticket'] uses custom image

def test_custom_owner_logo_in_email():
    # Create activity with custom logo
    # Send email  
    # Verify inline_images['logo'] uses custom image

def test_fallback_to_defaults():
    # Create activity without custom images
    # Verify defaults are used
```

---

### Task 4: Update Email Preview Modal
**Agent**: flask-ui-developer  
**Estimated LOC**: ~30 lines  
**Files to modify**:
- `/app.py` (preview_email route)

**Work**:
- Ensure preview shows custom images when set
- Update preview generation to use same logic as actual email

---

### Task 5: Database Migration (if needed)
**Agent**: backend-architect  
**Estimated LOC**: ~20 lines  
**Work**:
- No schema change needed (using existing email_templates JSON)
- Clean existing data to remove unused CTA/custom_message fields

---

## Testing Strategy

### Manual Testing (Using MCP Playwright)
```python
# Test credentials
email = "kdresdell@gmail.com"  
password = "admin123"
base_url = "http://localhost:5000"

# Test flow:
1. Login as admin
2. Navigate to Activities > Select "Competition de Kite" 
3. Go to Email Customization
4. Upload Hero Image (test with PNG/JPG)
5. Upload Owner Card Logo
6. Save and preview
7. Create new passport
8. Trigger email send
9. Check email preview modal
```

### Automated Tests
- Create unit tests in `/test/` folder
- Run: `python -m unittest test.test_email_customization -v`
- Run: `python -m unittest test.test_email_rendering -v`

### Integration Test with MCP Playwright
```python
# Use mcp__playwright__browser tools
# Navigate to email customization
# Upload files
# Verify preview updates
# Create passport and check email
```

---

## Risk Assessment
- **Low Risk**: Only affects email appearance, not functionality
- **Backup**: Existing compiled templates remain as fallback
- **Rollback**: Easy - just don't use custom images

---

## Implementation Order
1. Fix upload form UI (Task 1) - 30 min
2. Handle file uploads backend (Task 2) - 45 min  
3. Update email rendering (Task 3) - 45 min
4. Update preview (Task 4) - 20 min
5. Write tests - 30 min
6. Manual testing - 30 min

**Total estimate**: 3-4 hours

---

## Success Criteria
✅ Activities can upload custom hero image (replaces blue ticket icon)  
✅ Activities can upload owner card logo (replaces Minipass logo in card)  
✅ Dead fields removed from UI  
✅ Fallback to defaults when no custom images  
✅ All email types use custom images consistently  
✅ Unit tests pass  
✅ Manual testing confirms emails look correct  

---

## Notes
- Flask server already running on port 5000
- Use existing test credentials (kdresdell@gmail.com / admin123)
- Do NOT restart Flask (it's in debug mode, will auto-reload)
- Images stored in `/static/uploads/` with activity ID prefix
- Compiled templates remain unchanged (fallback)