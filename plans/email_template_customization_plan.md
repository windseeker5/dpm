# Email Template Customization Plan
**Date:** August 31, 2025  
**Version:** 2.0 (Ultra-Simplified)  
**Status:** Planning Phase

## Executive Summary
Enable per-activity email template customization with the absolute minimal implementation complexity. Users can customize text content and images for each activity's emails without any JavaScript, using a simple form-based approach that leverages existing patterns in the codebase.

## Current System Analysis

### What We Have
1. **Email Templates:** 6 compiled templates in `templates/email_templates/`
   - newPass (passport creation)
   - paymentReceived
   - latePayment  
   - signup
   - redeemPass
   - survey_invitation

2. **Template Variables:** Already using Jinja2 placeholders
   - `{{title}}`
   - `{{intro_text}}`
   - `{{body_text}}`
   - `{{footer_text}}`
   - `{{button_text}}`

3. **Existing Patterns We Can Reuse:**
   - Setting model (key-value storage)
   - File upload system (for images)
   - Form-based UI patterns throughout the app

## ULTRA-SIMPLIFIED APPROACH

### The Simplest Possible Implementation

#### Option 1: JSON in Activity Table (SIMPLEST)
Instead of creating new tables, add a single JSON column to the Activity model:

```python
class Activity(db.Model):
    # ... existing fields ...
    email_templates = db.Column(db.JSON, nullable=True, default={})
```

Store customizations as:
```json
{
  "newPass": {
    "title": "Welcome to Golf Tournament 2025!",
    "intro_text": "Your pass is ready...",
    "hero_image": "golf_hero_2025.jpg"
  },
  "paymentReceived": {
    "title": "Payment Confirmed!",
    "intro_text": "Thank you for your payment..."
  }
}
```

**Pros:**
- One migration, one field
- No new models or tables
- Reuses existing JSON support
- Dead simple to implement

