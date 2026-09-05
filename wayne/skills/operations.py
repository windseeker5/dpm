"""Trusted day-to-day operational skills for Wayne."""

from datetime import datetime, timedelta

from sqlalchemy import func, text

from models import Activity, ActivitySlot, EmailLog, Expense, Passport, PassportType, Redemption, Signup, SlotBooking, User, db
from wayne.types import SkillDefinition, SkillResult
from .helpers import MAX_ROWS, activity_filter, activity_label, date_bounds, money, period_label, rows_from


def operational_overview(args, language):
    now = datetime.now()
    recent = now - timedelta(days=7)
    pending = Signup.query.filter(Signup.status == "pending").count()
    unpaid = Signup.query.filter(Signup.paid.is_(False), ~Signup.status.in_(("rejected", "cancelled"))).count()
    failed_emails = EmailLog.query.filter(EmailLog.result == "FAILED", EmailLog.timestamp >= recent).count()
    nearly_full = (
        ActivitySlot.query
        .filter(
            ActivitySlot.status == "active",
            ActivitySlot.starts_at >= now,
            ActivitySlot.capacity > 0,
            (ActivitySlot.capacity - ActivitySlot.seats_taken) <= 2,
        )
        .count()
    )
    rows = [
        ["Inscriptions en attente" if language == "fr" else "Pending signups", pending],
        ["Inscriptions non payées" if language == "fr" else "Unpaid signups", unpaid],
        ["Séances presque complètes" if language == "fr" else "Nearly full sessions", nearly_full],
        ["Courriels échoués (7 jours)" if language == "fr" else "Failed emails (7 days)", failed_emails],
    ]
    answer = (
        "Voici les éléments pouvant nécessiter votre attention."
        if language == "fr"
        else "Here are the items that may need your attention."
    )
    columns = ["Élément", "Nombre"] if language == "fr" else ["Item", "Count"]
    return SkillResult(answer=answer, columns=columns, rows=rows)


def outstanding_balances(args, language):
    activity = args.get("activity")
    query = (
        db.session.query(User.name, User.email, Activity.name, Signup.requested_amount, Signup.signed_up_at)
        .join(Signup, Signup.user_id == User.id)
        .join(Activity, Activity.id == Signup.activity_id)
        .filter(Signup.paid.is_(False), ~Signup.status.in_(("rejected", "cancelled")))
    )
    query = activity_filter(query, Activity.name, activity)
    records = query.order_by(Signup.signed_up_at, User.name).limit(MAX_ROWS).all()
    total = sum(float(record[3] or 0) for record in records)
    answer = (
        f"{len(records)} inscription(s) non payée(s) totalisent {money(total)} pour {activity_label(activity, language)}."
        if language == "fr"
        else f"{len(records)} unpaid signup(s) total {money(total)} for {activity_label(activity, language)}."
    )
    columns = (
        ["Participant", "Courriel", "Activité", "Montant dû", "Inscription"]
        if language == "fr"
        else ["Participant", "Email", "Activity", "Amount due", "Signed up"]
    )
    rows = [[r[0], r[1] or "—", r[2], money(r[3]), r[4].strftime("%Y-%m-%d") if r[4] else "—"] for r in records]
    return SkillResult(answer=answer, columns=columns, rows=rows)


def outstanding_expenses(args, language):
    activity = args.get("activity")
    query = (
        db.session.query(Activity.name, Expense.category, Expense.description, Expense.amount, Expense.due_date)
        .join(Activity, Activity.id == Expense.activity_id)
        .filter(Expense.payment_status == "unpaid")
    )
    query = activity_filter(query, Activity.name, activity)
    records = query.order_by(Expense.due_date, Activity.name).limit(MAX_ROWS).all()
    total = sum(float(r[3] or 0) for r in records)
    answer = (
        f"{len(records)} dépense(s) impayée(s) totalisent {money(total)}."
        if language == "fr"
        else f"{len(records)} unpaid expense(s) total {money(total)}."
    )
    columns = (
        ["Activité", "Catégorie", "Description", "Montant", "Échéance"]
        if language == "fr"
        else ["Activity", "Category", "Description", "Amount", "Due date"]
    )
    rows = [[r[0], r[1], r[2] or "—", money(r[3]), r[4]] for r in records]
    return SkillResult(answer=answer, columns=columns, rows=rows_from(rows))


