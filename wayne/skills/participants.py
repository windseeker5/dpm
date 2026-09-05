"""Trusted participant and signup skills.

To change one of these skills, edit its handler and the matching metadata in
SKILLS at the bottom of this file. Wayne never creates SQL for these queries.
"""

from sqlalchemy import func

from models import Activity, Signup, User, db
from wayne.types import SkillDefinition, SkillResult
from .helpers import MAX_ROWS, activity_filter, activity_label, date_bounds, period_label, rows_from


def count_participants(args, language):
    activity = args.get("activity")
    query = db.session.query(func.count(func.distinct(User.id))).select_from(User)
    start, end = date_bounds(args)
    if activity or start:
        query = query.join(Signup, Signup.user_id == User.id).join(Activity, Activity.id == Signup.activity_id)
        query = activity_filter(query, Activity.name, activity)
    if start:
        query = query.filter(Signup.signed_up_at >= start)
    if end:
        query = query.filter(Signup.signed_up_at < end)
    count = query.scalar() or 0
    label = activity_label(activity, language)
    period = period_label(args, language)
    answer = (
        f"{count} participant(s) se sont inscrits{period} pour {label}."
        if language == "fr" and period
        else f"{count} participant(s) sont enregistrés pour {label}."
        if language == "fr"
        else f"{count} participant(s) registered{period} for {label}."
        if period
        else f"{count} participant(s) are registered for {label}."
    )
    return SkillResult(answer=answer)


def count_signups(args, language):
    activity = args.get("activity")
    query = db.session.query(func.count(Signup.id)).join(Activity, Activity.id == Signup.activity_id)
    query = activity_filter(query, Activity.name, activity)
    start, end = date_bounds(args)
    if start:
        query = query.filter(Signup.signed_up_at >= start)
    if end:
        query = query.filter(Signup.signed_up_at < end)
    count = query.scalar() or 0
    label = activity_label(activity, language)
    period = period_label(args, language)
    answer = (
        f"Il y a {count} inscription(s){period} pour {label}."
        if language == "fr"
        else f"There are {count} signup(s){period} for {label}."
    )
    return SkillResult(answer=answer)


def list_signups(args, language):
    activity = args.get("activity")
    status = args.get("status")
    query = (
        db.session.query(User.name, User.email, Activity.name, Signup.status, Signup.paid, Signup.signed_up_at)
        .join(Signup, Signup.user_id == User.id)
        .join(Activity, Activity.id == Signup.activity_id)
    )
    query = activity_filter(query, Activity.name, activity)
    if status:
        query = query.filter(Signup.status == status)
    start, end = date_bounds(args)
    if start:
        query = query.filter(Signup.signed_up_at >= start)
    if end:
        query = query.filter(Signup.signed_up_at < end)
    records = query.order_by(Signup.signed_up_at.desc(), User.name).limit(MAX_ROWS).all()
    period = period_label(args, language)
    answer = (
        f"J’ai trouvé {len(records)} inscription(s){period}."
        if language == "fr"
        else f"I found {len(records)} signup(s){period}."
    )
    columns = (
        ["Participant", "Courriel", "Activité", "Statut", "Payée", "Inscription"]
        if language == "fr"
        else ["Participant", "Email", "Activity", "Status", "Paid", "Signed up"]
    )
    rows = [[r[0], r[1] or "—", r[2], r[3], "Oui" if r[4] and language == "fr" else "Yes" if r[4] else "Non" if language == "fr" else "No", r[5]] for r in records]
    return SkillResult(answer=answer, columns=columns, rows=rows_from(rows))


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
        parameters={"activity": "Optional activity name", "period": "Optional common period", "year": "Optional year"},
        handler=count_participants,
    ),
    SkillDefinition(
        name="count_signups",
        description_en="Count signup or registration records, optionally for an activity.",
        description_fr="Compter les inscriptions, avec activité facultative.",
        examples=("How many signups?", "Combien d'inscriptions pour le hockey?"),
        parameters={"activity": "Optional activity name", "period": "Optional common period", "year": "Optional year"},
        handler=count_signups,
    ),
    SkillDefinition(
        name="list_signups",
        description_en="List signup records, optionally filtered by activity, status, period, or year.",
        description_fr="Lister les inscriptions par activité, statut, période ou année.",
        examples=("Who registered this week?", "Liste les nouvelles inscriptions aujourd’hui"),
        parameters={"activity": "Optional activity name", "status": "Optional signup status", "period": "Optional common period", "year": "Optional year"},
        handler=list_signups,
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
