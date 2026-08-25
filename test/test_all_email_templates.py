#!/usr/bin/env python3
"""
Test All Email Templates — visual check of the whole set in one run

Sends all 7 email templates to kdresdell@gmail.com so the cosmetics can be judged together
in a real client, which is the one thing the browser preview cannot show: the preview turns
the QR from a CID attachment into a data URI and never touches SMTP.

Each is sent with fixed sample content and _skip_email_context, so what varies between runs
is the layout, not the data.

Templates tested:
1. newPass - New pass creation (with QR)
2. redeemPass - Pass redemption (with QR)
3. paymentReceived - Payment confirmation (with QR)
4. latePayment - Late payment reminder (NO QR - the pass isn't usable until it's paid)
5. signup - Signup confirmation (no QR)
6. signup_payment_first - Pay-first signup with Interac instructions (no QR)
7. survey_invitation - Survey invitation (no QR)

Images (see docs/EMAIL_DELIVERABILITY.md):
- hero and owner logo are hosted HTTP URLs, never CID
- only the QR code is attached as a CID inline image
- use_hosted_images=True is passed to send_email()

Requirements:
- SITE_URL must point at a host the mail client can reach (e.g. https://lhgi.minipass.me).
  Run this from the VPS to check images. Run it locally and the hero and logo will appear
  broken in Gmail, because SITE_URL is 127.0.0.1 — the layout and the QR still validate.

Usage:
    cd /home/kdresdell/Documents/DEV/minipass_env/app
    source venv/bin/activate
    python test/test_all_email_templates.py
"""

import os
import sys
import time

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from utils import send_email, get_setting
from utils_email_defaults import get_default_email_templates
import qrcode
from io import BytesIO
from flask import render_template

# Target email
TARGET_EMAIL = "kdresdell@gmail.com"

# Template directory
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates/email_templates')

# Activity ID to use for hero image URLs (must exist in the DB)
TEST_ACTIVITY_ID = 1