def payment_summary(args, language):
    start, end = date_bounds(args)
    sql = text("""
        SELECT COALESCE(SUM(amount), 0), COUNT(*) FROM (
            SELECT sold_amt AS amount
            FROM passport
            WHERE paid = 1 AND paid_date IS NOT NULL
              AND (marked_paid_by IS NULL OR marked_paid_by NOT LIKE 'stripe%')
              AND (:start IS NULL OR paid_date >= :start)
              AND (:end IS NULL OR paid_date < :end)
            UNION ALL
            SELECT amount
            FROM income
            WHERE payment_status = 'received'
              AND (:start IS NULL OR COALESCE(payment_date, date) >= :start)
              AND (:end IS NULL OR COALESCE(payment_date, date) < :end)
        )
    """)
    amount, count = db.session.execute(sql, {"start": start, "end": end}).first()
    period = period_label(args, language)
    answer = (
        f"{count} paiement(s) reçu(s){period} totalisent {money(amount)}."
        if language == "fr"
        else f"{count} payment(s) received{period} total {money(amount)}."
    )
    columns = ["Paiements", "Montant"] if language == "fr" else ["Payments", "Amount"]
    return SkillResult(answer=answer, columns=columns, rows=[[count, money(amount)]])


def activity_performance(args, language):
    start, end = date_bounds(args)
    start_month = start.strftime("%Y-%m") if start else ""
    end_month = end.strftime("%Y-%m") if end else ""
    records = db.session.execute(text("""
        SELECT account,
               SUM(cash_received) AS revenue,
               SUM(total_expenses) AS expenses,
               SUM(net_income) AS profit
        FROM monthly_financial_summary
        WHERE (:start_month = '' OR month >= :start_month)
          AND (:end_month = '' OR month < :end_month)
        GROUP BY account
        ORDER BY revenue DESC
        LIMIT 200
    """), {"start_month": start_month, "end_month": end_month}).all()
    period = period_label(args, language)
    answer = (
        f"Voici la performance de {len(records)} activité(s){period}."
        if language == "fr"
        else f"Here is the performance of {len(records)} activity/activities{period}."
    )
    columns = (
        ["Activité", "Revenus encaissés", "Dépenses", "Bénéfice net"]
        if language == "fr"
        else ["Activity", "Collected revenue", "Expenses", "Net profit"]
    )
    rows = [[r[0], money(r[1]), money(r[2]), money(r[3])] for r in records]
    return SkillResult(answer=answer, columns=columns, rows=rows)


def activity_registration_summary(args, language):
    start, end = date_bounds(args)
    mode = args.get("mode") or "all"
    sql = text("""
        SELECT a.name,
               COUNT(s.id) AS signups,
               SUM(CASE WHEN s.paid = 1 THEN 1 ELSE 0 END) AS paid,
               SUM(CASE WHEN s.id IS NOT NULL AND s.paid = 0 THEN 1 ELSE 0 END) AS unpaid
        FROM activity a
        LEFT JOIN signup s ON s.activity_id = a.id
          AND (:start IS NULL OR s.signed_up_at >= :start)
          AND (:end IS NULL OR s.signed_up_at < :end)
        GROUP BY a.id, a.name
        HAVING (:mode != 'zero' OR COUNT(s.id) = 0)
        ORDER BY signups DESC, a.name
        LIMIT 200
    """)
    records = db.session.execute(sql, {"start": start, "end": end, "mode": mode}).all()
    if mode == "top":
        records = records[:1]
    period = period_label(args, language)
    if mode == "top" and records:
        answer = (
            f"L’activité avec le plus d’inscriptions{period} est « {records[0][0]} », avec {records[0][1]} inscription(s)."
            if language == "fr"
            else f"The activity with the most signups{period} is “{records[0][0]}” with {records[0][1]} signup(s)."
        )
    elif mode == "zero":
        answer = (
            f"J’ai trouvé {len(records)} activité(s) sans inscription{period}."
            if language == "fr"
            else f"I found {len(records)} activity/activities with no signups{period}."
        )
    else:
        answer = (
            f"Voici les inscriptions de {len(records)} activité(s){period}."
            if language == "fr"
            else f"Here are signup totals for {len(records)} activity/activities{period}."
        )
    columns = (
        ["Activité", "Inscriptions", "Payées", "Non payées"]
        if language == "fr"
        else ["Activity", "Signups", "Paid", "Unpaid"]
    )
    return SkillResult(answer=answer, columns=columns, rows=rows_from(records))


