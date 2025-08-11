# Activity Dashboard Wireframe - Field Operations Tool

## Executive Summary
This wireframe presents a field operations tool designed specifically for use at hockey rinks and sports venues. The dashboard prioritizes speed and simplicity for administrators who need to quickly validate players who arrive without QR codes. This is NOT a data analytics dashboard - it's a rapid check-in tool optimized for cold environments, gloved hands, and time-critical situations.

## Real-World Use Case
**Scenario**: It's game time at the hockey rink. A player arrives to play but forgot their QR code. Other players are waiting. The admin needs to:
1. Quickly search for the player by name
2. Verify they have remaining sessions
3. Check them in with one tap
4. Move on to the next player

## Design Philosophy
- **Search First**: Large, prominent search bar for instant player lookup
- **Speed Optimized**: Minimal clicks, maximum efficiency
- **Field Ready**: Large touch targets for gloved hands, high contrast for poor lighting
- **Essential Data Only**: Just what's needed for check-in decisions
- **Mobile First**: Optimized for phones/tablets used in the field

---

## Desktop Layout (1440px width)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ MINIMAL HEADER                                                             │
│ [Logo] Ligue Hockey Gagnon - Check-In            [High Contrast] [Settings]│
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 🔍 SEARCH BAR (Auto-focused on page load)                                  │
│ ┌─────────────────────────────────────────────────────────────────────┐   │
│ │ 🔍  Search player name...                          Press / to search │   │
│ │     (Large 56px height input for easy targeting)                    │   │
│ └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│ Quick Actions: [+ New Passport] [📷 Scan QR] [📱 Switch to Mobile View]    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ RECENT ACTIVITY (Last 5 check-ins for quick re-access)                     │
│ ┌─────────────────────────────────────────────────────────────────────┐   │
│ │ Just now: ✅ Ken Dresdell checked in (2 sessions left)   [UNDO]     │   │
│ │ 5 min ago: ✅ Marie Leblanc checked in (4 sessions left)            │   │
│ │ 10 min ago: 💰 John Smith marked as paid                            │   │
│ └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ ACTIVE PASSPORTS (8 players with remaining sessions)                       │
│ ┌─────────────────────────────────────────────────────────────────────┐   │
│ │ Player              Sessions    Last Activity    Actions             │   │
│ ├─────────────────────────────────────────────────────────────────────┤   │
│ │ 👤 Ken Dresdell     3/5 left    2 days ago      [CHECK IN] [DETAILS]│   │
│ │ 👤 Marie Leblanc    5/5 left    Never           [CHECK IN] [DETAILS]│   │
│ │ 👤 Bob Wilson       1/5 left    Yesterday       [CHECK IN] [DETAILS]│   │
│ │ 👤 Sarah Jones      4/5 left    3 days ago      [CHECK IN] [DETAILS]│   │
│ │ 👤 Mike Thompson    2/5 left    1 week ago      [CHECK IN] [DETAILS]│   │
│ └─────────────────────────────────────────────────────────────────────┘   │
│ Showing 5 of 8 • [Show All]                                                │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ ⚠️ UNPAID USERS (3 players need payment)                                   │
│ ┌─────────────────────────────────────────────────────────────────────┐   │
│ │ Player              Amount      Overdue         Actions             │   │
│ ├─────────────────────────────────────────────────────────────────────┤   │
│ │ 👤 John Doe         $50         3 days          [MARK PAID] [EMAIL] │   │
│ │ 👤 Jane Smith       $50         1 day           [MARK PAID] [EMAIL] │   │
│ │ 👤 Tom Brown        $50         Due today       [MARK PAID] [EMAIL] │   │
│ └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Mobile Layout (375px width) - PRIMARY DESIGN

