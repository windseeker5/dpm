"""Trusted participant and signup skills.

To change one of these skills, edit its handler and the matching metadata in
SKILLS at the bottom of this file. Wayne never creates SQL for these queries.
"""

from sqlalchemy import func

from models import Activity, Signup, User, db
from wayne.types import SkillDefinition, SkillResult
from .helpers import MAX_ROWS, activity_filter, activity_label, rows_from


def count_participants(args, language):
    activity = args.get("activity")
    query = db.session.query(func.count(func.distinct(User.id))).select_from(User)
    if activity:
        query = query.join(Signup, Signup.user_id == User.id).join(Activity, Activity.id == Signup.activity_id)
        query = activity_filter(query, Activity.name, activity)
    count = query.scalar() or 0
    label = activity_label(activity, language)
    answer = (
        f"{count} participant(s) sont enregistrés pour {label}."
        if language == "fr"
        else f"{count} participant(s) are registered for {label}."
    )
    return SkillResult(answer=answer)


def count_signups(args, language):
    activity = args.get("activity")
    query = db.session.query(func.count(Signup.id)).join(Activity, Activity.id == Signup.activity_id)
    query = activity_filter(query, Activity.name, activity)
    count = query.scalar() or 0
    label = activity_label(activity, language)
    answer = (
        f"Il y a {count} inscription(s) pour {label}."
        if language == "fr"
        else f"There are {count} signup(s) for {label}."
    )
    return SkillResult(answer=answer)


def _list_by_payment(args, language, paid):
    activity = args.get("activity")
    query = (
        db.session.query(User.name, User.email, User.phone_number, Activity.name, Signup.status)
        .join(Signup, Signup.user_id == User.id)
        .join(Activity, Activity.id == Signup.activity_id)
        .filter(Signup.paid.is_(paid))
    )
    query = activity_filter(query, Activity.name, activity)
    records = query.order_by(Activity.name, User.name).limit(MAX_ROWS).all()
    label = activity_label(activity, language)
    payment_word = ("payées" if paid else "non payées") if language == "fr" else ("paid" if paid else "unpaid")
    answer = (
        f"J’ai trouvé {len(records)} inscription(s) {payment_word} pour {label}."
        if language == "fr"
        else f"I found {len(records)} {payment_word} signup(s) for {label}."
    )
    columns = (
        ["Participant", "Courriel", "Téléphone", "Activité", "Statut"]
        if language == "fr"
        else ["Participant", "Email", "Phone", "Activity", "Status"]
    )
    return SkillResult(answer=answer, columns=columns, rows=rows_from(records))


def list_unpaid_participants(args, language):
    return _list_by_payment(args, language, False)


def list_paid_participants(args, language):
    return _list_by_payment(args, language, True)


SKILLS = [
    SkillDefinition(
        name="count_participants",
        description_en="Count distinct people/participants, optionally for an activity.",
        description_fr="Compter les personnes ou participants, avec activité facultative.",
        examples=("How many participants?", "Combien de personnes sont inscrites au yoga?"),
        parameters={"activity": "Optional activity name or part of its name"},
        handler=count_participants,
    ),
    SkillDefinition(
        name="count_signups",
        description_en="Count signup or registration records, optionally for an activity.",
        description_fr="Compter les inscriptions, avec activité facultative.",
        examples=("How many signups?", "Combien d'inscriptions pour le hockey?"),
        parameters={"activity": "Optional activity name or part of its name"},
        handler=count_signups,
    ),
    SkillDefinition(
        name="list_unpaid_participants",
        description_en="List people whose signup is not paid, optionally for an activity.",
        description_fr="Lister les personnes dont l'inscription n'est pas payée.",
        examples=("Who has not paid for hockey?", "Liste des inscriptions non payées pour le yoga"),
        parameters={"activity": "Optional activity name or part of its name"},
        handler=list_unpaid_participants,
    ),
    SkillDefinition(
        name="list_paid_participants",
        description_en="List people whose signup is paid, optionally for an activity.",
        description_fr="Lister les personnes dont l'inscription est payée.",
        examples=("Who paid for golf?", "Liste des participants payés"),
        parameters={"activity": "Optional activity name or part of its name"},
        handler=list_paid_participants,
    ),
]
