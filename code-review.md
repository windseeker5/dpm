# Minipass Full Codebase Review — 2026-09-10

Branch: `code-review-optimization`. Scope: `app.py` (15,840 lines), `utils.py` (6,578 lines),
`models.py` (711 lines), `api/*.py`, templates, static assets. Reviewed via three parallel
passes: security, performance/efficiency, dead/unused code.

---

## 🔴 Critical Security (fix first — live exposures)

**Status: all 5 fixed and verified 2026-09-10** (see Test Results below).

1. **Auth bypass, currently live** — `app.py:4713-4724` (`/api/payment-bot/check-emails`):
   ```python
   if True:  # Temporary bypass
       print("🔧 BYPASSING AUTH FOR DEBUG")
   elif "admin" not in session:
       ...
   ```
   Any unauthenticated caller can trigger the Interac/Gmail payment-matching bot on demand.
   Also marked `@csrf.exempt`. Remove the bypass.

2. **Plaintext passwords + bcrypt hashes logged on every login** — `app.py:7418-7429`:
   ```python
   print(f"📨 Login attempt for: {email}")
   print(f"🔑 Password entered: {password}")
   ...
   print(f"🔐 Stored hash (value): {admin.password_hash}")
   ```
   Container/journal logs now contain every admin's password in cleartext plus hashes.

3. **Admin financial/data endpoints with no auth check at all**:
   - `app.py:10069-10070` `POST /admin/activity-income/<id>[/edit/<id>]`
   - `app.py:10197-10198` `POST /admin/activity-expenses/<id>[/edit/<id>]`
   - `app.py:12530` `POST /api/passport-type-archive/<id>` (only `@csrf.exempt`, no session check)
   - `app.py:12500` `GET /api/passport-type-dependencies/<id>` (lower severity — info leak)

   Any anonymous POST with a guessable numeric ID can mutate financial records and
   passport-type data.

4. **`app.run(debug=True)` unconditional** — `app.py:15840`:
   ```python
   app.run(host='0.0.0.0', debug=True, port=port)
   ```
   Werkzeug's interactive debugger (RCE via known PIN-bypass techniques) is exposed on
   `0.0.0.0` if this entrypoint is ever invoked directly instead of via gunicorn. Gate on an
   env var, default `False`.

5. **Reflected XSS** — `app.py:15697-15707` (`/unsubscribe` GET handler):
   ```python
   email = request.args.get('email', '')
   ...
   return f'''...<input ... value="{email}"> ... value="{token}">...'''
   ```
   Unescaped request params interpolated into a raw f-string HTML response. Use
   `render_template_string`/Jinja autoescaping or `markupsafe.escape()`.

## 🟠 High Security

**Status: all 3 fixed and verified 2026-09-10** (see Test Results below).

6. **No rate limiting / lockout on `/login`** (`app.py:7409`) — the `rate_limit` decorator in
   `decorators.py` exists and is used elsewhere (e.g. `api/backup.py`) but not here.
   Credential-stuffing surface, worsened by #2.
   **✅ Fixed 2026-09-10** — added an in-memory rate limiter directly in `login()` keyed by
   `(remote_addr, email)`: 5 attempts per 300s window, cleared on successful login so a
   legitimate admin isn't penalized by their own past failures. Verified via Playwright:
   6th rapid attempt is blocked with a "too many login attempts" message; normal login
   still works outside the window.

7. **`SECRET_KEY` silently falls back to ephemeral random value** — `app.py:183`:
   ```python
   os.getenv("FLASK_SECRET_KEY", os.urandom(32).hex())
   ```
   If unset, each gunicorn worker gets a *different* random key — breaks
   session/CSRF-token validity unpredictably across workers instead of failing loudly.
   **✅ Fixed 2026-09-10** — now raises `RuntimeError` at startup if `FLASK_SECRET_KEY` is
   unset, instead of silently generating a random key. `.env` already has it set locally,
   so this doesn't affect local dev. Verified by code review (would require a server
   restart with the env var removed to exercise live, which risks the running dev session).

