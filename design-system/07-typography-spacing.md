# Typography & Spacing System

## Typography Scale

### Font Family Stack
```css
:root {
  --mp-font-family-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --mp-font-family-mono: 'JetBrains Mono', 'SF Mono', Monaco, Inconsolata, 'Roboto Mono', Consolas, 'Courier New', monospace;
}

body {
  font-family: var(--mp-font-family-sans);
  font-size: 1rem;
  line-height: 1.5;
  color: var(--mp-gray-700);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
```

### Typography Scale (16px base)
```css
/* Display - Large headings, hero sections */
.text-display-1 {
  font-size: 3rem;      /* 48px */
  font-weight: 800;
  line-height: 1.1;
  letter-spacing: -0.02em;
  color: var(--mp-gray-900);
}

.text-display-2 {
  font-size: 2.5rem;    /* 40px */
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -0.01em;
  color: var(--mp-gray-900);
}

/* Headings - Page structure */
.text-h1, h1 {
  font-size: 2rem;      /* 32px */
  font-weight: 700;
  line-height: 1.25;
  color: var(--mp-gray-900);
  margin-bottom: 1rem;
}

.text-h2, h2 {
  font-size: 1.75rem;   /* 28px */
  font-weight: 600;
  line-height: 1.3;
  color: var(--mp-gray-900);
  margin-bottom: 0.875rem;
}

.text-h3, h3 {
  font-size: 1.5rem;    /* 24px */
  font-weight: 600;
  line-height: 1.35;
  color: var(--mp-gray-800);
  margin-bottom: 0.75rem;
}

.text-h4, h4 {
  font-size: 1.25rem;   /* 20px */
  font-weight: 600;
  line-height: 1.4;
  color: var(--mp-gray-800);
  margin-bottom: 0.625rem;
}

.text-h5, h5 {
  font-size: 1.125rem;  /* 18px */
  font-weight: 600;
  line-height: 1.45;
  color: var(--mp-gray-700);
  margin-bottom: 0.5rem;
}

.text-h6, h6 {
  font-size: 1rem;      /* 16px */
  font-weight: 600;
  line-height: 1.5;
  color: var(--mp-gray-700);
  margin-bottom: 0.5rem;
}

/* Body Text */
.text-body-lg {
  font-size: 1.125rem;  /* 18px */
  font-weight: 400;
  line-height: 1.6;
  color: var(--mp-gray-700);
}

.text-body, p {
  font-size: 1rem;      /* 16px */
  font-weight: 400;
  line-height: 1.5;
  color: var(--mp-gray-700);
  margin-bottom: 1rem;
}

.text-body-sm {
  font-size: 0.875rem;  /* 14px */
  font-weight: 400;
  line-height: 1.5;
  color: var(--mp-gray-600);
}

/* Small Text */
.text-caption {
  font-size: 0.75rem;   /* 12px */
  font-weight: 500;
  line-height: 1.4;
  color: var(--mp-gray-500);
}

.text-overline {
  font-size: 0.75rem;   /* 12px */
  font-weight: 600;
  line-height: 1.4;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--mp-gray-500);
}

/* Code Text */
.text-code {
  font-family: var(--mp-font-family-mono);
  font-size: 0.875rem;
  background: var(--mp-gray-100);
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  color: var(--mp-gray-800);
}
```

### Font Weight System
```css
.font-weight-light { font-weight: 300; }
.font-weight-normal { font-weight: 400; }
.font-weight-medium { font-weight: 500; }
.font-weight-semibold { font-weight: 600; }
.font-weight-bold { font-weight: 700; }
.font-weight-extrabold { font-weight: 800; }
```

### Text Color Classes
```css
/* Primary Text Colors */
.text-primary { color: var(--mp-gray-900); }
.text-secondary { color: var(--mp-gray-600); }
.text-muted { color: var(--mp-gray-500); }
.text-light { color: var(--mp-gray-400); }

/* Brand Colors */
.text-brand { color: var(--mp-primary-600); }
.text-brand-secondary { color: var(--mp-secondary-600); }

/* Status Colors */
.text-success { color: var(--mp-success); }
.text-warning { color: var(--mp-warning); }
.text-error { color: var(--mp-error); }
.text-info { color: var(--mp-info); }
```

## Spacing System

