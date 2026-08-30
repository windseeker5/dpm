# Email Template Redesign — Handoff Context

**Read this before touching any email template code.** Status as of 2026-08-28, end of session 2.

## Current state: all 7 templates done and consistent

Every email (`newPass`, `redeemPass`, `latePayment`, `paymentReceived`, `signup`,
`signup_payment_first`, `survey_invitation`) now shares one visual language and has been
verified with real SMTP sends to a real inbox (not just the browser preview tool — see
**Testing** below for why that distinction matters).

### What the design actually is, top to bottom
1. **Photo header band** — real activity photo, full-width `<img>`, followed immediately (no
   gap, no overlay) by a solid ink-colored bar carrying a short eyebrow + the activity name.
   **This is not what the originally-approved mockup showed** (that had the caption overlaid on
   the photo with a gradient scrim) — real Gmail sends (web, iOS, Android) broke that, because
   Gmail does not support `position:absolute`/`relative` in HTML email at all. Do not "fix" the
   solid bar back toward the mockup's overlay — it will break in real inboxes again. See
   `photo_band()` in `templates/email/components.html` for the full reasoning, including the
   separate contained/no-overlay treatment for the generic mascot icon (used when an activity
   has no real photo — `hero_is_photo` controls which branch renders).
2. **Org identity** — logo (56px) + org name, plain, no card.
3. **Message** — `intro_text` + `custom_message` + `conclusion_text` as one flowing paragraph.
   `custom_message` is wired in now (was a real gap before this session). `<strong>` tags inside
   this text render near-black against the grey body text (`.mp-message strong` rule in
   `_base.html`) — not just bold-but-still-grey.
4. **Participant identity** — "PARTICIPANT" label (black, not grey — see below) + name + email.
5. **Facts, one column**: Montant → Statut (pill) → Crédits → Lieu. Do not also repeat the
   location inside the message paragraph — it's redundant with the Lieu row and was flagged
   twice as a bug before it stuck.
6. **QR code** — tight 1px black frame, generated at (or very near) its exact display size
   (165×165, `EMAIL_QR_BOX_SIZE` in `utils.py`) so nothing has to rescale it.
7. **Séances card** (conditional) then **Historique card** — same shared component
   (`section_card()`), light neutral-grey background (`C_WELL = #f6f6f7`, not blue-tinted),
   **no border**, and its section title (black, not grey) sits *above* the card, not inside it —
   this is the OpenRouter-reference convention the user asked to standardize on. Every section
   title in the system (Participant, Séances, Historique, Instructions de paiement) shares this
   exact typography: 11px / 700 / uppercase / 0.07em letter-spacing / near-black (`C_INK`).
8. **Instructions de paiement** (signup_payment_first only) — same title-above-card convention,
   a light-grey card containing a one-line instruction, the Interac logo, and Montant/Destinataire
   as rows. This used to be a bare, untitled well box relying on the message paragraph to explain
   itself — now it's self-contained like everything else.
9. **CTA button** — solid ink, full width, label pulled from the real `cta_text` context field
   (do NOT hardcode a label — `latePayment`'s is deliberately different, "Effectuer le paiement"
   not "Voir mon passeport en ligne", since that email is about an unpaid pass with nothing to
   view yet). `href` is always `pass_url` (the real per-passport link), never `cta_url` (a
   generic non-personalized default like `/my-passes`) — there's a comment at each call site
   about this, don't "helpfully" wire `cta_url` in.

### Hard rules (still true, established the hard way)
- No dark mode. No decorative chips/pills/dots/colored accent bars — color only where
  semantically load-bearing (the paid/unpaid status pill).
- Type scale: 4 sizes / 2 weights inside the card — 11 / 13.5 / 16 / 22px, weights 400 and 700.
- No `position:absolute`/`relative` anywhere in email HTML. Ever. (See photo band above.)
- Ground every example in real DB data, not invented content — this caught the "4 sur 1"
  credits bug, the location-shown-twice bug, and the hero-defaults-to-mascot bug below.

## Real bugs found and fixed this session (not just style)

