# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Standard Workflow

1. Understand the Problem First and think hard. Begin by reading the relevant source code and thinking through the problem. Then, write a clear plan in projectplan.md.

 - Always append new planned features to this file — even small ones.
 - Include the date and time for each new feature entry.

2. Write an Action Plan projectplan.md that include a checklist of concrete steps to implement the feature. You will tick off these steps as you complete them.

3. Review the Plan Before Starting. Before writing any code, contact me to review and approve the action plan.

4. Create Pytest unit tests for all new features — including functions, classes, routes, etc. If you modify existing logic, update the related tests accordingly.

 - All tests must live in the /tests directory. do not delete the test files
 - Include at least:
   - One success case
   - One edge case
   - One failure case

5. Execute the Plan. Begin coding based on the approved action plan. Check off each completed action in projectplan.md as you go.

6. Explain Your Changes. After each stage of implementation, write a clear explanation of the changes made and why.

7. Keep it Simple. Prioritize simplicity.
 - Break down tasks into small, manageable changes.
 - Avoid large or complex commits.
 - Each modification should have minimal impact on the overall codebase.

8. Document Revisions. At the end of each feature or task, add a Revision section to projectplan.md summarizing:
 - What was implemented or changed
 - Any key decisions or notes for future work




## Project Overview

Minipass is a mobile-first Activities and Digital Passport Management system built with Flask. It enables organizations and small businesses to easily manage activities, digital passport or tickets, user signups, and payments—all in one place.

Designed for non-technical users, Minipass offers an intuitive interface optimized for mobile devices, allowing users to manage everything on the go. The platform also features an AI-powered chatbot for real-time insights and activity analytics, making it easier to track engagement and make informed decisions.

## Tech Stack

- **Flask** - Python web framework with SQLAlchemy ORM
- **SQLite** - Database (dev: `instance/database.db`, prod: `instance/database_prod.db`)
- **Tabler.io** - UI framework for admin dashboard
- **Stripe** - Payment processing
- **Python** with comprehensive dependencies in `requirements.txt`

## Core Architecture

### Key Files
- `app.py` - Main Flask application with all routes
- `models.py` - Database models (User, Activity, Signup, Passport, etc.)
- `config.py` - Environment-based configuration
- `utils.py` - Utility functions for QR codes, emails, file handling
- `chatbot.py` - AI analytics chatbot (separate Blueprint)

### Database Models
Core business models: User, Activity, Signup, Passport, Expense/Income, Admin, AdminActionLog
Legacy models marked for cleanup: Pass, Redemption, EbankPayment

### Directory Structure
- `templates/` - Jinja2 HTML templates
- `static/` - Assets including Tabler UI, TinyMCE, uploads, email templates
- `instance/` - SQLite database files



## Key Patterns

- **Environment Detection**: Uses `FLASK_ENV` to switch between dev/prod databases
- **UTC Timezone**: All datetime operations use UTC with proper timezone handling
- **Background Jobs**: APScheduler for email automation and scheduled tasks
- **Security**: CSRF protection, bcrypt password hashing, secure file uploads
- **QR Code System**: Generated passes with QR codes for ticket validation
- **Email Templates**: HTML templates with inline CSS processing via premailer

## UI/UX Guidelines

### Typography & Layout Standards

**Section Headers:**
- Use `<h4>` for main section titles (not h5)
- Include consistent icon sizing with `style="font-size: 1.2em;"` for section header icons
- Maintain proper visual hierarchy with adequate spacing

**Examples:**
```html
<!-- Section Header with Icon -->
<h4 class="mb-3">
    <i class="ti ti-passport" style="font-size: 1.2em;"></i> Passport Types
</h4>

<!-- Page Title -->
<div class="page-header d-print-none">
    <div class="container-xl">
        <div class="row g-2 align-items-center">
            <div class="col">
                <h2 class="page-title">
                    <i class="ti ti-activity" style="font-size: 1.3em;"></i> Activity Management
                </h2>
            </div>
        </div>
    </div>
</div>
```

### Badge Styling Standards
Always use light background badges with darker text for optimal readability:

**Status Badges:**
- `badge bg-green-lt text-green` - Paid, Active, Success states
- `badge bg-red-lt text-red` - Unpaid, Inactive, Error states  
- `badge bg-yellow-lt text-yellow` - Pending, Warning states
- `badge bg-blue-lt text-blue` - Informational badges (counts, types)
- `badge bg-gray-lt text-gray` - Neutral categories (activity types, tags)