### Base Spacing Scale (4px grid)
```css
:root {
  --mp-space-0: 0;
  --mp-space-1: 0.25rem;    /* 4px */
  --mp-space-2: 0.5rem;     /* 8px */
  --mp-space-3: 0.75rem;    /* 12px */
  --mp-space-4: 1rem;       /* 16px */
  --mp-space-5: 1.25rem;    /* 20px */
  --mp-space-6: 1.5rem;     /* 24px */
  --mp-space-8: 2rem;       /* 32px */
  --mp-space-10: 2.5rem;    /* 40px */
  --mp-space-12: 3rem;      /* 48px */
  --mp-space-16: 4rem;      /* 64px */
  --mp-space-20: 5rem;      /* 80px */
  --mp-space-24: 6rem;      /* 96px */
}
```

### Margin Utilities
```css
/* Margin - All sides */
.m-0 { margin: var(--mp-space-0); }
.m-1 { margin: var(--mp-space-1); }
.m-2 { margin: var(--mp-space-2); }
.m-3 { margin: var(--mp-space-3); }
.m-4 { margin: var(--mp-space-4); }
.m-5 { margin: var(--mp-space-5); }
.m-6 { margin: var(--mp-space-6); }
.m-8 { margin: var(--mp-space-8); }
.m-10 { margin: var(--mp-space-10); }
.m-12 { margin: var(--mp-space-12); }

/* Margin - Specific sides */
.mt-0 { margin-top: var(--mp-space-0); }
.mt-1 { margin-top: var(--mp-space-1); }
.mt-2 { margin-top: var(--mp-space-2); }
.mt-3 { margin-top: var(--mp-space-3); }
.mt-4 { margin-top: var(--mp-space-4); }
.mt-5 { margin-top: var(--mp-space-5); }
.mt-6 { margin-top: var(--mp-space-6); }
.mt-8 { margin-top: var(--mp-space-8); }

.mb-0 { margin-bottom: var(--mp-space-0); }
.mb-1 { margin-bottom: var(--mp-space-1); }
.mb-2 { margin-bottom: var(--mp-space-2); }
.mb-3 { margin-bottom: var(--mp-space-3); }
.mb-4 { margin-bottom: var(--mp-space-4); }
.mb-5 { margin-bottom: var(--mp-space-5); }
.mb-6 { margin-bottom: var(--mp-space-6); }
.mb-8 { margin-bottom: var(--mp-space-8); }

.ml-0 { margin-left: var(--mp-space-0); }
.ml-1 { margin-left: var(--mp-space-1); }
.ml-2 { margin-left: var(--mp-space-2); }
.ml-3 { margin-left: var(--mp-space-3); }
.ml-4 { margin-left: var(--mp-space-4); }

.mr-0 { margin-right: var(--mp-space-0); }
.mr-1 { margin-right: var(--mp-space-1); }
.mr-2 { margin-right: var(--mp-space-2); }
.mr-3 { margin-right: var(--mp-space-3); }
.mr-4 { margin-right: var(--mp-space-4); }

/* Margin - Horizontal & Vertical */
.mx-0 { margin-left: var(--mp-space-0); margin-right: var(--mp-space-0); }
.mx-1 { margin-left: var(--mp-space-1); margin-right: var(--mp-space-1); }
.mx-2 { margin-left: var(--mp-space-2); margin-right: var(--mp-space-2); }
.mx-3 { margin-left: var(--mp-space-3); margin-right: var(--mp-space-3); }
.mx-4 { margin-left: var(--mp-space-4); margin-right: var(--mp-space-4); }
.mx-auto { margin-left: auto; margin-right: auto; }

.my-0 { margin-top: var(--mp-space-0); margin-bottom: var(--mp-space-0); }
.my-1 { margin-top: var(--mp-space-1); margin-bottom: var(--mp-space-1); }
.my-2 { margin-top: var(--mp-space-2); margin-bottom: var(--mp-space-2); }
.my-3 { margin-top: var(--mp-space-3); margin-bottom: var(--mp-space-3); }
.my-4 { margin-top: var(--mp-space-4); margin-bottom: var(--mp-space-4); }
.my-6 { margin-top: var(--mp-space-6); margin-bottom: var(--mp-space-6); }
.my-8 { margin-top: var(--mp-space-8); margin-bottom: var(--mp-space-8); }
```

