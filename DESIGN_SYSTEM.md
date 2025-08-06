# Minipass Design System Documentation

## Overview
This design system provides a comprehensive guide for implementing the Minipass UI redesign using Tabler.io components and custom enhancements. All components respect the existing style guide while introducing modern refinements.

## 1. Design Tokens

### Color Palette

#### Brand Colors
```css
/* Primary - Respecting existing #206bc4 */
--minipass-primary-50: #eff6ff;
--minipass-primary-100: #dbeafe;
--minipass-primary-200: #bfdbfe;
--minipass-primary-300: #93c5fd;
--minipass-primary-400: #60a5fa;
--minipass-primary-500: #3b82f6;
--minipass-primary-600: #206bc4; /* Current Primary */
--minipass-primary-700: #1d4ed8;
--minipass-primary-800: #1e40af;
--minipass-primary-900: #1e3a8a;

/* Brand Gradient - From Style Guide */
--minipass-brand-gradient: linear-gradient(180deg, #ffffff 0%, #fef3c7 100%);
```

#### Semantic Colors
```css
/* Success */
--minipass-success: #10b981;
--minipass-success-light: #d1fae5;
--minipass-success-dark: #065f46;

/* Warning */
--minipass-warning: #f59e0b;
--minipass-warning-light: #fef3c7;
--minipass-warning-dark: #92400e;

/* Danger */
--minipass-danger: #ef4444;
--minipass-danger-light: #fee2e2;
--minipass-danger-dark: #991b1b;

/* Info */
--minipass-info: #3b82f6;
--minipass-info-light: #dbeafe;
--minipass-info-dark: #1e40af;
```

#### Neutral Colors
```css
--minipass-gray-50: #f9fafb;
--minipass-gray-100: #f3f4f6;
--minipass-gray-200: #e5e7eb;
--minipass-gray-300: #d1d5db;
--minipass-gray-400: #9ca3af;
--minipass-gray-500: #6b7280;
--minipass-gray-600: #4b5563;
--minipass-gray-700: #374151;
--minipass-gray-800: #1f2937;
--minipass-gray-900: #111827;
```

### Typography

#### Font Families
```css
/* Brand Font - From Style Guide */
--minipass-font-brand: 'Anton', sans-serif;

/* System Font Stack */
--minipass-font-system: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;

/* Monospace for data */
--minipass-font-mono: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', monospace;
```

#### Font Sizes & Line Heights
```css
--minipass-text-xs: 0.75rem;    /* 12px */
--minipass-text-sm: 0.875rem;   /* 14px */
--minipass-text-base: 1rem;     /* 16px */
--minipass-text-lg: 1.125rem;   /* 18px */
--minipass-text-xl: 1.25rem;    /* 20px */
--minipass-text-2xl: 1.5rem;    /* 24px */
--minipass-text-3xl: 1.875rem;  /* 30px */
--minipass-text-4xl: 2.25rem;   /* 36px */
--minipass-text-5xl: 3rem;      /* 48px */

/* Line Heights */
--minipass-leading-tight: 1.25;
--minipass-leading-normal: 1.5;
--minipass-leading-relaxed: 1.75;
```

#### Font Weights
```css
--minipass-font-light: 300;
--minipass-font-normal: 400;
--minipass-font-medium: 500;
--minipass-font-semibold: 600;
--minipass-font-bold: 700;
```

### Spacing System
```css
--minipass-space-0: 0;
--minipass-space-1: 0.25rem;  /* 4px */
--minipass-space-2: 0.5rem;   /* 8px */
--minipass-space-3: 0.75rem;  /* 12px */
--minipass-space-4: 1rem;     /* 16px */
--minipass-space-5: 1.25rem;  /* 20px */
--minipass-space-6: 1.5rem;   /* 24px */
--minipass-space-8: 2rem;     /* 32px */
--minipass-space-10: 2.5rem;  /* 40px */
--minipass-space-12: 3rem;    /* 48px */
--minipass-space-16: 4rem;    /* 64px */
--minipass-space-20: 5rem;    /* 80px */
```

### Border Radius
```css
--minipass-radius-none: 0;
--minipass-radius-sm: 0.125rem;   /* 2px */
--minipass-radius-default: 0.25rem; /* 4px */
--minipass-radius-md: 0.375rem;   /* 6px */
--minipass-radius-lg: 0.5rem;     /* 8px */
--minipass-radius-xl: 1rem;       /* 16px - From Style Guide */
--minipass-radius-2xl: 1.5rem;    /* 24px */
--minipass-radius-full: 9999px;
```

