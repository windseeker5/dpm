#!/usr/bin/env python3
"""
Demo Data Generator for Minipass Promotional Video
Generates realistic Quebec/Canadian data for 4 activities
"""

import random
import string
from datetime import datetime, timedelta, timezone
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import (Activity, PassportType, Passport, User,
                    Income, Expense, Redemption)

# Quebec/Canadian Names
FIRST_NAMES = [
    "Marc", "Sophie", "Jean-Philippe", "Marie-Eve", "Luc", "Isabelle",
    "Francois", "Amelie", "Pierre", "Julie", "Simon", "Catherine",
    "Alexandre", "Genevieve", "Patrick", "Valerie", "Martin", "Nathalie",
    "Eric", "Stephanie", "David", "Caroline", "Michel", "Karine",
    "Andre", "Josee", "Daniel", "Annie", "Sylvain", "Melanie",
    "Benoit", "Chantal", "Nicolas", "Manon", "Guillaume", "Sylvie",
    "Mathieu", "Veronique", "Christian", "Johanne", "Bruno", "Line",
    "Alain", "Helene", "Yves", "Diane", "Richard", "Lucie",
    "Pascal", "Martine", "Louis", "Nadia", "Jean", "Monique",
    "Serge", "Dominique", "Robert", "France", "Jacques", "Ginette",
    "Claude", "Suzanne", "Gilles", "Therese", "Rene", "Nicole",
    "Marcel", "Francoise", "Paul", "Denise", "Roger", "Michelle",
    "Jean-Marc", "Marie-Claude", "Jean-Pierre", "Anne-Marie", "Philippe", "Christine"
]

LAST_NAMES = [
    "Tremblay", "Gagnon", "Roy", "Cote", "Bouchard", "Gauthier",
    "Morin", "Lavoie", "Fortin", "Gagne", "Ouellet", "Pelletier",
    "Belanger", "Levesque", "Bergeron", "Leblanc", "Paquette", "Girard",
    "Simard", "Boucher", "Poirier", "Caron", "Beaulieu", "Cloutier",
    "Dube", "Blais", "Dion", "Boisvert", "Fournier", "Hebert",
    "Lachance", "Thibault", "Mercier", "Savard", "Nadeau", "Martel",
    "Plante", "Michaud", "Gingras", "Perron", "Lapointe", "Breton",
    "Bolduc", "Lessard", "Carrier", "Beaudoin", "Drouin", "Turgeon",
    "Leclerc", "Parent", "Langlois", "Harvey", "Proulx", "Lemieux"
]

EMAIL_DOMAINS = ['gmail.com', 'outlook.com', 'videotron.ca', 'bell.ca', 'hotmail.com', 'yahoo.ca']


def generate_pass_code():
    """Generate unique pass code like MP-XXXX-XXXX"""
    chars = string.ascii_uppercase + string.digits
    return f"MP-{''.join(random.choices(chars, k=4))}-{''.join(random.choices(chars, k=4))}"


def generate_name():
    """Generate random Quebec-style name"""
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def generate_email(name):
    """Generate email from name"""
    # Simplify name for email
    clean = name.lower()
    clean = clean.replace(' ', '.').replace('-', '')
    # Remove accents manually
    accents = {'e': 'e', 'e': 'e', 'a': 'a', 'i': 'i', 'o': 'o', 'u': 'u'}
    domain = random.choice(EMAIL_DOMAINS)
    # Add random number to avoid duplicates
    suffix = random.randint(1, 999)
    return f"{clean}{suffix}@{domain}"


def random_date_between(start_date, end_date):
    """Generate random datetime between two dates"""
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    random_seconds = random.randint(0, 86400)
    return start_date + timedelta(days=random_days, seconds=random_seconds)


def create_activity(name, activity_type, admin_id, goal_revenue, description, start_date, end_date):
    """Create an activity"""
    activity = Activity(
        name=name,
        type=activity_type,
        description=description,
        start_date=start_date,
        end_date=end_date,
        created_by=admin_id,
        created_dt=datetime.now(timezone.utc) - timedelta(days=random.randint(30, 90)),
        status="active",
        goal_revenue=goal_revenue
    )
    db.session.add(activity)
    db.session.flush()
    return activity


def create_passport_type(activity_id, name, price, sessions, ptype):
    """Create a passport type"""
    pt = PassportType(
        activity_id=activity_id,
        name=name,
        type=ptype,
        price_per_user=price,
        sessions_included=sessions,
        target_revenue=0,
        created_dt=datetime.now(timezone.utc) - timedelta(days=random.randint(30, 90)),
        status="active"
    )
    db.session.add(pt)
    db.session.flush()
    return pt