### Padding Utilities
```css
/* Padding - All sides */
.p-0 { padding: var(--mp-space-0); }
.p-1 { padding: var(--mp-space-1); }
.p-2 { padding: var(--mp-space-2); }
.p-3 { padding: var(--mp-space-3); }
.p-4 { padding: var(--mp-space-4); }
.p-5 { padding: var(--mp-space-5); }
.p-6 { padding: var(--mp-space-6); }
.p-8 { padding: var(--mp-space-8); }

/* Padding - Specific sides */
.pt-0 { padding-top: var(--mp-space-0); }
.pt-1 { padding-top: var(--mp-space-1); }
.pt-2 { padding-top: var(--mp-space-2); }
.pt-3 { padding-top: var(--mp-space-3); }
.pt-4 { padding-top: var(--mp-space-4); }
.pt-6 { padding-top: var(--mp-space-6); }
.pt-8 { padding-top: var(--mp-space-8); }

.pb-0 { padding-bottom: var(--mp-space-0); }
.pb-1 { padding-bottom: var(--mp-space-1); }
.pb-2 { padding-bottom: var(--mp-space-2); }
.pb-3 { padding-bottom: var(--mp-space-3); }
.pb-4 { padding-bottom: var(--mp-space-4); }
.pb-6 { padding-bottom: var(--mp-space-6); }
.pb-8 { padding-bottom: var(--mp-space-8); }

.pl-0 { padding-left: var(--mp-space-0); }
.pl-1 { padding-left: var(--mp-space-1); }
.pl-2 { padding-left: var(--mp-space-2); }
.pl-3 { padding-left: var(--mp-space-3); }
.pl-4 { padding-left: var(--mp-space-4); }

.pr-0 { padding-right: var(--mp-space-0); }
.pr-1 { padding-right: var(--mp-space-1); }
.pr-2 { padding-right: var(--mp-space-2); }
.pr-3 { padding-right: var(--mp-space-3); }
.pr-4 { padding-right: var(--mp-space-4); }

/* Padding - Horizontal & Vertical */
.px-0 { padding-left: var(--mp-space-0); padding-right: var(--mp-space-0); }
.px-1 { padding-left: var(--mp-space-1); padding-right: var(--mp-space-1); }
.px-2 { padding-left: var(--mp-space-2); padding-right: var(--mp-space-2); }
.px-3 { padding-left: var(--mp-space-3); padding-right: var(--mp-space-3); }
.px-4 { padding-left: var(--mp-space-4); padding-right: var(--mp-space-4); }
.px-6 { padding-left: var(--mp-space-6); padding-right: var(--mp-space-6); }

.py-0 { padding-top: var(--mp-space-0); padding-bottom: var(--mp-space-0); }
.py-1 { padding-top: var(--mp-space-1); padding-bottom: var(--mp-space-1); }
.py-2 { padding-top: var(--mp-space-2); padding-bottom: var(--mp-space-2); }
.py-3 { padding-top: var(--mp-space-3); padding-bottom: var(--mp-space-3); }
.py-4 { padding-top: var(--mp-space-4); padding-bottom: var(--mp-space-4); }
.py-6 { padding-top: var(--mp-space-6); padding-bottom: var(--mp-space-6); }
```

## Layout Spacing

### Container Spacing
```css
.container-xl {
  max-width: 1320px;
  margin: 0 auto;
  padding: 0 var(--mp-space-4);
}

@media (max-width: 768px) {
  .container-xl {
    padding: 0 var(--mp-space-3);
  }
}
```

### Section Spacing
```css
.section {
  padding: var(--mp-space-12) 0;
}

.section-sm {
  padding: var(--mp-space-8) 0;
}

.section-lg {
  padding: var(--mp-space-20) 0;
}

@media (max-width: 768px) {
  .section {
    padding: var(--mp-space-8) 0;
  }
  
  .section-sm {
    padding: var(--mp-space-6) 0;
  }
  
  .section-lg {
    padding: var(--mp-space-12) 0;
  }
}
```

### Card Spacing
```css
.card {
  padding: var(--mp-space-6);
}

.card-header {
  padding: var(--mp-space-6) var(--mp-space-6) var(--mp-space-4);
}

.card-body {
  padding: var(--mp-space-6);
}

.card-footer {
  padding: var(--mp-space-4) var(--mp-space-6) var(--mp-space-6);
}

@media (max-width: 768px) {
  .card {
    padding: var(--mp-space-4);
  }
  
  .card-header {
    padding: var(--mp-space-4) var(--mp-space-4) var(--mp-space-3);
  }
  
  .card-body {
    padding: var(--mp-space-4);
  }
  
  .card-footer {
    padding: var(--mp-space-3) var(--mp-space-4) var(--mp-space-4);
  }
}
```