### Shadows
```css
--minipass-shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
--minipass-shadow-default: 0 1px 3px 0 rgb(0 0 0 / 0.1);
--minipass-shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
--minipass-shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
--minipass-shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1);
--minipass-shadow-glass: 0 8px 32px 0 rgb(31 38 135 / 0.37);
```

### Breakpoints
```css
--minipass-screen-xs: 480px;
--minipass-screen-sm: 640px;
--minipass-screen-md: 768px;
--minipass-screen-lg: 1024px;
--minipass-screen-xl: 1280px;
--minipass-screen-2xl: 1536px;
```

## 2. Component Library

### Cards

#### Basic Card
```html
<!-- Tabler.io Card with Minipass enhancements -->
<div class="card minipass-card">
  <div class="card-body">
    <h3 class="card-title">Card Title</h3>
    <p class="text-muted">Card content goes here</p>
  </div>
</div>
```

```css
.minipass-card {
  border-radius: var(--minipass-radius-xl); /* 16px from style guide */
  border: none;
  box-shadow: var(--minipass-shadow-default);
  transition: all 0.3s ease;
}

.minipass-card:hover {
  box-shadow: var(--minipass-shadow-md);
  transform: translateY(-2px);
}
```

#### KPI Card
```html
<div class="card minipass-kpi-card">
  <div class="card-body p-3">
    <div class="d-flex align-items-center">
      <div class="flex-fill">
        <h4 class="minipass-kpi-value">$12,458</h4>
        <div class="text-muted minipass-kpi-label">Total Revenue</div>
      </div>
      <div class="minipass-kpi-chart">
        <!-- Sparkline chart here -->
      </div>
    </div>
    <div class="minipass-kpi-trend mt-2">
      <span class="badge bg-success-lt">
        <svg class="icon"><!-- Up arrow icon --></svg>
        12.5%
      </span>
    </div>
  </div>
</div>
```

#### Glass Card (Modern Enhancement)
```html
<div class="card minipass-glass-card">
  <div class="card-body">
    <!-- Content -->
  </div>
</div>
```

```css
.minipass-glass-card {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
}
```

### Navigation

#### Desktop Navigation
```html
<header class="navbar navbar-expand-md minipass-navbar">
  <div class="container-xl">
    <h1 class="navbar-brand minipass-brand">
      MINIPASS
    </h1>
    <div class="navbar-nav flex-row order-md-last">
      <!-- User menu -->
    </div>
    <div class="collapse navbar-collapse">
      <div class="navbar-nav">
        <a class="nav-link active" href="/dashboard">
          <span class="nav-link-icon">
            <svg class="icon"><!-- Icon --></svg>
          </span>
          <span class="nav-link-title">Dashboard</span>
        </a>
        <!-- More nav items -->
      </div>
    </div>
  </div>
</header>
```

#### Mobile Bottom Navigation
```html
<nav class="minipass-mobile-nav d-md-none">
  <a href="/dashboard" class="minipass-mobile-nav-item active">
    <svg class="icon"><!-- Icon --></svg>
    <span>Home</span>
  </a>
  <a href="/activities" class="minipass-mobile-nav-item">
    <svg class="icon"><!-- Icon --></svg>
    <span>Activities</span>
  </a>
  <a href="/passes" class="minipass-mobile-nav-item">
    <svg class="icon"><!-- Icon --></svg>
    <span>Passes</span>
  </a>
  <a href="/payments" class="minipass-mobile-nav-item">
    <svg class="icon"><!-- Icon --></svg>
    <span>Payments</span>
  </a>
  <a href="/more" class="minipass-mobile-nav-item">
    <svg class="icon"><!-- Icon --></svg>
    <span>More</span>
  </a>
</nav>
```

```css
.minipass-mobile-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: white;
  box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
  display: flex;
  padding: 8px 0;
  z-index: 1000;
}

.minipass-mobile-nav-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px;
  color: var(--minipass-gray-600);
  text-decoration: none;
  font-size: 12px;
}

.minipass-mobile-nav-item.active {
  color: var(--minipass-primary-600);
}
```

### Forms

#### Floating Label Input
```html
<div class="form-floating minipass-form-floating">
  <input type="email" class="form-control" id="email" placeholder="name@example.com">
  <label for="email">Email address</label>
</div>
```

