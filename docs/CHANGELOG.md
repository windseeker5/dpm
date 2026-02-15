# Minipass Changelog

All notable features, improvements, and fixes documented by update date.

---

## 2026-02-08

### New Features
- **Stripe credit card payments** — Accept credit card payments via Stripe. Customers configure API keys in Settings. Guide at minipass.me/guides.
- **Dual signup workflow** — Two modes: payment-first (participant pays before enrollment) and approval-first (admin approves before payment). Handles large volumes (5,000+ participants) with duplicate name handling.
- **Financial report integrated into activity page** — Activity financials now based on SQL accounting views. Single source of truth across activity page and official reports.
- **7th email template** — Added to the email communication system.

### Improvements
- **Redesigned signup page** — Modernized form, improved desktop/mobile experience, Interac logo with better payment indications.
- **Activity page overhaul** — Entirely redesigned for better UX. Standardized and validated financial information display.
- **Clickable activity cards on dashboard** — Cards are now directly clickable, "Manage" button removed for simpler navigation.
- **Post-save redirect** — Saving an activity now redirects to dashboard instead of staying on the page.
- **Password management** — Reset and change password directly in Settings.
- **Default photos/logos** — Professional visuals displayed even when no cover photo or org logo uploaded.
- **Simplified location workflow** — Finding, selecting, and editing locations is now streamlined.
- **Email template cleanup** — Templates cleaned up and simplified for clarity and maintainability.

### Bug Fixes
- Fixed legacy email display on signup page when payment-first mode enabled.
- Fixed per-activity organization logo display.
- Fixed password change/reset functionality.
- Fixed passport creation from unmatched payment when phone/email field left empty.

---

## 2026-01-29

### New Features
- **Create passport from unmatched payment** — Create a passport directly from an unmatched (no_match) payment in the payment inbox. No need to manually create then match.

### Improvements
- **Standardized notification messages** — All flash messages use consistent styles: green (success), red (error), orange (warning). Uniform icons across the app.
- **Auto-completion deduplication** — When creating a passport, name/email/phone suggestions no longer show duplicates. Only most recent info shown.

### Bug Fixes
- Activity page revenue now aligned with official financial reports.
- Fixed timezone display issues across multiple pages.
- Fixed passport creation date in history email (correct timezone).
- Fixed confirmation message after payment matching to show correct status.

---

## 2026-01-27

### New Features
- **Custom payment email address** — Specify a different email address for payment instructions in automated emails to members.

### Bug Fixes
- AR/AP filtering by fiscal year now works correctly.
- Mobile KPI indicators display correctly with fiscal year.
- Passport creation dropdown now shows only active activities.

---

## 2026-01 (Early January)

### New Features
- **Custom fiscal year configuration** — Set fiscal year start month (1-12) in Settings. All reports and KPIs align automatically.
- **QR code toggle** — Option to disable QR codes in email templates (Settings > Advanced > Email Templates).

### Improvements
- **Email template defaults improved** — 6 default templates rewritten for clarity and simplicity.

---

## 2025-11 (Production Launch)

### Milestones
- **Official launch** with 2 production customers (LHGI, Hockey Coach).
- **Automated customer provisioning** via Stripe webhooks active.

### Features at Launch
- Digital passport management with QR codes
- Automatic e-transfer payment matching
- 6 customizable email templates with 3-tier hero image system
- Payment inbox and management dashboard
- Complete financial management suite (dual accounting: cash + accrual)
- User contacts export with CRM/marketing CSV
- Activity location management (Google Maps + OpenStreetMap)
- AI analytics chatbot (5 providers: Gemini, Groq, Anthropic, OpenAI, Ollama)
- Survey system with template library and 3-click deployment
- Admin personalization (names, avatars)
- Complete data ownership (backup & restore)
- KPI dashboard with real-time updates
- Registration forms with capacity management