## Content Hierarchy Examples

### Page Header Pattern
```html
<div class="page-header mb-8">
  <div class="d-flex justify-content-between align-items-start">
    <div>
      <p class="text-overline mb-2">Overview</p>
      <h1 class="text-h1 mb-2">Dashboard</h1>
      <p class="text-body-lg text-muted mb-0">Welcome back, manage your digital passport activities</p>
    </div>
    <div>
      <button class="btn btn-primary">
        <i class="ti ti-plus me-2"></i>
        New Activity
      </button>
    </div>
  </div>
</div>
```

### Section Header Pattern
```html
<div class="section-header mb-6">
  <div class="d-flex align-items-center gap-3 mb-2">
    <i class="ti ti-activity text-brand" style="font-size: 1.5rem;"></i>
    <h2 class="text-h2 mb-0">Active Activities</h2>
  </div>
  <p class="text-body text-muted mb-0">Manage ongoing events and track participation</p>
</div>
```

### Card Content Pattern
```html
<div class="card">
  <div class="card-header">
    <h3 class="text-h4 mb-1">Revenue Overview</h3>
    <p class="text-body-sm text-muted mb-0">Last 30 days performance</p>
  </div>
  <div class="card-body">
    <div class="mb-4">
      <div class="text-display-2 text-brand mb-1">$12,450</div>
      <div class="text-body-sm text-success">↗ 12% from last month</div>
    </div>
    <!-- Chart or additional content -->
  </div>
</div>
```

## Responsive Typography

### Mobile Adjustments
```css
@media (max-width: 768px) {
  .text-display-1 {
    font-size: 2.5rem;    /* 40px */
    line-height: 1.15;
  }
  
  .text-display-2 {
    font-size: 2rem;      /* 32px */
    line-height: 1.2;
  }
  
  .text-h1, h1 {
    font-size: 1.75rem;   /* 28px */
    line-height: 1.25;
  }
  
  .text-h2, h2 {
    font-size: 1.5rem;    /* 24px */
    line-height: 1.3;
  }
  
  .text-h3, h3 {
    font-size: 1.25rem;   /* 20px */
    line-height: 1.35;
  }
}

@media (max-width: 480px) {
  .text-display-1 {
    font-size: 2rem;      /* 32px */
  }
  
  .text-display-2 {
    font-size: 1.75rem;   /* 28px */
  }
  
  .text-h1, h1 {
    font-size: 1.5rem;    /* 24px */
  }
}
```

### Line Length & Reading Comfort
```css
.prose {
  max-width: 65ch;  /* Optimal reading line length */
  line-height: 1.6;
}

.prose-wide {
  max-width: 80ch;  /* Wider for technical content */
}

.prose-narrow {
  max-width: 45ch;  /* Narrow for captions, sidebars */
}
```

## Implementation Guidelines

### Typography Best Practices
1. **Hierarchy**: Use consistent heading levels (don't skip h2 to h4)
2. **Line Height**: Maintain 1.4-1.6 line height for body text
3. **Color Contrast**: Ensure minimum 4.5:1 contrast ratio
4. **Font Loading**: Use font-display: swap for web fonts
5. **Mobile First**: Scale down typography for smaller screens

### Spacing Best Practices
1. **Consistent Grid**: Use 4px base unit for all spacing
2. **Vertical Rhythm**: Maintain consistent spacing between elements
3. **Component Spacing**: Inner spacing should be smaller than outer spacing
4. **Mobile Adjustment**: Reduce spacing proportionally on smaller screens
5. **Visual Balance**: Use more space around important elements

### Content Structure
1. **Page Headers**: Overline + H1 + Description pattern
2. **Section Headers**: Icon + H2 + Description pattern
3. **Card Headers**: H3/H4 + Subtitle pattern
4. **Data Labels**: Overline style for field labels
5. **Status Text**: Caption size for secondary information

## Implementation Priority

### Phase 1: Core Typography
1. Define base font stack and sizes
2. Implement heading hierarchy
3. Set up text color classes
4. Basic spacing utilities

### Phase 2: Advanced Typography
1. Display text styles for hero sections
2. Code text formatting
3. Responsive typography adjustments
4. Line length optimizations

### Phase 3: Spacing System
1. Complete spacing utility classes
2. Component-specific spacing patterns
3. Mobile spacing adjustments
4. Layout spacing standards