**Examples:**
```html
<!-- Payment Status -->
<span class="badge bg-green-lt text-green">Paid</span>
<span class="badge bg-red-lt text-red">Unpaid</span>

<!-- Activity Status -->
<span class="badge bg-green-lt text-green">Active</span>
<span class="badge bg-red-lt text-red">Inactive</span>

<!-- Count Badges -->
<span class="badge bg-blue-lt text-blue">All Passports (25)</span>
<span class="badge bg-red-lt text-red">Unpaid (2)</span>
<span class="badge bg-green-lt text-green">Paid (18)</span>
<span class="badge bg-blue-lt text-blue">Active (17)</span>

<!-- Category Badges -->
<span class="badge bg-gray-lt text-gray">Hockey</span>
<span class="badge bg-gray-lt text-gray">Sports</span>
```

### Button Styling Standards
Maintain consistent button styles with proper sizing for all user interactions:

**Action Buttons (Standard Pattern):**
- `btn btn-outline-secondary dropdown-toggle` - ALL action dropdowns (always gray outline)
- `btn btn-primary` - Primary actions (create, submit, save)
- `btn btn-success` - Success actions (approve, mark as paid)
- `btn btn-danger` - Destructive actions (delete, reject)
- `btn btn-secondary` - Secondary actions (cancel, view details)

**Button Sizing:**
- Use standard button sizes (no `btn-sm` unless specifically needed for space constraints)
- Icons in buttons should use standard Tabler icon classes without custom sizing

### Actions Column Standard (MANDATORY for all tables)

**CRITICAL RULE**: In table Actions columns, use ONLY ONE dropdown button - never separate edit buttons.

**Required Pattern for Table Actions:**
```html
<td>
  <div class="dropdown">
    <a href="#" class="btn btn-outline-secondary dropdown-toggle" data-bs-toggle="dropdown">
      Actions
    </a>
    <div class="dropdown-menu">
      <a class="dropdown-item" href="{{ url_for('edit_item', item_id=item.id) }}">
        <i class="ti ti-edit me-2"></i> Edit
      </a>
      <!-- Additional context-specific actions -->
      <a class="dropdown-item" href="#">
        <i class="ti ti-check me-2"></i> Mark as Paid
      </a>
      <a class="dropdown-item" href="#">
        <i class="ti ti-thumb-up me-2"></i> Approve
      </a>
      <div class="dropdown-divider"></div>
      <a class="dropdown-item text-danger" href="#" onclick="return confirm('Delete this item?')">
        <i class="ti ti-trash me-2"></i> Delete
      </a>
    </div>
  </div>
</td>
```

**❌ NEVER DO THIS** (separate buttons):
```html
<!-- WRONG - Do not use separate edit button + actions dropdown -->
<td>
  <a href="#" class="btn btn-primary btn-sm">Edit</a>
  <div class="dropdown">
    <a href="#" class="btn btn-outline-secondary btn-sm dropdown-toggle">Actions</a>
    <!-- ... -->
  </div>
</td>
```

**✅ ALWAYS DO THIS** (single dropdown with Edit as first item):
```html
<!-- CORRECT - Single Actions dropdown with Edit as first option -->
<td>
  <div class="dropdown">
    <a href="#" class="btn btn-outline-secondary dropdown-toggle">Actions</a>
    <div class="dropdown-menu">
      <a class="dropdown-item" href="#"><i class="ti ti-edit me-2"></i> Edit</a>
      <!-- Other actions... -->
    </div>
  </div>
</td>
```

**Action Button Requirements:**
- **Single dropdown only**: Never use separate edit buttons alongside action dropdowns
- **Edit first**: Edit action must always be the first item in the dropdown
- **Standard styling**: Always use `btn btn-outline-secondary dropdown-toggle`
- **Icon spacing**: Use `me-2` for all icons in dropdown items
- **Danger actions**: Use `text-danger` class and place after divider
- **Confirmations**: Add `onclick="return confirm('...')"` for destructive actions

**Examples:**
```html
<!-- Standard Actions Dropdown (ALWAYS use this pattern) -->
<div class="dropdown">
    <a href="#" class="btn btn-outline-secondary dropdown-toggle" data-bs-toggle="dropdown">
        Actions
    </a>
    <div class="dropdown-menu">
        <a class="dropdown-item" href="#">
            <i class="ti ti-edit me-2"></i> Edit
        </a>
        <a class="dropdown-item" href="#">
            <i class="ti ti-eye me-2"></i> View Details
        </a>
        <div class="dropdown-divider"></div>
        <a class="dropdown-item text-danger" href="#">
            <i class="ti ti-trash me-2"></i> Delete
        </a>
    </div>
</div>

<!-- Primary Action Buttons (for page headers) -->
<a href="#" class="btn btn-primary">
    <i class="ti ti-plus me-2"></i> Add New Item
</a>

<!-- Success Actions (for confirmations) -->
<button class="btn btn-success">
    <i class="ti ti-check me-2"></i> Save Changes
</button>
```

