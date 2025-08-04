# Data Tables & List Views

## Current Table Issues

Based on the dashboard activity feed and other table implementations:
- Basic table styling without enhanced visual hierarchy
- Limited responsive behavior for mobile
- Inconsistent spacing and typography
- Need for better action patterns and status indicators

## Table Design System

### Base Table Component

```css
.data-table {
  width: 100%;
  background: white;
  border: 1px solid var(--mp-gray-200);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.data-table-header {
  padding: 1.5rem;
  border-bottom: 1px solid var(--mp-gray-100);
  background: var(--mp-gray-50);
}

.data-table-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--mp-gray-900);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.data-table-subtitle {
  font-size: 0.875rem;
  color: var(--mp-gray-500);
  margin: 0.25rem 0 0;
}

.data-table-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}
```

### Table Structure

```html
<div class="data-table">
  <!-- Table Header -->
  <div class="data-table-header">
    <div class="d-flex justify-content-between align-items-start">
      <div>
        <h3 class="data-table-title">
          <i class="ti ti-users"></i>
          Recent Signups
        </h3>
        <p class="data-table-subtitle">125 total signups this month</p>
      </div>
      <div class="data-table-actions">
        <button class="btn btn-sm btn-secondary">
          <i class="ti ti-download"></i>
          Export
        </button>
        <button class="btn btn-sm btn-primary">
          <i class="ti ti-plus"></i>
          Add New
        </button>
      </div>
    </div>
  </div>

  <!-- Table Content -->
  <div class="table-responsive">
    <table class="table table-vcenter">
      <thead>
        <tr>
          <th>Name</th>
          <th>Email</th>
          <th>Activity</th>
          <th>Status</th>
          <th>Date</th>
          <th class="w-1"></th>
        </tr>
      </thead>
      <tbody>
        <!-- Table rows here -->
      </tbody>
    </table>
  </div>
</div>
```

### Table Styling

```css
.table {
  margin: 0;
  border-collapse: separate;
  border-spacing: 0;
}

.table th {
  padding: 1rem 1.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--mp-gray-500);
  background: var(--mp-gray-50);
  border-bottom: 1px solid var(--mp-gray-200);
  white-space: nowrap;
  position: sticky;
  top: 0;
  z-index: 10;
}

.table td {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--mp-gray-100);
  vertical-align: middle;
  color: var(--mp-gray-700);
}

.table tbody tr:hover {
  background: var(--mp-gray-50);
}

.table tbody tr:last-child td {
  border-bottom: none;
}
```

## Table Patterns

### Activities List Table

