"""Row 90 — [REAL MONEY] Stripe payment.

Only runs with `--confirm-money`. Opens a HEADED (visible) browser — this
script never holds or types a real card number itself. It drives the flow up
to the real Stripe Checkout page for a $1 activity signup and a $1 shop
product, then PAUSES and waits for a human (Ken) to type his own card and
submit. Resumes automatically once Stripe redirects back to the app, and
verifies the resulting records.

Deliberately runs LAST in the catalog, and only against kdc.minipass.me — see
CATALOG.md and the plan this tool was built from.
"""

import time

from playwright.sync_api import sync_playwright

from lib import config
from lib.activity_log import assert_log_contains
from lib.browser import login
from lib.fixtures import create_minimal_activity, fill_public_signup_form

STRIPE_CHECKOUT_HOST = "checkout.stripe.com"


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

        # ---------------------------------------------------------------
        # Part B — $1 shop product, real Stripe Checkout
        # ---------------------------------------------------------------
        admin_page.goto(f"{ctx.base_url}/admin/products")
        admin_page.get_by_role("button", name="Add Product").click()
        admin_page.wait_for_selector("#productModal.show", timeout=5000)
        product_name = f"UAT REAL $1 Product {int(time.time())}"
        admin_page.fill("#name", product_name)
        admin_page.fill("#price", "1.00")
        admin_page.check("#active")
        admin_page.locator('#productModal button[type="submit"]').click()
        admin_page.wait_for_load_state("networkidle", timeout=15000)
        ctx.note(f"Created real $1 shop product {product_name!r}.")

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
        ctx.note(f"Shop order completed, landed on {shop_page.url}")

        context.close()
        browser.close()
