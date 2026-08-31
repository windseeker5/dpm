# Minipass Email System

## Overview

Minipass sends **7 transactional email types**:

| Template Key | Display Name | Trigger |
|---|---|---|
| `newPass` | New Pass Created | A digital pass is created |
| `paymentReceived` | Payment Received | Payment is confirmed |
| `latePayment` | Late Payment Reminder | Payment is overdue |
| `signup` | Signup Confirmation | User registers |
| `signup_payment_first` | Signup Confirmation (Pay First) | User registers on payment-first activity |
| `redeemPass` | Pass Redeemed | Pass is scanned/redeemed |
| `survey_invitation` | Survey Invitation | Survey is sent |

## Architecture

Two layers:

1. **Shared design layer** — one base layout, one set of reusable macros, seven thin per-type templates. Lives in `templates/email/`.
2. **Per-activity customization layer** — a JSON blob stored on `Activity.email_templates` that overrides subject, title, message, hero image, org logo, and QR visibility.

## File locations

```
templates/email/
├── _base.html              # Shared layout
├── components.html         # Shared macros
├── newPass.html
├── redeemPass.html
├── latePayment.html
├── paymentReceived.html
├── signup.html
├── signup_payment_first.html
└── survey_invitation.html

config/email_defaults.json  # Default text per template type

templates/pass.html         # Public passport page — visual counterpart

templates/email_template_customization.html  # Per-activity editor UI

utils.py                    # get_email_context(), send_email(), notify_*()
utils_email_defaults.py     # Default template loader
utils_email_text.py         # Sandboxed admin-message rendering
```

## Design language

Top to bottom, every pass-style email follows this order:

1. **Photo header band** — real activity photo, full-width, followed by a solid ink bar with eyebrow + activity name. No overlay, no gradient, no `position:absolute`.
2. **Org identity** — logo (56px) + org name, plain, no card.
3. **Admin message** — one flowing paragraph of admin-edited text.
4. **Participant identity** — uppercase label, name, email/phone.
5. **Facts** — single column: Montant → Statut (pill) → Crédits → Lieu.
6. **Code d'accès** — QR code in a white rounded card, pass code below, caption above.
7. **Séances** (conditional) and **Historique** (conditional) — title above a light grey well.
8. **Payment instructions** (`signup_payment_first` only) — title above a light grey well with Interac logo.
9. **CTA button** — full-width, ink background, label from `cta_text`, `href` always `pass_url`.

### Hard rules

- No dark mode.
- No decorative chips, pills, dots, or colored accent bars. Color only where semantically load-bearing (the paid/unpaid pill).
- Type scale inside the card: 11 / 13.5 / 16 / 22px, weights 400 and 700.
- No `position:absolute` or `position:relative` in email HTML.
- Ground every test in real DB data.

## Hero image resolution

`get_activity_hero_image(activity, template_type)` returns the image in this priority:

1. Custom uploaded hero for this template type: `static/uploads/{activity_id}_{template_type}_hero.png`
2. The activity's own real photo: `static/uploads/{activity.image_filename}`
3. Shipped generic default: `static/images/email/heroes/{template_type}.png`
4. Generated placeholder from activity name

Serving routes:
- `GET /activity/<id>/hero-image/<type>` — public, no auth, `Cache-Control: no-cache`.
- `GET /owner-logo?activity_id=<id>` — public, org logo.

## Per-activity customization

URL: `/activity/<id>/email-templates`

Editable per template type, per activity:
- Subject
- Title (headline in ink bar)
- Admin message (rich text)
- Activity image (hero override)
- Organization logo (shared across all 7 types for this activity)
- Show QR code toggle (pass-style templates only)

Save route: `POST /activity/<id>/email-templates/save`
Reset route: `POST /activity/<id>/email-templates/reset`

Reset deletes customization keys and uploaded files; the activity falls back to `config/email_defaults.json` and the hero priority order.

### SQLAlchemy JSON gotcha

`Activity.email_templates` is a JSON column. Mutating a nested dict in place does not mark the column dirty. Always call `flag_modified()`:

```python
from sqlalchemy.orm.attributes import flag_modified
activity.email_templates['newPass']['subject'] = 'New subject'
flag_modified(activity, 'email_templates')
db.session.commit()
```

## Admin message consolidation

Today the admin-editable body text is one field: `admin_message`. Older activities may still have the legacy trio `intro_text` + `custom_message` + `conclusion_text`. `consolidate_admin_message()` in `utils.py` folds them into `admin_message` automatically.

## Email sending pipeline

Call the trigger functions, not `send_email()` directly:

- `notify_pass_event(app, event_type=..., pass_data=..., activity=...)` — `newPass`, `paymentReceived`, `redeemPass`, `latePayment`.
- `notify_signup_event(app, signup=..., activity=...)` — `signup`, `signup_payment_first`.
- `send_survey_invitations(survey_id)` — `survey_invitation`.

`get_email_context()` merges defaults + event data + activity customizations. `send_email()` renders `templates/email/{type}.html` and sends via SMTP.

### Async sends

`send_email_async()` reloads `activity` and `pass_data` fresh in the background thread's own DB session. Do not fake `pass_data` in memory and expect it to show up.

## Deliverability

### Hosted images, except QR

| Image type | Delivery |
|---|---|
| Hero image | Hosted Flask route (`{{ hero_image_url }}`) |
| Owner logo | Hosted Flask route (`{{ owner_logo_url }}`) |
| Interac logo | Hosted static URL |
| **QR code** | **CID attachment (`cid:qr_code`)** — must survive forwarding/offline |

Only the QR code may be a CID attachment. Never add other CID attachments.

### Subject line rules

Avoid payment-urgency language and spam triggers:

- ❌ "Paiement requis" / "Payment required"
- ❌ "Urgent" / "Action required"
- ❌ "Confirmez maintenant" / "Confirm now"
- ❌ ALL CAPS words

Safe alternatives: "Prochaine étape", "Votre inscription", "Confirmation de pré-inscription".

### Compliance checklist

Already implemented; do not break:

- `Precedence: normal` for transactional emails, `bulk` for bulk sends.
- `List-Unsubscribe` + `List-Unsubscribe-Post` headers.
- `Message-ID` with microsecond precision.
- `multipart/alternative` with a real `text/plain` fallback.
- Physical address and unsubscribe link in footer.
- DKIM, SPF, DMARC aligned with the `From` domain.

## Testing

- Fast sanity check: `python test/render_all.py`
- Browser preview: `/activity/<id>/email-preview?type=newPass`
- **Real test:** `python test/send_real_email_preview.py --reset-fixture`
  - Sends all 7 templates via real SMTP.
  - Uses real DB writes on a fixture passport.
  - `--template <type>` to send just one.
- For any UI change, verify with pi's `browser-tools` against the real app at `localhost:5000`.

## Common traps

- Browser preview is same-origin; it cannot reveal what Gmail's sanitizer strips.
- `cta_url` is not used in templates; `href` is always `pass_url`.
- `latePayment` has no QR code (`NO_QR_TEMPLATES` in `utils.py`).
- Editing `config/email_defaults.json` does not retroactively update existing activities.
- After replacing a shipped default hero PNG, clear the LRU cache or restart the dev server.
