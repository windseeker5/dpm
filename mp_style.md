# Minipass UI/UX Style Guide

## Overview
This document defines the standardized UI/UX patterns for all Minipass templates. All templates should follow these guidelines for consistency and clean mobile-first design.

## Design Principles
- **Mobile-First**: All components must work seamlessly on mobile devices
- **Simple & Clean**: Minimal animations, focus on usability over flashy effects
- **Consistent Rounded Corners**: Use 8px border-radius for all components
- **Standard Tabler.io Styling**: Use native Tabler badges, buttons, and components
- **No Multi-Selectors**: Clean, simple interfaces without bulk selection checkboxes
- **Single Action Dropdowns**: Replace multiple small buttons with unified dropdown actions

## Color Palette
- **Primary Gradient**: `linear-gradient(135deg, #667eea 0%, #764ba2 100%)` (KPI cards only)
- **Card Background**: `#ffffff`
- **Panel Background**: `#f8f9fa` (simple solid color)
- **Border Color**: `#dee2e6` (standard Tabler border)
- **No Complex Shadows**: Use standard Tabler card styling

## Component Standards

### 1. Card Structure (Desktop Tables)
Use standard Tabler card structure with table:

```html
<div class="card">
  <div class="card-header">
    <h3 class="card-title">Section Title</h3>
  </div>
  <div class="table-responsive">
    <table class="table card-table table-vcenter">
      <!-- Table content -->
    </table>
  </div>
  <div class="card-footer d-flex align-items-center">
    <p class="m-0 text-muted">Showing entries</p>
    <ul class="pagination m-0 ms-auto">
      <!-- Pagination -->
    </ul>
  </div>
</div>
```

**CSS Requirements:**
```css
.card {
  background-color: #fff !important;
  border-radius: 8px;
  border: 1px solid #dee2e6;
}
```

### 2. Mobile Card Structure  
Clean, spacious mobile cards:

```html
<div class="mobile-card">
  <div class="mobile-card-header">
    <img src="..." class="activity-image me-3" alt="...">
    <div class="flex-fill">
      <h4 class="mobile-card-title">Item Name</h4>
    </div>
    <div class="dropdown">
      <a href="#" class="btn btn-outline-secondary btn-sm dropdown-toggle">Actions</a>
      <!-- Dropdown menu -->
    </div>
  </div>
  
  <div class="mobile-card-content">
    <div class="mobile-badges">
      <span class="badge bg-success">Active</span>
      <span class="badge bg-blue">Type</span>
    </div>
    
    <div class="mobile-stats">
      <div class="mobile-stat">
        <div class="mobile-stat-number">123</div>
        <div class="mobile-stat-label">Label</div>
      </div>
    </div>
  </div>
</div>
```

### 3. KPI Statistics Card
Simple gradient design:

```html
<div class="stats-card">
  <div class="row">
    <div class="col-6 col-md-3">
      <div class="stat-item">
        <span class="stat-number">{{ value }}</span>
        <span class="stat-label">Label</span>
      </div>
    </div>
    <!-- Repeat for other stats -->
  </div>
</div>
```

**CSS Requirements:**
```css
.stats-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.2);
  transition: all 0.3s ease;
}

.stats-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(102, 126, 234, 0.3);
}

.stat-item {
  text-align: center;
  padding: 0.75rem;
  transition: transform 0.2s ease;
}

.stat-item:hover {
  transform: scale(1.05);
}

.stat-number {
  font-size: 2.5rem;
  font-weight: 700;
  display: block;
  margin-bottom: 0.25rem;
  text-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.stat-label {
  font-size: 0.875rem;
  font-weight: 500;
  opacity: 0.95;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
```

### 3. Search & Filter Panel
Modern search with enhanced styling:

```html
<div class="filter-panel">
  <form method="GET" id="filterForm">
    <div class="row g-3">
      <div class="col-md-4">
        <div class="input-group">
          <input type="text" name="q" class="form-control search-input" 
                 placeholder="🔍 Search..." value="{{ current_filters.q }}" id="searchInput">
          <button type="submit" class="btn btn-search">
            <i class="ti ti-search"></i>
          </button>
        </div>
      </div>
      <!-- Additional filters -->
    </div>
  </form>
</div>
```

**CSS Requirements:**
```css
.filter-panel {
  background: linear-gradient(145deg, #f8f9fa 0%, #ffffff 100%);
  border: 1px solid rgba(0,0,0,0.06);
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
}

.search-input {
  border-radius: 8px;
  border: 2px solid #e9ecef;
  padding: 0.75rem 1rem;
  font-size: 0.95rem;
  transition: all 0.3s ease;
  background: #fff;
}

.search-input:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.15);
  transform: translateY(-1px);
}

.btn-search {
  border-radius: 8px;
  border: 2px solid #667eea;
  background: #667eea;
  color: white;
  padding: 0.75rem 1.25rem;
  transition: all 0.3s ease;
}

.btn-search:hover {
  background: #5a6fd8;
  border-color: #5a6fd8;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}
```

