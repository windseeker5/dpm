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

1. **Testing is mandatory.** Follow the first rule above. Never claim visual verification without opening and inspecting the captured screenshot.
2. **Brand spelling.** Always write the product name as `minipass` in lowercase—never `Minipass`, `MiniPass`, or any other capitalization.
3. **Python-first.** Business logic lives in Python, not JavaScript. Use minimal vanilla JavaScript only for interactions that cannot be handled server-side.
4. **Server-side rendering.** Use Flask routes + Jinja. No React, Vue, Angular, or SPA framework.
5. **Database changes:** edit `models.py`, then add an idempotent task to `migrations/upgrade_production_database.py`. Do not add Flask-Migrate/Alembic revisions — Alembic is present but legacy and dormant since 2026-01.
6. **Testing credentials:** when authentication is required locally, always use `kdresdell@gmail.com` / `admin123`. Do not substitute another admin account. Use these credentials only in the local development environment unless the user explicitly authorizes another environment.
7. **Test data:** always use `kdresdell@gmail.com` for any User, Passport, or Signup created during testing. Fake domains can bounce and damage email deliverability.
8. **Test artifacts:** screenshots, scripts, and test assets go in `test/`, never in the main app folder.
9. **Never start or restart the Flask server.** Do not run `python app.py`, `flask run`, kill the process, or ask the user to restart after ordinary code, template, static-file, or `.env` edits. The local app runs in debug mode specifically so edits reload automatically. If the app is not reachable at `localhost:5000`, ask the user to start it; otherwise rely on debug auto-reload and inspect the live result.
10. **Buttons: use the standard component, never hand-roll one.** Use `{% from 'macros/buttons.html' import button %}` / `{{ button(...) }}` (`templates/macros/buttons.html`, styled by `static/css/mp-components.css`) for every button. Do not add new `btn-success`/`btn-danger`/inline-color buttons or new bespoke `.btn-*` CSS classes. If the macro can't do what you need, extend the macro/CSS — don't improvise a one-off.
11. **Row/card actions: use the standard Action Menu, never a loose row of buttons.** Use `{% from 'macros/action_menu.html' import action_menu %}` / `{{ action_menu(id=..., items=[...]) }}` (styled by `static/css/mp-components.css`, wired by `static/js/mp-action-menu.js`) for View/Edit/Delete-style row actions. See both live at `/style-guide`.
12. **Typography: h1-h5 are global, never hardcode size/color/font on a page.** The scale is set once in `templates/base.html` (Inter, fixed rem sizes, validated against impeccable's typeset.md/operate.md). Body/description text uses the `.mp-text-body` class from `static/css/mp-components.css`. Do not add a page-local `<style>` overriding heading font-size, color, or font-family — if a heading looks wrong, fix the shared rule, not the page. See `/style-guide`.
13. **Table/list filter tabs: use the Filter Tabs macro, never hand-roll the segmented control.** Use `{% from 'macros/filter_tabs.html' import filter_tabs %}` / `{{ filter_tabs(tabs=[...]) }}` — styled by `.mp-filter-tabs`/`.mp-filter-btn` in `static/css/mp-components.css` (the same `--mp-*` tokens as Button/Action Menu), not the older `.github-filter-*` classes in `static/css/filter-component.css` (off-system GitHub-Primer palette, still used by the 9 live pages below — leave those alone). Do not add inline `style=""` to a tab, that's the exact problem this macro exists to stop. Not yet migrated into any real page (`activities.html`, `signups.html`, `passports.html`, `surveys.html`, `survey_templates.html`, `payment_bot_matches.html`, `user_contacts_report.html`, `survey_results.html`, `activity_dashboard.html` still hand-roll the old version as of this writing) — that migration is a separate, not-yet-approved task. See `/style-guide`.

## Dev environment

- Flask app: `app.py` on `localhost:5000` — **user-managed**, agents never start or restart it (see hard rule 8)
- Database: `instance/minipass.db` (SQLite)
- Models: `models.py`
- Templates: `templates/`
- Local admin: `kdresdell@gmail.com` / `admin123`

## Deprecated documentation

Files under `docs/.archive/` are historical only and are not tracked in git. Do not follow them.
