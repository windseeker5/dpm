#!/usr/bin/env python3
"""
Render every customer-facing surface to a standalone HTML file for design review.

WHY THIS EXISTS
---------------
The design skills need something to look at. `web-design-guidelines` reads source files, but
`frontend-design` works from rendered pages — and an email template is not a page you can
open. Without this, a design pass on the emails is guesswork.

Each email is rendered through the real `get_email_context()` and run through Premailer,
exactly as `send_email()` does, so the file on disk is what the customer receives. `cid:qr_code`
is swapped for a data URI so it displays in a browser; nothing else about the markup changes.

Output lands in test/render/ as plain .html — open them directly, or point Playwright at
file:// URLs to screenshot at several widths.

The web pages (passport, signup) are NOT rendered here: they need a live request context,
session and CSRF, so screenshot those from the running app at their real URLs instead.

Usage:
    source venv/bin/activate
    python test/render_all.py
"""
import base64
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'render')

TEMPLATES = [
    'newPass', 'paymentReceived', 'latePayment', 'redeemPass',
    'signup', 'signup_payment_first', 'survey_invitation',
]


def build_context(app_mod, activity, passport, template_type):
    """The same context a real send builds, so the render is faithful."""
    from utils import (get_email_context, _build_history_rows, _get_pass_url,
                       _get_booked_slot_labels, get_pass_history_data,
                       get_setting, NO_QR_TEMPLATES)

    base_url = get_setting('SITE_URL', '').rstrip('/')
    show_qr = template_type not in NO_QR_TEMPLATES

    base = {
        'pass_data': passport,
        'activity_name': activity.name,
        'show_qr_code': show_qr,
        'pass_url': _get_pass_url(passport),
        'uses_scheduling': bool(getattr(activity, 'uses_scheduling', False)),
        'booked_slots': _get_booked_slot_labels(passport),
        'history_rows': _build_history_rows(
            get_pass_history_data(passport.pass_code)),
        'owner_logo_url': f"{base_url}/owner-logo?activity_id={activity.id}",
        # Payment-first and survey extras, harmless on the templates that ignore them.
        'requested_amount': '150,00 $',
        'payment_email': get_setting('DISPLAY_PAYMENT_EMAIL') or get_setting('MAIL_USERNAME', ''),
        'needs_signup_code': True,
        'signup_code': 'MP-INS-0000001',
        'survey_url': f"{base_url}/survey/sample",
        'question_count': 8,
        'base_url': base_url,
    }
    return get_email_context(activity, template_type, base)


def main():
    import app as app_mod
    from flask import render_template
    from premailer import transform
    from models import Activity, Passport
    from utils import generate_qr_code_image

    os.makedirs(OUT_DIR, exist_ok=True)

    with app_mod.app.app_context(), app_mod.app.test_request_context():
        activity = Activity.query.filter_by(uses_scheduling=True).first() or Activity.query.first()
        passport = (Passport.query.filter_by(activity_id=activity.id).first()
                    or Passport.query.first())
        if not passport:
            print("No passport in the database to render with.")
            return 1

        qr_uri = 'data:image/png;base64,' + base64.b64encode(
            generate_qr_code_image(passport.pass_code)).decode()

        print(f"Activity: {activity.name} (customized: {bool(activity.email_templates)})")
        print(f"Passport: {passport.pass_code}\n")

        for t in TEMPLATES:
            ctx = build_context(app_mod, activity, passport, t)
            html = transform(render_template(f'email/{t}.html', **ctx))
            # Browsers can't resolve cid:, so inline the QR for viewing only.
            html = html.replace('cid:qr_code', qr_uri)

            path = os.path.join(OUT_DIR, f'email-{t}.html')
            with open(path, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"  {t:24} {len(html.encode())/1024:5.1f} KB  ->  {path}")

    print(f"\nWrote {len(TEMPLATES)} files to {OUT_DIR}")
    print("Screenshot them from file:// URLs, or open directly in a browser.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
