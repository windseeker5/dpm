"""Trusted survey skills."""

from sqlalchemy import func

from models import Activity, Survey, SurveyResponse, db
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
    return SkillResult(answer=answer, columns=columns, rows=rows_from(records))


SKILLS = [
    SkillDefinition(
        name="survey_summary",
        description_en="Summarize surveys and completed response counts.",
        description_fr="Résumer les sondages et le nombre de réponses complètes.",
        examples=("How many survey responses?", "Résumé des sondages"),
        parameters={"activity": "Optional activity name or part of its name"},
        handler=survey_summary,
    )
]