```
┌──────────────────────┐
│ STICKY SEARCH        │
│ ┌──────────────────┐ │
│ │🔍 Search player..│ │
│ └──────────────────┘ │
│ [Active (8)][Unpaid(3)]│
└──────────────────────┘

┌──────────────────────┐
│ ACTIVE TAB SELECTED  │
├──────────────────────┤
│ Ken Dresdell         │
│ 3 of 5 left          │
│ Last: 2 days ago     │
│ ┌──────────────────┐ │
│ │   CHECK IN       │ │
│ └──────────────────┘ │
├──────────────────────┤
│ Marie Leblanc        │
│ 5 of 5 left          │
│ Never used           │
│ ┌──────────────────┐ │
│ │   CHECK IN       │ │
│ └──────────────────┘ │
├──────────────────────┤
│ Bob Wilson           │
│ 1 of 5 left ⚠️       │
│ Last: Yesterday      │
│ ┌──────────────────┐ │
│ │   CHECK IN       │ │
│ └──────────────────┘ │
└──────────────────────┘

[Floating Actions Bar]
[📷 Scan] [+ Add] [⚙️]
```

### Mobile - Unpaid Tab
```
┌──────────────────────┐
│ UNPAID TAB SELECTED  │
├──────────────────────┤
│ ⚠️ John Doe          │
│ Owes: $50            │
│ 3 days overdue       │
│ ┌──────────────────┐ │
│ │   MARK PAID      │ │
│ └──────────────────┘ │
├──────────────────────┤
│ ⚠️ Jane Smith        │
│ Owes: $50            │
│ 1 day overdue        │
│ ┌──────────────────┐ │
│ │   MARK PAID      │ │
│ └──────────────────┘ │
└──────────────────────┘
```

---

## Component Specifications

### 1. Search Bar (Primary Component)
```html
<!-- Large Search Input with Keyboard Shortcut -->
<div class="card">
  <div class="card-body p-4">
    <div class="input-icon">
      <span class="input-icon-addon">
        <i class="ti ti-search"></i>
      </span>
      <input type="text" 
             class="form-control form-control-lg" 
             placeholder="Search player name..."
             style="height: 56px; font-size: 18px;"
             autofocus>
      <span class="position-absolute end-0 top-50 translate-middle-y me-3">
        <kbd>/</kbd>
      </span>
    </div>
  </div>
</div>
```

### 2. Active Passports Table (Tabler.io Style)
```html
<!-- Clean Table Design from Style Guide -->
<div class="table-responsive">
  <table class="table table-hover">
    <thead>
      <tr>
        <th style="width: 300px;">Player</th>
        <th>Sessions</th>
        <th>Last Activity</th>
        <th style="width: 200px;">Actions</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td style="vertical-align: middle;">
          <div class="d-flex align-items-center">
            <img src="avatar.jpg" class="rounded-circle me-3" width="48" height="48">
            <div>
              <div class="fw-bold">Ken Dresdell</div>
              <div class="text-muted small">#MP-9e5d4c</div>
            </div>
          </div>
        </td>
        <td style="vertical-align: middle;">
          <div class="fw-bold">3/5 remaining</div>
          <div class="progress" style="height: 6px;">
            <div class="progress-bar bg-primary" style="width: 60%"></div>
          </div>
        </td>
        <td style="vertical-align: middle;">
          <span class="text-muted">2 days ago</span>
        </td>
        <td style="vertical-align: middle;">
          <button class="btn btn-primary btn-lg" style="min-height: 48px;">
            CHECK IN
          </button>
        </td>
      </tr>
    </tbody>
  </table>
</div>
```

### 3. Mobile List Item
```html
<!-- Mobile-Optimized List Item -->
<div class="card mb-3">
  <div class="card-body p-3">
    <div class="d-flex justify-content-between align-items-start mb-2">
      <h4 class="mb-0">Ken Dresdell</h4>
      <span class="badge bg-green">3/5</span>
    </div>
    <p class="text-muted mb-3">Last: 2 days ago</p>
    <button class="btn btn-primary w-100 btn-lg" style="height: 48px;">
      CHECK IN
    </button>
  </div>
</div>
```