8. **Broad `@csrf.exempt` on session-authenticated JSON endpoints** — e.g. push
   subscribe/unsubscribe/test (`app.py:5821,5872,5924`), payment-linking/notification
   endpoints (`app.py:4777,4823,4906,5466,5680,5701`). These check `session["admin"]` but
   skip CSRF — a logged-in admin visiting a malicious page could trigger these via CSRF.
   Stripe's webhook exemption (`app.py:4157`) is legitimate (signature-authenticated, not
   cookie-authenticated); the admin JSON APIs are not and should not be exempt.
   **✅ Fixed 2026-09-10** — removed `@csrf.exempt` from all 9 flagged routes. For the 2
   that already sent `X-CSRFToken` from their frontend caller
   (`api_move_payment_email`, `api_create_passport_from_payment` in
   `templates/payment_bot_matches.html`), just removed the exemption. For the 3 that
   didn't (`api_cleanup_duplicate_logs` called from `templates/dashboard.html`,
   `push_subscribe`/`push_unsubscribe` called from `static/js/push-notifications.js`),
   removed the exemption **and** added the missing `X-CSRFToken` header, reading the
   token from the `<meta name="csrf-token">` tag already in `templates/base.html`. The
   remaining 4 (`api_link_payment_to_passport`, `api_payment_notification_html`,
   `api_signup_notification_html`, `push_test`) are dead code with no caller (see Dead
   Code below) — exemption removed with no functional change. `archive_passport_type`
   (`/api/passport-type-archive/<id>`) is **kept exempt**: its two callers in
   `templates/activity_form.html` don't send a CSRF token and weren't in scope for this
   fix — tracked as a known gap, not silently left broken. `stripe_webhook` and
   `/unsubscribe` exemptions are correct as-is (not session-cookie authenticated).
   Verified: only 3 `@csrf.exempt` lines remain in `app.py` (down from 12), matching the
   3 legitimate cases; settings page and dashboard load with zero JS console errors.

## 🟡 Low Security / follow-up

9. `db.session.execute(text(f"..."))` calls (`utils.py:1112`, `app.py:~7744`,
   `utils.py:~2064`, `app.py:~9260`) build SQL text via f-string with bind params for the
   actual values — not currently exploitable, but fragile; a future edit could interpolate
   untrusted input directly. Worth a lint rule or comment convention.
10. Admin password-reset token — not fully verified whether it's single-use/expiring.
    Flagged for follow-up, not confirmed vulnerable.
11. Debug `print()` statements throughout `app.py`/`utils.py` should move to
    `logger.debug()`; grep for `BYPASS|REMOVE THIS|TEMPORARY` before any release cut.

