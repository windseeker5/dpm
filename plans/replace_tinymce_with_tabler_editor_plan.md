# Replace TinyMCE with Paid Tabler.io Editor - Implementation Plan

**Created**: January 2, 2025  
**Project**: Minipass Email Template Editor Fix  
**Status**: Ready for Implementation  
**Priority**: HIGH - User has paid for Tabler.io and doesn't want TinyMCE watermark

## 🚨 CRITICAL ISSUE
- TinyMCE showing "Built with TinyMCE" watermark (unpaid version)
- User already has PAID Tabler.io editor working in settings page
- Must REUSE existing implementation, NOT build from scratch

## 📋 Implementation Tasks with Agent Assignments

### Phase 1: Research & Recovery (1 hour)

#### Task 1.1: Find Existing Working Implementation
**Assigned Agent**: `flask-ui-developer`  
**Duration**: 30 minutes  
**Description**: Locate and document the working Tabler.io editor configuration

**Steps**:
1. Check git history for working editor implementations:
   ```bash
   git log --oneline -- templates/unified_settings.html
   git log --oneline -- templates/admin/
   ```
2. Search for backup templates with editor
3. Examine current unified_settings.html page where editor works
4. Document exact HTML structure and initialization

**Testing**:
- Tool: MCP Playwright
- Navigate to: `http://localhost:5000/admin/unified-settings`
- Login: `kdresdell@gmail.com` / `admin123`
- Screenshot working editor
- Save to: `/test/playwright/working_tabler_editor.png`

#### Task 1.2: Analyze Editor Configuration
**Assigned Agent**: `js-code-reviewer`  
**Duration**: 30 minutes  
**Description**: Understand how Tabler.io editor is initialized

**Steps**:
1. Check base.html for Tabler editor includes
2. Look for initialization scripts
3. Find toolbar configuration
4. Document all required assets and dependencies

**Deliverable**: List of exact files and configurations needed

---

### Phase 2: Remove TinyMCE (30 minutes)

#### Task 2.1: Clean HTML Templates
**Assigned Agent**: `flask-ui-developer`  
**Duration**: 15 minutes  
**Description**: Remove TinyMCE classes from email template

**Steps**:
1. Open `/templates/email_template_customization.html`
2. Find all instances of `class="form-control tinymce"`
3. Replace with `class="form-control"` only
4. DO NOT add new classes yet (will copy from working version)

**Locations to update**:
- Line ~141: intro_text textarea
- Line ~237: custom_message textarea  
- Line ~247: conclusion_text textarea

#### Task 2.2: Disable TinyMCE JavaScript
**Assigned Agent**: `js-code-reviewer`  
**Duration**: 15 minutes  
**Description**: Remove TinyMCE initialization

**Steps**:
1. Open `/static/js/email-template-editor.js`
2. Comment out or remove `initTinyMCE()` function
3. Remove any TinyMCE-related calls
4. Keep all other functions (previewLogo, etc.)

---

### Phase 3: Apply Tabler.io Editor (1 hour)

#### Task 3.1: Copy Working Editor Configuration
**Assigned Agent**: `flask-ui-developer`  
**Duration**: 30 minutes  
**Description**: Apply EXACT configuration from working settings page

**CRITICAL**: 
- DO NOT create new editor implementation
- COPY exact HTML/attributes from working version
- Maintain consistency with existing paid solution

**Steps**:
1. Copy exact HTML structure from working editor in settings
2. Apply to email_template_customization.html textareas:
   - Same class names
   - Same data attributes
   - Same wrapper divs if needed
3. Ensure all three textareas have identical configuration

**Files to modify**:
- `/templates/email_template_customization.html`

#### Task 3.2: Verify JavaScript Integration
**Assigned Agent**: `js-code-reviewer`  
**Duration**: 15 minutes  
**Description**: Ensure Tabler editor initializes properly

**Steps**:
1. Check if Tabler editor auto-initializes
2. If manual init needed, copy from working implementation
3. Ensure no conflicts with other JavaScript
4. Keep under 50 lines total JavaScript

#### Task 3.3: Verify Assets Loading
**Assigned Agent**: `backend-architect`  
**Duration**: 15 minutes  
**Description**: Ensure all Tabler editor assets load

**Steps**:
1. Verify in base.html:
   - Tabler CSS includes editor styles
   - Tabler JS includes editor functionality
2. Check for any missing dependencies
3. Ensure load order is correct

---

### Phase 4: Testing & Validation (45 minutes)