### 4. Recent Activity Strip
```html
<!-- Recent Activity for Quick Re-access -->
<div class="alert alert-success d-flex align-items-center">
  <div class="flex-fill">
    <strong>Just now:</strong> Ken Dresdell checked in (2 sessions left)
  </div>
  <button class="btn btn-sm btn-outline-secondary">UNDO</button>
</div>
```

---

## Field-Optimized Features

### 1. Touch Targets
- **Minimum Size**: 48x48px for all interactive elements
- **Button Height**: 56px for primary actions (CHECK IN, MARK PAID)
- **Spacing**: 12px between buttons to prevent mis-taps
- **Mobile**: Full-width buttons for easy thumb access

### 2. High Contrast Mode
```css
/* High Contrast Mode for Poor Lighting */
.high-contrast {
  background: #000;
  color: #fff;
}
.high-contrast .btn-primary {
  background: #0066ff;
  border: 2px solid #fff;
  font-weight: bold;
}
.high-contrast .table {
  border: 2px solid #fff;
}
```

### 3. Keyboard Shortcuts
- `/` - Focus search input
- `Enter` - Check in selected player
- `Esc` - Clear search
- `Tab` - Navigate between players
- `c` - Quick check-in for highlighted player
- `p` - Mark as paid for highlighted player

### 4. Speed Optimizations
- **Auto-focus**: Search input focused on page load
- **Instant Search**: Results appear as you type (no submit needed)
- **Recent Activity**: One-click re-access to recent check-ins
- **Optimistic Updates**: UI updates immediately, sync in background
- **Offline Mode**: Service worker caches player list

---

## Color Scheme (High Visibility)

