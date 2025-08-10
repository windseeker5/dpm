# Flask Dashboard Template Wireframe: Base.html Redesign

## Overview
This wireframe outlines the redesigned layout for the Minipass Flask application dashboard template while preserving the existing sidebar menu structure and implementing specific layout requirements.

## Current Structure Analysis
- **Existing Sidebar**: Modern custom sidebar with brand, navigation sections, and user profile footer
- **Current Header**: Organization name with mobile menu toggle
- **Current Footer**: Copyright with Git branch version
- **Mobile Layout**: Bottom navigation bar with center scan button

## Design Requirements
1. Keep left sidebar menu exactly as current implementation
2. Center the main content section
3. Add header above main section with organization name (left) and user gravatar (right)
4. Maintain current footer with copyright and Git branch
5. Preserve mobile layout structure with organization name in mobile header

---

## Desktop Layout Specification (≥992px)

### Layout Structure
```
┌─────────────────────────────────────────────────────────────────┐
│  SIDEBAR (Fixed Left)  │         MAIN CONTENT AREA              │
│                        │                                         │
│  [Brand Logo]          │  ┌─────────────────────────────────┐   │
│                        │  │        HEADER SECTION           │   │
│  [Main Navigation]     │  │  Org Name (L)  User Avatar (R) │   │
│  • Dashboard           │  └─────────────────────────────────┘   │
│  • Activities          │                                         │
│  • Signups             │  ┌─────────────────────────────────┐   │
│  • Passports           │  │                                 │   │
│  • Surveys             │  │      CENTERED MAIN CONTENT     │   │
│                        │  │         (Flash Messages)       │   │
│  [Tools Navigation]    │  │         (Page Content)         │   │
│  • AI Analytics        │  │                                 │   │
│  • Style Guide         │  │                                 │   │
│  • Settings            │  │                                 │   │
│                        │  │                                 │   │
│                        │  │                                 │   │
│                        │  └─────────────────────────────────┘   │
│                        │                                         │
│                        │  ┌─────────────────────────────────┐   │
│                        │  │            FOOTER               │   │
│                        │  │  © 2025 Minipass. Version: v1  │   │
│                        │  └─────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Header Section Implementation
- **Container**: Full width of main content area
- **Left Side**: Organization name display (`{{ ORG_NAME }}`)
- **Right Side**: User gravatar with dropdown functionality
- **Styling**: Match existing organization header but add user avatar
- **Height**: 60px minimum for proper spacing

### Main Content Centering
- **Container**: `.minipass-content-container` - maintain existing class
- **Centering**: Use CSS flexbox or grid to center content horizontally
- **Max Width**: Consider 1200px maximum width for optimal readability
- **Responsive**: Scale down gracefully on smaller screens

---

## Mobile Layout Specification (<992px)

### Layout Structure
```
┌─────────────────────────────────┐
│          MOBILE HEADER          │
│  [☰] Organization Name [Avatar] │
└─────────────────────────────────┘
│                                 │
│         MAIN CONTENT            │
│                                 │
│      (Flash Messages)           │
│      (Page Content)             │
│                                 │
│                                 │
│                                 │
┌─────────────────────────────────┐
│            FOOTER               │
│   © 2025 Minipass. Version: v1 │
└─────────────────────────────────┘
┌─────────────────────────────────┐
│      MOBILE BOTTOM NAV          │
│ [Home] [Activities] [⊙] [Signups] [Passes] │
└─────────────────────────────────┘
```

### Mobile Header Updates
- **Left**: Hamburger menu button (existing)
- **Center**: Organization name (`{{ ORG_NAME }}`)
- **Right**: User gravatar (new addition)
- **Behavior**: Sidebar slides in from left when hamburger is tapped

---

## Component Specifications

### 1. Header Component
```html
<!-- Desktop & Mobile Header -->
<header class="minipass-header">
  <!-- Mobile menu toggle (existing) -->
  <button class="header-menu-toggle d-lg-none" type="button" id="sidebarToggle">
    <i class="ti ti-menu-2"></i>
  </button>
  
  <!-- Organization Name -->
  <div class="minipass-org-name">
    {{ ORG_NAME }}
  </div>
  
  <!-- User Avatar Section -->
  <div class="minipass-header-user">
    <div class="dropdown">
      <a href="#" class="header-user-link" data-bs-toggle="dropdown">
        <span class="avatar avatar-sm" 
              style="background-image: url('https://www.gravatar.com/avatar/{{ session['admin']|lower|trim|encode_md5 }}?d=identicon')">
        </span>
      </a>
      <div class="dropdown-menu dropdown-menu-end dropdown-menu-arrow">
        <a href="{{ url_for('activity_log') }}" class="dropdown-item">
          <i class="ti ti-history me-2"></i>Activity Log
        </a>
        <a href="{{ url_for('setup') }}" class="dropdown-item">
          <i class="ti ti-settings me-2"></i>Settings
        </a>
        <div class="dropdown-divider"></div>
        <a href="{{ url_for('logout') }}" class="dropdown-item text-danger">
          <i class="ti ti-logout me-2"></i>Logout
        </a>
      </div>
    </div>
  </div>
