# Minipass Email System

The single reference for how Minipass email works, what changed in the August 2026 redesign, and how to test it.

## Overview

Minipass sends **7 transactional email types**:

| Template Key | Display Name | Trigger |
|---|---|---|
| `newPass` | New Pass Created | A digital pass is created |
| `paymentReceived` | Payment Received | Payment is confirmed |
| `latePayment` | Late Payment Reminder | Payment is overdue |
| `signup` | Signup Confirmation | User registers (approval-first activity) |
| `signup_payment_first` | Signup Confirmation (Pay First) | User registers on payment-first activity |
| `redeemPass` | Pass Redeemed | Pass is scanned/redeemed |
| `survey_invitation` | Survey Invitation | Survey is sent |

The authoritative list is `EMAIL_TEMPLATE_TYPES` in `utils.py:3470`.

> **`templates/email/password_reset.html` is not one of the 7.** It sits in the same folder but is standalone — it does not extend `_base.html`, does not import `components.html`, has no per-activity customization, no preview route, and is outside `EMAIL_TEMPLATE_TYPES`. It is used only by the admin forgot-password flow (`forgot_password()`, `app.py:6371`). Do not fold it into the shared design system.

## Architecture

Two layers:

1. **Shared design layer** — one base layout, one set of reusable macros, seven thin per-type templates. Lives in `templates/email/`.
2. **Per-activity customization layer** — a JSON blob on `Activity.email_templates` overriding subject, title, admin message, hero image, org logo, and QR visibility.

## File locations

```
templates/email/
├── _base.html              # Shared layout (161 lines)
├── components.html         # Shared macros (319 lines)
├── newPass.html
├── redeemPass.html
├── latePayment.html
├── paymentReceived.html
├── signup.html
├── signup_payment_first.html
├── survey_invitation.html
└── password_reset.html     # NOT part of the 7 — standalone, see above

config/email_defaults.json  # Default text per template type

templates/pass.html         # Public passport page — visual counterpart

templates/email_template_customization.html  # Per-activity editor UI

utils.py                    # get_email_context(), send_email(), notify_*()
utils_email_defaults.py     # Default template loader
utils_email_text.py         # Sandboxed admin-message rendering
```

## Design language

Top to bottom, every pass-style email follows this order:

1. **Photo header band** — real activity photo, full-width, followed by a solid ink bar with eyebrow + activity name. No overlay, no gradient, no `position:absolute`. See the warning below.
2. **Org identity** — logo (56px) + org name, plain row, no card.
3. **Admin message** — one flowing paragraph of admin-edited text. `<strong>` renders near-black against grey body text (`.mp-message strong` in `_base.html`).
4. **Votre passeport** — `well('Votre passeport')` holding one `rows_block()`: Participant (name, email underneath) → Montant → Statut (pill) → Crédits → Lieu, label left / value right, hairline between rows. No grey fill, and the name is not repeated as a heading. Do not also repeat the location in the message paragraph; it is redundant with the Lieu row.
5. **Code d'accès** — `well("Code d'accès")` holding `qr_block()`: one outlined white box, QR centered, pass code below it, caption under that.
6. **CTA button** — full-width, ink background, directly under the QR so the action is above the fold. See CTA rules below. (`latePayment` has no QR, so its button goes directly under the Votre passeport list, above Historique — the whole email is one action and it must be on the first phone screen.) `latePayment` also shows `interac_block()` ("Instructions de paiement": amount + destination address) between the list and the button, only when a payment address is configured; the default message deliberately keeps the address in its sentence too. The address appears twice on purpose: recipients skim, and seeing it in both places makes them more likely to act. Do not "clean up" the repetition.
7. **Séances** (conditional) and **Historique** (conditional) — `section_card()`, title above hairline rows. Historique passes `muted=True`: regular weight, grey text, same 13.5px size.
8. **Payment instructions** (`signup_payment_first` only) — `interac_block()` keeps its own light-grey card (a payment card with the Interac logo, not a list section), with the Interac logo.

### ⚠️ Never overlay content on the photo

