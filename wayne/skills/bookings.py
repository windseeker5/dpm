"""Trusted session booking and attendance skills."""

from datetime import datetime

from models import Activity, ActivitySlot, SlotBooking, User, db
from wayne.types import SkillDefinition, SkillResult
from .helpers import MAX_ROWS, activity_filter, activity_label, date_bounds, period_label, rows_from


def available_session_seats(args, language):
    activity = args.get("activity")
    query = (
        db.session.query(
            Activity.name,
            ActivitySlot.label,
            ActivitySlot.starts_at,
            ActivitySlot.capacity,
            ActivitySlot.seats_taken,
            (ActivitySlot.capacity - ActivitySlot.seats_taken).label("seats_left"),
        )
        .join(Activity, Activity.id == ActivitySlot.activity_id)
        .filter(ActivitySlot.status == "active", ActivitySlot.starts_at >= datetime.now())
    )
    query = activity_filter(query, Activity.name, activity)
    mode = args.get("mode")
    if mode == "full":
        query = query.filter(ActivitySlot.seats_taken >= ActivitySlot.capacity)
    elif mode == "nearly_full":
        query = query.filter(
            ActivitySlot.seats_taken < ActivitySlot.capacity,
            (ActivitySlot.capacity - ActivitySlot.seats_taken) <= 2,
        )
    records = query.order_by(ActivitySlot.starts_at).limit(MAX_ROWS).all()
    answer = (
        f"J’ai trouvé {len(records)} séance(s) à venir pour {activity_label(activity, language)}."
        if language == "fr"
        else f"I found {len(records)} upcoming session(s) for {activity_label(activity, language)}."
    )
    columns = (
        ["Activité", "Séance", "Date", "Capacité", "Réservées", "Places libres"]
        if language == "fr"
        else ["Activity", "Session", "Date", "Capacity", "Booked", "Seats left"]
    )
    return SkillResult(answer=answer, columns=columns, rows=rows_from(records))


def session_attendance(args, language):
    activity = args.get("activity")
    query = (
        db.session.query(User.name, User.email, Activity.name, ActivitySlot.starts_at, SlotBooking.attended_dt)
        .join(SlotBooking, SlotBooking.user_id == User.id)
        .join(ActivitySlot, ActivitySlot.id == SlotBooking.slot_id)
        .join(Activity, Activity.id == SlotBooking.activity_id)
        .filter(SlotBooking.attended_dt.isnot(None))
    )
    query = activity_filter(query, Activity.name, activity)
    start, end = date_bounds(args)
    if start:
        query = query.filter(SlotBooking.attended_dt >= start)
    if end:
        query = query.filter(SlotBooking.attended_dt < end)
    records = query.order_by(ActivitySlot.starts_at.desc(), User.name).limit(MAX_ROWS).all()
    period = period_label(args, language)
    answer = (
        f"J’ai trouvé {len(records)} présence(s) enregistrée(s){period} pour {activity_label(activity, language)}."
        if language == "fr"
        else f"I found {len(records)} recorded attendance entries{period} for {activity_label(activity, language)}."
    )
    columns = (
        ["Participant", "Courriel", "Activité", "Séance", "Présence enregistrée"]
        if language == "fr"
        else ["Participant", "Email", "Activity", "Session", "Attendance recorded"]
    )
    return SkillResult(answer=answer, columns=columns, rows=rows_from(records))


SKILLS = [
    SkillDefinition(
        name="available_session_seats",
        description_en="List upcoming scheduled sessions with capacity, bookings and seats left.",
        description_fr="Lister les séances à venir avec capacité, réservations et places libres.",
        examples=("Which sessions have space?", "Combien de places restent pour le yoga?"),
        parameters={"activity": "Optional activity name", "mode": "Optional: full or nearly_full"},
        handler=available_session_seats,
    ),
    SkillDefinition(
        name="session_attendance",
        description_en="List recorded attendance for scheduled sessions.",
        description_fr="Lister les présences enregistrées aux séances planifiées.",
        examples=("Who attended?", "Liste des présences au hockey"),
        parameters={"activity": "Optional activity name", "period": "Optional common period", "year": "Optional year"},
        handler=session_attendance,
    ),
]
