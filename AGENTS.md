# AGENTS.md

## Documentation Index

**Read relevant docs before starting any task.**

- `docs/PRODUCT.md` — Complete feature inventory and system architecture (read for feature context)
- `docs/DESIGN_SYSTEM.md` — Tabler.io UI component patterns (read for ANY template/UI work)
- `docs/EMAIL_TEMPLATE_SYSTEM.md` — Email template system (read for ANY email-related work)
- `docs/EMAIL_DELIVERABILITY.md` — **RFC 5322 compliance, image hosting rules, spam triggers, CID policy** (read for ANY email template or send_email() work)
- `docs/CHANGELOG.md` — Recent feature updates and changes (read when you need recent context)
- `docs/UPGRADE_AND_DEPLOY.md` — Production deployment procedures (read for deployment tasks)

---

## ⛔ UI RULES — READ FIRST

### We use TABLER.IO — NOT Bootstrap, NOT Tailwind, NOT custom CSS

**Before ANY UI work:**
1. **READ `docs/DESIGN_SYSTEM.md`** — Search for the section you need
2. **COPY from existing templates** — `templates/dashboard.html`, `templates/passports.html`
3. **NO `<style>` blocks** — Everything uses Tabler classes

**After ANY UI work:**
4. **Audit the changed template(s) for accessibility/UX** — ARIA, focus states, touch targets, keyboard nav, semantic HTML — as a quality gate before considering the work done

### DESIGN_SYSTEM.md Quick Index:
| Need | Section |
|------|---------|
| Page layout | Section 12 |
| Tables | Section 6 |
| Search bars | Section 4 |
| Filters | Section 5 |
| Empty states | Section 7 |
| Form buttons | Section 13 |

### ❌ BANNED — Delete if you write this:
```html
<style> anything </style>
box-shadow, gradient, transform, animation
class="custom-anything"
class="my-anything"
```

### ✅ USE TABLER CLASSES:
```html
<div class="card">
<div class="container-xl">
<a class="btn btn-primary">
<table class="table table-vcenter card-table">
```

---

## Project Info

**Minipass** — SaaS for activity management (sports leagues, fitness classes, loyalty programs)

| Component | Location |
|-----------|----------|
| Flask app | `app.py` (runs on `localhost:5000`) |
| Models | `models.py` |
| Templates | `templates/` (Jinja2 + Tabler.io) |
| Database | `instance/minipass.db` (SQLite) |
| Design system | `docs/DESIGN_SYSTEM.md` |

---

## Development Rules

### Python-first
- Business logic in Python, not JavaScript
- JS only for small UI interactions (<10 lines per function)
- No React, Vue, Angular

### Testing
- Unit tests: `python -m unittest test.test_kpi_data -v`
- **MANDATORY — test every implemented plan with Playwright MCP against the real local dev environment** (`http://localhost:5000`, the actual running Flask app and dev database) — not just test-client scripts or DB copies. Scripted/simulated tests can silently target the wrong database and don't exercise real templates, JS, CSRF, or session behavior.
  - Login: `kdresdell@gmail.com` / `admin123` (local dev admin only)
  - After testing, verify cleanup with a direct DB query (`sqlite3 instance/minipass.db "SELECT ..."`), not just through the app/ORM — ORM identity-map caching across multiple requests can make a deletion look like it failed (or succeeded) when it didn't
- **MANDATORY — never use a fake or placeholder email** (`example.com`, `test@test.com`, etc.) for any `User`, `Passport`, or `Signup` created during testing, whether created through the UI or inserted directly for test setup. This app sends real SMTP email on passport/signup/redemption/payment actions — fake domains bounce and risk the sending Gmail account being flagged or banned. **Always use `kdresdell@gmail.com`** instead.
- **Test artifacts location**: Save ALL test files (screenshots, test scripts, images) in `test/` folder — NOT in the main `app/` folder

### Database changes
1. Edit `models.py`
2. Add migration to `migrations/upgrade_production_database.py`
3. Do NOT use Flask-Migrate

---

## What's Already Running

- Flask server: `localhost:5000` (always on, debug mode)
- Database: SQLite configured
- Tabler CSS: loaded globally in `base.html`

---

## Common Commands

```bash
source venv/bin/activate
python -m unittest test.test_kpi_data -v
```
