# Email Template Redesign — Handoff Context

## What we did
Replaced the old email template pipeline (7 near-duplicate ~240-line HTML files under
templates/email_templates/, compiled via compileEmailTemplate.py) with a single shared
base layout (templates/email/_base.html + components.html) and thin per-type templates
(~25-35 lines each). Old pipeline fully deleted (18MB, 79 files).

Key changes across the branch:
- New base layout: labelled "pass block" (holder, credits, amount, status) replacing
  the old skeuomorphic gradient card; mascot shrunk from 152px centred to 48px in a
  header band; QR shrunk from 350-400px to 150px inside the pass block.
- Per-type accent colors (payment received green, redeemed teal, survey purple,
  signups blue/amber, latePayment amber).
- Fixed several real bugs along the way: silent send failures for customized
  activities, raw Jinja leaking into previews, French/English amount formatting
  mismatches, a template-path double-resolution bug, credit "pips" rendering as
  five empty circles at zero credits.
- Most recent pass (a3e24e3): rebuilt the pass card again — activity photo and QR
  side-by-side at top, holder/contact/credits/amount below — after the label/value
  stack "looked like a form, not a pass."
- Typography: switched to serif for the "next session" headline (Georgia in email,
  Roboto Slab on the passport page) to unify the two surfaces.

Technically solid: 49 tests passing, all 7 email types render and send via real SMTP,
verified against the real dev DB.

## Where it fell short
Despite several passes, the result is **not good-looking** — overall visual polish/
spacing, the typography choice, the pass card/QR block layout, and the color/accent
scheme all still feel off. Functionally correct, aesthetically not there.

## What's next
New session's job: redesign the email templates for real visual quality, using
concrete reference examples the user will provide as a separate document (not
derived from scratch again). Treat the current templates/email/ output as the
functional baseline to restyle, not as the design target.

## Where the code lives
- templates/email/_base.html, components.html — shared layout/macros
- templates/email/<type>.html — per-type templates (newPass, redeemPass,
  paymentReceived, latePayment, signup, signup_payment_first, survey_invitation)
- templates/pass.html — the passport page (kept in visual sync with the email)
- test/render_all.py — renders every email type to standalone HTML for
  screenshotting/critique without sending real mail
- docs/EMAIL_TEMPLATE_SYSTEM.md, docs/EMAIL_DELIVERABILITY.md — system docs,
  read before touching this again

## Direction decision — APPROVED (2026-08-27)

Final direction is locked in for tonight. Reference mockups narrowed down over
several passes to **#1 (Wallet card) + #4 (Clean receipt) only** — #2/#3/#5/#6 and
every "card inside a card" / colored-accent-border treatment tried along the way
were explicitly rejected. Live preview (private artifact, will need republishing
if you want to see it again — the file is also saved in this repo, see below):
https://claude.ai/code/artifact/a440eec8-ac34-458a-a776-7d62c2c6357c

**The approved mockup file is saved at `email-redesign/passeport-mockup-approved.html`**
— open it directly in a browser, it's self-contained (real images/QR embedded as
base64, no server needed). This is the design target for the real implementation.

### What the approved design actually is
One continuous flowing document per email — no boxed "hero" card, no colored accent
borders anywhere. Top to bottom:
1. **Photo header band** — real activity photo, dark gradient scrim behind white
   text (eyebrow + activity name) for legibility.
2. **Org identity** — logo (56px, not the 26px it started at) + org name, plain,
   no card.
3. **Message** — the existing `intro_text` + `custom_message` fields rendered as
   one flowing paragraph, not two blocks. **`custom_message` is currently a real
   gap**: it exists as an admin-editable field (`config/email_defaults.json`,
   `utils.py:get_email_context()`) but nothing in `templates/email/` renders it
   today. This design assumes it gets wired in.
4. **Participant identity** — label + name + email, plain flow, generous space
   below the "PARTICIPANT" label (match this to how "HISTORIQUE" breathes).
5. **Facts, one column, in this exact order**: Montant → Statut (Payé pill) →
   Crédits → Lieu. All the same row style (13.5px label/value, tabular-nums,
   bottom-bordered as a group) — this row component is reused for everything
   below it too.
