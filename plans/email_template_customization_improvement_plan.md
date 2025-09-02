# Email Template Customization UI/UX Improvement Plan

**Created**: January 2, 2025  
**Project**: Minipass Email Template Customization Interface  
**Status**: Ready for Implementation

## 🎯 Executive Summary

Transform the email customization interface from "ugly and inefficient" to beautiful, mobile-friendly, and intuitive. This plan includes agent assignments, testing requirements, and credentials for seamless implementation.

## ⚠️ CRITICAL REMINDERS FOR ALL AGENTS

### Environment Setup
- **Flask Server**: Already running on `localhost:5000` in debug mode (DO NOT START ANOTHER!)
- **Database**: SQLite at `instance/minipass.db`
- **Virtual Environment**: Already activated at `venv/`
- **MCP Playwright**: Available for browser testing

### Testing Credentials
- **Admin Login**: 
  - URL: `http://localhost:5000/login`
  - Username: `admin@minipass.com` (or check session)
  - Password: `admin123` (or check app.py for test credentials)
- **Test Email**: `kdresdell@example.com` (for sending test emails)
- **Test Activity ID**: Use existing activities from database

### Testing Requirements
- **ALL CHANGES MUST BE TESTED**
- **Unit Tests**: Create in `/test/` folder
- **Integration Tests**: Use MCP Playwright
- **Manual Testing**: Use running Flask server on port 5000
- **Test File Naming**: `test_[feature_name].py`

---

## 📋 Implementation Tasks with Agent Assignments

### Phase 1: Core UI Restructuring (2-3 days)

#### Task 1.1: Redesign HTML Template Structure
**Assigned Agent**: `flask-ui-developer`  
**Duration**: 4-6 hours  
**Description**: Convert email_template_customization.html to mobile-first responsive layout with accordion sections

**Implementation Steps**:
1. Read current template: `/templates/email_template_customization.html`
2. Create backup before modifying
3. Implement accordion-based form sections
4. Add prominent activity header with avatar component
5. Replace inline iframe with modal trigger button

**Testing**:
- Tool: MCP Playwright browser testing
- Create test: `/test/test_email_template_ui.py`
- Test responsive layout at 375px (mobile) and 1920px (desktop)
- Verify accordion expand/collapse functionality
- Check activity context visibility

```python
# Test template for agent
import unittest
from app import app

class TestEmailTemplateUI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        
    def test_mobile_responsive_layout(self):
        # Test at 375px width
        pass
        
    def test_accordion_sections(self):
        # Test collapsible sections
        pass
```

#### Task 1.2: Implement Preview Modal
**Assigned Agent**: `flask-ui-developer`  
**Duration**: 3-4 hours  
**Description**: Create modal-based preview system with device toggle

**Implementation Steps**:
1. Add modal HTML structure to template
2. Include device toggle buttons (desktop/mobile)
3. Create iframe container with responsive classes
4. Add template type switcher in modal footer

**Testing**:
- Tool: MCP Playwright
- Test modal open/close functionality
- Verify device toggle changes iframe dimensions
- Test preview URL generation
- Create test: `/test/test_preview_modal.py`

#### Task 1.3: Add Minimal JavaScript
**Assigned Agent**: `js-code-reviewer`  
**Duration**: 2-3 hours  
**Description**: Implement minimal JavaScript for interactivity (<50 lines total)

**Implementation Steps**:
1. Create `/static/js/email-template-editor.js`
2. Implement functions:
   - `initTinyMCE()` - 8 lines max
   - `openPreviewModal()` - 9 lines max
   - `toggleDevice()` - 6 lines max
   - `previewLogo()` - 7 lines max
3. Use event delegation pattern
4. Add cleanup on page unload

**Testing**:
- Tool: Browser console + MCP Playwright
- Test each function independently
- Verify no memory leaks
- Check error handling
- Create test: `/test/test_email_template_js.py`

```javascript
// Testing checklist for JS agent
// 1. Open browser console at http://localhost:5000/activity/1/email-templates
// 2. Test each function manually
// 3. Check for console errors
// 4. Verify event listeners are properly attached
```

---

### Phase 2: Rich Text & Media Features (1-2 days)