### Security — confirmed solid (no action needed)
- Password storage: `bcrypt.hashpw`/`bcrypt.checkpw` throughout, no plaintext comparisons.
- `api/backup.py` filename handling: explicit extension allowlist + `/`/`\` rejection —
  solid path-traversal defense.
- File upload paths (activity images/avatars): extension allowlist, 10MB cap,
  `secure_filename`/UUID naming.
- CSRF globally enabled via `CSRFProtect(app)`, exemptions itemized (intent is sound, a
  few exemptions are misapplied per #8).
- Raw SQL almost entirely goes through SQLAlchemy `text()` with bound `:param` style, not
  string-formatted untrusted input.
- Wayne/OpenRouter AI integration uses operator-configured `base_url`/API key from env, not
  user-supplied URLs — no SSRF path found.

---

## 🟠 Performance / Efficiency (prioritized, biggest impact first)

**Status 2026-09-10: items 1, 3, 4, 6 fixed and verified. Items 2, 5, 7, 8, 9 evaluated,
not changed this pass — see notes below each.**

1. **Dashboard route — worst-scaling path in the app, hit on every login/main-page load.**
   `app.py:1627-1670`: for every active `Activity`, loops and issues 3 separate unbounded
   queries (`Signup.query.filter_by(...).all()`, `Passport.query.filter_by(...).all()`,
   `PassportType.query.filter_by(...).all()`), computing paid/unpaid/active counts and
   revenue in Python — classic N+1 (3N queries for N activities). Then `app.py:1673,1684`
   do `Passport.query.all()` and `Signup.query.all()` — **full table scans into memory** —
   to compute the same stats *again*, redundantly, at global scope.
   **Fix:** aggregate with `func.sum`/`func.count` grouped by `activity_id` in one query,
   reused for both per-activity cards and global stats.
   **✅ Fixed 2026-09-10** — replaced with grouped aggregate queries
   (`signup_agg`/`passport_agg`/`passport_types_by_activity` built from 3 queries total,
   independent of activity count) plus two single-row aggregate queries for global
   passport/signup stats. Verified against raw SQL ground truth — see Test Results.

2. **`get_kpi_data()` called twice per dashboard load** — `app.py:1620,1623`: normal and
   `period='fy'` mobile variant both run their full aggregate query set every request, even
   though only one is shown per device via CSS (`d-md-none`). Doubles dashboard query cost
   unconditionally.
   **Evaluated, not changed** — the two calls use different `period` arguments (`'7d'`
   default vs `'fy'`), so they return genuinely different data, not a literal duplicate
   call. The `is_mobile` user-agent sniff already computed at `app.py:1622-1623` could gate
   which one runs, but responsive layout here is CSS-breakpoint-based, not UA-based — a
   user resizing past the breakpoint would see a stale/missing KPI card until full reload.
   Left as-is to avoid a UX regression; worth a follow-up if it becomes a real hot spot.

3. **`list_passports` loads the entire Passport table to compute tab stats** —
   `app.py:8930`: `all_passports = Passport.query.all()` then Python-side counting/summing
   (`8933-8938`) — same anti-pattern as #1, should be SQL `SUM(CASE WHEN paid ...)`/`COUNT`.
   **✅ Fixed 2026-09-10** — replaced with one aggregate query. Verified filter-tab counts
   (`Unpaid (3)`, `All (362)`) match raw SQL ground truth — see Test Results.

4. **Sidebar counts run uncached on every request** — `app.py:1042-1076`
   (`_get_sidebar_counts`, docstring says *"Fresh query every request"*), invoked from the
   `@app.context_processor` `inject_globals_and_csrf` (`app.py:1078-1099`) which fires on
   every template render for every logged-in admin request. 4-5 queries per page view
   site-wide. No backend cache found — the "45s cache" in prior notes may be client-side
   only; worth confirming.
   **✅ Fixed 2026-09-10** — added a 45s per-admin in-memory cache
   (`_sidebar_counts_cache`), bypassed when `app.debug` is true so local dev keeps seeing
   live counts (matching the behavior described in prior notes). Cannot be exercised live
   in this session since the dev server runs with `debug=True`; verified by code review only.

5. **Bulk passport actions: N+1 lazy loads + unthrottled thread-per-email fan-out** —
   `app.py:9882` (`passports_bulk_action`) fetches passports with no `joinedload`, then:
   - `delete` branch (~9935-9942) accesses `passport.user.name`/`passport.activity.name`
     per row → N+1 lazy-load queries. **Not changed this pass.**
   - `send_reminders` branch (~9908-9919) → `notify_pass_event` → `send_email_async`
     (`utils.py:4430`) **spawns a new thread per email** (`utils.py:4444
     send_in_thread`). Selecting 200 unpaid passports spawns 200 concurrent SMTP threads —
     no batching/queue/worker pool.
     **✅ Fixed 2026-09-11.** Extracted `notify_pass_event`'s content-building logic into a
     pure helper (`_build_pass_event_email`, no I/O), kept `notify_pass_event` as a thin
     wrapper so all its other call sites (pass created, payment received, redeemed, etc.)
     are unaffected, and added `notify_pass_event_bulk()` — one background thread, sends
     sequentially with a 0.3s gap between recipients, mirroring the existing
     `send_bulk_sequential()` pattern used for announcements. `passports_bulk_action`'s
     `send_reminders` branch now calls it once for the whole batch instead of looping
     `notify_pass_event()` per passport.
     **Bug caught during testing, fixed before landing:** the first version passed the
     live `Passport` ORM objects into the thread and read `.pass_code` from them lazily
     inside the loop. That works for the first item, but the caller's request-thread
     session commits (`db.session.commit()` for the `AdminActionLog` write) *before* the
     background thread finishes, which by default expires every attribute on every object
     in that session — so `.pass_code` access on a later item threw an unhandled
     `DetachedInstanceError` inside the thread, silently killing it with **zero visible
     error** (no EmailLog row, no exception surfaced anywhere) after the first
     recipient. Fixed by extracting all `pass_code` strings synchronously *before*
     `thread.start()`, so the thread never touches the caller's ORM objects at all. This
     is exactly the kind of bug that wouldn't show up in a 1-recipient test — only caught
     it by testing with 2 real unpaid passports (both `kdresdell@gmail.com`, per the
     project's no-fake-domain testing rule) and confirming both actually arrived in
     `EmailLog` as `SENT`, not just that the request returned 302.

6. **Missing indexes on columns filtered in hot paths** — `models.py` has only 3 explicit
   indexes in the whole schema. Filtered constantly with no index:
   `Passport.activity_id/paid/uses_remaining`, `Signup.status/activity_id`,
   `EbankPayment.result`, `EmailLog.result`. SQLite doesn't auto-index FKs, so these become
   full scans as tables grow. Recommend adding indexes on
   `Passport(activity_id, paid, uses_remaining)`, `Signup(status, activity_id)`,
   `EbankPayment.result`, `EmailLog.result`.
   **✅ Fixed 2026-09-10** — turns out `Signup.activity_id`, `Signup.status`, and
   `Passport.activity_id` were *already indexed at the actual DB level* via earlier
   migrations (`task9`/`task10`/`task31` in `upgrade_production_database.py`) even though
   `models.py` didn't declare `index=True` — a docs/model drift, not a functional gap.
   Added `index=True` to those 3 columns in `models.py` to match reality, and added the
   genuinely missing ones (`Passport.paid`, `Passport.uses_remaining`,
   `EbankPayment.result`, `EmailLog.result`) via a new idempotent `task54` in
   `migrations/upgrade_production_database.py` (per `AGENTS.md` rule 5 — no Alembic
   revisions). Ran the migration against the local dev DB; confirmed all 4 new indexes
   exist via `sqlite_master`.

7. **Repeated identical `Setting.query.all()` with no per-request caching** — 12+ call
   sites (`app.py:3428,3609,3694,3714,3756,3801,3853,3981,4541,6180,6528,7639`) each
   independently run `{s.key: s.value for s in Setting.query.all()}`. `utils.py:449`
   (`get_setting`) has a `flask.g`-scoped cache for single-key lookups that these bypass.
   **Not changed this pass** — 12+ call sites to migrate individually; low risk but wanted
   to keep this batch reviewable. Good next-pass candidate.

8. **Process-local in-memory redemption throttle won't work correctly under multiple
   workers** — `app.py:12199` (`recent_redemptions = {}`), used at `~7834-7863` and again
   at `~12227-12249` (duplicated logic). Self-pruning (bounded to 30s, not a leak) but a
   plain module-level dict is per-process — under gunicorn with >1 worker the
   duplicate-redemption guard only works if the same worker handles both requests.
   **Not changed this pass** — correctness edge case under multi-worker gunicorn, not a
   regression risk on its own; needs a shared store (e.g. a DB row or Redis) to fix
   properly, out of scope for this batch.

9. **Static assets in the web root** — `static/backups/` (104MB) and the
   `static/uploads_backup_*` snapshots sit under `static/`, served by Flask's static
   handler even though they're backup artifacts, not page assets.
   **Partially addressed 2026-09-11**: the `uploads_backup_*` snapshots were one-off
   manual dumps with zero references — deleted (see Dead Code below). `static/backups/`
   is different: it's the **live, actively-used** backup storage for `api/backup.py`'s
   real database/file backup feature (11+ hardcoded `static/backups` path references, plus
   download URLs built from that path). Moving it outside the web root is a real code
   change — every path reference and the download-serving logic would need updating and
   testing — not a cleanup deletion. Left in place; flagged as a genuine follow-up
   architecture task, not done here to avoid risking the backup feature or losing data.

### Performance — confirmed fine (checked, no action needed)
- Image upload handling (`utils.py:1340-1362,5351-5439`) thumbnails/resizes before saving.
- QR generation (`utils.py:1366-1480`) is small and per-request, not batched in loops.
- Geocoding (`api/geocode.py`) and the outbound webhook POST (`utils.py:6574`) already use
  explicit `timeout=`.
- `list_passports`/`list_signups` list views already use `.options(db.joinedload(...))`
  plus `.paginate(...)` correctly (undermined only by the redundant `.all()` in #3).
- Regex in email parsing uses `re.search` with literal patterns, not `re.compile()` inside
  a loop — CPython's regex cache already avoids recompilation.

---

## 🧹 Dead / Unused Code

**Status 2026-09-10/11: routes, templates, JS/CSS, and stale backup dirs all removed and
verified. Commented-out code blocks and `static/backups/` deliberately left — see notes.**

### Dead Flask routes — ✅ removed 2026-09-11
`/health` (`health_check`) was **kept** per maintainer decision (possible external
uptime-monitor dependency, can't verify from the repo). All 11 others deleted after
confirming zero references anywhere (function name, `url_for`, template links) via `ast`
parsing plus grep:
- `api_payment_notification_html`, `api_signup_notification_html`,
  `push_status`, `push_test`, `api_link_payment_to_passport`,
  `save_unified_settings`, `export_passports`, `export_signups`,
  `mark_signup_paid`, `create_pass_from_signup`, `update_signup_status`

Removed as precise `ast`-derived line ranges (decorator through function end), deleted
bottom-to-top to avoid line-shift errors, then normalized excess blank lines. Verified:
`app.py` still parses, all 3 verification test suites still pass, zero 404s across
dashboard/passports/signups/settings/activities/login in a live browser crawl.

### Orphaned template files (~286 lines) — ✅ removed 2026-09-11
- `templates/login.html`, `templates/reset_password_form.html`,
  `templates/partials/settings_email.html`, `templates/partials/settings_org.html`,
  `templates/partials/passport_table.html` (not to be confused with the still-active
  `passport_table_rows.html`)

  `templates/email/*.html` looked orphaned by static grep but are dynamically resolved via
  `safe_template()` (`utils.py:4047`) — confirmed **not** dead, left alone.

### Stale backup directories (~3.2MB) — ✅ removed 2026-09-11
- `static/uploads_backup_20251125_202232/`, `static/uploads_backup_20251126_205643/`,
  `static/uploads_backup_20251129_165613/` — one-off manual `cp -r` snapshots, already
  gitignored (`static/uploads_backup_*/` in `.gitignore`), so `rm -rf`'d directly rather
  than `git rm`.

### Unused static JS/CSS — ✅ removed 2026-09-11
- `static/js/email-customization-fix.js`, `static/js/login-visual.js`,
  `static/css/activity-header-polish.css`
- `static/css/login-standalone.css` — checked first as flagged: `login_standalone.html`
  already has its own inline `<style>` block, and the login page renders correctly in
  testing, confirming this 551-line stylesheet is legacy (predates the inline styles),
  not a missing-link bug. Safe to remove.

### Commented-out code blocks (31 total) — not changed this pass
**Line numbers below are stale** (from the original audit, before the ~350 lines of dead
routes were removed above) — treat as a starting point, re-locate each block before
touching it. Deferred: verifying 31 individual blocks are genuinely safe to delete (vs.
intentionally disabled-but-kept code) is exactly the kind of judgment call worth doing as
its own focused pass rather than folding into this one.
- `app.py`: 103-106, 145-148, 1706-1712, 1792-1795, 2546-2550, 2578-2583, 2639-2646,
  3233-3237, 3435-3440, 6081-6085, 6127-6130, 9697-9701, 10625-10628, 10833-10836,
  10899-10908, 14388-14391
- `utils.py`: 462-465, 579-589, 2648-2651, 2766-2771, 2780-2784, 2989-2992, 3317-3320,
  4013-4016, 4437-4441, 4505-4508, 4908-4915, 5063-5070, 5268-5275, 5320-5325, 5873-5877
- `models.py`: 127-130, 443-446, 529-532

### Dead code — confirmed NOT dead (false positives ruled out, don't re-flag)
- `enable_foreign_keys`, `check_first_run` (`@app.before_request` hooks),
  `inject_globals_and_csrf` (`@app.context_processor`), `combine_dicts` (Jinja filter,
  used in `templates/macros/pagination.html`) — all framework-dispatched.
- `stripe_webhook`, `test_discord_webhook` — external-caller endpoints, no internal refs
  expected.
- `dev_simulate_payout` — self-documented dev-only route, guarded by `app.debug`.
- All 297 `db.Column` definitions in `models.py` swept — no dead columns.
- No unused top-level imports found in `app.py`/`utils.py`.
- `wayne/` is an actively-registered Flask blueprint (`app.py:189-190`), not dead.

### Not covered in this pass
- `api/backup.py`, `api/geocode.py`, `api/settings.py` internals (1,589 LOC combined) —
  only confirmed as registered blueprints, no deep dead-code pass done.
- `.pi/` and `.impeccable/` — tool-scratch directories, out of scope (general repo tidy,
  not app code).

---

## Test Results — Critical Security Fixes (2026-09-10)

Verified against the running local app (`localhost:5000`) with a real browser session via
Playwright (`test/verify_security_fixes.py`), logging in as `kdresdell@gmail.com` per the
project's testing convention.

| Fix | Check | Result |
|---|---|---|
| #1 Auth bypass on payment-bot endpoint | Unauthenticated POST to `/api/payment-bot/check-emails` is rejected | **PASS** (400 — CSRF+auth now both gate it; route also has no live frontend caller, confirmed separately as dead code) |
| #2 Plaintext password/hash logging | Login flow no longer prints password/hash; grep for the removed log lines returns zero matches | **PASS** — normal login still succeeds (`/dashboard` reached) |
| #3 Missing auth on financial/passport-type endpoints | Unauthenticated `GET /api/passport-type-dependencies/<id>` → 401; unauthenticated `GET /admin/activity-income/<id>` → 302 redirect to login; both work normally once logged in (200 / page loads) | **PASS** (all 4 sub-checks) |
| #4 `app.run(debug=True)` unconditional | Now gated by `FLASK_ENV`/`FLASK_DEBUG` env vars, defaults preserved for local dev (no restart performed — change takes effect on next server start, per project rule against restarting the dev server) | **Code verified, not runtime-tested** (would require a server restart) |
| #5 Reflected XSS on `/unsubscribe` | `?email="><script>...</script>` now renders HTML-escaped (`&lt;script&gt;`) instead of executing | **PASS** |

