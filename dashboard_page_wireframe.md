# Minipass Dashboard Page Wireframe

## Overview
This wireframe defines a modern, elegant dashboard for the Minipass application using exclusively Tabler.io components from the style guide. The design prioritizes rapid development with existing components while maintaining visual appeal and functionality.

## Page Structure

### Header Section
Utilizing the existing base.html structure with page title and breadcrumbs.

### Component References & Layout

## 1. KPI Cards Section (Lines 597-748 from style guide)

**Layout:** 4-column grid on desktop, 2-column on tablet, 1-column on mobile

### Revenue Card (Advanced KPI with Chart - Lines 600-628)
```html
<div class="col-lg-3 col-md-6 mb-3">
  <div class="card" style="border-radius: 12px; overflow: hidden;">
    <div class="card-body">
      <div class="d-flex align-items-center justify-content-between mb-2">
        <div class="text-muted small text-uppercase">REVENUE</div>
        <div class="dropdown">
          <button class="btn btn-sm text-muted dropdown-toggle" type="button" data-bs-toggle="dropdown">
            Last 30 days
          </button>
          <ul class="dropdown-menu">
            <li><a class="dropdown-item" href="#">Last 7 days</a></li>
            <li><a class="dropdown-item" href="#">Last 30 days</a></li>
            <li><a class="dropdown-item" href="#">Last 90 days</a></li>
          </ul>
        </div>
      </div>
      <div class="h2 mb-1">${{ total_revenue|default('0.00') }}</div>
      <div class="d-flex align-items-center mb-3">
        <div class="text-success me-2">
          {{ revenue_growth|default('0') }}% <i class="ti ti-trending-up"></i>
        </div>
      </div>
      <div style="height: 40px; position: relative; overflow: hidden;">
        <svg width="100%" height="40" viewBox="0 0 300 40" preserveAspectRatio="none">
          <path d="M 0,32 L 15,30 L 30,31 L 45,28 L 60,29 L 75,26 L 90,27 L 105,24 L 120,25 L 135,22 L 150,24 L 165,21 L 180,22 L 195,19 L 210,20 L 225,18 L 240,19 L 255,17 L 270,18 L 285,16 L 300,17" 
                fill="none" stroke="#206bc4" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </div>
    </div>
  </div>
</div>
```

### Active Passes Card (Bar Chart KPI - Lines 629-674)
```html
<div class="col-lg-3 col-md-6 mb-3">
  <div class="card" style="border-radius: 12px; overflow: hidden;">
    <div class="card-body">
      <div class="d-flex align-items-center justify-content-between mb-2">
        <div class="text-muted small text-uppercase">ACTIVE PASSES</div>
        <div class="dropdown">
          <button class="btn btn-sm text-muted dropdown-toggle" type="button" data-bs-toggle="dropdown">
            This month
          </button>
          <ul class="dropdown-menu">
            <li><a class="dropdown-item" href="#">This month</a></li>
            <li><a class="dropdown-item" href="#">Last month</a></li>
            <li><a class="dropdown-item" href="#">Last 3 months</a></li>
          </ul>
        </div>
      </div>
      <div class="h2 mb-1">{{ active_passes_count|default('0') }}</div>
      <div class="d-flex align-items-center mb-3">
        <div class="text-success me-2">
          {{ passes_growth|default('0') }}% <i class="ti ti-trending-up"></i>
        </div>
      </div>
      <div style="height: 40px; position: relative; overflow: hidden;">
        <!-- Bar chart SVG from lines 651-670 -->
        <svg width="100%" height="40" viewBox="0 0 300 40" preserveAspectRatio="none">
          {% for i in range(19) %}
          <rect x="{{ 10 + (i * 15) }}" y="{{ 40 - (10 + (i * 1.5)) }}" width="8" height="{{ 10 + (i * 1.5) }}" fill="#206bc4" opacity="0.8" />
          {% endfor %}
        </svg>
      </div>
    </div>
  </div>
</div>
```