def redemption_summary(args, language):
    activity = args.get("activity")
    start, end = date_bounds(args)
    query = (
        db.session.query(User.name, User.email, Activity.name, Passport.pass_code, Redemption.date_used)
        .join(Passport, Passport.id == Redemption.passport_id)
        .join(User, User.id == Passport.user_id)
        .join(Activity, Activity.id == Passport.activity_id)
    )
    query = activity_filter(query, Activity.name, activity)
    if start:
        query = query.filter(Redemption.date_used >= start)
    if end:
        query = query.filter(Redemption.date_used < end)
    records = query.order_by(Redemption.date_used.desc()).limit(MAX_ROWS).all()
    period = period_label(args, language)
    answer = (
        f"J’ai trouvé {len(records)} utilisation(s) de passeport{period} pour {activity_label(activity, language)}."
        if language == "fr"
        else f"I found {len(records)} passport redemption(s){period} for {activity_label(activity, language)}."
    )
    columns = (
        ["Participant", "Courriel", "Activité", "Passeport", "Utilisation"]
        if language == "fr"
        else ["Participant", "Email", "Activity", "Passport", "Redeemed"]
    )
    return SkillResult(answer=answer, columns=columns, rows=rows_from(records))


def passport_sales_summary(args, language):
    activity = args.get("activity")
    start, end = date_bounds(args)
    query = (
        db.session.query(
            Activity.name,
            func.coalesce(PassportType.name, Passport.passport_type_name, "—"),
            func.count(Passport.id),
            func.coalesce(func.sum(Passport.sold_amt), 0),
        )
        .join(Activity, Activity.id == Passport.activity_id)
        .outerjoin(PassportType, PassportType.id == Passport.passport_type_id)
        .filter(Passport.paid.is_(True))
    )
    query = activity_filter(query, Activity.name, activity)
    if start:
        query = query.filter(Passport.paid_date >= start)
    if end:
        query = query.filter(Passport.paid_date < end)
    records = (
        query.group_by(Activity.name, PassportType.name, Passport.passport_type_name)
        .order_by(func.count(Passport.id).desc())
        .limit(MAX_ROWS)
        .all()
    )
    count = sum(int(r[2] or 0) for r in records)
    amount = sum(float(r[3] or 0) for r in records)
    period = period_label(args, language)
    answer = (
        f"{count} passeport(s) vendu(s){period} totalisent {money(amount)}."
        if language == "fr"
        else f"{count} passport(s) sold{period} total {money(amount)}."
    )
    columns = (
        ["Activité", "Type de passeport", "Vendus", "Montant"]
        if language == "fr"
        else ["Activity", "Passport type", "Sold", "Amount"]
    )
    rows = [[r[0], r[1], r[2], money(r[3])] for r in records]
    return SkillResult(answer=answer, columns=columns, rows=rows)


