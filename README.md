# Minipass

**A SaaS platform for organizations that run activities** — sports leagues, fitness classes, coaching, tournaments, and small-business loyalty programs.

Minipass sells digital passports (a pack of credits or a membership), collects registrations and payments automatically, lets customers book into dated sessions, tracks attendance by QR scan, and handles the financial reporting behind it. It runs as a progressive web app, one container per customer.

## Stack

| Layer | Technology |
|---|---|
| Backend | Flask (Python) |
| Frontend | Server-rendered Jinja2 + Tabler.io |
| Database | SQLite, one per customer |
| Auth | Session-based |
| Payments | Stripe + automated Interac e-transfer matching |
| Email | SMTP with Premailer CSS inlining |
| Deployment | Docker per customer, nginx reverse proxy, Let's Encrypt |

## Running locally

```bash
cd app
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

The app serves on **http://localhost:5000** in debug mode. Configuration comes from `.env`; the database lives at `instance/minipass.db`.

> In debug mode all outgoing mail is redirected to `MAIL_USERNAME` from `.env`, regardless of the recipient the code asks for.

## Sanity check

```bash
python -m py_compile app.py utils.py models.py api/settings.py decorators.py
python -m compileall .
```

## Testing

Test every UI flow against the real running app at `localhost:5000`, not just scripts or database inspection — scripts can silently target the wrong database and never exercise real templates, JavaScript, CSRF, or session behavior.

- Always use `kdresdell@gmail.com` for any User, Passport, or Signup created during testing. The app sends real mail; fake domains bounce and damage sending reputation.
- Verify cleanup with a direct SQLite query, not through the ORM.
- Keep screenshots, scripts, and test assets in `test/`.
- Email testing: see the Testing section of [`docs/EMAIL.md`](docs/EMAIL.md).

## Documentation

| Doc | Purpose |
|---|---|
| [`AGENTS.md`](AGENTS.md) | Rules for AI agents working in this repo — start here |
| [`docs/PRODUCT.md`](docs/PRODUCT.md) | What Minipass is, who it serves, core flows |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Stack, models, routes, integrations, migrations |
| [`docs/DESIGN.md`](docs/DESIGN.md) | Page-by-page UI/UX workflow and quality rules |
| [`docs/EMAIL.md`](docs/EMAIL.md) | Email system, design language, and how to test all 7 templates |
| [`docs/CHANGELOG.md`](docs/CHANGELOG.md) | Shipped features, improvements, and fixes by date |

## Database changes

Edit `models.py`, then add an idempotent task to `migrations/upgrade_production_database.py`. Do not add Alembic revisions — see `docs/ARCHITECTURE.md`.

---

**Developer:** Ken Dresdell — kdresdell@gmail.com
