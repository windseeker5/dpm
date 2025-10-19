# Header Gradient Redesign Plan V4 - WITH DETAILED WIREFRAME

**Created**: October 19, 2025
**Status**: Ready for Implementation
**Source**: User's mockup2.png + explicit requirements

---

## 🎯 THE CORE PROBLEM:

The gradient header was INSIDE `.minipass-main` so it only covered the main section, NOT the full page width.

**SOLUTION**: Put the gradient header OUTSIDE everything, fixed at the top, spanning the entire viewport width.

---

## 📐 DETAILED WIREFRAME - DESKTOP VIEW:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  GRADIENT HEADER - FIXED AT TOP (position: fixed, top: 0, width: 100vw)       │
│  Height: 60px                                                                   │
│  ┌──────────────────────┬─────────────────────────────────────┬──────────────┐ │
│  │  WHITE MINIPASS LOGO │     "FONDATION LHGI"                │   AVATAR     │ │
│  │  (45px height)       │     (centered, white, 26px)         │  (dropdown)  │ │
│  │  Left: 260px area    │     Main area (flex: 1)             │  Right side  │ │
│  └──────────────────────┴─────────────────────────────────────┴──────────────┘ │
│  └─────────── Very Subtle Wave (30px) ─────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────┘
                                 ↑
                            FIXED AT TOP
                         (z-index: 9999)
                              ↓

┌─────────────────────────────────────────────────────────────────────────────────┐
│  PAGE CONTENT - padding-top: 90px (to clear fixed header)                      │
│  ┌─────────────────────┬─────────────────────────────────────────────────────┐ │
│  │  SIDEBAR            │  MAIN CONTENT AREA                                  │ │
│  │  (FIXED)            │  (SCROLLABLE)                                       │ │
│  │  width: 260px       │  overflow-y: auto                                   │ │
│  │  position: fixed    │  padding-top: 90px                                  │ │
│  │  padding-top: 90px  │                                                     │ │
│  │                     │  ┌───────────────────────────────────────────────┐ │ │
│  │  ┌─────────────┐    │  │  "Welcome back, Ken!"                         │ │ │
│  │  │  minipass   │    │  │  KPI Cards (Revenue, Passports, etc.)         │ │ │
│  │  │  logo       │    │  │                                                 │ │ │
│  │  └─────────────┘    │  │  Your Active Activities                        │ │ │
│  │                     │  │  ┌──────┐ ┌──────┐ ┌──────┐                   │ │ │
│  │  ☐ Dashboard        │  │  │ gi   │ │ Golf │ │ Surf │                   │ │ │
│  │  ☐ Activities       │  │  │ Logo │ │ img  │ │ img  │                   │ │ │
│  │  ☐ Signups          │  │  └──────┘ └──────┘ └──────┘                   │ │ │
│  │  ☐ Passports  (27)  │  │                                                 │ │ │
│  │  ☐ Surveys          │  │  Recent events                                 │ │ │
│  │  ☐ Reports >        │  │  [Table of events]                             │ │ │
│  │  ☐ Settings >       │  │                                                 │ │ │
│  │                     │  │  Footer: © 2025 minipass.me                    │ │ │
│  │                     │  └───────────────────────────────────────────────┘ │ │
│  │                     │         ↑                                           │ │
│  │  (STAYS FIXED)      │    THIS SCROLLS                                    │ │
│  │                     │         ↓                                           │ │
│  └─────────────────────┴─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔍 KEY LAYOUT DETAILS:

### GRADIENT HEADER (Fixed at Top)
- **Position**: `fixed`, `top: 0`, `left: 0`, `right: 0`
- **Width**: `100vw` (full viewport width)
- **Height**: `60px` (thin strip)
- **Z-index**: `9999` (above everything)
- **Background**: Stripe-inspired gradient (pink → purple → blue → orange)

**Contains 3 sections:**

1. **LEFT (260px width)**: White minipass logo
   - Logo: 45px height
   - Centered in the 260px area (matches sidebar width)

2. **CENTER (flex: 1)**: "FONDATION LHGI"
   - Font: Anton, 26px
   - Color: White
   - Centered in the main content area

3. **RIGHT**: User avatar + dropdown
   - Same as current implementation
   - Padding-right: 2rem

**Bottom**: Very subtle wave (30px height) with matching gradient

---

### SIDEBAR (Fixed, NOT scrollable)
- **Position**: `fixed`
- **Width**: `260px`
- **Height**: `100vh`
- **Padding-top**: `90px` (to clear the fixed header)
- **Background**: White
- **Contains**: Logo + navigation menu (Dashboard, Activities, etc.)
- **Scrolling**: NO - sidebar stays fixed

---

### MAIN CONTENT AREA (Scrollable)
- **Position**: `relative`
- **Margin-left**: `260px` (to clear sidebar)
- **Padding-top**: `90px` (to clear fixed header: 60px header + 30px wave)
- **Overflow-y**: `auto` (scrollable)
- **Contains**: Dashboard content, KPI cards, activities, footer
- **Scrolling**: YES - this is the only part that scrolls

---

## 💻 HTML STRUCTURE:

