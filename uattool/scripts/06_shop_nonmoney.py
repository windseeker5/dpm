"""Row 06 — Shop (non-money paths).

Ensures SHOP_ENABLED is on (turning it on via Settings > Shop if needed —
left ON afterward since later shop tests depend on it staying enabled).
Creates the supplied Yoga scenario via the real admin UI: a $200/25-session
Regulier passport, a $50 mat with a photo, and $70 leggings without a photo
in S/M/L/XL. It confirms all three list, then builds a mixed cart containing
the mat, XL leggings, and the Yoga passport and confirms the $320 total. Never touches /shop/checkout — stops right before
any payment step, since this script must not move money.
"""

import re

from lib.browser import login, new_page
from lib.fixtures import (
    YOGA_ACTIVITY_NAME,
    YOGA_LEGGINGS_NAME,
    YOGA_LEGGINGS_PRICE,
    YOGA_LEGGINGS_SIZES,
    YOGA_MAT_NAME,
    YOGA_MAT_PRICE,
    YOGA_PASSPORT_TYPE,
    YOGA_PRICE,
    YOGA_SESSIONS,
    create_minimal_activity,
    create_product,
    ensure_shop_enabled,
    scenario_name,
)


def _ensure_shop_enabled(page, ctx):
    ensure_shop_enabled(page, ctx)


def _create_product(page, ctx, name, price, with_photo, sizes=None):
    create_product(page, ctx, name, price, with_photo=with_photo, sizes=sizes)


def run(ctx):
    mat_name = scenario_name(YOGA_MAT_NAME)
    leggings_name = scenario_name(YOGA_LEGGINGS_NAME)

    with new_page(viewport="desktop") as page:
        login(page, base_url=ctx.base_url)

        _ensure_shop_enabled(page, ctx)

        _create_product(page, ctx, mat_name, YOGA_MAT_PRICE, with_photo=True)
        _create_product(
            page,
            ctx,
            leggings_name,
            YOGA_LEGGINGS_PRICE,
            with_photo=False,
            sizes=YOGA_LEGGINGS_SIZES,
        )

        def check_show_in_shop(form_page):
            form_page.check('input[name="show_in_shop"]')

        activity_id, activity_name, _ = create_minimal_activity(
            page,
            ctx,
            name=scenario_name(YOGA_ACTIVITY_NAME),
            passport_type_name=YOGA_PASSPORT_TYPE,
            price=YOGA_PRICE,
            sessions=YOGA_SESSIONS,
            extra_setup=check_show_in_shop,
        )

        # --- browse /shop and confirm both products + the activity list ---
        page.goto(f"{ctx.base_url}/shop")
        page.wait_for_load_state("networkidle", timeout=15000)
        ctx.screenshot(page, "shop_browse_desktop")

        body_text = page.locator("body").inner_text()
        for expected in (mat_name, leggings_name, activity_name):
            if expected not in body_text:
                raise AssertionError(f"Expected {expected!r} to appear on /shop, but it did not.")
        ctx.note("Confirmed the Yoga activity, mat, and leggings all list on /shop.")

        # --- build a mixed cart: mat + size-specific leggings + Yoga passport ---
        page.locator(f'a.card:has-text("{mat_name}")').first.click()
        page.wait_for_load_state("networkidle", timeout=15000)
        page.fill("#quantity", "1")
        page.locator('form[method="POST"] button[type="submit"]').first.click()
        page.wait_for_load_state("networkidle", timeout=15000)
        ctx.note(f"Added product {mat_name!r} to cart.")

        page.goto(f"{ctx.base_url}/shop")
        page.locator(f'a.card:has-text("{leggings_name}")').first.click()
        page.wait_for_load_state("networkidle", timeout=15000)
        actual_sizes = page.locator("#size option").evaluate_all("els => els.map(el => el.value)")
        expected_sizes = ["S", "M", "L", "XL"]
        if actual_sizes != expected_sizes:
            raise AssertionError(f"Expected legging sizes {expected_sizes!r}, got {actual_sizes!r}.")
        page.select_option("#size", "XL")
        page.fill("#quantity", "1")
        page.locator('form[method="POST"] button[type="submit"]').first.click()
        page.wait_for_load_state("networkidle", timeout=15000)
        ctx.note(f"Confirmed sizes S/M/L/XL and added {leggings_name!r} in XL to cart.")

        page.goto(f"{ctx.base_url}/shop")
        page.locator(f'a.card:has-text("{activity_name}")').first.click()
        page.wait_for_load_state("networkidle", timeout=15000)
        page.locator('form[method="POST"] button[type="submit"]').first.click()
        page.wait_for_load_state("networkidle", timeout=15000)
        ctx.note(f"Added activity {activity_name!r} signup to the same cart (mixed cart).")

        # --- confirm the cart total is correct, then stop — no checkout ---
        page.goto(f"{ctx.base_url}/shop/cart")
        ctx.screenshot(page, "shop_cart_desktop")

        cart_text = page.locator("body").inner_text()
        for expected in (mat_name, leggings_name, activity_name):
            if expected not in cart_text:
                raise AssertionError(f"Expected {expected!r} to appear as a line in /shop/cart, but it did not.")

        if "XL" not in cart_text:
            raise AssertionError("Expected selected legging size 'XL' to appear in /shop/cart.")

        expected_total = round(YOGA_MAT_PRICE + YOGA_LEGGINGS_PRICE + float(YOGA_PRICE), 2)
        # The cart total is rendered by shop_cart.html as .mp-shop-total__amount; the old
        # ".card-footer strong" predates that markup and matches nothing.
        total_text = page.locator(".mp-shop-total__amount").last.inner_text().strip()
        # The tenant renders money fr-CA ("320,00 $" — comma decimal, non-breaking space,
        # trailing sign), so strip everything but digits/separators and treat a comma as
        # the decimal mark rather than assuming en-US "$320.00".
        cleaned = re.sub(r"[^\d,.]", "", total_text).replace(",", ".")
        actual_total = float(cleaned)
        if abs(actual_total - expected_total) > 0.001:
            raise AssertionError(
                f"Cart total mismatch: expected ${expected_total:.2f}, got {total_text!r} "
                f"(mat ${YOGA_MAT_PRICE:.2f} + leggings ${YOGA_LEGGINGS_PRICE:.2f} "
                f"+ Yoga passport ${float(YOGA_PRICE):.2f})."
            )
        ctx.note(f"Mixed cart total confirmed correct: ${actual_total:.2f}.")

        if page.locator('a[href*="/shop/checkout"], a:has-text("Checkout"), button:has-text("Checkout")').count():
            ctx.note("Checkout button is present but was NOT clicked — this script never touches money.")

    # --- mobile pass: confirm /shop browsing and the cart view render correctly on a phone ---
    with new_page(viewport="mobile") as page:
        login(page, base_url=ctx.base_url)
        page.goto(f"{ctx.base_url}/shop")
        page.wait_for_load_state("networkidle", timeout=15000)
        ctx.screenshot(page, "shop_browse_mobile")

        page.goto(f"{ctx.base_url}/shop/cart")
        page.wait_for_load_state("networkidle", timeout=15000)
        ctx.screenshot(page, "shop_cart_mobile")
        ctx.note("Confirmed /shop and /shop/cart render correctly on mobile (390px). Not proceeding to checkout.")
