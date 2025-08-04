# Forms & Component Specifications

## Current Form Issues Analysis

Based on the current login form and form patterns throughout the app:
- Basic Tabler form styling without customization
- Inconsistent spacing and visual hierarchy
- Limited visual feedback for validation states
- Need for better component standardization

## Form Design System

### Input Components

#### Text Input (Standard)
```css
.form-group {
  margin-bottom: 1.5rem;
}

.form-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--mp-gray-700);
  margin-bottom: 0.5rem;
  display: block;
}

.form-control {
  width: 100%;
  padding: 0.75rem 1rem;
  font-size: 1rem;
  line-height: 1.5;
  color: var(--mp-gray-700);
  background: white;
  border: 1px solid var(--mp-gray-300);
  border-radius: 8px;
  transition: all 0.2s ease;
}

.form-control:focus {
  outline: none;
  border-color: var(--mp-primary-500);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.form-control:disabled {
  background: var(--mp-gray-50);
  color: var(--mp-gray-500);
  cursor: not-allowed;
}
```

#### Input with Icon
```html
<div class="form-group">
  <label class="form-label" for="email">Email Address</label>
  <div class="input-icon">
    <span class="input-icon-addon">
      <i class="ti ti-mail"></i>
    </span>
    <input type="email" class="form-control" id="email" placeholder="Enter your email">
  </div>
</div>
```

```css
.input-icon {
  position: relative;
}

.input-icon-addon {
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--mp-gray-400);
  z-index: 2;
}

.input-icon .form-control {
  padding-left: 2.75rem;
}
```

#### Validation States
```css
/* Success State */
.form-control.is-valid {
  border-color: var(--mp-success);
  background-image: url("data:image/svg+xml,..."); /* Success icon */
  background-repeat: no-repeat;
  background-position: right 1rem center;
  background-size: 1rem;
}

.valid-feedback {
  display: block;
  width: 100%;
  margin-top: 0.25rem;
  font-size: 0.875rem;
  color: var(--mp-success);
}

/* Error State */
.form-control.is-invalid {
  border-color: var(--mp-error);
  background-image: url("data:image/svg+xml,..."); /* Error icon */
  background-repeat: no-repeat;
  background-position: right 1rem center;
  background-size: 1rem;
}

.invalid-feedback {
  display: block;
  width: 100%;
  margin-top: 0.25rem;
  font-size: 0.875rem;
  color: var(--mp-error);
}
```

### Button Components

#### Primary Buttons
```css
.btn-primary {
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 600;
  line-height: 1.5;
  color: white;
  background: var(--mp-primary-600);
  border: 1px solid var(--mp-primary-600);
  border-radius: 8px;
  transition: all 0.2s ease;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
}

.btn-primary:hover {
  background: var(--mp-primary-700);
  border-color: var(--mp-primary-700);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}

.btn-primary:active {
  transform: translateY(0);
  box-shadow: 0 2px 4px rgba(37, 99, 235, 0.3);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}
```

#### Secondary Buttons
```css
.btn-secondary {
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 600;
  color: var(--mp-gray-700);
  background: white;
  border: 1px solid var(--mp-gray-300);
  border-radius: 8px;
  transition: all 0.2s ease;
}

.btn-secondary:hover {
  background: var(--mp-gray-50);
  border-color: var(--mp-gray-400);
  color: var(--mp-gray-800);
}
```

#### Button Sizes
```css
.btn-sm {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
}

.btn-lg {
  padding: 1rem 2rem;
  font-size: 1.125rem;
}

.btn-block {
  width: 100%;
  justify-content: center;
}
```

## Form Layout Patterns

