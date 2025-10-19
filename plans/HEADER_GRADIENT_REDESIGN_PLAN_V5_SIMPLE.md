# Header Gradient Redesign Plan V5 - SIMPLE & VISUAL

**Created**: October 19, 2025
**Status**: Ready for Implementation
**Source**: User's mockup2.png

---

## 🎯 WHAT THE USER WANTS:

A **thin, elegant gradient strip** fixed at the top of the page that spans the entire viewport width (including sidebar area). Think Stripe.com header style.

---

## 📐 WIREFRAME - DESKTOP VIEW:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  GRADIENT HEADER - FIXED AT TOP (80px height)                                  │
│  Full viewport width (covers sidebar + main area)                              │
│  ┌──────────────────────┬─────────────────────────────────────┬──────────────┐ │
│  │  WHITE MINIPASS LOGO │     "FONDATION LHGI"                │   AVATAR     │ │
│  │  (45px height)       │     (white, centered, 26px)         │  (dropdown)  │ │
│  │  Left 260px area     │     Main area (flex: 1)             │  Right side  │ │
│  └──────────────────────┴─────────────────────────────────────┴──────────────┘ │
│  └─────────── Very Subtle Wave (20px height) ──────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────┘
        ↑ FIXED AT TOP - Doesn't scroll, always visible

┌─────────────────────────────────────────────────────────────────────────────────┐
│  PAGE CONTENT - padding-top to clear the fixed header                          │
│  ┌─────────────────────┬─────────────────────────────────────────────────────┐ │
│  │  SIDEBAR            │  MAIN CONTENT AREA                                  │ │
│  │  (FIXED)            │  (SCROLLABLE)                                       │ │
│  │                     │                                                     │ │
│  │                     │  "Welcome back, Ken!"                              │ │
│  │                     │  KPI Cards                                         │ │
│  │                     │  Your Active Activities                            │ │
│  │                     │  ┌──────┐ ┌──────┐ ┌──────┐                       │ │
│  │  ☐ Dashboard        │  │ gi   │ │ Golf │ │ Surf │                       │ │
│  │  ☐ Activities       │  │ Logo │ │ img  │ │ img  │                       │ │
│  │  ☐ Signups          │  └──────┘ └──────┘ └──────┘                       │ │
│  │  ☐ Passports  (27)  │                                                     │ │
│  │  ☐ Surveys          │  Recent events                                     │ │
│  │  ☐ Reports >        │  [Table]                                           │ │
│  │  ☐ Settings >       │                                                     │ │
│  │                     │  Footer                                             │ │
│  │  (STAYS FIXED)      │  (THIS SCROLLS ↓)                                  │ │
│  └─────────────────────┴─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎨 VISUAL STYLE REQUIREMENTS:

### Gradient Header
- **Height**: 80px (elegant strip style background)
- **Position**: Fixed at top of viewport
- **Width**: 100vw (full viewport width - covers sidebar + main)
- **Z-index**: Very high (above everything else)
- **Background**: Stripe-inspired gradient
  - Complex radial + linear gradient
  - Colors: Pink/Purple → Blue → Orange (like Stripe.com)
  - Should look vibrant and modern

### Header Contents (3 sections):

**LEFT (260px width):**
- White minipass logo
- Height: ~45px
- Centered in the 260px area
- NO hover effects (static)

**CENTER (flexible width):**
- Text: "Fondation LHGI" (or `{{ ORG_NAME }}`)
- Font: Anton
- Size: 26px
- Color: Pure white
- Centered in the main content area
- Subtle text shadow

**RIGHT:**
- User avatar with dropdown (same as current)
- Small padding from right edge

### Subtle Wave
- Height: ~20px
- Very gentle curve (noticeable)
- Gradient colors matching the light gray main section background

---

## 🔑 KEY IMPLEMENTATION POINTS:

### Structure:
1. **Gradient header must be OUTSIDE `.minipass-app`** - at body level, fixed position
2. **Remove existing logo from sidebar** - only keep navigation menu
3. **Add padding-top** to both sidebar and main content to clear the fixed header
4. **Sidebar stays fixed** (doesn't scroll)
5. **Main content scrolls** (only this area scrolls)

### Critical Requirements:
- ✅ Gradient covers FULL page width (sidebar + main)
- ✅ Header is FIXED (stays at top when scrolling)
- ✅ Header is THIN (80px, not bulky)
- ✅ Logo appears ONLY in header (NOT in sidebar)
- ✅ Sidebar menu has NO logo (just navigation links)
- ✅ Main content scrolls, sidebar doesn't
- ✅ No white gaps anywhere


---

## ✅ SUCCESS CRITERIA:

1. ✅ Gradient header is fixed at top (doesn't scroll)
2. ✅ Header spans FULL viewport width (100vw)
3. ✅ Header is 80px tall (thin strip style like)
4. ✅ White logo visible in header (45px, left area)
5. ✅ **Only ONE logo total** (in header, NOT in sidebar)
6. ✅ Sidebar has no logo, only navigation menu
7. ✅ Org name centered in main area (26px, white)
8. ✅ Avatar unchanged on right
9. ✅ Wave is subtle (20px)
10. ✅ Sidebar fixed, main content scrolls
11. ✅ No white/gray gaps anywhere
12. ✅ Gradient looks like Stripe.com (complex, vibrant)

---

## 📋 REFERENCE:

**User's mockup**: `/home/kdresdell/mockup2.png`
- Shows thin gradient header at top
- White logo on left
- Org name centered
- Avatar on right
- Sidebar menu below (NO logo in sidebar)

**Stripe.com reference**: Complex, vibrant gradients (user has seen this 10 times)

---

**SPECIALIST: Figure out the best way to implement this. The wireframe shows WHAT we want, you determine HOW to build it.**
