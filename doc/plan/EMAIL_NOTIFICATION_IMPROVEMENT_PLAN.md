# Email Notification Interface Improvement Plan

## Executive Summary
This document outlines a comprehensive plan to improve the email notification interface in Minipass, transforming it from a basic text editor into a full-featured email template builder with WYSIWYG capabilities, variable management, and testing features.

## Current System Analysis

### Existing Architecture
- **Pre-compiled templates** stored in `/templates/email_templates/` with fixed HTML structure
- **Template compilation process** (`compileEmailTemplate.py`) that embeds images as base64 for email delivery
- **Text content management** through TinyMCE for intro/conclusion sections only
- **Fixed templates** (newPass, redeemPass, paymentReceived, payment_late, signup, survey_invitation) that users cannot modify structurally
- **Variable system** using Jinja2 syntax (e.g., `{{ pass_data.user.name }}`)
- **Settings storage** in database through SettingsManager with keys like `SUBJECT_pass_created`, `INTRO_pass_created`, etc.

### Current Limitations
- Users can only modify text content, not email design/layout
- No visual preview of final email
- Manual variable insertion without assistance
- No way to test emails before using them
- Single template per email type with no variations
- No mobile/responsive preview

## Proposed Improvements

## 1. Enhanced Email Editor Interface

### A. Visual Email Template Builder
- **Dual-mode editor**: Toggle between WYSIWYG and HTML source view
- **Live preview panel**: Side-by-side editing with real-time preview using sample data
- **Template sections**: Draggable blocks for header, content, footer, social links
- **Style presets**: Pre-designed color schemes and layouts users can choose from
- **Responsive design**: Automatic mobile-friendly email generation

### B. Advanced TinyMCE Integration
Upgrade TinyMCE configuration with email-specific plugins:
- Template plugin for reusable content blocks
- Variable insertion buttons in toolbar
- Image upload/management with automatic base64 conversion
- Email-safe CSS styles only (inline styles)
- Table editing tools for layout
- Color picker with brand color presets

## 2. Variable Management System

### A. Smart Variable Insertion
**Variable palette** - Sidebar with categorized available variables:

#### User Variables
- `{{ user.name }}` - User's full name
- `{{ user.email }}` - User's email address
- `{{ user.phone_number }}` - User's phone number

#### Pass/Passport Variables
- `{{ pass_data.pass_code }}` - Unique pass code
- `{{ pass_data.games_remaining }}` - Remaining uses
- `{{ pass_data.user_name }}` - Pass owner name
- `{{ pass_data.activity }}` - Activity name
- `{{ pass_data.sold_amt }}` - Pass price
- `{{ pass_data.pass_created_dt }}` - Creation date
- `{{ pass_data.paid_ind }}` - Payment status

#### Activity Variables
- `{{ activity.name }}` - Activity name
- `{{ activity.date }}` - Activity date
- `{{ activity.location }}` - Activity location
- `{{ activity.capacity }}` - Maximum capacity

#### Features
- **Click-to-insert buttons**: One-click insertion at cursor position
- **Variable validation**: Highlight and validate variables in real-time
- **Tooltips**: Show sample data when hovering over variables
- **Auto-complete**: Suggestions when typing `{{`
- **Custom variables**: User-defined variables with default values

### B. Template Variables Documentation
- In-editor help panel showing all available variables with descriptions
- Sample data preview for each variable
- Context-aware variable suggestions based on email type

## 3. Template Management

### A. Template Gallery
- **Pre-built templates**: Professional designs for each email type
  - Modern minimal
  - Classic professional
  - Colorful friendly
  - Holiday themed
  - Sport themed
- **Custom template storage**: Save and reuse custom designs
- **Template versioning**: Keep history of template changes
- **Import/Export**: Share templates between activities or organizations
- **Template marketplace**: Share templates with other users

### B. Responsive Design Tools
- Mobile/Desktop preview toggle
- Automatic responsive table conversion
- Media query support for advanced users
- Dark mode preview
- Email client preview (Gmail, Outlook, Apple Mail)

## 4. Test Email Functionality

### A. Test Email System
**Test button** for each email type with:
- Email address input field (with validation)
- Sample data selection:
  - Use real data from recent passes
  - Use dummy/preview data
  - Custom test data input
- Preview before sending in modal
- Delivery status tracking
- Bounce/error reporting