### Total Activities Card (Simple KPI - Lines 703-713)
```html
<div class="col-lg-3 col-md-6 mb-3">
  <div class="card" style="border-radius: 12px; overflow: hidden;">
    <div class="card-body text-center">
      <div class="text-muted small text-uppercase mb-2">TOTAL ACTIVITIES</div>
      <div class="h3 mb-1">{{ total_activities|default('0') }}</div>
      <div class="text-success small">
        <i class="ti ti-trending-up me-1"></i>{{ activities_growth|default('0') }}%
      </div>
    </div>
  </div>
</div>
```

### Conversion Rate Card (Simple KPI - Lines 725-735)
```html
<div class="col-lg-3 col-md-6 mb-3">
  <div class="card" style="border-radius: 12px; overflow: hidden;">
    <div class="card-body text-center">
      <div class="text-muted small text-uppercase mb-2">CONVERSION RATE</div>
      <div class="h3 mb-1">{{ conversion_rate|default('0.0') }}%</div>
      <div class="text-warning small">
        <i class="ti ti-minus me-1"></i>{{ conversion_change|default('0') }}%
      </div>
    </div>
  </div>
</div>
```

## 2. Recent Activities Section (Lines 750-837)

**Layout:** 3-column grid on desktop, 2-column on tablet, 1-column on mobile

```html
<div class="row mb-4">
  <div class="col-12">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h3 class="page-title">Recent Activities</h3>
      <a href="{{ url_for('list_activities') }}" class="btn btn-outline-primary btn-sm">
        View All <i class="ti ti-arrow-right ms-1"></i>
      </a>
    </div>
  </div>
  {% for activity in recent_activities %}
  <div class="col-lg-4 col-md-6 mb-3">
    <div class="card" style="border-radius: 12px; overflow: hidden;">
      <!-- Activity Image -->
      {% if activity.image_path %}
      <div class="img-responsive img-responsive-21x9 card-img-top" 
           style="background-image: url('{{ url_for('static', filename='uploads/activity_images/' + activity.image_path) }}');">
      </div>
      {% else %}
      <div class="img-responsive img-responsive-21x9 card-img-top" 
           style="background: linear-gradient(45deg, #e3f2fd 0%, #2196f3 100%); display: flex; align-items: center; justify-content: center;">
        <i class="ti ti-calendar-event" style="font-size: 3rem; color: #1976d2; opacity: 0.8;"></i>
      </div>
      {% endif %}
      <div class="card-body">
        <div class="d-flex justify-content-between align-items-center mb-2">
          <h3 class="card-title mb-0">{{ activity.name|truncate(25) }}</h3>
          <small class="text-muted">{{ activity.days_remaining }}d left</small>
        </div>
        <div class="d-flex gap-2 flex-wrap mb-3">
          <span class="badge bg-green-lt">{{ activity.active_signups }} active</span>
          <span class="badge bg-yellow-lt">{{ activity.pending_signups }} pending</span>
          <span class="badge bg-blue-lt">{{ activity.total_passports }} passes</span>
        </div>
        <a href="{{ url_for('activity_detail', activity_id=activity.id) }}" class="btn btn-secondary btn-sm">
          <i class="ti ti-settings me-1"></i>Manage
        </a>
      </div>
    </div>
  </div>
  {% endfor %}
</div>
```

## 3. Recent Signups Table (Lines 870-1204)

