"""Trusted financial skills using the application's approved accounting views."""

from sqlalchemy import text

from models import db
from wayne.types import SkillDefinition, SkillResult
from .helpers import money


def activity_revenue(args, language):
    activity = (args.get("activity") or "").strip().lower()
    sql = text("""
        SELECT account, COALESCE(SUM(cash_received), 0) AS revenue
        FROM monthly_financial_summary
        WHERE (:activity = '' OR LOWER(account) LIKE '%' || :activity || '%')
        GROUP BY account
        ORDER BY revenue DESC
        LIMIT 200
    """)
    records = db.session.execute(sql, {"activity": activity}).all()
    total = sum(float(row[1] or 0) for row in records)
    answer = (
        f"Les revenus encaissés totalisent {money(total)} pour {len(records)} activité(s)."
        if language == "fr"
        else f"Cash revenue totals {money(total)} across {len(records)} activity/activities."
    )
    columns = ["Activité", "Revenus encaissés"] if language == "fr" else ["Activity", "Cash revenue"]
    rows = [[row[0], money(row[1])] for row in records]
    return SkillResult(answer=answer, columns=columns, rows=rows)


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
        description_en="Show cash revenue received, optionally filtered by activity.",
        description_fr="Afficher les revenus encaissés, avec activité facultative.",
        examples=("Revenue by activity", "Quel revenu a été encaissé pour le hockey?"),
        parameters={"activity": "Optional activity name or part of its name"},
        handler=activity_revenue,
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