#### Task 4.1: Functional Testing
**Assigned Agent**: `flask-ui-developer`  
**Duration**: 30 minutes  
**Description**: Comprehensive testing with MCP Playwright

**Test Checklist**:
1. **Login**: 
   - URL: `http://localhost:5000/login`
   - Credentials: `kdresdell@gmail.com` / `admin123`
2. **Navigate**: Activity → Email Templates
3. **Verify Editor**:
   - [ ] NO TinyMCE watermark
   - [ ] Toolbar visible with all buttons
   - [ ] Bold button works
   - [ ] Italic button works
   - [ ] Alignment buttons work
   - [ ] List buttons work
   - [ ] Undo/Redo work
4. **Test Each Textarea**:
   - [ ] Intro Text editor works
   - [ ] Custom Message editor works
   - [ ] Conclusion Text editor works
5. **Compare with Settings Page**:
   - [ ] Same appearance
   - [ ] Same functionality
   - [ ] No branding/watermarks

**Screenshots Required**:
- `/test/playwright/email_template_no_tinymce.png`
- `/test/playwright/tabler_editor_working.png`
- `/test/playwright/comparison_with_settings.png`

#### Task 4.2: Create Test Script
**Assigned Agent**: `flask-ui-developer`  
**Duration**: 15 minutes  
**Description**: Create automated test

**File**: `/test/test_tabler_editor_integration.py`

```python
import unittest
from app import app

class TestTablerEditor(unittest.TestCase):
    def test_no_tinymce_class(self):
        # Verify tinymce class removed
        pass
    
    def test_editor_loads(self):
        # Verify Tabler editor loads
        pass
    
    def test_no_watermark(self):
        # Verify no TinyMCE branding
        pass
```

---

## 🚫 What NOT to Do

**ALL AGENTS MUST AVOID**:
1. DO NOT build a new editor from scratch
2. DO NOT install new packages
3. DO NOT modify database
4. DO NOT start a new Flask server (use existing on port 5000)
5. DO NOT create complex JavaScript (stay under 50 lines)
6. DO NOT touch search or filter functionality
7. DO NOT modify Activity model

---

## ✅ Success Criteria

1. **No TinyMCE Watermark**: Zero branding or "built with" messages
2. **Identical to Settings**: Same editor as unified_settings page
3. **Full Functionality**: All formatting buttons work
4. **Reused Code**: Using existing paid Tabler.io implementation
5. **Clean Removal**: No leftover TinyMCE code active
6. **Testing Proof**: Screenshots showing working editor

---

## 🔄 Rollback Plan

If issues occur:
1. `git status` to see changes
2. `git diff` to review modifications
3. `git checkout -- templates/email_template_customization.html` to revert
4. Database is safe (already fixed, no changes needed)

---

## 📊 Testing Matrix

| Feature | Unit Test | Browser Test | Screenshot | Agent |
|---------|-----------|--------------|------------|--------|
| TinyMCE Removed | ✅ | ✅ | ✅ | flask-ui-developer |
| Tabler Editor Loads | ✅ | ✅ | ✅ | flask-ui-developer |
| No Watermark | ❌ | ✅ | ✅ | flask-ui-developer |
| Toolbar Works | ❌ | ✅ | ✅ | js-code-reviewer |
| Rich Text Saves | ✅ | ✅ | ❌ | backend-architect |

---

## 🔑 Critical Information for Agents

### Server & Credentials
- **Flask Server**: Already running on `localhost:5000` (DO NOT START ANOTHER)
- **Login**: `kdresdell@gmail.com` / `admin123`
- **Test Activity ID**: 1 (or any existing activity)
- **MCP Playwright**: Available for browser testing

### File Locations
- **Template**: `/templates/email_template_customization.html`
- **JavaScript**: `/static/js/email-template-editor.js`
- **Base Template**: `/templates/base.html`
- **Working Example**: `/templates/unified_settings.html` (or in git history)

### Key Requirements
- User has PAID for Tabler.io Pro
- Editor already works in settings page
- Must REUSE existing implementation
- No new development needed

---

## 📅 Timeline

- **Phase 1**: 1 hour - Research and document existing implementation
- **Phase 2**: 30 minutes - Remove TinyMCE
- **Phase 3**: 1 hour - Apply Tabler.io editor
- **Phase 4**: 45 minutes - Testing and validation

**Total Duration**: ~3.5 hours

---

## 📝 Notes

- User showed screenshots proving Tabler editor works in settings
- TinyMCE was mistakenly added when paid solution already existed
- This is a REPLACEMENT task, not new development
- Priority is removing the embarrassing "Built with TinyMCE" watermark

---

**End of Plan**