```html
<div class="row mb-4">
  <div class="col-12">
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Recent Signups</h3>
        <div class="card-actions">
          <a href="{{ url_for('list_signups') }}" class="btn btn-outline-primary btn-sm">
            View All <i class="ti ti-arrow-right ms-1"></i>
          </a>
        </div>
      </div>
      <div class="card-body">
        <!-- Search Bar (Lines 880-892) -->
        <div class="d-flex justify-content-end align-items-center mb-3">
          <div class="position-relative" style="width: 300px;">
            <div class="input-icon">
              <span class="input-icon-addon">
                <i class="ti ti-search"></i>
              </span>
              <input type="text" class="form-control" placeholder="Search signups..." style="padding-right: 60px;">
              <span class="position-absolute end-0 top-50 translate-middle-y me-3">
                <kbd class="small text-muted">ctrl + k</kbd>
              </span>
            </div>
          </div>
        </div>

        <!-- Table -->
        <div class="table-responsive">
          <table class="table table-hover">
            <thead>
              <tr>
                <th style="width: 300px;">Participant</th>
                <th>Activity</th>
                <th>Status</th>
                <th>Pass Type</th>
                <th>Date</th>
                <th style="width: 120px;">Actions</th>
              </tr>
            </thead>
            <tbody>
              {% for signup in recent_signups %}
              <tr>
                <td style="vertical-align: middle;">
                  <div class="d-flex align-items-center">
                    <img src="https://www.gravatar.com/avatar/{{ signup.participant_email|md5 }}?d=identicon&s=48" 
                         class="rounded-circle me-3" width="48" height="48" alt="Avatar">
                    <div>
                      <div class="fw-bold">{{ signup.participant_name }}</div>
                      <div class="text-muted small">{{ signup.participant_email }}</div>
                    </div>
                  </div>
                </td>
                <td style="vertical-align: middle;">{{ signup.activity.name|truncate(30) }}</td>
                <td style="vertical-align: middle;">
                  {% if signup.status == 'confirmed' %}
                  <span class="badge bg-green-lt text-green-lt-fg">
                    <i class="ti ti-check me-1"></i>Confirmed
                  </span>
                  {% elif signup.status == 'pending' %}
                  <span class="badge bg-yellow-lt text-yellow-lt-fg">
                    <i class="ti ti-clock me-1"></i>Pending
                  </span>
                  {% elif signup.status == 'cancelled' %}
                  <span class="badge bg-red-lt text-red-lt-fg">
                    <i class="ti ti-x me-1"></i>Cancelled
                  </span>
                  {% endif %}
                </td>
                <td style="vertical-align: middle;">{{ signup.passport_type.name }}</td>
                <td style="vertical-align: middle;">{{ signup.created_at.strftime('%m/%d/%Y') }}</td>
                <td style="vertical-align: middle;">
                  <div class="dropdown">
                    <button class="btn btn-outline-secondary dropdown-toggle btn-sm" type="button" data-bs-toggle="dropdown">
                      Actions
                    </button>
                    <ul class="dropdown-menu">
                      <li><a class="dropdown-item" href="{{ url_for('signup_detail', signup_id=signup.id) }}">
                        <i class="ti ti-eye me-1"></i>View
                      </a></li>
                      <li><a class="dropdown-item" href="{{ url_for('edit_signup', signup_id=signup.id) }}">
                        <i class="ti ti-edit me-1"></i>Edit
                      </a></li>
                      <li><hr class="dropdown-divider"></li>
                      <li><a class="dropdown-item text-danger" href="#">
                        <i class="ti ti-trash me-1"></i>Delete
                      </a></li>
                    </ul>
                  </div>
                </td>
              </tr>
              {% endfor %}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</div>
```

## 4. Quick Actions Section

**Layout:** Horizontal button group

```html
<div class="row mb-4">
  <div class="col-12">
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Quick Actions</h3>
      </div>
      <div class="card-body">
        <div class="d-flex gap-3 flex-wrap">
          <!-- Buttons from Lines 400-408 -->
          <a href="{{ url_for('create_activity') }}" class="btn btn-primary">
            <i class="ti ti-plus me-1"></i>New Activity
          </a>
          <a href="{{ url_for('bulk_signup') }}" class="btn btn-secondary">
            <i class="ti ti-users me-1"></i>Bulk Signup
          </a>
          <a href="{{ url_for('create_passport_type') }}" class="btn btn-info">
            <i class="ti ti-ticket me-1"></i>New Pass Type
          </a>
          <a href="{{ url_for('export_data') }}" class="btn btn-outline-primary">
            <i class="ti ti-download me-1"></i>Export Data
          </a>
          <a href="{{ url_for('activity_reports') }}" class="btn btn-outline-secondary">
            <i class="ti ti-chart-bar me-1"></i>Reports
          </a>
        </div>
      </div>
    </div>
  </div>
</div>
```