def low_credit_passports(args, language):
    activity = args.get("activity")
    threshold = int(args.get("threshold") or 1)
    threshold = min(10, max(1, threshold))
    query = (
        db.session.query(User.name, User.email, Activity.name, Passport.pass_code, Passport.uses_remaining)
        .join(User, User.id == Passport.user_id)
        .join(Activity, Activity.id == Passport.activity_id)
        .filter(Passport.paid.is_(True), Passport.uses_remaining.between(1, threshold))
    )
    query = activity_filter(query, Activity.name, activity)
    records = query.order_by(Passport.uses_remaining, User.name).limit(MAX_ROWS).all()
    answer = (
        f"J’ai trouvé {len(records)} passeport(s) avec {threshold} crédit(s) ou moins."
        if language == "fr"
        else f"I found {len(records)} passport(s) with {threshold} credit(s) or fewer."
    )
    columns = (
        ["Participant", "Courriel", "Activité", "Passeport", "Crédits restants"]
        if language == "fr"
        else ["Participant", "Email", "Activity", "Passport", "Credits left"]
    )
    return SkillResult(answer=answer, columns=columns, rows=rows_from(records))


def unused_passports(args, language):
    activity = args.get("activity")
    query = (
        db.session.query(User.name, User.email, Activity.name, Passport.pass_code, Passport.uses_remaining)
        .join(User, User.id == Passport.user_id)
        .join(Activity, Activity.id == Passport.activity_id)
        .outerjoin(Redemption, Redemption.passport_id == Passport.id)
        .filter(Passport.paid.is_(True), Redemption.id.is_(None))
    )
    query = activity_filter(query, Activity.name, activity)
    records = query.order_by(Activity.name, User.name).limit(MAX_ROWS).all()
    answer = (
        f"J’ai trouvé {len(records)} passeport(s) qui n’ont jamais été utilisés."
        if language == "fr"
        else f"I found {len(records)} passport(s) that have never been used."
    )
    columns = (
        ["Participant", "Courriel", "Activité", "Passeport", "Crédits restants"]
        if language == "fr"
        else ["Participant", "Email", "Activity", "Passport", "Credits left"]
    )
    return SkillResult(answer=answer, columns=columns, rows=rows_from(records))


def session_no_shows(args, language):
    activity = args.get("activity")
    query = (
        db.session.query(User.name, User.email, Activity.name, ActivitySlot.starts_at)
        .join(SlotBooking, SlotBooking.user_id == User.id)
        .join(ActivitySlot, ActivitySlot.id == SlotBooking.slot_id)
        .join(Activity, Activity.id == SlotBooking.activity_id)
        .filter(
            SlotBooking.status == "confirmed",
            SlotBooking.attended_dt.is_(None),
            ActivitySlot.starts_at < datetime.now(),
        )
    )
    query = activity_filter(query, Activity.name, activity)
    records = query.order_by(ActivitySlot.starts_at.desc(), User.name).limit(MAX_ROWS).all()
    answer = (
        f"J’ai trouvé {len(records)} absence(s) parmi les réservations confirmées passées."
        if language == "fr"
        else f"I found {len(records)} no-show(s) among past confirmed bookings."
    )
    columns = (
        ["Participant", "Courriel", "Activité", "Séance"]
        if language == "fr"
        else ["Participant", "Email", "Activity", "Session"]
    )
    return SkillResult(answer=answer, columns=columns, rows=rows_from(records))


