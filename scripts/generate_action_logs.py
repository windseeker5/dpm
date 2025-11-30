#!/usr/bin/env python3
"""
Generate AdminActionLog entries for demo database
Populates the Recent Events and Activity Log sections
"""

import random
from datetime import datetime, timedelta, timezone
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import (Activity, PassportType, Passport, User,
                    Income, Expense, Redemption, AdminActionLog)


ADMIN_EMAILS = ["admin@minipass.me", "demo@minipass.me"]


def create_log(timestamp, admin_email, action):
    """Create an admin action log entry"""
    log = AdminActionLog(
        timestamp=timestamp,
        admin_email=admin_email,
        action=action
    )
    db.session.add(log)


def generate_action_logs():
    """Generate all admin action log entries based on existing demo data"""

    print("Generating Admin Action Logs...")

    # Get all activities
    activities = Activity.query.all()

    for activity in activities:
        admin = random.choice(ADMIN_EMAILS)

        # Activity Created log
        pt_count = PassportType.query.filter_by(activity_id=activity.id, status='active').count()
        create_log(
            activity.created_dt,
            admin,
            f"Activity Created: {activity.name} with {pt_count} passport types"
        )
        print(f"  Activity Created: {activity.name}")

        # Get all passports for this activity
        passports = Passport.query.filter_by(activity_id=activity.id).all()

        for passport in passports:
            user = User.query.get(passport.user_id)
            admin = random.choice(ADMIN_EMAILS)

            # Passport created log
            create_log(
                passport.created_dt,
                admin,
                f"Passport created for {user.name} for activity '{activity.name}' by {admin}"
            )

            # Marked as paid log (if paid)
            if passport.paid and passport.paid_date:
                create_log(
                    passport.paid_date,
                    admin,
                    f"Passport for {user.name} ({passport.pass_code}) marked as PAID by {admin}"
                )

            # Redemption logs
            redemptions = Redemption.query.filter_by(passport_id=passport.id).all()
            for redemption in redemptions:
                redeemer = random.choice(ADMIN_EMAILS)
                create_log(
                    redemption.date_used,
                    redeemer,
                    f"Passport for {user.name} ({passport.pass_code}) was redeemed by {redeemer}"
                )

        print(f"    {len(passports)} passport logs created")

        # Income logs
        incomes = Income.query.filter_by(activity_id=activity.id).all()
        for income in incomes:
            admin = random.choice(ADMIN_EMAILS)
            create_log(
                income.date,
                admin,
                f"Added Income: ${income.amount:.2f} - {income.category} for Activity '{activity.name}'"
            )

        # Expense logs
        expenses = Expense.query.filter_by(activity_id=activity.id).all()
        for expense in expenses:
            admin = random.choice(ADMIN_EMAILS)
            create_log(
                expense.date,
                admin,
                f"Added Expense: ${expense.amount:.2f} - {expense.category} for Activity '{activity.name}'"
            )

        print(f"    {len(incomes)} income + {len(expenses)} expense logs created")

    db.session.commit()


def main():
    """Main function"""
    print("=" * 50)
    print("ADMIN ACTION LOG GENERATOR")
    print("=" * 50)
    print()

    with app.app_context():
        # Check if there are already logs
        existing = AdminActionLog.query.count()
        if existing > 0:
            print(f"Warning: {existing} existing logs found. Clearing them first...")
            AdminActionLog.query.delete()
            db.session.commit()

        # Generate logs
        generate_action_logs()

        # Summary
        total_logs = AdminActionLog.query.count()
        recent_logs = AdminActionLog.query.filter(
            AdminActionLog.action.notlike('%API Call%')
        ).order_by(AdminActionLog.timestamp.desc()).limit(10).all()

        print()
        print("=" * 50)
        print("GENERATION COMPLETE")
        print("=" * 50)
        print(f"Total logs created: {total_logs}")
        print()
        print("Recent entries sample:")
        for log in recent_logs:
            print(f"  {log.timestamp.strftime('%Y-%m-%d %H:%M')} - {log.action[:70]}...")


if __name__ == "__main__":
    main()
