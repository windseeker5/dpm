"""Financial view + export: every passport income row says its passport type, and Ticket or Donation.

Asked by FBI (Catherine, 2026-11) to see ticket money and donation money separately. The label
lives in the monthly_transactions_detail view (task63 of the upgrade script), the only source of
truth for money; the CSV/ZIP export just reads it. A passport TYPE with 0 sessions is a donation.

Checked here:
  - a ticket and a donation paid by Interac / cash are labelled Ticket / Donation
  - a ticket scanned down to 0 uses at the door stays a Ticket (the type is read, not uses_remaining)
  - a ticket paid by Stripe is labelled on its Stripe income row; its Stripe fee row is not
  - a manual income row (no passport) gets no label
  - task63 adds no row and changes no amount, and runs twice without harm
  - the ZIP export carries the same two columns as the CSV

The views are built by the upgrade script's own tasks (task55, task56, task63) on a throwaway
database, so the test exercises exactly what customers get. Nothing is sent: config.Config is
pointed at a temp file BEFORE app.py is imported.

Run:  python -m unittest test.test_financial_export_ticket_donation -v
"""
import atexit
import contextlib
import csv
import io
import os
import shutil
import sqlite3
import sys
import tempfile
import unittest
import zipfile
from datetime import datetime

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, APP_DIR)
sys.path.insert(0, os.path.join(APP_DIR, "migrations"))

import config                                                     # noqa: E402

_tmp_dir = tempfile.mkdtemp(prefix="minipass_test_")
atexit.register(shutil.rmtree, _tmp_dir, ignore_errors=True)
_tmp_db = os.path.join(_tmp_dir, "test.db")
config.Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{_tmp_db}"

from app import app, db                                           # noqa: E402
from models import (Activity, Admin, Expense, Income, Passport,   # noqa: E402
                    PassportType, StripeTransaction, User)
import upgrade_production_database as upgrade                     # noqa: E402

DAY = datetime(2026, 11, 7, 18, 0)


def _run_view_tasks(*tasks):
    conn = sqlite3.connect(_tmp_db)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            for task in tasks:
                task(conn.cursor())
        conn.commit()
    finally:
        conn.close()


def setUpModule():
    app.config["TESTING"] = True
    with app.app_context():
        if os.path.realpath(db.engine.url.database) != os.path.realpath(_tmp_db):
            raise RuntimeError(f"Refusing to run against {db.engine.url.database}")
        db.create_all()

        db.session.add(Admin(email="kdresdell@gmail.com", password_hash=b"x"))
        activity = Activity(name="Souper FBI", status="active")
        user = User(name="Ken Test", email="kdresdell@gmail.com")
        db.session.add_all([activity, user])
        db.session.flush()

        ticket = PassportType(activity_id=activity.id, name="Billet souper", type="permanent",
                              price_per_user=60.0, sessions_included=1, status="active")
        donation = PassportType(activity_id=activity.id, name="Don", type="permanent",
                                price_per_user=25.0, sessions_included=0, status="active")
        db.session.add_all([ticket, donation])
        db.session.flush()

        def passport(code, ptype, amount, uses, method="interac", marked_by="admin"):
            p = Passport(pass_code=code, user_id=user.id, activity_id=activity.id, sold_amt=amount,
                         uses_remaining=uses, paid=True, paid_date=DAY, created_dt=DAY,
                         marked_paid_by=marked_by, passport_type_id=ptype.id,
                         passport_type_name=ptype.name, payment_method=method)
            db.session.add(p)
            return p

        passport("TICKET01", ticket, 60.0, 1)
        passport("SCANNED1", ticket, 60.0, 0, method="cash")      # used at the door
        passport("DON00001", donation, 25.0, 0)
        stripe_pass = passport("STRIPE01", ticket, 60.0, 1, method="stripe",
                               marked_by="stripe-webhook")
        db.session.flush()

        # Stripe: the view hides the passport row; the income row and its fee stand for it.
        stripe_income = Income(activity_id=activity.id, date=DAY, category="Passport Sales",
                               amount=60.0, payment_status="received", created_by="stripe")
        db.session.add(stripe_income)
        db.session.flush()
        st = StripeTransaction(gross_amount=60.0, stripe_fee=2.04, net_amount=57.96,
                               charge_date=DAY, passport_id=stripe_pass.id,
                               income_id=stripe_income.id)
        db.session.add(st)
        db.session.flush()
        db.session.add(Expense(activity_id=activity.id, date=DAY, category="Stripe Fees",
                               amount=2.04, payment_status="paid", stripe_transaction_id=st.id))
        # A manual income row with no passport behind it (e.g. a sponsor cheque).
        db.session.add(Income(activity_id=activity.id, date=DAY, category="Sponsorship",
                              amount=500.0, payment_status="received", note="Commanditaire"))
        db.session.commit()

    # Views as the upgrade script leaves them before this change, then task63 on top.
    _run_view_tasks(upgrade.task55_financial_views_with_products,
                    upgrade.task56_transactions_detail_add_keys)
    global BEFORE
    BEFORE = _detail_rows()
    _run_view_tasks(upgrade.task63_transactions_detail_ticket_or_donation)


