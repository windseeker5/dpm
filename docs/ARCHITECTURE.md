# Minipass Architecture

## Stack

| Layer | Technology |
|---|---|
| Backend | Flask (Python) |
| Frontend | Jinja2 server-side rendering |
| UI foundation | Tabler.io + application styles |
| Database | SQLite per customer |
| Auth | Session-based |
| File storage | Local filesystem |
| Deployment | Docker container per customer, nginx reverse proxy, Let's Encrypt |
| Email | SMTP, Premailer CSS inlining, Bleach sanitization |

## Key files

| File | Responsibility |
|---|---|
| `app.py` | Flask routes and request handlers (~14k lines, ~145 routes) |
| `models.py` | SQLAlchemy models (24 models) |
| `utils.py` | Email context, sending, helpers (~5.9k lines) |
| `utils_email_defaults.py` | Default email template text |
| `utils_email_text.py` | Sandboxed Jinja rendering for admin-edited text |
| `kpi_renderer.py` | KPI/dashboard rendering helpers |
| `decorators.py` | Route decorators (auth, tier limits) |
| `config/email_defaults.json` | Default subject/title/message/CTA per email type |
| `migrations/upgrade_production_database.py` | Idempotent production migrations |

## Packages and blueprints

Registered in `app.py:148-191`:

| Blueprint | Source | Purpose |
|---|---|---|
| `backup_api` | `api/backup.py` | Backup/restore endpoints |
| `geocode_api` | `api/geocode.py` | Address geocoding |
| `settings_api` | `api/settings.py` | Settings endpoints |
| `chatbot_bp` | `chatbot_v2/routes_simple.py` | AI analytics chatbot (CSRF-exempt) |

## Models

| Model | Purpose |
|---|---|
| `Admin` | Admin users and authentication |
| `AdminActionLog` | Audit trail of admin actions |
| `PushSubscription` | Web push notification subscriptions |
| `User` | Participants/customers |
| `Activity` | Activities/programs |
| `ActivityPassportInheritance` | Accept passports from another activity (e.g. previous season) |
| `PassportType` | Types of passes within an activity |
| `Passport` | Individual digital passes with QR codes |
| `Signup` | Registration records |
| `Redemption` | Pass usage / attendance log |
| `ActivitySlot` | A dated session occurrence with a seat limit |
| `SlotBooking` | Seat-hold ledger linking a passport to a slot |
| `EbankPayment` | Incoming e-transfer payment emails |
| `StripeTransaction` | Stripe payment records |
| `Income` / `Expense` | Financial transaction records |
| `Setting` | Organization settings (key-value) |
| `ReminderLog` | Sent payment reminders |
| `EmailLog` | Email sending history |
| `AnnouncementLog` | Broadcast/announcement history |
| `Survey` / `SurveyTemplate` / `SurveyResponse` | Survey system |
| `QueryLog` | AI chatbot query audit trail |

> The session-booking feature is called **Book Session** in the product, but the models are named `ActivitySlot` (`models.py:346`) and `SlotBooking` (`models.py:406`). There are no models named `Session` or `Booking`.

## Route groups

`app.py` carries ~145 routes. The main groups:

- **Auth** — `/login`, `/logout`, `/forgot-password`, `/reset-password/<token>`, `/change-password`
- **Dashboard/KPIs** — `/dashboard`, `/api/global-kpis`, `/api/kpi-data`, `/api/activity-kpis/<id>`
- **Activities** — `/create-activity`, `/edit-activity/<id>`, `/activities`, `/activity-dashboard/<id>`
- **Signups** — `/signup/<activity_id>`, `/signups`, `/signups/bulk-action`, `/signup/approve-create-pass/<id>`
- **Passports** — `/create-passport`, `/redeem/<pass_code>`, `/redeem-qr/<pass_code>`, `/pass/<pass_code>`, `/scan-qr`
- **Session booking** — `/pass/<pass_code>/book`, `/pass/<pass_code>/cancel-booking/<id>`
- **Payments/Stripe** — `/stripe/webhook`, `/signup/stripe-success`, `/link-payment-to-passport`, `/payment-bot-*`
- **Subscription/billing** — `/current-plan`, `/current-plan/proration-preview`, `/tier-limit-exceeded`, `/admin/subscription`
- **Financial reports** — `/reports/financial`, `/reports/financial/export`, `/reports/user-contacts`
- **Email templates** — `/activity/<id>/email-templates`, `/email-preview`, `/email-test`, `/hero-image`
- **Surveys** — `/surveys`, `/create-survey`, `/survey/<token>`, `/survey/<id>/results`
- **Settings/admin** — `/admin/unified-settings`, `/setup`, `/generate-backup`, `/restore-backup/<filename>`
- **Push notifications** — `/api/push/subscribe`, `/api/push/unsubscribe`, `/api/push/status`

## Integrations

| Service | Purpose |
|---|---|
| Stripe | Credit card payments, subscriptions, proration |
| SMTP | Automated participant communication |
| Google Maps API | Primary geocoding |
| Nominatim/OpenStreetMap | Fallback geocoding |
| Google Gemini / Groq / Ollama | Optional AI chatbot providers |

Chatbot providers live in `chatbot_v2/providers/` (`gemini.py`, `groq.py`, `ollama.py`, plus `mock.py` for testing). Enabled via `CHATBOT_ENABLE_GEMINI` / `_GROQ` / `_OLLAMA` in `.env`. There is no Anthropic or OpenAI provider — older docs and a stale docstring in `chatbot_v2/ai_providers.py` claim otherwise.

## Subscription tiers

Defined in `app.py:5714-5716`:

| Key | Name | Activities | Monthly | Annual (per month) |
|---|---|---|---|---|
| `basic` | Solo | 1 | $20 | $10 |
| `pro` | Club | 15 | $50 | $25 |
| `ultimate` | Organisation | 100 | $120 | $60 |

Tenants change plans themselves at `/current-plan`. Upgrades apply immediately with Stripe proration (`proration_behavior='always_invoice'`, `app.py:856`); `/current-plan/proration-preview` computes the credit/charge breakdown shown in the confirmation modal before the tenant commits.

## Deployment model

- One Docker container per customer organization.
- Subdomains: `{customer}.minipass.me`.
- Each container mounts `instance/` and `static/uploads/` as volumes.
- Customer upgrades are handled by the existing upgrade script.

## Database changes

1. Edit `models.py`.
2. Add an idempotent task to `migrations/upgrade_production_database.py` (46 tasks so far; follow the existing `taskNN_description(cursor)` pattern).
3. Do **not** add Flask-Migrate/Alembic revisions.

Alembic exists in the repo (`flask_migrate` is imported at `app.py:44` and `migrations/versions/` holds 10 revisions), but it is **legacy and dormant** — the newest revision is from 2026-01-27, while all schema work since has gone through the idempotent tasks, including session scheduling (`task43`) and the email admin-message consolidation (`task46`, 2026-08-30).

## Security and reliability notes

- Session cookies are `HTTPONLY`, `SAMESITE=Lax`, `SECURE` in production.
- Stripe webhook signatures are verified.
- Admin-edited email text renders through a Jinja `SandboxedEnvironment` (`utils_email_text.py`), never a bare `Template` — hardening against SSTI via user-supplied signup names.
- Email sending uses `multipart/alternative` with a text/plain fallback.
- Only the QR code is sent as a CID attachment; all other images are hosted URLs.
