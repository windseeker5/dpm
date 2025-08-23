# Signup Form Improvement Plan v4

## Executive Summary
This plan outlines minimal, safe improvements to the signup form. The URL structure `/signup/<activity_id>?passport_type_id=<id>` already determines which passport type the user is signing up for - NO selection needed.

## Critical Understanding - Passport Type System

### URL Structure
```
http://127.0.0.1:8890/signup/1?passport_type_id=1
                            ↑                    ↑
                      Activity ID         Passport Type ID
```

**KEY POINT**: The passport type is ALREADY DETERMINED by the URL parameter. Users arrive at this form through a specific link for a specific passport type. They DO NOT choose between passport types on this form.

### Current Implementation (app.py lines 1526-1530)
```python
passport_type_id = request.args.get('passport_type_id')
selected_passport_type = None
if passport_type_id:
    selected_passport_type = PassportType.query.get(passport_type_id)
```

### What This Means
- Each passport type has its own unique signup URL
- Users click a specific link (e.g., "Register as Regular Player" or "Register as Substitute")
- The form is PRE-CONFIGURED for that passport type
- NO passport type selection UI needed on the form

## Logo Clarification
**CONFIRMED**: The logo displayed is the ORGANIZATION'S logo (stored in settings["LOGO_FILENAME"]), NOT a Minipass logo. This is the logo of the sports club, community center, or organization running the activity.

## Improvement Plan - Simple & Safe

### What to REMOVE
1. **Passport Type Selection UI** (lines 313-364 in signup_form.html)
   - Remove the mobile card selection
   - Remove the desktop dropdown
   - These are NOT needed since passport type comes from URL

### What to KEEP and ENHANCE

#### 1. Display Selected Passport Type Info (READ-ONLY)
Show the pre-selected passport type information clearly:
```html
<!-- Enhanced passport type display (not selectable) -->
<div class="card bg-blue-lt mb-4">
  <div class="card-body">
    <h5>Registration Type: {{ selected_passport_type.name }}</h5>
    <div class="row">
      <div class="col-6">
        <i class="ti ti-currency-dollar"></i> 
        ${{ "%.2f"|format(selected_passport_type.price_per_user) }}
      </div>
      <div class="col-6">
        <i class="ti ti-ticket"></i> 
        {{ selected_passport_type.sessions_included }} sessions
      </div>
    </div>
    {% if selected_passport_type.payment_instructions %}
      <small>{{ selected_passport_type.payment_instructions }}</small>
    {% endif %}
  </div>
</div>
```

#### 2. Form Structure Enhancement
```html
<div class="signup-wrapper">
  <div class="card shadow-sm" style="max-width: 1400px;">
    <div class="row g-0">
      <!-- Left: Form -->
      <div class="col-md-6">
        <div class="card-body p-4">
          <!-- Organization Logo -->
          {% if settings["LOGO_FILENAME"] %}
            <img src="{{ url_for('static', filename='uploads/' + settings['LOGO_FILENAME']) }}" 
                 alt="Organization Logo" class="mb-3" style="height: 60px;">
          {% endif %}
          
          <!-- Activity Name -->
          <h2>{{ activity.name }}</h2>
          
          <!-- Passport Type Info (READ-ONLY, from URL) -->
          <div class="alert alert-info">
            Registering as: {{ selected_passport_type.name }}
            Price: ${{ selected_passport_type.price_per_user }}
          </div>
          
          <!-- Form Fields -->
          <form method="POST">
            <input type="hidden" name="passport_type_id" 
                   value="{{ selected_passport_type.id }}">
            <!-- Name, Email, Phone, Notes fields -->
            <!-- Submit button -->
          </form>
        </div>
      </div>
      
      <!-- Right: Activity Image -->
      <div class="col-md-6">
        <div class="h-100" style="background-image: url('{{ url_for('static', filename='uploads/activity_images/' + activity.image_filename) }}'); 
                                   background-size: cover; 
                                   background-position: center;
                                   min-height: 600px;">
        </div>
      </div>
    </div>
  </div>
</div>
```