def _detail_rows():
    conn = sqlite3.connect(_tmp_db)
    conn.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM monthly_transactions_detail ORDER BY source_type, record_id")]
    finally:
        conn.close()


def _export(fmt):
    c = app.test_client()
    with c.session_transaction() as s:
        s["admin"] = "kdresdell@gmail.com"
    resp = c.get(f"/reports/financial/export?format={fmt}&period=all")
    assert resp.status_code == 200, resp.status_code
    if fmt == "zip":
        with zipfile.ZipFile(io.BytesIO(resp.get_data())) as z:
            body = z.read("financial_report.csv").decode("utf-8-sig")
    else:
        body = resp.get_data(as_text=True)
    return list(csv.DictReader(io.StringIO(body)))


class TicketOrDonationViewTest(unittest.TestCase):

    def _by_memo_or_code(self, rows):
        return {(r["source_type"], r["passport_number"] or r["memo"]): r for r in rows}

    def test_view_labels(self):
        rows = self._by_memo_or_code(_detail_rows())
        self.assertEqual(rows[("passport", "TICKET01")]["ticket_or_donation"], "Ticket")
        self.assertEqual(rows[("passport", "TICKET01")]["passport_type"], "Billet souper")
        self.assertEqual(rows[("passport", "DON00001")]["ticket_or_donation"], "Donation")
        self.assertEqual(rows[("passport", "DON00001")]["passport_type"], "Don")
        self.assertEqual(rows[("passport", "SCANNED1")]["ticket_or_donation"], "Ticket")
        self.assertEqual(rows[("income", "STRIPE01")]["ticket_or_donation"], "Ticket")
        self.assertIsNone(rows[("expense", "STRIPE01")]["ticket_or_donation"])
        self.assertIsNone(rows[("income", "Commanditaire")]["ticket_or_donation"])

    def test_task63_changes_no_row_and_no_amount(self):
        after = _detail_rows()
        strip = lambda rows: [{k: v for k, v in r.items()
                               if k not in ("passport_type", "ticket_or_donation")} for r in rows]
        self.assertEqual(strip(after), BEFORE)

    def test_task63_is_rerunnable(self):
        _run_view_tasks(upgrade.task63_transactions_detail_ticket_or_donation)
        self.assertEqual(len(_detail_rows()), len(BEFORE))

    def test_csv_export_split(self):
        rows = _export("csv")
        tickets = sum(float(r["amount"]) for r in rows if r["ticket_or_donation"] == "Ticket")
        dons = sum(float(r["amount"]) for r in rows if r["ticket_or_donation"] == "Donation")
        self.assertEqual(tickets, 180.0)   # TICKET01 + SCANNED1 + STRIPE01
        self.assertEqual(dons, 25.0)
        fee = [r for r in rows if r["transaction_type"] == "Expense"]
        self.assertEqual([r["ticket_or_donation"] for r in fee], [""])

    def test_zip_export_has_same_columns(self):
        csv_rows = _export("csv")
        zip_rows = _export("zip")
        key = lambda r: (r["passport_number"], r["amount"], r["ticket_or_donation"],
                         r["passport_type"])
        self.assertEqual(sorted(map(key, zip_rows)), sorted(map(key, csv_rows)))


if __name__ == "__main__":
    unittest.main()
