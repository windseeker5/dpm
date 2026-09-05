"""Trusted financial skills using the application's approved accounting views."""

from sqlalchemy import text

from models import db
from wayne.types import SkillDefinition, SkillResult
from .helpers import money


def activity_revenue(args, language):
    activity = (args.get("activity") or "").strip().lower()
    year = args.get("year")
    try:
        year = int(year) if year is not None else None
    except (TypeError, ValueError):
        year = None
    if year is not None and not 1900 <= year <= 2100:
        year = None

    sql = text("""
        SELECT account, COALESCE(SUM(cash_received), 0) AS revenue
        FROM monthly_financial_summary
        WHERE (:activity = '' OR LOWER(account) LIKE '%' || :activity || '%')
          AND (:year_prefix = '' OR month LIKE :year_prefix)
        GROUP BY account
        ORDER BY revenue DESC
        LIMIT 200
    """)
    records = db.session.execute(
        sql,
        {"activity": activity, "year_prefix": f"{year}-%" if year else ""},
    ).all()
    total = sum(float(row[1] or 0) for row in records)
    period = f" en {year}" if language == "fr" and year else f" in {year}" if year else ""
    answer = (
        f"Les revenus encaissés{period} totalisent {money(total)} pour {len(records)} activité(s)."
        if language == "fr"
        else f"Cash revenue{period} totals {money(total)} across {len(records)} activity/activities."
    )
    columns = ["Activité", "Revenus encaissés"] if language == "fr" else ["Activity", "Cash revenue"]
    rows = [[row[0], money(row[1])] for row in records]
    return SkillResult(answer=answer, columns=columns, rows=rows)


def _top_activity(args, language, metric):
    year = args.get("year")
    try:
        year = int(year) if year is not None else None
    except (TypeError, ValueError):
        year = None
    if year is not None and not 1900 <= year <= 2100:
        year = None

    metric_column = "cash_received" if metric == "cash_revenue" else "net_income"
    sql = text(f"""
        SELECT account, COALESCE(SUM({metric_column}), 0) AS amount
        FROM monthly_financial_summary
        WHERE (:year_prefix = '' OR month LIKE :year_prefix)
        GROUP BY account
        ORDER BY amount DESC, account
        LIMIT 1
    """)
    record = db.session.execute(
        sql,
        {"year_prefix": f"{year}-%" if year else ""},
    ).first()
    period = f" en {year}" if language == "fr" and year else f" in {year}" if year else ""

    if not record:
        answer = (
            f"Aucune donnée financière n’est disponible{period}."
            if language == "fr"
            else f"No financial data is available{period}."
        )
        return SkillResult(answer=answer)

    activity, amount = record
    if metric == "cash_revenue":
        answer = (
            f"L’activité ayant généré le plus de revenus encaissés{period} est « {activity} », avec {money(amount)}."
            if language == "fr"
            else f"The activity with the highest collected revenue{period} is “{activity}” with {money(amount)}."
        )
        columns = ["Activité", "Revenus encaissés"] if language == "fr" else ["Activity", "Collected revenue"]
    else:
        answer = (
            f"L’activité la plus profitable{period} est « {activity} », avec un bénéfice net de {money(amount)}."
            if language == "fr"
            else f"The most profitable activity{period} is “{activity}” with net profit of {money(amount)}."
        )
        columns = ["Activité", "Bénéfice net"] if language == "fr" else ["Activity", "Net profit"]
    return SkillResult(answer=answer, columns=columns, rows=[[activity, money(amount)]])


def highest_revenue_activity(args, language):
    return _top_activity(args, language, "cash_revenue")


def most_profitable_activity(args, language):
    return _top_activity(args, language, "net_profit")


def financial_summary(args, language):
    records = db.session.execute(text("""
        SELECT month,
               SUM(cash_received) AS cash_received,
               SUM(cash_paid) AS cash_paid,
               SUM(net_cash_flow) AS net_cash_flow,
               SUM(accounts_receivable) AS accounts_receivable,
               SUM(accounts_payable) AS accounts_payable
        FROM monthly_financial_summary
        GROUP BY month
        ORDER BY month DESC
        LIMIT 12
    """)).all()
    if records:
        latest = records[0]
        answer = (
            f"Pour {latest[0]}, le flux de trésorerie net est de {money(latest[3])}."
            if language == "fr"
            else f"For {latest[0]}, net cash flow is {money(latest[3])}."
        )
    else:
        answer = "Aucune donnée financière n’est disponible." if language == "fr" else "No financial data is available."
    columns = (
        ["Mois", "Encaissements", "Décaissements", "Flux net", "Comptes clients", "Comptes fournisseurs"]
        if language == "fr"
        else ["Month", "Cash received", "Cash paid", "Net cash flow", "Accounts receivable", "Accounts payable"]
    )
    rows = [[row[0], *(money(value) for value in row[1:])] for row in records]
    return SkillResult(answer=answer, columns=columns, rows=rows)


SKILLS = [
    SkillDefinition(
        name="activity_revenue",
        description_en="Show cash revenue received, optionally filtered by activity and calendar year.",
        description_fr="Afficher les revenus encaissés, avec activité et année civile facultatives.",
        examples=("Revenue by activity", "Revenue in 2026", "Quel revenu a été encaissé pour le hockey en 2026?"),
        parameters={
            "activity": "Optional activity name or part of its name",
            "year": "Optional four-digit calendar year",
        },
        handler=activity_revenue,
    ),
    SkillDefinition(
        name="highest_revenue_activity",
        description_en="Find the activity with the highest collected cash revenue, optionally for a calendar year.",
        description_fr="Trouver l’activité ayant les revenus encaissés les plus élevés, avec année civile facultative.",
        examples=("Which activity generated the most revenue?", "Quelle activité a été la plus payante?"),
        parameters={"year": "Optional four-digit calendar year"},
        handler=highest_revenue_activity,
    ),
    SkillDefinition(
        name="most_profitable_activity",
        description_en="Find the activity with the highest net profit after expenses, optionally for a calendar year.",
        description_fr="Trouver l’activité avec le bénéfice net le plus élevé après dépenses, avec année facultative.",
        examples=("What is my most profitable activity?", "Quelle activité est la plus rentable?"),
        parameters={"year": "Optional four-digit calendar year"},
        handler=most_profitable_activity,
    ),
    SkillDefinition(
        name="financial_summary",
        description_en="Show monthly cash flow, receivables and payables for the last 12 recorded months.",
        description_fr="Afficher les flux de trésorerie, comptes clients et fournisseurs mensuels.",
        examples=("What is my cash flow?", "Sommaire financier mensuel"),
        parameters={},
        handler=financial_summary,
    ),
]
