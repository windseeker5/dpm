"""Bilingual local-first router for Wayne's trusted skills."""

import json
import re
import unicodedata
from collections import OrderedDict
from datetime import datetime
from dataclasses import replace
from threading import Lock

from wayne.client import select_skill
from wayne.skills import SKILLS, public_catalog
from wayne.types import RouteDecision


FRENCH_MARKERS = {
    "bonjour", "bonsoir", "salut", "allo", "combien", "quel", "quelle", "quels", "quelles", "qui", "pour", "activité",
    "activite", "inscription", "inscriptions", "passeport", "passeports", "payé",
    "paye", "payées", "payees", "personne", "personnes", "revenu", "trésorerie",
    "tresorerie", "sondage", "présence", "presence", "places", "reste", "liste",
}

SCOPE_TERMS = (
    "activit", "participant", "personne", "signup", "registration", "inscription",
    "passport", "passeport", "payment", "paiement", "paid", "paye", "revenue",
    "revenu", "cash flow", "tresorerie", "booking", "reservation", "session",
    "attendance", "presence", "survey", "sondage", "email", "courriel",
    "customer", "client", "reminder", "rappel", "expense", "depense", "credit",
    "seat", "place", "cancelled", "canceled", "annule",
)


def _plain(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.lower())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def detect_language(question: str) -> str:
    words = set(re.findall(r"[a-zà-ÿ']+", question.lower()))
    return "fr" if words & FRENCH_MARKERS else "en"


def _extract_year(question: str) -> int | None:
    """Extract an explicit calendar year without confusing activity season names."""
    q = _plain(question)
    patterns = (
        r"\b(?:in|during|en)\s+((?:19|20)\d{2})\b",
        r"\bfor\s+(?:the\s+)?year\s+((?:19|20)\d{2})\b",
        r"\bpour\s+l['’]annee\s+((?:19|20)\d{2})\b",
        r"\b(?:year|annee)\s+((?:19|20)\d{2})\b",
    )
    for pattern in patterns:
        match = re.search(pattern, q)
        if match:
            return int(match.group(1))
    if any(term in q for term in ("this year", "cette annee")):
        return datetime.now().year
    return None


def _extract_period(question: str) -> str | None:
    q = _plain(question)
    if any(term in q for term in ("today", "aujourd'hui", "aujourd’hui")):
        return "today"
    if any(term in q for term in ("this week", "cette semaine")):
        return "this_week"
    if any(term in q for term in ("this month", "ce mois", "ce mois-ci")):
        return "this_month"
    if any(term in q for term in ("this year", "cette annee")):
        return "this_year"
    return None


def _extract_customer(question: str) -> str | None:
    patterns = (
        r"\b(?:everything about|summary for|history for)\s+(.+?)[?.!]*$",
        r"\bhow much has\s+(.+?)\s+spent[?.!]*$",
        r"\bwhen was\s+(.+?)(?:'s|’s)\s+last visit[?.!]*$",
        r"\b(?:tout sur|resume de|historique de|derniere visite de)\s+(.+?)[?.!]*$",
        r"\bcombien\s+(.+?)\s+a-t-il depense[?.!]*$",
    )
    plain_question = _plain(question)
    for pattern in patterns:
        match = re.search(pattern, plain_question, re.IGNORECASE)
        if match:
            return match.group(1).strip()[:150] or None
    return None


def _extract_activity(question: str) -> str | None:
    """Extract common English/French trailing activity phrases locally."""
    match = re.search(
        r"\b(?:for|pour|au|aux|du|de la|de l['’])\s+(.+?)[?.!]*$",
        question,
        re.IGNORECASE,
    )
    if not match:
        return None
    value = match.group(1).strip()
    value = re.sub(r"^(?:the|l['’]|le|la|les)\s*", "", value, flags=re.IGNORECASE)
    # A year or relative date is a filter, not an activity name. Existing skills
    # do not support date filters and must not silently return an all-time total.
    plain_value = _plain(value)
    if (
        re.fullmatch(r"(?:19|20)\d{2}", value)
        or re.fullmatch(r"(?:the\s+)?year\s+(?:19|20)\d{2}", plain_value)
        or re.fullmatch(r"annee\s+(?:19|20)\d{2}", plain_value)
        or plain_value in {
            "today", "this week", "this month", "this year", "aujourd'hui", "cette semaine", "ce mois", "cette annee",
        }
    ):
        return None
    return value[:150] or None


