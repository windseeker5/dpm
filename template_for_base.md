# Flask Dashboard Template Wireframe: Base.html Redesign - Option B

## Overview
This wireframe outlines the redesigned layout for the Minipass Flask application dashboard template using **Option B** design approach while preserving the existing sidebar menu structure and implementing specific layout requirements.

## Selected Design: Option B
**Option B** keeps the organization name aligned with the sidebar logo on the left side of the header, places the user avatar on the right side of the header, ensures the header spans the full width of the main content area, and maintains proper alignment between the sidebar logo and the organization name in the header.

## Current Structure Analysis
- **Existing Sidebar**: Modern custom sidebar with brand and navigation sections (no user profile)
- **Current Header**: Organization name with mobile menu toggle
- **Current Footer**: Copyright with Git branch version at end of content
- **Mobile Layout**: Bottom navigation bar with center scan button

## Design Requirements - Option B Implementation
1. Keep left sidebar menu structure but remove user profile section from bottom
2. Center the main content section
3. **Option B**: Add header above main section with organization name (left aligned with sidebar logo) and user gravatar (right)
4. **Option B**: Header spans the full width of the main content area
5. **Option B**: Maintain proper alignment between the sidebar logo and the organization name in the header
6. Place footer at end of main content (not sticky) with copyright and Git branch
7. Preserve mobile layout structure with organization name in mobile header

---

## Desktop Layout Specification (≥992px)

### Layout Structure
```
┌─────────────────────────────────────────────────────────────────┐
│  SIDEBAR (Fixed Left)  │         MAIN CONTENT AREA              │
│                        │                                         │
│  [Brand Logo] ←────────┼→ ┌─────────────────────────────────┐   │
│                        │  │ HEADER (Option B - Full Width)  │   │
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
│                        │  │            ...                  │   │
│                        │  │                                 │   │
│  (Clean sidebar end)   │  │  ─────────────────────────────  │   │
│                        │  │            FOOTER               │   │
│                        │  │  © 2025 Minipass. Version: v1  │   │
│                        │  └─────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Header Section Implementation (Option B)
- **Container**: Full width of main content area
- **Left Side**: Organization name display (`{{ ORG_NAME }}`) - **aligned with sidebar logo** (Option B requirement)
- **Right Side**: User gravatar with dropdown functionality (Option B requirement)
- **Layout**: Header spans full width of main content area (Option B requirement)
- **Styling**: Match existing organization header but add user avatar
- **Height**: 60px minimum for proper spacing
- **Alignment**: Organization name baseline matches sidebar logo vertical position (Option B specification)

### Main Content Centering
- **Container**: `.minipass-content-container` - maintain existing class
- **Centering**: Use CSS flexbox or grid to center content horizontally
- **Max Width**: Consider 1200px maximum width for optimal readability
- **Responsive**: Scale down gracefully on smaller screens
- **Footer**: Positioned at end of content (not sticky), appears after scrolling

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
<!-- Desktop & Mobile Header - Option B Implementation -->
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

### 3. Footer at End of Content
```html
<!-- Footer appears at the end of main content, not sticky -->
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
/* Header Styling - Option B Implementation */
.minipass-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: var(--tblr-bg-surface);
  border-bottom: 1px solid var(--tblr-border-color);
  /* Option B: Header spans full width of main content area */
  width: 100%;
  /* Option B: Ensure vertical alignment with sidebar logo */
  min-height: 60px;
}

.minipass-org-name {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--tblr-primary);
  /* Option B: Align with sidebar logo on left side */
  line-height: 1;
  display: flex;
  align-items: center;
  /* Option B: Ensure proper alignment with sidebar brand logo */
  margin-left: 0;
}

.minipass-header-user {
  display: flex;
  align-items: center;
  /* Option B: User avatar positioned on right side */
  margin-left: auto;
}

/* Content Centering */
.minipass-content {
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 60px); /* Full height minus header */
}

.minipass-content-container {
  flex: 1;
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

/* Footer at end of content */
.minipass-footer {
  margin-top: auto; /* Push to bottom of content */
  padding: 1rem;
  text-align: center;
  border-top: 1px solid var(--tblr-border-color);
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
- Sidebar navigation structure (except removing user profile section)
- Mobile bottom navigation
- JavaScript functionality (preserve existing)

### Elements to Remove
- Sidebar footer user profile section
- Gray divider lines in sidebar footer
- Any user-related components from sidebar

---

This wireframe preserves the existing sidebar menu structure while implementing the requested centered layout with proper header organization name and user avatar placement, maintaining full mobile responsiveness and Flask/Jinja2 integration.