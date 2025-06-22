# Survey System Module Plan

**Date:** 2025-06-22  
**Feature:** Simple and Intuitive Survey System for Minipass Activities

## 📋 Overview

Implement a comprehensive survey system that allows Minipass admins to collect feedback from activity participants through email-based surveys. The system will be fully integrated with the existing activity dashboard and follow all established UI/UX patterns.

## 🎯 Core Requirements

### Survey Templates
- **Quick Setup**: Pre-defined templates with 5 questions (4 multiple-choice + 1 open-ended)
- **Reusable**: Templates can be used across multiple activities
- **Customizable**: Basic customization of questions and options

### Admin Interface
- **Dashboard Integration**: Add survey button on activity-dashboard/<id> page
- **Modal Interface**: Survey creation through modal/form
- **Template Selection**: Choose from available survey templates
- **Passport Type Targeting**: Select which passport type users receive surveys

### Survey Distribution
- **Email Links**: Generate unique survey links for each participant
- **Mobile-Friendly**: Responsive design optimized for mobile completion
- **Quick Completion**: Maximum 1-minute completion time

### Results & Analytics
- **Dashboard Display**: Survey results shown at bottom of activity dashboard
- **Response Tracking**: Track completion rates and responses
- **Visual Presentation**: Clean, modern results display

## 🗄️ Database Schema Design

### New Models

#### SurveyTemplate
```python
class SurveyTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    questions = db.Column(db.Text)  # JSON string containing questions
    created_by = db.Column(db.Integer, db.ForeignKey("admin.id"))
    created_dt = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(50), default="active")  # active, archived
    
    # Relationships
    surveys = db.relationship("Survey", backref="template", lazy=True)
```

#### Survey
```python
class Survey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey("activity.id"), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey("survey_template.id"), nullable=False)
    passport_type_id = db.Column(db.Integer, db.ForeignKey("passport_type.id"), nullable=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    survey_token = db.Column(db.String(32), unique=True, nullable=False)  # For URL generation
    created_by = db.Column(db.Integer, db.ForeignKey("admin.id"))
    created_dt = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(50), default="active")  # active, closed, archived
    email_sent = db.Column(db.Boolean, default=False)
    email_sent_dt = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    activity = db.relationship("Activity", backref="surveys")
    passport_type = db.relationship("PassportType", backref="surveys")
    responses = db.relationship("SurveyResponse", backref="survey", lazy=True)
```

#### SurveyResponse
```python
class SurveyResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey("survey.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    passport_id = db.Column(db.Integer, db.ForeignKey("passport.id"), nullable=True)
    response_token = db.Column(db.String(32), unique=True, nullable=False)
    responses = db.Column(db.Text)  # JSON string containing all answers
    completed = db.Column(db.Boolean, default=False)
    completed_dt = db.Column(db.DateTime, nullable=True)
    started_dt = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    
    # Relationships
    user = db.relationship("User", backref="survey_responses")
    passport = db.relationship("Passport", backref="survey_responses")
```

## 🏗️ Implementation Plan

### Phase 1: Database Models & Migrations
- [ ] Create SurveyTemplate model
- [ ] Create Survey model  
- [ ] Create SurveyResponse model
- [ ] Create database migration script
- [ ] Test model relationships and constraints

### Phase 2: Survey Templates System
- [ ] Create default survey templates with sample questions
- [ ] Implement template CRUD operations
- [ ] Build template management interface
- [ ] Add template validation logic

### Phase 3: Admin Interface Integration
- [ ] Add survey button to activity dashboard
- [ ] Create survey creation modal
- [ ] Implement template selection dropdown
- [ ] Add passport type targeting selection
- [ ] Integrate with existing admin authentication

### Phase 4: Survey Distribution
- [ ] Generate unique survey tokens
- [ ] Create email template for survey invitations
- [ ] Implement email sending functionality
- [ ] Add survey link generation utilities
- [ ] Track email delivery status

### Phase 5: Public Survey Interface
- [ ] Create mobile-friendly survey form
- [ ] Implement survey response collection
- [ ] Add form validation and error handling
- [ ] Create thank you page
- [ ] Add response tracking

