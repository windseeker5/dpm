# Dashboard Layout Wireframes

## Current Dashboard Issues

- KPI cards use excessive rounded corners (16px) 
- Mobile carousel complexity for KPI cards
- Heavy visual treatment with multiple box shadows
- Inconsistent spacing between sections
- Table design lacks visual hierarchy

## Proposed Dashboard Layout

### Desktop Layout (1200px+)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          NAVIGATION HEADER                                 │
│  [As defined in navigation wireframes]                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CONTAINER-XL (max-width: 1320px, centered)                               │
│                                                                             │
│  ┌─ PAGE HEADER ──────────────────────────────────────────────────────────┐ │
│  │                                                                         │ │
│  │  Overview                                           [+ New Activity]   │ │
│  │  Dashboard                                          btn-primary         │ │
│  │  ─ subtitle ─                                       ─ button ─         │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌─ KPI METRICS ROW ──────────────────────────────────────────────────────┐ │
│  │  [Grid: 4 columns on desktop, 2 on tablet, 1 on mobile]               │ │
│  │                                                                         │ │
│  │  ┌─ REVENUE ────┐  ┌─ PASSPORTS ──┐  ┌─ CREATED ──┐  ┌─ PENDING ───┐  │ │
│  │  │ Revenue      │  │ Active Pass  │  │ Created     │  │ Pending     │  │ │
│  │  │ ──────       │  │ ──────       │  │ ──────      │  │ ──────      │  │ │
│  │  │ $1,245  ↗8%  │  │ 89    ↗12%  │  │ 156   ↗4%  │  │ 23    →0%   │  │ │
│  │  │              │  │              │  │             │  │             │  │ │
│  │  │ [sparkline]  │  │ [sparkline]  │  │ [sparkline] │  │ [sparkline] │  │ │
│  │  └──────────────┘  └──────────────┘  └─────────────┘  └─────────────┘  │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌─ ACTIVE ACTIVITIES SECTION ────────────────────────────────────────────┐ │
│  │                                                                         │ │
│  │  🎯 Your Active Activities                                             │ │  
│  │  ─ section title ─                                                     │ │
│  │                                                                         │ │
│  │  [Grid: 3 columns on desktop, 2 on tablet, 1 on mobile]               │ │
│  │                                                                         │ │
│  │  ┌─ ACTIVITY CARD ─────┐  ┌─ ACTIVITY CARD ─────┐  ┌─ ACTIVITY CARD ─┐ │ │
│  │  │ [Image/Thumbnail]   │  │ [Image/Thumbnail]   │  │ [Image/Thumbnail]│ │ │
│  │  │                     │  │                     │  │                  │ │ │
│  │  │ 🎯 Activity Name    │  │ 🎯 Summer Festival  │  │ 🎯 Workshop     │ │ │
│  │  │    ─ title ─        │  │    ─ title ─        │  │    ─ title ─    │ │ │
│  │  │                     │  │                     │  │                  │ │ │
│  │  │ 👥 12 Pending       │  │ 👥 8 Pending        │  │ 👥 3 Pending    │ │ │
│  │  │ 🎫 45 Active        │  │ 🎫 23 Active        │  │ 🎫 12 Active    │ │ │
│  │  │ 💰 $234.50 Paid     │  │ 💰 $150.00 Paid     │  │ 💰 $89.00 Paid  │ │ │
│  │  │                     │  │                     │  │                  │ │ │
│  │  │ [View Details] ───► │  │ [View Details] ───► │  │ [View Details]►  │ │ │
│  │  └─────────────────────┘  └─────────────────────┘  └──────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌─ RECENT ACTIVITY FEED ──────────────────────────────────────────────────┐ │
│  │                                                                         │ │
│  │  📊 What's happening...                                                │ │
│  │  ─ section title ─                                                     │ │
│  │                                                                         │ │
│  │  ┌─ ACTIVITY TABLE ──────────────────────────────────────────────────┐  │ │
│  │  │ Time     │ Type │        │ Description                            │  │ │
│  │  │ ────     │ ──── │ ────── │ ───────────                            │  │ │
│  │  │ 2:34 PM  │ 🎫   │ Pass   │ New passport created for John Smith    │  │ │
│  │  │ 1:22 PM  │ 💰   │ Pay    │ Payment received: $25.00 for event X   │  │ │
│  │  │ 12:15 PM │ ✅   │ Sign   │ Signup approved: Jane Doe              │  │ │
│  │  │ 11:45 AM │ 📧   │ Email  │ Reminder sent to 12 pending users      │  │ │
│  │  │ 10:30 AM │ 🎫   │ Pass   │ Passport redeemed at Event Hall        │  │ │
│  │  └────────────────────────────────────────────────────────────────────┘  │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Tablet Layout (768px - 1199px)
```
┌─────────────────────────────────────────────────────────────┐
│                     NAVIGATION HEADER                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CONTAINER (responsive padding)                             │
│                                                             │
│  Overview                               [+ Activity]        │
│  Dashboard                              ─ button ─          │
│                                                             │
│  ┌─ KPI METRICS ─────────────────────────────────────────┐  │
│  │  [2x2 Grid on tablet]                                │  │
│  │                                                       │  │
│  │  ┌─ REVENUE ─────┐    ┌─ PASSPORTS ──┐              │  │
│  │  │ $1,245   ↗8%  │    │ 89     ↗12%  │              │  │
│  │  │ [sparkline]   │    │ [sparkline]  │              │  │
│  │  └───────────────┘    └──────────────┘              │  │
│  │                                                       │  │
│  │  ┌─ CREATED ─────┐    ┌─ PENDING ────┐              │  │
│  │  │ 156     ↗4%   │    │ 23     →0%   │              │  │
│  │  │ [sparkline]   │    │ [sparkline]  │              │  │
│  │  └───────────────┘    └──────────────┘              │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  🎯 Your Active Activities                                 │
│                                                             │
│  ┌─ ACTIVITY ─────┐    ┌─ ACTIVITY ─────┐                │
│  │ [2-column grid] │    │ [2-column grid] │                │
│  │ [Same structure │    │ as desktop but  │                │
│  │ as desktop]     │    │ 2 per row]      │                │
│  └─────────────────┘    └─────────────────┘                │
│                                                             │
│  📊 What's happening...                                    │
│  [Activity table - condensed for tablet]                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Mobile Layout (< 768px)
```
┌─────────────────────────────────────────────────────────┐
│                 MOBILE NAVIGATION                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  CONTAINER (mobile padding: 16px)                      │
│                                                         │
│  Overview                            [+ Activity]       │
│  Dashboard                           ─ button ─         │
│  ─ compact header ─                                     │
│                                                         │
│  ┌─ KPI CAROUSEL ──────────────────────────────────────┐ │
│  │  [Single card view with dots indicator]             │ │
│  │                                                      │ │
│  │  ← ┌─ REVENUE ─────────────────┐ →                  │ │
│  │    │ Revenue                   │                     │ │
│  │    │ ──────                    │                     │ │
│  │    │ $1,245              ↗8%   │                     │ │
│  │    │                           │                     │ │
│  │    │ [sparkline chart]         │                     │ │
│  │    └───────────────────────────┘                     │ │
│  │                                                      │ │
│  │  ● ○ ○ ○  [Pagination dots]                         │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                         │
│  🎯 Your Active Activities                             │
│                                                         │
│  ┌─ ACTIVITY STACK ────────────────────────────────────┐ │
│  │  [Single column, full width cards]                  │ │
│  │                                                      │ │
│  │  ┌─ ACTIVITY CARD ─────────────────────────────────┐ │ │
│  │  │ [Thumbnail Image]                                │ │ │
│  │  │                                                  │ │ │
│  │  │ 🎯 Activity Name                                │ │ │
│  │  │                                                  │ │ │
│  │  │ 👥 12 Pending  |  🎫 45 Active                  │ │ │
│  │  │ 💰 $234.50 Paid  |  ⏱️ 5 days left             │ │ │
│  │  │                                                  │ │ │
│  │  │ [View Details ────────────────────────────────►] │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  │                                                      │ │
│  │  [Additional activity cards in stack...]             │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                         │
│  📊 Recent Activity                                    │
│  [Simplified mobile table with key info only]          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Component Specifications