## Wireframes v4

### Desktop Version (1920x1080)
```
┌────────────────────────────────────────────────────────────────┐
│                          Browser Window                          │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Signup Card Container                  │  │
│  │  ┌─────────────────────────┬───────────────────────────┐ │  │
│  │  │                          │                           │ │  │
│  │  │      Form Section        │    Activity Image         │ │  │
│  │  │       (Left 50%)         │      (Right 50%)         │ │  │
│  │  │                          │                           │ │  │
│  │  │  [Organization Logo]     │   [activity.image_       │ │  │
│  │  │  (Not Minipass!)         │    filename]             │ │  │
│  │  │                          │                           │ │  │
│  │  │  Activity Name           │   Full height image      │ │  │
│  │  │  ─────────────           │   background with        │ │  │
│  │  │                          │   object-fit: cover      │ │  │
│  │  │  ┌──────────────────┐    │                           │ │  │
│  │  │  │ℹ️ Registering as: │    │                           │ │  │
│  │  │  │ [Passport Type]  │    │                           │ │  │
│  │  │  │ Price: $XX.XX    │    │                           │ │  │
│  │  │  │ Sessions: X      │    │                           │ │  │
│  │  │  └──────────────────┘    │                           │ │  │
│  │  │  (NO SELECTION NEEDED)   │                           │ │  │
│  │  │                          │                           │ │  │
│  │  │  Name                    │                           │ │  │
│  │  │  ┌────────────────────┐  │                           │ │  │
│  │  │  │                    │  │                           │ │  │
│  │  │  └────────────────────┘  │                           │ │  │
│  │  │                          │                           │ │  │
│  │  │  Email                   │                           │ │  │
│  │  │  ┌────────────────────┐  │                           │ │  │
│  │  │  │                    │  │                           │ │  │
│  │  │  └────────────────────┘  │                           │ │  │
│  │  │                          │                           │ │  │
│  │  │  Phone                   │                           │ │  │
│  │  │  ┌────────────────────┐  │                           │ │  │
│  │  │  │                    │  │                           │ │  │
│  │  │  └────────────────────┘  │                           │ │  │
│  │  │                          │                           │ │  │
│  │  │  Notes                   │                           │ │  │
│  │  │  ┌────────────────────┐  │                           │ │  │
│  │  │  │                    │  │                           │ │  │
│  │  │  │                    │  │                           │ │  │
│  │  │  └────────────────────┘  │                           │ │  │
│  │  │                          │                           │ │  │
│  │  │  ☐ Accept Terms          │                           │ │  │
│  │  │                          │                           │ │  │
│  │  │  ┌────────────────────┐  │                           │ │  │
│  │  │  │  Submit Registration│  │                           │ │  │
│  │  │  └────────────────────┘  │                           │ │  │
│  │  │                          │                           │ │  │
│  │  └─────────────────────────┴───────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

### Mobile Version (375x667) - IMPROVED
```
┌─────────────────┐
│  Mobile Browser │
├─────────────────┤
│                 │
│ ┌─────────────┐ │
│ │             │ │
│ │  Activity   │ │
│ │   Image     │ │
│ │ Background  │ │
│ │   (Subtle   │ │
│ │  Overlay)   │ │
│ │             │ │
│ │ ┌─────────┐ │ │
│ │ │  Org    │ │ │
│ │ │  Logo   │ │ │
│ │ └─────────┘ │ │
│ │             │ │
│ │  Activity   │ │
│ │    Name     │ │
│ │             │ │
│ └─────────────┘ │
│                 │
│ ┌─────────────┐ │
│ │ Registration│ │
│ │ Type Info   │ │
│ │ [Type Name] │ │
│ │ $XX | X sess│ │
│ └─────────────┘ │
│                 │
│  Name           │
│  ┌───────────┐  │
│  │           │  │
│  └───────────┘  │
│                 │
│  Email          │
│  ┌───────────┐  │
│  │           │  │
│  └───────────┘  │
│                 │
│  Phone          │
│  ┌───────────┐  │
│  │           │  │
│  └───────────┘  │
│                 │
│  Notes          │
│  ┌───────────┐  │
│  │           │  │
│  │           │  │
│  └───────────┘  │
│                 │
│  ☐ Accept Terms │
│                 │
│  ┌───────────┐  │
│  │  Submit   │  │
│  └───────────┘  │
│                 │
└─────────────────┘
```

### Mobile Design Notes
- Activity image as hero background with overlay (not small preview)
- Organization logo overlaid on image
- Clean card for passport type info (read-only)
- Form fields below in clean white section

## Implementation Steps

### Step 1: Remove Passport Type Selection
**Lines to remove from signup_form.html:**
- Lines 313-364: Entire passport type selection section
- Lines 459-533: JavaScript for passport type selection

### Step 2: Enhance Passport Type Display
**Keep lines 367-379 but modify to:**
```html
{% if selected_passport_type %}
<div class="card bg-blue-lt mb-4">
  <div class="card-body">
    <h5 class="card-title mb-3">
      <i class="ti ti-ticket me-2"></i>
      Registration Details
    </h5>
    <div class="row">
      <div class="col-6">
        <strong>Type:</strong> {{ selected_passport_type.name }}
      </div>
      <div class="col-6">
        <strong>Price:</strong> ${{ "%.2f"|format(selected_passport_type.price_per_user) }}
      </div>
    </div>
    <!-- Keep payment instructions if exists -->
  </div>