### Login Form (Enhanced)
```html
<div class="container-sm" style="max-width: 400px;">
  <div class="card form-card">
    <div class="card-body">
      <!-- Logo/Brand -->
      <div class="text-center mb-4">
        <div class="form-brand-logo">
          <div class="brand-icon">
            <i class="ti ti-shield-check"></i>
          </div>
          <h2 class="brand-title">minipass</h2>
          <p class="brand-subtitle">Admin Portal</p>
        </div>
      </div>

      <!-- Form -->
      <form method="POST" autocomplete="on">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
        
        <div class="form-group">
          <label class="form-label" for="email">Email Address</label>
          <div class="input-icon">
            <span class="input-icon-addon">
              <i class="ti ti-mail"></i>
            </span>
            <input type="email" class="form-control" id="email" name="email" 
                   placeholder="Enter your email" required autocomplete="email">
          </div>
        </div>

        <div class="form-group">
          <label class="form-label" for="password">Password</label>
          <div class="input-icon">
            <span class="input-icon-addon">
              <i class="ti ti-lock"></i>
            </span>
            <input type="password" class="form-control" id="password" name="password" 
                   placeholder="Enter your password" required autocomplete="current-password">
          </div>
        </div>

        <div class="form-footer">
          <button type="submit" class="btn btn-primary btn-block">
            <i class="ti ti-login"></i>
            Sign In
          </button>
        </div>
      </form>
    </div>
  </div>
</div>
```

### Activity Creation Form
```html
<div class="card form-card">
  <div class="card-header">
    <h3 class="card-title">Create New Activity</h3>
    <p class="card-subtitle">Set up a new event or activity for passport redemption</p>
  </div>
  
  <div class="card-body">
    <form method="POST" enctype="multipart/form-data">
      <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
      
      <!-- Basic Info Section -->
      <div class="form-section">
        <h4 class="form-section-title">Basic Information</h4>
        
        <div class="row">
          <div class="col-md-8">
            <div class="form-group">
              <label class="form-label" for="name">Activity Name *</label>
              <input type="text" class="form-control" id="name" name="name" 
                     placeholder="e.g., Summer Music Festival" required>
            </div>
          </div>
          <div class="col-md-4">
            <div class="form-group">
              <label class="form-label" for="fee">Entry Fee</label>
              <div class="input-icon">
                <span class="input-icon-addon">$</span>
                <input type="number" class="form-control" id="fee" name="fee" 
                       placeholder="0.00" min="0" step="0.01">
              </div>
            </div>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label" for="description">Description</label>
          <textarea class="form-control tinymce" id="description" name="description" 
                    rows="4" placeholder="Describe the activity..."></textarea>
        </div>
      </div>

      <!-- Dates Section -->
      <div class="form-section">
        <h4 class="form-section-title">Schedule</h4>
        
        <div class="row">
          <div class="col-md-6">
            <div class="form-group">
              <label class="form-label" for="signup_start">Signup Opens</label>
              <input type="datetime-local" class="form-control" id="signup_start" name="signup_start">
            </div>
          </div>
          <div class="col-md-6">
            <div class="form-group">
              <label class="form-label" for="signup_end">Signup Closes</label>
              <input type="datetime-local" class="form-control" id="signup_end" name="signup_end">
            </div>
          </div>
        </div>
      </div>

      <!-- Image Upload -->
      <div class="form-section">
        <h4 class="form-section-title">Activity Image</h4>
        
        <div class="form-group">
          <label class="form-label" for="image">Upload Image</label>
          <div class="file-upload-area">
            <input type="file" class="form-control" id="image" name="image" 
                   accept="image/*" onchange="previewImage(this)">
            <div class="file-upload-preview" id="imagePreview"></div>
          </div>
        </div>
      </div>

      <!-- Form Actions -->
      <div class="form-footer">
        <div class="btn-group">
          <a href="{{ url_for('list_activities') }}" class="btn btn-secondary">
            <i class="ti ti-arrow-left"></i>
            Cancel
          </a>
          <button type="submit" class="btn btn-primary">
            <i class="ti ti-plus"></i>
            Create Activity
          </button>
        </div>
      </div>
    </form>
  </div>
</div>
```

## Form Styling Components

### Form Card Container
```css
.form-card {
  background: white;
  border: 1px solid var(--mp-gray-200);
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.form-card .card-header {
  padding: 2rem 2rem 1rem;
  border-bottom: 1px solid var(--mp-gray-100);
  background: var(--mp-gray-50);
}

.form-card .card-body {
  padding: 2rem;
}

.form-card .card-footer {
  padding: 1rem 2rem 2rem;
  background: var(--mp-gray-50);
  border-top: 1px solid var(--mp-gray-100);
}
```