def create_user_and_passport(activity, passport_type, admin_id, paid=True, created_date=None):
    """Create a user with their passport"""
    name = generate_name()
    email = generate_email(name)

    user = User(
        name=name,
        email=email,
        phone_number=f"514-{random.randint(200, 999)}-{random.randint(1000, 9999)}" if random.random() > 0.3 else None,
        email_opt_out=random.random() < 0.05  # 5% opt out
    )
    db.session.add(user)
    db.session.flush()

    if created_date is None:
        created_date = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 60))

    passport = Passport(
        pass_code=generate_pass_code(),
        user_id=user.id,
        activity_id=activity.id,
        passport_type_id=passport_type.id,
        passport_type_name=passport_type.name,
        sold_amt=passport_type.price_per_user,
        uses_remaining=passport_type.sessions_included,
        created_by=admin_id,
        created_dt=created_date,
        paid=paid,
        paid_date=created_date + timedelta(days=random.randint(0, 3)) if paid else None,
        marked_paid_by="admin@minipass.me" if paid else None
    )
    db.session.add(passport)
    db.session.flush()

    return user, passport


def create_redemptions(passport, count, start_date, end_date):
    """Create redemption records for a passport"""
    for _ in range(count):
        redemption = Redemption(
            passport_id=passport.id,
            date_used=random_date_between(start_date, end_date),
            redeemed_by="Scanner"
        )
        db.session.add(redemption)
        # Decrement uses remaining
        if passport.uses_remaining > 0:
            passport.uses_remaining -= 1


def create_income(activity, category, amount, note, date, payment_method="e-transfer"):
    """Create income record"""
    income = Income(
        activity_id=activity.id,
        date=date,
        category=category,
        amount=amount,
        note=note,
        created_by="admin@minipass.me",
        payment_status="received",
        payment_date=date,
        payment_method=payment_method
    )
    db.session.add(income)


def create_expense(activity, category, amount, description, date, payment_method="e-transfer"):
    """Create expense record"""
    expense = Expense(
        activity_id=activity.id,
        date=date,
        category=category,
        amount=amount,
        description=description,
        created_by="admin@minipass.me",
        payment_status="paid",
        payment_date=date,
        payment_method=payment_method
    )
    db.session.add(expense)


def generate_hockey_league():
    """Generate Ligue Hockey Centrale - 100+ passports"""
    print("Creating Ligue Hockey Centrale...")

    activity = create_activity(
        name="Ligue Hockey Centrale",
        activity_type="Hockey",
        admin_id=1,
        goal_revenue=25000,
        description="Ligue de hockey recreatif pour adultes. Matchs le midi.",
        start_date=datetime(2025, 9, 1, tzinfo=timezone.utc),
        end_date=datetime(2026, 4, 30, tzinfo=timezone.utc)
    )

    # Create passport types
    pt_regular = create_passport_type(activity.id, "Regulier - Saison", 200.0, 30, "permanent")
    pt_sub = create_passport_type(activity.id, "Remplacant", 25.0, 1, "substitute")

    passports = []

    # 85 Regular passports (80 paid, 5 unpaid)
    for i in range(85):
        paid = i < 80
        _, passport = create_user_and_passport(activity, pt_regular, 1, paid)
        passports.append((passport, "regular"))

    # 25 Substitute passports (22 paid, 3 unpaid)
    for i in range(25):
        paid = i < 22
        _, passport = create_user_and_passport(activity, pt_sub, 1, paid)
        passports.append((passport, "sub"))

    # Create redemptions (spread across season)
    season_start = datetime(2025, 9, 15, tzinfo=timezone.utc)
    season_current = datetime.now(timezone.utc)

    for passport, ptype in passports:
        if passport.paid:
            if ptype == "regular":
                # Regular players: 3-8 redemptions each
                redemption_count = random.randint(3, 8)
            else:
                # Subs: 1-3 redemptions
                redemption_count = random.randint(1, 3)
            create_redemptions(passport, redemption_count, season_start, season_current)

    # Create income records
    create_income(activity, "Commandite", 3000.0, "Commandite corporative Desjardins",
                  datetime(2025, 8, 15, tzinfo=timezone.utc))
    create_income(activity, "Dons", 500.0, "Don anonyme",
                  datetime(2025, 9, 10, tzinfo=timezone.utc))
    create_income(activity, "Tournoi", 1500.0, "Tournoi amical septembre",
                  datetime(2025, 9, 25, tzinfo=timezone.utc))

    # Create expense records
    create_expense(activity, "Location", 8000.0, "Location glace - saison complete",
                   datetime(2025, 8, 20, tzinfo=timezone.utc))
    create_expense(activity, "Arbitres", 1500.0, "Arbitres - premiere moitie saison",
                   datetime(2025, 9, 1, tzinfo=timezone.utc))
    create_expense(activity, "Equipement", 800.0, "Rondelles et equipement",
                   datetime(2025, 8, 25, tzinfo=timezone.utc))
    create_expense(activity, "Assurance", 1200.0, "Assurance responsabilite",
                   datetime(2025, 8, 1, tzinfo=timezone.utc))

    print(f"  Created {len(passports)} passports")
    return activity