```html
<div class="data-table">
  <div class="data-table-header">
    <div class="d-flex justify-content-between align-items-start">
      <div>
        <h3 class="data-table-title">
          <i class="ti ti-activity"></i>
          Activities Management
        </h3>
        <p class="data-table-subtitle">Manage all activities and events</p>
      </div>
      <div class="data-table-actions">
        <div class="input-group input-group-sm" style="width: 250px;">
          <input type="text" class="form-control" placeholder="Search activities...">
          <button class="btn btn-outline-secondary">
            <i class="ti ti-search"></i>
          </button>
        </div>
        <a href="{{ url_for('create_activity') }}" class="btn btn-sm btn-success">
          <i class="ti ti-plus"></i>
          New Activity
        </a>
      </div>
    </div>
  </div>

  <div class="table-responsive">
    <table class="table table-vcenter">
      <thead>
        <tr>
          <th>Activity</th>
          <th>Status</th>
          <th>Signups</th>
          <th>Passports</th>
          <th>Revenue</th>
          <th>Dates</th>
          <th class="w-1">Actions</th>
        </tr>
      </thead>
      <tbody>
        {% for activity in activities %}
        <tr>
          <td>
            <div class="d-flex align-items-center gap-3">
              {% if activity.image_filename %}
              <img src="{{ url_for('static', filename='uploads/activity_images/' ~ activity.image_filename) }}" 
                   class="avatar avatar-sm rounded" alt="{{ activity.name }}">
              {% else %}
              <div class="avatar avatar-sm rounded bg-primary text-white">
                <i class="ti ti-activity"></i>
              </div>
              {% endif %}
              <div>
                <div class="font-weight-medium">{{ activity.name }}</div>
                <div class="text-muted small">Fee: ${{ "%.2f"|format(activity.fee or 0) }}</div>
              </div>
            </div>
          </td>
          <td>
            <span class="badge badge-status-{{ activity.status|lower }}">
              {{ activity.status }}
            </span>
          </td>
          <td>
            <div class="d-flex align-items-center gap-2">
              <span class="font-weight-medium">{{ activity.total_signups }}</span>
              {% if activity.pending_signups > 0 %}
              <span class="badge badge-warning badge-sm">{{ activity.pending_signups }} pending</span>
              {% endif %}
            </div>
          </td>
          <td>
            <div class="progress" style="height: 6px;">
              <div class="progress-bar bg-success" 
                   style="width: {{ (activity.active_passports / activity.total_passports * 100) if activity.total_passports > 0 else 0 }}%">
              </div>
            </div>
            <small class="text-muted">{{ activity.active_passports }}/{{ activity.total_passports }}</small>
          </td>
          <td>
            <div class="font-weight-medium text-success">${{ "%.2f"|format(activity.paid_amount) }}</div>
            {% if activity.unpaid_amount > 0 %}
            <div class="small text-muted">${{ "%.2f"|format(activity.unpaid_amount) }} pending</div>
            {% endif %}
          </td>
          <td>
            <div class="small">
              <div>{{ activity.signup_start|dateformat('%b %d') }} - {{ activity.signup_end|dateformat('%b %d') }}</div>
              <div class="text-muted">{{ activity.event_date|dateformat('%b %d, %Y') if activity.event_date }}</div>
            </div>
          </td>
          <td>
            <div class="dropdown">
              <button class="btn btn-sm btn-ghost-secondary dropdown-toggle" data-bs-toggle="dropdown">
                <i class="ti ti-dots-vertical"></i>
              </button>
              <div class="dropdown-menu dropdown-menu-end">
                <a class="dropdown-item" href="{{ url_for('activity_dashboard', activity_id=activity.id) }}">
                  <i class="ti ti-eye me-2"></i>View Details
                </a>
                <a class="dropdown-item" href="{{ url_for('edit_activity', activity_id=activity.id) }}">
                  <i class="ti ti-edit me-2"></i>Edit
                </a>
                <div class="dropdown-divider"></div>
                <a class="dropdown-item text-danger" href="#" onclick="confirmDelete({{ activity.id }})">
                  <i class="ti ti-trash me-2"></i>Delete
                </a>
              </div>
            </div>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
```

### Passports List Table