#### Task 2.1: TinyMCE Integration
**Assigned Agent**: `flask-ui-developer`  
**Duration**: 2-3 hours  
**Description**: Replace textareas with TinyMCE rich text editor

**Implementation Steps**:
1. Verify TinyMCE is loaded in `base.html`
2. Add class `tinymce` to textarea fields
3. Configure minimal toolbar (bold, italic, links, lists)
4. Set up auto-save draft functionality

**Testing**:
- Tool: MCP Playwright
- Navigate to: `http://localhost:5000/activity/1/email-templates`
- Test rich text formatting
- Verify HTML sanitization
- Test character limits
- Create test: `/test/test_tinymce_integration.py`

#### Task 2.2: Logo Upload Feature
**Assigned Agent**: `backend-architect`  
**Duration**: 3-4 hours  
**Description**: Implement owner logo upload and management

**Backend Implementation**:
1. Add migration for `logo_filename` field on Activity model
2. Create file upload handler in `app.py`
3. Implement cleanup for old logos
4. Add logo URL generation with fallback

**Frontend Implementation** (flask-ui-developer):
1. Add logo upload section to template
2. Implement preview functionality
3. Add to all email templates

**Testing**:
- Tool: Bash + MCP Playwright
- Test file upload with various formats (jpg, png, gif)
- Verify old logo cleanup
- Test fallback to default logo
- Create test: `/test/test_logo_upload.py`

```python
# Backend test template
def test_logo_upload():
    # Test with Flask test client
    with app.test_client() as client:
        # Login first
        client.post('/login', data={'email': 'admin@minipass.com', 'password': 'admin123'})
        
        # Upload logo
        data = {'logo': (io.BytesIO(b"fake image data"), 'test.jpg')}
        response = client.post('/activity/1/upload-logo', data=data)
        assert response.status_code == 200
```

---

### Phase 3: Backend Enhancements (1 day)

#### Task 3.1: Live Preview System
**Assigned Agent**: `backend-architect`  
**Duration**: 3-4 hours  
**Description**: Create live preview endpoint without database saves

**Implementation Steps**:
1. Create new route: `/activity/<id>/email-preview-live`
2. Accept POST with form data
3. Generate preview without saving
4. Support mobile/desktop modes
5. Add caching if needed

**Testing**:
- Tool: curl + MCP Playwright
- Test with curl: `curl -X POST http://localhost:5000/activity/1/email-preview-live -d '{"template_type":"newPass"}'`
- Verify preview updates without saving
- Test mobile vs desktop rendering
- Create test: `/test/test_live_preview.py`

#### Task 3.2: Content Security
**Assigned Agent**: `backend-architect`  
**Duration**: 2-3 hours  
**Description**: Implement HTML sanitization and security measures

**Implementation Steps**:
1. Install bleach: `pip install bleach`
2. Create ContentSanitizer class
3. Sanitize all rich text inputs
4. Validate URLs for CTAs
5. Add XSS prevention

**Testing**:
- Create test: `/test/test_content_security.py`
- Test XSS attempts
- Verify allowed HTML tags
- Test URL validation
- Check SQL injection prevention

```python
# Security test examples
def test_xss_prevention():
    malicious_input = "<script>alert('XSS')</script>"
    sanitized = ContentSanitizer.sanitize_html(malicious_input)
    assert '<script>' not in sanitized
```

---

### Phase 4: CSS & Polish (1 day)

#### Task 4.1: Mobile-First CSS
**Assigned Agent**: `ui-designer` + `flask-ui-developer`  
**Duration**: 3-4 hours  
**Description**: Create beautiful, responsive styles

**Implementation Steps**:
1. Create `/static/css/email-template-customization.css`
2. Mobile-first breakpoints (375px, 768px, 1024px)
3. Device preview styles
4. Touch-friendly buttons
5. Smooth transitions

**Testing**:
- Tool: MCP Playwright with different viewports
- Test at: 375px (iPhone), 768px (iPad), 1920px (Desktop)
- Verify touch targets are 44x44px minimum
- Test landscape orientation
- Create visual regression tests

