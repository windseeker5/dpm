# Dashboard Component Rework — Plan

## Goal

Rework `templates/dashboard.html` **only**, replacing its hand-rolled markup/CSS/JS with the reusable Jinja macros that already exist and are confirmed merged on `main` (the style guide, `templates/style_guide.html`). No new components get designed — every macro named below already exists in `templates/macros/`.

## Confirmed available components (on `main`, PR #46 merged)

| Component | File | Macros |
|---|---|---|
| Button | `macros/buttons.html` | `button(text, variant, size, type, href, id, attrs)` |
| Action Menu | `macros/action_menu.html` | `dropdown_menu(...)` (low-level popover), `action_menu(id, items, label, align)` |
| Filter Tabs | `macros/filter_tabs.html` | `filter_tabs(tabs, aria_label)` |
| Typography | `style_guide.html` only | no macro — semantic tags + `.mp-text-body` |
| KPI Card | `macros/kpi_card.html` | `kpi_card_desktop(...)`, `kpi_card_mobile(...)` |
| Avatar (Initials) | `macros/avatar.html` | `avatar_initials(name, size, attrs)` |
| Data Table | `macros/data_table.html` | `table_toolbar(...)`, `table_desktop(...)`, `table_mobile(...)`, `table_empty_state(...)` |
| Pagination | `macros/pagination.html` | `pagination_desktop(...)`, `pagination_mobile(...)` (plain-value based — not the older `render_pagination()`, which needs a Flask-SQLAlchemy pagination object) |

Two things need adding to dashboard's own `{% block scripts %}` because they aren't global (checked `base.html` — only `mp-components.css` and `mp-action-menu.js` are):
- ApexCharts CDN + `mp-kpi-card.js` — powers `kpi_card_desktop`'s sparkline
- `mp-table-toolbar.js` — powers the Data Table's collapsible search/filter toolbar

## Current `dashboard.html` structure (before)

1. Page header — plain markup
2. **Desktop KPI row** — 5 hand-rolled cards (Revenue, Active Passports, Passports Created, Passports Redeemed, Pending Signups), custom SVG chart generator, Bootstrap `.dropdown` period selector
3. **Mobile KPI carousel** — separate hand-rolled `.mobile-kpi-card` markup, dot-indicator carousel
4. **Activities grid/scroller** — per-card hand-rolled `.share-dropdown-menu` popover (not using `action_menu`)
5. **History / Activity Log table** — entirely client-side JS rendering from `logs|tojson`, hand-rolled pagination footer, no search, no filters
6. A large `{% block scripts %}`: custom SVG chart generation (`generateInteractiveLineChart`, `generateBarChart`), tooltip logic, mobile-carousel JS/CSS, dropdown handlers, client-side table/pagination rendering

## Rework mapping (section → component)

- Desktop KPI row → `kpi_card_desktop()` × 5, using the macro's own period dropdown (`dropdown_menu`) instead of the hard-coded Bootstrap one
- Mobile KPI carousel → `kpi_card_mobile()` × 5, kept inside the existing dot-carousel wrapper (that wrapper is dashboard-specific layout, not a style-guide component)
- Activity card share popover → `action_menu()`
- History/Activity Log table → `table_toolbar()` + `table_desktop()` + `table_mobile()` + `table_empty_state()`, with real filter tabs (e.g. All / Signups / Passports Created / Redeemed / Payments — using fields the log already has) and a real search box (e.g. by name/email)
- Log table pagination → `pagination_desktop()` + `pagination_mobile()`
- Any plain buttons (e.g. "Add activity", header actions) → `button()`

## Required plumbing changes

- **`app.py` `dashboard()` route:**
  - Shape `trend_data` per KPI metric for `kpi_card_desktop`
  - Convert History log fetching from "dump everything, paginate client-side in JS" to real server-side pagination (`.paginate()` on the existing log query) — `pagination_desktop`/`pagination_mobile` take plain `page`/`pages`/`total`/`items_count`, not a client-rendered blob. This is the one real backend change, but it's mechanical — reusing the existing log query, not new business logic.
  - Build the `rows` list in the shape `table_desktop`/`table_mobile` expect (`id`, `avatar_name`, `primary`, `secondary`, `cells`, `actions`) from log entries
  - Wire filter-tab / search query params (`?tab=..&q=..`) into the same route, filtering on fields the log data already has — no new functionality invented, just exposing existing fields as filters
- **Cleanup:** delete the now-dead CSS (`.mobile-kpi-card`, `.share-dropdown-menu`, chart-tooltip styles) and JS (`generateInteractiveLineChart`, `generateBarChart`, custom dropdown/pagination handlers) from dashboard's scripts block

## Explicitly out of scope for this round

- No new components — everything used already exists on `main`
- No changes to other pages (Passports, Signups, Activities) even though Data Table/Pagination exist partly to eventually unify those — dashboard only, this round
- No touching `feature/wayne-operations-skills` — that's separate, unrelated work

## Suggested sequencing

1. Branch off `main` (now that PR #46 — Data Table/Pagination/Filter Tabs — is confirmed merged): `feature/dashboard-component-rework`
2. Swap KPI cards (desktop + mobile) first — self-contained, only touches `trend_data` shaping
3. Swap activity card share menu — self-contained
4. Convert History table to Data Table + real server-side pagination + filter/search — the larger, backend-touching piece, done last
5. Delete dead CSS/JS
6. Playwright click-through test on `localhost:5000` — KPI period switches, activity share menu, mobile carousel, History filters/search/pagination