</header>
```

### 2. Main Content Centering
```html
<main class="minipass-content minipass-content-centered" id="main-content">
  <div class="minipass-content-container">
    <!-- Flash Messages (existing) -->
    <!-- Page Content (existing) -->
  </div>
</main>
```

### 3. Updated Footer
```html
<footer class="minipass-footer">
  <div class="minipass-footer-content">
    <div class="minipass-footer-text">
      © 2025 Minipass. All rights reserved. | Version: {{ git_branch }}
    </div>
  </div>
</footer>
```

---

## CSS Implementation Notes

### Required CSS Classes
```css
/* Header Styling */
.minipass-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: var(--tblr-bg-surface);
  border-bottom: 1px solid var(--tblr-border-color);
}

.minipass-org-name {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--tblr-primary);
}

.minipass-header-user {
  display: flex;
  align-items: center;
}

/* Content Centering */
.minipass-content-centered {
  display: flex;
  justify-content: center;
  padding: 2rem 1rem;
}

.minipass-content-centered .minipass-content-container {
  width: 100%;
  max-width: 1200px;
}

/* Mobile Responsive */
@media (max-width: 991.98px) {
  .minipass-header {
    padding: 1rem;
  }
  
  .minipass-org-name {
    font-size: 1.1rem;
  }
  
  .minipass-content-centered {
    padding: 1rem;
  }
}
```

---

## Integration Points

### 1. Flask/Jinja2 Template Variables
- `{{ ORG_NAME }}` - Organization name display
- `{{ session['admin'] }}` - User email for Gravatar
- `{{ git_branch }}` - Git branch for version display
- `{{ request.endpoint }}` - Active navigation state

### 2. Existing JavaScript Functionality
- Sidebar toggle for mobile (preserve existing)
- Dropdown menu initialization (Bootstrap/Tabler)
- Alert auto-dismiss (preserve existing)

### 3. Tabler.io Components Used
- `.avatar` - User avatar styling
- `.dropdown` - User menu dropdown
- `.ti` icons - Tabler icons for UI elements
- Bootstrap grid and utility classes

---

## Responsive Breakpoints

### Desktop (≥992px)
- Show full header with organization name and user avatar
- Sidebar always visible
- Centered main content with max-width constraint

### Tablet (768px - 991px)
- Same as desktop but adjust padding/spacing
- Sidebar becomes overlay when triggered

### Mobile (<768px)
- Compact header with hamburger menu
- Organization name in center of mobile header
- User avatar remains on right
- Bottom navigation bar active

---

## Accessibility Considerations

1. **Skip Navigation**: Maintain existing skip link
2. **Focus Management**: Ensure header elements are keyboard accessible
3. **Screen Readers**: Proper ARIA labels for avatar dropdown
4. **Color Contrast**: Maintain Tabler.io contrast standards
5. **Touch Targets**: Minimum 44px touch targets for mobile

---

## Implementation Priority

### Phase 1: Core Layout
1. Update header structure with organization name and user avatar
2. Implement main content centering
3. Test responsive behavior

### Phase 2: Styling & Polish
1. Refine CSS for visual consistency
2. Ensure Tabler.io component integration
3. Mobile optimization

### Phase 3: Testing & Validation
1. Cross-browser testing
2. Accessibility audit
3. Mobile device testing

---

## File Dependencies

### Templates to Update
- `/templates/base.html` - Main template file
- Potential child templates if header structure changes

### CSS Files to Modify
- `/static/minipass-redesign.css` - Custom styling additions
- Ensure Tabler.io CSS integration

### No Changes Required
- Sidebar navigation structure (preserve exactly as is)
- Mobile bottom navigation
- Footer copyright structure (just format adjustment)
- JavaScript functionality (preserve existing)

---

This wireframe preserves the existing sidebar menu structure while implementing the requested centered layout with proper header organization name and user avatar placement, maintaining full mobile responsiveness and Flask/Jinja2 integration.