#### Task 4.2: Final Integration Testing
**Assigned Agent**: `flask-ui-developer` + `js-code-reviewer`  
**Duration**: 2-3 hours  
**Description**: Complete end-to-end testing

**Testing Checklist**:
1. Login to admin panel
2. Navigate to activity dashboard
3. Click "Email Templates" for an activity
4. Test each template type
5. Upload logo and hero image
6. Use rich text editor
7. Preview in modal (desktop + mobile)
8. Send test email
9. Save changes
10. Verify in database

---

## 📊 Testing Matrix

| Feature | Unit Test | Integration Test | Manual Test | Agent |
|---------|-----------|-----------------|-------------|--------|
| Accordion Layout | ✅ | ✅ | ✅ | flask-ui-developer |
| Preview Modal | ✅ | ✅ | ✅ | flask-ui-developer |
| TinyMCE | ✅ | ✅ | ✅ | flask-ui-developer |
| Logo Upload | ✅ | ✅ | ✅ | backend-architect |
| Live Preview | ✅ | ✅ | ✅ | backend-architect |
| Mobile Responsive | ❌ | ✅ | ✅ | ui-designer |
| Content Security | ✅ | ✅ | ✅ | backend-architect |
| JavaScript Functions | ✅ | ✅ | ✅ | js-code-reviewer |

---

## 🚀 Deployment Checklist

### Pre-Implementation
- [ ] Backup current `email_template_customization.html`
- [ ] Backup database
- [ ] Document current email template data structure
- [ ] Verify Flask server running on port 5000

### During Implementation
- [ ] Create feature branch: `git checkout -b email-template-ui-improvement`
- [ ] Run tests after each major change
- [ ] Commit frequently with descriptive messages
- [ ] Keep JavaScript under 50 lines total

### Post-Implementation
- [ ] Run full test suite: `python -m pytest test/`
- [ ] Test on real mobile devices
- [ ] Verify email sending still works
- [ ] Check memory usage stays under 512MB
- [ ] Create PR with screenshots

---

## 📝 Agent-Specific Instructions

### For flask-ui-developer:
- Use Tabler.io components exclusively
- Server-side rendering with Jinja2
- Test with MCP Playwright browser tools
- Create unit tests in `/test/` folder

### For backend-architect:
- Keep SQLite migrations simple
- Use existing Flask patterns from app.py
- Test with Flask test client
- Implement proper error handling

### For js-code-reviewer:
- Maximum 10 lines per function
- Use event delegation
- No external libraries except TinyMCE
- Test in browser console first

### For ui-designer:
- Mobile-first approach
- Use existing Tabler.io classes
- Maintain consistency with current design
- Test at multiple breakpoints

---

## 🎯 Success Metrics

1. **Mobile Score**: 100% usable on 375px screens
2. **JavaScript Size**: < 50 lines total
3. **Page Load**: < 2 seconds
4. **Memory Usage**: < 512MB container limit
5. **Test Coverage**: > 80% for new code
6. **User Satisfaction**: "Beautiful and intuitive"

---

## 📅 Timeline

- **Day 1-2**: Phase 1 (Core UI)
- **Day 3-4**: Phase 2 (Rich Text & Media)
- **Day 5**: Phase 3 (Backend)
- **Day 6**: Phase 4 (Polish & Testing)

**Total Duration**: 6 days (within sprint constraint)

---

## 🔥 Common Pitfalls to Avoid

1. **DO NOT** start a new Flask server (use existing on port 5000)
2. **DO NOT** forget to test after each change
3. **DO NOT** use complex JavaScript frameworks
4. **DO NOT** modify database schema without migration
5. **DO NOT** forget mobile testing
6. **DO NOT** skip unit tests
7. **DO NOT** commit without testing

---

## 📞 Support & Questions

- Flask server issues: Check `python app.py` output
- Database issues: Check `instance/minipass.db`
- JavaScript errors: Browser console (F12)
- Testing issues: Run with `-v` flag for verbose output
- UI issues: Use MCP Playwright screenshot tool

This plan ensures every agent knows exactly what to do, how to test it, and what credentials to use. The clear assignment of responsibilities and testing requirements will prevent the common issues of forgetting credentials, server setup, and testing protocols.