def generate_yoga_studio():
    """Generate Studio Yoga Harmonie - ~50 passports"""
    print("Creating Studio Yoga Harmonie...")

    activity = create_activity(
        name="Studio Yoga Harmonie",
        activity_type="Fitness",
        admin_id=1,
        goal_revenue=5000,
        description="Studio de yoga pour tous les niveaux. Vinyasa, Hatha, et Yin yoga.",
        start_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
        end_date=datetime(2025, 12, 31, tzinfo=timezone.utc)
    )

    # Create passport types
    pt_monthly = create_passport_type(activity.id, "Mensuel - Illimite", 80.0, 20, "permanent")
    pt_dropin = create_passport_type(activity.id, "A la seance", 15.0, 1, "substitute")
    pt_pack = create_passport_type(activity.id, "Forfait 10 cours", 120.0, 10, "permanent")

    passports = []

    # 30 Monthly (28 paid, 2 unpaid)
    for i in range(30):
        paid = i < 28
        _, passport = create_user_and_passport(activity, pt_monthly, 1, paid)
        passports.append((passport, "monthly"))

    # 15 Drop-in (all paid)
    for i in range(15):
        _, passport = create_user_and_passport(activity, pt_dropin, 1, True)
        passports.append((passport, "dropin"))

    # 8 Class packs (7 paid, 1 unpaid)
    for i in range(8):
        paid = i < 7
        _, passport = create_user_and_passport(activity, pt_pack, 1, paid)
        passports.append((passport, "pack"))

    # Create redemptions
    year_start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    current = datetime.now(timezone.utc)

    for passport, ptype in passports:
        if passport.paid:
            if ptype == "monthly":
                redemption_count = random.randint(8, 15)
            elif ptype == "dropin":
                redemption_count = 1
            else:  # pack
                redemption_count = random.randint(4, 8)
            create_redemptions(passport, redemption_count, year_start, current)

    # Income
    create_income(activity, "Ventes", 300.0, "Ventes accessoires yoga",
                  datetime(2025, 3, 15, tzinfo=timezone.utc))
    create_income(activity, "Atelier", 450.0, "Atelier meditation",
                  datetime(2025, 4, 20, tzinfo=timezone.utc))

    # Expenses
    create_expense(activity, "Location", 1200.0, "Location studio - trimestre",
                   datetime(2025, 1, 5, tzinfo=timezone.utc))
    create_expense(activity, "Equipement", 400.0, "Tapis et blocs yoga",
                   datetime(2025, 1, 10, tzinfo=timezone.utc))
    create_expense(activity, "Marketing", 150.0, "Publicite Facebook",
                   datetime(2025, 2, 1, tzinfo=timezone.utc))

    print(f"  Created {len(passports)} passports")
    return activity


def generate_boxing_club():
    """Generate Club Boxe Elite - ~25 passports"""
    print("Creating Club Boxe Elite...")

    activity = create_activity(
        name="Club Boxe Elite",
        activity_type="Boxing",
        admin_id=1,
        goal_revenue=4500,
        description="Club de boxe recreatif et competitif. Cours de groupe et entrainement prive.",
        start_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
        end_date=datetime(2025, 12, 31, tzinfo=timezone.utc)
    )

    # Create passport types
    pt_member = create_passport_type(activity.id, "Membre - Mensuel", 150.0, 12, "permanent")
    pt_private = create_passport_type(activity.id, "Entrainement prive", 50.0, 1, "substitute")

    passports = []

    # 15 Members (14 paid, 1 unpaid)
    for i in range(15):
        paid = i < 14
        _, passport = create_user_and_passport(activity, pt_member, 1, paid)
        passports.append((passport, "member"))

    # 12 Private sessions (11 paid, 1 unpaid)
    for i in range(12):
        paid = i < 11
        _, passport = create_user_and_passport(activity, pt_private, 1, paid)
        passports.append((passport, "private"))

    # Create redemptions
    year_start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    current = datetime.now(timezone.utc)

    for passport, ptype in passports:
        if passport.paid:
            if ptype == "member":
                redemption_count = random.randint(6, 12)
            else:
                redemption_count = 1
            create_redemptions(passport, redemption_count, year_start, current)

    # Income
    create_income(activity, "Equipement", 500.0, "Vente gants et equipement",
                  datetime(2025, 2, 20, tzinfo=timezone.utc))
    create_income(activity, "Evenement", 350.0, "Soiree combat exhibition",
                  datetime(2025, 5, 10, tzinfo=timezone.utc))

    # Expenses
    create_expense(activity, "Location", 1000.0, "Location salle - trimestre",
                   datetime(2025, 1, 3, tzinfo=timezone.utc))
    create_expense(activity, "Equipement", 600.0, "Sacs de frappe et ring",
                   datetime(2025, 1, 15, tzinfo=timezone.utc))
    create_expense(activity, "Assurance", 450.0, "Assurance sport contact",
                   datetime(2025, 1, 1, tzinfo=timezone.utc))

    print(f"  Created {len(passports)} passports")
    return activity


