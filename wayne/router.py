"""Bilingual local-first router for Wayne's trusted skills."""

import json
import re
import unicodedata

from wayne.client import select_skill
from wayne.skills import SKILLS, public_catalog
from wayne.types import RouteDecision


FRENCH_MARKERS = {
    "bonjour", "bonsoir", "salut", "allo", "combien", "quel", "quelle", "quels", "quelles", "qui", "pour", "activité",
    "activite", "inscription", "inscriptions", "passeport", "passeports", "payé",
    "paye", "payées", "payees", "personne", "personnes", "revenu", "trésorerie",
    "tresorerie", "sondage", "présence", "presence", "places", "reste", "liste",
}


def _plain(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.lower())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def detect_language(question: str) -> str:
    words = set(re.findall(r"[a-zà-ÿ']+", question.lower()))
    return "fr" if words & FRENCH_MARKERS else "en"


def _extract_activity(question: str) -> str | None:
    """Extract a simple trailing activity phrase without asking OpenRouter."""
    match = re.search(r"\b(?:for|pour)\s+(.+?)[?.!]*$", question, re.IGNORECASE)
    if not match:
        return None
    value = match.group(1).strip()
    value = re.sub(r"^(?:the|l['’]|le|la|les)\s*", "", value, flags=re.IGNORECASE)
    return value[:150] or None


def _local_decision(question: str, language: str) -> RouteDecision | None:
    q = _plain(question)
    activity = _extract_activity(question)
    args = {"activity": activity} if activity else {}

    if re.search(r"\b(hello|hi|hey|bonjour|salut|allo)\b", q):
        return RouteDecision(status="greeting", language=language)

    if any(term in q for term in (
        "weather", "meteo", "recipe", "recette", "joke", "blague",
        "politics", "politique", "stock market", "stock price", "stocks",
        "marche boursier", "cours de bourse", "bourse",
    )):
        return RouteDecision(status="out_of_scope", language=language)

    unpaid = any(term in q for term in ("unpaid", "not paid", "hasn't paid", "have not paid", "non pay", "impaye", "pas paye"))
    paid = any(term in q for term in (" paid", "paye", "payee"))
    count = any(term in q for term in ("how many", "count", "combien", "nombre"))

    if unpaid:
        return RouteDecision(status="skill", language=language, skill="list_unpaid_participants", arguments=args)
    if paid and any(term in q for term in ("who", "list", "qui", "liste", "participant", "personne")):
        return RouteDecision(status="skill", language=language, skill="list_paid_participants", arguments=args)
    if "passport" in q or "passeport" in q:
        if any(term in q for term in ("active", "valid", "credit restant", "credits remaining", "still have")):
            return RouteDecision(status="skill", language=language, skill="list_active_passports", arguments=args)
        if any(term in q for term in ("exhaust", "used up", "no credit", "sans credit", "epuise")):
            return RouteDecision(status="skill", language=language, skill="list_exhausted_passports", arguments=args)
        if count:
            return RouteDecision(status="skill", language=language, skill="count_passports", arguments=args)
    if any(term in q for term in ("signup", "registration", "inscription")) and count:
        return RouteDecision(status="skill", language=language, skill="count_signups", arguments=args)
    if any(term in q for term in ("participant", "person", "people", "personne")) and count:
        return RouteDecision(status="skill", language=language, skill="count_participants", arguments=args)
    if any(term in q for term in ("cash flow", "tresorerie", "sommaire financier", "financial summary")):
        return RouteDecision(status="skill", language=language, skill="financial_summary", arguments={})
    if any(term in q for term in ("revenue", "revenu", "revenus")):
        return RouteDecision(status="skill", language=language, skill="activity_revenue", arguments=args)
    if any(term in q for term in ("seat", "space", "place libre", "places libre", "places restent", "capacity", "capacite")):
        return RouteDecision(status="skill", language=language, skill="available_session_seats", arguments=args)
    if any(term in q for term in ("attendance", "attended", "presence", "present")):
        return RouteDecision(status="skill", language=language, skill="session_attendance", arguments=args)
    if "survey" in q or "sondage" in q:
        return RouteDecision(status="skill", language=language, skill="survey_summary", arguments=args)
    if any(term in q for term in ("activit", "activities")) and any(term in q for term in ("list", "show", "which", "liste", "quelles")):
        status = "archived" if ("archiv" in q) else "active"
        return RouteDecision(status="skill", language=language, skill="list_activities", arguments={"status": status})
    return None


SYSTEM_PROMPT = """You are Wayne, the minipass data assistant. Your only job in this call is to select one approved skill; never answer the question and never write SQL.
Scope: minipass activities, participants, signups, passports, payments, finances, bookings, attendance, and surveys only.
Return JSON only with: status (skill, out_of_scope, or unsupported), language (en or fr), skill (approved name or null), arguments (object).
Use out_of_scope for unrelated questions. Use unsupported when the question concerns minipass data but no skill can answer it. Never invent arguments. Preserve an activity name from the question exactly."""


def route_question(question: str) -> RouteDecision:
    language = detect_language(question)
    local = _local_decision(question, language)
    if local:
        return local

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": json.dumps(
                {"question": question, "approved_skills": public_catalog()},
                ensure_ascii=False,
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
    if status == "skill" and skill_name not in SKILLS:
        status, skill_name = "unsupported", None

    selected_args = payload.get("arguments") if isinstance(payload.get("arguments"), dict) else {}
    if skill_name:
        allowed = SKILLS[skill_name].parameters
        selected_args = {
            key: value for key, value in selected_args.items()
            if key in allowed and isinstance(value, (str, int, float, bool))
        }
    else:
        selected_args = {}

    return RouteDecision(
        status=status if status in {"skill", "out_of_scope", "unsupported"} else "unsupported",
        language=payload.get("language") if payload.get("language") in {"en", "fr"} else language,
        skill=skill_name,
        arguments=selected_args,
        source="openrouter",
        model=response["model"],
        tokens_used=response["tokens_used"],
    )