## 5. Status Overview Section

**Layout:** 2-column grid with status badges

```html
<div class="row">
  <div class="col-md-6 mb-4">
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">System Status</h3>
      </div>
      <div class="card-body">
        <div class="d-flex align-items-center justify-content-between mb-3">
          <span>Payment System</span>
          <span class="badge bg-green text-green-fg">
            <i class="ti ti-check me-1"></i>Operational
          </span>
        </div>
        <div class="d-flex align-items-center justify-content-between mb-3">
          <span>Email Notifications</span>
          <span class="badge bg-green text-green-fg">
            <i class="ti ti-check me-1"></i>Operational
          </span>
        </div>
        <div class="d-flex align-items-center justify-content-between mb-3">
          <span>Database</span>
          <span class="badge bg-green text-green-fg">
            <i class="ti ti-check me-1"></i>Operational
          </span>
        </div>
        <div class="d-flex align-items-center justify-content-between">
          <span>AI Chatbot</span>
          <span class="badge bg-yellow text-yellow-fg">
            <i class="ti ti-alert-triangle me-1"></i>Maintenance
          </span>
        </div>
      </div>
    </div>
  </div>
  
  <div class="col-md-6 mb-4">
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Recent Activity Feed</h3>
      </div>
      <div class="card-body">
        <div class="list-group list-group-flush list-group-hoverable">
          {% for log in recent_logs %}
          <div class="list-group-item">
            <div class="row align-items-center">
              <div class="col-auto">
                <span class="status-dot status-dot-animated bg-green d-block"></span>
              </div>
              <div class="col text-truncate">
                <a href="#" class="text-body d-block">{{ log.action }}</a>
                <div class="d-block text-muted text-truncate mt-n1">
                  {{ log.details }} • {{ log.created_at|timeago }}
                </div>
              </div>
            </div>
          </div>
          {% endfor %}
        </div>
      </div>
    </div>
  </div>
</div>
```

## Template Structure

### Complete Dashboard Template
```jinja2
{% extends "base.html" %}

{% block title %}Dashboard - Minipass{% endblock %}

{% block content %}
<div class="page-wrapper">
  <!-- Page Header -->
  <div class="page-header d-print-none">
    <div class="container-xl">
      <div class="row g-2 align-items-center">
        <div class="col">
          <h2 class="page-title">Dashboard</h2>
          <div class="text-muted">
            Welcome back, {{ current_user.name }}. Here's what's happening with your activities.
          </div>
        </div>
        <div class="col-auto ms-auto d-print-none">
          <div class="btn-list">
            <a href="{{ url_for('create_activity') }}" class="btn btn-primary d-none d-md-inline-block">
              <i class="ti ti-plus"></i>
              New Activity
            </a>
            <a href="{{ url_for('create_activity') }}" class="btn btn-primary d-md-none btn-icon" aria-label="New Activity">
              <i class="ti ti-plus"></i>
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Page Body -->
  <div class="page-body">
    <div class="container-xl">
      
      <!-- KPI Cards Row -->
      <div class="row mb-4">
        <!-- Insert KPI cards here as defined above -->
      </div>
      
      <!-- Recent Activities Section -->
      <!-- Insert activities cards section here -->
      
      <!-- Recent Signups Table -->
      <!-- Insert table section here -->
      
      <!-- Quick Actions and Status Row -->
      <div class="row">
        <div class="col-md-8">
          <!-- Quick Actions -->
        </div>
        <div class="col-md-4">
          <!-- Status Overview -->
        </div>
      </div>
      
    </div>
  </div>
</div>
{% endblock %}

{% block scripts %}
<script>
// Dashboard-specific JavaScript
document.addEventListener('DOMContentLoaded', function() {
  // Auto-refresh KPI data every 30 seconds
  setInterval(function() {
    fetch('/api/dashboard/kpis')
      .then(response => response.json())
      .then(data => {
        // Update KPI values without full page refresh
        updateKPICards(data);
      })
      .catch(error => console.error('Error updating KPIs:', error));
  }, 30000);
  
  // Initialize search functionality
  initializeTableSearch();
});

function updateKPICards(data) {
  // Update revenue
  document.querySelector('[data-kpi="revenue"]').textContent = '$' + data.revenue;
  document.querySelector('[data-kpi="revenue-growth"]').innerHTML = 
    data.revenue_growth + '% <i class="ti ti-trending-up"></i>';
  
  // Update other KPIs similarly
}

function initializeTableSearch() {
  const searchInput = document.querySelector('input[placeholder*="Search"]');
  if (searchInput) {
    searchInput.addEventListener('input', function(e) {
      // Implement client-side search filtering
      filterTableRows(e.target.value);
    });
  }
}
</script>
{% endblock %}
```