### B. Email Testing Features
- Send test to multiple recipients simultaneously
- A/B testing support for different versions
- Spam score checking (integrate with mail-tester API)
- Rendering tests across email clients
- Link validation
- Image loading tests
- Subject line preview in different clients

## 5. Technical Implementation Strategy

### Phase 1: Foundation (Week 1-2)
1. **Create new email editor component**
   - File: `/templates/partials/email_editor.html`
   - JavaScript: `/static/js/email-editor.js`
   - CSS: `/static/css/email-editor.css`

2. **Implement enhanced TinyMCE configuration**
   - Email-specific toolbar
   - Custom plugins for variables
   - Image handling improvements

3. **Build variable insertion toolbar**
   - Variable palette component
   - Click-to-insert functionality
   - Variable validation

4. **Create live preview system**
   - iframe sandboxing for security
   - Real-time preview updates
   - Sample data management

### Phase 2: Template System (Week 2-3)
1. **Develop template storage system**
   - Database schema updates
   - CRUD operations for templates
   - Template metadata management

2. **Create template gallery interface**
   - Grid/list view toggle
   - Template preview cards
   - Quick apply functionality

3. **Implement template import/export**
   - JSON format for templates
   - Validation on import
   - Bulk operations support

4. **Build responsive design preview**
   - Device frame visualization
   - Viewport size controls
   - Orientation toggle

### Phase 3: Testing Features (Week 3-4)
1. **Implement test email API endpoint**
   - Endpoint: `/api/email/test`
   - Rate limiting
   - Authentication required

2. **Create test email modal dialog**
   - Multi-step wizard
   - Recipient management
   - Data selection interface

3. **Add delivery tracking**
   - Status updates via WebSocket
   - Error reporting
   - Retry mechanism

4. **Integrate email validation**
   - HTML validation
   - CSS compatibility checks
   - Link verification

### Phase 4: Advanced Features (Week 4-5)
1. **Add template versioning**
   - Git-like version control
   - Diff viewer
   - Rollback functionality

2. **Implement A/B testing**
   - Variant creation
   - Test scheduling
   - Results analytics

3. **Create email analytics dashboard**
   - Open rates (if tracking enabled)
   - Test email statistics
   - Template usage metrics

4. **Build template sharing**
   - Export to marketplace
   - Rating system
   - Usage statistics

## 6. Database Schema Updates

### New Tables Required

