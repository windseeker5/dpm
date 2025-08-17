# Dashboard Wireframe Specification

## Overview
A comprehensive dashboard page that provides activity managers with a real-time overview of their business metrics, activities, and system activity logs. Built using Tabler.io components exclusively for rapid development and consistent UI patterns.

---

## Desktop Layout (≥992px)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            HEADER SECTION                                    │
│                                                                             │
│  Welcome back, [User Name]!                                                │
│  Here's what's happening with your activities today.                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         KPI CARDS SECTION                                    │
│                                                                             │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐             │
│ │ REVENUE     │ │ ACTIVE      │ │ PASSPORTS   │ │ PENDING     │             │
│ │ Last 7 days▼│ │ PASSPORTS   │ │ CREATED     │ │ SIGN UPS    │             │
│ │             │ │ Last 7 days▼│ │ Last 7 days▼│ │ Last 7 days▼│             │
│ │ $4,300      │ │ 2,986       │ │ 145         │ │ 23          │             │
│ │ 8% ↗        │ │ 4% ↗        │ │ 12% ↗       │ │ 5% ↗        │             │
│ │ ~~~~~~~~~~~ │ │ ||||||||    │ │ ||||||||    │ │ ||||||||    │             │
│ │ Line Chart  │ │ Bar Chart   │ │ Bar Chart   │ │ Bar Chart   │             │
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        ACTIVITIES SECTION                                    │
│                                                                             │
│  Your Activities                                                            │
│                                                                             │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                             │
│ │ Image   │ │ Image   │ │ Image   │ │ Image   │                             │
│ │ [Camp]  │ │ [Work]  │ │ [Event] │ │ [Class] │                             │
│ │         │ │         │ │         │ │         │                             │
│ │ Summer  │ │ Weekend │ │ Music   │ │ Yoga    │                             │
│ │ Camp    │ │ Workshop│ │ Festival│ │ Class   │                             │
│ │ 152d    │ │ 28d     │ │ 7d      │ │ 3d      │                             │
│ │         │ │         │ │         │ │         │                             │
│ │ 55 act  │ │ 42 act  │ │ 18 act  │ │ 12 act  │                             │
│ │ 22 pend │ │ 8 pend  │ │ 5 pend  │ │ 3 pend  │                             │
│ │ 125 cre │ │ 89 cre  │ │ 67 cre  │ │ 45 cre  │                             │
│ │         │ │         │ │         │ │         │                             │
│ │[Manage] │ │[Manage] │ │[Manage] │ │[Manage] │                             │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘                             │
│                                                                             │
│ [More activities continue in additional rows...]                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                       ACTIVITY LOG SECTION                                   │
│                                                                             │
│  What's Happening?                                                          │
│                                                                             │
│ ┌─────────────┬──────────────────────┬─────────────────────────────────────┐ │
│ │ Date/Time   │ Type                 │ Description                         │ │
│ ├─────────────┼──────────────────────┼─────────────────────────────────────┤ │
│ │ 2025-08-10  │ 🎫 Passport Redeemed│ John Doe redeemed summer camp pass  │ │
│ │ 14:32       │                      │                                     │ │
│ ├─────────────┼──────────────────────┼─────────────────────────────────────┤ │
│ │ 2025-08-10  │ ✉️ Email Sent        │ Confirmation email sent to jane@... │ │
│ │ 14:15       │                      │                                     │ │
│ ├─────────────┼──────────────────────┼─────────────────────────────────────┤ │
│ │ 2025-08-10  │ 🆔 Passport Created  │ New passport created for Mike J.    │ │
│ │ 13:45       │                      │                                     │ │
│ └─────────────┴──────────────────────┴─────────────────────────────────────┘ │
│                                                                             │
│ [Showing 1 to 20 of 487 entries]               [1] [2] [3] ... [25]        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Mobile Layout (≤991px)

```
┌─────────────────────────────────────┐
│            HEADER SECTION           │
│                                     │
│ Welcome back, [User Name]!          │
│ Here's what's happening with        │
│ your activities today.              │
│                                     │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│          KPI CARDS SECTION          │
│         (Swipeable Carousel)        │
│                                     │
│ ┌─────────────┐                     │
│ │ REVENUE     │  ●○○○               │
│ │ Last 7 days▼│                     │
│ │             │                     │
│ │ $4,300      │                     │
│ │ 8% ↗        │                     │
│ │ ~~~~~~~~~~~ │  [Swipe indicators] │
│ │ Line Chart  │                     │
│ └─────────────┘                     │
│                                     │
│ [← Swipe to see more cards →]       │
│                                     │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│         ACTIVITIES SECTION          │
│         (Swipeable Carousel)        │
│                                     │
│ Your Activities                     │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ Image                           │ │
│ │ [Summer Camp Photo]             │ │
│ │                                 │ │
│ │ Summer Camp Adventure           │ │
│ │ 152d left                       │ │
│ │                                 │ │
│ │ 55 active  22 pending  125 cre  │ │
│ │                                 │ │
│ │ [Manage Button]                 │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ●○○○  [Swipe indicators]            │
│ [← Swipe to see more activities →]  │
│                                     │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│        ACTIVITY LOG SECTION         │
│                                     │
│ What's Happening?                   │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ 2025-08-10 14:32               │ │
│ │ 🎫 Passport Redeemed            │ │
│ │ John Doe redeemed summer       │ │
│ │ camp pass                       │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ 2025-08-10 14:15               │ │
│ │ ✉️ Email Sent                   │ │
│ │ Confirmation email sent to     │ │
│ │ jane@...                        │ │
│ └─────────────────────────────────┘ │
│                                     │
│ [Show 1-20 of 487] [Load More]      │
│                                     │
└─────────────────────────────────────┘
```