</div>
{% endif %}
```

### Step 3: Mobile Image Enhancement
Replace lines 241-249 with hero image section:
```html
<div class="d-block d-md-none mb-4">
  <div class="position-relative" 
       style="height: 200px; 
              background-image: url('{{ url_for('static', filename='uploads/activity_images/' + activity.image_filename) }}');
              background-size: cover;
              background-position: center;
              border-radius: 12px;">
    <div style="background: linear-gradient(to bottom, rgba(0,0,0,0.3), rgba(0,0,0,0.6)); 
                position: absolute; 
                inset: 0; 
                border-radius: 12px;
                padding: 1.5rem;
                display: flex;
                flex-direction: column;
                justify-content: flex-end;">
      {% if settings["LOGO_FILENAME"] %}
        <img src="{{ url_for('static', filename='uploads/' + settings['LOGO_FILENAME']) }}" 
             alt="Organization Logo" 
             style="height: 40px; margin-bottom: 1rem;">
      {% endif %}
      <h3 class="text-white mb-0">{{ activity.name }}</h3>
    </div>
  </div>
</div>
```

## What NOT to Change
1. Form field names and IDs
2. Form POST action
3. CSRF token
4. Hidden passport_type_id field (line 309)
5. Backend logic in app.py

## Testing Checklist
- [ ] Navigate to `/signup/1?passport_type_id=1` - passport type 1 shows correctly
- [ ] Navigate to `/signup/1?passport_type_id=2` - passport type 2 shows correctly
- [ ] Verify NO selection UI appears
- [ ] Submit form successfully
- [ ] Check data saved with correct passport_type_id
- [ ] Test on mobile - hero image displays well
- [ ] Organization logo shows (not Minipass logo)

## Common Mistakes to Avoid
1. ❌ DON'T add passport type selection - it's in the URL
2. ❌ DON'T use placeholder images - use activity.image_filename
3. ❌ DON'T confuse organization logo with Minipass logo
4. ❌ DON'T break the hidden passport_type_id field
5. ❌ DON'T start a new Flask server

## Success Criteria
- Form displays the pre-selected passport type from URL
- No passport type selection UI exists
- Organization logo displays correctly
- Activity image used appropriately
- Form submits with correct passport_type_id
- Mobile experience is clean and modern

---
*Plan v4 - Correct understanding of passport type URL parameter*