The originally-approved mockup had the caption overlaid on the photo with a gradient scrim. **Real Gmail sends broke it** (web, iOS and Android) because Gmail has no support for `position:absolute`/`relative` in HTML email at all. That failure is *why* the solid ink bar and the plain org-identity row exist.

Do not "fix" this back toward an overlay — it will break in real inboxes again. This was re-litigated once already when the passport page gained an overlaid org logo; see **Deliberate divergences** below.

### Hard rules

- No dark mode.
- No decorative chips, pills, dots, or colored accent bars. Color only where semantically load-bearing (the paid/unpaid pill).
- Type scale inside the card: 11 / 13.5 / 16 / 22px, weights 400 and 700. Do not add in-between sizes (12, 12.5…) — mute with weight and color instead.
- No filled grey boxes and no card inside a card. A section is a title above hairline rows; the QR is the one outlined box.
- The unpaid pill text is `#7a5f17` on `#fff3d6` (5.5:1). The earlier `#8a6d1f` measured 4.44:1 and failed. `pass.html`'s `.pass-status-pill--unpaid` uses the same value.
- Muted text is `#5f6779` (`C_LABEL` / `c_label`). It clears 4.5:1 on both the white card and the `#f1f4f9` page behind the footer; the earlier `#8892a4` and `#a8b0bf` did not.
- No `position:absolute` or `position:relative` in email HTML. Ever.
- Ground every test in real DB data. Invented content hid three separate real bugs.

### When the signup reference code shows

Only when another unpaid signup in the same activity has the **same name and the same amount** (`has_conflicting_unpaid_signup()`, `utils.py`). Every signup has a code stored, but it is shown to the customer only in that case. The signup email and the web confirmation page (`signup_confirmation.html`) must both follow this rule; the page passes `earlier_only=True` so the first person is never shown a code after a later duplicate appears. The email *preview* forces the code on so admins can see the layout.

### CTA rules

| Template | Button |
|---|---|
| `newPass`, `paymentReceived`, `redeemPass` | `button(pass_url, cta_text or 'Voir mon passeport en ligne')` |
| `latePayment` | `button(pass_url, cta_text or 'Effectuer le paiement')` |
| `survey_invitation` | `button(survey_url, 'Répondre au formulaire')` |
| `signup`, `signup_payment_first` | No CTA button |

`signup` shows a short `Votre demande` recap list (participant + email, activity, status "En attente d'approbation") under the message. It only uses fields every real send has (`user_name`, `user_email`, `activity_name`), and escapes them with `| e` because `rows_block()` renders values with `|safe`.

- `cta_text` **is** read from context — do not hardcode labels. `latePayment`'s label is deliberately different, since that email is about an unpaid pass with nothing to view yet.
- `cta_url` exists in `config/email_defaults.json` and has sanitization behind it (`utils.py:380`) but is **deliberately never used**. `href` is always the real per-passport `pass_url` (or `survey_url`), never a generic `/my-passes` default. Every call site carries a comment saying so — do not "helpfully" wire it in.

## Component macros (`templates/email/components.html`)

| Macro | Purpose |
|---|---|
| `money(amount)` | Quebec-French amount formatting: `50,00 $` |
| `credit_line(remaining, total=None)` | "1 sur 5", or bare "1" when no real session total exists |
| `interac_block(requested_amount, payment_email, base_url='')` | Interac transfer instructions card + logo |
| `signup_code_notice(signup_code)` | Yellow warning card for the payment reference code, shown only on naming conflict. The code sits directly on the amber card (no white box inside it), 16px mono, on the documented type scale |
| `button(href, label, accent=None)` | Full-width solid-ink CTA (`accent` is ignored — kept for old call sites) |
| `photo_band(hero_image_url, eyebrow, headline, is_photo=True)` | Hero image + solid ink caption bar; branches on `is_photo` |
| `rows_block(items, outer_border=True, top_margin=18, muted=False)` | The label/value row list used by Facts, Séances and Historique. Items are `{label, value, sub}`; `muted=True` is the quiet Historique style |
| `status_pill(paid)` | "Payé"/"Non payé" pill — the one place color is load-bearing |
| `qr_block(qr_src, ref_code=None, caption=None)` | One outlined box: QR → pass code → caption, all centered |
| `well(label)` | Section title above its content, used via `{% call %}`. No fill, no padding |
| `section_card(label, items, muted=False)` | `well()` + `rows_block()` convenience wrapper |

