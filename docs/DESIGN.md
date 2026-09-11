---
name: minipass
description: The Field Desk — a quiet, structural design system for running real-world activities and money without ceremony.
colors:
  background: "oklch(1 0 0)"
  foreground: "oklch(0.145 0 0)"
  graphite: "oklch(0.205 0 0)"
  graphite-foreground: "oklch(0.985 0 0)"
  tenant-blue: "#066fd1"
  muted: "#eef3f6"
  muted-foreground: "#49566c"
  border: "#dce1e7"
  destructive: "oklch(0.577 0.245 27.325)"
  success: "#10b981"
  warning: "#f59e0b"
typography:
  display:
    fontFamily: "Anton, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "normal"
  h1:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 600
    lineHeight: 1.3
  h2:
    fontFamily: "Inter, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 600
    lineHeight: 1.3
  h5-label:
    fontFamily: "Inter, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 600
    letterSpacing: "0.03em"
  body:
    fontFamily: "Inter, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.5
rounded:
  sm: "0.375rem"
  md: "0.5rem"
  lg: "0.625rem"
  pill: "999px"
spacing:
  xs: "0.25rem"
  sm: "0.5rem"
  md: "1rem"
  lg: "1.5rem"
  xl: "2rem"
components:
  button-primary:
    backgroundColor: "{colors.graphite}"
    textColor: "{colors.graphite-foreground}"
    rounded: "{rounded.md}"
    padding: "0 0.625rem"
    height: "2.25rem"
  button-primary-hover:
    backgroundColor: "color-mix(in oklch, {colors.graphite} 80%, transparent)"
  button-outline:
    backgroundColor: "{colors.background}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.md}"
  button-destructive:
    backgroundColor: "color-mix(in oklch, {colors.destructive} 10%, transparent)"
    textColor: "{colors.destructive}"
    rounded: "{rounded.md}"
  badge-default:
    backgroundColor: "{colors.graphite}"
    textColor: "{colors.graphite-foreground}"
    rounded: "{rounded.pill}"
    padding: "0.125rem 0.625rem"
  badge-outline:
    backgroundColor: "transparent"
    textColor: "{colors.foreground}"
    rounded: "{rounded.pill}"
  card:
    backgroundColor: "{colors.background}"
    rounded: "{rounded.md}"
    padding: "1.5rem"
---

# Design System: minipass

## Overview

**Creative North Star: "The Field Desk"**

minipass is the calm control point at a real event — the check-in table, the scorer's booth, the folder of passports and payments an organizer keeps at hand. It is not a marketing product being browsed; it is a tool being operated, often on a phone, often mid-task, often by someone who runs the activity itself rather than a professional software administrator. The system stays quiet and structural: borders, spacing, and type hierarchy carry the weight, and color is spent only where it means something (a status, a destructive action, the one branded or trending element on a screen) rather than as decoration.

The visual language is a deliberate port of a shadcn/basecoat-style neutral system (namespaced `mp-*` to coexist with the inherited Tabler.io foundation) layered on top of Tabler's own gray scale, so the two never drift into two different grays. It is flat by default, uses one restrained shadow weight for the handful of surfaces that need to read as distinct cards, and reserves its only saturated color — Tenant Blue — for the small set of places where "this is the current or branded thing" needs to be visible: a KPI trend line, the active page in pagination, and eventually a tenant's own brand color.

minipass deliberately does not chase generic SaaS-dashboard aesthetics — no purple/violet gradients, no glassmorphism, no oversized rounded-everything "AI startup" look. It reads closer to an operations tool than a marketing surface, because that is what it is used as.

**Key Characteristics:**
- Quiet and structural: color and shadow are reserved for meaning, not mood
- Flat by default, one shadow weight, used sparingly on real card surfaces
- Two-tier color system: a neutral does the heavy lifting, blue marks the exception
- Server-rendered, no SPA framework, animations minimal and purposeful
- Every component ships one canonical macro; no page hand-rolls a variant

## Colors

The palette is almost entirely neutral by design; Graphite carries default interactive weight and Tenant Blue is spent on a short, fixed list of elements.

### Primary
- **Graphite** (`oklch(0.205 0 0)`, ≈ near-black): the default action color — primary buttons, the default badge, and link-variant text. It is a neutral, not a brand color; it is what most of the interface's interactive weight rests on.
- **Graphite Foreground** (`oklch(0.985 0 0)`, near-white): text/icon color on top of Graphite surfaces.

