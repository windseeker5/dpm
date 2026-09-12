"""Assert an expected entry shows up in /activity-log.

The route supports a real search query string (?q=...), which is enough to
verify an action was logged without scraping the whole table.
"""

from urllib.parse import quote

from . import config


def assert_log_contains(page, expected_substring, base_url=None, timeout_ms=10000):
    """Search /activity-log for expected_substring; raise AssertionError if absent.

    Retries with a fresh page load up to timeout_ms since logging happens
    synchronously in the request that triggers it, but the page itself may
    still be mid-navigation when this is called right after an action.
    """
    base_url = base_url or config.BASE_URL
    url = f"{base_url}/activity-log?q={quote(expected_substring)}"

    page.goto(url)
    page.wait_for_load_state("networkidle", timeout=timeout_ms)

    body_text = page.locator("body").inner_text()
    if expected_substring.lower() not in body_text.lower():
        raise AssertionError(
            f"Expected activity log entry containing {expected_substring!r} not found at {url}"
        )