#### Multi-Step Form
```html
<div class="minipass-form-wizard">
  <!-- Progress Bar -->
  <div class="minipass-wizard-progress">
    <div class="progress">
      <div class="progress-bar" style="width: 33%"></div>
    </div>
    <div class="minipass-wizard-steps">
      <div class="minipass-wizard-step active">
        <span class="minipass-wizard-step-number">1</span>
        <span class="minipass-wizard-step-label">Basic Info</span>
      </div>
      <div class="minipass-wizard-step">
        <span class="minipass-wizard-step-number">2</span>
        <span class="minipass-wizard-step-label">Details</span>
      </div>
      <div class="minipass-wizard-step">
        <span class="minipass-wizard-step-number">3</span>
        <span class="minipass-wizard-step-label">Confirm</span>
      </div>
    </div>
  </div>
  
  <!-- Form Steps -->
  <div class="minipass-wizard-content">
    <!-- Step content -->
  </div>
</div>
```

### Buttons

#### Primary Actions
```html
<!-- Using Tabler classes with Minipass enhancements -->
<button class="btn btn-primary minipass-btn-primary">
  Create Activity
</button>

<button class="btn btn-success minipass-btn-success">
  <svg class="icon icon-tabler icon-tabler-check"><!-- Icon --></svg>
  Save Changes
</button>
```

```css
.minipass-btn-primary {
  background: var(--minipass-primary-600);
  border-radius: var(--minipass-radius-lg);
  padding: var(--minipass-space-3) var(--minipass-space-6);
  font-weight: var(--minipass-font-semibold);
  transition: all 0.2s ease;
}

.minipass-btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: var(--minipass-shadow-md);
}
```

#### Floating Action Button (Mobile)
```html
<button class="minipass-fab d-md-none">
  <svg class="icon icon-tabler icon-tabler-plus"><!-- Plus icon --></svg>
</button>
```

```css
.minipass-fab {
  position: fixed;
  bottom: 80px; /* Above mobile nav */
  right: 16px;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--minipass-primary-600);
  color: white;
  border: none;
  box-shadow: var(--minipass-shadow-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 900;
}
```

### Tables (Mobile Optimized)

#### Responsive Table Card View
```html
<!-- Desktop: Table View -->
<div class="table-responsive d-none d-md-block">
  <table class="table table-vcenter minipass-table">
    <thead>
      <tr>
        <th>Activity</th>
        <th>Date</th>
        <th>Status</th>
        <th>Revenue</th>
        <th class="w-1"></th>
      </tr>
    </thead>
    <tbody>
      <!-- Table rows -->
    </tbody>
  </table>
</div>

<!-- Mobile: Card View -->
<div class="d-md-none">
  <div class="minipass-mobile-table-card">
    <div class="d-flex justify-content-between mb-2">
      <strong>Hockey Season 2024</strong>
      <span class="badge bg-success">Active</span>
    </div>
    <div class="text-muted small">Jan 15, 2024</div>
    <div class="mt-2">
      <span class="text-muted">Revenue:</span>
      <strong>$1,250</strong>
    </div>
    <div class="mt-3">
      <button class="btn btn-sm btn-outline-primary">View Details</button>
    </div>
  </div>
</div>
```

### Data Visualization

#### Enhanced KPI with Sparkline
```html
<div class="minipass-kpi-enhanced">
  <div class="minipass-kpi-header">
    <span class="minipass-kpi-icon">
      <svg class="icon"><!-- Icon --></svg>
    </span>
    <span class="minipass-kpi-period">Last 30 days</span>
  </div>
  <div class="minipass-kpi-value">
    $24,589
    <span class="minipass-kpi-change positive">+12.5%</span>
  </div>
  <div class="minipass-kpi-label">Total Revenue</div>
  <div class="minipass-kpi-sparkline">
    <canvas id="sparkline-revenue"></canvas>
  </div>
</div>
```

### Loading States

#### Skeleton Loader
```html
<div class="card minipass-skeleton">
  <div class="card-body">
    <div class="minipass-skeleton-line" style="width: 60%"></div>
    <div class="minipass-skeleton-line" style="width: 100%"></div>
    <div class="minipass-skeleton-line" style="width: 80%"></div>
  </div>
</div>
```

```css
.minipass-skeleton-line {
  height: 12px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: loading 1.5s infinite;
  border-radius: var(--minipass-radius-default);
  margin-bottom: 8px;
}

@keyframes loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
```

