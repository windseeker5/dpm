# Activity Header - Final Design Plan (With Image & Revenue Progress)

## Key Requirements
1. **Activity image MUST be included** - it's essential
2. **Progress bar should show revenue progress** (actual revenue / target revenue)
3. **Clean, modern design** without weird gaps
4. **No gray dividers** (except the proper progress bar)

---

## DESKTOP WIREFRAME (1920px width)

### Option A: Classic Split Layout (Recommended)
```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  ┌─────────────────────────────────┬─────────────────────────────┐ │
│  │          LEFT SIDE (60%)         │      RIGHT SIDE (40%)       │ │
│  │                                  │                             │ │
│  │  ACTIVITY • Active 🟢            │    ┌──────────────────┐    │ │
│  │                                  │    │                  │    │ │
│  │  Ligue Hockey Gagnon Image       │    │   Hockey Image   │    │ │
│  │                                  │    │                  │    │ │
│  │  Les games de hockey du lundi,   │    │   Border-radius  │    │ │
│  │  mercredi et vendredi.           │    │   8px            │    │ │
│  │                                  │    │                  │    │ │
│  │  👥 8    ⭐ 4.8    📍 Location    │    └──────────────────┘    │ │
│  │         🔗 signups                │                             │ │
│  │                                  │                             │ │
│  │  Revenue Progress                │                             │ │
│  │  ▓▓▓▓▓▓▓▓▓▓▓▓░░░░░ $3,000/$5,000│                             │ │
│  │  ████████████░░░░░ 60%           │                             │ │
│  │                                  │                             │ │
│  │  [👤][👤][👤][👤] +5              │                             │ │
│  │                                  │                             │ │
│  │  [Edit] [Scan] [Passport]        │                             │ │
│  │                                  │                             │ │
│  └─────────────────────────────────┴─────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

Total Height: 280px
Padding: 24px
Background: white
Border: 1px solid #e5e7eb
```

### Option B: Image as Background Banner
```
┌─────────────────────────────────────────────────────────────────────┐
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Hockey Image Banner                      │   │
│  │                    Height: 120px                           │   │
│  │                    Full width with gradient overlay        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ACTIVITY • Active 🟢                                               │
│  Ligue Hockey Gagnon Image                                         │
│  Les games de hockey du lundi, mercredi et vendredi.              │
│                                                                     │
│  👥 8 users    ⭐ 4.8 rating    📍 Location    🔗 signups           │
│                                                                     │
│  Revenue Progress: $3,000 / $5,000 target                          │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░ 60%                                    │
│                                                                     │
│  [👤][👤][👤][👤] +5    [Edit] [Scan] [Passport]                    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

Total Height: 320px
```

## MOBILE WIREFRAME (390px width)

```
┌──────────────────────┐
│                      │
│  ┌────────────────┐  │
│  │                │  │  <- Image 16:9
│  │  Hockey Image  │  │     Full width
│  │                │  │     Height: 180px
│  └────────────────┘  │
│                      │
│  ACTIVITY • Active 🟢 │
│                      │
│  Ligue Hockey        │
│  Gagnon Image        │
│                      │
│  Les games de hockey │
│  du lundi...         │
│                      │
│  👥 8      ⭐ 4.8     │
│  📍 Loc    🔗 signup  │
│                      │
│  Revenue: $3k/$5k    │
│  ▓▓▓▓▓▓░░░░ 60%     │
│                      │
│  [👤][👤][👤] +5      │
│                      │
│  [    Edit    ]     │
│  [    Scan    ]     │
│  [  Passport  ]     │
│                      │
└──────────────────────┘
```

---

## REVENUE PROGRESS BAR DESIGN

### Visual Design
```
Revenue Progress: $3,000 / $5,000 target        ← Labels above
┌────────────────────────────────────────┐
│▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░│     ← Actual bar
└────────────────────────────────────────┘
                60% Complete                     ← Percentage below
```

### Implementation
```python
# In the view/template
progress_percentage = (activity.actual_revenue / activity.target_revenue) * 100
```

```html
<div class="revenue-progress-container">
  <div class="progress-label">
    <span>Revenue Progress</span>
    <span>${{ activity.actual_revenue|format_currency }} / ${{ activity.target_revenue|format_currency }}</span>
  </div>
  <div class="progress-bar-wrapper">
    <div class="progress-bar-fill" style="width: {{ progress_percentage }}%"></div>
  </div>
  <div class="progress-percentage">{{ progress_percentage|round }}% Complete</div>
</div>
```

### CSS for Progress Bar
```css
.revenue-progress-container {
  margin: 20px 0;
}

.progress-label {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
  color: #6b7280;
}

.progress-bar-wrapper {
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #10b981, #059669);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-percentage {
  margin-top: 4px;
  font-size: 12px;
  color: #9ca3af;
  text-align: right;
}
```

---

## IMAGE INTEGRATION APPROACH

### For Desktop (Option A - Recommended)
1. **Split Layout**: 60% content, 40% image
2. **Image styling**:
   - Border-radius: 8px
   - Object-fit: cover
   - Height: 100% of container
   - No weird gaps or margins

### For Mobile
1. **Stacked Layout**: Image on top
2. **16:9 aspect ratio** for consistency
3. **Full width** with proper padding

### HTML Structure
```html
<div class="activity-header-final">
  <div class="header-layout">
    <div class="content-section">
      <!-- All text content, stats, buttons -->
    </div>
    <div class="image-section">
      <img src="{{ activity.image }}" alt="{{ activity.name }}">
    </div>
  </div>
</div>
```

### CSS for Clean Integration
```css
.header-layout {
  display: flex;
  gap: 32px;
  align-items: center;
}

.content-section {
  flex: 1 1 60%;
}

.image-section {
  flex: 0 0 40%;
  height: 220px;
}

.image-section img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 8px;
}

@media (max-width: 768px) {
  .header-layout {
    flex-direction: column;
  }
  
  .image-section {
    width: 100%;
    height: 180px;
    order: -1; /* Image on top */
  }
}
```

---

## FIXES FOR CURRENT ISSUES

1. **Remove fake progress bar that looks like divider**
   - Current: `<div class="progress-indicator">` with no context
   - New: Proper revenue progress with labels and percentage

2. **Fix image integration**
   - Current: Weird opacity and gaps
   - New: Clean split or banner layout

3. **Remove gray lines from stats**
   - Current: Dividers between stats
   - New: Clean spacing only (gap: 24px)

4. **Fix weird top spacing**
   - Remove unnecessary padding/margin before "ACTIVITY"

---

## IMPLEMENTATION PRIORITY

1. **First**: Implement proper revenue progress bar
2. **Second**: Fix image layout (use Option A split layout)
3. **Third**: Clean up spacing and remove dividers
4. **Fourth**: Test responsive design

## Expected Result

- Clean, modern activity header
- Properly integrated image (not faded or gapped)
- Real revenue progress bar with context
- No gray dividers (except the actual progress bar)
- Professional SaaS appearance like Linear/Notion

---

**Recommendation**: Go with Option A (Split Layout) as it's cleaner and more common in modern SaaS apps.