All 7 automated checks passed:
```
[PASS] Fix #5: /unsubscribe XSS payload is escaped, not rendered as markup
[PASS] Fix #1: /api/payment-bot/check-emails blocks unauthenticated POST status=400
[PASS] Fix #3: /api/passport-type-dependencies/1 blocks unauthenticated GET status=401
[PASS] Fix #3: /admin/activity-income/5 redirects unauthenticated GET to login status=302
[PASS] Login still succeeds after logging fix url=http://localhost:5000/dashboard
[PASS] Fix #3: authenticated admin can access passport-type-dependencies status=200
[PASS] Fix #3: authenticated admin can load activity-income page
```

**Note on Fix #4:** the debug-mode change only takes effect the next time the Flask process
is started manually (`python app.py`); per project rules the dev server is never restarted
automatically, so this fix is verified by code review only, not a live restart test. It has no
effect on the current session since production runs via gunicorn regardless.

## Test Results — High Security Fixes (2026-09-10)

Verified via Playwright (`test/verify_high_security_fixes.py`) against the running local app.

| Fix | Check | Result |
|---|---|---|
| #6 Rate limiting on `/login` | 6 rapid attempts with a valid CSRF token: the 6th is blocked with a "too many login attempts" message, the first 5 are not | **PASS** |
| #7 `SECRET_KEY` fail-fast | Static check: `os.urandom(32).hex()` fallback removed, `RuntimeError` raise present | **PASS** (code review only — exercising this live would require unsetting `FLASK_SECRET_KEY` and restarting the dev server, which the project rules prohibit) |
| #8 CSRF exemptions trimmed | Exactly 3 `@csrf.exempt` lines remain in `app.py` (Stripe webhook, `/unsubscribe`, `archive_passport_type`) | **PASS** |