### Empty States

```html
<div class="empty">
  <div class="empty-icon">
    <svg class="icon icon-tabler icon-tabler-mood-happy"><!-- Icon --></svg>
  </div>
  <p class="empty-title">No activities yet</p>
  <p class="empty-subtitle text-muted">
    Create your first activity to get started
  </p>
  <div class="empty-action">
    <button class="btn btn-primary">
      <svg class="icon"><!-- Plus icon --></svg>
      Create Activity
    </button>
  </div>
</div>
```

## 3. Interaction Patterns

### Micro-Interactions

#### Hover Effects
- Cards: Subtle elevation on hover
- Buttons: Scale and shadow changes
- Links: Underline animation

#### Transitions
```css
/* Standard transition timing */
--minipass-transition-fast: 150ms ease;
--minipass-transition-normal: 300ms ease;
--minipass-transition-slow: 500ms ease;
```

#### Feedback States
- Loading: Skeleton screens and spinners
- Success: Green toast notifications
- Error: Red inline validation messages
- Processing: Disabled state with spinner

### Mobile Gestures

#### Swipe Actions
- Horizontal swipe for carousel navigation
- Pull-to-refresh for data updates
- Swipe-to-delete with confirmation

#### Touch Targets
- Minimum 44x44px touch areas
- 8px minimum spacing between targets
- Visual feedback on touch (ripple effect)

## 4. Accessibility Guidelines

### Color Contrast
- Normal text: 4.5:1 minimum ratio
- Large text: 3:1 minimum ratio
- Interactive elements: Clear focus states

### Keyboard Navigation
- All interactive elements keyboard accessible
- Visible focus indicators
- Logical tab order
- Skip navigation links

### Screen Reader Support
- Semantic HTML structure
- ARIA labels where needed
- Alt text for images
- Form label associations

## 5. Implementation with Tabler.io

### Required Tabler Components
- Cards and Card Decks
- Navigation and Navbar
- Forms and Form Controls
- Buttons and Button Groups
- Tables and Data Tables
- Modals and Offcanvas
- Alerts and Toasts
- Progress Bars
- Badges and Pills
- Dropdowns and Popovers

### Custom CSS File Structure
```css
/* minipass-redesign.css */

/* 1. Design Tokens */
:root {
  /* Color tokens */
  /* Typography tokens */
  /* Spacing tokens */
  /* Shadow tokens */
}

/* 2. Base Styles */
.minipass-brand { }
.minipass-card { }
.minipass-btn-primary { }

/* 3. Component Overrides */
.card.minipass-card { }
.navbar.minipass-navbar { }

/* 4. Mobile Specific */
@media (max-width: 768px) {
  .minipass-mobile-nav { }
  .minipass-mobile-table-card { }
}

/* 5. Utility Classes */
.minipass-mt-1 { margin-top: var(--minipass-space-1); }
.minipass-shadow-glass { box-shadow: var(--minipass-shadow-glass); }
```

## 6. Flask/Jinja2 Integration

### Template Structure
```jinja2
<!-- base_redesign.html -->
{% extends "base.html" %}

{% block styles %}
  {{ super() }}
  <link rel="stylesheet" href="{{ url_for('static', filename='minipass-redesign.css') }}">
{% endblock %}

{% block content %}
  <div class="minipass-container">
    {% block minipass_content %}{% endblock %}
  </div>
{% endblock %}
```

### Component Macros
```jinja2
<!-- macros/cards.html -->
{% macro kpi_card(title, value, trend, icon) %}
<div class="card minipass-kpi-card">
  <div class="card-body">
    <!-- KPI card content -->
  </div>
</div>
{% endmacro %}
```

## 7. Progressive Enhancement

### CSS Variables Fallback
```css
.minipass-card {
  border-radius: 16px; /* Fallback */
  border-radius: var(--minipass-radius-xl, 16px);
}
```

### Feature Detection
```javascript
// Check for CSS Grid support
if (CSS.supports('display', 'grid')) {
  // Use grid layout
} else {
  // Fallback to flexbox
}
```

## Conclusion

This design system provides a complete foundation for implementing the Minipass UI redesign. It maintains compatibility with Tabler.io while introducing modern enhancements that create a cleaner, more elegant user experience. The system is built for scalability and maintains consistency across all application screens while respecting the original style guide elements.