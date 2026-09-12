"""Row 00 — Preflight: log in, confirm the target tenant is reachable and behaving.

Runs the login+dashboard check once per viewport (desktop, then mobile) and
fails the row if the browser logged any JS console error or uncaught
exception during the process — not just if the page loaded.
"""

from lib.browser import new_page, login, watch_console_errors


def _check_viewport(ctx, viewport_label):
    with new_page(viewport=viewport_label) as page:
        errors = watch_console_errors(page)

        login(page, base_url=ctx.base_url)
        ctx.note(f"[{viewport_label}] Logged in to {ctx.base_url} as admin, landed on dashboard.")

        # Sanity check we're talking to the real app, not a maintenance/error page.
        page.goto(f"{ctx.base_url}/dashboard")
        title = page.title()
        if not title:
            raise AssertionError(f"[{viewport_label}] Dashboard loaded with no page title — target may not be healthy.")
        ctx.note(f"[{viewport_label}] Dashboard page title: {title!r}")

        ctx.screenshot(page, f"dashboard_after_login_{viewport_label}")

        if errors:
            raise AssertionError(f"[{viewport_label}] JS console error(s) during login/dashboard load: {errors}")
        ctx.note(f"[{viewport_label}] No JS console errors during login/dashboard load.")


def run(ctx):
    _check_viewport(ctx, "desktop")
    _check_viewport(ctx, "mobile")
