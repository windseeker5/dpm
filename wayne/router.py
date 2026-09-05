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
    args = {"activity": activity} if activity else {}

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
        "unpaid", "not paid", "hasn't paid", "have not paid", "non pay", "impaye", "pas paye",
        "n'a pas paye", "n'ont pas paye", "n’est pas paye", "ne sont pas paye",
    ))
    paid = any(term in q for term in (" paid", "paye", "payee"))
    count = any(term in q for term in ("how many", "count", "combien", "nombre", "total number"))
    unsupported_date_filter = any(term in q for term in (
        "today", "this week", "this month", "aujourd'hui", "cette semaine", "ce mois",
    ))

    if unpaid:
        return RouteDecision(status="skill", language=language, skill="list_unpaid_participants", arguments=args)
    if paid and any(term in q for term in ("who", "list", "show", "qui", "liste", "participant", "personne")):
        return RouteDecision(status="skill", language=language, skill="list_paid_participants", arguments=args)
    if "passport" in q or "passeport" in q:
        if any(term in q for term in ("active", "actif", "actifs", "valid", "credit restant", "credits remaining", "still have", "encore des credit")):
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
        if year or unsupported_date_filter:
            return RouteDecision(status="unsupported", language=language)
        return RouteDecision(status="skill", language=language, skill="financial_summary", arguments={})
    if any(term in q for term in ("revenue", "revenu", "revenus")):
        if unsupported_date_filter:
            return RouteDecision(status="unsupported", language=language)
        if year:
            args["year"] = year
        return RouteDecision(status="skill", language=language, skill="activity_revenue", arguments=args)
    if any(term in q for term in ("seat", "space", "place libre", "places libre", "places restent", "capacity", "capacite")):
        return RouteDecision(status="skill", language=language, skill="available_session_seats", arguments=args)
    if any(term in q for term in ("attendance", "attended", "presence", "present")):
        return RouteDecision(status="skill", language=language, skill="session_attendance", arguments=args)
    if "survey" in q or "sondage" in q:
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
