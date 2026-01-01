#!/usr/bin/env python3
"""
Email Prototype Sender
Sends the V3 email prototype to kdresdell@gmail.com for review.

Usage:
    cd /home/kdresdell/Documents/DEV/minipass_env/app
    source venv/bin/activate
    python send_prototype_email.py
"""

import os
import sys

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Flask app context
from app import app, db
from utils import send_email
import qrcode
from io import BytesIO
import base64

def generate_sample_qr_code():
    """Generate a sample QR code for the prototype"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data('PASSPORT-PROTOTYPE-V3-2025')
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()

def load_hero_image():
    """Load the hero image from the newPass template"""
    hero_path = os.path.join(
        os.path.dirname(__file__),
        'templates/email_templates/newPass/hero_new_pass.png'
    )
    if os.path.exists(hero_path):
        with open(hero_path, 'rb') as f:
            return f.read()
    return None

def load_org_logo():
    """Load an organization logo placeholder"""
    # Try to find an existing logo
    logo_paths = [
        os.path.join(os.path.dirname(__file__), 'static/uploads/1_owner_logo.png'),
        os.path.join(os.path.dirname(__file__), 'static/minipass_logo.png'),
    ]
    for logo_path in logo_paths:
        if os.path.exists(logo_path):
            with open(logo_path, 'rb') as f:
                return f.read()
    return None

def send_prototype():
    """Send the prototype email"""

    print("=" * 60)
    print("EMAIL PROTOTYPE V3 - SENDER")
    print("=" * 60)
    print()
    print("This script will send the improved email prototype to:")
    print("  kdresdell@gmail.com")
    print()
    print("Changes in V3 prototype:")
    print("  1. Card appears BEFORE QR code")
    print("  2. UNIFIED instruction + QR card (white/gray border)")
    print("  3. QR code INSIDE the instruction card")
    print("  4. Font sizes increased (16px body)")
    print("  5. Mobile margins reduced (75px -> 16px)")
    print("  6. Same width for all cards (consistent alignment)")
    print()

    # Load the prototype HTML
    prototype_path = os.path.join(
        os.path.dirname(__file__),
        'templates/email_templates/prototype_v3.html'
    )

    if not os.path.exists(prototype_path):
        print(f"ERROR: Prototype file not found at {prototype_path}")
        return False

    with open(prototype_path, 'r', encoding='utf-8') as f:
        html_body = f.read()

    print(f"Loaded prototype HTML: {len(html_body)} bytes")

    # Prepare inline images
    inline_images = {}

    # Load hero image
    hero_data = load_hero_image()
    if hero_data:
        inline_images['hero_image'] = hero_data
        print(f"Loaded hero image: {len(hero_data)} bytes")
    else:
        print("WARNING: Hero image not found, using placeholder")

    # Load organization logo
    org_logo_data = load_org_logo()
    if org_logo_data:
        inline_images['org_logo'] = org_logo_data
        print(f"Loaded org logo: {len(org_logo_data)} bytes")
    else:
        print("WARNING: Org logo not found, will show broken image")

    # Generate QR code
    qr_data = generate_sample_qr_code()
    inline_images['qr_code'] = qr_data
    print(f"Generated QR code: {len(qr_data)} bytes")

    # Send the email
    print()
    print("Sending email...")
    print("-" * 40)

    with app.app_context():
        try:
            result = send_email(
                subject="[PROTOTYPE V5] Bigger QR (300px/400px) + Consistent Widths",
                to_email="kdresdell@gmail.com",
                html_body=html_body,
                inline_images=inline_images
            )

            print("-" * 40)
            print()
            if result is not False:
                print("SUCCESS! Email sent.")
                print()
                print("Please check your inbox at kdresdell@gmail.com")
                print("Test on both DESKTOP and MOBILE views.")
                print()
                print("Key things to evaluate:")
                print("  - Is the unified instruction+QR card clear?")
                print("  - Is the QR code properly contained in the card?")
                print("  - Do all cards have consistent width?")
                print("  - Are mobile margins better?")
                print("  - Is the instruction text clear about SHOWING not scanning?")
                return True
            else:
                print("FAILED: Email was blocked (user opted out?)")
                return False

        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = send_prototype()
    sys.exit(0 if success else 1)