```html
<body>
  <!-- GRADIENT HEADER - FIXED AT TOP (OUTSIDE everything) -->
  <div class="gradient-header-fixed">
    <div class="gradient-header-content">
      <!-- LEFT: Logo in 260px area -->
      <div class="gradient-header-left">
        <a href="/dashboard">
          <img src="minipass_logo_white.png" class="gradient-logo" />
        </a>
      </div>

      <!-- CENTER: Org name -->
      <div class="gradient-header-center">
        <h1 class="gradient-org-name">Fondation LHGI</h1>
      </div>

      <!-- RIGHT: Avatar -->
      <div class="gradient-header-right">
        <div class="dropdown">
          <a href="#" data-bs-toggle="dropdown">
            <span class="avatar avatar-sm"></span>
          </a>
          <!-- dropdown menu -->
        </div>
      </div>
    </div>

    <!-- Wave at bottom -->
    <div class="gradient-wave">
      <svg>...</svg>
    </div>
  </div>

  <!-- APP CONTAINER (with padding-top) -->
  <div class="minipass-app">
    <!-- SIDEBAR (fixed) -->
    <nav class="minipass-sidebar" style="padding-top: 90px;">
      <!-- Sidebar logo (regular minipass logo) -->
      <!-- Navigation menu -->
    </nav>

    <!-- MAIN CONTENT (scrollable) -->
    <div class="minipass-main" style="padding-top: 90px; margin-left: 260px;">
      <main class="minipass-content">
        <!-- Dashboard content -->
        <!-- KPI cards -->
        <!-- Activities -->
        <!-- Footer -->
      </main>
    </div>
  </div>
</body>
```

---

## 🎨 CSS SPECIFICATIONS:

```css
/* GRADIENT HEADER - FIXED AT TOP */
.gradient-header-fixed {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  width: 100vw;
  z-index: 9999;
  background: white; /* fallback */
}

.gradient-header-content {
  width: 100%;
  height: 60px; /* THIN */
  display: flex;
  align-items: center;

  /* Stripe gradient */
  background:
    radial-gradient(circle at 20% 50%, rgba(217, 70, 239, 0.8) 0%, transparent 50%),
    radial-gradient(circle at 80% 50%, rgba(251, 146, 60, 0.8) 0%, transparent 50%),
    linear-gradient(135deg,
      #D946EF 0%,
      #A855F7 20%,
      #3B82F6 40%,
      #60A5FA 60%,
      #FB923C 80%,
      #FDBA74 100%
    );
}

/* LEFT: Logo section */
.gradient-header-left {
  width: 260px; /* Match sidebar width */
  display: flex;
  justify-content: center;
  align-items: center;
  flex-shrink: 0;
}

.gradient-logo {
  height: 45px; /* Small logo */
  width: auto;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
}

/* CENTER: Org name */
.gradient-header-center {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
}

.gradient-org-name {
  font-family: 'Anton', sans-serif;
  font-size: 26px; /* Smaller */
  color: white;
  margin: 0;
  text-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

/* RIGHT: Avatar */
.gradient-header-right {
  padding-right: 2rem;
}

/* Wave */
.gradient-wave {
  width: 100%;
  height: 30px;
  line-height: 0;
}

.gradient-wave svg {
  width: 100%;
  height: 30px;
}

/* SIDEBAR - Add padding-top */
.minipass-sidebar {
  padding-top: 90px !important; /* 60px header + 30px wave */
}

/* MAIN CONTENT - Add padding-top */
.minipass-main {
  padding-top: 90px !important; /* 60px header + 30px wave */
}
```

---

## ✅ IMPLEMENTATION CHECKLIST:

### Step 1: HTML Changes (base.html)
- [ ] Add gradient header HTML at line 395 (BEFORE `<div class="minipass-app">`)
- [ ] Ensure it's OUTSIDE the `.minipass-app` container
- [ ] Include: logo section (260px) + org name (center) + avatar (right)
- [ ] Add wave SVG at bottom of header

### Step 2: CSS Changes (minipass.css)
- [ ] Add `.gradient-header-fixed` styles (fixed, z-index 9999)
- [ ] Add `.gradient-header-content` with Stripe gradient
- [ ] Add left/center/right section styles
- [ ] Add `padding-top: 90px` to `.minipass-sidebar`
- [ ] Add `padding-top: 90px` to `.minipass-main`

### Step 3: Testing
- [ ] Gradient covers FULL page width (sidebar + main)
- [ ] Header stays fixed when scrolling
- [ ] Main content scrolls normally
- [ ] Sidebar stays fixed
- [ ] No white gaps anywhere
- [ ] Logo is 45px, org name is 26px
- [ ] Wave is subtle (30px)

---

## 🎯 SUCCESS CRITERIA:

1. ✅ Gradient header is **FIXED at top** (doesn't scroll)
2. ✅ Header spans **FULL viewport width** (100vw)
3. ✅ Header is **60px tall** (thin strip)
4. ✅ Logo is **45px** in the left 260px area
5. ✅ Org name is **26px**, centered in main area
6. ✅ Avatar unchanged on right
7. ✅ Wave is **30px**, very subtle
8. ✅ Sidebar is **FIXED** with padding-top 90px
9. ✅ Main content **SCROLLS** with padding-top 90px
10. ✅ No white/gray gaps anywhere

---

## 🚫 CRITICAL DON'Ts:

1. ❌ Don't put header inside `.minipass-main`
2. ❌ Don't put header inside `.minipass-app`
3. ❌ Put it BEFORE `.minipass-app` at the body level
4. ❌ Don't forget `position: fixed` and `z-index: 9999`
5. ❌ Don't forget `padding-top: 90px` on sidebar and main

---

**THIS IS THE FINAL, CORRECT WIREFRAME. FOLLOW THIS EXACTLY.**