def _local_decision(question: str, language: str) -> RouteDecision | None:
    q = _plain(question).strip()
    activity = _extract_activity(question)
    year = _extract_year(question)
    period = _extract_period(question)
    customer = _extract_customer(question)
    args = {"activity": activity} if activity else {}
    time_args = {"year": year} if year else {"period": period} if period else {}

    greeting_only = re.fullmatch(
        r"(?:hello|hi|hey|bonjour|bonsoir|salut|allo)(?:\s+wayne)?[\s!.,?]*",
        q,
    )
    if greeting_only:
        return RouteDecision(status="greeting", language=language)

    if any(term in q for term in (
        "what can you do", "how can you help", "what data can you", "help me use wayne",
        "que peux-tu faire", "comment peux-tu m'aider", "comment peux-tu m’aider",
        "qu'est-ce que tu peux faire", "qu’est-ce que tu peux faire", "quelles donnees peux-tu",
    )):
        return RouteDecision(status="help", language=language)

    if any(term in q for term in (
        "weather", "meteo", "recipe", "recette", "joke", "blague",
        "politics", "politique", "stock market", "stock price", "stocks",
        "marche boursier", "cours de bourse", "bourse",
    )):
        return RouteDecision(status="out_of_scope", language=language)

    unpaid = any(term in q for term in (
        "unpaid", "not paid", "hasn't paid", "hasn’t paid", "have not paid", "non pay", "impaye", "pas paye",
        "n'a pas paye", "n'ont pas paye", "n’est pas paye", "ne sont pas paye",
    ))
    paid = any(term in q for term in (" paid", "paye", "payee"))
    count = any(term in q for term in ("how many", "count", "combien", "nombre", "total number"))
    if any(term in q for term in (
        "what needs my attention", "needs attention", "need my attention",
        "necessite mon attention", "a surveiller aujourd", "priorites aujourd",
    )):
        return RouteDecision(status="skill", language=language, skill="operational_overview", arguments={})

    if customer and any(term in q for term in (
        "everything about", "summary for", "history for", "how much has", "last visit",
        "tout sur", "resume de", "historique de", "derniere visite", "a-t-il depense",
    )):
        return RouteDecision(status="skill", language=language, skill="customer_summary", arguments={"customer": customer})

    if any(term in q for term in ("email", "emails", "courriel", "courriels")):
        email_args = dict(time_args)
        if customer:
            email_args["customer"] = customer
        return RouteDecision(status="skill", language=language, skill="email_delivery_summary", arguments=email_args)
    if any(term in q for term in ("reminder", "reminders", "rappel", "rappels")):
        return RouteDecision(status="skill", language=language, skill="reminder_summary", arguments=time_args)

    if any(term in q for term in ("expense", "expenses", "depense", "depenses")) and any(term in q for term in ("owe", "unpaid", "still pay", "dois", "impaye")):
        return RouteDecision(status="skill", language=language, skill="outstanding_expenses", arguments=args)
    if any(term in q for term in ("how much do customers owe", "how much do customers still owe", "amounts still owed", "outstanding balance", "who owes", "montant du", "me doivent", "doit encore", "soldes impayes")):
        return RouteDecision(status="skill", language=language, skill="outstanding_balances", arguments=args)
    if any(term in q for term in ("payment received", "payments received", "pay today", "paid today", "money did i collect", "how much money", "how much did i collect", "paiement recu", "paiements recus", "recu ce", "recu aujourd", "combien ai-je encaisse")):
        return RouteDecision(status="skill", language=language, skill="payment_summary", arguments=time_args)

    if any(term in q for term in ("no-show", "no show", "did not show", "didn't show", "didn’t show", "not show up", "absence", "pas presente", "ne s'est pas presente", "ne s’est pas presente")):
        return RouteDecision(status="skill", language=language, skill="session_no_shows", arguments=args)

    if any(term in q for term in ("not answered", "not completed", "hasn't answered", "hasn’t answered", "haven't answered", "haven’t answered", "pas repondu", "pas encore repondu", "n'a pas repondu", "n’ont pas repondu")):
        return RouteDecision(status="skill", language=language, skill="pending_survey_responses", arguments=args)
    if ("survey" in q or "sondage" in q) and any(term in q for term in ("completed", "response", "reponse", "taux")):
        return RouteDecision(status="skill", language=language, skill="survey_summary", arguments=args)

    if any(term in q for term in ("attendance", "attended", "presence", "present")):
        return RouteDecision(status="skill", language=language, skill="session_attendance", arguments={**args, **time_args})

    if unpaid:
        return RouteDecision(status="skill", language=language, skill="list_unpaid_participants", arguments=args)
    if paid and any(term in q for term in ("who", "list", "show", "qui", "liste", "participant", "personne")):
        return RouteDecision(status="skill", language=language, skill="list_paid_participants", arguments=args)
    if any(term in q for term in ("one credit", "1 credit", "running out of credit", "low credit", "peu de credit", "un credit restant")):
        low_args = dict(args)
        low_args["threshold"] = 1
        return RouteDecision(status="skill", language=language, skill="low_credit_passports", arguments=low_args)

    if "passport" in q or "passeport" in q:
        if any(term in q for term in ("sold", "sell", "sales", "vendu", "vente", "se vend")):
            return RouteDecision(status="skill", language=language, skill="passport_sales_summary", arguments={**args, **time_args})
        if any(term in q for term in ("never been used", "never used", "jamais ete utilise", "jamais utilise", "jamais servi")):
            return RouteDecision(status="skill", language=language, skill="unused_passports", arguments=args)
        if any(term in q for term in ("one credit", "1 credit", "running out", "low credit", "peu de credit", "un credit", "manquent de credit")):
            low_args = dict(args)
            low_args["threshold"] = 1
            return RouteDecision(status="skill", language=language, skill="low_credit_passports", arguments=low_args)
        if any(term in q for term in ("active", "actif", "actifs", "valid", "credit restant", "credits remaining", "still have", "encore des credit")):
            return RouteDecision(status="skill", language=language, skill="list_active_passports", arguments=args)
        if any(term in q for term in ("exhaust", "used up", "no credit", "sans credit", "epuise")):
            return RouteDecision(status="skill", language=language, skill="list_exhausted_passports", arguments=args)
        if count:
            return RouteDecision(status="skill", language=language, skill="count_passports", arguments=args)
    participant_question = any(term in q for term in ("participant", "person", "people", "personne"))
    if any(term in q for term in ("signup", "registration", "registered", "inscription", "inscrit")) and not (participant_question and count):
        if any(term in q for term in ("most", "highest", "le plus", "la plus")):
            return RouteDecision(status="skill", language=language, skill="activity_registration_summary", arguments={"mode": "top", **time_args})
        if any(term in q for term in ("no registration", "no signup", "without registration", "sans inscription")):
            return RouteDecision(status="skill", language=language, skill="activity_registration_summary", arguments={"mode": "zero", **time_args})
        if count:
            return RouteDecision(status="skill", language=language, skill="count_signups", arguments={**args, **time_args})
        if any(term in q for term in ("who", "list", "show", "new", "qui", "liste", "nouvelles")):
            return RouteDecision(status="skill", language=language, skill="list_signups", arguments={**args, **time_args})
    if participant_question and count:
        return RouteDecision(status="skill", language=language, skill="count_participants", arguments={**args, **time_args})

    year_args = {"year": year} if year else {}
    if any(term in q for term in (
        "most profitable", "highest profit", "best profit", "plus profitable",
        "plus rentable", "meilleur benefice", "benefice le plus eleve",
    )):
        return RouteDecision(status="skill", language=language, skill="most_profitable_activity", arguments=year_args)
    if any(term in q for term in (
        "most revenue", "highest revenue", "top revenue", "generated the most revenue",
        "plus payante", "plus payant", "genere le plus de revenus", "revenus les plus eleves",
    )):
        return RouteDecision(status="skill", language=language, skill="highest_revenue_activity", arguments=year_args)

    if any(term in q for term in ("compare my activities", "compare activities", "activity performance", "performance des activites", "compare mes activites")):
        return RouteDecision(status="skill", language=language, skill="activity_performance", arguments=time_args)

    if any(term in q for term in ("cash flow", "tresorerie", "sommaire financier", "financial summary")):
        if year or period:
            return RouteDecision(status="unsupported", language=language)
        return RouteDecision(status="skill", language=language, skill="financial_summary", arguments={})
    if any(term in q for term in ("revenue", "revenu", "revenus")):
        if any(term in q for term in ("compared", "compare to", "versus", "vs ", "par rapport")):
            return RouteDecision(status="unsupported", language=language)
        if period in {"today", "this_week"}:
            return RouteDecision(status="skill", language=language, skill="payment_summary", arguments=time_args)
        if year:
            args["year"] = year
        elif period:
            args["period"] = period
        return RouteDecision(status="skill", language=language, skill="activity_revenue", arguments=args)
    if any(term in q for term in ("almost full", "nearly full", "presque complete", "presque pleine")):
        return RouteDecision(status="skill", language=language, skill="available_session_seats", arguments={**args, "mode": "nearly_full"})
    if any(term in q for term in ("completely full", "are full", "sont completes", "sont pleines")):
        return RouteDecision(status="skill", language=language, skill="available_session_seats", arguments={**args, "mode": "full"})
    if any(term in q for term in ("seat", "space", "place libre", "places libre", "places restent", "capacity", "capacite")):
        return RouteDecision(status="skill", language=language, skill="available_session_seats", arguments=args)
    if any(term in q for term in ("redeemed", "redemption", "credits used", "credit utilise", "utilisations de passeport")):
        return RouteDecision(status="skill", language=language, skill="redemption_summary", arguments={**args, **time_args})
    if "survey" in q or "sondage" in q:
        if any(term in q for term in ("not answered", "not completed", "hasn't answered", "have not answered", "pas repondu", "pas encore repondu", "n'a pas repondu", "n’a pas repondu", "n’ont pas repondu")):
            return RouteDecision(status="skill", language=language, skill="pending_survey_responses", arguments=args)
        return RouteDecision(status="skill", language=language, skill="survey_summary", arguments=args)
    if any(term in q for term in ("activit", "activities")) and any(term in q for term in ("list", "show", "which", "liste", "quelles")):
        status = "archived" if "archiv" in q else "active"
        return RouteDecision(status="skill", language=language, skill="list_activities", arguments={"status": status})

    # An obvious minipass request with no matching trusted skill is unsupported.
    # Handling it here avoids paying an AI model to reach the same conclusion.
    if any(term in q for term in SCOPE_TERMS):
        return RouteDecision(status="unsupported", language=language)
    return None