### Phase 6: Results & Analytics
- [ ] Build survey results display component
- [ ] Add results section to activity dashboard
- [ ] Implement response statistics
- [ ] Create visual charts for responses
- [ ] Add export functionality

### Phase 7: Testing & Polish
- [ ] Write comprehensive unit tests
- [ ] Implement integration tests
- [ ] Add error handling and edge cases
- [ ] Performance optimization
- [ ] UI/UX refinements

## 🚀 Routes & Endpoints

### Admin Routes
```python
# Survey Management
@app.route("/activity-dashboard/<int:activity_id>/create-survey", methods=["GET", "POST"])
@app.route("/survey/<int:survey_id>/edit", methods=["GET", "POST"])
@app.route("/survey/<int:survey_id>/delete", methods=["POST"])
@app.route("/survey/<int:survey_id>/send-emails", methods=["POST"])
@app.route("/survey/<int:survey_id>/results")

# Template Management
@app.route("/survey-templates")
@app.route("/survey-templates/create", methods=["GET", "POST"])
@app.route("/survey-templates/<int:template_id>/edit", methods=["GET", "POST"])
@app.route("/survey-templates/<int:template_id>/delete", methods=["POST"])
```

### Public Routes
```python
# Survey Participation
@app.route("/survey/<survey_token>")
@app.route("/survey/<survey_token>/submit", methods=["POST"])
@app.route("/survey/<survey_token>/thank-you")
```

## 🎨 UI/UX Implementation

### Activity Dashboard Integration
- **Location**: Bottom of activity dashboard page
- **Button**: Primary action button "Create Survey" in dashboard header
- **Modal**: Survey creation modal following existing patterns
- **Results Section**: New card section showing survey results

### Survey Creation Modal
```html
<!-- Survey Creation Modal -->
<div class="modal modal-blur fade" id="create-survey-modal">
  <div class="modal-dialog modal-lg">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">Create Activity Survey</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">
        <!-- Survey form content -->
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
        <button type="submit" class="btn btn-primary">Create Survey</button>
      </div>
    </div>
  </div>
</div>
```

### Mobile Survey Form
- **Responsive Design**: Mobile-first approach using Tabler responsive classes
- **Progress Indicator**: Show completion progress
- **Smooth Transitions**: Animated question transitions
- **Clear CTAs**: Large, accessible buttons

## 📧 Email Templates

### Survey Invitation Email
```html
<!-- templates/email_templates/survey_invitation/ -->
<div class="email-content">
  <h2>We'd love your feedback!</h2>
  <p>Hi {{ user.name }},</p>
  <p>How was your experience with {{ activity.name }}? We'd love to hear your thoughts!</p>
  <a href="{{ survey_url }}" class="btn btn-primary">Take Survey (1 minute)</a>
  <p><small>This survey will only take about 1 minute to complete.</small></p>
</div>
```

## 🧪 Testing Strategy

### Unit Tests
- **Model Tests**: Test all database models and relationships
- **Route Tests**: Test all endpoints and response codes
- **Form Tests**: Test survey form validation
- **Email Tests**: Test email template rendering and sending

### Integration Tests
- **End-to-End Flow**: Test complete survey creation to response workflow
- **Dashboard Integration**: Test survey button and modal functionality
- **Email Delivery**: Test survey invitation email sending
- **Response Collection**: Test survey form submission and data storage

### Test Files
```python
# test_survey_models.py - Database model tests
# test_survey_routes.py - Route and endpoint tests
# test_survey_forms.py - Form validation tests
# test_survey_email.py - Email template and sending tests
# test_survey_integration.py - End-to-end integration tests
```

## 📱 Mobile Optimization

### Design Principles
- **Touch-Friendly**: Large touch targets (minimum 44px)
- **Fast Loading**: Optimized images and minimal JavaScript
- **Offline Resilience**: Handle poor connectivity gracefully
- **Thumb Navigation**: Key actions within thumb reach

### Technical Implementation
- **Responsive Grid**: CSS Grid with mobile breakpoints
- **Progressive Enhancement**: Works without JavaScript
- **Optimized Images**: WebP format with fallbacks
- **Caching Strategy**: Service worker for offline capability

## 🔐 Security Considerations

