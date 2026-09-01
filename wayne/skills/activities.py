"""Trusted activity summary skills."""

from sqlalchemy import func

from models import Activity, Passport, Signup, db
from wayne.types import SkillDefinition, SkillResult
from .helpers import MAX_ROWS, rows_from


def list_activities(args, language):
    requested_status = (args.get("status") or "active").lower()
    if requested_status not in {"active", "archived"}:
        requested_status = "active"
    records = (
        db.session.query(
            Activity.name,
            Activity.type,
            Activity.start_date,
            Activity.end_date,
            Activity.status,
            func.count(func.distinct(Signup.id)),
            func.count(func.distinct(Passport.id)),
        )
        .outerjoin(Signup, Signup.activity_id == Activity.id)
        .outerjoin(Passport, Passport.activity_id == Activity.id)
        .filter(Activity.status == requested_status)
        .group_by(Activity.id)
        .order_by(Activity.start_date.desc(), Activity.name)
        .limit(MAX_ROWS)
        .all()
    )
    answer = (
        f"J’ai trouvé {len(records)} activité(s) {('actives' if requested_status == 'active' else 'archivées')}."
        if language == "fr"
        else f"I found {len(records)} {requested_status} activity/activities."
    )
    columns = (
        ["Activité", "Type", "Début", "Fin", "Statut", "Inscriptions", "Passeports"]
        if language == "fr"
        else ["Activity", "Type", "Start", "End", "Status", "Signups", "Passports"]
    )
    return SkillResult(answer=answer, columns=columns, rows=rows_from(records))


SKILLS = [
    SkillDefinition(
        name="list_activities",
        description_en="List active or archived activities with signup and passport counts.",
        description_fr="Lister les activités actives ou archivées avec leurs totaux.",
        examples=("Show active activities", "Quelles activités sont archivées?"),
        parameters={"status": "Optional: active or archived; defaults to active"},
        handler=list_activities,
    )
]
