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
| `app.py` | Flask routes and request handlers |
| `models.py` | SQLAlchemy models |
| `utils.py` | Email context, sending, helpers |
| `utils_email_defaults.py` | Default email template text |
| `utils_email_text.py` | Sandboxed Jinja rendering for admin-edited text |
| `config/email_defaults.json` | Default subject/title/message/CTA per email type |
| `migrations/upgrade_production_database.py` | Idempotent production migrations |

## Models

| Model | Purpose |
|---|---|
| `Admin` | Admin users and authentication |
| `User` | Participants/customers |
| `Activity` | Activities/programs |
| `PassportType` | Types of passes within an activity |
| `Passport` | Individual digital passes with QR codes |
| `Signup` | Registration records |
| `Redemption` | Pass usage / attendance log |
| `Session` | Dated session with seats |
| `Booking` | Link between a passport and a session |
| `EbankPayment` | Incoming e-transfer payment emails |
| `Income` / `Expense` | Financial transaction records |
| `Setting` | Organization settings (key-value) |
| `Survey` / `SurveyTemplate` / `SurveyResponse` | Survey system |
| `QueryLog` | AI chatbot query audit trail |
| `EmailLog` | Email sending history |

## Integrations

| Service | Purpose |
|---|---|
| Stripe | Credit card payments, subscriptions |
| SMTP | Automated participant communication |
| Google Maps API | Primary geocoding |
| Nominatim/OpenStreetMap | Fallback geocoding |
| Google Gemini / Groq / Anthropic / OpenAI / Ollama | Optional AI chatbot providers |

## Deployment model

- One Docker container per customer organization.
- Subdomains: `{customer}.minipass.me`.
- Each container mounts `instance/` and `static/uploads/` as volumes.
- Customer upgrades are handled by the existing upgrade script (not by `docs/.archive/UPGRADE_AND_DEPLOY.md`).

## Database changes

1. Edit `models.py`.
2. Add an idempotent task to `migrations/upgrade_production_database.py`.
3. Do **not** use Flask-Migrate.

## Security and reliability notes

- Session cookies are `HTTPONLY`, `SAMESITE=Lax`, `SECURE` in production.
- Stripe webhook signatures are verified.
- Email sending uses `multipart/alternative` with a text/plain fallback.
- Only the QR code is sent as a CID attachment; all other images are hosted URLs.