These were found by testing against real data and real Gmail sends, not by inspection:
- **`get_activity_hero_image()` priority order was backwards** (`utils.py`) — the shipped
  generic mascot PNG was checked *before* the activity's own real photo, so every email for
  every activity showed the mascot regardless of whether a real photo existed. Reordered:
  custom upload → real activity photo (now the default) → mascot only if there's truly no photo.
- **`DetachedInstanceError` race in `send_email_async()`'s background thread** (`utils.py`) —
  it re-queries `Passport` fresh in its own session before rendering (this is why `pass_data`
  can't be faked/flushed-not-committed by a test script and expect it to show up — see Testing).
- **`notify_signup_event()` and `send_survey_invitations()` never set `owner_logo_url` or
  `hero_is_photo`** in the context they hand to `send_email_async()` — the org logo has been
  silently missing from every real signup/survey email, and the hero always defaulted to
  "treat as photo" even for the mascot icon. Fixed in `utils.py` and both occurrences in
  `app.py`.
- **`cta_text`/`cta_url` existed in `config/email_defaults.json` with real sanitization code
  behind them but were never actually read by any template** — `cta_text` is wired in now,
  `cta_url` deliberately still isn't (see CTA button note above).
- **`credit_line()` "4 sur 1" bug** — a quantity-purchase passport type (`sessions_included=1`,
  multiple tickets bought) showed a nonsensical "X sur 1" fraction; now only shows the fraction
  when the total is a real multi-session count (`> 1`).

## Where the code lives
- `templates/email/_base.html`, `components.html` — shared layout/macros. `pass_card()`/
  `session_list()`/`next_session()`/`history_table()` (the old pre-redesign macros) are gone —
  confirmed zero remaining callers before deleting them.
- `templates/email/<type>.html` — the 7 thin per-type templates.
- `config/email_defaults.json` — default subject/title/intro/conclusion/cta text per type. Note:
  **editing this file does not retroactively update existing activities** — each activity gets
  its own frozen snapshot of this JSON at creation time, stored in `activity.email_templates`.
  This bit us twice this session (the location-in-message fix had to be re-applied directly to
  the test fixture's stored copy after editing the shared defaults).
- `templates/pass.html` — the passport page. **Not yet synced to the new email design** — still
  pending, see punch list.
- `docs/EMAIL_TEMPLATE_SYSTEM.md` — **still stale**, describes the deleted 3-tier compiled
  pipeline. Still needs a rewrite, see punch list.

## Testing — read this before assuming a preview means anything

- `test/render_all.py` — renders all 7 templates to static HTML, fast sanity check for
  exceptions, but tells you nothing about how it looks in a real inbox.
- The `/activity/<id>/email-preview` browser route is useful for a quick visual check but is
  **same-origin** — it can't reveal anything Gmail's HTML sanitizer would strip (this is exactly
  how the `position:absolute` photo-overlay bug went unnoticed for a whole round). It also used
  to silently omit the Interac logo (missing `base_url` in its own context) — fixed, but a
  reminder that this tool's context-building is separately maintained from the real send path
  and can drift.
- **`test/send_real_email_preview.py` is the one that matters** — it sends real emails via real
  SMTP, with the real photo/logo/QR embedded as CID attachments (the only way they'll actually
  load in Gmail, since this dev environment's `SITE_URL` isn't publicly reachable). Key things
  to understand before using it:
  - It **writes real data** — it actually marks the fixture passport paid and actually redeems
    it (mirroring `mark_passport_paid()`/`redeem_passport_qr()` in `app.py` exactly) before
    firing `paymentReceived`/`redeemPass`, because the render path re-queries the real DB state
    — faking it in memory produces emails that contradict their own content (this happened, and
    it was ugly). Idempotent: re-running doesn't re-decrement credits or re-mark paid.
  - Default target is a **disposable fixture** ("Cours de Yoga du Mardi", activity id 15,
    passport `MP-a0ece8456173`) created solely for this purpose — **never point real-data writes
    at passport #402 (`MP-acae50029c26`) or anything else restored from the real LHGI production
    backup.** Pointing this script at anything other than the default fixture requires
    `--confirm-writes` specifically to prevent that mistake.
  - It only covers the 4 pass-style templates (`newPass`/`redeemPass`/`latePayment`/
    `paymentReceived`) plus a lifecycle ordering (create → late reminder while unpaid → mark
    paid → redeem). For `signup`/`signup_payment_first`/`survey_invitation`, there's no reusable
    script yet — this session sent real test copies with inline one-off Python (create a real
    Signup via the actual public signup form, or use the fixture Passport for survey), CID-embed
    the images the same way, and send. Worth turning into a proper script if this keeps coming up.

## Next session — punch list

1. ~~**Admin field consolidation**~~ — **Done.** `intro_text` + `conclusion_text` +
   `custom_message` are now a single `admin_message` field everywhere: the editing form
   (`templates/email_template_customization.html`), `config/email_defaults.json`,
   `utils_email_defaults.py`'s fallback, and every context-building call site in `utils.py` /
   `app.py`. Existing activities' already-saved 3-field text is handled by
   `utils.consolidate_admin_message()` (folds the legacy trio into `admin_message` at
   read/edit time, same concatenation order the layout always rendered them in) plus
   `task46_consolidate_admin_message` in `migrations/upgrade_production_database.py`, which
   does the one-time DB-wide sweep — same pattern as task45. Saving or resetting a template
   also lazily drops the legacy keys for that activity. Verified against the real dev DB
   (LHGI activities had legacy-shaped data; ran task46, admin UI showed the consolidated text
   correctly, save/reset round-tripped, rendered output byte-identical before/after).
2. ~~**Sync `templates/pass.html`**~~ — **Done, 2026-08-30, session 4.** Earlier commits
   (`ffe7f29`, `a3e24e3`) had already aligned *copy* with the email (money formatting,
   "Participation N", etc.) but predated the Aug 2026 visual redesign in
   `email/components.html` — the card still used a small circular avatar, stacked
   label-above-value pairs, and bordered white `.card` sections. This pass rebuilt the visual
   language to match, reusing Tabler's `card-img-top` where possible and adding new
   `.pass-*` classes (documented inline) for what Tabler has no native equivalent for:
   - Photo header band (`.pass-hero-photo`/`.pass-hero-contained` + `.pass-hero-caption` ink
     bar) replacing the avatar-in-card-header, mirroring `photo_band()`. Falls back to the
     activity logo, then the same letter-avatar treatment the page already used, when there's
     no real photo — no mascot asset exists on this surface, unlike email.
   - Participant identity block, mirroring `identity_block()`.
   - Facts as label-left/value-right divided rows (`.pass-rows`/`.pass-row`), mirroring
     `rows_block()` — Montant → Statut (new: a real pill, previously only shown as a badge
     next to the title, now removed from there to avoid duplication) → Crédits → Lieu (new
     row; `activity.location_address_formatted` was already available server-side but never
     rendered on this page).
   - QR now framed (`.pass-qr-frame`) with the pass_code printed below it in monospace,
     mirroring `qr_block()` — the code text was not shown on this page before.
   - Séances/Historique switched from bordered white `.card` to the title-above-well
     `.pass-section-title` + `.pass-well` pattern, mirroring `section_card()`.
   - Content ordering changed to match the email exactly: Participant → Facts → QR, stacked
     single-column (previously QR and Titulaire/Montant/Crédits sat side-by-side in a
     `flex-md-row`, which the new Facts-rows layout doesn't need — it's already responsive
     without a breakpoint).

   Found and fixed one real bug along the way, live in the dev DB: the Crédits row used the
   pre-fix, unguarded `{% if total_credits %}` check, so a quantity-purchase passport type
   (`sessions_included=1`, multiple tickets) rendered "1 sur 1" — the exact "X sur 1" bug
   `credit_line()` already fixed on the email side, just never ported here. Now guarded the
   same way (`total_credits > 1`). Caught via Playwright against a real unpaid passport in the
   dev DB (`MP-5b3b75346faf`), not by inspection.

   Ran `web-design-guidelines` after, which caught a real regression: the rewrite had turned
   the activity headline and the three section titles (Participant/Séances/Historique) into
   plain `<div>`s instead of the `<h3>` the original card-header/card-title markup used —
   fixed back to `<h3>` with margin resets in CSS instead of relying on `.card-title`. Also
   added explicit `width`/`height` on the two new `<img>` tags (hero photo, logo fallback) per
   the CLS guideline, even though a fixed-height CSS class already prevents any actual shift.

   Verified live via Playwright against `localhost:5000`: the fixture yoga activity (real
   photo, real location, paid, with history — `MP-a0ece8456173`) and a real unpaid golf
   passport (`MP-5b3b75346faf`, confirms the "Non payé" pill and the credits fix). Confirmed
   the admin 3-dot dropdown (Edit/Check In/Mark as Paid) still opens and positions correctly
   from its new spot in the ink bar. Confirmed responsive wrapping (headline, Facts rows) via
   a simulated 375px viewport — this session's Chrome extension couldn't resize the actual OS
   window under Hyprland's tiled WM, so this wasn't a real device test, just a CSS-injection
   approximation; worth a real narrow-device pass if anyone doubts it.

   **Not tested with real data, because none exists in this dev DB**: the letter/logo hero
   fallback (every activity here has a real photo) and the Séances section (no activity here
   has `uses_scheduling=1` with a real passport against it) — code-reviewed only, not
   click-tested. Worth a real pass if either situation comes up in production data.

   **Correction round, same session, right after the above.** The first pass above got the
   individual pieces right but missed the actual headline principle of the Aug 2026 redesign —
   "one continuous flowing document, no boxed sections" (see the redesign docblock at the top
   of `email/components.html`). It still rendered as three separate boxes: an org-branding
   header floating above the card as its own page element, then the main card, then Séances
   and Historique as their *own* separate `.card`s below it with gaps between them. The user
   caught this immediately from a screenshot — correctly furious that this doesn't match the
   email at all. Fixed:
   - Removed the standalone page-top org-branding header (`.pass-page-header` and its CSS)
     entirely.
   - Added the org identity row (56px logo + name, `.pass-org-logo-inline`) *inside* the main
     card, directly below the hero ink bar — same position and treatment as the email's org
     identity row.
   - Merged what were three separate `.card` elements into one continuous card: Séances and
     Historique are now `.pass-section-title`/`.pass-well` sections nested inside the same
     `card-body` as Participant/Facts/QR, not separate boxes with their own outer column div.
     (Introduced one div-nesting bug doing this — the Historique `.pass-well` wasn't closed
     before its `{% endif %}` — caught by a scripted open/close `<div>` tag count across the
     file before it shipped, not by rendering it and hoping.)

   Re-verified live via Playwright after the fix: logged-in admin view on the same fixture
   passport confirms one unbroken card from hero photo through Historique, and the 3-dot
   dropdown still opens and positions correctly from inside the ink bar.
3. ~~**Rewrite `docs/EMAIL_TEMPLATE_SYSTEM.md`**~~ — **Done, 2026-08-30, session 4.** Full
   rewrite (v3.0 → v4.0), grounded in the actual current code (route line numbers, function
   line numbers, and field names all read from source, not carried over from the old doc) —
   the old version described the deleted three-tier compile pipeline
   (`{type}_compiled/`/`{type}_original/`, `compileEmailTemplate.py`, `inline_images.json`)
   start to finish and listed only 6 templates (missing `signup_payment_first`). New doc
   covers: the shared `_base.html`/`components.html` macro architecture, the design language
   top-to-bottom (mirrors the numbered list at the top of this handoff), the two-tier hero
   priority order and why it was flipped, the `admin_message` consolidation, the full
   save/reset/preview/test-send routes with current line numbers, and a new section mapping
   `pass.html`'s classes 1:1 to their email macro counterparts (including the "one continuous
   card" rule, called out explicitly since that's the mistake made and fixed in item #2 above —
   worth a reader hitting this warning before repeating it).
4. ~~**Extend `send_real_email_preview.py` to the 3 non-pass templates**~~ — **Done, 2026-08-30,
   session 4.** `signup`/`signup_payment_first` now send off a real `Signup` row already in the
   dev DB (id 76, activity 15) — the script forces the template type rather than deferring to
   the fixture activity's actual `workflow_type`, so both get covered from one signup.
   `survey_invitation` needed a fixture that didn't exist yet (no `Survey` row anywhere in this
   dev DB) — `_get_or_create_fixture_survey()` creates a real `Survey` + `SurveyTemplate` once,
   idempotently, tied to the same fixture activity, and a real `SurveyResponse` for the fixture
   passport's participant. All three verified with real SMTP sends (real subjects: "Demande
   d'inscription reçue", "Pré-inscription reçue — Prochaine étape", "Votre avis sur Cours de
   Yoga du Mardi"), and idempotency confirmed by re-running `--template survey_invitation` a
   second time (reused the existing response token instead of duplicating). One script now
   covers all 7 templates: `python test/send_real_email_preview.py` with no args sends
   everything; `--template <type>...` narrows it.

   **Follow-up same session:** the user ran individual smoke-test invocations across this
   session (5 sends total, real reasons, real content — see the `email_log` table, not
   guesswork) and reasonably expected "run the script" to mean 7 emails in one go. It didn't:
   `latePayment` intentionally self-skips once the fixture passport is already marked paid
   (true from Aug 28), so a plain run only fires 6. Added `--reset-fixture` — puts the fixture
   passport back to unpaid/unredeemed (real DB write: `paid=False`, `Redemption` rows deleted,
   `uses_remaining` restored) immediately before sending, so `python
   test/send_real_email_preview.py --reset-fixture` now fires all 7, verified via `email_log`
   timestamps in the same run.
