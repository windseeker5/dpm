"""Trusted passport skills."""

from sqlalchemy import func

from models import Activity, Passport, User, db
from wayne.types import SkillDefinition, SkillResult
from .helpers import MAX_ROWS, activity_filter, activity_label, money, rows_from


def count_passports(args, language):
    activity = args.get("activity")
    query = db.session.query(func.count(Passport.id)).join(Activity, Activity.id == Passport.activity_id)
    query = activity_filter(query, Activity.name, activity)
    count = query.scalar() or 0
    label = activity_label(activity, language)
    answer = (
        f"Il y a {count} passeport(s) pour {label}."
        if language == "fr"
        else f"There are {count} passport(s) for {label}."
    )
    return SkillResult(answer=answer)


def _passport_list(args, language, active):
    activity = args.get("activity")
    query = (
        db.session.query(
            User.name,
            User.email,
            Activity.name,
            Passport.pass_code,
            Passport.uses_remaining,
            Passport.sold_amt,
            Passport.paid,
        )
        .join(User, User.id == Passport.user_id)
        .join(Activity, Activity.id == Passport.activity_id)
        .filter(Passport.paid.is_(True))
    )
    query = query.filter(Passport.uses_remaining > 0) if active else query.filter(Passport.uses_remaining <= 0)
    query = activity_filter(query, Activity.name, activity)
    records = query.order_by(Activity.name, User.name).limit(MAX_ROWS).all()
    rows = [[r[0], r[1] or "—", r[2], r[3], r[4], money(r[5]), "Oui" if language == "fr" else "Yes"] for r in records]
    label = activity_label(activity, language)
    state = ("actifs" if active else "épuisés") if language == "fr" else ("active" if active else "exhausted")
    answer = (
        f"J’ai trouvé {len(records)} passeport(s) {state} pour {label}."
        if language == "fr"
        else f"I found {len(records)} {state} passport(s) for {label}."
    )
    columns = (
        ["Participant", "Courriel", "Activité", "Passeport", "Crédits restants", "Montant", "Payé"]
        if language == "fr"
        else ["Participant", "Email", "Activity", "Passport", "Credits left", "Amount", "Paid"]
    )
    return SkillResult(answer=answer, columns=columns, rows=rows)


def list_active_passports(args, language):
    return _passport_list(args, language, True)


def list_exhausted_passports(args, language):
    return _passport_list(args, language, False)


SKILLS = [
    SkillDefinition(
        name="count_passports",
        description_en="Count passports, optionally for an activity.",
        description_fr="Compter les passeports, avec activité facultative.",
        examples=("How many passports?", "Combien de passeports pour le hockey?"),
        parameters={"activity": "Optional activity name or part of its name"},
        handler=count_passports,
    ),
    SkillDefinition(
        name="list_active_passports",
        description_en="List paid passports that still have credits remaining.",
        description_fr="Lister les passeports payés qui ont encore des crédits.",
        examples=("Show active passports", "Quels passeports ont encore des crédits?"),
        parameters={"activity": "Optional activity name or part of its name"},
        handler=list_active_passports,
    ),
    SkillDefinition(
        name="list_exhausted_passports",
        description_en="List paid passports with no remaining credits. Use for exhausted/used-up passes, not date expiration.",
        description_fr="Lister les passeports payés sans crédit restant.",
        examples=("Show exhausted passports", "Passeports sans crédit"),
        parameters={"activity": "Optional activity name or part of its name"},
        handler=list_exhausted_passports,
    ),
]
