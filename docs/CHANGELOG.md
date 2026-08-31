# Minipass Changelog

All notable features, improvements, and fixes documented by update date.

---

## 2026-08

### New Features
- **Session scheduling / Book Session** (#28) — Activities can offer dated sessions with limited seats (`ActivitySlot`, `SlotBooking`). Customers pick a session at signup or book later from their passport page; credits are spent at booking time and the QR scan only marks attendance. Admins can cancel a session and refund bookings. Activities with scheduling off behave exactly as before.
- **Passport inheritance** (#26) — An activity can accept passports issued by another activity, e.g. the previous season, so returning members keep the pass they already hold.

### Improvements
- **Unified passport and email design** (#29) — All 7 email templates and the public passport page (`templates/pass.html`) were rebuilt onto one visual language: photo band + solid ink bar, org identity row, grey "well" sections for Participant / Code d'accès / Séances / Historique. Shared macros consolidated in `templates/email/components.html`. See `docs/EMAIL.md`.
- **Scheduling and signup experience redesign** (#30).
- **Admin email fields consolidated** — `intro_text` + `custom_message` + `conclusion_text` merged into a single `admin_message` field, with a one-time DB sweep (`task46`).
- **Documentation consolidated** into `docs/` (#31, #32).

### Bug Fixes
- Three security issues fixed in a pre-merge audit (#29), including sandboxing admin-edited email text against SSTI.
- Hero image priority order corrected — the generic mascot was being shown ahead of an activity's own real photo in every email.
- Org logo was silently missing from every signup and survey email (`owner_logo_url` never set).
- `credit_line()` "X sur 1" bug on quantity-purchase passport types.
- Payment-first passports showed "Payé" in Facts but "En attente" in Historique forever — `approve_and_create_pass()` never set `paid_date`.
- Allow linking NO_MATCH Interac payments to pending signups (#27).

---

## 2026-05

### Bug Fixes
- Prevent duplicate Interac notification emails from creating ghost inbox entries (#25).

---

## 2026-04

### Improvements
- **Plan change hardening** (#13–#19) — Extensive work on tenant self-service upgrade / downgrade / cancel, including syncing plan state between the container, the customer database, and the website. 13 separate security issues addressed in the final pass.
- **Announcement / broadcast to large groups** (#21–#24) — Four rounds of fixes to sending announcements to large recipient groups.
- **Match a payment to an existing passport** (#12) — Handles the case where a parent pays by Interac for a child's passport. Financial CSV export gained a passport-number column.

### Bug Fixes
- Duplicate payment detection now validates each notification email's UID instead of guessing from a 5-minute window (#20).
- Redeem-after-search bug (#19).

### Security
- Removed a `pytest/` directory containing exposed SMTP credentials (#11).

---

## 2026-03

### New Features
- **Forgot-password tool** — Self-service password reset valid for one hour, synced back to the customer database.
- **Payment method tracking** — Interac vs Stripe now visible in the Activity Log and recorded through the Mark as Paid flow.
- **Passport status indicators** on the passport table and activity dashboard.

### Improvements
- **Performance** — Dead dependencies stripped, database indexes added, caching and image compression introduced.
- **Activity form simplified**, financial report normalized for desktop and mobile.
- Signup confirmation pages unified into a single template.
- Settings section simplified — backup, restore and data reset merged into one cleaner interface.
- Terminology normalized across the app ("check-in" instead of "reading").
- Push notification, Stripe and Interac payment visuals normalized.

### Bug Fixes
- Stripe accounting — Stripe passports excluded from cash-basis KPIs.
- Pay-first flow: session calculation, email spam triggers, image hosting and deliverability.
- Archiving an activity that still had active passports.
- Failed-email resume button.
- Network ID assignment for newly deployed customers.
- Organization logo upload rendering with a black background.
- Search bar interfering with action buttons.
- KPI trends hidden correctly when "all time" is selected.

---

## 2026-02 (mid–late February)

### New Features
- **Stripe subscription financing** and webhook URL surfaced in settings for tenant setup.
- **Reply-To extraction from Interac notifications** — the sender's email is captured and reused when creating a passport from an unmatched payment.
- **Version indicator** in the footer, derived from the current commit.

### Improvements
- **Email infrastructure aligned to RFC 5322**, including date formatting.
- **Hero image normalization** — size, resolution and transparency standardized so images work against both light and dark email clients, with automatic crop/resize of unsuitable uploads.
- Pagination normalized across every table (activity log, dashboard, passports, activities).
- Login page redesigned for desktop and mobile, using the organization logo or a PWA-consistent fallback.
- Signup page and post-signup thank-you page improved, especially on mobile.
- QR scanner UI and cover photo tooling (compression, crop) improved.

### Bug Fixes
- QR scan security scoped per activity.
- Fuzzy-match setting now honored for payment descriptions instead of a hardcoded 50% threshold.
- Passport quantity vs. passport-type session count when creating from an unmatched payment.
- Settings first/last name change, and activity-data reset leaving admin data intact.

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
