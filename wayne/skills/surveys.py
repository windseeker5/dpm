"""Trusted survey skills."""

from sqlalchemy import func

from models import Activity, Survey, SurveyResponse, User, db
from wayne.types import SkillDefinition, SkillResult
from .helpers import MAX_ROWS, activity_filter, rows_from


def survey_summary(args, language):
    activity = args.get("activity")
    query = (
        db.session.query(
            Survey.name,
            Activity.name,
            Survey.status,
            func.count(SurveyResponse.id),
            func.sum(func.cast(SurveyResponse.completed, db.Integer)),
        )
        .join(Activity, Activity.id == Survey.activity_id)
        .outerjoin(SurveyResponse, SurveyResponse.survey_id == Survey.id)
    )
    query = activity_filter(query, Activity.name, activity)
    records = query.group_by(Survey.id).order_by(Survey.created_dt.desc()).limit(MAX_ROWS).all()
    answer = (
        f"J’ai trouvé {len(records)} sondage(s)."
        if language == "fr"
        else f"I found {len(records)} survey(s)."
    )
    columns = (
        ["Sondage", "Activité", "Statut", "Invitations", "Réponses complètes"]
        if language == "fr"
        else ["Survey", "Activity", "Status", "Invitations", "Completed responses"]
    )
    rows = []
    for record in records:
        invitations = int(record[3] or 0)
        completed = int(record[4] or 0)
        rate = f"{(completed / invitations * 100):.1f}%" if invitations else "0.0%"
        rows.append([record[0], record[1], record[2], invitations, completed, rate])
    columns.append("Taux de réponse" if language == "fr" else "Response rate")
    return SkillResult(answer=answer, columns=columns, rows=rows)


def pending_survey_responses(args, language):
    activity = args.get("activity")
    query = (
        db.session.query(User.name, User.email, Survey.name, Activity.name, SurveyResponse.invited_dt)
        .join(SurveyResponse, SurveyResponse.user_id == User.id)
        .join(Survey, Survey.id == SurveyResponse.survey_id)
        .join(Activity, Activity.id == Survey.activity_id)
        .filter(SurveyResponse.completed.is_(False))
    )
    query = activity_filter(query, Activity.name, activity)
    records = query.order_by(SurveyResponse.invited_dt.desc(), User.name).limit(MAX_ROWS).all()
    answer = (
        f"J’ai trouvé {len(records)} invitation(s) de sondage sans réponse complète."
        if language == "fr"
        else f"I found {len(records)} survey invitation(s) without a completed response."
    )
    columns = (
        ["Participant", "Courriel", "Sondage", "Activité", "Invitation"]
        if language == "fr"
        else ["Participant", "Email", "Survey", "Activity", "Invited"]
    )
    return SkillResult(answer=answer, columns=columns, rows=rows_from(records))


SKILLS = [
    SkillDefinition(
        name="survey_summary",
        description_en="Summarize surveys and completed response counts.",
        description_fr="Résumer les sondages et le nombre de réponses complètes.",
        examples=("How many survey responses?", "Résumé des sondages"),
        parameters={"activity": "Optional activity name or part of its name"},
        handler=survey_summary,
    ),
    SkillDefinition(
        name="pending_survey_responses",
        description_en="List invited participants who have not completed a survey.",
        description_fr="Lister les participants invités qui n’ont pas terminé un sondage.",
        examples=("Who has not answered the survey?", "Qui n’a pas encore répondu au sondage?"),
        parameters={"activity": "Optional activity name or part of its name"},
        handler=pending_survey_responses,
    ),
]
