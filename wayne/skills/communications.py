"""Trusted email and reminder reporting skills for Wayne."""

from sqlalchemy import func, or_

from models import Activity, EmailLog, Passport, ReminderLog, User, db
from wayne.types import SkillDefinition, SkillResult
from .helpers import MAX_ROWS, date_bounds, period_label, rows_from


def email_delivery_summary(args, language):
    start, end = date_bounds(args)
    customer = (args.get("customer") or "").strip()
    query = EmailLog.query
    if start:
        query = query.filter(EmailLog.timestamp >= start)
    if end:
        query = query.filter(EmailLog.timestamp < end)
    if customer:
        matching_emails = [
            row[0] for row in
            db.session.query(User.email)
            .filter(or_(func.lower(User.name).contains(customer.lower()), func.lower(User.email).contains(customer.lower())))
            .all()
            if row[0]
        ]
        if matching_emails:
            query = query.filter(EmailLog.to_email.in_(matching_emails))
        else:
            query = query.filter(func.lower(EmailLog.to_email).contains(customer.lower()))

    sent = query.filter(func.upper(EmailLog.result) == "SENT").count()
    failed = query.filter(func.upper(EmailLog.result) == "FAILED").count()
    period = period_label(args, language)
    qualifier = f" pour {customer}" if language == "fr" and customer else f" for {customer}" if customer else ""
    answer = (
        f"{sent} courriel(s) envoyé(s) et {failed} échec(s){period}{qualifier}. Un statut envoyé ne confirme pas l’ouverture du courriel."
        if language == "fr"
        else f"{sent} email(s) sent and {failed} failed{period}{qualifier}. Sent status does not confirm that the email was opened."
    )
    failures = (
        query.filter(func.upper(EmailLog.result) == "FAILED")
        .order_by(EmailLog.timestamp.desc())
        .limit(MAX_ROWS)
        .all()
    )
    columns = (
        ["Courriel", "Sujet", "Modèle", "Date", "Erreur"]
        if language == "fr"
        else ["Email", "Subject", "Template", "Date", "Error"]
    )
    rows = [[r.to_email, r.subject, r.template_name or "—", r.timestamp, r.error_message or "—"] for r in failures]
    return SkillResult(answer=answer, columns=columns, rows=rows_from(rows))


def reminder_summary(args, language):
    start, end = date_bounds(args)
    query = (
        db.session.query(User.name, User.email, Activity.name, Passport.pass_code, ReminderLog.reminder_sent_at)
        .join(Passport, Passport.id == ReminderLog.passport_id)
        .join(User, User.id == Passport.user_id)
        .join(Activity, Activity.id == Passport.activity_id)
    )
    if start:
        query = query.filter(ReminderLog.reminder_sent_at >= start)
    if end:
        query = query.filter(ReminderLog.reminder_sent_at < end)
    records = query.order_by(ReminderLog.reminder_sent_at.desc()).limit(MAX_ROWS).all()
    period = period_label(args, language)
    answer = (
        f"{len(records)} rappel(s) de paiement ont été envoyés{period}."
        if language == "fr"
        else f"{len(records)} payment reminder(s) were sent{period}."
    )
    columns = (
        ["Client", "Courriel", "Activité", "Passeport", "Rappel envoyé"]
        if language == "fr"
        else ["Customer", "Email", "Activity", "Passport", "Reminder sent"]
    )
    return SkillResult(answer=answer, columns=columns, rows=rows_from(records))


SKILLS = [
    SkillDefinition(
        name="email_delivery_summary",
        description_en="Count sent and failed emails, optionally for a period, year, or customer; list failures.",
        description_fr="Compter les courriels envoyés et échoués par période, année ou client; lister les échecs.",
        examples=("Did any emails fail?", "How many emails did I send this year?", "Le courriel de Martin a-t-il été envoyé?"),
        parameters={"period": "today, this_week, this_month, or this_year", "year": "Optional year", "customer": "Optional customer name or email"},
        handler=email_delivery_summary,
    ),
    SkillDefinition(
        name="reminder_summary",
        description_en="List payment reminders sent for a period or year.",
        description_fr="Lister les rappels de paiement envoyés pour une période ou une année.",
        examples=("Who received a payment reminder?", "Combien de rappels ai-je envoyés ce mois-ci?"),
        parameters={"period": "today, this_week, this_month, or this_year", "year": "Optional year"},
        handler=reminder_summary,
    ),
]
