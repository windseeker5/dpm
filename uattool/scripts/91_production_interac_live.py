"""Row 91 — [REAL MONEY] Interac payment, mixed cart.

Only runs with `--confirm-money`.

Buys ONE cart containing both a $2.00 activity passport and a $1.00 shop product — $3.00 total,
settled with a single real Interac e-transfer. Then PAUSES for Ken to send that transfer, triggers
the same matcher that lives behind `/test-payment-bot-now`, and verifies the money landed in the
right place.

Why a mixed cart rather than two separate purchases: it costs one e-transfer instead of two, and
it tests the highest-value case in the whole shop feature — that a single payment SPLITS
correctly. Passport money must land on the activity, product money must land on 'Boutique', and
neither may contaminate the other. A view that attributed product revenue to an activity would
still show the right grand total, so only the split reveals it.

The assertions are deltas, never absolute totals: demo holds real money and its starting figures
change between runs.

An unpaid mixed cart does NOT put its whole value in receivables, and that surprised the author
enough to be worth writing down. Verified on a dry run:

  the $1.00 product   -> ACCOUNTS RECEIVABLE immediately (shop_order.status='awaiting_payment'
                         is a receivable in the view)
  the $2.00 passport  -> INVISIBLE until paid. An unpaid activity line in a cart is a `Signup`
                         row, and `signup` appears in NEITHER financial view — they read only
                         passport, income and expense. The $2.00 only enters the books when
                         payment creates the Passport.

So the unpaid cart shows AR +1.00, and payment produces cash +3.00 with AR -1.00. That is
correct: a signup is not a sale until a passport exists. Asserting AR +3.00 here would fail
against working code.

Deliberately runs LAST in the catalog, and only against demo.minipass.me — see CATALOG.md and the
plan this tool was built from.
"""

from playwright.sync_api import sync_playwright

from lib import config, financials
from lib.activity_log import assert_log_contains
from lib.browser import login
from lib.fixtures import (
    create_minimal_activity,
    create_product,
    ensure_shop_enabled,
    scenario_name,
)

ACTIVITY_AMOUNT = 2.00
PRODUCT_AMOUNT = 1.00
CART_TOTAL = ACTIVITY_AMOUNT + PRODUCT_AMOUNT  # 3.00


def _pause_for_human(message):
    print("\n" + "=" * 78)
    print(message)
    input("This script is paused. Press Enter here once you've completed that step... ")
    print("=" * 78 + "\n")


def _add_to_cart(page, ctx, base_url, item_name, quantity=None):
    """Open an item from /shop and add it to the session cart."""
    page.goto(f"{base_url}/shop")
    page.wait_for_load_state("networkidle", timeout=15000)

    card = page.locator(f'a.card:has-text("{item_name}")')
    if not card.count():
        raise AssertionError(
            f"{item_name!r} is not listed on /shop. Products need active=1; activities need "
            f"show_in_shop=1. Cannot build the mixed cart."
        )
    card.first.click()
    page.wait_for_load_state("networkidle", timeout=15000)

    if quantity is not None and page.locator("#quantity").count():
        page.fill("#quantity", str(quantity))

    page.locator('form button[type="submit"]:has-text("Add to Cart")').first.click()
    page.wait_for_load_state("networkidle", timeout=15000)
    ctx.note(f"Added {item_name!r} to the cart.")


