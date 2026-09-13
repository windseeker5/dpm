#!/usr/bin/env python3
"""Developer tool — simulate an Interac cart payment and assert the books move correctly.

Leading underscore so run_uat.py never picks this up as a catalog row. This is not a test in the
catalog; it is how the financial assertions in rows 90/91 were proven without spending real money.

WHAT IT SIMULATES
    Exactly the state transition the real Interac matcher performs when it matches a cart
    (utils.py:2825-2840):

        cart.status = "paid";  cart.paid_at = now
        every order in the cart -> status "paid", same paid_at
        every unpaid signup     -> auto_create_passport_from_signup(marked_paid_by="minipass-bot@system")

    auto_create_passport_from_signup() is the real function the matcher calls, so the rows this
    produces are identical to those from a genuine payment.

WHAT IT DOES NOT SIMULATE
    The matching itself — reading the bank notification email and fuzzy-matching payer name and
    amount to a cart. That logic is inline inside match_gmail_payments_to_passes(), reads a live
    IMAP inbox, and cannot be invoked in isolation. It stays unproven until row 91 runs for real
    on demo. This covers the money LANDING, not the FINDING of the cart.

USAGE
    cd uattool && source ../venv/bin/activate
    python scripts/_simulate_payment.py --list
    python scripts/_simulate_payment.py --cart MP-CART-0000003 --assert
    python scripts/_simulate_payment.py --stripe-shape --assert
"""

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UATTOOL = os.path.dirname(HERE)
APP_DIR = os.path.dirname(UATTOOL)
sys.path.insert(0, UATTOOL)
sys.path.insert(0, APP_DIR)

from lib import config, financials  # noqa: E402
from lib.browser import login, new_page  # noqa: E402


class Ctx:
    """Minimal stand-in for the UAT runner Context, so lib/financials.py works unchanged."""
    base_url = config.BASE_URL

    def note(self, msg):
        print(f"    {msg}")

    def screenshot(self, page, label):
        pass


def _app_context():
    """Import the Flask app and return an app context. Imported lazily: this pulls in the whole
    application module, which is only needed for the write half of this tool."""
    os.chdir(APP_DIR)
    from app import app
    return app


def list_carts():
    app = _app_context()
    from models import CartOrder

    with app.app_context():
        carts = CartOrder.query.order_by(CartOrder.id).all()
        if not carts:
            print("No carts in the database.")
            return
        print(f"{'cart_code':<20} {'total':>8}  {'status':<18} lines")
        for c in carts:
            lines = f"{len(c.orders)} product, {len(c.signups)} signup"
            print(f"{c.cart_code:<20} {c.total_amount:>8.2f}  {c.status:<18} {lines}")


def simulate_cart_payment(cart_code):
    """Apply the matcher's exact state transition. Returns (product_total, signup_total)."""
    from datetime import datetime, timezone

    app = _app_context()
    from models import CartOrder, db
    from utils import auto_create_passport_from_signup

    with app.app_context():
        cart = CartOrder.query.filter_by(cart_code=cart_code).first()
        if not cart:
            sys.exit(f"No cart named {cart_code!r}. Run with --list to see what exists.")
        if cart.status == "paid":
            sys.exit(f"Cart {cart_code} is already paid — nothing to simulate.")

        product_total = round(sum(o.amount or 0 for o in cart.orders), 2)
        signup_total = round(sum(s.requested_amount or 0 for s in cart.signups), 2)

        cart.status = "paid"
        cart.paid_at = datetime.now(timezone.utc)
        for order in cart.orders:
            order.status = "paid"
            order.paid_at = cart.paid_at

        created = 0
        for signup in cart.signups:
            if signup.paid:
                continue
            if auto_create_passport_from_signup(signup, marked_paid_by="minipass-bot@system"):
                created += 1

        db.session.commit()

        print(f"  Simulated payment of ${cart.total_amount:.2f} for {cart_code}: "
              f"{len(cart.orders)} order line(s) marked paid, {created} passport(s) created.")
        return product_total, signup_total


