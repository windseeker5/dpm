# Minipass Brand Style Guide

**Framework:** Tabler.io v1.0.0
**Last updated:** February 2026

---

## Fonts

| Role | Family | Loaded from |
|---|---|---|
| H1 / H2 / H3 | **Roboto Slab** (serif) | Google Fonts |
| Body / UI / H4+ | **Inter** (sans-serif) | Google Fonts / Tabler default |
| Sidebar org name | **Anton** (display) | Google Fonts |

Google Fonts import (in `base.html`):
```
Anton, Inter:wght@300;400;500;600;700, Roboto+Slab:wght@400;500;600;700
```

---

## Typography — Web UI

| Element | Family | Weight | Size | Color | Notes |
|---|---|---|---|---|---|
| H1 | Roboto Slab | 600 | 2rem | `#1a1f36` | letter-spacing -0.02em, line-height 1.2 |
| H2 | Roboto Slab | 600 | 1.7rem | `#2d3748` | letter-spacing -0.02em, line-height 1.3 |
| H3 | Roboto Slab | 400 | 1.4rem | `#2d3748` | letter-spacing -0.02em, line-height 1.3 |
| H4 / H5 / H6 | Inter | 600 | Tabler default | `#232b38` | Tabler handles these |
| Body text | Inter | 400 | 0.875rem | `#232b38` | Tabler default |
| Secondary / muted | Inter | 400 | 0.875rem | `#6b7280` | Use `text-muted` class |
| Small / fine print | Inter | 400 | 0.75rem | `#94a3b8` | Use `text-secondary small` |
| Org name (sidebar) | Anton | 400 | 1.8rem | Animated gradient | See gradient spec below |

---

## Typography — Emails

| Element | Size | Weight | Color |
|---|---|---|---|
| Email title / H1 | 20px | bold | `#232b38` |
| Body text | 15–16px | 400 | `#475569` |
| Line height | — | — | 1.7 |
| Footer main text | 13px | 400 | `#6b7280` |
| Footer detail | 12px | 400 | `#6b7280` |
| Footer fine print | 11px | 400 | `#94a3b8` |
| Email font stack | `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif` | | |

---

## Brand Colors

| Name | Hex | Usage |
|---|---|---|
| **Brand Green** | `#00ab66` | PWA theme color, nav badges, primary accent |
| **Green CTA** | `#22c55e` | Email CTA buttons, section divider end |
| **Tabler Primary (Blue)** | `#206bc4` | `btn-primary`, links |
| **Tabler Dark** | `#1a1f36` | H1 color, near-black text |
| **Dark Gray** | `#2d3748` | H2 / H3 color |
| **Body Gray** | `#232b38` | Default UI body text |

---

## Status / Alert Colors

| Status | Background gradient | Text |
|---|---|---|
| Success | `#10b981` → `#059669` | White |
| Danger | `#ef4444` → `#dc2626` | White |
| Warning | `#f59e0b` → `#d97706` | White |
| Tier limit | `#fcd34d` border, light bg | `#92400e` dark amber |

---

## Section Divider

Rainbow gradient used between page sections:

```css
background: linear-gradient(90deg, #6366F1, #3B82F6, #06B6D4, #14B8A6, #10B981, #059669);
height: 1px;
```

HTML: `<hr class="section-divider">`

---

## Org Name Gradient (Sidebar)

```css
font-family: 'Anton', sans-serif;
font-size: 1.8rem;                /* mobile: 1.5rem */
background: linear-gradient(90deg, #1a73e8 0%, #6c4edb 25%, #db4ed4 50%, #6c4edb 75%, #1a73e8 100%);
background-size: 200% 200%;
-webkit-background-clip: text;
-webkit-text-fill-color: transparent;
animation: gradientShift 7s ease infinite;  /* slow animated shift */
```

---

## Tables

Tabler classes — copy exactly:

```html
<table class="table table-vcenter card-table">
  <thead>
    <tr>
      <th>Column</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Value</td>
    </tr>
  </tbody>
</table>
```

- No hover effects on rows (project rule)
- Wrap in `<div class="card"><div class="table-responsive">` for responsive behaviour
- Table header: Inter, uppercase not required, Tabler handles weight

---

## Buttons

| Class | Usage |
|---|---|
| `btn btn-primary` | Main action (create, save, send) |
| `btn btn-secondary` | Secondary / Actions dropdown trigger |
| `btn btn-success` | Approve, mark paid |
| `btn btn-danger` | Delete, reject |
| `btn btn-warning` | Caution actions |
| `btn btn-link` | Cancel / dismiss in modals |
| Add `btn-sm` | For actions inside table rows |

---

## Badges

```html
<span class="badge bg-success">Paid</span>
<span class="badge bg-warning text-dark">Pending</span>
<span class="badge bg-danger">Overdue</span>
<span class="badge bg-secondary">Inactive</span>
<span class="badge bg-blue">Info</span>
```

---

## Card

```html
<div class="card">
  <div class="card-header">
    <h3 class="card-title">Title</h3>
  </div>
  <div class="card-body">
    Content here
  </div>
</div>
```

- No `box-shadow` overrides, no gradients — plain white cards only
- `card-title` renders in Tabler defaults (Inter, ~1rem, `#232b38`)

---

## Icons

Tabler Icons — prefix `ti ti-`:

```html
<i class="ti ti-edit"></i>
<i class="ti ti-trash"></i>
<i class="ti ti-mail"></i>
<i class="ti ti-speakerphone"></i>
```

Full library: https://tabler.io/icons

---

## ❌ Never Use

```css
/* These are banned */
<style> any custom styles </style>
box-shadow: ...
background: gradient(...)    /* except section-divider and org-name — already defined */
transform: ...
animation: ...               /* except org-name gradient — already defined */
class="custom-*"
class="my-*"
```

All styling must come from Tabler classes or the global styles already defined in `base.html`.

---

## Reference Files

| File | Purpose |
|---|---|
| `templates/base.html` | Global typography + flash alerts + fonts |
| `templates/activity_dashboard.html` | Reference page — all UI patterns |
| `templates/passports.html` | Reference for tables + filters |
| `docs/DESIGN_SYSTEM.md` | Full component patterns (tables, search, pagination) |
| `static/tabler/css/tabler.min.css` | Tabler v1.0.0 source |