5. ~~**Standardize the Activity Image / Organization Logo pickers in the email template
   editor**~~ — **Done, but see #6 before trusting it.** Both fields in
   `templates/email_template_customization.html` now use the exact same Photo Normalization
   Tool widget (search + upload + crop), matching the canonical patterns in
   `docs/DESIGN_SYSTEM.md` §15: Activity Image = the Cover Photo variant (§15.2–§15.4, copied
   from `templates/activity_form.html`), Organization Logo = the Logo variant (new §15.7,
   copied from `templates/unified_settings.html`'s Organization Logo field — freeform crop, PNG
   output, upload-first toggle). Organization Logo also moved to render in every template's
   editor (was previously only visible inside the first template card, via a
   `{% if loop.first %}` gate) and now sits directly under Activity Image, matching the actual
   email layout order. Backend: `save_email_templates()` in `app.py` now handles an
   Unsplash-selected logo the same way it already handled an Unsplash-selected hero
   (`{type}_owner_logo_filename` form field, not just a direct file upload) — needed once Logo
   got a Search tab. Removed now-dead code this touched (`previewImage()` JS function, a stale
   hero cache-busting block referencing IDs that no longer exist in the DOM).
   - **Two real CSS bugs found and fixed** in `static/css/email-template-customization.css`,
     both from the page's blanket `.template-form-single-column .form-control { width: 100%; }`
     rule (already flagged once in DESIGN_SYSTEM.md §15 for breaking the search input-group —
     turns out it wasn't fully fixed, just fixed for that one case): (a) it stretched the plain
     upload `<input type="file">` — which isn't inside an `.input-group`, so it never got the
     existing restoration rule — past its container; (b) even after (a), the options panel
     (`.flex-grow-1.p-2`) still visually overflowed, because a flex child's default
     `min-width: auto` means it won't shrink below its content's natural width — classic
     flexbox overflow gotcha. Both now have explicit restoration rules right after the
     original `.input-group` one, same file.
6. ~~**Verify on the user's actual machine**~~ — **Done, 2026-08-30, session 4.** After the
   reboot, `list_connected_browsers` connected successfully to the user's real Chrome (Linux).
   Ran the full repro live in it: Email Templates → Customize on `newPass` → Organization Logo
   → Upload → real file input → crop modal (background image renders correctly, no stray
   overflow) → Use Logo → Save → toast "Email template saved successfully!". Byte-confirmed via
   direct file read (`static/uploads/15_owner_logo.png`, fresh mtime) and a direct sqlite query
   (`activity.email_templates` JSON on activity 15 showed `"activity_logo": "15_owner_logo.png"`
   under `newPass`) — not just the UI toast. Reset-to-default afterward and confirmed the DB
   round-tripped back to `{}` and the uploaded file was removed, so the fixture activity is
   clean. **The CSS fixes from #5 hold in a real browser — this item is closed.**
   - Non-blocking cleanup note found along the way: the page has duplicate DOM `id`s across the
     7 template cards' hidden modals (e.g. two elements both `id="modal_newPass_owner_logo"` —
     one live inside `#customizeModal`, one a leftover elsewhere in the DOM). Harmless for real
     users (only one is ever visible/interactive via Bootstrap's `.show` class), but it means
     any browser-automation tool that resolves elements by id/label across the whole page (not
     scoped to the open dialog) can silently target the wrong hidden input. Worth a dedup pass
     someday; not urgent enough to block anything on the punch list.

## New item, not on the original punch list: card skeleton redesign (2026-08-30, session 4)

The Email Templates page's collapsed card preview (`templates/email_template_customization.html`,
the `.email-preview-placeholder` skeleton) still modeled the *deleted* pre-redesign email
layout: small centered thumbnail, generic centered title, 5 unstructured body lines, a grey
"owner card" box with an unlabeled 24px icon, a separate history-table box, and — the most
visibly wrong part — a **CTA bar colored differently per template type**
(green/blue/orange/purple), directly contradicting the redesign's "no per-type accent color"
rule. The user caught this from a screenshot mid-session and asked for a low-fidelity but
structurally accurate skeleton instead.

