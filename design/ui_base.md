# Minipass UI Base Template - Design Specification

## Overview

This document outlines the redesigned user interface for the Minipass SAAS PWA application. The design follows modern SaaS principles with a clean, professional aesthetic inspired by industry leaders like Stripe, Linear, and Notion.

## Design Philosophy

- **Clean & Minimal**: Focus on content with reduced visual clutter
- **Professional**: Enterprise-ready appearance with sophisticated color palette
- **Responsive**: Mobile-first approach with adaptive layouts
- **Accessible**: WCAG 2.1 AA compliant with proper focus management
- **Consistent**: Unified design language across all components

## Layout Structure

### Desktop Layout (≥992px)

```
┌─────────────────────────────────────────────────────────────────┐
│                         Application Container                    │
├──────────────┬──────────────────────────────────────────────────┤
│              │         Organization Name Header (48px)          │
│   Sidebar    │         Background: #F8F9FA (seamless)           │
│   (260px)    ├──────────────────────────────────────────────────┤
│              │                                                  │
│   Fixed      │         Main Content Area (Centered)             │
│   Position   │         Max-width: 1320px Container              │
│              │            Flexible Height/Scroll                 │
│              │                                                  │
│              ├──────────────────────────────────────────────────┤
│              │          Footer (Auto, no border)                │
└──────────────┴──────────────────────────────────────────────────┘
```

### Mobile Layout (<992px)

```
┌─────────────────────────────────────┐
│    Organization Name Header (48px)  │
│         Background: #F8F9FA         │
├─────────────────────────────────────┤
│                                     │
│                                     │
│        Main Content Area            │
│         (Full Width)                │
│                                     │
│                                     │
├─────────────────────────────────────┤
│    Bottom Navigation Bar (70px)     │
└─────────────────────────────────────┘
```

## Component Specifications

### Content Container