6. **QR code** — a *tight* 1px black frame (border-radius 4px, ~3px padding)
   around *only* the QR image, not around the reference code or caption text.
   Reference code + caption sit plain underneath, unboxed.
7. **Séances card** (conditional — only when `activity.uses_scheduling` and there
   are real upcoming slot bookings) — same white/grey-border card style as
   Historique below it, same row component inside. **Sits above Historique.**
8. **Historique card** — white background, 1px grey border (never a filled grey
   box), same row component, labels are the real ones from
   `utils.py::_build_history_rows()` (Création / Paiement / Participation N) —
   do not invent different wording.
9. **CTA button** — solid black/ink (`var(--ink)`, not the brand blue), full
   width, hover + focus-visible states.

### Hard rules that got established the hard way (do not regress on these)
- **No dark mode.** No "AI slop" decorative chips/pills/dots/colored accent bars —
  color only where it's semantically load-bearing (the paid/unpaid status pill).
- **Type scale: 4 sizes / 2 weights only** inside the card — 11 / 13.5 / 16 / 22px,
  weights 400 and 700. Spacing snapped to the 8-point grid (8/16/24/32...).
- **QR crispness is a real technical constraint, not just styling**: the QR PNG
  from `generate_qr_code_image()` is 330×330 native. Displaying it at a size that
  isn't a clean divisor of the source forces browser smoothing and makes it look
  "muddy." In the real templates, generate the QR at (or very near) its final
  display size rather than relying on `image-rendering: pixelated` in CSS (Outlook
  ignores that property).
- **Ground every example in real DB data**, not invented content — pulling from
  the actual `instance/minipass.db` (after the LHGI restore, see below) caught
  several real bugs: a fake pass_code format, invented history labels that don't
  match `_build_history_rows()`, an invented "next game" concept for an activity
  that doesn't use scheduling at all, and a "4 sur 1" credits display that made no
  sense for a quantity-purchase passport type (`sessions_included=1`,
  `uses_remaining=4` tickets) — that passport shows a plain ticket count instead.
- **Photo must become a real `<img>` in production**, not the CSS
  `background-image` the mockup uses — Outlook and other clients strip CSS
  background-images entirely.

### Environment note — local dev DB now has real LHGI data
`instance/minipass.db` was restored from the user's real LHGI production backup
(`~/Downloads/minipass_backup_2026-08-28_00-14-35.zip`) and upgraded via
`migrations/upgrade_production_database.py` (44/44 tasks, alembic_version fixed to
`c8f3a2d91b45`). Real activity photos/logos were copied into `static/uploads/`.
The **previous dev DB and uploads are backed up** at
`instance/minipass.db.backup_20260827_202025` and
`static/uploads.dev_backup_20260827_202025/` if you need KDC Corporation's test
data back. `templates/email_templates/` also reappeared on disk (from the same
backup zip, old deleted pipeline) — it's untracked, harmless, safe to delete
whenever, just wasn't touched tonight.

## Next session — punch list

1. **Rebuild `templates/email/components.html`** to match the approved mockup:
   replace `pass_card()`/`session_list()` with the structure in "What the approved
   design actually is" above. Introduce a reusable `.section-card`-equivalent
   Jinja macro so Séances and Historique share one implementation.
2. **Wire in `custom_message`** — real gap identified above, closes it.
3. **Real `<img>` for the photo**, sized/positioned to match the mockup's gradient
   scrim treatment.
4. **QR**: generate at final display size (or very close) instead of relying on
   browser-side scaling.
5. **Apply to `newPass.html`, `redeemPass.html`, `latePayment.html`** (all three
   share `pass_card()` — one component change covers all three).
6. **Test for real** per this project's mandatory rule: Playwright against
   `localhost:5000`, real send to `kdresdell@gmail.com`, verify DB cleanup with
   `sqlite3` after — see root `app/CLAUDE.md`.
7. Only after 1-6 are solid: extend the same visual language to `paymentReceived`,
   `signup`, `signup_payment_first`, `survey_invitation`, then sync `pass.html` to
   match, then finally rewrite `docs/EMAIL_TEMPLATE_SYSTEM.md` (still stale/
   describes the deleted 3-tier compiled pipeline — confirmed obsolete earlier
   this session).
