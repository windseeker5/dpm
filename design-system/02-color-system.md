# MiniPass Color System

## Primary Color Palette

### Brand Colors
```css
/* Primary Brand Blue - Professional & Trustworthy */
--mp-primary: #2563eb;        /* Main brand color */
--mp-primary-50: #eff6ff;     /* Lightest blue - backgrounds */
--mp-primary-100: #dbeafe;    /* Light blue - hover states */
--mp-primary-200: #bfdbfe;    /* Medium light - borders */
--mp-primary-500: #3b82f6;    /* Standard blue - interactive elements */
--mp-primary-600: #2563eb;    /* Primary blue - main buttons */
--mp-primary-700: #1d4ed8;    /* Dark blue - active states */
--mp-primary-900: #1e3a8a;    /* Darkest blue - text */

/* Secondary Purple - Modern Accent */
--mp-secondary: #7c3aed;      /* Secondary brand color */
--mp-secondary-50: #f5f3ff;   /* Background tint */
--mp-secondary-100: #ede9fe;  /* Light accent */
--mp-secondary-500: #8b5cf6;  /* Medium purple */
--mp-secondary-600: #7c3aed;  /* Main secondary */
--mp-secondary-700: #6d28d9;  /* Dark purple */
```

### Functional Colors
```css
/* Success - Green */
--mp-success: #059669;        /* Success actions */
--mp-success-50: #ecfdf5;     /* Success backgrounds */
--mp-success-100: #d1fae5;    /* Success hover */

/* Warning - Amber */
--mp-warning: #d97706;        /* Warning states */
--mp-warning-50: #fffbeb;     /* Warning backgrounds */
--mp-warning-100: #fef3c7;    /* Warning hover */

/* Error - Red */
--mp-error: #dc2626;          /* Error states */
--mp-error-50: #fef2f2;       /* Error backgrounds */
--mp-error-100: #fee2e2;      /* Error hover */

/* Info - Cyan */
--mp-info: #0891b2;           /* Info states */
--mp-info-50: #ecfeff;        /* Info backgrounds */
--mp-info-100: #cffafe;       /* Info hover */
```

### Neutral Palette
```css
/* Gray Scale - Professional */
--mp-gray-50: #f9fafb;        /* Page backgrounds */
--mp-gray-100: #f3f4f6;       /* Card backgrounds */
--mp-gray-200: #e5e7eb;       /* Borders, dividers */
--mp-gray-300: #d1d5db;       /* Input borders */
--mp-gray-400: #9ca3af;       /* Placeholders */
--mp-gray-500: #6b7280;       /* Secondary text */
--mp-gray-600: #4b5563;       /* Primary text light */
--mp-gray-700: #374151;       /* Primary text */
--mp-gray-800: #1f2937;       /* Headers, emphasis */
--mp-gray-900: #111827;       /* High contrast text */
```

## Color Usage Guidelines

### Navigation
```css
/* NEW: Single Navigation Design */
.navbar-primary {
  background: linear-gradient(135deg, var(--mp-primary-600) 0%, var(--mp-secondary-600) 100%);
  color: white;
}

/* Remove the dual navigation system */
/* OLD: .navbar.bg-gray-800 + .navbar.bg-white */
/* NEW: Single gradient navigation */
```

### Cards & Components
```css
/* KPI Cards */
.kpi-card {
  background: white;
  border: 1px solid var(--mp-gray-200);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* Activity Cards */
.activity-card {
  background: white;
  border: 1px solid var(--mp-gray-200);
  transition: all 0.2s ease;
}

.activity-card:hover {
  border-color: var(--mp-primary-200);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.15);
}
```

### Interactive Elements
```css
/* Primary Buttons */
.btn-primary {
  background: var(--mp-primary-600);
  border-color: var(--mp-primary-600);
  color: white;
}

.btn-primary:hover {
  background: var(--mp-primary-700);
  border-color: var(--mp-primary-700);
}

/* Secondary Buttons */
.btn-secondary {
  background: var(--mp-gray-100);
  border-color: var(--mp-gray-300);
  color: var(--mp-gray-700);
}

/* Success Actions */
.btn-success {
  background: var(--mp-success);
  border-color: var(--mp-success);
}
```

### Status Indicators
```css
/* Revenue/Financial */
.status-revenue { color: var(--mp-success); }

/* Active/Live */
.status-active { color: var(--mp-primary-600); }

/* Pending/Warning */
.status-pending { color: var(--mp-warning); }

/* Error/Inactive */
.status-error { color: var(--mp-error); }

/* Information */
.status-info { color: var(--mp-info); }
```

## Logo & Brand Treatment

### NEW: Simplified Logo
```css
/* Replace bright gradient with professional treatment */
.brand-logo {
  font-family: 'Inter', sans-serif;
  font-weight: 600;
  font-size: 1.5rem;
  color: white;
  text-decoration: none;
}

/* Remove OLD gradient */
/* OLD: background: linear-gradient(to right, #fffee9, #bc6ff1, #ed2988); */
```

### Icon Usage
- **Primary icons**: Use Tabler Icons in `--mp-primary-600`
- **Secondary icons**: Use `--mp-gray-500` for less important icons
- **Status icons**: Match status colors (success green, warning amber, etc.)

## Accessibility Compliance

### Contrast Ratios
- **Primary text**: `--mp-gray-700` on white (AAA compliant)
- **Secondary text**: `--mp-gray-500` on white (AA compliant)
- **Button text**: White on `--mp-primary-600` (AAA compliant)
- **Links**: `--mp-primary-600` with 4.5:1 contrast ratio

### Color Blindness Considerations
- Never rely on color alone for information
- Use icons + color for status indicators
- Test with color blindness simulators
- Ensure sufficient contrast in all color combinations

## Implementation Notes

### CSS Custom Properties
Define all colors as CSS custom properties for easy theming:

```css
:root {
  /* Primary brand colors */
  --mp-primary: #2563eb;
  --mp-primary-50: #eff6ff;
  /* ... continue with full palette */
}
```

### Tabler.io Integration
- Override Tabler's default primary color with `--mp-primary`
- Maintain Tabler's component structure
- Add custom properties for extended palette
- Use Tabler's utility classes with custom colors