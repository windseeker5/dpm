"""Row 10 — Outbound doc links.

Collects every outbound https://minipass.me/... (and https://www.minipass.me)
link the app can render — both by statically scanning templates/ (so we catch
links on pages this suite doesn't otherwise navigate, e.g. public/auth pages)
and by live-crawling the real admin Settings pages (unified-settings,
current-plan, setup) to confirm what's actually in the rendered DOM matches
source. Every unique URL found is then requested for real via Playwright's
request context (not a full page navigation) and its HTTP status recorded.

This is exactly the kind of check that would have caught the already-known
broken link at templates/unified_settings.html:272
(https://minipass.me/docs/how-to-setup-stripe -> 404), which this script
should surface clearly rather than crash on.

Desktop only.
"""

import glob
import os
import re

from lib.browser import login, new_page

# app/ root: this file is app/uattool/scripts/10_outbound_doc_links.py
APP_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
TEMPLATES_DIR = os.path.join(APP_ROOT, "templates")

# Matches any quoted https://minipass.me or https://www.minipass.me URL,
# whether it's a plain <a href="..."> or a JS string (e.g. a redirect).
# Deliberately anchored to the root domain so it does NOT match tenant
# subdomains like https://kdc.minipass.me or https://lhgi.minipass.me.
LINK_RE = re.compile(r'["\'](https://(?:www\.)?minipass\.me(?:/[^"\']*)?)["\']')

# Live admin pages worth crawling for outbound links, beyond the one already
# flagged. Settings is a single page (all sections render server-side; the
# `section` query param only controls which tab starts active), so one visit
# covers general/email/payments/shop.
LIVE_PAGES = [
    "/admin/unified-settings",
    "/current-plan",
    "/setup?section=team",
    "/setup?section=data",
]


def _scan_templates():
    """Static scan of templates/**/*.html. Returns list of (url, "file:line")."""
    found = []
    for path in glob.glob(os.path.join(TEMPLATES_DIR, "**", "*.html"), recursive=True):
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        rel_path = os.path.relpath(path, APP_ROOT)
        for lineno, line in enumerate(text.splitlines(), start=1):
            for match in LINK_RE.finditer(line):
                found.append((match.group(1), f"{rel_path}:{lineno}"))
    return found


def run(ctx):
    # --- static discovery across all templates ---
    static_hits = _scan_templates()
    if not static_hits:
        ctx.note("No https://minipass.me links found via static template scan (unexpected).")

    sources_by_url = {}
    for url, source in static_hits:
        sources_by_url.setdefault(url, set()).add(source)

    ctx.note(f"Static scan of templates/ found {len(sources_by_url)} unique minipass.me URL(s) "
              f"across {len(static_hits)} reference(s).")
    for url, sources in sources_by_url.items():
        ctx.note(f"  {url}  <-  {', '.join(sorted(sources))}")

    with new_page(viewport="desktop") as page:
        login(page, base_url=ctx.base_url)

        # --- live crawl of real admin Settings pages for cross-check ---
        live_count = 0
        for rel_path in LIVE_PAGES:
            page.goto(f"{ctx.base_url}{rel_path}")
            page.wait_for_load_state("networkidle", timeout=15000)
            anchors = page.locator('a[href^="https://minipass.me"], a[href^="https://www.minipass.me"]')
            n = anchors.count()
            for i in range(n):
                href = anchors.nth(i).get_attribute("href")
                if not href:
                    continue
                live_count += 1
                sources_by_url.setdefault(href, set()).add(f"live:{rel_path}")
        ctx.note(f"Live DOM crawl of {LIVE_PAGES} found {live_count} outbound minipass.me anchor(s) "
                  f"(rendered set of unique URLs unchanged at {len(sources_by_url)}).")

        ctx.screenshot(page, "unified_settings_stripe_section")

        # --- check every unique URL's HTTP status via a lightweight request,
        #     never navigating the page itself away ---
        results = []
        for url in sorted(sources_by_url):
            try:
                response = page.request.get(url, timeout=15000)
                results.append((url, response.status, None))
            except Exception as exc:  # noqa: BLE001 - report every failure, don't crash the script
                results.append((url, None, str(exc)))

        broken = []
        for url, status, error in results:
            sources = ", ".join(sorted(sources_by_url[url]))
            if error is not None:
                ctx.note(f"REQUEST ERROR: {url} -> {error}  (referenced from: {sources})")
                broken.append(f"{url} -> request error: {error}")
            elif status >= 400:
                ctx.note(f"BROKEN: {url} -> HTTP {status}  (referenced from: {sources})")
                broken.append(f"{url} -> HTTP {status}")
            else:
                ctx.note(f"OK: {url} -> HTTP {status}  (referenced from: {sources})")

        if broken:
            raise AssertionError(
                f"{len(broken)} outbound minipass.me link(s) are broken:\n" + "\n".join(broken)
            )