**Specifications:**
- Max-width: 1320px (Bootstrap's XXL container)
- Margin: 0 auto (centered horizontally)
- Padding: Inherits from parent (2rem)
- Purpose: Centers content and creates equal visual spacing on both sides

**CSS Implementation:**
```css
.minipass-content {
  flex: 1;
  padding: 2rem;
  display: flex;
  justify-content: center;
}

.minipass-content-container {
  width: 100%;
  max-width: 1320px;
  margin: 0 auto;
}
```

### 1. Sidebar Navigation

**Desktop Specifications:**
- Width: 260px (fixed)
- Background: #FFFFFF
- Border: 1px solid #E9ECEF (right)
- Position: Fixed left, full height
- Z-index: 1040

**Structure:**
```
Sidebar
├── Brand Section
│   ├── Logo (32x32px)
│   └── Brand Text (Anton, 1.5rem)
├── Navigation Sections
│   ├── Main Section
│   │   ├── Dashboard
│   │   ├── Activities
│   │   ├── Signups (with badge)
│   │   ├── Passports
│   │   └── Surveys
│   └── Tools Section
│       ├── AI Analytics (Beta tag)
│       └── Style Guide
└── Footer Section
    ├── Settings Link
    └── User Profile
        ├── Avatar (32x32px)
        ├── User Name
        └── Role Text
```

**Navigation Link States:**
- Default: Color #475569, Background transparent
- Hover: Color #1E293B, Background #F1F5F9
- Active: Color #206BC4, Background #EFF6FF, Left indicator 3px

### 2. Organization Name Header

**Specifications:**
- Height: 48px (fixed)
- Background: #F8F9FA (matches main content area)
- Border: None (seamless integration)
- Position: Sticky top
- Z-index: 1030
- Text: Dynamically pulled from ORG_NAME settings variable

**Components:**
```
Organization Header
├── Organization Name (Center)
│   ├── Font: Inter, font-weight: 600
│   ├── Size: 1.125rem (18px)
│   ├── Color: #374151
│   └── Dynamic content from settings.ORG_NAME
└── Mobile Menu Toggle (Left, mobile only)
```

**CSS Implementation:**
```css
.minipass-org-header {
  height: 48px;
  background: #F8F9FA;
  display: flex;
  align-items: center;
  justify-content: center;
  position: sticky;
  top: 0;
  z-index: 1030;
  padding: 0 1rem;
}

.minipass-org-header h1 {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: #374151;
  text-align: center;
}

@media (max-width: 991px) {
  .minipass-org-header {
    justify-content: space-between;
  }
  
  .minipass-org-header h1 {
    flex: 1;
    margin-left: 2rem; /* Account for mobile menu toggle */
  }
}
```

### 3. Mobile Bottom Navigation

**Specifications:**
- Height: 70px
- Background: #FFFFFF
- Border: 1px solid #E9ECEF (top)
- Position: Fixed bottom
- Z-index: 1050

**Layout:**
```
Bottom Nav (5 items, equal width)
├── Home (Dashboard)
├── Activities
├── Scan QR (Center FAB)
├── Signups
└── Passes
```

**Center FAB Button:**
- Size: 56x56px
- Background: #206BC4
- Position: Absolute, -20px top offset
- Border-radius: 50%
- Shadow: 0 4px 12px rgba(32, 107, 196, 0.4)

### 4. Footer

**Specifications:**
- Background: Transparent (no white background)
- Border: None (removed border lines)
- Padding: 1rem 0
- Text alignment: Center

**Content:**
```
Footer
├── Copyright Text
│   ├── Format: "© 2025 Minipass. All rights reserved. - version: {git_branch}"
│   ├── Font: Inter, 14px
│   ├── Color: #6B7280
│   └── Dynamic git branch from repository
```

**CSS Implementation:**
```css
.minipass-footer {
  background: transparent;
  border: none;
  padding: 1rem 0;
  text-align: center;
  color: #6B7280;
  font-size: 0.875rem;
}

.minipass-footer p {
  margin: 0;
}
```

## Color System

### Primary Colors
```css
--primary-50: #EFF6FF
--primary-100: #DBEAFE
--primary-200: #BFDBFE
--primary-300: #93C5FD
--primary-400: #60A5FA
--primary-500: #3B82F6
--primary-600: #206BC4  /* Main brand color */
--primary-700: #1D4ED8
--primary-800: #1E40AF
--primary-900: #1E3A8A
```

### Neutral Colors
```css
--gray-50: #F9FAFB
--gray-100: #F3F4F6
--gray-200: #E5E7EB
--gray-300: #D1D5DB
--gray-400: #9CA3AF
--gray-500: #6B7280
--gray-600: #4B5563
--gray-700: #374151
--gray-800: #1F2937
--gray-900: #111827
```

### Semantic Colors
```css
--success: #10B981
--warning: #F59E0B
--danger: #EF4444
--info: #3B82F6
```

### Background Colors
```css
--bg-primary: #FFFFFF
--bg-secondary: #F8F9FA
--bg-sidebar: #FFFFFF
--bg-header: #F8F9FA  /* Updated to match main content */
--bg-org-header: #F8F9FA  /* New organization header background */
```

## Typography

### Font Families
```css
--font-brand: 'Anton', sans-serif;      /* Brand/Logo */
--font-body: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
```

### Font Sizes
```css
--text-xs: 0.75rem;    /* 12px */
--text-sm: 0.875rem;   /* 14px */
--text-base: 1rem;     /* 16px */
--text-lg: 1.125rem;   /* 18px */
--text-xl: 1.25rem;    /* 20px */
--text-2xl: 1.5rem;    /* 24px */
--text-3xl: 1.875rem;  /* 30px */
```

### Font Weights
```css
--font-light: 300;
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

## Spacing System

Using an 8px grid system:

```css
--space-0: 0;
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-3: 0.75rem;   /* 12px */
--space-4: 1rem;      /* 16px */
--space-5: 1.25rem;   /* 20px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
--space-10: 2.5rem;   /* 40px */
--space-12: 3rem;     /* 48px */
--space-16: 4rem;     /* 64px */
```

## Interactive Elements

### Button Styles

**Primary Button:**
- Background: #206BC4
- Text: #FFFFFF
- Padding: 12px 24px
- Border-radius: 6px
- Hover: Background #1D4ED8, translateY(-1px)
- Active: translateY(0)

**Icon Buttons:**
- Size: 32x32px
- Background: Transparent
- Hover: Background #F4F6FA
- Border-radius: 6px

### Form Controls

**Input Fields:**
- Height: 38px
- Background: #F4F6FA
- Border: None (default), 1px solid #206BC4 (focus)
- Border-radius: 6px
- Padding: 8px 12px
- Focus: Box-shadow 0 0 0 4px rgba(32, 107, 196, 0.1)

**Search Input:**
- Background: #F4F6FA
- Padding-left: 40px (for icon)
- Max-width: 400px

### Dropdown Menus

- Background: #FFFFFF
- Border: 1px solid #E9ECEF
- Border-radius: 8px
- Shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1)
- Item hover: Background #F9FAFB

## Responsive Breakpoints

```css
/* Mobile First Approach */
--breakpoint-sm: 640px;
--breakpoint-md: 768px;
--breakpoint-lg: 992px;  /* Primary desktop breakpoint */
--breakpoint-xl: 1280px;
--breakpoint-2xl: 1536px;
```

### Responsive Behaviors

**< 992px (Mobile/Tablet):**
- Sidebar: Hidden by default, slide-over when toggled
- Organization header: Show mobile menu toggle, center organization name
- Bottom navigation: Visible
- Content padding: 16px

**≥ 992px (Desktop):**
- Sidebar: Always visible, sticky position
- Organization header: Hide mobile menu toggle, center organization name
- Bottom navigation: Hidden
- Content padding: 32px

## Animation & Transitions

### Standard Transitions
```css
--transition-fast: 150ms ease;
--transition-normal: 300ms ease;
--transition-slow: 500ms ease;
```

### Common Animations
- Sidebar slide: translateX with 300ms ease
- Hover effects: 200ms ease
- Button interactions: 150ms ease
- Dropdown appearance: 200ms ease-out

## Accessibility Requirements

### Focus Management
- Visible focus indicators: 2px solid #206BC4, 2px offset
- Skip navigation link at page start
- Proper focus trap for modals/dropdowns

### ARIA Implementation
- Proper landmarks (nav, main, footer)
- Button and link labels
- Live regions for notifications
- Semantic HTML structure

### Keyboard Navigation
- Tab order follows visual hierarchy
- Escape key closes dropdowns/modals
- Arrow keys for menu navigation
- Enter/Space for button activation

## Component States

### Navigation Items
1. **Default**: Base styling, ready for interaction
2. **Hover**: Elevated background, darker text
3. **Active**: Blue background, blue text, left indicator
4. **Disabled**: Reduced opacity (0.5), no pointer events

### Alerts/Notifications
1. **Success**: Green accent (#10B981)
2. **Warning**: Orange accent (#F59E0B)
3. **Error**: Red accent (#EF4444)
4. **Info**: Blue accent (#3B82F6)

## Mobile-Specific Considerations

### Touch Targets
- Minimum size: 44x44px
- Spacing between targets: 8px minimum
- Increased padding for mobile nav items

### Gestures
- Swipe right: Open sidebar (from left edge)
- Swipe left: Close sidebar
- Pull to refresh: Content areas
- Tap outside: Close dropdowns/sidebar

### Performance
- CSS transforms for animations (GPU acceleration)
- Will-change property for frequently animated elements
- Lazy loading for images and heavy components
- Throttled scroll events

## Implementation Notes

### CSS Architecture
- BEM naming convention for custom classes
- Utility-first approach with Tabler/Bootstrap base
- CSS custom properties for theming
- Mobile-first media queries

### Framework Integration
- Built on Tabler.io (Bootstrap 5)
- Custom CSS layer: minipass-redesign.css
- Maintains Bootstrap grid system
- Compatible with existing Tabler components

### Dynamic Content Integration
- **Organization Name**: Pulled from Flask app settings via `current_app.config['ORG_NAME']`
- **Git Branch Detection**: Footer displays current branch via `subprocess` or environment variable
- Template implementation uses Jinja2 variables for dynamic content

### Git Branch Integration
```python
# In Flask app context
import subprocess
import os

def get_git_branch():
    try:
        branch = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
            cwd=os.path.dirname(__file__)
        ).decode('utf-8').strip()
        return branch
    except:
        return os.environ.get('GIT_BRANCH', 'main')