### Form Sections
```css
.form-section {
  margin-bottom: 2rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid var(--mp-gray-100);
}

.form-section:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.form-section-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--mp-gray-800);
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.form-section-title::before {
  content: '';
  width: 4px;
  height: 1.5rem;
  background: var(--mp-primary-500);
  border-radius: 2px;
}
```

### File Upload Component
```css
.file-upload-area {
  border: 2px dashed var(--mp-gray-300);
  border-radius: 8px;
  padding: 2rem;
  text-align: center;
  transition: all 0.2s ease;
  background: var(--mp-gray-50);
}

.file-upload-area:hover {
  border-color: var(--mp-primary-300);
  background: var(--mp-primary-50);
}

.file-upload-area.dragover {
  border-color: var(--mp-primary-500);
  background: var(--mp-primary-100);
}

.file-upload-preview {
  margin-top: 1rem;
}

.file-upload-preview img {
  max-width: 200px;
  max-height: 150px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
```

### Login Page Brand Treatment
```css
.form-brand-logo {
  text-align: center;
  margin-bottom: 2rem;
}

.brand-icon {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, var(--mp-primary-500), var(--mp-secondary-500));
  border-radius: 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1rem;
  box-shadow: 0 4px 16px rgba(37, 99, 235, 0.3);
}

.brand-icon i {
  font-size: 2rem;
  color: white;
}

.brand-title {
  font-size: 1.875rem;
  font-weight: 700;
  color: var(--mp-gray-900);
  margin-bottom: 0.25rem;
}

.brand-subtitle {
  font-size: 1rem;
  color: var(--mp-gray-500);
  margin: 0;
}
```

## Component States

### Loading States
```css
.btn.loading {
  position: relative;
  color: transparent;
  cursor: not-allowed;
}

.btn.loading::after {
  content: '';
  position: absolute;
  width: 16px;
  height: 16px;
  top: 50%;
  left: 50%;
  margin-left: -8px;
  margin-top: -8px;
  border: 2px solid transparent;
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
```

### Form Validation
```css
.form-feedback {
  margin-top: 0.375rem;
  font-size: 0.875rem;
  line-height: 1.4;
}

.form-feedback.valid {
  color: var(--mp-success);
}

.form-feedback.invalid {
  color: var(--mp-error);
}

.form-feedback::before {
  content: '';
  display: inline-block;
  width: 16px;
  height: 16px;
  margin-right: 0.5rem;
  background-size: contain;
  vertical-align: middle;
}

.form-feedback.valid::before {
  background-image: url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' fill='%23059669' viewBox='0 0 16 16'><path d='M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.061L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z'/></svg>");
}

.form-feedback.invalid::before {
  background-image: url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' fill='%23dc2626' viewBox='0 0 16 16'><path d='M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM5.354 4.646a.5.5 0 1 0-.708.708L7.293 8l-2.647 2.646a.5.5 0 0 0 .708.708L8 8.707l2.646 2.647a.5.5 0 0 0 .708-.708L8.707 8l2.647-2.646a.5.5 0 0 0-.708-.708L8 7.293 5.354 4.646z'/></svg>");
}
```

## Mobile Optimizations

### Responsive Form Layouts
```css
@media (max-width: 768px) {
  .form-card .card-body {
    padding: 1.5rem;
  }
  
  .form-card .card-header {
    padding: 1.5rem 1.5rem 1rem;
  }
  
  .form-section {
    margin-bottom: 1.5rem;
    padding-bottom: 1.5rem;
  }
  
  .btn-group {
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .btn-group .btn {
    width: 100%;
  }
}
```

## Implementation Priority

### Phase 1: Basic Form Components
1. Enhanced input styling with proper focus states
2. Improved button components with hover effects
3. Form validation styling
4. Basic layout improvements

### Phase 2: Advanced Components
1. File upload component with drag-and-drop
2. Form section organization
3. Loading states for buttons
4. Enhanced brand treatment for login

### Phase 3: Interaction & Polish
1. Smooth animations and transitions
2. Advanced form validation patterns
3. Mobile-specific optimizations
4. Accessibility enhancements