def run(ctx):
    if not ctx.money_confirmed:
        raise AssertionError(
            "Refusing to run: this is a real-money script and requires --confirm-money."
        )

    product_name = scenario_name("UAT REAL $1 Product")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=150)

        admin_context = browser.new_context(viewport=config.VIEWPORTS["desktop"])
        admin_page = admin_context.new_page()
        login(admin_page, base_url=ctx.base_url)

        # --- 1: baseline, before anything exists ---
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

        # --- 2: the two things being bought ---
        ensure_shop_enabled(admin_page, ctx)
        create_product(admin_page, ctx, product_name, f"{PRODUCT_AMOUNT:.2f}")

        def show_in_shop(form_page):
            form_page.check('input[name="show_in_shop"]')

        activity_id, activity_name, _ = create_minimal_activity(
            admin_page, ctx,
            name=scenario_name("UAT REAL Interac Activity"),
            workflow_type="payment_first",
            price=f"{ACTIVITY_AMOUNT:.2f}", sessions="1",
            extra_setup=show_in_shop,
        )
        ctx.note(
            f"Created real ${ACTIVITY_AMOUNT:.2f} activity id={activity_id} ({activity_name!r}) "
            f"and ${PRODUCT_AMOUNT:.2f} product {product_name!r}."
        )

        # --- 3: build the mixed cart as a customer and check out with Interac ---
        # Separate context so the buyer is NOT carrying the admin session — the cart lives in the
        # Flask session, so it must not be shared with the admin page.
        shop_context = browser.new_context(viewport=config.VIEWPORTS["desktop"])
        shop_page = shop_context.new_page()

        _add_to_cart(shop_page, ctx, ctx.base_url, product_name, quantity=1)
        _add_to_cart(shop_page, ctx, ctx.base_url, activity_name)

        shop_page.goto(f"{ctx.base_url}/shop/cart")
        shop_page.wait_for_load_state("networkidle", timeout=15000)
        ctx.screenshot(shop_page, "shop_cart_mixed")

        total_text = shop_page.locator(".card-footer strong").last.inner_text().strip()
        cart_total = float(total_text.replace("$", "").replace(",", ""))
        if abs(cart_total - CART_TOTAL) > 0.005:
            raise AssertionError(
                f"Mixed cart total is {total_text!r}, expected ${CART_TOTAL:.2f} "
                f"(activity ${ACTIVITY_AMOUNT:.2f} + product ${PRODUCT_AMOUNT:.2f}). "
                f"Aborting before asking for a real transfer of the wrong amount."
            )
        ctx.note(f"Mixed cart total is ${cart_total:.2f} as expected.")

        shop_page.goto(f"{ctx.base_url}/shop/checkout")
        shop_page.wait_for_load_state("networkidle", timeout=15000)
        shop_page.fill("#buyer_name", config.TEST_NAME)
        shop_page.fill("#buyer_email", config.TEST_EMAIL)

        interac_radio = shop_page.locator('input[name="payment_method"][value="interac"]')
        if not interac_radio.count():
            raise AssertionError(
                "Interac is not offered at /shop/checkout. Aborting before placing an order with "
                "the wrong payment method."
            )
        interac_radio.first.check()
        ctx.screenshot(shop_page, "shop_checkout_interac")

        shop_page.get_by_role("button", name="Place Order").click()
        shop_page.wait_for_url(f"{ctx.base_url}/shop/order/thank-you/*", timeout=30000)
        # Cart code is the last URL segment (app.py:3746) and is what the matcher and the
        # Activity Log both reference.
        cart_code = shop_page.url.rstrip("/").split("/")[-1]
        ctx.screenshot(shop_page, "shop_order_awaiting_payment")
        ctx.note(f"Placed unpaid Interac order, cart {cart_code} for ${CART_TOTAL:.2f}.")
        shop_context.close()

        # --- 4: the product is an immediate receivable; the unpaid signup is not in the books ---
        after_order = financials.read_tiles(admin_page, base_url=ctx.base_url)
        financials.assert_views_agree(
            after_order, financials.read_csv_totals(admin_page, base_url=ctx.base_url),
            ctx, "after unpaid order",
        )
        financials.assert_delta(
            baseline, after_order,
            {"accounts_receivable": PRODUCT_AMOUNT},
            ctx, "unpaid mixed cart (product only — see module docstring)",
        )
        ctx.note(
            f"As expected, only the product's ${PRODUCT_AMOUNT:.2f} is receivable so far. The "
            f"${ACTIVITY_AMOUNT:.2f} signup is not in the books yet — `signup` is in neither "
            f"financial view; its money appears when payment creates the passport."
        )
        ctx.screenshot(admin_page, "financial_report_as_receivable")

        # --- 5: the human bit ---
        _pause_for_human(
            f"ACTION NEEDED — send yourself a REAL Interac e-transfer for exactly "
            f"${CART_TOTAL:.2f} CAD, payer name {config.TEST_NAME!r}, to whichever email inbox "
            f"{ctx.base_url} is configured to monitor for incoming e-transfer notifications. "
            f"This one transfer covers the whole cart ({cart_code}): the ${ACTIVITY_AMOUNT:.2f} "
            f"activity AND the ${PRODUCT_AMOUNT:.2f} product. Wait for the bank notification "
            f"email to actually arrive before continuing — the matcher reads that notification, "
            f"not the transfer itself."
        )

        # --- 6: run the matcher ---
        login(admin_page, base_url=ctx.base_url)  # re-affirm session in case the pause was long
        admin_page.goto(f"{ctx.base_url}/test-payment-bot-now")
        admin_page.wait_for_load_state("networkidle", timeout=60000)
        ctx.screenshot(admin_page, "payment_bot_run_result")
        ctx.note(f"Triggered the Interac matcher: {admin_page.inner_text('body')[:300]!r}")

        admin_page.goto(f"{ctx.base_url}/payment-bot-matches")
        admin_page.wait_for_load_state("networkidle", timeout=15000)
        ctx.screenshot(admin_page, "payment_bot_matches")

        matches_text = admin_page.locator("body").inner_text().lower()
        if config.TEST_NAME.lower() not in matches_text and f"{CART_TOTAL:.2f}" not in matches_text:
            raise AssertionError(
                f"No /payment-bot-matches entry for {config.TEST_NAME!r} / ${CART_TOTAL:.2f} — "
                f"the real e-transfer may not have arrived yet, or the matcher did not match it. "
                f"Check /payment-bot-matches by hand."
            )
        ctx.note(f"Matcher recorded the ${CART_TOTAL:.2f} transfer against cart {cart_code}.")

        # --- 7: THE KEY ASSERTION — the whole cart becomes cash ---
        # The product's receivable clears (-1.00) and both lines land as cash (+3.00): the order
        # flips to 'paid' and the signup becomes a paid Passport (utils.py:2825-2860).
        after_paid = financials.read_tiles(admin_page, base_url=ctx.base_url)
        financials.assert_views_agree(
            after_paid, financials.read_csv_totals(admin_page, base_url=ctx.base_url),
            ctx, "after Interac payment",
        )
        financials.assert_delta(
            after_order, after_paid,
            {"accounts_receivable": -PRODUCT_AMOUNT,
             "cash_received": CART_TOTAL,
             "net_cash_flow": CART_TOTAL},
            ctx, "Interac payment received",
        )
        # Against the original baseline: the full $3.00 is cash and receivables are back where
        # they started. If cash moved by more than CART_TOTAL, something was double-counted.
        financials.assert_delta(
            baseline, after_paid,
            {"cash_received": CART_TOTAL, "net_cash_flow": CART_TOTAL},
            ctx, "whole Interac chain vs baseline",
        )
        ctx.screenshot(admin_page, "financial_report_as_cash")

        # --- 8: the split — this is what proves products don't pollute activity revenue ---
        boutique_total = financials.activity_row_total(admin_page, "Boutique", base_url=ctx.base_url)
        if boutique_total is None:
            raise AssertionError(
                "No 'Boutique' row in Transactions by Activity after a paid product sale. Product "
                "revenue is reaching the KPI tiles but being dropped from the per-activity "
                "breakdown — check the no-activity bucket in utils.get_financial_data_from_views."
            )

        activity_total = financials.activity_row_total(admin_page, activity_name, base_url=ctx.base_url)
        if activity_total is None:
            raise AssertionError(
                f"No row for {activity_name!r} in Transactions by Activity, but its ${ACTIVITY_AMOUNT:.2f} "
                f"passport was paid in this cart."
            )
        if abs(activity_total - ACTIVITY_AMOUNT) > 0.005:
            raise AssertionError(
                f"Activity {activity_name!r} shows ${activity_total:,.2f} cash received, expected "
                f"exactly ${ACTIVITY_AMOUNT:.2f}. If it shows ${CART_TOTAL:.2f}, the product's "
                f"${PRODUCT_AMOUNT:.2f} is being wrongly attributed to the activity instead of Boutique."
            )
        ctx.note(
            f"Cart split correctly: activity {activity_name!r} got ${activity_total:,.2f}, "
            f"Boutique row totals ${boutique_total:,.2f} (includes this run's ${PRODUCT_AMOUNT:.2f})."
        )

        # --- 9: the product line is visible in the report and the export ---
        financials.assert_report_line(admin_page, ctx, product_name, PRODUCT_AMOUNT, base_url=ctx.base_url)
        financials.assert_csv_line(admin_page, ctx, product_name, PRODUCT_AMOUNT, base_url=ctx.base_url)

        # --- 10: Activity Log ---
        assert_log_contains(admin_page, cart_code, base_url=ctx.base_url)
        ctx.note(f"Activity Log contains the Interac match entry for cart {cart_code}.")

        admin_context.close()
        browser.close()