### Primary Actions
- **Check In Button**: Bright Blue (#0066ff) - High contrast
- **Mark Paid Button**: Bright Green (#00cc44) - Clear success action
- **Warning Badges**: Bright Orange (#ff6600) - Attention grabbing

### Status Indicators
- **Active**: Green text/badge - Player can play
- **Low Sessions**: Orange warning - 1-2 sessions left
- **Unpaid**: Red badge - Payment required
- **Expired**: Gray - No sessions remaining

### Background Colors
- **Normal Mode**: White background, black text
- **High Contrast**: Black background, white text
- **Selected Row**: Light blue highlight (#e3f2fd)

---

## Interaction Patterns

### 1. Search Flow
```javascript
// Instant search with highlighting
searchInput.addEventListener('input', (e) => {
  const query = e.target.value.toLowerCase();
  filterPlayers(query);
  highlightFirstResult();
});

// Keyboard navigation
searchInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    checkInFirstResult();
  }
});
```

### 2. One-Tap Actions
- **CHECK IN**: Single tap, immediate confirmation
- **MARK PAID**: Single tap with success animation
- **UNDO**: Available for 30 seconds after action
- **Audio Feedback**: Optional beep on successful action

### 3. Confirmation Feedback
```javascript
// Visual + Audio confirmation
function confirmCheckIn(player) {
  showSuccessToast(`✅ ${player.name} checked in`);
  if (audioEnabled) playSuccessSound();
  updateRecentActivity(player);
}
```

---

## Mobile-First Considerations

### Touch Optimization
- **Swipe Actions**: Swipe right to check in, left for options
- **Pull to Refresh**: Update player list
- **Sticky Search**: Always accessible at top
- **Tab Toggle**: Easy switch between Active/Unpaid

### Performance
- **Lazy Loading**: Load 20 players at a time
- **Virtual Scrolling**: For lists over 50 players
- **Image Optimization**: 48x48px avatars, lazy loaded
- **Minimal Animations**: Reduce motion for better performance

### Offline Capability
```javascript
// Service Worker for Offline Mode
self.addEventListener('fetch', (event) => {
  if (event.request.url.includes('/api/players')) {
    event.respondWith(
      caches.match(event.request).then((response) => {
        return response || fetch(event.request);
      })
    );
  }
});
```

---

## Implementation Notes

### Required Tabler.io Components
1. **Tables** (table, table-hover, table-responsive)
2. **Forms** (form-control, form-control-lg, input-icon)
3. **Buttons** (btn, btn-primary, btn-lg)
4. **Cards** (card, card-body)
5. **Badges** (badge, bg-green, bg-warning)
6. **Alerts** (alert, alert-success)
7. **Progress** (progress, progress-bar)

### Flask Template Structure
```python
templates/
  ├── base.html
  ├── activity_dashboard_field.html  # New field-optimized design
  └── components/
      ├── search_bar.html
      ├── player_table.html
      └── mobile_player_list.html
```

### API Endpoints (Simplified)
```python
# Minimal endpoints for speed
GET  /api/activity/{id}/active-players  # Players with sessions
GET  /api/activity/{id}/unpaid-players  # Players who owe money
POST /api/player/{id}/check-in         # Quick check-in
POST /api/player/{id}/mark-paid        # Mark as paid
GET  /api/activity/{id}/recent         # Recent activity
```

### JavaScript (Field Operations)
```javascript
// Focus on speed and reliability
document.addEventListener('DOMContentLoaded', () => {
  // Auto-focus search
  document.getElementById('playerSearch').focus();
  
  // Keyboard shortcuts
  initKeyboardShortcuts();
  
  // Load players
  loadActivePlayers();
  
  // Enable offline mode
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js');
  }
});
```

---

## Accessibility Features

### Field Accessibility
- **Large Text**: 18px minimum for readability
- **High Contrast**: Toggle for poor lighting
- **Clear Labels**: Simple, descriptive text
- **Audio Feedback**: Optional for confirmations
- **Error Prevention**: Confirmation for destructive actions

### Keyboard Navigation
- Full keyboard support for non-touch devices
- Tab navigation through all interactive elements
- Clear focus indicators (3px blue border)
- Shortcuts displayed on hover

---

## Performance Metrics

### Target Performance (Field Conditions)
- **Initial Load**: < 1 second
- **Search Response**: < 100ms
- **Check-in Action**: < 200ms
- **Offline Mode**: Full functionality

### Optimization Strategies
1. **Minimal Dependencies**: Only essential JS/CSS
2. **Local Storage**: Cache player list
3. **Progressive Enhancement**: Works without JS
4. **CDN Assets**: Tabler.io from CDN
5. **Compressed Data**: Minimal JSON responses

---

## Testing Checklist

### Field Testing
- [ ] Test with gloves on
- [ ] Test in bright sunlight
- [ ] Test in dim lighting
- [ ] Test with cold fingers
- [ ] Test on various phones/tablets
- [ ] Test offline mode
- [ ] Test with 100+ players

### Functional Testing
- [ ] Search finds players instantly
- [ ] Check-in completes in one tap
- [ ] Mark paid works correctly
- [ ] Recent activity displays
- [ ] Undo function works
- [ ] High contrast mode toggles
- [ ] Audio feedback (if enabled)

### Device Testing
- [ ] iPhone (various sizes)
- [ ] Android phones
- [ ] iPad/Tablets
- [ ] Desktop (backup option)

---

## Future Enhancements

### Phase 2 Features
1. **Voice Search**: "Check in Ken Dresdell"
2. **Facial Recognition**: Camera-based check-in
3. **Team Lists**: Pre-game roster loading
4. **Batch Actions**: Check in multiple players

### Phase 3 Features
1. **Predictive Search**: Learn common players
2. **NFC Support**: Tap phone/card to check in
3. **Watch App**: Check in from smartwatch
4. **Integration**: Sync with team management apps

---

## Conclusion

This wireframe represents a complete paradigm shift from a traditional dashboard to a field operations tool. Every design decision prioritizes speed, simplicity, and reliability in challenging real-world conditions.

**Key Differentiators:**
1. **Search-first interface** - Players found in seconds
2. **One-tap actions** - No multi-step processes
3. **Field-optimized UI** - Works with gloves, in any lighting
4. **Minimal data display** - Only what's needed for decisions
5. **Mobile-first design** - Built for phones/tablets in the field

This is not a dashboard for analyzing data - it's a tool for getting players on the ice quickly and efficiently when they don't have their QR codes.