**Cons:**
- Less queryable (but we don't need complex queries)

#### Option 2: Reuse Setting Model Pattern (MOST CONSISTENT)
Use the existing Setting model with prefixed keys:

```python
# Store as: "activity_42_newPass_title" = "Welcome!"
key = f"activity_{activity_id}_{template_type}_{field}"
Setting.query.filter_by(key=key).first()
```

**Pros:**
- No database changes at all
- Follows existing patterns
- Can start using immediately

**Cons:**
- More database queries
- Settings table gets larger

### Recommended: Option 1 (JSON Column)
The JSON approach is the cleanest and simplest, requiring minimal code changes.

## User Interface Design

### Desktop Wireframe

```
┌─────────────────────────────────────────────────────────────────┐
│ Activity: Golf Tournament 2025 > Email Templates                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [New Pass] [Payment] [Late Payment] [Survey] [Redemption]      │
│  ─────────                                                      │
│                                                                  │
│  ┌──────────────────────┬────────────────────────────────┐     │
│  │ CUSTOMIZE             │ PREVIEW                        │     │
│  │                      │                                 │     │
│  │ □ Use Custom Template│ ┌────────────────────────┐     │     │
│  │                      │ │                        │     │     │
│  │ Title:               │ │    [Hero Image]       │     │     │
│  │ [_______________]    │ │                        │     │     │
│  │                      │ ├────────────────────────┤     │     │
│  │ Intro Text:          │ │                        │     │     │
│  │ [_______________]    │ │    Welcome!            │     │     │
│  │ [_______________]    │ │                        │     │     │
│  │                      │ │    Your pass is ready  │     │     │
│  │ Body Text:           │ │                        │     │     │
│  │ [_______________]    │ │    [QR Code]           │     │     │
│  │ [_______________]    │ │                        │     │     │
│  │ [_______________]    │ │    Thank you!          │     │     │
│  │                      │ │                        │     │     │
│  │ Hero Image:          │ └────────────────────────┘     │     │
│  │ [Choose File]        │                                │     │
│  │                      │ [Update Preview]               │     │
│  │ [Save Changes]       │                                │     │
│  └──────────────────────┴────────────────────────────────┘     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Mobile Wireframe

```
┌─────────────────────┐
│ Golf Tournament     │
│ Email Templates     │
├─────────────────────┤
│ [New] [Pay] [Late]  │
│ ────                │
├─────────────────────┤
│ □ Use Custom        │
│                     │
│ Title:              │
│ [_________________] │
│                     │
│ Intro Text:         │
│ [_________________] │
│ [_________________] │
│                     │
│ Body Text:          │
│ [_________________] │
│ [_________________] │
│                     │
│ Hero Image:         │
│ [Choose File]       │
│                     │
│ [Save Changes]      │
│                     │
│ [Preview Email ▼]   │
├─────────────────────┤
│ Email Preview       │
│ ┌─────────────────┐ │
│ │                 │ │
│ │  [Hero Image]   │ │
│ │                 │ │
│ │   Welcome!      │ │
│ │                 │ │
│ │  Your pass...   │ │
│ │                 │ │
│ │   [QR Code]     │ │
│ │                 │ │
│ └─────────────────┘ │
└─────────────────────┘
```

## Implementation Steps

### Phase 1: Database (30 minutes)
```python
# Single migration adding JSON column
class Activity(db.Model):
    email_templates = db.Column(db.JSON, nullable=True, default={})
```

### Phase 2: Template Helper (1 hour)
```python
def get_email_context(activity_id, template_type, base_context):
    """Merge activity customizations with defaults"""
    activity = Activity.query.get(activity_id)
    if activity and activity.email_templates:
        custom = activity.email_templates.get(template_type, {})
        base_context.update(custom)
    return base_context
```

### Phase 3: Simple UI (2-3 hours)
```python
@app.route('/activity/<int:activity_id>/email-templates')
def email_templates(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    return render_template('email_customizer.html', 
                         activity=activity,
                         templates=TEMPLATE_TYPES)

@app.route('/activity/<int:activity_id>/email-templates/save', methods=['POST'])
def save_email_template(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    
    # Get or initialize templates
    if not activity.email_templates:
        activity.email_templates = {}
    
    template_type = request.form.get('template_type')
    
    # Handle file upload
    if 'hero_image' in request.files:
        file = request.files['hero_image']
        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join('static/uploads/email_heroes', filename))
            activity.email_templates[template_type]['hero_image'] = filename
    
    # Save text fields
    activity.email_templates[template_type] = {
        'title': request.form.get('title'),
        'intro_text': request.form.get('intro_text'),
        'body_text': request.form.get('body_text'),
        'use_custom': bool(request.form.get('use_custom'))
    }
    
    db.session.commit()
    flash('✅ Email template updated')
    return redirect(url_for('email_templates', activity_id=activity_id))
```

### Phase 4: Integration (1 hour)
Modify `send_email()` to check for activity customizations:
```python
# In send_email or send_email_async
if activity_id and template_name:
    context = get_email_context(activity_id, template_name, context)
```

## UI Implementation Details

### Form Structure (Pure HTML/Tabler)
```html
<form method="POST" action="/activity/{{ activity.id }}/email-templates/save" 
      enctype="multipart/form-data">
  
  <!-- Template Type Tabs -->
  <div class="card">
    <div class="card-header">
      <ul class="nav nav-tabs card-header-tabs">
        <li class="nav-item">
          <button type="submit" name="template_type" value="newPass" 
                  class="nav-link active">New Pass</button>
        </li>
        <li class="nav-item">
          <button type="submit" name="template_type" value="paymentReceived" 
                  class="nav-link">Payment Received</button>
        </li>
      </ul>
    </div>
    
    <div class="card-body">
      <div class="row">
        <!-- Left: Form Fields -->
        <div class="col-md-6">
          <div class="form-check mb-3">
            <input type="checkbox" class="form-check-input" 
                   name="use_custom" id="use_custom">
            <label class="form-check-label" for="use_custom">
              Use Custom Template
            </label>
          </div>
          
          <div class="mb-3">
            <label class="form-label">Title</label>
            <input type="text" class="form-control" name="title" 
                   placeholder="Welcome to {{ activity.name }}!">
          </div>
          
          <div class="mb-3">
            <label class="form-label">Introduction Text</label>
            <textarea class="form-control" name="intro_text" rows="3"></textarea>
          </div>
          
          <div class="mb-3">
            <label class="form-label">Hero Image</label>
            <input type="file" class="form-control" name="hero_image" 
                   accept="image/*">
          </div>
          
          <button type="submit" class="btn btn-primary">Save Changes</button>
        </div>
        
        <!-- Right: Preview (iframe to preview endpoint) -->
        <div class="col-md-6">
          <iframe src="/activity/{{ activity.id }}/email-preview?type=newPass" 
                  style="width: 100%; height: 600px; border: 1px solid #dee2e6;">
          </iframe>
        </div>
      </div>
    </div>
  </div>
</form>
```

### No JavaScript Required!
- Tab switching = form submission with different `template_type` value
- Preview update = form submission to preview endpoint
- All state managed server-side
- Mobile: Preview collapses below form (responsive grid)

## Advantages of This Approach

1. **MINIMAL CODE:** ~100 lines of Python, zero JavaScript
2. **REUSES EVERYTHING:** Existing forms, uploads, templates
3. **PROGRESSIVE:** Start with text, add images later
4. **FALLBACK SAFE:** Always falls back to defaults
5. **MOBILE FIRST:** Works perfectly on mobile with no JS

## Migration Path

### Step 1: Add JSON column (non-breaking)
```sql
ALTER TABLE activity ADD COLUMN email_templates JSON;
```

### Step 2: Update send_email gradually
- Add activity_id parameter (optional)
- Check for customizations if present
- Existing emails continue working

### Step 3: Roll out UI per activity
- Start with one activity as pilot
- Gradually enable for others

## Total Implementation Time

- **Database:** 30 minutes
- **Backend Logic:** 1 hour  
- **UI Creation:** 2-3 hours
- **Testing:** 1 hour
- **Total: 4-5 hours**

This is 50% faster than the original estimate by:
- Using JSON instead of new tables
- Reusing existing UI patterns
- No JavaScript = no client complexity
- Server-side preview (simple iframe)

## Next Steps

1. Approve this simplified approach
2. Add JSON column to Activity model
3. Create single template customization page
4. Test with one activity
5. Roll out to all activities

## Questions for Consideration

1. Should we limit which fields can be customized initially?
2. Should hero images be shared across templates or unique per template?
3. Do we need a "Reset to Default" button?
4. Should admins preview emails with real data or sample data?

---

*This plan prioritizes simplicity and speed of implementation while providing users with the essential customization features they need.*