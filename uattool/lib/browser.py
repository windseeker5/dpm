"""Playwright session helpers: launch, viewport presets, login.

Two things happen here that the 24 files in scripts/ never have to know about:

  * **One browser per row, not per block.** Each `with new_page(...)` used to
    call chromium.launch() — a full browser start/stop, ~40 of them in a full
    run. lib/runner.py now opens one browser per catalog row and new_page()
    just makes a fresh *context* on it. Contexts are still fully isolated, so a
    logged-out guest page in row 02 stays logged out.
  * **Instrumentation.** Every context gets a Playwright trace and a DOM-level
    listener that reports clicks and field changes to the run's event bus, so
    the live dashboard shows a step-by-step log without a single script edit.

new_page()'s signature is unchanged on purpose — scripts/ is untouched.
"""

import os
from contextlib import contextmanager

from playwright.sync_api import sync_playwright

from . import config

# Set by lib/runner.py for the duration of one catalog row. None when a script
# is imported and run on its own, in which case new_page() falls back to
# launching (and tearing down) its own browser per call, exactly as before.
_session = None

# Reports clicks and field changes from inside the page. Deliberately reads no
# input values: login() fills the real admin password on every single row, and
# this text ends up in events.jsonl and on screen.
_STEP_PROBE = """
(() => {
  if (window.__uatStepProbe) return;
  window.__uatStepProbe = true;
  const isSecret = (el) =>
    el && el.tagName === 'INPUT' &&
    ['password', 'hidden'].includes((el.getAttribute('type') || '').toLowerCase());
  const label = (el) => {
    if (!el || !el.tagName) return '?';
    const tag = el.tagName.toLowerCase();
    if (el.id) return tag + '#' + el.id;
    if (el.getAttribute && el.getAttribute('name')) return tag + '[name=' + el.getAttribute('name') + ']';
    let out = tag;
    const cls = typeof el.className === 'string' ? el.className.trim().split(/\\s+/)[0] : '';
    if (cls) out += '.' + cls;
    if (tag !== 'input' && tag !== 'select' && tag !== 'textarea') {
      const txt = (el.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 40);
      if (txt) out += ' "' + txt + '"';
    }
    return out;
  };
  document.addEventListener('click', (e) => {
    const target = (e.target.closest && e.target.closest('button, a, label, input, select, [role=button], .btn')) || e.target;
    if (isSecret(target)) return;
    console.debug('[uat-step] click ' + label(target));
  }, true);
  document.addEventListener('change', (e) => {
    if (isSecret(e.target)) return;
    console.debug('[uat-step] fill ' + label(e.target));
  }, true);
})();
"""


def start_row_session(order, row_dir, bus, headless=None):
    """Open one browser for a catalog row. Called by lib/runner.py."""
    global _session
    stop_row_session()
    headless = config.HEADLESS if headless is None else headless
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=headless, slow_mo=0 if headless else 150)
    _session = {
        "pw": pw, "browser": browser, "headless": headless,
        "order": order, "row_dir": row_dir, "bus": bus, "traces": 0,
    }
    return _session


def stop_row_session():
    global _session
    if not _session:
        return
    try:
        _session["browser"].close()
    finally:
        try:
            _session["pw"].stop()
        finally:
            _session = None


def _emit(kind, **fields):
    if _session and _session.get("bus"):
        _session["bus"].emit(kind, order=_session["order"], **fields)


def _next_trace_path():
    """reports/<run_id>/<row>/trace_<n>.zip, or None when running standalone."""
    if not _session or not _session.get("row_dir"):
        return None
    _session["traces"] += 1
    os.makedirs(_session["row_dir"], exist_ok=True)
    return os.path.join(_session["row_dir"], f"trace_{_session['traces']}.zip")