def generate_qr_code(data="PASSPORT-TEST-V16-2025"):
    """Generate a sample QR code as bytes"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()


def get_base_url():
    """Get SITE_URL from settings — required for Phase 3 hosted images"""
    base_url = get_setting('SITE_URL', '').rstrip('/')
    if not base_url:
        print("  ⚠️  WARNING: SITE_URL not set in app settings!")
        print("       Images will NOT display in emails.")
        print("       Set SITE_URL to https://lhgi.minipass.me in Admin > Settings.")
    return base_url


def get_owner_logo_url(base_url, activity_id):
    """Compute owner logo URL — activity-specific first, then org fallback"""
    activity_logo_path = os.path.join('static', 'uploads', f'{activity_id}_owner_logo.png')
    if os.path.exists(activity_logo_path):
        return f"{base_url}/static/uploads/{activity_id}_owner_logo.png"
    org_logo = get_setting('LOGO_FILENAME', 'logo.png')
    org_logo_path = os.path.join('static', 'uploads', org_logo)
    if os.path.exists(org_logo_path):
        return f"{base_url}/static/uploads/{org_logo}"
    return None


def sample_pass_data():
    """The passport shape templates/email/components.html reads.

    pass_block accesses pass_data.user.name, .uses_remaining, .sold_amt, .paid and
    .passport_type.sessions_included. This replaces the old render_owner_card() helper: the
    owner card was a pre-rendered owner_html block, and the reworked layout builds the pass
    block itself from the passport instead.

    5 of 8 credits on purpose, so the pips show both filled and spent.
    """
    return type('PassData', (object,), {
        'activity': type('obj', (object,), {
            'name': 'Hockey LHGI - Session Hiver 2025',
            'id': TEST_ACTIVITY_ID,
        })(),
        'user': type('obj', (object,), {
            'name': 'Jean-Marc Tremblay',
            'email': 'jmtremblay@example.com',
            'phone_number': '514-555-1234',
        })(),
        'passport_type': type('obj', (object,), {
            'name': 'Carte 8 activites',
            'sessions_included': 8,
        })(),
        'pass_code': 'MP-TEST-0000001',
        'sold_amt': 150.00,
        'uses_remaining': 5,
        'paid': True,
    })()


def sample_history_rows():
    """Rows for the restored history table, in the {label, date, by} shape
    utils._build_history_rows() produces for a real send."""
    return [
        {'label': 'Creation', 'date': '2026-01-15 09:12', 'by': 'admin'},
        {'label': 'Paiement', 'date': '2026-01-16 14:03', 'by': 'minipass-bot'},
        {'label': 'Participation 1', 'date': '2026-01-20 18:30', 'by': 'kdresdell'},
        {'label': 'Participation 2', 'date': '2026-01-27 18:26', 'by': 'kdresdell'},
    ]


def pass_context(base_url, show_qr=True, paid=True):
    """Context shared by the four passport templates."""
    pass_data = sample_pass_data()
    pass_data.paid = paid
    return {
        'pass_data': pass_data,
        'history_rows': sample_history_rows(),
        'booked_slots': ['samedi 31 janvier, 08:30'],
        'pass_url': f"{base_url}/pass/MP-TEST-0000001",
        'uses_scheduling': True,
        'show_qr_code': show_qr,
        'owner_logo_url': get_owner_logo_url(base_url, TEST_ACTIVITY_ID),
    }


def send_template(template_name, subject, context, inline_images):
    """Send a single template email — Phase 3: use_hosted_images=True"""
    # Bare name: safe_template() resolves it to templates/email/<name>.html.
    template_path = template_name

    try:
        result = send_email(
            subject=subject,
            to_email=TARGET_EMAIL,
            template_name=template_path,
            context=context,
            inline_images=inline_images,
            use_hosted_images=True
        )
        return result
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def test_newPass():
    """Test newPass template"""
    print("\n[1/7] Sending newPass template...")

    base_url = get_base_url()
    inline_images = {'qr_code': generate_qr_code("NEWPASS-V16-TEST")}

    context = {
        'title': 'Votre nouveau passe est pret!',
        'intro_text': '<p>Bonjour Jean-Marc,</p><p>Votre inscription a ete confirmee avec succes. Vous trouverez ci-dessous les details de votre passe ainsi que votre code QR personnel.</p>',
        **pass_context(base_url),
        'conclusion_text': '<p>Merci de votre confiance et a bientot!</p><p>L\'equipe LHGI</p>',
        'hero_image_url': f"{base_url}/activity/{TEST_ACTIVITY_ID}/hero-image/newPass",
        'owner_logo_url': get_owner_logo_url(base_url, TEST_ACTIVITY_ID),
        'site_url': base_url,
        'support_email': 'support@lhgi.minipass.me',
        'organization_name': 'LHGI Hockey',
        'organization_address': '123 rue du Sport, Montreal, QC H1A 1A1',
        'unsubscribe_url': f"{base_url}/unsubscribe",
        'privacy_url': f"{base_url}/privacy",
        'activity_name': 'Hockey LHGI - Session Hiver 2025',
        '_skip_email_context': True,
    }

    result = send_template('newPass', '[TEST V16] 1/7 - newPass Template', context, inline_images)
    print(f"  Result: {'SUCCESS' if result else 'FAILED'}")
    return result


def test_redeemPass():
    """Test redeemPass template"""
    print("\n[2/7] Sending redeemPass template...")

    base_url = get_base_url()
    inline_images = {'qr_code': generate_qr_code("REDEEMPASS-V16-TEST")}

    context = {
        'title': 'Activite enregistree!',
        'intro_text': '<p>Bonjour Jean-Marc,</p><p>Votre participation a ete enregistree avec succes. Voici un resume de votre passe.</p>',
        **pass_context(base_url),
        'conclusion_text': '<p>A la prochaine!</p><p>L\'equipe LHGI</p>',
        'hero_image_url': f"{base_url}/activity/{TEST_ACTIVITY_ID}/hero-image/redeemPass",
        'owner_logo_url': get_owner_logo_url(base_url, TEST_ACTIVITY_ID),
        'site_url': base_url,
        'support_email': 'support@lhgi.minipass.me',
        'organization_name': 'LHGI Hockey',
        'organization_address': '123 rue du Sport, Montreal, QC H1A 1A1',
        'unsubscribe_url': f"{base_url}/unsubscribe",
        'privacy_url': f"{base_url}/privacy",
        'activity_name': 'Hockey LHGI - Session Hiver 2025',
        '_skip_email_context': True,
    }

    result = send_template('redeemPass', '[TEST V16] 2/7 - redeemPass Template', context, inline_images)
    print(f"  Result: {'SUCCESS' if result else 'FAILED'}")
    return result


def test_paymentReceived():
    """Test paymentReceived template"""
    print("\n[3/7] Sending paymentReceived template...")

    base_url = get_base_url()
    inline_images = {'qr_code': generate_qr_code("PAYMENT-V16-TEST")}

    context = {
        'title': 'Paiement recu!',
        'intro_text': '<p>Bonjour Jean-Marc,</p><p>Nous avons bien recu votre paiement de <strong>150,00 $</strong>. Merci!</p>',
        **pass_context(base_url),
        'conclusion_text': '<p>Votre passe est maintenant actif. A bientot sur la glace!</p><p>L\'equipe LHGI</p>',
        'hero_image_url': f"{base_url}/activity/{TEST_ACTIVITY_ID}/hero-image/paymentReceived",
        'owner_logo_url': get_owner_logo_url(base_url, TEST_ACTIVITY_ID),
        'site_url': base_url,
        'support_email': 'support@lhgi.minipass.me',
        'organization_name': 'LHGI Hockey',
        'organization_address': '123 rue du Sport, Montreal, QC H1A 1A1',
        'unsubscribe_url': f"{base_url}/unsubscribe",
        'privacy_url': f"{base_url}/privacy",
        'activity_name': 'Hockey LHGI - Session Hiver 2025',
        '_skip_email_context': True,
    }

    result = send_template('paymentReceived', '[TEST V16] 3/7 - paymentReceived Template', context, inline_images)
    print(f"  Result: {'SUCCESS' if result else 'FAILED'}")
    return result


def test_latePayment():
    """Test latePayment template"""
    print("\n[4/7] Sending latePayment template...")

    base_url = get_base_url()
    # No QR: the latePayment layout renders none (the pass isn't usable until it's paid),
    # so attaching one would ship an unreferenced MIME part.
    inline_images = {}

    context = {
        'title': 'Rappel de paiement',
        'intro_text': '<p>Bonjour Jean-Marc,</p><p>Nous n\'avons pas encore recu votre paiement de <strong>150,00 $</strong> pour votre inscription. Veuillez effectuer le paiement dans les plus brefs delais.</p>',
        # Unpaid, and no QR — this is the one template whose pass isn't usable yet.
        **pass_context(base_url, show_qr=False, paid=False),
        'conclusion_text': '<p>Si vous avez des questions, n\'hesitez pas a nous contacter.</p><p>L\'equipe LHGI</p>',
        'hero_image_url': f"{base_url}/activity/{TEST_ACTIVITY_ID}/hero-image/latePayment",
        'owner_logo_url': get_owner_logo_url(base_url, TEST_ACTIVITY_ID),
        'site_url': base_url,
        'support_email': 'support@lhgi.minipass.me',
        'organization_name': 'LHGI Hockey',
        'organization_address': '123 rue du Sport, Montreal, QC H1A 1A1',
        'unsubscribe_url': f"{base_url}/unsubscribe",
        'privacy_url': f"{base_url}/privacy",
        'activity_name': 'Hockey LHGI - Session Hiver 2025',
        '_skip_email_context': True,
    }

    result = send_template('latePayment', '[TEST V16] 4/7 - latePayment Template', context, inline_images)
    print(f"  Result: {'SUCCESS' if result else 'FAILED'}")
    return result


def test_signup():
    """Test signup template"""
    print("\n[5/7] Sending signup template...")

    base_url = get_base_url()
    inline_images = {}  # No QR code for signup

    context = {
        'title': 'Inscription confirmee!',
        'intro_text': '<p>Bonjour Jean-Marc,</p><p>Nous avons bien recu votre inscription pour <strong>Hockey LHGI - Session Hiver 2025</strong>.</p><p>Votre inscription sera completee une fois le paiement recu.</p>',
        'conclusion_text': '<p>Merci de votre interet!</p><p>L\'equipe LHGI</p>',
        'hero_image_url': f"{base_url}/activity/{TEST_ACTIVITY_ID}/hero-image/signup",
        'site_url': base_url,
        'support_email': 'support@lhgi.minipass.me',
        'organization_name': 'LHGI Hockey',
        'organization_address': '123 rue du Sport, Montreal, QC H1A 1A1',
        'unsubscribe_url': f"{base_url}/unsubscribe",
        'privacy_url': f"{base_url}/privacy",
        'activity_name': 'Hockey LHGI - Session Hiver 2025',
        '_skip_email_context': True,
    }

    result = send_template('signup', '[TEST V16] 5/7 - signup Template', context, inline_images)
    print(f"  Result: {'SUCCESS' if result else 'FAILED'}")
    return result


def test_signup_payment_first():
    """Test signup_payment_first template - Pay First workflow with Interac logo

    V16: Phase 3 — Interac logo served via {{ site_url }}/static/images/email/interac-logo.jpg
    """
    print("\n[6/7] Sending signup_payment_first template...")

    base_url = get_base_url()

    # Load defaults from JSON (single source of truth)
    defaults = get_default_email_templates()
    template_defaults = defaults.get('signup_payment_first', {})

    inline_images = {}  # No QR, no CID attachments — interac logo served via site_url

    test_user_name = 'Jean-Marc Tremblay'
    test_activity_name = 'Hockey LHGI - Session Hiver 2025'
    test_activity_location = '123 rue du Sport, Montreal, QC H1A 1A1'
    test_organization_name = 'LHGI Hockey'

    context = {
        # From JSON defaults
        'title': template_defaults.get('title', 'Pré-inscription reçue — Paiement requis'),
        'intro_text': template_defaults.get('intro_text', '').replace('{{ user_name }}', test_user_name).replace('{{ activity_name }}', test_activity_name),
        'conclusion_text': template_defaults.get('conclusion_text', '').replace('{{ organization_name }}', test_organization_name),

        # Template layout variables
        'requested_amount': '150,00 $',
        'payment_email': 'paiement@lhgi.minipass.me',
        'needs_signup_code': True,
        'signup_code': 'MP-INS-0000042',

        # Activity/user context
        'user_name': test_user_name,
        'activity_name': test_activity_name,
        'activity': {'location_address_formatted': test_activity_location},
        'organization_name': test_organization_name,

        # Phase 3 — hosted images
        'hero_image_url': f"{base_url}/activity/{TEST_ACTIVITY_ID}/hero-image/signup_payment_first",
        'site_url': base_url,

        # Standard footer context
        'support_email': 'support@lhgi.minipass.me',
        'organization_address': test_activity_location,
        'unsubscribe_url': f"{base_url}/unsubscribe",
        'privacy_url': f"{base_url}/privacy",
        '_skip_email_context': True,
    }

    result = send_template('signup_payment_first', '[TEST V16] 6/7 - signup_payment_first', context, inline_images)
    print(f"  Result: {'SUCCESS' if result else 'FAILED'}")
    return result


def test_survey_invitation():
    """Test survey_invitation template"""
    print("\n[7/7] Sending survey_invitation template...")

    base_url = get_base_url()
    inline_images = {}  # No QR code for survey

    context = {
        'title': 'Votre avis compte!',
        'intro_text': '<p>Bonjour Jean-Marc,</p><p>Nous aimerions connaitre votre experience avec <strong>Hockey LHGI - Session Hiver 2025</strong>.</p><p>Votre feedback nous aide a ameliorer nos services.</p>',
        'conclusion_text': '<p>Le sondage ne prend que 2 minutes. Merci d\'avance!</p><p>L\'equipe LHGI</p>',
        'survey_url': f"{base_url}/survey/abc123",
        'hero_image_url': f"{base_url}/activity/{TEST_ACTIVITY_ID}/hero-image/survey_invitation",
        'site_url': base_url,
        'support_email': 'support@lhgi.minipass.me',
        'organization_name': 'LHGI Hockey',
        'organization_address': '123 rue du Sport, Montreal, QC H1A 1A1',
        'unsubscribe_url': f"{base_url}/unsubscribe",
        'privacy_url': f"{base_url}/privacy",
        'activity_name': 'Hockey LHGI - Session Hiver 2025',
        '_skip_email_context': True,
    }

    result = send_template('survey_invitation', '[TEST V16] 7/7 - survey_invitation Template', context, inline_images)
    print(f"  Result: {'SUCCESS' if result else 'FAILED'}")
    return result


def main():
    """Send all 7 email templates"""
    print("=" * 60)
    print("EMAIL TEMPLATE V16 - Phase 3 Hybrid Hosted Images")
    print("=" * 60)
    print(f"\nTarget email: {TARGET_EMAIL}")
    print(f"Test activity ID: {TEST_ACTIVITY_ID}")
    with app.app_context():
        site_url = get_setting('SITE_URL', '')
        print(f"SITE_URL: {site_url or '(NOT SET — images will be broken)'}")
    print("\nTemplates to test:")
    print("  1. newPass (QR + hosted hero/logo)")
    print("  2. redeemPass (QR + hosted hero/logo)")
    print("  3. paymentReceived (QR + hosted hero/logo)")
    print("  4. latePayment (no QR + hosted hero/logo)")
    print("  5. signup (hosted hero only)")
    print("  6. signup_payment_first (hosted hero + interac via site_url)")
    print("  7. survey_invitation (hosted hero only)")
    print("\n" + "-" * 60)

    results = {}

    with app.app_context():
        results['newPass'] = test_newPass()
        time.sleep(1)  # Small delay between emails

        results['redeemPass'] = test_redeemPass()
        time.sleep(1)

        results['paymentReceived'] = test_paymentReceived()
        time.sleep(1)

        results['latePayment'] = test_latePayment()
        time.sleep(1)

        results['signup'] = test_signup()
        time.sleep(1)

        results['signup_payment_first'] = test_signup_payment_first()
        time.sleep(1)

        results['survey_invitation'] = test_survey_invitation()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    success_count = sum(1 for r in results.values() if r)
    fail_count = len(results) - success_count

    for template, result in results.items():
        status = "OK" if result else "FAIL"
        print(f"  {template}: {status}")

    print(f"\nTotal: {success_count}/7 successful, {fail_count}/7 failed")
    print(f"\nCheck your inbox at: {TARGET_EMAIL}")
    print("\nWhat to check in Gmail:")
    print("  - Layout holds on a phone (single column, nothing squeezed side by side)")
    print("  - Credit pips read 5 filled / 3 hollow, not a wall of dots")
    print("  - History table is readable: label + date, operator beneath")
    print("  - Amounts are French — 150,00 $ — never $150.00")
    print("  - QR scans in newPass/redeemPass/paymentReceived; latePayment has none")
    print("  - Accent bar colour differs per template, and is visible with images blocked")
    print("  - No stray {{ }} or {% %} anywhere in the body")
    print("  - Email size stays well under 100 KB")
    print("\n  Hero and owner logo only load if SITE_URL is reachable from Gmail.")
    print("  Sending from localhost, expect those two broken — everything else still counts.")
    print("=" * 60)

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