### 4. Action Dropdowns
Single dropdown approach instead of multiple buttons:

```html
<div class="dropdown">
  <button class="btn btn-sm action-dropdown dropdown-toggle" 
          data-bs-toggle="dropdown" data-bs-boundary="viewport">
    <i class="ti ti-dots-vertical me-1"></i> Actions
  </button>
  <div class="dropdown-menu dropdown-menu-end">
    <a class="dropdown-item" href="#">
      <i class="ti ti-pencil me-2"></i>Edit Item
    </a>
    <a class="dropdown-item" href="#">
      <i class="ti ti-chart-bar me-2"></i>View Statistics
    </a>
    <div class="dropdown-divider"></div>
    <a class="dropdown-item text-danger" href="#">
      <i class="ti ti-trash me-2"></i>Delete Item
    </a>
  </div>
</div>
```

**CSS Requirements:**
```css
.action-dropdown {
  border-radius: 8px;
  border: 2px solid #e9ecef;
  background: #fff;
  transition: all 0.3s ease;
  padding: 0.5rem 1rem;
}

.action-dropdown:hover {
  border-color: #667eea;
  background: #f8f9fa;
  transform: translateY(-1px);
}

.dropdown-menu {
  border-radius: 12px;
  border: 1px solid rgba(0,0,0,0.08);
  box-shadow: 0 8px 32px rgba(0,0,0,0.12);
  padding: 0.5rem;
  margin-top: 0.5rem;
}

.dropdown-item {
  border-radius: 8px;
  padding: 0.75rem 1rem;
  transition: all 0.2s ease;
  font-size: 0.9rem;
}

.dropdown-item:hover {
  background: #f8f9fa;
  transform: translateX(4px);
}
```

### 5. Form Controls
Consistent styling for all form elements:

```css
.form-select, .form-control {
  border-radius: 8px;
  border: 2px solid #e9ecef;
  padding: 0.75rem 1rem;
  transition: all 0.3s ease;
  background: #fff;
}

.form-select:focus, .form-control:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.15);
}
```

### 6. Buttons
Enhanced button styling with hover effects:

```css
.btn {
  border-radius: 8px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.btn:hover {
  transform: translateY(-1px);
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.btn-primary:hover {
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}
```

### 7. Mobile Responsive Patterns
```css
@media (max-width: 768px) {
  .desktop-table {
    display: none;
  }
  .mobile-cards {
    display: block;
  }
  .filter-panel {
    padding: 1rem;
  }
  .stats-card {
    padding: 1.5rem;
  }
  .stat-number {
    font-size: 2rem;
  }
  .card-body {
    padding: 1rem;
  }
}

@media (min-width: 769px) {
  .desktop-table {
    display: block;
  }
  .mobile-cards {
    display: none;
  }
}
```

### 8. JavaScript Enhancements
Standard animations and interactions:

```javascript
document.addEventListener('DOMContentLoaded', function() {
  // Enhanced search input animations
  const searchInput = document.getElementById('searchInput');
  searchInput.addEventListener('focus', function() {
    this.style.transform = 'translateY(-2px)';
    this.style.boxShadow = '0 8px 25px rgba(102, 126, 234, 0.15)';
  });
  
  // Enhanced button interactions
  document.querySelectorAll('.btn').forEach(btn => {
    btn.addEventListener('mouseenter', function() {
      if (!this.disabled) {
        this.style.transform = 'translateY(-2px)';
      }
    });
    btn.addEventListener('mouseleave', function() {
      this.style.transform = 'translateY(0)';
    });
  });
  
  // Card hover animations
  document.querySelectorAll('.card').forEach(card => {
    card.addEventListener('mouseenter', function() {
      this.style.transform = 'translateY(-4px)';
      this.style.boxShadow = '0 8px 32px rgba(0,0,0,0.12)';
    });
    card.addEventListener('mouseleave', function() {
      this.style.transform = 'translateY(-2px)';
      this.style.boxShadow = '0 4px 20px rgba(0,0,0,0.08)';
    });
  });
});
```

## Implementation Checklist

For each template, ensure:
- [ ] Uses card-header and card-body structure
- [ ] Has 12px rounded corners throughout
- [ ] No multi-selector checkboxes
- [ ] Single action dropdown instead of multiple buttons
- [ ] Modern search bar with animations
- [ ] Enhanced KPI statistics card
- [ ] Proper mobile responsiveness
- [ ] Consistent color scheme and gradients
- [ ] Smooth animations and transitions

## Notes
- Always use `data-bs-boundary="viewport"` for dropdowns to prevent clipping
- Remove all bulk action functionality and related JavaScript
- Use Tabler icons consistently with proper spacing
- Maintain accessibility with proper ARIA attributes
- Test on mobile devices to ensure touch-friendly interactions