def _instrument(page, viewport):
    """Turn page/DOM activity into `step` events on the run's event bus."""
    if not (_session and _session.get("bus")):
        return

    def on_console(msg):
        if msg.type != "debug":
            return
        text = msg.text or ""
        if text.startswith("[uat-step] "):
            _emit("step", text=f"[{viewport}] {text[len('[uat-step] '):]}")

    def on_navigated(frame):
        if frame != page.main_frame:
            return
        url = frame.url or ""
        if not url or url == "about:blank":
            return
        # Strip the origin — every row targets the same base_url, so the path is
        # the only part that tells you anything.
        shown = url[len(config.BASE_URL):] if url.startswith(config.BASE_URL) else url
        _emit("step", text=f"[{viewport}] goto {shown or '/'}")

    page.on("console", on_console)
    page.on("framenavigated", on_navigated)
    page.on("download", lambda d: _emit("step", text=f"[{viewport}] download {d.suggested_filename}"))
    page.on("pageerror", lambda exc: _emit("step", text=f"[{viewport}] ⚠ uncaught exception: {exc}", level="error"))


@contextmanager
def new_page(viewport="desktop", headless=None):
    """Yield a fresh logged-out page at the given viewport ("desktop" or "mobile").

    Reuses the current row's browser when lib/runner.py has opened one (a new
    isolated context per call), and otherwise launches its own. `headless`
    defaults to config.HEADLESS (`--headed` on run_uat.py flips it); pass it
    explicitly to force one call's mode regardless, as _simulate_payment.py does.
    """
    if viewport not in config.VIEWPORTS:
        raise ValueError(f"Unknown viewport {viewport!r}, expected one of {list(config.VIEWPORTS)}")

    want_headless = config.HEADLESS if headless is None else headless
    reuse = _session is not None and _session["headless"] == want_headless

    if reuse:
        with _page_on(_session["browser"], viewport) as page:
            yield page
        return

    # No row session, or this call wants the opposite headless mode from the
    # row's browser (_simulate_payment.py forces headless=True even under
    # --headed). Launch a second browser for it — reusing the row's *Playwright
    # instance* when there is one, since the sync API doesn't like two live
    # instances on the same thread.
    if _session:
        browser = _session["pw"].chromium.launch(
            headless=want_headless, slow_mo=0 if want_headless else 150
        )
        try:
            with _page_on(browser, viewport) as page:
                yield page
        finally:
            browser.close()
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=want_headless, slow_mo=0 if want_headless else 150)
        try:
            with _page_on(browser, viewport) as page:
                yield page
        finally:
            browser.close()


@contextmanager
def _page_on(browser, viewport):
    context = browser.new_context(
        viewport=config.VIEWPORTS[viewport],
        accept_downloads=True,
    )
    trace_path = _next_trace_path()
    if trace_path:
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
    context.add_init_script(_STEP_PROBE)
    page = context.new_page()
    _instrument(page, viewport)
    try:
        yield page
    finally:
        if trace_path:
            try:
                context.tracing.stop(path=trace_path)
            except Exception:  # noqa: BLE001 - a broken trace must never fail a row
                pass
        context.close()


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


def post_as_admin(page, path, base_url=None):
    """Submit an admin action that the app only accepts as a POST (with its CSRF token),
    the way the real button's form does — e.g. approving a signup or running the payment bot.

    The page must already be logged in. It lands wherever the app redirects after the action.
    """
    base_url = base_url or config.BASE_URL
    if not page.locator('meta[name="csrf-token"]').count():
        page.goto(f"{base_url}/dashboard")
    with page.expect_navigation(timeout=60000):
        page.evaluate(
            """(action) => {
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = action;
                const token = document.createElement('input');
                token.type = 'hidden';
                token.name = 'csrf_token';
                token.value = document.querySelector('meta[name="csrf-token"]').content;
                form.appendChild(token);
                document.body.appendChild(form);
                form.submit();
            }""",
            f"{base_url}{path}",
        )
    page.wait_for_load_state("networkidle", timeout=60000)


def thank_you_value(url):
    """The signup id (int) or cart code (str) behind a public thank-you page URL.

    Those pages are addressed by a signed token (so strangers can't enumerate other buyers'
    receipts), but the payload itself isn't secret — only the signature is — so it can be
    read back here without the app's secret key.
    """
    from itsdangerous import URLSafeSerializer

    token = url.split("?")[0].rstrip("/").split("/")[-1]
    _valid, value = URLSafeSerializer("unused").loads_unsafe(token)
    if value is None:
        raise AssertionError(f"Could not read the thank-you token in {url!r}")
    return value