Rebuilt to mirror the real design 1:1, reusing `templates/pass.html`'s already-proven `.pass-*`
CSS vocabulary (same color tokens: `#15192c` ink, `#f6f6f7` well, `#e4e8f0` divider) scaled
down to `mini-*` classes: full-width photo strip → solid ink caption bar (2 lines) →
per-template-family content. Verified the family structure against the real template source,
not assumption — `signup.html`'s content block is completely empty, `signup_payment_first.html`
has no `button()` call anywhere (ends at the payment well), `latePayment.html` has no QR
(matches `NO_QR_TEMPLATES` in `utils.py`) but does have both Facts and a CTA button. Deleted the
per-type colored button classes entirely (`.mini-cta` is now one variant, always ink) and the
dead unused `@keyframes placeholder-glow`. Bumped the card's fixed height 280px → 300px to fit
the richer structure. Verified live via Playwright: all 7 cards, the hover/Custom overlay on
the new taller card, and mobile single-column collapse. `web-design-guidelines` caught and fixed
two small issues in the new markup: missing `width`/`height` on the new photo `<img>` (CLS) and
a `transition: all` that should've listed just `box-shadow`/`border-color`.

## Second new item: pass.html consistency pass (2026-08-30, session 4)

Real-world use surfaced this: the user created a real "Cours de Wing Foil" activity (real photo,
real booked session, real payment) and reviewed the resulting `/pass/<code>` page fresh — the
first holistic look since it was rebuilt to mirror the email design language. Used the
`frontend-design` skill's restraint principle ("a minimal direction needs precision in spacing,
not more decoration") to find 4 concrete inconsistencies against the page's otherwise disciplined
ink/grey system, all fixed in `templates/pass.html`:
- The "Annuler" (cancel booking) button was the **only** colored, bordered, pill-shaped element
  on the page (`btn-outline-danger`) — restyled to a quiet `btn-link text-danger`, no border/pill.
