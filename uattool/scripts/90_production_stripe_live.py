"""Row 90 — [REAL MONEY] Stripe payment.

Only runs with `--confirm-money`. Opens a HEADED (visible) browser — this
script never holds or types a real card number itself. It drives the flow up
to the real Stripe Checkout page for a $1 activity signup and a $1 shop
product, then PAUSES and waits for a human (Ken) to type his own card and
submit. Resumes automatically once Stripe redirects back to the app, and
verifies the resulting records.

It then verifies the money actually reached the financial report, which is the
whole point of the exercise — a payment that produces records but never shows
up in the books is still a bug.

The two halves land in DIFFERENT buckets, and this is deliberate, not a bug:

  Part A, $1 activity  -> ACCOUNTS RECEIVABLE +1.00, cash unchanged.
      The Stripe webhook writes an Income row with payment_status='pending'
      (app.py:4023) because the money sits in Stripe's clearing account until
      payout, and the passport itself is excluded from the views by
      `marked_paid_by NOT LIKE 'stripe%'` so it is not double-counted.

  Part B, $1 product   -> CASH RECEIVED +1.00.
      shop_order.status flips to 'paid' (app.py:3985) and the view counts
      paid/ready/picked_up orders as cash.

The expense side is read and reported but never asserted: the Stripe processing
fee may or may not be booked yet depending on payout timing, so failing on it
would make this row flaky for a reason that is not a defect.

Deliberately runs LAST in the catalog, and only against demo.minipass.me — see
CATALOG.md and the plan this tool was built from.
"""

import time

from playwright.sync_api import sync_playwright

from lib import config, financials
from lib.activity_log import assert_log_contains
from lib.browser import login, thank_you_value
from lib.fixtures import create_minimal_activity, create_product, fill_public_signup_form, scenario_name

