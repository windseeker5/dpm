# Wireframe Implementation Guide for Minipass

## Table of Contents
1. [User Flow Diagrams](#user-flow-diagrams)
2. [Dashboard Wireframes](#dashboard-wireframes)
3. [Activities Management](#activities-management)
4. [Digital Pass System](#digital-pass-system)
5. [Payment Tracking](#payment-tracking)
6. [Survey System](#survey-system)
7. [Mobile Responsive Layouts](#mobile-responsive-layouts)
8. [Implementation Notes](#implementation-notes)

## 1. User Flow Diagrams

### Main User Journey
```
┌─────────────┐     ┌──────────────┐     ┌───────────────┐
│   Login     │────▶│   Dashboard  │────▶│   Activities  │
└─────────────┘     └──────────────┘     └───────────────┘
                            │                      │
                            ▼                      ▼
                    ┌──────────────┐     ┌───────────────┐
                    │   Payments   │     │    Signups    │
                    └──────────────┘     └───────────────┘
                            │                      │
                            ▼                      ▼
                    ┌──────────────┐     ┌───────────────┐
                    │   Reports    │     │   Passports   │
                    └──────────────┘     └───────────────┘
```

### Activity Creation Flow
```
Dashboard ──▶ Activities ──▶ Create New ──▶ Basic Info ──▶ Pricing Tiers ──▶ Review ──▶ Publish
                                               │               │              │
                                               ▼               ▼              ▼
                                          Save Draft      Add Images    Email Templates
```

## 2. Dashboard Wireframes

### Desktop Layout (1280px+)
```
┌─────────────────────────────────────────────────────────────────────────┐
│  Navbar                                          User Menu │ Notifications│
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Welcome Back, [User Name]                                 Quick Actions│
│  ┌──────────────────────────────────────────────────────┐  ┌──────────┐│
│  │                  Revenue Overview Chart               │  │ + Create │││
│  │                       (Area Chart)                    │  │ Activity │││
│  └──────────────────────────────────────────────────────┘  ├──────────┤│
│                                                             │ + Add    │││
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────┐  │ Payment  │││
│  │    KPI     │ │    KPI     │ │    KPI     │ │  KPI   │  ├──────────┤│
│  │  Revenue   │ │   Users    │ │  Active    │ │ Survey │  │ Send     │││
│  │  $12,458   │ │    342     │ │     8      │ │  85%   │  │ Reminder │││
│  │   +12.5%   │ │   +8.2%    │ │    +2      │ │  +5%   │  └──────────┘│
│  └────────────┘ └────────────┘ └────────────┘ └────────┘              │
│                                                                         │
│  Recent Activities                           Upcoming Events           │
│  ┌──────────────────────────────┐  ┌──────────────────────────────┐  │
│  │ • New signup: John Doe       │  │ • Hockey Game - Tomorrow    │  │
│  │ • Payment received: $250     │  │ • Yoga Class - Friday       │  │
│  │ • Pass redeemed: Mary Smith  │  │ • Soccer Practice - Sunday  │  │
│  │ • Survey completed: 5 new    │  │                             │  │
│  └──────────────────────────────┘  └──────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Mobile Layout (< 768px)
```
┌─────────────────────┐
│  ☰  MINIPASS    🔔  │
├─────────────────────┤
│ Welcome Back!       │
│                     │
│ ┌─────────────────┐ │
│ │  Revenue Chart  │ │
│ │   (Simplified)  │ │
│ └─────────────────┘ │
│                     │
│ ╔═══════════════╗   │
│ ║ Swipeable KPI ║◄──┤ Carousel
│ ║    Cards      ║   │
│ ╚═══════════════╝   │
│ ●○○○                │
│                     │
│ Recent Activity     │
│ ┌─────────────────┐ │
│ │ • New signup    │ │
│ │ • Payment: $250 │ │
│ │ View All →      │ │
│ └─────────────────┘ │
│                     │
│      [+] FAB        │
├─────────────────────┤
│ Home│Acts│Pass│Pay│●│ Bottom Nav
└─────────────────────┘
```

## 3. Activities Management

### Activity List View - Desktop
```
┌─────────────────────────────────────────────────────────────────────────┐
│  Activities                                    [+ Create] [Filter] [Sort]│
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Search activities...                                    🔍      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  View: [Cards ▼] [List] [Calendar]                          8 Activities│
│                                                                         │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │
│  │   [Image]    │ │   [Image]    │ │   [Image]    │ │   [Image]    │ │
│  │              │ │              │ │              │ │              │ │
│  │ Hockey 2024  │ │ Yoga Classes │ │ Soccer Camp  │ │ Dance Recital│ │
│  │ Active ●     │ │ Active ●     │ │ Upcoming ○   │ │ Completed ✓  │ │
│  │ 45 signups   │ │ 28 signups   │ │ 12 signups   │ │ 62 signups   │ │
│  │ $2,250       │ │ $840         │ │ $360         │ │ $3,100       │ │
│  │              │ │              │ │              │ │              │ │
│  │ [View] [Edit]│ │ [View] [Edit]│ │ [View] [Edit]│ │ [View] [Edit]│ │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### Activity Detail View - Mobile
```
┌─────────────────────┐
│ ← Hockey Season 2024│
├─────────────────────┤
│    [Hero Image]     │
│                     │
│ ┌─────────────────┐ │
│ │ Active ● Edit ⚙ │ │
│ └─────────────────┘ │
│                     │
│ Overview            │
│ ┌─────────────────┐ │
│ │ 45 Participants │ │
│ │ $2,250 Revenue  │ │
│ │ 8/12 Sessions   │ │
│ └─────────────────┘ │
│                     │
│ Quick Stats         │
│ ┌─────────────────┐ │
│ │ [Mini Chart]    │ │
│ └─────────────────┘ │
│                     │
│ Actions             │
│ [View Signups]      │
│ [Manage Passes]     │
│ [Send Update]       │
│ [Export Report]     │
└─────────────────────┘
```

### Activity Creation Wizard
```
Step 1: Basic Information
┌─────────────────────────────────────────────────────────────────────────┐
│  Create New Activity                                           Step 1 of 4│
│  ━━━━━━━━━━━━━━━━━━━━━━━━                                     25%      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Activity Name *                                                       │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │ Enter activity name...                                       │     │
│  └──────────────────────────────────────────────────────────────┘     │
│                                                                         │
│  Activity Type                        Start Date                       │
│  ┌────────────────────┐              ┌────────────────────┐          │
│  │ Select type...    ▼│              │ 📅 Select date     │          │
│  └────────────────────┘              └────────────────────┘          │
│                                                                         │
│  Description                                                           │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │ Describe your activity...                                   │     │
│  │                                                              │     │
│  │                                                              │     │
│  └──────────────────────────────────────────────────────────────┘     │
│                                                                         │
│  Upload Image                                                          │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │     📷 Drag and drop or click to upload                     │     │
│  └──────────────────────────────────────────────────────────────┘     │
│                                                                         │
│                                              [Cancel] [Save Draft] [Next →]│
└─────────────────────────────────────────────────────────────────────────┘
```

## 4. Digital Pass System

### Pass Gallery View
```
┌─────────────────────────────────────────────────────────────────────────┐
│  Digital Passes                                         [+ Create] [Scan]│
├─────────────────────────────────────────────────────────────────────────┤
│  Filter: [All ▼] [Active] [Expired] [Redeemed]              Search: [__]│
│                                                                         │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐             │
│  │    QR     │ │    QR     │ │    QR     │ │    QR     │             │
│  │   Code    │ │   Code    │ │   Code    │ │   Code    │             │
│  │           │ │           │ │           │ │           │             │
│  │ John Doe  │ │ Jane Smith│ │ Bob Wilson│ │ Alice Lee │             │
│  │ Hockey    │ │ Yoga      │ │ Soccer    │ │ Dance     │             │
│  │ 4/8 Used  │ │ 2/4 Used  │ │ Unlimited │ │ Expired   │             │
│  │           │ │           │ │           │ │           │             │
│  │ [View]    │ │ [View]    │ │ [View]    │ │ [View]    │             │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘             │
└─────────────────────────────────────────────────────────────────────────┘
```

### Pass Detail - Mobile
```
┌─────────────────────┐
│ ← Pass Details      │
├─────────────────────┤
│                     │
│   ┌─────────────┐   │
│   │             │   │
│   │   QR CODE   │   │
│   │             │   │
│   │   [Large]   │   │
│   └─────────────┘   │
│                     │
│   PASS-XXXX-YYYY    │
│                     │
│ ┌─────────────────┐ │
│ │ John Doe        │ │
│ │ john@email.com  │ │
│ │ (555) 123-4567  │ │
│ └─────────────────┘ │
│                     │
│ Activity: Hockey    │
│ Status: Active ●    │
│ Sessions: 4/8       │
│ Valid Until: Dec 31 │
│                     │
│ Recent Redemptions  │
│ ┌─────────────────┐ │
│ │ Nov 15 - Game 4 │ │
│ │ Nov 8 - Game 3  │ │
│ │ Nov 1 - Game 2  │ │
│ └─────────────────┘ │
│                     │
│ [Share] [Edit] [⋮]  │
└─────────────────────┘
```

### QR Scanner Interface
```
┌─────────────────────┐
│ × Scan QR Code      │
├─────────────────────┤
│                     │
│  ┌───────────────┐  │
│  │               │  │
│  │    Camera     │  │
│  │     View      │  │
│  │               │  │
│  │   [━━━━━━]    │  │ Scanner Frame
│  │               │  │
│  └───────────────┘  │
│                     │
│ Point at QR code    │
│                     │
│ ──── OR ────        │
│                     │
│ Enter Code Manually │
│ ┌───────────────┐   │
│ │ PASS-____-____|   │
│ └───────────────┘   │
│                     │
│    [Verify Code]    │
└─────────────────────┘
```

## 5. Payment Tracking

### Payment Dashboard
```
┌─────────────────────────────────────────────────────────────────────────┐
│  Payment Management                                    [+ Add] [Export] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Revenue Overview                                      Period: [Month ▼]│
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │                     Revenue & Expense Chart                   │     │
│  │                         (Dual Axis)                           │     │
│  └──────────────────────────────────────────────────────────────┘     │
│                                                                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                │
│  │ Revenue  │ │ Expenses │ │  Profit  │ │ Pending  │                │
│  │ $12,458  │ │  $3,240  │ │  $9,218  │ │  $1,450  │                │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘                │
│                                                                         │
│  Recent Transactions                                    [View All →]   │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │ Date       │ User         │ Activity    │ Amount  │ Status  │     │
│  ├──────────────────────────────────────────────────────────────┤     │
│  │ Nov 20     │ John Doe     │ Hockey      │ $250    │ Paid ✓  │     │
│  │ Nov 19     │ Jane Smith   │ Yoga        │ $120    │ Pending │     │
│  │ Nov 18     │ Bob Wilson   │ Soccer      │ $180    │ Paid ✓  │     │
│  └──────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────┘
```

### Add Payment Form - Mobile
```
┌─────────────────────┐
│ ← Add Payment       │
├─────────────────────┤
│                     │
│ Select User         │
│ ┌─────────────────┐ │
│ │ Search user... ▼│ │
│ └─────────────────┘ │
│                     │
│ Activity            │
│ ┌─────────────────┐ │
│ │ Select...     ▼│ │
│ └─────────────────┘ │
│                     │
│ Amount              │
│ ┌─────────────────┐ │
│ │ $0.00          │ │
│ └─────────────────┘ │
│                     │
│ Payment Method      │
│ ○ Cash              │
│ ● E-Transfer        │
│ ○ Credit Card       │
│ ○ Other             │
│                     │
│ Notes (Optional)    │
│ ┌─────────────────┐ │
│ │                 │ │
│ └─────────────────┘ │
│                     │
│ [Cancel] [Save]     │
└─────────────────────┘
```

## 6. Survey System

### Survey Templates Gallery
```
┌─────────────────────────────────────────────────────────────────────────┐
│  Survey Templates                                    [+ Create Template]│
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐             │
│  │           │ │           │ │           │ │           │             │
│  │    📋     │ │    ⭐     │ │    💬     │ │    📊     │             │
│  │           │ │           │ │           │ │           │             │
│  │ Activity  │ │   User    │ │  Custom   │ │   Post    │             │
│  │ Feedback  │ │   Rating  │ │  Survey   │ │   Event   │             │
│  │           │ │           │ │           │ │           │             │
│  │ 5 questions│ 3 questions│ Variable   │ 8 questions│             │
│  │           │ │           │ │           │ │           │             │
│  │ [Use] [Edit]│[Use] [Edit]│[Use] [Edit]│[Use] [Edit]│             │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘             │
└─────────────────────────────────────────────────────────────────────────┘
```

### Survey Builder - Desktop
```
┌─────────────────────────────────────────────────────────────────────────┐
│  Survey Builder: Customer Satisfaction                    [Preview] [Save]│
├─────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────┐     ┌──────────────────────────────────┐   │
│  │ Question Types         │     │ Survey Canvas                    │   │
│  │                        │     │                                  │   │
│  │ [+] Text Input         │     │ 1. How would you rate...?       │   │
│  │ [+] Multiple Choice    │     │    ┌─────────────────────┐      │   │
│  │ [+] Rating Scale       │────▶│    │ ⭐⭐⭐⭐⭐            │      │   │
│  │ [+] Yes/No             │     │    └─────────────────────┘      │   │
│  │ [+] Long Text          │     │                                  │   │
│  │ [+] Date Picker        │     │ 2. What did you enjoy most?     │   │
│  │ [+] File Upload        │     │    ┌─────────────────────┐      │   │
│  │                        │     │    │ Type your answer... │      │   │
│  │ Survey Settings        │     │    └─────────────────────┘      │   │
│  │ ┌──────────────┐       │     │                                  │   │
│  │ │ ☑ Required   │       │     │ [+ Add Question]                 │   │
│  │ │ ☑ Anonymous  │       │     │                                  │   │
│  │ └──────────────┘       │     └──────────────────────────────────┘   │
│  └────────────────────────┘                                             │
└─────────────────────────────────────────────────────────────────────────┘
```

### Survey Response View - Mobile
```
┌─────────────────────┐
│ Hockey Feedback     │
├─────────────────────┤
│ Question 1 of 5     │
│ ━━━━━━━━━           │
│                     │
│ How satisfied are   │
│ you with the hockey │
│ season?             │
│                     │
│   😞  😐  😊  😄  🤩   │
│                     │
│ ┌─────────────────┐ │
│ │     [Next →]    │ │
│ └─────────────────┘ │
│                     │
│ Skip this question  │
└─────────────────────┘
```

## 7. Mobile Responsive Layouts

### Responsive Breakpoints
```
Mobile:     320px - 767px    (Single column, stacked layout)
Tablet:     768px - 1023px   (Two column layout)
Desktop:    1024px - 1279px  (Multi-column with sidebar)
Wide:       1280px+          (Full featured layout)
```

### Mobile Navigation Pattern
```
┌─────────────────────┐
│  Status Bar         │
├─────────────────────┤
│  App Header         │ Fixed
├─────────────────────┤
│                     │
│                     │
│   Scrollable        │ Scrollable
│    Content          │ Content
│     Area            │
│                     │
│                     │
├─────────────────────┤
│  Bottom Navigation  │ Fixed
└─────────────────────┘
```

### Touch Gesture Support
- **Swipe Left/Right**: Navigate between tabs or carousel items
- **Pull to Refresh**: Update data on lists
- **Long Press**: Show context menu
- **Pinch to Zoom**: View images and charts
- **Swipe to Delete**: Remove items with confirmation

## 8. Implementation Notes

### Flask Template Structure
```
templates/
├── base_redesign.html          # New base template
├── layouts/
│   ├── dashboard_layout.html   # Dashboard specific layout
│   └── form_layout.html        # Form wizard layout
├── components/
│   ├── navbar.html             # Navigation component
│   ├── kpi_card.html           # KPI card component
│   ├── activity_card.html      # Activity card component
│   └── mobile_nav.html         # Mobile bottom nav
└── pages/
    ├── dashboard.html          # Dashboard page
    ├── activities/
    │   ├── list.html          # Activity list
    │   ├── detail.html        # Activity detail
    │   └── create.html        # Activity creation
    └── payments/
        ├── overview.html       # Payment dashboard
        └── add.html           # Add payment form
```

### CSS Architecture
```css
/* Component-based structure */
.minipass-dashboard { }
.minipass-dashboard__header { }
.minipass-dashboard__kpi { }
.minipass-dashboard__chart { }

/* State modifiers */
.minipass-card--active { }
.minipass-card--disabled { }
.minipass-card--loading { }

/* Responsive utilities */
@media (max-width: 768px) {
  .minipass-hide-mobile { display: none; }
  .minipass-show-mobile { display: block; }
}
```

### JavaScript Enhancements
```javascript
// Progressive enhancement approach
if ('IntersectionObserver' in window) {
  // Lazy load images
}

if ('serviceWorker' in navigator) {
  // Register service worker for PWA
}

// Touch gesture support
if ('ontouchstart' in window) {
  // Enable swipe gestures
}
```

### Accessibility Checklist
- [ ] All images have alt text
- [ ] Form inputs have labels
- [ ] Color contrast meets WCAG AA
- [ ] Keyboard navigation works
- [ ] Focus states are visible
- [ ] ARIA labels where needed
- [ ] Semantic HTML structure
- [ ] Screen reader tested

### Performance Optimization
- Lazy load images below the fold
- Minify CSS and JavaScript
- Enable gzip compression
- Use CSS sprites for icons
- Implement virtual scrolling for long lists
- Cache static assets
- Optimize database queries

### Testing Requirements
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- iOS Safari
- Chrome Android
- Screen sizes: 320px to 1920px

## Conclusion

These wireframes provide a comprehensive blueprint for implementing the Minipass UI redesign. Each layout has been carefully designed to:

1. **Simplify user workflows** with clear navigation and actions
2. **Enhance mobile experience** with touch-optimized interfaces
3. **Maintain consistency** across all screens and components
4. **Respect the style guide** while introducing modern improvements
5. **Support rapid development** using Tabler.io components

The implementation should proceed in phases, starting with the dashboard and core screens, then expanding to feature-specific interfaces. All designs are mobile-first and should be tested thoroughly across devices before deployment.