- "N séance(s) réservée(s)" used to float as a disconnected line between Facts and the QR code
  — folded into the Crédits row as a sub-line (new `.pass-row-value-group`/`.pass-row-sub`
  classes, mirroring `rows_block()`'s `item.sub` pattern from the email macros exactly).
- The Séances well's booking rows used `px-0` while Historique's used `px-3` — same `.pass-well`
  container, two different internal rhythms. Standardized Séances to `px-3` to match, including
  the empty-state paragraphs and the booking form, which previously had no matching inset either.
- The org-logo row sat below the ink bar with no visual closure before `.card-body` — added a
  `border-bottom: 1px solid #e4e8f0`, reusing the existing divider token already used everywhere
  else (`.pass-row`), tightened `pt-4`→`pt-3`+`pb-3` to match.

No color, typography, or structural/ordering changes — all four fixes reuse tokens/classes
already established this session, deliberately, so `pass.html` stays in lockstep with the email
design language rather than drifting into a second, competing visual system. Verified live
against the real Wing Foil passport (`MP-8bf85bf462a5` — has a real booking, so it's the first
real test of the Séances well and its Annuler button on this rebuilt page), at desktop and a
simulated 375px width, including actually opening the cancel-booking modal to confirm the
restyled button still works. `web-design-guidelines` re-run after: clean, no new findings.

## Third item: pass.html layout overhaul + a real payment-metadata bug (2026-08-30, session 4)

The user annotated a screenshot of the Wing Foil passport with explicit, opinionated changes —
different from the consistency-only pass above, this is a deliberate departure from strict
email/page parity on two points, confirmed with the user before implementing:
- **Org logo + name moved onto the hero photo itself** (top-left, logo bumped 56px→72px, name
  white with a text-shadow for legibility over any photo) — replaces the separate white row
  below the ink bar. The email can't do this (Gmail has no `position:absolute` support, see
  `photo_band()`'s docstring in `email/components.html`), but this is a real page, so it's a
  conscious, page-only divergence, called out inline in both the CSS comment and this doc.
- **"Prochaine séance" removed entirely** — redundant with Mes séances below; the `{% set
  upcoming %}` line stays (still feeds the Crédits sub-line) even though its own visual block
  is gone.
- **Participant + Facts + QR merged into one grey `.pass-well` card, everything left-aligned**
  — Facts rows changed from label-left/value-right-on-one-line to label-above-value stacked
  block (mirrors the Participant name block's existing pattern), and the QR block lost its
  `text-center` wrapper so it sits flush left instead of centered. This is the second deliberate
  parity divergence — the email keeps rows_block()'s right-aligned values and qr_block()'s
  centered QR; only this page changes.

**Real bug found along the way, not a design issue:** the user reported Statut showing "Payé"
while Historique's "Paiement" row showed "En attente" for a passport they created themselves
(payment-first workflow: approve the signup + create the passport after confirming payment in
person). Traced to `approve_and_create_pass()` in `app.py` (~line 2274) — it copies
`paid=signup.paid` onto the new `Passport` but never sets `paid_date`/`marked_paid_by`/
`payment_method`, and `get_pass_history_data()` (`utils.py` ~line 1479) only populates the
Historique "Paiement" row when **both** `paid` and `paid_date` are truthy — so a
payment-first-created passport was always paid=True with an eternally-empty payment history
row. Fixed to set `paid_date=now_utc`, `marked_paid_by=session admin`, and
`payment_method=signup.payment_method` whenever `signup.paid` is true at creation time — same
fields `mark_passport_paid()` already sets, just applied at creation instead of only at the
separate "mark paid" action. Backfilled the one real passport this affected
(`MP-8bf85bf462a5`) directly in the dev DB to match what the fixed code would have produced.
Note: the unused, unreferenced `create_pass_from_signup()` route (no template links to it) has
the identical latent bug — left alone since it's unreachable from the UI, not the cause of
anything.

Verified live: hero overlay legible at desktop and simulated 375px width, Historique now shows
the real paid date/admin instead of "En attente". `web-design-guidelines` caught one thing:
the new org-logo `<img>` was missing explicit `width`/`height` — fixed.

## Fourth fix, same session: the hero-overlay logo "card" was box-shadow, not the image

The user's very next look at the overlay caught a real CSS bug: the org logo appeared to sit on
a solid white card, and they correctly suspected the logo PNG itself (`flhgi-logo-kd.png`) was
actually transparent — confirmed with PIL (`mode: RGBA`, ~35% of pixels at alpha=0, a real
alpha channel, not a flattened white background). The "card" was `box-shadow` on the `<img>`:
box-shadow always renders around an element's rectangular bounding box, ignoring the image's
own alpha shape — so a transparent circular badge got a solid rounded-rect shadow painted
behind its transparent area, looking exactly like a backing card. Fixed by switching to
`filter: drop-shadow(...)` instead, which *does* follow the PNG's real alpha silhouette — and
made it white/soft instead of dark, per the ask, so it reads as a glow around the crest, not a
shadow. Left `box-shadow` in place only on the solid-color letter-avatar fallback
(`.pass-hero-org-logo--fallback`, used when no logo is uploaded), where a rectangular shadow is
correct since that shape genuinely is a filled rectangle, not a transparent PNG.

Also bumped the logo 72px→96px, and split the org name one word per line (`{% for word in
org_name.split() %}`) instead of one flowing line — generalizes to any number of words, not
hardcoded to two. `web-design-guidelines` re-run after: clean, no new findings.