def create_stripe_shaped_income(activity_name_hint="Stripe shape"):
    """Write the Income row a Stripe passport payment produces (app.py:4023): pending, so it
    belongs in RECEIVABLES, not cash. Returns (income_id, amount, activity_name)."""
    from datetime import datetime, timezone

    app = _app_context()
    from models import Activity, Income, db

    with app.app_context():
        activity = Activity.query.filter_by(status="active").order_by(Activity.id).first()
        if not activity:
            sys.exit("No active activity to attach a simulated Stripe Income row to.")

        income = Income(
            activity_id=activity.id,
            amount=1.00,
            category="Passport Sales",
            date=datetime.now(timezone.utc),
            payment_status="pending",          # the Stripe clearing-account convention
            payment_method="credit_card",
            note=f"SIMULATED Stripe Checkout ({activity_name_hint})",
            created_by="stripe-webhook",
        )
        db.session.add(income)
        db.session.commit()
        print(f"  Created simulated Stripe Income row id={income.id} $1.00 pending "
              f"on activity {activity.name!r}.")
        return income.id, 1.00, activity.name


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true", help="list carts and exit")
    parser.add_argument("--cart", help="cart code to mark paid, e.g. MP-CART-0000003")
    parser.add_argument("--stripe-shape", action="store_true",
                        help="also prove a Stripe-style pending Income lands in receivables")
    parser.add_argument("--assert", dest="do_assert", action="store_true",
                        help="read the financial report before and after and check the deltas")
    args = parser.parse_args()

    if args.list:
        list_carts()
        return 0
    if not args.cart and not args.stripe_shape:
        parser.error("give --cart <code>, --stripe-shape, or --list")

    ctx = Ctx()
    failures = []

    with new_page(viewport="desktop", headless=True) as page:
        login(page, base_url=ctx.base_url)

        def read():
            tiles = financials.read_tiles(page, base_url=ctx.base_url)
            csv_totals = financials.read_csv_totals(page, base_url=ctx.base_url)
            financials.assert_views_agree(tiles, csv_totals, ctx, "reading")
            return tiles

        # ---------------- Interac cart ----------------
        if args.cart:
            print(f"\n=== Interac cart payment: {args.cart} ===")
            before = read()
            print(f"  before: cash ${before['cash_received']:,.2f}  "
                  f"AR ${before['accounts_receivable']:,.2f}")

            # Capture the split baselines while the page is still pre-payment.
            boutique_before = financials.activity_row_total(page, "Boutique", base_url=ctx.base_url) or 0.0

            product_total, signup_total = simulate_cart_payment(args.cart)

            after = read()
            print(f"  after:  cash ${after['cash_received']:,.2f}  "
                  f"AR ${after['accounts_receivable']:,.2f}")

            if args.do_assert:
                try:
                    financials.assert_delta(
                        before, after,
                        {"cash_received": product_total + signup_total,
                         "accounts_receivable": -product_total,
                         "net_cash_flow": product_total + signup_total},
                        ctx, "Interac cart payment",
                    )
                except AssertionError as e:
                    failures.append(str(e))
                    print(f"  FAIL {e}")

                boutique_after = financials.activity_row_total(page, "Boutique", base_url=ctx.base_url) or 0.0
                moved = round(boutique_after - boutique_before, 2)
                if abs(moved - product_total) > 0.01:
                    msg = (f"Boutique row moved ${moved:+,.2f}, expected ${product_total:+,.2f}. "
                           f"Product money is not landing on Boutique.")
                    failures.append(msg)
                    print(f"  FAIL {msg}")
                else:
                    print(f"    Boutique row moved ${moved:+,.2f} — the product's money, and only that.")

        # ---------------- Stripe shape ----------------
        if args.stripe_shape:
            print("\n=== Stripe-shaped payment (pending Income -> receivables, not cash) ===")
            before = read()
            income_id, amount, activity_name = create_stripe_shaped_income()
            after = read()
            print(f"  AR ${before['accounts_receivable']:,.2f} -> ${after['accounts_receivable']:,.2f}, "
                  f"cash ${before['cash_received']:,.2f} -> ${after['cash_received']:,.2f}")

            if args.do_assert:
                try:
                    financials.assert_delta(
                        before, after, {"accounts_receivable": amount}, ctx, "Stripe pending income",
                    )
                except AssertionError as e:
                    failures.append(str(e))
                    print(f"  FAIL {e}")
            print(f"  (clean up afterwards: DELETE FROM income WHERE id={income_id};)")

    print()
    if failures:
        print(f"{len(failures)} FAILURE(S)")
        return 1
    print("All financial assertions passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