SYSTEM_PROMPT = """Select one listed minipass skill. Never answer and never write SQL.
Return one JSON object with keys: status, language, skill, arguments.
status must be skill, out_of_scope, or unsupported. language must be en or fr.
For status skill, use an exact listed skill name. Otherwise skill must be JSON null.
arguments must be a JSON object. Preserve activity names exactly."""


_decision_cache = OrderedDict()
_decision_cache_lock = Lock()
_DECISION_CACHE_SIZE = 256


def clear_decision_cache() -> None:
    """Clear cached AI routing decisions (primarily for tests and maintenance)."""
    with _decision_cache_lock:
        _decision_cache.clear()


def _openrouter_decision(question: str, language: str) -> RouteDecision:
    """Route unusual wording once, then reuse that decision without more tokens."""
    cache_key = (question, language)
    with _decision_cache_lock:
        cached = _decision_cache.get(cache_key)
        if cached:
            _decision_cache.move_to_end(cache_key)
            return replace(cached, source="cache", tokens_used=0)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": json.dumps(
                {"question": question, "skills": public_catalog(language=language)},
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        },
    ]
    response = select_skill(messages)
    raw = response["content"].strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.IGNORECASE)
    try:
        payload = json.loads(raw)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("OpenRouter did not return a valid skill selection.") from exc

    status = payload.get("status")
    skill_name = payload.get("skill")
    if skill_name not in SKILLS:
        if status == "skill":
            status = "unsupported"
        skill_name = None

    selected_args = payload.get("arguments") if isinstance(payload.get("arguments"), dict) else {}
    if skill_name:
        allowed = SKILLS[skill_name].parameters
        selected_args = {
            key: value for key, value in selected_args.items()
            if key in allowed and isinstance(value, (str, int, float, bool))
        }
    else:
        selected_args = {}

    decision = RouteDecision(
        status=status if status in {"skill", "out_of_scope", "unsupported"} else "unsupported",
        language=payload.get("language") if payload.get("language") in {"en", "fr"} else language,
        skill=skill_name,
        arguments=selected_args,
        source="openrouter",
        model=response["model"],
        tokens_used=response["tokens_used"],
    )
    with _decision_cache_lock:
        _decision_cache[cache_key] = decision
        _decision_cache.move_to_end(cache_key)
        while len(_decision_cache) > _DECISION_CACHE_SIZE:
            _decision_cache.popitem(last=False)
    return decision


def route_question(question: str) -> RouteDecision:
    language = detect_language(question)
    local = _local_decision(question, language)
    if local:
        return local
    return _openrouter_decision(question.strip(), language)
