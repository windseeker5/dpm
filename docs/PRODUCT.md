# Minipass Product Reference

**What it is:** A SaaS platform for organizations that run activities: sports leagues, fitness classes, coaching, tournaments, and small-business loyalty programs.

**Status:** Production — 2 live customers (LHGI, Hockey Coach). One container per customer, single-tenant SQLite.

## Core value proposition

1. **Sell a passport** (a pack of credits or a membership).
2. **Collect registrations and payments** automatically.
3. **Let customers book into dated sessions** when the activity uses scheduling.
4. **Track attendance** via QR scan.
5. **Handle money** with built-in financial reporting.

## Feature inventory

### 1. Digital Passport Management
- Create digital passports with QR codes.
- Distribute via email automatically.
- Track status: sent, opened, redeemed.
- QR scan interface for redemption.
- Custom payment instructions per passport type.
- **Passport inheritance** — an activity can accept passports issued by another activity (e.g. the previous season), so returning members keep using the pass they already hold.

### 2. Registration System
- Customizable registration forms per activity.
- **Dual signup workflow:** payment-first OR approval-first.
- Automated email confirmations.
- Capacity management.

### 3. Payments
- **Automatic e-transfer/Interac matching** from a monitored inbox.
- **Stripe credit card payments** through signup forms.
- Payment inbox dashboard: MATCHED, NO_MATCH, MANUAL_PROCESSED.
- One-click passport creation from unmatched payments.

### 4. Session Booking *(Book Session)*
- Activities can enable dated sessions with limited seats.
- Customers pick a session at signup, or book later from their passport page.
- Credits are spent at booking time; scanning the QR at the door only marks attendance.
- Admins can cancel a session and refund bookings.
- Sessions off = existing behavior is unchanged.

### 5. Email Communication
- 7 transactional email templates, redesigned August 2026.
- Per-activity customization: subject, title, message, hero image, org logo, QR toggle.
- See `docs/EMAIL.md` for the design system and sending rules.

### 6. KPI Dashboard
- Revenue, passports created, active passports, pending signups, payment status, survey scores.
- Clickable activity cards.

### 7. Financial Management
- Cash basis and accrual basis reporting.
- Income and expense tracking with categories.
- Receipt uploads.
- CSV export.
- Fiscal year configuration.

### 8. Admin & Settings
- Admin profile, SMTP/org branding, custom payment email, Stripe keys, fiscal year, QR toggle.

### 9. Data Ownership
- SQLite export, backup/restore, automated daily backups.

### 10. Self-Service Plan Management
- Tenants upgrade/downgrade their own plan at `/current-plan`.
- Proration preview before committing: credit for unused time, prorated new charge, net amount.
- Upgrades apply immediately; downgrades take effect at renewal.
- Activity-limit enforcement with an archive-or-upgrade prompt when the cap is hit.

### 11. Wayne Data Assistant
- English/French questions over the organization's own data.
- Trusted Python skills execute predefined queries; the model never writes SQL.
- Obvious questions route locally. OpenRouter selects an approved skill only when wording is ambiguous.
- Wayne only answers questions about data stored in minipass.
- Queries are audited in `QueryLog`.

### 12. Push Notifications
- Web push subscriptions (`PushSubscription`) for admin alerts, e.g. new signups.

## Pricing tiers

Defined in `app.py:5714-5716`:

| | Solo | Club | Organisation |
|---|---|---|---|
| Active activities | 1 | 15 | 100 |
| Monthly | $20 | $50 | $120 |
| Annual (per month) | $10 | $25 | $60 |

**Active activity count is the only limit enforced in code.** Every other feature — payment matching, email templates, financial management, Stripe payments, session booking, surveys, AI chatbot — is available on all tiers; there is no per-feature tier gate anywhere in the codebase. Treat any feature-by-tier matrix on the marketing site as packaging intent, not as something the app enforces.

Tenants change plans themselves at `/current-plan`, with Stripe proration previewed before they commit.

## Technical stack

| Layer | Technology |
|---|---|
| Backend | Flask (Python) |
| Frontend | Server-rendered Jinja2 + Tabler.io |
| Database | SQLite per customer |
| Auth | Session-based |
| File storage | Local filesystem |
| Deployment | Docker per customer, nginx reverse proxy, Let's Encrypt |
| Email | SMTP with Premailer CSS inlining, Bleach sanitization |

## Key models

`Admin`, `User`, `Activity`, `PassportType`, `Passport`, `Signup`, `Redemption`, `ActivitySlot`, `SlotBooking`, `EbankPayment`, `StripeTransaction`, `Income`, `Expense`, `Setting`, `Survey`, `SurveyTemplate`, `SurveyResponse`, `EmailLog`.

The Book Session feature's models are `ActivitySlot` and `SlotBooking` — there are no models named `Session` or `Booking`. Full list in `docs/ARCHITECTURE.md`.

## UI direction

Minipass keeps its Flask/Jinja/Tabler foundation. Selected pages are improved individually with the UI/UX skills rather than through a framework-wide migration. See `docs/DESIGN.md`.