def generate_running_club():
    """Generate Groupe Course Performance - ~30 passports"""
    print("Creating Groupe Course Performance...")

    activity = create_activity(
        name="Groupe Course Performance",
        activity_type="Running",
        admin_id=1,
        goal_revenue=4000,
        description="Club de course a pied. Entrainements de groupe et preparation courses.",
        start_date=datetime(2025, 4, 1, tzinfo=timezone.utc),
        end_date=datetime(2025, 10, 31, tzinfo=timezone.utc)
    )

    # Create passport types
    pt_season = create_passport_type(activity.id, "Saison complete", 100.0, 24, "permanent")
    pt_race = create_passport_type(activity.id, "Inscription course", 35.0, 1, "substitute")

    passports = []

    # 20 Season (18 paid, 2 unpaid)
    for i in range(20):
        paid = i < 18
        _, passport = create_user_and_passport(activity, pt_season, 1, paid)
        passports.append((passport, "season"))

    # 12 Race entries (all paid)
    for i in range(12):
        _, passport = create_user_and_passport(activity, pt_race, 1, True)
        passports.append((passport, "race"))

    # Create redemptions
    season_start = datetime(2025, 4, 1, tzinfo=timezone.utc)
    current = datetime.now(timezone.utc)

    for passport, ptype in passports:
        if passport.paid:
            if ptype == "season":
                redemption_count = random.randint(8, 16)
            else:
                redemption_count = 1
            create_redemptions(passport, redemption_count, season_start, current)

    # Income
    create_income(activity, "Courses", 800.0, "Frais inscription course 10K",
                  datetime(2025, 6, 1, tzinfo=timezone.utc))
    create_income(activity, "Commandite", 400.0, "Commandite boutique sport",
                  datetime(2025, 5, 15, tzinfo=timezone.utc))

    # Expenses
    create_expense(activity, "Permis", 300.0, "Permis utilisation parc",
                   datetime(2025, 4, 1, tzinfo=timezone.utc))
    create_expense(activity, "Equipement", 200.0, "Cones et materiel",
                   datetime(2025, 4, 5, tzinfo=timezone.utc))
    create_expense(activity, "Evenement", 450.0, "Organisation course 10K",
                   datetime(2025, 5, 25, tzinfo=timezone.utc))

    print(f"  Created {len(passports)} passports")
    return activity


def main():
    """Main function to generate all demo data"""
    print("=" * 50)
    print("MINIPASS DEMO DATA GENERATOR")
    print("=" * 50)
    print()

    with app.app_context():
        # Generate all activities
        generate_hockey_league()
        generate_yoga_studio()
        generate_boxing_club()
        generate_running_club()

        # Commit all changes
        db.session.commit()

        # Print summary
        print()
        print("=" * 50)
        print("GENERATION COMPLETE - SUMMARY")
        print("=" * 50)

        from sqlalchemy import func

        activities = Activity.query.all()
        total_passports = 0
        total_paid = 0
        total_unpaid = 0
        total_redemptions = 0

        for activity in activities:
            passports = Passport.query.filter_by(activity_id=activity.id).all()
            paid_count = sum(1 for p in passports if p.paid)
            unpaid_count = len(passports) - paid_count
            redemptions = Redemption.query.join(Passport).filter(Passport.activity_id == activity.id).count()
            revenue = sum(p.sold_amt for p in passports if p.paid)

            print(f"\n{activity.name}:")
            print(f"  Passports: {len(passports)} (paid: {paid_count}, unpaid: {unpaid_count})")
            print(f"  Redemptions: {redemptions}")
            print(f"  Revenue from passes: ${revenue:,.2f}")

            total_passports += len(passports)
            total_paid += paid_count
            total_unpaid += unpaid_count
            total_redemptions += redemptions

        print()
        print("-" * 50)
        print(f"TOTALS:")
        print(f"  Activities: {len(activities)}")
        print(f"  Passports: {total_passports} (paid: {total_paid}, unpaid: {total_unpaid})")
        print(f"  Redemptions: {total_redemptions}")
        print(f"  Users: {User.query.count()}")


if __name__ == "__main__":
    main()