### Page Layout Standards

**Standard Page Header Pattern:**
```html
<div class="page-header d-print-none">
    <div class="container-xl">
        <div class="row g-2 align-items-center">
            <div class="col">
                <h2 class="page-title">
                    <i class="ti ti-[icon-name]" style="font-size: 1.3em;"></i> Page Title
                </h2>
            </div>
            <div class="col-auto ms-auto d-print-none">
                <div class="btn-list">
                    <a href="#" class="btn btn-primary">
                        <i class="ti ti-plus me-2"></i> Primary Action
                    </a>
                </div>
            </div>
        </div>
    </div>
</div>
```

**Card Section Headers:**
```html
<div class="card">
    <div class="card-header">
        <h4 class="card-title">
            <i class="ti ti-[icon-name]" style="font-size: 1.2em;"></i> Section Title
        </h4>
        <div class="card-actions">
            <a href="#" class="btn btn-primary">
                <i class="ti ti-plus me-2"></i> Add Item
            </a>
        </div>
    </div>
    <div class="card-body">
        <!-- Content -->
    </div>
</div>
```

### Table Styling Standards

**Standard Table Structure:**
All data tables must follow this consistent pattern for visual uniformity:

```html
<!-- Desktop Table View -->
<div class="card">
  <div class="table-responsive">
    <table class="table table-vcenter card-table">
      <thead>
        <tr>
          <th><input type="checkbox" id="selectAll"></th>
          <th>User</th>
          <!-- Other headers -->
        </tr>
      </thead>
      <tbody>
        <!-- Table rows -->
      </tbody>
    </table>
  </div>
</div>
```

**User Column Pattern (Required for all user tables):**
```html
<td>
  <div class="d-flex align-items-center">
    <span class="avatar avatar-sm me-3" style="background-image: url('https://www.gravatar.com/avatar/{{ (user.email or 'default@example.com')|lower|trim|encode_md5 }}?d=identicon')"></span>
    <div>
      <strong>{{ user.name or 'Anonymous' }}</strong>
      <br>
      <span class="text-muted small">{{ user.email or '-' }}</span>
    </div>
  </div>
</td>
```

**Mobile Card Pattern (for responsive design):**
```html
<div class="mobile-cards">
  <div class="card mb-3">
    <div class="card-body">
      <div class="d-flex align-items-center">
        <span class="avatar avatar-md me-3" style="background-image: url('https://www.gravatar.com/avatar/{{ (user.email or 'default@example.com')|lower|trim|encode_md5 }}?d=identicon')"></span>
        <div>
          <div class="fw-bold">{{ user.name or 'Anonymous' }}</div>
          <div class="text-muted small">{{ user.email or '-' }}</div>
        </div>
      </div>
    </div>
  </div>
</div>
```

**Table Requirements:**
- **Card wrapper**: Always wrap tables in `<div class="card">`
- **Gravatar avatars**: Use for all user columns with `encode_md5` filter
- **Avatar sizing**: `avatar-sm` for desktop tables, `avatar-md` for mobile cards
- **Consistent spacing**: `me-3` for avatar margins, proper alignment with `d-flex align-items-center`
- **Fallback values**: 'Anonymous' for names, '-' for emails, 'default@example.com' for Gravatar generation
- **Hover effects**: Automatic with `table-vcenter card-table` classes

### Consistency Rules
1. **Always use Tabler's standard color classes** - avoid custom CSS overrides
2. **Action buttons are ALWAYS `btn btn-outline-secondary dropdown-toggle`** - no exceptions
3. **Actions columns use SINGLE dropdown only** - never separate edit buttons, Edit must be first menu item
4. **Badges always use light backgrounds with matching darker text** - `bg-[color]-lt text-[color]`
5. **Section headers use h4 with properly sized icons** - `style="font-size: 1.2em;"`
6. **Page titles use h2 with larger icons** - `style="font-size: 1.3em;"`
7. **Tables must use card wrapper and Gravatar avatars** - follow table styling standards above
8. **Maintain semantic meaning** - green = success/paid, red = danger/unpaid, blue = informational
9. **Icon + text patterns in all buttons and dropdowns** - use `me-2` for icon spacing
10. **Follow established patterns** - reference these guidelines for all new implementations

## Business Logic

The system manages digital passes for activities where users can:
1. Sign up for activities with e-bank transfert or Stripe payment integration
2. Receive digital passes with QR codes
3. Have passes validated via QR scanning
4. Receive automated email confirmations and reminders

Financial tracking per activity includes income/expense management with payment reconciliation.

The AI chatbot provides natural language analytics queries against the business data.