```html
<div class="data-table">
  <div class="data-table-header">
    <div class="d-flex justify-content-between align-items-start">
      <div>
        <h3 class="data-table-title">
          <i class="ti ti-ticket"></i>
          Digital Passports
        </h3>
        <p class="data-table-subtitle">All issued digital passports</p>
      </div>
      <div class="data-table-actions">
        <select class="form-select form-select-sm" style="width: auto;">
          <option>All Activities</option>
          <option>Summer Festival</option>
          <option>Tech Conference</option>
        </select>
        <select class="form-select form-select-sm" style="width: auto;">
          <option>All Status</option>
          <option>Active</option>
          <option>Redeemed</option>
          <option>Expired</option>
        </select>
      </div>
    </div>
  </div>

  <div class="table-responsive">
    <table class="table table-vcenter">
      <thead>
        <tr>
          <th>Passport</th>
          <th>Holder</th>
          <th>Activity</th>
          <th>Status</th>
          <th>Payment</th>
          <th>Created</th>
          <th class="w-1">Actions</th>
        </tr>
      </thead>
      <tbody>
        {% for passport in passports %}
        <tr>
          <td>
            <div class="d-flex align-items-center gap-3">
              <div class="passport-qr-mini">
                <img src="{{ url_for('generate_qr_code', passport_id=passport.id) }}" 
                     alt="QR Code" width="32" height="32">
              </div>
              <div>
                <div class="font-family-monospace small">{{ passport.unique_code }}</div>
                <div class="text-muted small">ID: {{ passport.id }}</div>
              </div>
            </div>
          </td>
          <td>
            <div class="d-flex align-items-center gap-2">
              <div class="avatar avatar-sm">{{ passport.user.first_name[0] }}{{ passport.user.last_name[0] }}</div>
              <div>
                <div class="font-weight-medium">{{ passport.user.first_name }} {{ passport.user.last_name }}</div>
                <div class="text-muted small">{{ passport.user.email }}</div>
              </div>
            </div>
          </td>
          <td>
            <div class="font-weight-medium">{{ passport.activity.name }}</div>
            <div class="text-muted small">{{ passport.activity.location or 'No location' }}</div>
          </td>
          <td>
            <span class="badge badge-passport-{{ passport.status|lower }}">
              {% if passport.status == 'active' %}
              <i class="ti ti-check-circle"></i>
              {% elif passport.status == 'redeemed' %}
              <i class="ti ti-ticket-off"></i>
              {% else %}
              <i class="ti ti-clock"></i>
              {% endif %}
              {{ passport.status|title }}
            </span>
          </td>
          <td>
            {% if passport.payment_status == 'paid' %}
            <span class="text-success font-weight-medium">
              <i class="ti ti-check-circle"></i>
              ${{ "%.2f"|format(passport.amount_paid) }}
            </span>
            {% else %}
            <span class="text-warning font-weight-medium">
              <i class="ti ti-clock"></i>
              ${{ "%.2f"|format(passport.activity.fee) }}
            </span>
            {% endif %}
          </td>
          <td>
            <div class="small">{{ passport.created_at|dateformat('%b %d, %Y') }}</div>
            <div class="text-muted small">{{ passport.created_at|timeformat('%I:%M %p') }}</div>
          </td>
          <td>
            <div class="btn-group btn-group-sm">
              <button class="btn btn-ghost-secondary" 
                      onclick="viewPassport({{ passport.id }})" 
                      title="View Details">
                <i class="ti ti-eye"></i>
              </button>
              <button class="btn btn-ghost-secondary" 
                      onclick="downloadPassport({{ passport.id }})" 
                      title="Download">
                <i class="ti ti-download"></i>
              </button>
              {% if passport.status == 'active' %}
              <button class="btn btn-ghost-danger" 
                      onclick="revokePassport({{ passport.id }})" 
                      title="Revoke">
                <i class="ti ti-x"></i>
              </button>
              {% endif %}
            </div>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
```

## Status Badges & Indicators

### Badge Styling
```css
.badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

/* Activity Status Badges */
.badge-status-active {
  background: var(--mp-success-100);
  color: var(--mp-success);
}

.badge-status-draft {
  background: var(--mp-gray-100);
  color: var(--mp-gray-600);
}

.badge-status-completed {
  background: var(--mp-info-100);
  color: var(--mp-info);
}

.badge-status-cancelled {
  background: var(--mp-error-100);
  color: var(--mp-error);
}

/* Passport Status Badges */
.badge-passport-active {
  background: var(--mp-success-100);
  color: var(--mp-success);
}

.badge-passport-redeemed {
  background: var(--mp-gray-100);
  color: var(--mp-gray-600);
}

.badge-passport-expired {
  background: var(--mp-warning-100);
  color: var(--mp-warning);
}

/* Size Variations */
.badge-sm {
  padding: 0.125rem 0.375rem;
  font-size: 0.625rem;
}

.badge-lg {
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
}
```

## Mobile Responsive Tables

