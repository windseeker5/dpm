# AGENTS.md — Minipass Development Guide

This is the single entry point for AI agents working on Minipass.

## First rule — test every implementation

1. **Always test the implemented result.** For every UI change, use pi's `browser-tools` or Playwright against the real local app at `http://localhost:5000`, capture the relevant desktop and mobile screenshots, **open and visually inspect those screenshots**, and verify the requested result before reporting completion. DOM values, CSS properties, computed measurements, or merely generating a screenshot do not count as visual validation. For non-UI changes, run the most relevant focused test or compile check and report it accurately.

## Response rules

1. **Answer briefly and clearly by default.** Use plain language and include only what is needed to understand the result.
2. **Put required user actions first.** If the user must do something, begin with a clearly labelled action and exact steps. Never bury an action after explanations.
3. **Lead with the result.** Do not repeat the request or add a long preamble. Add detail only when requested or needed to explain risk.

## Project in one sentence

Minipass is a Flask/Jinja SaaS for activity management: digital passports, registrations, payments (Interac auto-match + Stripe), session booking, financials, surveys, and transactional email.

## UI strategy

Minipass keeps its current **Flask + Jinja + Tabler.io** foundation. There is no framework migration planned.

Improve UI one explicitly selected page at a time using the available UI/UX skills. Preserve working behavior and avoid broad redesigns outside the requested page. Read `docs/DESIGN.md` before any UI work.

## Documentation map

| Task | Read this |
|---|---|
| Understand the product and flows | `docs/PRODUCT.md` |
| Do any UI work | `docs/DESIGN.md` |
| Do any email work | `docs/EMAIL.md` |
| Change models or migrations | `docs/ARCHITECTURE.md` |
| Set up or run the app | `README.md` |
| Lost? | `docs/README.md` |

## Hard rules

1. **Python-first.** Business logic lives in Python, not JavaScript. Use minimal vanilla JavaScript only for interactions that cannot be handled server-side.
2. **Server-side rendering.** Use Flask routes + Jinja. No React, Vue, Angular, or SPA framework.
3. **Database changes:** edit `models.py`, then add an idempotent task to `migrations/upgrade_production_database.py`. Do not add Flask-Migrate/Alembic revisions — Alembic is present but legacy and dormant since 2026-01.
4. **Browser testing:** verify every implemented UI flow with pi's `browser-tools` against the real local app at `http://localhost:5000`. Inspect the DOM first and use screenshots for visual confirmation. Verify cleanup with a direct SQLite query.
5. **Testing credentials:** when authentication is required locally, always use `kdresdell@gmail.com` / `admin123`. Do not substitute another admin account. Use these credentials only in the local development environment unless the user explicitly authorizes another environment.
6. **Test data:** always use `kdresdell@gmail.com` for any User, Passport, or Signup created during testing. Fake domains can bounce and damage email deliverability.
7. **Test artifacts:** screenshots, scripts, and test assets go in `test/`, never in the main app folder.
8. **Never start the Flask server.** Do not run `python app.py`, `flask run`, or any command that launches the dev server, in the foreground or background. The user runs and restarts it themselves so they can watch the terminal output and errors live. If the app isn't reachable at `localhost:5000`, ask the user to start it — don't start it for them.

## Dev environment

- Flask app: `app.py` on `localhost:5000` — **user-managed**, agents never start or restart it (see hard rule 8)
- Database: `instance/minipass.db` (SQLite)
- Models: `models.py`
- Templates: `templates/`
- Local admin: `kdresdell@gmail.com` / `admin123`

## Deprecated documentation

Files under `docs/.archive/` are historical only and are not tracked in git. Do not follow them.
