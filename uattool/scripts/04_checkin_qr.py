"""Row 04 — Check-in / QR.

Redeems a passport through the real admin "Check In" UI. Headless Playwright can't drive
templates/scan_qr.html's actual flow (getUserMedia camera + client-side jsQR decode of a
physical QR code), so this uses the real fallback for entering/confirming a pass by hand as
an admin: the pass_code-driven "Check In" action on /pass/<pass_code>
(templates/pass.html #redeem-confirm-modal), which POSTs to the legacy
/redeem/<pass_code> route (app.py ~line 12201, redeem_passport()) — the same underlying
credit-deduction + Redemption + AdminActionLog logic as the QR-scan route
(/redeem-qr/<pass_code>, redeem_passport_qr() ~line 7805), just reached by a typed/known
pass_code instead of a camera decode. Runs the full flow twice, independently (fresh
activity + passport each time, no shared state): once on a mobile-viewport pass (primary —
this is a phone-at-the-door flow) and once on desktop.
"""

import re

from lib import config
from lib.activity_log import assert_log_contains
from lib.browser import login, new_page
from lib.fixtures import (
    LHGI_ACTIVITY_NAME,
    LHGI_PASSPORT_TYPE,
    LHGI_PRICE,
    LHGI_SESSIONS,
    create_admin_passport,
    create_minimal_activity,
    scenario_name,
)


def _read_uses_remaining(page):
    # Crédits row is "{{ uses_remaining }} sur {{ total }}" or "{{ uses_remaining }} crédit(s)"
    # — the first number is always uses_remaining either way.
    text = page.locator(".pass-row-value-group .pass-row-value").first.inner_text()
    match = re.search(r"\d+", text)
    if not match:
        raise AssertionError(f"Could not parse uses_remaining from pass page text: {text!r}")
    return int(match.group())


def _checkin_one(ctx, viewport):
    with new_page(viewport=viewport) as page:
        login(page, base_url=ctx.base_url)

        activity_id, activity_name, _ = create_minimal_activity(
            page,
            ctx,
            name=scenario_name(LHGI_ACTIVITY_NAME, f"Check-in {viewport}"),
            passport_type_name=LHGI_PASSPORT_TYPE,
            price=LHGI_PRICE,
            sessions=LHGI_SESSIONS,
        )
        pass_code = create_admin_passport(
            page, ctx, activity_id, uses_remaining=int(LHGI_SESSIONS)
        )

        page.goto(f"{ctx.base_url}/pass/{pass_code}")
        page.wait_for_load_state("networkidle", timeout=15000)
        ctx.screenshot(page, f"pass_before_checkin_{viewport}")

        credits_before = _read_uses_remaining(page)
        ctx.note(f"[{viewport}] Passport {pass_code} uses_remaining before check-in: {credits_before}")

        # Open the 3-dot admin menu, then the "Check In" action -> #redeem-confirm-modal.
        page.locator('button[aria-label="Actions"]').first.click()
        page.wait_for_timeout(200)
        page.locator('button[data-bs-target="#redeem-confirm-modal"]').first.click()
        page.wait_for_selector("#redeem-confirm-modal.show", timeout=5000)
        ctx.screenshot(page, f"checkin_confirm_modal_{viewport}")

        page.locator("#redeem-form button[type=submit]").click()
        page.wait_for_load_state("networkidle", timeout=15000)

        # redeem_passport() logs: "Passport for {name} ({pass_code}) was redeemed by {admin}"
        assert_log_contains(page, "redeemed", base_url=ctx.base_url)
        assert_log_contains(page, pass_code, base_url=ctx.base_url)

        page.goto(f"{ctx.base_url}/pass/{pass_code}")
        page.wait_for_load_state("networkidle", timeout=15000)
        ctx.screenshot(page, f"pass_after_checkin_{viewport}")

        credits_after = _read_uses_remaining(page)
        ctx.note(f"[{viewport}] Passport {pass_code} uses_remaining after check-in: {credits_after}")

        if credits_after != credits_before - 1:
            raise AssertionError(
                f"[{viewport}] Expected uses_remaining to drop by exactly 1 after check-in "
                f"({credits_before} -> {credits_before - 1}), got {credits_after}."
            )

        ctx.note(
            f"[{viewport}] Check-in on activity {activity_name!r} confirmed: Activity Log "
            f"shows the redemption for {pass_code}, credits {credits_before} -> {credits_after}."
        )


def run(ctx):
    # Mobile first — this is primarily a phone-at-the-door flow.
    _checkin_one(ctx, "mobile")
    _checkin_one(ctx, "desktop")