Deleted in the redesign — if you see these referenced anywhere, the reference is stale: `pass_card()`, `session_list()`, `next_session()`, `history_table()`, `identity_block()` (the participant is now the first row of the Facts list).

## Hero image resolution

`get_activity_hero_image(activity, template_type)` returns the image in this priority:

1. Custom uploaded hero for this template type: `static/uploads/{activity_id}_{template_type}_hero.png`
2. The activity's own real photo: `static/uploads/{activity.image_filename}`
3. Shipped generic default: `static/images/email/heroes/{template_type}.png`
4. Generated placeholder from activity name

`hero_is_photo` controls which `photo_band()` branch renders (full-bleed photo vs. contained mascot icon).

Serving routes:
- `GET /activity/<id>/hero-image/<type>` — public, no auth, `Cache-Control: no-cache` (`app.py:13585`).
- `GET /owner-logo?activity_id=<id>` — public, org logo (`app.py:13628`).

## Per-activity customization

URL: `/activity/<id>/email-templates` (`email_template_customization()`, `app.py:12637`)

Editable per template type, per activity: subject, title, admin message (rich text), activity image (hero override), organization logo (shared across all 7 types), show-QR toggle (pass-style templates only).

- Save: `POST /activity/<id>/email-templates/save`
- Reset: `POST /activity/<id>/email-templates/reset` (`app.py:12987`)
- Preview: `GET /activity/<id>/email-preview?type=newPass` (`app.py:13104`)
- Send test: `POST /activity/<id>/email-test` (`app.py:13657`) — uses `TEST123` stub data

Reset deletes customization keys and uploaded files; the activity falls back to `config/email_defaults.json` and the hero priority order.

### Gotcha: editing the defaults does not update existing activities

Each activity holds its **own frozen snapshot** of the defaults JSON in `activity.email_templates`. Editing `config/email_defaults.json` changes what *new* activities get — it does not retroactively touch existing ones. Fixing shared default copy means also applying it to any activity you are testing against.

### Gotcha: `flag_modified()` on the JSON column

`Activity.email_templates` is a JSON column. Mutating a nested dict in place does not mark it dirty:

```python
from sqlalchemy.orm.attributes import flag_modified
activity.email_templates['newPass']['subject'] = 'New subject'
flag_modified(activity, 'email_templates')
db.session.commit()
```

### Admin message consolidation

The admin-editable body is one field: `admin_message`. Older activities may still carry the legacy trio `intro_text` + `custom_message` + `conclusion_text`; `consolidate_admin_message()` (`utils.py:4482`) folds them in automatically at read/edit time, and `task46_consolidate_admin_message` in `migrations/upgrade_production_database.py` did the one-time DB-wide sweep.

Subject, title and admin message are stored as Jinja **source** and rendered through a `SandboxedEnvironment` in `utils_email_text.py` — never a bare `jinja2.Template`. This is deliberate hardening against SSTI from user-supplied signup names reaching a second render pass. A broken customization degrades to raw source rather than blocking the send.

## Sending pipeline

Call the trigger functions, not `send_email()` directly:

- `notify_pass_event(app, event_type=..., pass_data=..., activity=...)` (`utils.py:4349`) — `newPass`, `paymentReceived`, `redeemPass`, `latePayment`.
- `notify_signup_event(app, signup=..., activity=...)` (`utils.py:4221`) — `signup`, `signup_payment_first`, chosen from `activity.workflow_type`.
- `send_survey_invitations(survey_id)` (`app.py:11891`) — `survey_invitation`.

`get_email_context()` (`utils.py:4498`) merges, in order: hardcoded defaults → `config/email_defaults.json` → event data → activity customizations. `send_email()` (`utils.py:3509`) renders the template, inlines CSS with Premailer, builds `multipart/related` with deliverability headers, generates a real text/plain alternative, and sends over SMTP.

**In Flask debug mode, `send_email()` force-redirects the recipient to `MAIL_USERNAME` from `.env`** regardless of the address passed in.