### KPI Cards (Improved Design)
```css
/* Cleaner, more professional KPI cards */
.kpi-card {
  background: white;
  border: 1px solid var(--mp-gray-200);
  border-radius: 12px; /* Reduced from 16px */
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08); /* Subtle shadow */
  transition: all 0.2s ease;
}

.kpi-card:hover {
  border-color: var(--mp-primary-200);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.12);
  transform: translateY(-1px);
}

.kpi-header {
  display: flex;
  justify-content: between;
  align-items: center;
  margin-bottom: 1rem;
}

.kpi-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--mp-gray-500);
}

.kpi-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--mp-gray-900);
  line-height: 1.2;
}

.kpi-trend {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.875rem;
  font-weight: 600;
}

.kpi-trend.positive { color: var(--mp-success); }
.kpi-trend.negative { color: var(--mp-error); }
.kpi-trend.neutral { color: var(--mp-warning); }
```

### Activity Cards (Enhanced)
```css
.activity-card {
  background: white;
  border: 1px solid var(--mp-gray-200);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  transition: all 0.2s ease;
  height: 100%; /* Equal height cards */
}

.activity-card:hover {
  border-color: var(--mp-primary-200);
  box-shadow: 0 6px 20px rgba(37, 99, 235, 0.15);
  transform: translateY(-2px);
}

.activity-card-image {
  height: 160px;
  background-size: cover;
  background-position: center;
  background-color: var(--mp-gray-100);
}

.activity-card-body {
  padding: 1.5rem;
}

.activity-card-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--mp-gray-900);
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.activity-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.activity-stat {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.875rem;
  color: var(--mp-gray-600);
}

.activity-card-footer {
  padding: 0 1.5rem 1.5rem;
  border-top: 1px solid var(--mp-gray-100);
  padding-top: 1rem;
}
```

