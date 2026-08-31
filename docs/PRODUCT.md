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

## Pricing tiers

| Feature | Starter | Professional | Enterprise |
|---|---|---|---|
| Active activities | 1 | 10 | 100 |
| Payment matching | ✅ | ✅ | ✅ |
| Email templates | ✅ | ✅ | ✅ |
| Financial management | ✅ | ✅ | ✅ |
| Stripe payments | ✅ | ✅ | ✅ |
| Session booking | ✅ | ✅ | ✅ |
| Surveys | — | ✅ | ✅ |
| AI analytics chatbot | — | ✅ | ✅ |

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

`Admin`, `User`, `Activity`, `PassportType`, `Passport`, `Signup`, `Redemption`, `Session`, `Booking`, `EbankPayment`, `Income`, `Expense`, `Setting`, `Survey`, `SurveyTemplate`, `SurveyResponse`, `EmailLog`.

## UI direction

Minipass keeps its Flask/Jinja/Tabler foundation. Selected pages are improved individually with the UI/UX skills rather than through a framework-wide migration. See `docs/DESIGN.md`.