### Data Protection
- **Token Security**: Cryptographically secure survey tokens
- **Response Anonymization**: Option to anonymize responses
- **Data Retention**: Configurable data retention policies
- **GDPR Compliance**: User consent and data deletion options

### Access Control
- **Admin Authentication**: Existing admin authentication system
- **Survey Access**: Token-based access for public surveys
- **Rate Limiting**: Prevent survey spam and abuse
- **Input Validation**: Sanitize all user inputs

## 🚀 Performance Optimization

### Database Optimization
- **Indexes**: Add indexes on frequently queried fields
- **Query Optimization**: Use joins and eager loading
- **Connection Pooling**: Optimize database connections
- **Caching**: Cache survey templates and results

### Frontend Optimization
- **Lazy Loading**: Load survey questions progressively
- **Minification**: Minify CSS and JavaScript
- **CDN Integration**: Use CDN for static assets
- **Image Optimization**: Compress and optimize images

## 📊 Analytics & Reporting

### Key Metrics
- **Response Rate**: Percentage of invited users who responded
- **Completion Rate**: Percentage of users who completed the survey
- **Time to Complete**: Average time to complete survey
- **Response Quality**: Analysis of open-ended responses

### Reporting Features
- **Dashboard Widgets**: Key metrics on activity dashboard
- **Export Options**: CSV/PDF export of responses
- **Visual Charts**: Charts for multiple-choice responses
- **Trend Analysis**: Response trends over time

## 🔄 Future Enhancements

### Advanced Features
- **Question Logic**: Conditional questions based on previous answers
- **Custom Templates**: Allow admins to create custom question templates
- **Multi-language Support**: Support for multiple languages
- **Advanced Analytics**: Sentiment analysis for open-ended responses

### Integration Opportunities
- **Notification System**: In-app notifications for survey responses
- **Passport Integration**: Link survey completion to passport rewards
- **Automated Triggers**: Automatic survey sending based on activity events
- **Third-party Analytics**: Integration with Google Analytics or similar

## 🎯 Success Criteria

### Functionality
- ✅ Admins can create surveys in under 2 minutes
- ✅ Survey completion takes maximum 1 minute
- ✅ 95% of surveys load correctly on mobile devices
- ✅ Email delivery success rate above 95%

### User Experience
- ✅ Clean, intuitive interface following Tabler UI patterns
- ✅ Responsive design works on all device sizes
- ✅ Survey results display clearly on activity dashboard
- ✅ Error messages are helpful and actionable

### Technical
- ✅ All tests pass with 90%+ code coverage
- ✅ Database queries optimized for performance
- ✅ Secure handling of user data and responses
- ✅ Follows existing code patterns and conventions

---

## 📝 Implementation Notes

### Default Survey Template
```json
{
  "name": "Activity Feedback Survey",
  "questions": [
    {
      "id": 1,
      "type": "multiple_choice",
      "question": "How would you rate your overall experience?",
      "options": ["Excellent", "Good", "Fair", "Poor"],
      "required": true
    },
    {
      "id": 2,
      "type": "multiple_choice",
      "question": "How likely are you to recommend this activity to others?",
      "options": ["Very likely", "Likely", "Unlikely", "Very unlikely"],
      "required": true
    },
    {
      "id": 3,
      "type": "multiple_choice",
      "question": "What did you like most about this activity?",
      "options": ["Instruction quality", "Facilities", "Organization", "Other participants"],
      "required": false
    },
    {
      "id": 4,
      "type": "multiple_choice",
      "question": "Would you participate in this activity again?",
      "options": ["Definitely", "Probably", "Maybe", "No"],
      "required": true
    },
    {
      "id": 5,
      "type": "open_ended",
      "question": "Any additional feedback or suggestions for improvement?",
      "required": false,
      "max_length": 500
    }
  ]
}
```

### URL Structure
- **Survey Creation**: `/activity-dashboard/{activity_id}#create-survey`
- **Public Survey**: `/survey/{survey_token}`
- **Survey Results**: `/activity-dashboard/{activity_id}#survey-results`
- **Template Management**: `/admin/survey-templates`

This comprehensive plan provides a solid foundation for implementing the survey system while maintaining consistency with the existing Minipass application architecture and UI patterns.