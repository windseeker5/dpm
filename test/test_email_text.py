"""Unit tests for utils_email_text — the shared renderer for customizable email text.

These are pure-function tests against a stub get_setting. They create no User/Passport/
Signup and never touch SMTP or instance/minipass.db.

Run:  python -m unittest test.test_email_text -v
"""
import json
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils_email_text import (                                    # noqa: E402
    EMAIL_TEXT_VARIABLES,
    build_email_text_context,
    render_email_text,
)

_SETTINGS = {
    "ORG_NAME": "KDC Corporation",
    "DISPLAY_PAYMENT_EMAIL": "paiement@kdc.ca",
    "MAIL_USERNAME": "bot@minipass.me",
}


class _SettingsPatchMixin:
    """Stub out Settings lookups so these stay pure-function tests with no app context.

    build_email_text_context does `from utils import get_setting` at call time, so patching
    the attribute on the module is enough — and unlike swapping sys.modules['utils'], it
    works whether or not another test has already imported the real utils.
    """

    def setUp(self):
        super().setUp()
        patcher = mock.patch(
            "utils.get_setting", side_effect=lambda k, d="": _SETTINGS.get(k, d)
        )
        patcher.start()
        self.addCleanup(patcher.stop)


class _User:
    name = "Ken Dresdell"
    email = "kdresdell@gmail.com"
    phone_number = "5816240081"


class _Activity:
    name = "Wing Foil Course"
    location_address_formatted = "Les Îles-de-la-Madeleine"


class _Pass:
    user = _User()
    activity = _Activity()
    sold_amt = 500.0
    uses_remaining = 3
    paid = False
    pass_code = "MP-0db36110e748"


class EmailTextContextTests(_SettingsPatchMixin, unittest.TestCase):

    def test_documented_variables_are_always_defined(self):
        """Every documented name must exist even with no arguments at all.

        A missing name is not a harmless blank: `{% if payment_email %}` silently turns the
        whole clause off, which is how a payment address can disappear from an email.
        """
        ctx = build_email_text_context()
        for name, _description in EMAIL_TEXT_VARIABLES:
            self.assertIn(name, ctx, f"{name} missing from context")

    def test_payment_email_and_org_resolve_from_settings(self):
        ctx = build_email_text_context(pass_data=_Pass())
        self.assertEqual(ctx["payment_email"], "paiement@kdc.ca")
        self.assertEqual(ctx["organization_name"], "KDC Corporation")

    def test_scalars_are_derived_from_the_passport(self):
        ctx = build_email_text_context(pass_data=_Pass())
        self.assertEqual(ctx["user_name"], "Ken Dresdell")
        self.assertEqual(ctx["activity_name"], "Wing Foil Course")
        self.assertEqual(ctx["amount"], 500.0)
        # French formatting, matching utils._fr_money and the money() macro, so one email
        # cannot show both "$500.00" and "500,00 $".
        self.assertEqual(ctx["amount_display"], "500,00 $")
        self.assertEqual(ctx["credits_remaining"], 3)
        self.assertFalse(ctx["is_paid"])

    def test_legacy_nested_spellings_still_resolve(self):
        """Existing per-activity customizations address pass_data.* / activity.*."""
        ctx = build_email_text_context(pass_data=_Pass())
        out = render_email_text(
            "{{ pass_data.user.name }}|{{ pass_data.uses_remaining }}|"
            "{{ pass_data.activity.name }}|{{ activity.location_address_formatted }}",
            ctx,
        )
        self.assertEqual(
            out, "Ken Dresdell|3|Wing Foil Course|Les Îles-de-la-Madeleine"
        )


class EmailTextRenderTests(_SettingsPatchMixin, unittest.TestCase):

    def test_shipped_defaults_render_without_leftover_jinja(self):
        """The real config/email_defaults.json must render clean for every template.

        Guards the regression where the preview emitted `Bonjour {{ pass_data.user.name }},`
        as body text.
        """
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config",
            "email_defaults.json",
        )
        with open(path, encoding="utf-8") as f:
            defaults = json.load(f)

        ctx = build_email_text_context(pass_data=_Pass())
        for template_name, fields in defaults.items():
            for field in ("subject", "title", "admin_message"):
                raw = fields.get(field)
                if not raw:
                    continue
                out = render_email_text(raw, ctx)
                self.assertNotIn("{{", out, f"{template_name}.{field} leaked a variable")
                self.assertNotIn("{%", out, f"{template_name}.{field} leaked a tag")

    def test_unpaid_conclusion_names_the_payment_address(self):
        ctx = build_email_text_context(pass_data=_Pass())
        out = render_email_text(
            "{% if not pass_data.paid %}Payer {{ '%.2f'|format(amount) }}$"
            "{% if payment_email %} à {{ payment_email }}{% endif %}{% endif %}",
            ctx,
        )
        self.assertEqual(out, "Payer 500.00$ à paiement@kdc.ca")

    def test_sandbox_blocks_traversal_into_internals(self):
        """Customized text is DB-editable, so it must not reach through an object.

        Rendered with a bare jinja2.Template this returns the class MRO.
        """
        ctx = build_email_text_context(pass_data=_Pass())
        out = render_email_text("{{ pass_data.__class__.__mro__ }}", ctx)
        self.assertNotIn("object", out)

    def test_broken_template_falls_back_instead_of_raising(self):
        """A bad customization must never abort the email carrying someone's passport."""
        ctx = build_email_text_context(pass_data=_Pass())
        raw = "{% if unclosed %}oops"
        self.assertEqual(render_email_text(raw, ctx), raw)

    def test_unknown_names_render_empty_rather_than_raising(self):
        ctx = build_email_text_context(pass_data=_Pass())
        self.assertEqual(render_email_text("[{{ nope.deeply.missing }}]", ctx), "[]")


if __name__ == "__main__":
    unittest.main()
