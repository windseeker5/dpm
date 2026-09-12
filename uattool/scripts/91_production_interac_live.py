"""Row 91 — [REAL MONEY] Interac payment.

Only runs with `--confirm-money`. Creates a small real signup on
kdc.minipass.me, then PAUSES for Ken to send himself a real Interac
e-transfer for that exact amount to whatever inbox kdc.minipass.me monitors.
Once he confirms it's sent, triggers the same matcher that lives behind
`/test-payment-bot-now` and verifies the payment gets matched.

Deliberately runs LAST in the catalog, and only against kdc.minipass.me — see
CATALOG.md and the plan this tool was built from.
"""

import time

from lib import config
from lib.activity_log import assert_log_contains
from lib.browser import login, new_page
from lib.fixtures import create_minimal_activity, fill_public_signup_form

INTERAC_AMOUNT = "2.00"


def _pause_for_human(message):
    print("\n" + "=" * 78)
    print(message)
    input("This script is paused. Press Enter here once you've completed that step... ")
    print("=" * 78 + "\n")


def run(ctx):
    if not ctx.money_confirmed:
        raise AssertionError(
            "Refusing to run: this is a real-money script and requires --confirm-money."
        )

    with new_page(viewport="desktop") as page:
        login(page, base_url=ctx.base_url)

        activity_id, activity_name, _ = create_minimal_activity(
            page, ctx,
            name=f"UAT REAL Interac {int(time.time())}",
            workflow_type="payment_first", price=INTERAC_AMOUNT, sessions="1",
        )
        ctx.note(f"Created real ${INTERAC_AMOUNT} activity id={activity_id} ({activity_name!r}).")

        signup_page_url_before = page.url
        fill_public_signup_form(page, ctx, activity_id, payment_method="interac")
        page.locator('form button[type="submit"]').first.click()
        page.wait_for_url(f"{ctx.base_url}/signup/thank-you/*", timeout=15000)
        ctx.screenshot(page, "signup_thank_you")
        ctx.note(f"Submitted real Interac signup, landed on {page.url}")

        _pause_for_human(
            f"ACTION NEEDED — send yourself a REAL Interac e-transfer for exactly "
            f"${INTERAC_AMOUNT} CAD, payer name {config.TEST_NAME!r}, to whichever email "
            f"inbox kdc.minipass.me is configured to monitor for incoming e-transfer "
            f"notifications. Wait for the bank notification email to actually arrive before "
            f"continuing — the matcher below reads that notification, not the transfer itself."
        )

        login(page, base_url=ctx.base_url)  # re-affirm session in case of timeout during the pause
        page.goto(f"{ctx.base_url}/test-payment-bot-now")
        page.wait_for_load_state("networkidle", timeout=30000)
        ctx.screenshot(page, "payment_bot_run_result")
        ctx.note(f"Triggered the real Interac matcher, result page: {page.inner_text('body')[:300]!r}")

        page.goto(f"{ctx.base_url}/payment-bot-matches")
        page.wait_for_load_state("networkidle", timeout=15000)
        ctx.screenshot(page, "payment_bot_matches")

        body_text = page.locator("body").inner_text().lower()
        if config.TEST_NAME.lower() not in body_text and INTERAC_AMOUNT not in body_text:
            raise AssertionError(
                f"Could not find a payment-bot-matches entry for {config.TEST_NAME!r} / "
                f"${INTERAC_AMOUNT} — the real e-transfer may not have arrived yet, or the "
                f"matcher didn't match it. Check /payment-bot-matches by hand."
            )

        assert_log_contains(page, "interac", base_url=ctx.base_url)
        ctx.note("Confirmed an Interac-related entry landed in the Activity Log.")
