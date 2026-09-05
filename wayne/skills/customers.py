"""Trusted customer-history skills for Wayne."""

from sqlalchemy import func, or_

from models import Passport, Redemption, Signup, User, db
from wayne.types import SkillDefinition, SkillResult
from .helpers import MAX_ROWS, money


def customer_summary(args, language):
    customer = (args.get("customer") or "").strip()
    if not customer:
        answer = (
            "Indiquez le nom ou le courriel du client."
            if language == "fr"
            else "Please include the customer’s name or email."
        )
        return SkillResult(answer=answer)

    users = (
        User.query
        .filter(or_(func.lower(User.name).contains(customer.lower()), func.lower(User.email).contains(customer.lower())))
        .order_by(User.name)
        .limit(20)
        .all()
    )
    groups = {}
    for user in users:
        key = (user.email or user.name).strip().lower()
        groups.setdefault(key, {"name": user.name, "email": user.email, "ids": []})["ids"].append(user.id)

    rows = []
    for group in groups.values():
        user_ids = group["ids"]
        signup_count = Signup.query.filter(Signup.user_id.in_(user_ids)).count()
        passport_count = Passport.query.filter(Passport.user_id.in_(user_ids)).count()
        paid_total = (
            db.session.query(func.coalesce(func.sum(Passport.sold_amt), 0))
            .filter(Passport.user_id.in_(user_ids), Passport.paid.is_(True))
            .scalar() or 0
        )
        credits = (
            db.session.query(func.coalesce(func.sum(Passport.uses_remaining), 0))
            .filter(Passport.user_id.in_(user_ids), Passport.paid.is_(True))
            .scalar() or 0
        )
        redemption_count, last_visit = (
            db.session.query(func.count(Redemption.id), func.max(Redemption.date_used))
            .join(Passport, Passport.id == Redemption.passport_id)
            .filter(Passport.user_id.in_(user_ids))
            .first()
        )
        amount_due = (
            db.session.query(func.coalesce(func.sum(Signup.requested_amount), 0))
            .filter(
                Signup.user_id.in_(user_ids),
                Signup.paid.is_(False),
                ~Signup.status.in_(("rejected", "cancelled")),
            )
            .scalar() or 0
        )
        rows.append([
            group["name"],
            group["email"] or "—",
            signup_count,
            passport_count,
            money(paid_total),
            int(credits),
            redemption_count,
            last_visit.strftime("%Y-%m-%d") if last_visit else "—",
            money(amount_due),
        ])

    if not rows:
        answer = (
            f"Je n’ai trouvé aucun client correspondant à « {customer} »."
            if language == "fr"
            else f"I found no customer matching “{customer}”."
        )
    elif len(rows) == 1:
        answer = (
            f"Voici le résumé de {rows[0][0]}."
            if language == "fr"
            else f"Here is the summary for {rows[0][0]}."
        )
    else:
        answer = (
            f"J’ai trouvé {len(rows)} clients correspondant à « {customer} »."
            if language == "fr"
            else f"I found {len(rows)} customers matching “{customer}”."
        )
    columns = (
        ["Client", "Courriel", "Inscriptions", "Passeports", "Montant payé", "Crédits", "Présences", "Dernière visite", "Montant dû"]
        if language == "fr"
        else ["Customer", "Email", "Signups", "Passports", "Amount paid", "Credits", "Visits", "Last visit", "Amount due"]
    )
    return SkillResult(answer=answer, columns=columns, rows=rows[:MAX_ROWS])


SKILLS = [
    SkillDefinition(
        name="customer_summary",
        description_en="Show one customer's signups, passports, spending, credits, visits, last visit, and amount due.",
        description_fr="Afficher les inscriptions, passeports, dépenses, crédits, visites et montant dû d’un client.",
        examples=("Show me everything about Steven Belanger", "Combien Martin a-t-il dépensé?"),
        parameters={"customer": "Required customer name or email"},
        handler=customer_summary,
    )
]