---

## Component Specifications

### 1. Header Section
**Layout:** Simple header with welcome message
**Components Used:** Standard HTML headings with Tabler typography classes
**Implementation:**
```html
<div class="page-header d-print-none">
  <div class="container-xl">
    <div class="row g-2 align-items-center">
      <div class="col">
        <h2 class="page-title mb-2">
          Welcome back, {{ user.name }}!
        </h2>
        <div class="text-muted">
          Here's what's happening with your activities today.
        </div>
      </div>
    </div>
  </div>
</div>
```

### 2. KPI Cards Section
**Reference:** Style Guide lines 601-676 (KPI Cards WITH CHARTS)
**Layout:** 
- Desktop: 4 cards per row (`col-md-3`)
- Mobile: Single card with horizontal scrolling/swipe
**Components Used:** Tabler card with dropdown, SVG charts, trend indicators

**Desktop Implementation:**
```html
<div class="row">
  <div class="col-md-3 mb-3">
    <div class="card" style="border-radius: 12px; overflow: hidden;">
      <div class="card-body">
        <div class="d-flex align-items-center justify-content-between mb-2">
          <div class="text-muted small text-uppercase">REVENUE</div>
          <div class="dropdown">
            <button class="btn btn-sm text-muted dropdown-toggle" type="button" data-bs-toggle="dropdown">
              Last 7 days
            </button>
            <ul class="dropdown-menu">
              <li><a class="dropdown-item" href="#">Last 7 days</a></li>
              <li><a class="dropdown-item" href="#">Last 30 days</a></li>
              <li><a class="dropdown-item" href="#">Last 90 days</a></li>
            </ul>
          </div>
        </div>
        <div class="h2 mb-1">$4,300</div>
        <div class="d-flex align-items-center mb-3">
          <div class="text-success me-2">8% <i class="ti ti-trending-up"></i></div>
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
  <!-- Repeat for other 3 cards with bar charts -->
</div>
```

**Mobile Implementation:**
```html
<!-- Mobile: Horizontal scrolling container -->
<div class="d-md-none">
  <div class="d-flex overflow-auto pb-2" style="scroll-snap-type: x mandatory;">
    <div class="flex-shrink-0 me-3" style="width: 280px; scroll-snap-align: start;">
      <!-- KPI Card content -->
    </div>
    <!-- More cards -->
  </div>
  <!-- Scroll indicators -->
  <div class="text-center mt-2">
    <span class="badge bg-primary me-1"></span>
    <span class="badge bg-light me-1"></span>
    <span class="badge bg-light me-1"></span>
    <span class="badge bg-light"></span>
  </div>
</div>
```

### 3. Activities Section
**Reference:** Style Guide lines 754-814 (Activity Card)
**Layout:**
- Desktop: 4 cards per row (`col-md-3`), multiple rows
- Mobile: Single card with horizontal scrolling/swipe
**Components Used:** Tabler cards with image, badges, buttons

**Desktop Implementation:**
```html
<div class="mb-4">
  <h3 class="mb-3">Your Activities</h3>
  <div class="row">
    <div class="col-md-3 mb-3">
      <div class="card" style="border-radius: 12px; overflow: hidden;">
        <!-- Activity Image -->
        <div class="img-responsive img-responsive-21x9 card-img-top" 
             style="background-image: url('/static/uploads/activity_images/activity_28486c0e82.jpg');">
        </div>
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-center mb-2">
            <h3 class="card-title mb-0">Summer Camp Adventure</h3>
            <small class="text-muted">152d left</small>
          </div>
          <div class="d-flex gap-2 flex-wrap mb-3">
            <span class="badge bg-green-lt">55 active</span>
            <span class="badge bg-yellow-lt">22 pending</span>
            <span class="badge bg-blue-lt">125 created</span>
          </div>
          <button class="btn btn-secondary">Manage</button>
        </div>
      </div>
    </div>
    <!-- Repeat for other activities -->
  </div>
</div>
```

### 4. Activity Log Section
**Reference:** activity_log.html lines 60-111 (EXACT table format)
**Layout:** Full-width responsive table
**Components Used:** Tabler table with icons, exact same styling as activity_log.html

