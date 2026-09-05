# Dashboard Page — UI/UX Recommendations

Audit of the main admin dashboard (`/dashboard`, `templates/dashboard.html`, route `app.py:1584`) — the KPI + Activities overview admins land on after login. Done with the Impeccable audit framework, the Vercel Web Interface Guidelines, and `docs/DESIGN.md`'s own quality floor. Static code review only (Chrome extension wasn't connected this session) — re-verify anything below with a live 375px + desktop pass before shipping.

Scope: this is the main `/dashboard` only, not the per-activity `/activity-dashboard/<id>` page (that one already got a redesign pass in commits `9f91538`/`4585380`/`a8d41eb`).

> **Known direction change:** you already plan to rebuild the KPI cards as a macro/component and redesign the table pagination. The KPI-specific and pagination items below describe *what's wrong today* so that context isn't lost — treat them as input to that redesign, not as a separate patch to apply first.

---

## KPI cards (rebuilding as a macro — feed these in)

- Every KPI card repeats `style="border-radius: 12px; position: relative;"` inline (desktop: lines 43, 85, 191, 235; mobile: 292, 305, 318, 331) instead of a shared class/macro.
- Scattered raw hex colors instead of tokens: `#0f172a`, `#dc2626`, `#94a3b8`, `#f1f5f9`, `#206bc4`, `#4a5a6b`, `#d1d5db` — no dark-mode support, and desktop/mobile cards duplicate the same colors independently.
- Lines 135–187: a fully commented-out "Passports Created" card (~50 lines) left in the file after being replaced by "Passports Redeemed" — dead code to drop when the macro replaces this section.
- Lines 629–666: `.kpi-carousel-wrapper` / `.kpi-carousel` / `.kpi-track` / `.kpi-slide` / `.kpi-dots` CSS with no matching markup anywhere — leftover from an earlier mobile-carousel implementation (the real one uses `.mobile-kpi-*` classes). Drop it.
- Period-selector dropdown toggle (e.g. line 48, `class="btn btn-sm text-muted dropdown-toggle"`) is well under the project's own 44×44px touch-target floor (`docs/DESIGN.md`) — worth fixing in the new component regardless of visual redesign.
- The 40px sparkline charts (`#revenue-chart`, `#active-passports-chart`, etc.) have no text alternative — screen reader users get the number and trend badge but not the shape. Give the new component an `aria-label` summarizing the trend.
- ApexCharts is loaded unpinned (`cdn.jsdelivr.net/npm/apexcharts@latest`, line 40), inline mid-body instead of in `head`/`scripts`. Pin an exact version and move it when you touch this.
- The KPI refresh/chart logic (`scripts` block, roughly lines 715–2243) is ~1600 lines of hand-rolled JS with what look like parallel desktop/mobile codepaths (`updateSingleKPIChart` vs. separate `mobile-revenue-chart`/`mobile-active-passports-chart` lookups). A macro rebuild is a natural place to collapse this — see if the new component can share one update path for both breakpoints.

## Table pagination (redesigning — feed these in)

- Mobile hides `Date/Time` and `Type` columns entirely (`d-none d-md-table-cell`, lines 596–597), leaving only `Description` — `docs/DESIGN.md`'s own mobile rule says not to simply hide essential desktop information. When the redesign happens, fold date/type into the description cell (e.g. a small muted line under it) instead of dropping them.
- Current pagination controls (`#paginationControls`, populated by JS around line 1759) are plain Bootstrap pagination — reasonable candidate to swap for the new component library's controls once you have real primitives instead of ad hoc Bootstrap markup.

## Everything else on the page (not tied to the two redesigns above)

1. **New component library isn't used on this page.** `mp-btn`, `mp-action-menu`, `mp-filter-tabs` (commit `a8d41eb`) only appear on `/style-guide` and `/components` today. The "Add" button (line 363) is still a raw `.btn.btn-dark`.
2. **Nested interactive elements on activity cards — real bug, not just cleanup.** Each activity card is one big `<a href="...">` wrapping the whole card, with a `<div role="button" onclick="...">` copy-link control nested inside it (desktop: lines 396–422, mobile: 493–521), relying on `stopPropagation()`. This is invalid HTML, isn't keyboard-focusable, and on mobile a mis-tap opens the activity dashboard instead of copying the link. Recommend pulling the control out of the anchor and using a real `<button type="button" aria-label="Copy signup link">`.
3. **Circular copy-link buttons are 40px (`2.5rem`)** — just under the 44×44px touch-target floor.
4. **Horizontal-scroll carousels** (`.mobile-kpi-scroll` and `#mobileActivitiesScroll`, both `scroll-snap-type: x mandatory`) are a plausible pattern but should be confirmed live on a real phone — edge-swipe conflicts with the browser's back-swipe gesture are a common papercut with this exact setup. Not asserting a defect, just flagging for a live check.

## Priority if you want to sequence it

- **P1:** nested interactive elements on activity cards (#2 above) — genuine a11y + mis-tap bug, independent of either redesign.
- **P2 (fold into the KPI macro / pagination redesign):** touch targets, mobile table column-hiding, dead code removal, hardcoded colors/tokens, unpinned CDN script.
- **P3:** chart text alternative, JS consolidation, adopting `mp-btn`/`mp-action-menu` for the "Add" button.

## Next steps

- `/impeccable audit templates/dashboard.html` for a scored (0–20) technical report once you're ready to track progress numerically.
- Live Playwright/Chrome pass at 375px and desktop widths before/after the KPI macro and pagination redesign ship, per the standing testing workflow (`localhost:5000`, real browser, not DOM-injected state).
