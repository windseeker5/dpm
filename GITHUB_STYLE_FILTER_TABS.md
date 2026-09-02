# GitHub-Style Filter Tabs — Cleanup Plan

Status: **not started**. Written up 2026-09-01 during the mobile design pass so we can come back to it as its own task.

## What this is

The segmented filter control at the top of nearly every list page — e.g. `Active (5) | Archived (8) | All (13)` on Activities, `Pending | Approved | All` on Signups, `Unmatched | Matched | All` on Interac Inbox. Named `github-filter-*` in the code because it's modeled on GitHub's own filter-tab UI.

It is **not** part of the "too colorful" complaint — its colors are already neutral (`#f6f8fa`, `#ffffff`, `#d1d5da`, `#24292e`, `#586069`). This is a code-health and consistency finding, not a visual-noise one.

## What's actually there (verified, not assumed)

There **is** a real, dedicated stylesheet for this: `static/css/filter-component.css` (388 lines), whose own header comment says *"Reusable GitHub-style filter button styles — Consistent filter experience across all pages."* It defines `.github-filter-group` / `.github-filter-btn` / `.active` with real `:hover`, `:focus-visible`, a `.loading` state, and three separate mobile breakpoints.

The problem: every template that uses this component **also** repeats the exact same styling as a ~700–900 character inline `style=""` attribute per tab, instead of relying on those classes. To make its own rules win over that inline style, `filter-component.css` then has to fight back with `!important` — **118 occurrences in one file.** That's the real signal something's wrong here, not the color choices.

On top of that, `dashboard.html`'s `window.filterLogs()` toggles the active tab by running regex find/replace directly on `btn.style.cssText` (e.g. `.replace(/background: #ffffff[^;]*;/, 'background: rgba(0, 0, 0, 0.03);')`) instead of toggling the `.active` class the CSS already handles. That only keeps working as long as the inline string never changes shape — a fragile, easy-to-silently-break mechanism.

## Where it's used

Real markup instances (`.github-filter-group`), one segmented control per location unless noted:

| File | Line(s) |
|---|---|
| `templates/activities.html` | 64 |
| `templates/signups.html` | 54 |
| `templates/passports.html` | 62 |
| `templates/surveys.html` | 134 |
| `templates/survey_templates.html` | 87 |
| `templates/payment_bot_matches.html` | 60 |
| `templates/user_contacts_report.html` | 67 |
| `templates/survey_results.html` | 479 |
| `templates/activity_dashboard.html` | 1142, 1514, 3411 (3 separate filter groups: passport filters, signup filters, and one more) |

`templates/style_guide.html` also has 3 instances, but that's a static component-reference page, not a live filtered list — lower priority, mostly for keeping the style guide honest.

`templates/dashboard.html` has no markup instance, only the `filterLogs()` JS referenced above, which appears to target a component that isn't actually rendered on that page — worth confirming it's dead code when this is picked up.

## What the skills flag

**Web Design Guidelines**: no real `:hover`/`:focus` feedback was being *authored* per-instance — each template just repeats a static inline snapshot of "active" vs "inactive" — the interactive states only work at all because `filter-component.css` fights through with `!important`. That's backwards from the guideline of styling states via CSS, not inline snapshots.

**Impeccable / design specificity**: copy-pasting the same ~800-character inline block into 9 templates is the textbook case its own "design-specificity" check flags — not because the *look* is wrong (it's fine, and clearly was intentionally designed as *this app's* reusable pattern, not a foreign one), but because the *implementation* never actually became reusable. A real shared component exists in name (`filter-component.css`) but every call site defeats it.

**The project's own `docs/DESIGN.md`** already states the rule being broken: *"Custom CSS is allowed when Tabler cannot express the intended result, but keep it purposeful, small, and in a stylesheet — not scattered inline."* and *"Reuse an existing Minipass pattern only when it is already good enough for the task."* `filter-component.css` is that already-good-enough pattern; it's just not being reused — it's being duplicated around.

## Recommended fix

This is lower-risk than a from-scratch component build, because the shared stylesheet already exists and is already well-built (hover, focus-visible, mobile breakpoints, loading state). The fix is mostly *subtraction*:

1. Strip the inline `style="..."` attribute from every `.github-filter-group` and `.github-filter-btn` instance across the 9 files above, keeping only the semantic classes (`github-filter-group`, `github-filter-btn`, `active` where applicable) and the Jinja logic that decides which tab is active.
2. Once no inline styles remain to fight, remove the now-unnecessary `!important`s from `filter-component.css` and confirm the cascade still resolves correctly.
3. Fix `dashboard.html`'s `filterLogs()` to toggle the `.active` class instead of regex-editing `style.cssText` — first confirm whether that function is even reachable from any rendered markup on that page (may be dead code to delete outright instead).
4. Re-verify every one of the 9 pages afterward: the tabs are functional filters (they carry real URL query params and counts), not decoration — each one needs a click-through check, not just a visual glance, on both desktop and mobile.
5. Decide whether `activity_dashboard.html`'s 3 instances should be reduced to fewer than 3 separate filter groups on one page, or left as-is — flagged for a judgment call at implementation time, not decided here.

## Explicitly not part of this

- Not a color change — leave the neutral palette as-is.
- Not a decision to replace the pattern with Tabler's native `nav-pills`/`btn-group` — `filter-component.css` is a legitimate, already-designed component for this app, not a foreign one. Replacing it with something else is a bigger, separate call this doc isn't making.
- Not touching `style_guide.html`'s 3 reference instances unless they need it to stay accurate to whatever the live pages end up looking like.