**Implementation:**
```html
<div class="card">
  <div class="card-header">
    <h3 class="card-title">What's Happening?</h3>
  </div>
  <div class="table-responsive">
    <table class="table card-table table-vcenter" id="logTable">
      <thead>
        <tr>
          <th scope="col" class="text-muted">Date/Time</th>
          <th scope="col" class="text-muted">Type</th>
          <th scope="col" class="text-muted">Description</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>2025-08-10 14:32</td>
          <td data-type="Passport Redeemed">
            <i class="ti ti-ticket text-danger"></i>
            Passport Redeemed
          </td>
          <td>John Doe redeemed summer camp pass</td>
        </tr>
        <tr>
          <td>2025-08-10 14:15</td>
          <td data-type="Email Sent">
            <i class="ti ti-mail text-info"></i>
            Email Sent
          </td>
          <td>Confirmation email sent to jane@example.com</td>
        </tr>
        <!-- More rows... -->
      </tbody>
    </table>
  </div>
  
  <!-- Pagination -->
  <div class="card-footer d-flex align-items-center">
    <p class="m-0 text-muted">Showing <span id="showingCount">20</span> of 487</p>
    <ul class="pagination m-0 ms-auto" id="paginationControls">
      <li class="page-item active"><a href="#" class="page-link">1</a></li>
      <li class="page-item"><a href="#" class="page-link">2</a></li>
      <li class="page-item"><a href="#" class="page-link">3</a></li>
    </ul>
  </div>
</div>
```

### Icon Mapping for Activity Log (From activity_log.html lines 75-102)
```javascript
const iconMap = {
  'Passport Redeemed': 'ti ti-ticket text-danger',
  'Email Sent': 'ti ti-mail text-info', 
  'Passport Created': 'ti ti-id text-lime',
  'Interact Payment': 'ti ti-currency-dollar text-success',
  'Marked Paid': 'ti ti-check text-green',
  'Reminder Sent': 'ti ti-bell text-purple',
  'Signup Submitted': 'ti ti-user-plus text-success',
  'Signup Approved': 'ti ti-user-check text-green',
  'Signup Rejected': 'ti ti-user-x text-danger',
  'Signup Cancelled': 'ti ti-user-x text-danger',
  'Activity Created': 'ti ti-target text-orange',
  'Admin Action': 'ti ti-settings text-muted',
  'default': 'ti ti-activity text-muted'
};
```

---

## Responsive Behavior

### Mobile Optimizations
1. **KPI Cards**: Horizontal scrolling with scroll-snap and visual indicators
2. **Activities**: Horizontal scrolling with visual indicators
3. **Activity Log**: Stack table cells vertically or use card-based layout
4. **Typography**: Use responsive font sizes
5. **Spacing**: Reduce padding/margins for mobile

### Breakpoints
- **Mobile**: `< 768px` - Single column, horizontal scrolling
- **Tablet**: `768px - 991px` - 2 cards per row for activities
- **Desktop**: `≥ 992px` - Full 4-card layout

---

## Implementation Notes

### CSS Classes to Use
- **Grid**: `row`, `col-md-3`, `col-md-6`, `col-md-12`
- **Cards**: `card`, `card-body`, `card-header`, `card-footer`
- **Badges**: `badge`, `bg-green-lt`, `bg-yellow-lt`, `bg-blue-lt`
- **Icons**: `ti ti-*` (Tabler Icons)
- **Tables**: `table`, `table-responsive`, `card-table`, `table-vcenter`
- **Buttons**: `btn`, `btn-secondary`, `btn-primary`
- **Text**: `text-muted`, `text-success`, `text-danger`

### JavaScript Requirements
1. **KPI Cards**: Swipe functionality for mobile (using CSS scroll-snap)
2. **Activities**: Swipe functionality for mobile
3. **Activity Log**: Pagination and filtering (reuse from activity_log.html)
4. **Charts**: Simple SVG rendering for KPI sparklines

### Performance Considerations
- Lazy load activity images
- Paginate activity log (show 20-25 entries initially)
- Use CSS scroll-snap for smooth mobile scrolling
- Minimize DOM manipulation for better mobile performance

### Accessibility
- Proper ARIA labels for swipeable content
- Keyboard navigation for all interactive elements  
- Screen reader friendly table structure
- High contrast icons and text

---

## Data Requirements

### KPI Data
```javascript
{
  revenue: { value: 4300, change: 8, trend: 'up', period: '7d' },
  activePassports: { value: 2986, change: 4, trend: 'up', period: '7d' },
  passportsCreated: { value: 145, change: 12, trend: 'up', period: '7d' },
  pendingSignups: { value: 23, change: 5, trend: 'up', period: '7d' }
}
```

### Activities Data
```javascript
{
  id: 1,
  name: "Summer Camp Adventure", 
  image: "/static/uploads/activity_images/activity_28486c0e82.jpg",
  daysLeft: 152,
  stats: {
    active: 55,
    pending: 22, 
    created: 125
  }
}
```

### Activity Log Data
- Reuse existing log structure from activity_log.html
- Show latest 20-25 entries
- Include type-based icon mapping
- Maintain same filtering/pagination functionality

This wireframe specification provides a complete blueprint for implementing a dashboard that matches Tabler.io design patterns while being optimized for both rapid development and excellent user experience across all device types.