### Async sends

`send_email_async()` (`utils.py:3880`) spawns a thread that reopens the app context and **reloads `Activity` and `Passport` fresh in its own DB session** — this is what fixed a `DetachedInstanceError` race. Consequence: you cannot fake `pass_data` in memory (or leave it flushed-but-uncommitted) and expect it to appear in the email. The render path re-queries real DB state. On success it writes an `EmailLog` row.

## Deliverability

### Hosted images, except the QR

| Image type | Delivery |
|---|---|
| Hero image | Hosted Flask route (`{{ hero_image_url }}`) |
| Owner logo | Hosted Flask route (`{{ owner_logo_url }}`) |
| Interac logo | Hosted static URL |
| **QR code** | **CID attachment (`cid:qr_code`)** — must survive forwarding/offline |

Only the QR may be a CID attachment. Never add others. `EMAIL_QR_BOX_SIZE` in `utils.py` generates it at (or near) its exact 165×165 display size so nothing rescales it. `NO_QR_TEMPLATES = {'latePayment'}` — that template has no QR.

### Subject line rules

Avoid payment-urgency language and spam triggers:

- ❌ "Paiement requis" / "Payment required"
- ❌ "Urgent" / "Action required"
- ❌ "Confirmez maintenant" / "Confirm now"
- ❌ ALL CAPS words

Safe alternatives: "Prochaine étape", "Votre inscription", "Confirmation de pré-inscription".

### Compliance checklist

Already implemented; do not break:

- `Precedence: normal` for transactional, `bulk` for bulk sends.
- `List-Unsubscribe` + `List-Unsubscribe-Post` headers.
- `Message-ID` with microsecond precision.
- `multipart/alternative` with a real `text/plain` fallback.
- Physical address and unsubscribe link in footer.
- DKIM, SPF, DMARC aligned with the `From` domain.

## Testing

### Sending all 7 emails

There are **two** all-7 scripts and they are not interchangeable:

| Script | Data | Images | Run from |
|---|---|---|---|
| `test/send_real_email_preview.py` | Real DB writes on a fixture | CID attachments | Local dev |
| `test/test_all_email_templates.py` | Static sample data | Hosted URLs | The VPS |

Both send to a hardcoded `kdresdell@gmail.com`.

**The one that matters day to day:**

```bash
python test/send_real_email_preview.py --reset-fixture
```

`--reset-fixture` puts the fixture passport back to unpaid/unredeemed first, so all **7** actually fire. Without it a plain run sends only 6 — `latePayment` self-skips once the fixture is already marked paid.

| Flag | Effect |
|---|---|
| `--template <type> [<type> ...]` | Send only these (default: all 7) |
| `--pass-code <code>` | Use a real passport by code |
| `--passport-id <int>` | Use a real passport by DB id |
| `--confirm-writes` | **Required** to target anything but the default fixture |
| `--reset-fixture` | Reset the fixture to unpaid/unredeemed first |

> **This script writes real data.** It genuinely marks the fixture passport paid and genuinely redeems it (mirroring `mark_passport_paid()` / `redeem_passport_qr()`) before firing `paymentReceived`/`redeemPass`, because the render path re-queries real DB state — faking it produces emails that contradict their own content. It is idempotent: re-running does not re-decrement credits.
>
> Default target is a disposable fixture: **"Cours de Yoga du Mardi", activity 15, passport `MP-a0ece8456173`**. Never point real-data writes at anything restored from the LHGI production backup — that is exactly what `--confirm-writes` exists to prevent.

Use `test/test_all_email_templates.py` instead when you need to confirm the **hosted** hero/logo URLs actually resolve in a recipient's client, since the dev `SITE_URL` is not publicly reachable.

### Faster checks

- Render sanity check (catches exceptions, tells you nothing about appearance): `python test/render_all.py`
- Browser preview: `http://localhost:5000/activity/<id>/email-preview?type=newPass`

### Why a preview is not proof

The `/email-preview` route is **same-origin** — it cannot reveal anything Gmail's HTML sanitizer would strip. This is exactly how the `position:absolute` photo-overlay bug survived a whole round of review. Its context-building is also maintained separately from the real send path and has drifted before (it once silently omitted the Interac logo). A same-origin preview alone never proves an email survives a real client.

