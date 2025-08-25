# Activity Header Visual Mockups

## Current Design (Problem)
```
┌────────────────────────────────────────────────────────────┐
│  Activities 🟢                                             │
│                                                            │
│  Ligue Hockey Gagnon Image              ┌─────────────┐   │
│  Les games de hockey...                 │   IMAGE     │   │
│                                         │   CARD      │   │
│  👥 7 | ⭐ 4.8 | 📍 Location | 🔗       │  (nested)   │   │
│                                         └─────────────┘   │
│  [Edit] [Scan] [Passport]                                 │
└────────────────────────────────────────────────────────────┘
```
**Issue**: Image feels like a separate card inside the main card

---

## Option A: Full-Width Background Image (Netflix/Spotify Style)
```
┌────────────────────────────────────────────────────────────┐
│░░░░░░░░░░░░░░░░░░░░░░░░░[IMAGE BACKGROUND]░░░░░░░░░░░░░░░│
│▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓[GRADIENT OVERLAY]▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│
│                                                            │
│  Activity • Active 🟢                                      │
│  LIGUE HOCKEY GAGNON IMAGE                                │
│  Les games de hockey du lundi, mercredi et vendredi.      │
│                                                            │
│  👥 7    ⭐ 4.8 rating    📍 Location    🔗 signups        │
│                                                            │
│  [Edit] [Scan] [Passport]                                 │
└────────────────────────────────────────────────────────────┘
```
**Used by**: Netflix, Spotify, modern media platforms
**Feel**: Dramatic, immersive, content-focused

---

## Option B: Seamless Split Layout (Stripe/Linear Style) ⭐ RECOMMENDED
```
┌────────────────────────────────────────────────────────────┐
│                                      │                     │
│  Activity • Active 🟢                │                     │
│                                      │                     │
│  LIGUE HOCKEY GAGNON IMAGE          │    Hockey Player    │
│                                      │       Image         │
│  Les games de hockey du lundi,      │    (no border,      │
│  mercredi et vendredi.               │     seamless)       │
│                                      │                     │
│  👥 7   ⭐ 4.8   📍 Location   🔗    │                     │
│                                      │                     │
│  [Edit] [Scan] [Passport]           │                     │
│                                      │                     │
└────────────────────────────────────────────────────────────┘
```
**Used by**: Stripe, Linear, Notion, Vercel, modern SaaS
**Feel**: Clean, professional, balanced

---

## Option C: Subtle Background Pattern (Slack/Discord Style)
```
┌────────────────────────────────────────────────────────────┐
│  ░░░░░░░░░░░░░░░[FADED IMAGE @ 10% opacity]░░░░░░░░░░░░░ │
│                                                            │
│  Activity • Active 🟢                                      │
│                                                            │
│  LIGUE HOCKEY GAGNON IMAGE                                │
│  Les games de hockey du lundi, mercredi et vendredi.      │
│                                                            │
│  👥 7    ⭐ 4.8 rating    📍 Location    🔗 signups        │
│                                                            │
│  [Edit] [Scan] [Passport]                                 │
│                                                            │
└────────────────────────────────────────────────────────────┘
```
**Used by**: Slack (subtle), Discord, GitHub
**Feel**: Subtle, professional, text-focused

---

## 🏆 Most Common for Modern SaaS: Option B

**Option B (Seamless Split)** is the most popular for modern SaaS because:
- ✅ Clean separation of content and visuals
- ✅ Easy to read text (no overlay issues)
- ✅ Responsive-friendly (stacks on mobile)
- ✅ Professional and trustworthy appearance
- ✅ Used by leading SaaS: Stripe, Linear, Vercel, Notion

### How Option B Would Look (Detailed):
```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  Activity • Active 🟢 ←── Small subtitle with inline badge  │
│                                                              │
│  Ligue Hockey Gagnon Image ←─── Bold, prominent title       │
│                                                              │
│  Les games de hockey du      ┊     🏒 Hockey player         │
│  lundi, mercredi et vendredi.┊     image seamlessly         │
│                               ┊     integrated, no           │
│  👥 7 users                   ┊     borders or card          │
│  ⭐ 4.8 rating                ┊     appearance               │
│  📍 Location                  ┊                              │
│  🔗 signups                   ┊     Slight overlap or        │
│                               ┊     fade for integration     │
│  ━━━━━━━━━━━━━━━             ┊                              │
│  Progress: 60%                ┊                              │
│                               ┊                              │
│  👤👤👤👤👤 +5                   ┊                              │
│                                                              │
│  [📝 Edit] [🔍 Scan] [➕ Passport]                          │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Mobile Version (Stacked):
```
┌─────────────────────┐
│  Activity • Active 🟢│
│                     │
│  Ligue Hockey       │
│  Gagnon Image       │
│                     │
│  [  Hockey Image  ] │
│  [   Full Width   ] │
│                     │
│  Les games de...    │
│                     │
│  👥 7    ⭐ 4.8     │
│  📍 Loc  🔗 signup  │
│                     │
│  [Edit] [Scan]      │
│  [Passport]         │
└─────────────────────┘
```

## Statistics Without Dividers:
```
BEFORE (with dividers):
👥 7 │ ⭐ 4.8 │ 📍 Location │ 🔗 signups

AFTER (clean spacing):
👥 7    ⭐ 4.8 rating    📍 Location    🔗 signups

OR (pills style):
[👥 7] [⭐ 4.8] [📍 Location] [🔗 signups]

OR (dots separator):
👥 7 • ⭐ 4.8 • 📍 Location • 🔗 signups
```

## Recommendation: 
Start with **Option B** - it's the most common pattern in modern SaaS (Stripe, Linear, Notion style) and provides the best balance of visual appeal and usability.