## Responsive Breakpoints

### Desktop (≥992px)
- KPI Cards: 4 columns
- Activity Cards: 3 columns  
- Table: Full width with all columns
- Quick Actions: Horizontal layout

### Tablet (768px - 991px)
- KPI Cards: 2 columns
- Activity Cards: 2 columns
- Table: Scrollable with condensed columns
- Quick Actions: Wrapped horizontal

### Mobile (≤767px)
- KPI Cards: 1 column
- Activity Cards: 1 column
- Table: Vertical card layout (responsive transformation)
- Quick Actions: Stacked vertical buttons

## Color Scheme (Lines 291-356)

### Brand Colors
- **Primary Blue**: `#007bff` (buttons, links)
- **Success Green**: `.bg-green-lt` (active status)
- **Warning Yellow**: `.bg-yellow-lt` (pending status)
- **Danger Red**: `.bg-red-lt` (error status)
- **Info Blue**: `.bg-blue-lt` (informational badges)

### Badge Colors (Lines 429-586)
- Active: `bg-green-lt text-green-lt-fg`
- Pending: `bg-yellow-lt text-yellow-lt-fg`
- Inactive: `bg-red-lt text-red-lt-fg`
- Featured: `bg-blue text-blue-fg`

## Implementation Notes

1. **Component Reuse**: All components are directly from the style guide with exact class names
2. **Tabler Icons**: Using `ti ti-*` classes for consistent iconography
3. **Bootstrap Grid**: Responsive grid system with proper breakpoints
4. **Card Styling**: Consistent `border-radius: 12px; overflow: hidden;` for modern look
5. **Hover States**: Built-in with `.table-hover` and `.list-group-hoverable`
6. **Accessibility**: Proper ARIA labels, keyboard navigation, and semantic HTML

## Data Requirements

### Flask Route Context
```python
@app.route('/dashboard')
@login_required
def dashboard():
    context = {
        'total_revenue': get_total_revenue(),
        'revenue_growth': get_revenue_growth(),
        'active_passes_count': get_active_passes_count(),
        'passes_growth': get_passes_growth(),
        'total_activities': get_total_activities(),
        'activities_growth': get_activities_growth(),
        'conversion_rate': get_conversion_rate(),
        'conversion_change': get_conversion_change(),
        'recent_activities': get_recent_activities(limit=6),
        'recent_signups': get_recent_signups(limit=10),
        'recent_logs': get_recent_activity_logs(limit=5)
    }
    return render_template('dashboard.html', **context)
```

This wireframe provides a complete, implementable dashboard design using only Tabler.io components from the style guide, ensuring rapid development while maintaining a professional, modern appearance suitable for the Minipass SAAS application.