# Issues to Fix — Activity Archive Flow

Status: **RESOLVED** (2026-09-02). Verified live via browser click-through, not just code reading.

## 1. Archive confirmation screen (close vs. keep passports) is unreachable — FIXED

Root cause: `Activity.status` had two spellings of "archived" (`'archived'` from
the Edit Activity toggle, `'inactive'` from older archive routes), and the gate
meant to trigger the confirm screen only checked for `'inactive'`
(`app.py:2971`), so it never fired for the toggle path everyone actually uses.

Fix: standardized on `'archived'` everywhere (`app.py:2971`, `7120`, `9336`,
`9350`, `activities.html:172`, `activity_dashboard.html:1115`), with a DB
migration (`migrations/versions/d1a7e42b9c03_...py`) backfilling old
`'inactive'` rows.

Also found and fixed while wiring this back up:
- The confirm screen's form was missing its CSRF token (`confirm_archive_activity.html`) —
  it would 400 on every submit once actually reached.
- Per Ken's request, the "close all passports" option now does a real check-in
  (decrement + `Redemption` row + the activity's `redeemPass` email) instead of
  a silent bulk DB update, via a new shared helper `close_out_passport()` in
  `utils.py`, reused by `execute_archive_activity` and `bulk_close_passports`.
- Options relabeled: **"Archive and check in every active passport"** vs
  **"Archive silently"**.

Verified live: toggling Archive on an activity with active passports now shows
the confirm screen; "Archive silently" leaves passports/uses untouched with no
email; "Archive and check in" zeroes `uses_remaining`, creates a `Redemption`,
and sends the `redeemPass` email (confirmed via `EmailLog`, result `SENT`).

## 2. "Archive" action in the Activities list does nothing — FIXED

The row menu's Archive link pointed at the same URL as Edit. Now wired via
`checkAndArchiveActivity()` (same pattern as the existing delete-confirmation
flow): checks for active passports, then either routes to the confirm screen
above or shows a lightweight archive-confirm modal for activities with none.

Verified live: Archive from the activities list now correctly opens the
confirm screen when active passports exist.

## 3. Follow-up: the "confirm screen" from #1 was a separate ugly page — FIXED

First pass at #1 reused the existing standalone `confirm_archive_activity.html`
page as-is (just relabeled it) instead of questioning why a confirmation ever
navigated to its own page instead of a modal like everywhere else in this app.
Run through the `impeccable` skill and redone properly:

- Both entry points (Activities list Archive action, and the Edit Activity
  page's Active/Archived toggle+Save) now show a real in-page Bootstrap modal
  matching the exact house style already used by `#activityDeleteModal` /
  `#cannotDeleteModal` — no page navigation, generic h3 title with the activity
  name in the body text instead of an awkwardly quoted heading.
- The Edit Activity page's toggle+Save previously always redirected through
  the standalone page (discarding it wasn't reachable at all — see #1's root
  cause). Now, saving with the toggle set to Archived intercepts via JS,
  checks for active passports, and shows the modal in place; choosing an
  option feeds back into the *same* form submission, so any other edits made
  on that page (name, description, passport types, etc.) are saved together
  with the archive decision in one request — nothing gets silently discarded.
- Found and fixed a real bug introduced during this pass: a Jinja variable
  (`current_status`) was set inside `{% block content %}` and read from
  `{% block scripts %}` — those are separately scoped in Jinja, so it rendered
  as `Undefined` and crashed the New/Edit Activity page (`TypeError: Object of
  type Undefined is not JSON serializable`). Fixed by re-deriving the value
  inline in the scripts block instead of relying on cross-block scope.
- The standalone page (`confirm_archive_activity.html`) still exists as the
  backing route for the tier-limit-exceeded flow (a separate, page-based flow)
  and as a graceful fallback; its title was cleaned up to match the same
  pattern (generic heading, name below) rather than left ugly.

Verified live: both entry points now show the modal with no page navigation;
tested the Edit Activity path end-to-end with a simultaneous description edit
+ "Archive and check in" — activity archived, description saved, passport
checked in, and the `redeemPass` email sent, all in one request. Ran the
skill's mechanical design detector on the changed templates (clean, aside from
one unrelated pre-existing finding) and the full test suite (49/49 pass).