### Mobile Card View
```html
<!-- Desktop Table (hidden on mobile) -->
<div class="table-responsive d-none d-md-block">
  <!-- Standard table markup -->
</div>

<!-- Mobile Card View (visible on mobile only) -->
<div class="d-md-none">
  {% for item in items %}
  <div class="mobile-card">
    <div class="mobile-card-header">
      <div class="d-flex align-items-center gap-3">
        <div class="avatar avatar-sm">{{ item.name[0] }}</div>
        <div class="flex-1">
          <div class="font-weight-medium">{{ item.name }}</div>
          <div class="text-muted small">{{ item.email }}</div>
        </div>
        <span class="badge badge-status-{{ item.status|lower }}">{{ item.status }}</span>
      </div>
    </div>
    
    <div class="mobile-card-body">
      <div class="mobile-card-stat">
        <div class="stat-label">Activity</div>
        <div class="stat-value">{{ item.activity.name }}</div>
      </div>
      <div class="mobile-card-stat">
        <div class="stat-label">Payment</div>
        <div class="stat-value text-success">${{ "%.2f"|format(item.amount) }}</div>
      </div>
      <div class="mobile-card-stat">
        <div class="stat-label">Date</div>
        <div class="stat-value">{{ item.created_at|dateformat('%b %d, %Y') }}</div>
      </div>
    </div>
    
    <div class="mobile-card-actions">
      <button class="btn btn-sm btn-outline-primary">View</button>
      <button class="btn btn-sm btn-outline-secondary">Edit</button>
    </div>
  </div>
  {% endfor %}
</div>
```

### Mobile Card Styling
```css
.mobile-card {
  background: white;
  border: 1px solid var(--mp-gray-200);
  border-radius: 12px;
  margin-bottom: 1rem;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.mobile-card-header {
  padding: 1rem;
  border-bottom: 1px solid var(--mp-gray-100);
  background: var(--mp-gray-50);
}

.mobile-card-body {
  padding: 1rem;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.mobile-card-stat {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.stat-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--mp-gray-500);
}

.stat-value {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--mp-gray-700);
}

.mobile-card-actions {
  padding: 1rem;
  border-top: 1px solid var(--mp-gray-100);
  display: flex;
  gap: 0.75rem;
}

.mobile-card-actions .btn {
  flex: 1;
}
```

## Table Interactions

### Sortable Headers
```css
.table th.sortable {
  cursor: pointer;
  user-select: none;
  position: relative;
  transition: background-color 0.2s ease;
}

.table th.sortable:hover {
  background: var(--mp-gray-100);
}

.table th.sortable::after {
  content: '';
  position: absolute;
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
  width: 0;
  height: 0;
  border-left: 4px solid transparent;
  border-right: 4px solid transparent;
  border-bottom: 4px solid var(--mp-gray-400);
  opacity: 0.5;
}

.table th.sortable.sort-asc::after {
  border-bottom: 4px solid var(--mp-primary-600);
  opacity: 1;
}

.table th.sortable.sort-desc::after {
  border-bottom: none;
  border-top: 4px solid var(--mp-primary-600);
  opacity: 1;
}
```

### Row Selection
```css
.table-row-selectable {
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.table-row-selectable:hover {
  background: var(--mp-primary-50);
}

.table-row-selectable.selected {
  background: var(--mp-primary-100);
  border-left: 4px solid var(--mp-primary-600);
}

.bulk-actions {
  padding: 1rem 1.5rem;
  background: var(--mp-primary-50);
  border-bottom: 1px solid var(--mp-primary-200);
  display: none;
}

.bulk-actions.show {
  display: flex;
  align-items: center;
  justify-content: between;
}
```

## Implementation Priority

### Phase 1: Core Table Structure
1. Enhanced table styling with proper hierarchy
2. Status badges and indicators
3. Basic responsive behavior
4. Action buttons and dropdowns

### Phase 2: Advanced Features
1. Mobile card view implementation
2. Sortable headers with visual feedback
3. Row selection and bulk actions
4. Advanced filtering components

### Phase 3: Interactions & Polish
1. Smooth animations for state changes
2. Loading states for data fetching
3. Empty states with proper messaging
4. Accessibility improvements for screen readers