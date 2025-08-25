# Clean Modern Activity Header - Better Design

## Problems with Current Design:
1. **Image has white gaps/margins** - not integrated at all
2. **Card is too tall** - needs to be 40% shorter
3. **Gray dividers still showing** between stats
4. **Ugly gradient line** at top (blue to pink)
5. **Image looks like a separate box** inside the card

## Proposed Solution: Clean Integrated Design

### Option 1: Background Image with Overlay (Most Modern)
```
┌────────────────────────────────────────────────┐
│ [Hockey image as subtle background @ 20% opacity]
│                                                 │
│  ACTIVITY • Active 🟢                           │
│                                                 │
│  Ligue Hockey Gagnon Image                     │
│  Les games de hockey du lundi...               │
│                                                 │
│  👥 8    ⭐ 4.8    📍 Location    🔗 signups    │
│                                                 │
│  [Edit] [Scan] [Passport]                      │
└────────────────────────────────────────────────┘
```
- Height: 280px max (40% reduction)
- Image as subtle background
- All content overlaid
- Clean, modern, integrated

### Option 2: Compact Side-by-Side (Clean)
```
┌────────────────────────────────────────────────┐
│ ACTIVITY • Active 🟢        │   [Small circular │
│ Ligue Hockey Gagnon         │    hockey image  │
│ Les games de hockey...      │    200x200px]    │
│ 👥 8  ⭐ 4.8  📍 Loc         │                  │
│ [Edit] [Scan] [Passport]    │                  │
└────────────────────────────────────────────────┘
```
- Height: 200px (very compact)
- Small circular image
- Clean layout

### Option 3: Image Behind Text (Apple Style)
```
┌────────────────────────────────────────────────┐
│     [Blurred hockey image background]          │
│     with white overlay for text readability    │
│                                                 │
│     ACTIVITY • Active 🟢                        │
│     Ligue Hockey Gagnon Image                  │
│     Les games de hockey...                     │
│     👥 8    ⭐ 4.8    📍 Location               │
│     [Edit] [Scan] [Passport]                   │
└────────────────────────────────────────────────┘
```
- Height: 300px
- Blurred background image
- White semi-transparent overlay
- Text on top

## Which Design to Implement?

**I recommend Option 1** - Background image with low opacity:
- Most modern and clean
- No gaps or margins
- Truly integrated
- Compact height
- Used by: GitHub, Vercel, modern dashboards

## Implementation Details for Option 1:

### CSS Changes:
```css
.activity-header-modern {
  height: 280px; /* 40% reduction */
  position: relative;
  background: white;
  overflow: hidden;
}

/* Image as background, not a separate element */
.activity-header-modern::before {
  content: '';
  position: absolute;
  top: 0;
  right: -20%;
  bottom: 0;
  width: 70%;
  background-image: url(image);
  background-size: cover;
  background-position: center;
  opacity: 0.15; /* Very subtle */
  mask-image: linear-gradient(to left, black, transparent);
}

/* Remove all borders from stats */
.stat-item {
  border: none !important;
  padding: 0 !important;
}

/* Remove gradient line at top */
.page-wrapper::before {
  display: none !important;
}
```

This will create a MUCH cleaner, more integrated design without gaps, excessive height, or ugly gradients.