### Related unit tests

- `test/test_email_render.py` — renders all 7 the way a real send does; guards a regression where customized activities raised `UndefinedError` silently inside the send worker thread.
- `test/test_email_text.py` — unit tests for `utils_email_text.py`.
- `test/test_bulk_email_prod_path.py` — exercises `send_email()`'s production (non-debug) branch.

## August 2026 redesign — what changed and why

All 7 templates were unified into one visual language, and `templates/pass.html` was rebuilt to match.

**Real bugs found and fixed** (found by testing against real data and real Gmail sends, not by inspection):

- **`get_activity_hero_image()` priority was backwards** — the generic mascot PNG was checked *before* the activity's own photo, so every email showed the mascot even when a real photo existed. Reordered.
- **`DetachedInstanceError` race** in `send_email_async()`'s background thread — now re-queries fresh in its own session.
- **`notify_signup_event()` and `send_survey_invitations()` never set `owner_logo_url` or `hero_is_photo`** — the org logo had been silently missing from every real signup and survey email.
- **`cta_text` was never read by any template** despite existing in the defaults with sanitization behind it. Now wired in; `cta_url` still deliberately unused.
- **`credit_line()` "4 sur 1" bug** — a quantity-purchase passport type (`sessions_included=1`, multiple tickets) showed a nonsensical fraction. Now only shows the fraction when the total is a real multi-session count.
- **`approve_and_create_pass()` never set `paid_date`** (`app.py` ~2274) — it copied `paid=signup.paid` onto the new Passport but not `paid_date`/`marked_paid_by`/`payment_method`, and `get_pass_history_data()` only fills the Historique "Paiement" row when both `paid` and `paid_date` are truthy. Payment-first passports showed "Payé" in Facts but "En attente" in Historique forever. Fixed at creation time.

**Accepted tradeoff, do not re-litigate as a defect:** the QR sits in a thin light-grey outline rather than a heavy frame, so an email client that blocks images shows an empty outlined box with the pass code still readable beneath it. The pass code text is the fallback; the QR is a convenience.

### Deliberate divergences from `templates/pass.html`

The passport page and the emails share a design language but are **not** identical, on purpose:

| Element | Passport page | Email | Why |
|---|---|---|---|
| Org logo | Overlaid on the hero photo with a drop-shadow glow | Plain row below the ink bar | Gmail has no `position:absolute`; `filter:drop-shadow` is unsupported in Outlook/Windows Mail |
| QR box | Outlined box, centered (`.pass-qr-frame`) | Same (`qr_block()`) | Kept in step (Sept 2026 lean pass) |
| Section style | Title above hairline rows, no fill (`.pass-well`) | Same (`well()`) | Kept in step |
| Facts rows | Participant first, then Montant → Lieu, label left / value right | Same | Kept in step |
| Historique | Regular weight, grey (`.pass-well--quiet`) | `muted=True` | Kept in step |
| Button under QR | n/a (the page is the destination) | `button()` right below QR | The email's job is to send people here |

The org-logo overlay is a permanent, deliberate divergence — not an oversight to be "fixed."

## Common traps

- The preview route falls back to the local host for `pass_url` when `SITE_URL` is unset, so the CTA button is visible in dev. Real sends still read `SITE_URL` and omit the button without it.

- Browser preview is same-origin; it cannot reveal what Gmail's sanitizer strips.
- `cta_url` is not used in templates; `href` is always `pass_url` (or `survey_url`).
- `latePayment` has no QR code (`NO_QR_TEMPLATES` in `utils.py`).
- Editing `config/email_defaults.json` does not retroactively update existing activities.
- After replacing a shipped default hero PNG, clear the LRU cache or restart the dev server.
- `send_email()` redirects all mail to `MAIL_USERNAME` when Flask is in debug mode.
- The email-templates editor page has duplicate DOM `id`s across the 7 hidden modals. Harmless for real users, but browser automation that resolves elements by id across the whole page can silently target the wrong hidden input — scope selectors to the open dialog.