```sql
-- Custom email templates
CREATE TABLE email_templates_custom (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    email_type VARCHAR(50) NOT NULL, -- pass_created, pass_redeemed, etc.
    html_content TEXT NOT NULL,
    css_content TEXT,
    variables_used JSON,
    thumbnail_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(255),
    organization_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Template version history
CREATE TABLE email_template_versions (
    id INTEGER PRIMARY KEY,
    template_id INTEGER NOT NULL,
    version_number INTEGER NOT NULL,
    html_content TEXT NOT NULL,
    css_content TEXT,
    changed_by VARCHAR(255),
    change_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES email_templates_custom(id)
);

-- Test email logs
CREATE TABLE email_test_logs (
    id INTEGER PRIMARY KEY,
    template_id INTEGER,
    email_type VARCHAR(50),
    recipient_email VARCHAR(255),
    test_data JSON,
    status VARCHAR(50), -- sent, failed, bounced
    error_message TEXT,
    delivery_time INTEGER, -- milliseconds
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Custom variables
CREATE TABLE email_variables (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    default_value TEXT,
    variable_type VARCHAR(50), -- string, number, date, boolean
    scope VARCHAR(50), -- global, activity, organization
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 7. Backward Compatibility Strategy

### Ensuring Nothing Breaks
1. **Keep existing template compilation process intact**
   - Maintain `compileEmailTemplate.py`
   - Preserve current folder structure
   - Keep base64 image embedding

2. **Maintain current settings structure**
   - Continue using existing settings keys
   - Add new settings with `_v2` suffix initially
   - Gradual migration path

3. **Feature flags for gradual rollout**
   ```python
   FEATURES = {
       'email_editor_v2': False,  # New editor
       'email_templates_custom': False,  # Custom templates
       'email_test_mode': True,  # Test emails
       'email_variables_panel': False  # Variable insertion
   }
   ```

4. **Migration path for existing templates**
   - Auto-import existing templates to new system
   - Preserve all current customizations
   - One-click migration tool

5. **Fallback mechanism**
   - Keep original email sending logic
   - Automatic fallback on error
   - Logging for debugging

## 8. UI/UX Improvements

### Interface Enhancements

1. **Navigation Improvements**
   - Replace tabs with vertical sidebar for email types
   - Breadcrumb navigation
   - Quick switcher (Cmd/Ctrl + K)

2. **Editor Enhancements**
   - Auto-save every 30 seconds
   - Draft status indicator
   - Undo/redo with history
   - Full-screen editing mode

3. **Productivity Features**
   - Keyboard shortcuts for common actions
   - Template quick preview on hover
   - Bulk operations for multiple templates
   - Search and filter capabilities

4. **Help and Documentation**
   - Contextual help tooltips
   - Interactive tutorials
   - Video guides
   - Sample template library

## 9. Security Considerations

### Security Measures

1. **Input Validation**
   - HTML sanitization with DOMPurify
   - Variable injection prevention
   - CSS validation for email safety
   - Script tag blocking

2. **Access Control**
   - Template permissions per user role
   - Organization-level template isolation
   - Audit logging for all changes
   - IP-based rate limiting

3. **Data Protection**
   - Encryption for sensitive template data
   - Secure test email data handling
   - PII masking in logs
   - GDPR compliance for email data

4. **Testing Security**
   - Rate limit test emails (10 per hour)
   - Recipient whitelist option
   - Captcha for bulk testing
   - Abuse detection and blocking

## 10. Performance Optimizations

### Performance Improvements

1. **Frontend Optimizations**
   - Lazy load template previews
   - Virtual scrolling for template gallery
   - Code splitting for editor components
   - WebWorker for preview rendering

2. **Backend Optimizations**
   - Template compilation caching
   - Redis cache for frequently used templates
   - Database query optimization
   - CDN for template assets

3. **Email Delivery**
   - Queue system for bulk emails
   - Parallel processing for tests
   - Connection pooling for SMTP
   - Retry mechanism with exponential backoff

4. **Image Handling**
   - Automatic image optimization
   - WebP conversion with fallback
   - Lazy loading in previews
   - CDN delivery for images

## Implementation Timeline

### Week 1-2: Foundation
- Set up new editor infrastructure
- Implement basic WYSIWYG functionality
- Create variable insertion system
- Build preview panel

### Week 2-3: Templates
- Design template storage
- Create template gallery
- Implement import/export
- Add responsive preview

### Week 3-4: Testing
- Build test email system
- Create delivery tracking
- Add validation tools
- Implement spam checking

### Week 4-5: Polish
- Add advanced features
- Optimize performance
- Complete security audit
- User documentation

### Week 5-6: Testing & Launch
- QA testing
- User acceptance testing
- Bug fixes
- Gradual rollout

## Success Metrics

### Key Performance Indicators
- **Adoption Rate**: % of users using new editor
- **Template Creation**: Average templates created per user
- **Test Email Usage**: Number of test emails sent
- **Error Reduction**: Decrease in email-related support tickets
- **User Satisfaction**: Survey scores for email features

### Monitoring Plan
- Analytics dashboard for feature usage
- Error tracking with Sentry
- Performance monitoring with New Relic
- User feedback collection system

## Risk Mitigation

### Identified Risks and Mitigation Strategies

1. **Risk**: Breaking existing email functionality
   - **Mitigation**: Comprehensive testing suite, feature flags, gradual rollout

2. **Risk**: Performance degradation
   - **Mitigation**: Load testing, caching strategy, CDN usage

3. **Risk**: Security vulnerabilities
   - **Mitigation**: Security audit, input sanitization, rate limiting

4. **Risk**: User adoption challenges
   - **Mitigation**: Training materials, intuitive UI, migration assistance

5. **Risk**: Email client compatibility
   - **Mitigation**: Extensive testing, fallback templates, progressive enhancement

## Next Steps

1. **Immediate Actions**
   - Review and approve this plan
   - Allocate development resources
   - Set up development environment
   - Create feature branch

2. **Phase 1 Start**
   - Begin foundation development
   - Set up testing framework
   - Create initial UI mockups
   - Start documentation

3. **Stakeholder Communication**
   - Present plan to team
   - Gather feedback
   - Adjust timeline if needed
   - Set up progress tracking

## Conclusion

This comprehensive plan addresses all aspects of improving the email notification interface while ensuring backward compatibility and system stability. The phased approach allows for gradual implementation with minimal risk to existing functionality. The focus on user experience, testing capabilities, and template flexibility will significantly enhance the email management capabilities of the Minipass platform.