# Make available to templates
@app.context_processor
def inject_git_info():
    return {
        'git_branch': get_git_branch(),
        'org_name': current_app.config.get('ORG_NAME', 'Minipass')
    }
```

### Browser Support
- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: Latest 2 versions
- Mobile browsers: iOS Safari 12+, Chrome Mobile

### Performance Targets
- First Contentful Paint: < 1.5s
- Time to Interactive: < 3.5s
- Lighthouse Score: > 90
- Bundle size: < 200KB CSS

## File Structure

```
/static/
  ├── minipass-redesign.css  # Main redesign styles
  ├── minipass.css           # Legacy styles
  └── tabler/                # Tabler framework files

/templates/
  ├── base.html              # Main template with new structure
  └── components/            # Reusable component templates
```

## Migration Path

1. **Phase 1**: Implement new base.html structure
2. **Phase 2**: Update CSS with minipass-redesign.css
3. **Phase 3**: Test responsive behaviors
4. **Phase 4**: Migrate page-specific templates
5. **Phase 5**: Remove legacy styles

## Testing Checklist

- [ ] Desktop layout (1920x1080, 1440x900, 1366x768)
- [ ] Tablet layout (iPad, iPad Pro)
- [ ] Mobile layout (iPhone, Android devices)
- [ ] Keyboard navigation
- [ ] Screen reader compatibility
- [ ] Color contrast (WCAG AA)
- [ ] Touch interactions
- [ ] Performance metrics
- [ ] Cross-browser compatibility

---

**Version**: 1.2.0  
**Last Updated**: 2025-08-09  
**Author**: UI/UX Design Team  
**Status**: Ready for Implementation

## Changelog

### Version 1.2.0 (2025-08-09)
- **BREAKING**: Removed entire header bar section (search, notifications, user menu, action buttons)
- **NEW**: Added simplified organization name header with seamless background integration
- **NEW**: Dynamic organization name pulled from ORG_NAME settings variable
- **UPDATED**: Footer redesign - removed white background and borders
- **UPDATED**: Footer copyright format includes dynamic git branch detection
- **UPDATED**: Header background now matches main content area (#F8F9FA) for seamless flow
- **UPDATED**: Reduced header height from 64px to 48px for minimal footprint
- **TECHNICAL**: Added git branch detection implementation notes
- **TECHNICAL**: Added CSS specifications for new .minipass-org-header styles

### Version 1.1.0 (2025-08-09)
- Added centered content container with max-width (1320px) for better content balance
- Fixed asymmetric spacing issue between left and right margins
- Improved readability on wide screens by limiting content width