### Activity Feed Table
```css
.activity-feed {
  background: white;
  border: 1px solid var(--mp-gray-200);
  border-radius: 12px;
  overflow: hidden;
}

.activity-feed-header {
  padding: 1.5rem;
  border-bottom: 1px solid var(--mp-gray-100);
}

.activity-feed-table {
  width: 100%;
}

.activity-feed-table th {
  padding: 1rem 1.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--mp-gray-500);
  background: var(--mp-gray-50);
  border-bottom: 1px solid var(--mp-gray-200);
}

.activity-feed-table td {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--mp-gray-100);
  vertical-align: middle;
}

.activity-feed-table tr:hover {
  background: var(--mp-gray-50);
}
```

## Responsive Behavior

### Breakpoints
- **Desktop**: 1200px+ (4-column KPI grid, 3-column activities)
- **Tablet**: 768px-1199px (2x2 KPI grid, 2-column activities)  
- **Mobile**: <768px (KPI carousel, single-column activities)

### Mobile Optimizations
- **KPI Carousel**: Smooth touch scrolling with pagination dots
- **Activity Cards**: Full-width, optimized spacing
- **Activity Feed**: Simplified table with essential columns only
- **Touch Targets**: Minimum 44px height for all interactive elements

## Implementation Notes

### Key Changes from Current
1. **Reduced border radius**: 12px instead of 16px for more professional look
2. **Simplified shadows**: Lighter, more subtle shadow treatments
3. **Better typography hierarchy**: Clearer font weights and sizes
4. **Improved spacing**: More consistent rhythm throughout
5. **Enhanced hover states**: Subtle animations and visual feedback

### Development Priority
1. **Phase 1**: Update KPI card styling and layout
2. **Phase 2**: Enhance activity card design and grid
3. **Phase 3**: Improve activity feed table design
4. **Phase 4**: Mobile carousel optimization
5. **Phase 5**: Polish animations and interactions