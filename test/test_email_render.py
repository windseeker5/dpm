"""Rendering tests for the reworked email templates in templates/email/.

These guard the regression that shipped in the Phase 2 rework: notify_pass_event had two
branches, and the one taken by any activity WITH customizations rebuilt pass_data as a plain
dict with different key names. The pass_block macro reads pass_data.user.name, so that branch
raised UndefinedError inside the send worker thread and the email was silently never
delivered. Every activity created through the UI is seeded with customizations, so this was
close to universal — and it was invisible from the admin UI, because preview and test-send
both build a proper object.

The tests below render each template the way a real send does. They use the app's Jinja
environment but never send mail and never write to the database.

Run:  python -m unittest test.test_email_render -v
"""
import os
import sys
import unittest
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as app_module                                          # noqa: E402
from flask import render_template                                 # noqa: E402

PASS_TEMPLATES = ["newPass", "paymentReceived", "latePayment", "redeemPass"]
ALL_TEMPLATES = PASS_TEMPLATES + ["signup", "signup_payment_first", "survey_invitation"]


class _User:
    name = "Ken Dresdell"
    email = "kdresdell@gmail.com"
    phone_number = "5816240081"


class _PassportType:
    name = "Carte 8 séances"
    sessions_included = 8


class _Activity:
    id = 1
    name = "Wing Foil Course"
    uses_scheduling = True
    location_address_formatted = "Les Îles-de-la-Madeleine"


class _Passport:
    """The shape notify_pass_event actually passes: the Passport model, not a dict."""
    pass_code = "MP-0db36110e748"
    user = _User()
    activity = _Activity()
    passport_type = _PassportType()
    sold_amt = 500.0
    uses_remaining = 3
    paid = False
    created_dt = datetime(2026, 1, 9, 9, 14)


def _context(**overrides):
    ctx = {
        "pass_data": _Passport(),
        "title": "Votre passeport est prêt",
        "admin_message": "<p>Bonjour,</p><p>À bientôt.</p>",
        "activity_name": "Wing Foil Course",
        "organization_name": "KDC Corporation",
        "show_qr_code": True,
        "owner_logo_url": "https://example.invalid/logo.png",
        "hero_image_url": "https://example.invalid/hero.png",
        "pass_url": "https://example.invalid/pass/MP-0db36110e748",
        "uses_scheduling": True,
        "booked_slots": ["samedi 29 août, 08:30"],
        "history_rows": [
            {"label": "Création", "date": "2026-01-09 09:14", "by": "kdresdell"},
            {"label": "Paiement", "date": "2026-01-10 11:02", "by": "minipass-bot"},
            {"label": "Participation 1", "date": "2026-01-11 18:30", "by": "kdresdell"},
        ],
        "requested_amount": "50,00 $",
        "payment_email": "paiement@kdc.ca",
        "needs_signup_code": True,
        "signup_code": "MP-INS-0000001",
        "survey_url": "https://example.invalid/survey",
        "question_count": 8,
        "base_url": "https://example.invalid",
        "support_email": "support@minipass.me",
        "unsubscribe_url": "https://example.invalid/u",
        "privacy_url": "https://example.invalid/p",
    }
    ctx.update(overrides)
    return ctx


class EmailTemplateRenderTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = app_module.app
        cls.ctx = cls.app.test_request_context()
        cls.ctx.push()

    @classmethod
    def tearDownClass(cls):
        cls.ctx.pop()

    def test_every_template_renders(self):
        for name in ALL_TEMPLATES:
            with self.subTest(template=name):
                html = render_template(f"email/{name}.html", **_context())
                self.assertIn("<html", html.lower())

    def test_pass_templates_render_with_the_passport_model(self):
        """The regression: pass_block reads pass_data.user.name / .uses_remaining / .paid.

        Anything that hands it an object without those attributes raises UndefinedError and
        the email is lost, so this asserts the model shape renders and shows its data.
        """
        for name in PASS_TEMPLATES:
            with self.subTest(template=name):
                html = render_template(f"email/{name}.html", **_context())
                # The holder's name and their credit count both come off the model, so these
                # two cover the attribute access that used to raise.
                self.assertIn("Ken Dresdell", html)
                self.assertIn("3 sur 8", html)

    def test_history_table_is_present_and_names_the_operator(self):
        """History was dropped by the rework and explicitly wanted back.

        It has to carry who performed each step, not just the dates.
        """
        for name in PASS_TEMPLATES:
            with self.subTest(template=name):
                html = render_template(f"email/{name}.html", **_context())
                self.assertIn("Historique", html)
                self.assertIn("Participation 1", html)
                self.assertIn("kdresdell", html)

    def test_history_block_is_omitted_when_there_is_none(self):
        html = render_template("email/newPass.html", **_context(history_rows=[]))
        self.assertNotIn("Historique", html)

    def test_late_payment_shows_no_qr(self):
        """The pass isn't usable until it's paid, and an unreferenced CID part is exactly
        the attachment weight that triggered the Feb 2026 Gmail block."""
        html = render_template("email/latePayment.html", **_context())
        self.assertNotIn("cid:qr_code", html)

    def test_other_pass_templates_do_show_the_qr(self):
        for name in ["newPass", "paymentReceived", "redeemPass"]:
            with self.subTest(template=name):
                html = render_template(f"email/{name}.html", **_context())
                self.assertIn("cid:qr_code", html)

    def test_qr_is_hidden_when_the_owner_turns_it_off(self):
        html = render_template("email/newPass.html", **_context(show_qr_code=False))
        self.assertNotIn("cid:qr_code", html)

    def test_layout_does_not_depend_on_media_queries(self):
        """The Gmail app strips <style> for non-Gmail accounts, so a layout that needs a
        breakpoint to become readable is broken there. Nothing may reference the old
        collapsing-column hook."""
        for name in ALL_TEMPLATES:
            with self.subTest(template=name):
                html = render_template(f"email/{name}.html", **_context())
                self.assertNotIn("mp-stack", html)

    def test_declares_a_light_color_scheme(self):
        """Without this, dark-mode clients invert background and text independently."""
        html = render_template("email/newPass.html", **_context())
        self.assertIn('name="color-scheme"', html)

    def test_session_list_renders_when_slots_are_booked(self):
        html = render_template("email/newPass.html", **_context())
        self.assertIn("samedi 29 août, 08:30", html)

    def test_signup_payment_first_carries_the_transfer_details(self):
        html = render_template("email/signup_payment_first.html", **_context())
        self.assertIn("paiement@kdc.ca", html)
        self.assertIn("MP-INS-0000001", html)
        # People put the code in the Interac security-question field otherwise, and the
        # transfer then can't be matched to their signup.
        self.assertIn("Message au destinataire", html)

    def test_amounts_are_french_formatted(self):
        html = render_template("email/newPass.html", **_context())
        self.assertIn("500,00", html)
        self.assertNotIn("$500.00", html)


if __name__ == "__main__":
    unittest.main()