SKILLS = [
    SkillDefinition(
        name="operational_overview",
        description_en="Show pending signups, unpaid signups, nearly full sessions, and recent failed emails needing attention.",
        description_fr="Afficher les inscriptions en attente ou impayées, séances presque complètes et échecs de courriel récents.",
        examples=("What needs my attention today?", "Qu’est-ce qui nécessite mon attention aujourd’hui?"),
        parameters={}, handler=operational_overview,
    ),
    SkillDefinition(
        name="outstanding_balances",
        description_en="List unpaid signup balances with participant, activity and amount due.",
        description_fr="Lister les soldes d’inscription impayés avec participant, activité et montant dû.",
        examples=("How much do customers owe me?", "Qui me doit encore de l’argent?"),
        parameters={"activity": "Optional activity name"}, handler=outstanding_balances,
    ),
    SkillDefinition(
        name="outstanding_expenses",
        description_en="List unpaid expenses and their total amount due.",
        description_fr="Lister les dépenses impayées et leur montant total dû.",
        examples=("How much do I still owe in expenses?", "Quelles dépenses dois-je encore payer?"),
        parameters={"activity": "Optional activity name"}, handler=outstanding_expenses,
    ),
    SkillDefinition(
        name="payment_summary",
        description_en="Count and total payments received for today, this week, month, year, or a calendar year.",
        description_fr="Compter et totaliser les paiements reçus aujourd’hui, cette semaine, ce mois ou cette année.",
        examples=("Did anyone pay today?", "Combien ai-je reçu ce mois-ci?"),
        parameters={"period": "today, this_week, this_month, or this_year", "year": "Optional calendar year"},
        handler=payment_summary,
    ),
    SkillDefinition(
        name="activity_performance",
        description_en="Compare activities by collected revenue, expenses, and net profit.",
        description_fr="Comparer les activités selon les revenus encaissés, dépenses et bénéfice net.",
        examples=("Compare my activities", "Compare la performance de mes activités en 2026"),
        parameters={"year": "Optional calendar year"}, handler=activity_performance,
    ),
    SkillDefinition(
        name="activity_registration_summary",
        description_en="Compare activities by paid, unpaid, or total signups; find the most popular or activities with none.",
        description_fr="Comparer les activités par inscriptions payées, impayées ou totales; trouver la plus populaire ou celles sans inscription.",
        examples=("Which activity has the most registrations?", "Which activities have no registrations?"),
        parameters={"mode": "all, top, or zero", "period": "Optional common period", "year": "Optional year"},
        handler=activity_registration_summary,
    ),
    SkillDefinition(
        name="redemption_summary",
        description_en="List and count passport redemptions for an activity, period, or year.",
        description_fr="Lister et compter les utilisations de passeport par activité, période ou année.",
        examples=("How many credits were redeemed this week?", "Combien de présences ce mois-ci?"),
        parameters={"activity": "Optional activity name", "period": "Optional common period", "year": "Optional year"},
        handler=redemption_summary,
    ),
    SkillDefinition(
        name="passport_sales_summary",
        description_en="Summarize paid passport sales by activity and passport type for a period or year.",
        description_fr="Résumer les ventes de passeports payés par activité et type pour une période ou année.",
        examples=("How many passports did I sell this month?", "Quel type de passeport se vend le plus?"),
        parameters={"activity": "Optional activity name", "period": "Optional common period", "year": "Optional year"},
        handler=passport_sales_summary,
    ),
    SkillDefinition(
        name="low_credit_passports",
        description_en="List paid passports with only a small number of credits remaining.",
        description_fr="Lister les passeports payés auxquels il reste peu de crédits.",
        examples=("Who has one credit left?", "Quels passeports manquent de crédits?"),
        parameters={"activity": "Optional activity name", "threshold": "Maximum credits remaining; defaults to 1"},
        handler=low_credit_passports,
    ),
    SkillDefinition(
        name="unused_passports",
        description_en="List paid passports that have never recorded a redemption.",
        description_fr="Lister les passeports payés qui n’ont jamais été utilisés.",
        examples=("Which passports have never been used?", "Quels passeports n’ont jamais servi?"),
        parameters={"activity": "Optional activity name"}, handler=unused_passports,
    ),
    SkillDefinition(
        name="session_no_shows",
        description_en="List confirmed bookings for past sessions without a recorded check-in.",
        description_fr="Lister les réservations confirmées de séances passées sans présence enregistrée.",
        examples=("Who did not show up?", "Qui ne s’est pas présenté?"),
        parameters={"activity": "Optional activity name"}, handler=session_no_shows,
    ),
]
