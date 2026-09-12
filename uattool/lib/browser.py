"""Playwright session helpers: launch, viewport presets, login."""

from contextlib import contextmanager

from playwright.sync_api import sync_playwright

from . import config


@contextmanager
def new_page(viewport="desktop", headless=False):
    """Yield a fresh logged-out page at the given viewport ("desktop" or "mobile").

    Runs headed (a real, visible Chrome window) by default so you can watch each
    row happen live during a run. slow_mo keeps clicks/fills from flashing by
    too fast to follow.
    """
    if viewport not in config.VIEWPORTS:
        raise ValueError(f"Unknown viewport {viewport!r}, expected one of {list(config.VIEWPORTS)}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, slow_mo=150 if not headless else 0)
        context = browser.new_context(
            viewport=config.VIEWPORTS[viewport],
            accept_downloads=True,
        )
        page = context.new_page()
        try:
            yield page
        finally:
            context.close()
            browser.close()


def watch_console_errors(page):
    """Attach listeners that collect JS console errors and uncaught page errors.

    Returns a list that fills in as the page runs — check it (e.g. `if errors:
    raise AssertionError(errors)`) after whatever navigation/actions you want
    covered. Attach this before navigating so nothing is missed.
    """
    errors = []
    page.on("console", lambda msg: errors.append(f"console.{msg.type}: {msg.text}") if msg.type == "error" else None)
    page.on("pageerror", lambda exc: errors.append(f"uncaught exception: {exc}"))
    return errors


def login(page, base_url=None):
    """Log in as the admin and land on the dashboard."""
    if not config.ADMIN_PASSWORD:
        raise RuntimeError(
            "UAT_ADMIN_PASSWORD is not set. Export it in your shell (or a local .env this "
            "tool loads) before running — the real password is never hardcoded in this repo."
        )
    base_url = base_url or config.BASE_URL
    page.goto(f"{base_url}/login")
    page.fill("#email", config.ADMIN_EMAIL)
    page.fill("#password", config.ADMIN_PASSWORD)
    page.click("button[type=submit]")
    page.wait_for_url(f"{base_url}/dashboard*", timeout=15000)
