#!/usr/bin/env python3
"""
Generate EmailLog entries for demo database
Shows the "magical automation" - professional emails for every action
"""

import random
import json
from datetime import datetime, timedelta, timezone
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import (Activity, Passport, User, Redemption, EmailLog)


# Email template configurations (from backup)
EMAIL_TEMPLATES = {
    'newPass': {
        'template_name': 'newPass_compiled/index.html',
        'subject': "Votre passe numérique pour le {emoji} est prête !"
    },
    'redeemPass': {
        'template_name': 'redeemPass_compiled/index.html',
        'subject': "{emoji} Activité confirmée !"
    },
    'paymentReceived': {
        'template_name': 'paymentReceived_compiled/index.html',
        'subject': "✅ Paiement confirmé !"
    },
    'latePayment': {
        'template_name': 'latePayment_compiled/index.html',
        'subject': "⚠️ Rappel - Passe numérique en attente de paiement"
    },
    'signup': {
        'template_name': 'signup_compiled/index.html',
        'subject': "🎉 Inscription confirmée !"
    },
    'survey': {
        'template_name': 'survey_invitation',
        'subject': "📝 Donnez-nous votre avis !"
    }
}

# Activity type emojis
ACTIVITY_EMOJIS = {
    'Hockey': '🏒',
    'Fitness': '🧘',
    'Boxing': '🥊',
    'Running': '🏃'
}


def create_email_log(timestamp, to_email, subject, pass_code, template_name):
    """Create an email log entry"""
    log = EmailLog(
        timestamp=timestamp,
        to_email=to_email,
        subject=subject,
        pass_code=pass_code,
        template_name=template_name,
        context_json=json.dumps({"demo": True}),
        result="SENT"
    )
    db.session.add(log)


def generate_email_logs():
    """Generate email log entries based on existing demo data"""

    print("Generating Email Logs...")

    # Get all activities
    activities = Activity.query.all()

    newpass_count = 0
    redeem_count = 0
    payment_count = 0
    late_count = 0
    signup_count = 0
    survey_count = 0

    for activity in activities:
        emoji = ACTIVITY_EMOJIS.get(activity.type, '🎫')
        print(f"\n  Processing: {activity.name} ({emoji})")

        # Get all passports for this activity
        passports = Passport.query.filter_by(activity_id=activity.id).all()

        for passport in passports:
            user = db.session.get(User, passport.user_id)

            # 1. New Passport email (sent when passport created)
            subject = EMAIL_TEMPLATES['newPass']['subject'].format(emoji=emoji)
            create_email_log(
                passport.created_dt + timedelta(seconds=random.randint(1, 30)),
                user.email,
                subject,
                passport.pass_code,
                EMAIL_TEMPLATES['newPass']['template_name']
            )
            newpass_count += 1

            # 2. Payment Received email (if paid)
            if passport.paid and passport.paid_date:
                create_email_log(
                    passport.paid_date + timedelta(seconds=random.randint(1, 30)),
                    user.email,
                    EMAIL_TEMPLATES['paymentReceived']['subject'],
                    passport.pass_code,
                    EMAIL_TEMPLATES['paymentReceived']['template_name']
                )
                payment_count += 1
            else:
                # Late payment reminder for unpaid
                late_date = passport.created_dt + timedelta(days=random.randint(3, 7))
                create_email_log(
                    late_date,
                    user.email,
                    EMAIL_TEMPLATES['latePayment']['subject'],
                    passport.pass_code,
                    EMAIL_TEMPLATES['latePayment']['template_name']
                )
                late_count += 1

            # 3. Redemption emails
            redemptions = Redemption.query.filter_by(passport_id=passport.id).all()
            for redemption in redemptions:
                subject = EMAIL_TEMPLATES['redeemPass']['subject'].format(emoji=emoji)
                create_email_log(
                    redemption.date_used + timedelta(seconds=random.randint(1, 60)),
                    user.email,
                    subject,
                    passport.pass_code,
                    EMAIL_TEMPLATES['redeemPass']['template_name']
                )
                redeem_count += 1

            # 4. Signup confirmation (randomly for some users)
            if random.random() < 0.25:  # 25% chance
                signup_date = passport.created_dt - timedelta(hours=random.randint(1, 24))
                create_email_log(
                    signup_date,
                    user.email,
                    EMAIL_TEMPLATES['signup']['subject'],
                    None,
                    EMAIL_TEMPLATES['signup']['template_name']
                )
                signup_count += 1

            # 5. Survey invitation (randomly for paid users)
            if passport.paid and random.random() < 0.15:  # 15% chance
                survey_date = passport.created_dt + timedelta(days=random.randint(7, 30))
                # Make timezone aware for comparison
                now = datetime.now(timezone.utc)
                survey_date_aware = survey_date.replace(tzinfo=timezone.utc) if survey_date.tzinfo is None else survey_date
                if survey_date_aware < now:
                    create_email_log(
                        survey_date,
                        user.email,
                        EMAIL_TEMPLATES['survey']['subject'],
                        passport.pass_code,
                        EMAIL_TEMPLATES['survey']['template_name']
                    )
                    survey_count += 1

        print(f"    Processed {len(passports)} passports")

    db.session.commit()

    return {
        'newPass': newpass_count,
        'redeemPass': redeem_count,
        'paymentReceived': payment_count,
        'latePayment': late_count,
        'signup': signup_count,
        'survey': survey_count
    }


def main():
    """Main function"""
    print("=" * 50)
    print("EMAIL LOG GENERATOR")
    print("=" * 50)
    print()

    with app.app_context():
        # Check if there are already logs
        existing = EmailLog.query.count()
        if existing > 0:
            print(f"Warning: {existing} existing email logs found. Clearing them first...")
            EmailLog.query.delete()
            db.session.commit()

        # Generate logs
        counts = generate_email_logs()

        # Summary
        total_logs = EmailLog.query.count()

        print()
        print("=" * 50)
        print("GENERATION COMPLETE")
        print("=" * 50)
        print(f"\nEmail logs by type:")
        print(f"  📬 New Passport:      {counts['newPass']}")
        print(f"  🏒 Activity Redeemed: {counts['redeemPass']}")
        print(f"  ✅ Payment Received:  {counts['paymentReceived']}")
        print(f"  ⚠️  Late Payment:      {counts['latePayment']}")
        print(f"  🎉 Signup:            {counts['signup']}")
        print(f"  📝 Survey:            {counts['survey']}")
        print(f"\n  TOTAL: {total_logs} emails")

        # Show recent samples
        print("\nRecent email samples:")
        recent = EmailLog.query.order_by(EmailLog.timestamp.desc()).limit(10).all()
        for log in recent:
            print(f"  {log.timestamp.strftime('%Y-%m-%d %H:%M')} | {log.subject[:50]}...")


if __name__ == "__main__":
    main()