### Secondary
- **Tenant Blue** (`#066fd1`, currently sourced from Tabler's `--tblr-primary`): the system's only saturated accent. Used exclusively for the KPI card trend line/chart, and pagination's current-page indicator. It is read from a single custom property (`--mp-brand-primary`) specifically so a future per-tenant branding setting can override it in one place with no component changes — it is provisioned as a variable point, not hardcoded, on purpose.

### Neutral
- **Surface** (`oklch(1 0 0)`, white): default background for cards, popovers, and inputs.
- **Ink** (`oklch(0.145 0 0)`, near-black): body text and icon color on Surface.
- **Muted** (`#eef3f6`, Tabler gray-100): secondary/ghost-hover backgrounds, filter-tab track, muted surfaces.
- **Muted Foreground** (`#49566c`, Tabler gray-600): secondary text, descriptions, table header text.
- **Border** (`#dce1e7`, Tabler gray-200): all component borders, dividers, outline-button borders.

### Status
- **Destructive** (`oklch(0.577 0.245 27.325)`): delete actions and destructive badges, always shown at low-opacity tint (`color-mix(... 10%)`) rather than a solid fill, so it reads as a warning tone rather than an alarm.
- **Success** (`#10b981`) / **Warning** (`#f59e0b`): status semantics used on legacy (pre-`mp-*`) dashboard surfaces; not yet ported into the `mp-*` badge/button variant set.

### Named Rules
**The Tenant Blue Rule.** Tenant Blue never appears on a default action, a primary button, or ordinary body content. It marks exactly one of: a trend/chart series, the current page in pagination, or (in the future) a tenant's own brand color. If a design adds blue to a button or a badge that isn't one of those three things, that's the wrong color — reach for Graphite or a status tint instead.

**The No Pure Gray Rule.** Neutral tones are never zero-chroma achromatic gray; they're read from Tabler's own lightly cool-tinted gray scale (`--tblr-gray-*`). A fully neutral gray reads flatter and more sterile in side-by-side comparison — this was proven out replacing the old GitHub-Primer palette in Filter Tabs, whose cool-tinted grays revealed the difference. Every `mp-*` component reads gray through this one scale so nothing reintroduces a competing, more sterile gray.

## Typography

**Display Font:** Anton (with sans-serif fallback) — organization name / brand gradient text only, never body UI.
**Body Font:** Inter (weights 300–700, loaded via Google Fonts), with the system font stack as fallback.
**Mono Font:** `SF Mono, Monaco, Cascadia Code, Roboto Mono, monospace` — used only by the Kbd component for keyboard-shortcut hints.

**Character:** A single, fixed heading scale applied globally — no page ever overrides heading size, color, or family locally. The scale is intentionally compact (24px down to 14px) because these are task screens read at a glance, not editorial pages meant to be lingered on.

### Hierarchy
- **H1** (600, 24px/1.3): page title — one per page, in the page header only.
- **H2** (600, 20px/1.3): section title within a page body.
- **H3** (600, 18px): card or subsection title.
- **H4** (600, 16px): minor heading.
- **H5 / Label** (600, 14px, uppercase, +0.03em tracking): eyebrow labels and field-group headers.
- **Body** (400, 14px/1.5, `.mp-text-body`, color Muted Foreground): descriptions and secondary text.

### Named Rules
**The Fixed Scale Rule.** Headings are global. If a heading looks wrong on a page, the fix is in `templates/base.html`'s shared scale, never a page-local `<style>` override.

## Layout

The page-width primitive is `.dashboard-container` (`max-width: 1400px`, centered, `1.5rem` gutter, `1rem` below 991px) — every real page-header/page-body pair renders inside it. `.container-xl` is a Bootstrap class that is force-zeroed app-wide (an intentional `!important` override strips its padding/max-width) and must never be used for page content; it silently renders edge-to-edge with no gutter, invisible on a wide desktop screenshot and glaring on mobile.

A single-card form or detail page is a full-width direct child of `.dashboard-container` — never centered via a Bootstrap `row.justify-content-center > col-lg-*`, which visually detaches the card from a flush-left page header above it. Inside that full-width card, the actual fields (and the footer's action buttons, in the same wrapper) are wrapped in `.mp-form-content` (`max-width: 40rem`, left-anchored, no auto margin), so a wide monitor doesn't stretch a single-line input past 1300px or strand the submit button 1000px+ from the field the user just filled.

Responsive behavior is breakpoint-driven at the component level (e.g. the Data Table toolbar's search control is `@container`-driven, collapsing to icon-only under ~768px of its own card, not the viewport) rather than hiding whole sections on mobile.

### Named Rules
**The Dashboard Container Rule.** Page-header and page-body content always sits in `.dashboard-container`. `.container-xl` is dead for content purposes anywhere in this app.

## Elevation & Depth

minipass is flat by default. There is no ambient shadow system and no dark mode (an explicit design decision, not an oversight — `mp-components.css` states this directly, and the Style Guide's theme-switcher is a self-contained interaction demo only, wired to nothing global). Depth exists only as a single, restrained shadow (`--minipass-shadow-sm`, `0 1px 2px 0 rgb(0 0 0 / 0.05)`) applied to a short list of surfaces that need to visually separate from the page background: KPI cards, the Settings navigation surface, and mobile table-row cards. Popovers (Action Menu) use a slightly heavier layered shadow plus a 1px ring to read above app chrome, since they must visually float rather than sit flush.

### Shadow Vocabulary
- **Surface** (`box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05)`): KPI cards, settings surface, mobile table cards — anything that needs to read as "a card" without looking lifted.
- **Popover** (`box-shadow: 0 0 0 1px color-mix(in oklch, var(--mp-foreground) 10%, transparent), 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)`): Action Menu and other floating overlays.

### Named Rules
**The Flat-By-Default Rule.** Surfaces are flat at rest. A shadow appears only to mark a genuine card boundary or a floating overlay — never as decoration on a button, badge, or static block of content.

## Shapes

Radius is deliberately small and consistent: `--mp-radius: 0.625rem` (10px) as the base scale, from which components derive `--mp-radius-md` (0.5rem / 8px — the default for buttons, inputs, cards, popovers) and `--mp-radius-sm` (0.375rem / 6px — menu items, skeletons, kbd keys). Fully round shapes (`999px`) are reserved for pill-shaped elements only: badges, the progress bar, and switch tracks. Borders are 1px, always drawn from the Border neutral token, never a heavier or colored border for emphasis — emphasis comes from background/color, not stroke weight.

## Components

### Buttons
- **Shape:** `border-radius: 0.5rem` (`--mp-radius-md`); compact sizes (`xs`, icon variants) tighten to 8px, default/lg stay at the base.
- **Primary:** Graphite background, Graphite Foreground text, height 2.25rem, `0.625rem` horizontal padding, 500-weight 14px label.
- **Hover / Focus:** hover mixes the base color to 80% opacity; focus-visible draws a 3px `color-mix` ring from `--mp-ring`; active press shifts the button down 1px (`translateY(1px)`) instead of scaling — a physical "pressed" cue, not an opacity fade.
- **Secondary / Outline / Ghost / Destructive / Link:** Secondary uses Muted background; Outline is Surface + Border + a faint 1px shadow; Ghost is transparent until hover; Destructive is a 10%-opacity Destructive tint, never a solid fill; Link is text-only in Graphite with an underline on hover.
- Standard actions (Save, Submit, Cancel, Update) are always plain text, never icon+label — the icon slot exists only for icon-only buttons or an established idiom like a "+" on an Add button.

### Badges
- **Style:** pill (`border-radius: 999px`), `0.125rem 0.625rem` padding, 500-weight 12px text.
- **Variants:** Default (Graphite fill), Secondary (Muted fill), Destructive (10%-tint, matches button destructive treatment), Outline (transparent + Border stroke).
- Coexists with Tabler's own `badge bg-*-lt` spans, which remain on pages not yet migrated to the `mp-*` system — the two are not visually reconciled by design; `mp-badge` is the target for new/redesigned pages.

### Cards / Containers
- **Corner Style:** `--mp-radius-md` (8px).
- **Background:** Surface (white).
- **Shadow Strategy:** the Surface shadow from Elevation & Depth, or no shadow at all on cards that already sit inside `.dashboard-container` without needing to separate from it.
- **Border:** 1px Border token where a card needs a hairline edge (e.g. Accordion items); omitted where the shadow alone is sufficient.

### Inputs / Fields
- **Style:** Border-token stroke, Surface background, `--mp-radius-md` corners, shared field shell across Input, Textarea, and Select.
- **Focus:** same recipe as buttons — a `color-mix` ring from `--mp-ring`, not a color or border-width change.
- **Disabled:** 0.5 opacity, `pointer-events: none`.
- Every field ships with a visible label and optional description via the shared `.mp-field`/`.mp-label` shell; there is no label-less input pattern in the system.

### Choice Cards
- **Purpose:** Use for one-of-many decisions whose options need a title and supporting context; use the simpler Radio Group when labels are short.
- **Structure:** A semantic fieldset of native radio inputs. Each complete card is one label and click/tap target; no JavaScript manages selection.
- **Style:** Compact operational layout with the icon and title in one header row, a visible radio at the top-right, and supporting copy below. Selected cards use one Graphite border plus a faint Muted fill rather than Tenant Blue; the outer focus ring appears only for keyboard navigation.
- **Validation:** The macro accepts an accessible inline error state and renders guidance rather than a blank fieldset when no options are available.
- **Responsive:** Two- and three-column groups stack into one column below the tablet breakpoint.

### Image Picker
- **Structure:** A labelled 100px photo thumbnail stays visible; activating it reveals one inline drawer separated by the standard Border token.
- **Sources:** Search and Upload share the same drawer and are selected with the standard Switch component. Search composes the standard Input and icon Button; Upload uses the standard file Input.
- **Behavior:** `macros/image_picker.html` owns all markup and `photo-normalizer.js` adds page-specific image search, cropping, thumbnail, and removal behavior. Pages must call the macro rather than recreating the shell.
- **Responsive:** The drawer shrinks within the available form width without horizontal page overflow; the thumbnail remains a fixed, reliable target.

### Form Dialog
- **Purpose:** Use for short create/edit work that must stay in context. It adapts Basic Form spacing to a modal without Bootstrap's divided header and gray footer bands.
- **Structure:** One white surface with title, optional description, a vertical `.mp-form-fields` stack, and right-aligned actions. Bootstrap may own focus trapping and backdrop behavior, but `form_dialog()` owns the visual composition.
- **Scope:** Use a full page for long, consequential, or multi-section forms; do not force them into a dialog.

### Editable Collection
- **Purpose:** Use for form-local rows—such as passport types or sessions—that can be added and edited before the parent form is saved. It is the client-editable companion to Data Table, not a competing table style.
- **Structure:** Reuses Data Table headers, gray scale, row rhythm, empty-state language, and Action Menu. Runtime rows use `mp-editable-collection.js` helpers so pages do not recreate button or menu markup.
- **Responsive:** Desktop renders a table. Narrow layouts turn each row into a labelled card rather than introducing horizontal scrolling or hiding important values.

### Collapsible Section
- **Purpose:** Use for a substantial optional group such as Advanced Settings; use Accordion for multiple peer FAQ-style items.
- **Structure:** Native `<details>/<summary>` via `collapsible_section()`, with a title, optional description and standard chevron. No Bootstrap collapse JavaScript is required.

### Navigation
- **Filter Tabs:** a segmented track (Muted background, Border edge) with a sliding-indicator active pill (inset ring, not a border) — matched deliberately to GitHub's file-view tab pattern. Scroll position across a tab click's page reload is preserved automatically.
- **Settings Navigation:** horizontal links on desktop with a 2px Tenant Blue underline on the active tab; collapses to a labeled selector on mobile.
- **Pagination:** ghost buttons by default; the current page is drawn as an outline button using the Tenant Blue-ready current-indicator token (`--mp-brand-primary`) rather than Graphite, deliberately foreshadowing per-tenant branding. Mobile drops individual page-number buttons for a "‹ Page 2 of 5 ›" control with 44px+ touch targets.

### Data Table (signature component)
The shared shape behind every list page: a toolbar (centered filter tabs, a search affordance that expands inline on desktop and fully replaces the tabs on a narrow container), `table_desktop()` / `table_mobile()` row rendering, and a dedicated empty state. It is `@container`-responsive at the card's own width, not the viewport's, so the same markup behaves correctly whether it's the only content on the page or sitting in a narrower context.

### KPI Card (signature component)
Desktop: label, a period dropdown, the value, a trend badge, and an edge-to-edge sparkline (Tenant Blue series) — narrow enough that five sit across a row, forced to equal width/height via a grid track regardless of content. Mobile: a deliberately simpler, centered-value card with no dropdown and no chart — not a shrunk desktop card, a different composition for a swipeable context.

## Do's and Don'ts

### Do:
- **Do** use `.dashboard-container` for all page-header/page-body content.
- **Do** wrap form fields and footer action buttons in `.mp-form-content` inside a full-width card.
- **Do** use the shared macros (`macros/buttons.html`, `macros/badge.html`, `macros/action_menu.html`, `macros/filter_tabs.html`, etc.) for every instance of a component — extend the macro/CSS if it can't do what's needed, rather than hand-rolling a one-off.
- **Do** keep standard button labels plain text (Save, Submit, Cancel, Update) with no leading icon.
- **Do** reserve Tenant Blue for the current-page indicator, KPI trend series, and future per-tenant branding — nothing else.

### Don't:
- **Don't** use `.container-xl` for page content — it is force-zeroed app-wide and will silently render edge-to-edge.
- **Don't** center a single-card page in a Bootstrap `row.justify-content-center > col-lg-*` — it detaches the card from a flush-left page header.
- **Don't** add a decorative icon in front of an ordinary button label — icons are for icon-only buttons or well-established idioms only.
- **Don't** introduce a second gray scale, a zero-chroma neutral, or a competing shadow/radius value outside the `--mp-*` tokens.
- **Don't** reach for purple/violet gradients, glassmorphism, or an oversized "rounded-everything" treatment — this system reads as an operations tool, not a marketing surface.
- **Don't** build a real dark mode from the Style Guide's theme-switcher demo — it is an isolated interaction pattern only, wired to nothing global.

## Process & Workflow

*(Non-canonical section, carried forward from the prior DESIGN.md revision — process and QA guardrails rather than visual tokens. Most implementation rules below are also enforced as hard rules in `AGENTS.md`; this section adds the parts that are process/QA detail rather than a single rule.)*

### Strategy

minipass keeps its existing **Flask + Jinja + Tabler.io** foundation; there is no framework migration planned. UI improvements happen **one explicitly selected page at a time**, using the available UI/UX skills to improve hierarchy, usability, accessibility, responsiveness, and visual quality while preserving working product behavior.

### Page-by-page workflow

1. **Audit the current page first.** Inspect its template, route, real data, desktop layout, and mobile layout.
2. **Confirm the goal.** Understand what the user dislikes, what must remain, and what success looks like before editing.
3. **Design for the page's real task.** Do not apply a generic dashboard template or copy another framework's starter component.
4. **Preserve behavior.** Keep routes, form fields, CSRF, permissions, payments, emails, and business rules working.
5. **Implement narrowly.** Change only the selected page and truly shared code required by it.
6. **Test the real flow.** Test against `localhost:5000` with the real local database and credentials.
7. **Review desktop and mobile together.** Inspect the DOM, verify keyboard/touch behavior, and capture screenshots for visual confirmation.
8. **Run an accessibility/UX quality pass** before considering the page complete.

### UX quality floor

**Hierarchy:** one clear page title and one obvious primary action; group related controls; avoid excessive cards/borders/badges/competing accents; put the most frequent user task first.

**Forms:** every control has a visible label; errors explain the problem and recovery; preserve entered values after validation errors when safe; use the correct input type/autocomplete; touch targets at least 44×44px.

**Mobile:** design and test at 375px width; no horizontal overflow; don't simply hide essential desktop information; keep primary actions reachable and readable; long names/dates/addresses/translated text must wrap safely.

**Accessibility:** semantic headings, landmarks, labels, buttons; preserve visible keyboard focus; body text meets WCAG AA contrast; don't disable zoom; don't use color as the only status indicator; images need useful alt text and explicit dimensions where practical.

**Performance:** avoid unnecessary web fonts, icon fonts, JavaScript, and duplicate assets; prefer committed local assets over runtime frontend build dependencies; Node.js must not be required in production containers; keep animations rare, purposeful, and respectful of reduced-motion preferences.

### Definition of done

A UI change is complete only when: the real user flow works; desktop and mobile have both been inspected; keyboard and touch interactions work; loading/empty/error/success states relevant to the page are handled; no unrelated page was unintentionally changed; and the browser console and Flask logs show no new errors.