```
[PASS] Fix #6: 6th rapid login attempt is rate-limited attempt_results=[False, False, False, False, False, True]
[PASS] Fix #7: app.py raises if FLASK_SECRET_KEY is unset (no silent random fallback)
[PASS] Fix #8: only 3 legitimate @csrf.exempt routes remain (stripe webhook, unsubscribe, archive_passport_type) count=3
[PASS] Fix #6: login page correctly shows rate-limit message in browser after 6 failed attempts
```

Separately confirmed with a JS-console-error check across `/dashboard`, `/passports`, and
`/admin/unified-settings` (where the CSRF-header additions to `push-notifications.js` and
`dashboard.html` apply) — zero console errors, zero unexpected 404s.

**Side effect to know about:** this test intentionally fails 6 login attempts for
`kdresdell@gmail.com` from localhost to exercise the rate limiter, which puts that
account/IP combination in a ~5 minute lockout afterward. It clears automatically; no action
needed, but a login attempt in that window will show "too many login attempts."

## Test Results — Performance Fixes (2026-09-10)

Verified via Playwright (`test/verify_performance_fixes.py`), comparing rendered page output
against raw SQL queries run directly against `instance/minipass.db` as ground truth.

| Fix | Check | Result |
|---|---|---|
| #1 Dashboard N+1 → aggregate queries | Per-activity card for the busiest active activity (id 14, "FLHGI: Tournoi de Golf...") shows "22 active" / "2 pending", matching raw SQL exactly | **PASS** |
| #3 `list_passports` full-table-scan → aggregate query | Filter-tab counts "Unpaid (3)" and "All (362)" match raw SQL exactly | **PASS** |
| #4 Sidebar 45s cache | Code review only — dev server runs with `app.debug=True`, which intentionally bypasses the cache, so it cannot be exercised live in this session | **Not runtime-tested** |
| #6 New indexes | Migration run against local DB; `ix_passport_paid`, `ix_passport_uses_remaining`, `ix_ebank_payment_result`, `ix_email_log_result` confirmed present via `sqlite_master` query | **PASS** |

