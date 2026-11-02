"""Which email goes out when an admin clicks Mark Paid & Create Passport.

Payment-first: "Paiement reçu" only, the same single email the Interac bot and Stripe send.
It already carries the QR code and the passport details, so "Votre passeport est prêt" on top
of it would only repeat them. An admin who customized "Paiement reçu" must see that text.
Approval-first: "Votre passeport est prêt" only, because no money has come in yet.

Runs on a throwaway database and never sends anything: config.Config is pointed at a temp file
BEFORE app.py is imported (afterwards it is too late, and the real instance/minipass.db is what
gets opened), and setUpModule refuses to run if that did not take.

Run:  python -m unittest test.test_pay_first_payment_email -v
"""
import atexit
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config                                                     # noqa: E402

_tmp_dir = tempfile.mkdtemp(prefix="minipass_test_")
atexit.register(shutil.rmtree, _tmp_dir, ignore_errors=True)
_tmp_db = os.path.join(_tmp_dir, "test.db")
config.Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{_tmp_db}"

from app import app, db                                           # noqa: E402
from models import Activity, Admin, Passport, PassportType, Signup, User  # noqa: E402

ADMIN_EMAIL = "kdresdell@gmail.com"


def setUpModule():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.app_context():
        if os.path.realpath(db.engine.url.database) != os.path.realpath(_tmp_db):
            raise RuntimeError(f"Refusing to run against {db.engine.url.database}")
        db.create_all()
        db.session.add(Admin(email=ADMIN_EMAIL, password_hash=b"x"))
        db.session.commit()


class MarkPaidEmailTest(unittest.TestCase):

    def _make_signup(self, workflow_type, email_templates=None):
        activity = Activity(name=f"Test {workflow_type}", workflow_type=workflow_type,
                            email_templates=email_templates, status="active")
        user = User(name="Ken Test", email=ADMIN_EMAIL)
        db.session.add_all([activity, user])
        db.session.flush()
        passport_type = PassportType(activity_id=activity.id, name="Billet", type="permanent", price_per_user=60.0,
                                     sessions_included=1, status="active")
        db.session.add(passport_type)
        db.session.flush()
        signup = Signup(user_id=user.id, activity_id=activity.id, passport_type_id=passport_type.id,
                        requested_sessions=1, requested_amount=60.0, status="pending")
        db.session.add(signup)
        db.session.commit()
        return signup.id

    def _mark_paid(self, signup_id):
        """Post the real route and return every email it tried to send (nothing is sent)."""
        client = app.test_client()
        with client.session_transaction() as sess:
            sess["admin"] = ADMIN_EMAIL
        with patch("utils.send_email_async") as send, patch("utils.send_push_notification_to_admins"):
            response = client.post(f"/signup/approve-create-pass/{signup_id}")
        self.assertEqual(response.status_code, 302)
        return [call.kwargs for call in send.call_args_list]

    def test_pay_first_sends_only_payment_received(self):
        with app.app_context():
            signup_id = self._make_signup("payment_first")
            emails = self._mark_paid(signup_id)
            self.assertEqual([e["template_name"] for e in emails], ["paymentReceived"])
            self.assertTrue(Passport.query.filter_by(user_id=db.session.get(Signup, signup_id).user_id).first().paid)

    def test_pay_first_default_email_has_the_qr_code(self):
        with app.app_context():
            email = self._mark_paid(self._make_signup("payment_first"))[0]
            self.assertTrue(email["context"]["show_qr_code"])
            self.assertIn("qr_code", email["inline_images"])

    def test_pay_first_uses_the_admins_custom_text(self):
        templates = {"paymentReceived": {"subject": "Merci {{ user_name }}",
                                         "admin_message": "<p>Consignes de JF</p>"}}
        with app.app_context():
            email = self._mark_paid(self._make_signup("payment_first", templates))[0]
            self.assertEqual(email["subject"], "Merci Ken Test")
            self.assertIn("Consignes de JF", email["context"]["admin_message"])

    def test_pay_first_respects_qr_turned_off(self):
        templates = {"paymentReceived": {"show_qr_code": False}}
        with app.app_context():
            email = self._mark_paid(self._make_signup("payment_first", templates))[0]
            self.assertFalse(email["context"]["show_qr_code"])
            self.assertNotIn("qr_code", email["inline_images"])

    def test_approval_first_still_sends_only_new_pass(self):
        with app.app_context():
            emails = self._mark_paid(self._make_signup("approval_first"))
            self.assertEqual([e["template_name"] for e in emails], ["newPass"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