STRIPE_CHECKOUT_HOST = "checkout.stripe.com"
ACTIVITY_AMOUNT = 1.00
PRODUCT_AMOUNT = 1.00


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

    with sync_playwright() as p:
        # headless=False on purpose — a human has to see this page and type a real card.
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport=config.VIEWPORTS["desktop"])
        admin_page = context.new_page()
        login(admin_page, base_url=ctx.base_url)

        # Baseline BEFORE anything is created. Every later check is a delta against this —
        # the live tenant's absolute figures are unknowable and change between runs.
        baseline = financials.read_tiles(admin_page, base_url=ctx.base_url)
        ctx.note(
            f"Financial baseline: cash ${baseline['cash_received']:,.2f}, "
            f"AR ${baseline['accounts_receivable']:,.2f}, "
            f"expenses paid ${baseline['cash_paid']:,.2f}, AP ${baseline['accounts_payable']:,.2f}."
        )
        financials.assert_views_agree(
            baseline, financials.read_csv_totals(admin_page, base_url=ctx.base_url), ctx, "baseline"
        )
        ctx.screenshot(admin_page, "financial_report_baseline")

        # ---------------------------------------------------------------
        # Part A — $1 activity, real Stripe Checkout
        # ---------------------------------------------------------------
        def enable_stripe(page):
            page.check('input[name="accept_credit_card"]')

        activity_id, activity_name, _ = create_minimal_activity(
            admin_page, ctx,
            name=f"UAT REAL $1 Activity {int(time.time())}",
            workflow_type="payment_first", price="1.00", sessions="1",
            extra_setup=enable_stripe,
        )
        ctx.note(f"Created real $1 activity id={activity_id} ({activity_name!r}) with Stripe accepted.")

        customer_page = context.new_page()
        fill_public_signup_form(customer_page, ctx, activity_id, payment_method="stripe")
        customer_page.locator('form button[type="submit"]').first.click()
        customer_page.wait_for_url(f"**{STRIPE_CHECKOUT_HOST}/**", timeout=20000)
        ctx.screenshot(customer_page, "stripe_checkout_activity")

        _pause_for_human(
            f"ACTION NEEDED — a real Stripe Checkout page is open for the $1 activity "
            f"{activity_name!r}. Enter your own real card and complete the $1.00 payment now."
        )

        customer_page.wait_for_url(f"{ctx.base_url}/signup/stripe-success*", timeout=120000)
        ctx.screenshot(customer_page, "stripe_success_activity")
        customer_page.close()
        ctx.note("Stripe redirected back to /signup/stripe-success for the activity payment.")

        assert_log_contains(admin_page, "Stripe", base_url=ctx.base_url)
        ctx.note("Confirmed a Stripe-related entry landed in the Activity Log for the activity payment.")

        # --- Financial check for Part A: AR up, cash untouched (see the module docstring) ---
        after_activity = financials.read_tiles(admin_page, base_url=ctx.base_url)
        financials.assert_views_agree(
            after_activity, financials.read_csv_totals(admin_page, base_url=ctx.base_url),
            ctx, "after Stripe activity payment",
        )
        fee_booked = round(after_activity["cash_paid"] - baseline["cash_paid"], 2)
        ctx.note(
            f"Expense side moved ${fee_booked:+,.2f} after the activity payment "
            f"(Stripe processing fee; reported, not asserted — it depends on payout timing)."
        )
        financials.assert_delta(
            baseline, after_activity,
            {"accounts_receivable": ACTIVITY_AMOUNT,
             "cash_paid": fee_booked,
             "net_cash_flow": -fee_booked},
            ctx, "Stripe $1 activity",
        )
        ctx.screenshot(admin_page, "financial_report_after_activity")

        # ---------------------------------------------------------------
        # Part B — $1 shop product, real Stripe Checkout
        # ---------------------------------------------------------------
        product_name = scenario_name("UAT REAL $1 Product")
        create_product(admin_page, ctx, product_name, f"{PRODUCT_AMOUNT:.2f}")
        before_product = financials.read_tiles(admin_page, base_url=ctx.base_url)

        shop_page = context.new_page()
        shop_page.goto(f"{ctx.base_url}/shop")
        shop_page.get_by_text(product_name).first.click()
        shop_page.wait_for_load_state("networkidle", timeout=10000)
        shop_page.get_by_role("button", name="Add to Cart").click()
        shop_page.wait_for_load_state("networkidle", timeout=10000)

        shop_page.goto(f"{ctx.base_url}/shop/checkout")
        shop_page.fill("#buyer_name", config.TEST_NAME)
        shop_page.fill("#buyer_email", config.TEST_EMAIL)
        stripe_radio = shop_page.locator('input[name="payment_method"][value="stripe"]')
        if not stripe_radio.count():
            raise AssertionError(
                "Stripe payment option not offered at /shop/checkout — is STRIPE_PAYMENTS_ENABLED "
                "on for this tenant? Aborting before placing a real order with the wrong method."
            )
        stripe_radio.first.check()
        ctx.screenshot(shop_page, "shop_checkout_before_place_order")

        shop_page.get_by_role("button", name="Place Order").click()
        shop_page.wait_for_url(f"**{STRIPE_CHECKOUT_HOST}/**", timeout=20000)
        ctx.screenshot(shop_page, "stripe_checkout_product")

        _pause_for_human(
            f"ACTION NEEDED — a real Stripe Checkout page is open for the $1 product "
            f"{product_name!r}. Enter your own real card and complete the $1.00 payment now."
        )

        shop_page.wait_for_url(f"{ctx.base_url}/shop/order/thank-you/*", timeout=120000)
        ctx.screenshot(shop_page, "shop_order_thank_you")
        # The cart code is the last URL segment (app.py:3725) and is what the Activity Log
        # entry names — "Stripe Payment Received: $X from ... for Cart MP-CART-0000001".
        cart_code = thank_you_value(shop_page.url)
        ctx.note(f"Shop order completed, landed on {shop_page.url} (cart {cart_code}).")
        shop_page.close()

        # --- Financial check for Part B: the product is cash, and it lands on Boutique ---
        after_product = financials.read_tiles(admin_page, base_url=ctx.base_url)
        financials.assert_views_agree(
            after_product, financials.read_csv_totals(admin_page, base_url=ctx.base_url),
            ctx, "after Stripe product payment",
        )
        product_fee = round(after_product["cash_paid"] - before_product["cash_paid"], 2)
        financials.assert_delta(
            before_product, after_product,
            {"cash_received": PRODUCT_AMOUNT,
             "cash_paid": product_fee,
             "net_cash_flow": round(PRODUCT_AMOUNT - product_fee, 2)},
            ctx, "Stripe $1 product",
        )

        financials.assert_report_line(admin_page, ctx, product_name, PRODUCT_AMOUNT, base_url=ctx.base_url)
        financials.assert_csv_line(admin_page, ctx, product_name, PRODUCT_AMOUNT, base_url=ctx.base_url)

        boutique_total = financials.activity_row_total(admin_page, "Boutique", base_url=ctx.base_url)
        if boutique_total is None:
            raise AssertionError(
                "No 'Boutique' row in the Transactions by Activity table after a paid product sale. "
                "Product revenue is reaching the KPI tiles but being dropped from the per-activity "
                "breakdown — check the no-activity bucket in utils.get_financial_data_from_views."
            )
        ctx.note(f"Boutique row present in Transactions by Activity at ${boutique_total:,.2f} cash received.")

        assert_log_contains(admin_page, cart_code, base_url=ctx.base_url)
        ctx.note(f"Activity Log contains the Stripe payment entry for cart {cart_code}.")

        ctx.screenshot(admin_page, "financial_report_after_product")

        context.close()
        browser.close()