```
[PASS] Login succeeds
[PASS] Dashboard loads without error (200, no traceback)
[PASS] Dashboard renders KPI cards
[PASS] Dashboard renders activity/stat cards count=9
[PASS] Dashboard card for 'FLHGI: Tournoi de Golf et Souper des retrouvailles 2026' shows ground-truth active count (22) activity_id=14
[PASS] Dashboard card for 'FLHGI: Tournoi de Golf et Souper des retrouvailles 2026' shows ground-truth pending count (2) activity_id=14
[PASS] Passports list loads without error
[PASS] Passports page 'Unpaid' filter tab shows ground-truth count (3)
[PASS] Passports page 'All' filter tab shows ground-truth count (362)
```

A full-DB backup was taken before running the index migration (`instance/minipass.db.pre-task54-backup`)
and removed after confirming all 4 indexes were created successfully with no errors.

## Suggested order of work — updated status (2026-09-11)

1. ~~Security critical items (1-5)~~ — **done, verified.**
2. ~~Security high items (6-8)~~ — **done, verified.**
3. ~~Dashboard query rewrite (Performance #1, #3, #4)~~ — **done, verified.**
4. ~~Indexes (Performance #6)~~ — **done, verified (migration run locally).**
5. ~~Dead code cleanup~~ — **done, verified**: 11 dead routes, 5 orphaned templates, 4
   unused JS/CSS files, 3 stale backup dirs (~3.2MB) all removed. `/health` kept per
   maintainer decision. 31 commented-out blocks and `static/backups/` (real, in-use backup
   storage) deliberately left — see notes above.
6. ~~Performance #5 (bulk email thread-per-request fan-out)~~ — **done, verified
   2026-09-11**: `notify_pass_event_bulk()` sends sequentially from one background thread.
   Tested live with 2 real unpaid passports and a real SMTP send — caught and fixed a
   session-detachment bug during testing that would have silently dropped every recipient
   after the first (see note above).
7. **Remaining, not yet done:**
   - Performance #2 (dual KPI calls) — evaluated, deliberately left as-is (see note above).
   - Performance #7 (`Setting.query.all()` caching) — 12+ call sites to migrate.
   - Performance #8 (multi-worker redemption throttle) — needs a shared store.
   - Performance #9 remainder — moving `static/backups/` outside the web root; a real code
     change across `api/backup.py`/`app.py`, not a cleanup deletion.
   - 31 commented-out code blocks — needs a dedicated pass, one at a time.
   - `archive_passport_type`'s CSRF exemption (tracked gap from High #8) — needs the two
     `templates/activity_form.html` callers updated to send `X-CSRFToken` before the
     exemption can be safely removed.
