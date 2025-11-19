"""
Semantic Layer for Bilingual Chatbot
Provides French ↔ English mappings and business term aliases
"""

import re
from typing import Dict, List, Tuple, Union


# === BUSINESS GLOSSARY ===
# Maps user business terms to correct database columns and contexts

BUSINESS_GLOSSARY = {
    # === REVENUE / CASH FLOW (CRITICAL) ===
    # COMPLETE FINANCIAL MODEL - Use ALL 3 sources: passport + income - expense
    "cash flow": {
        "tables": ["passport", "income", "expense"],
        "formula": "(passport sales + other income) - expenses paid",
        "context": "Net cash flow = SUM(passport.sold_amt WHERE paid=1) + SUM(income.amount WHERE payment_status='received') - SUM(expense.amount WHERE payment_status='paid')"
    },
    "flux de trésorerie": {
        "tables": ["passport", "income", "expense"],
        "formula": "(ventes passeports + autres revenus) - dépenses payées",
        "context": "Flux de trésorerie net = SUM(passport.sold_amt WHERE paid=1) + SUM(income.amount WHERE payment_status='received') - SUM(expense.amount WHERE payment_status='paid')"
    },
    "flux de tresorerie": {  # Without accent
        "tables": ["passport", "income", "expense"],
        "formula": "(ventes passeports + autres revenus) - dépenses payées",
        "context": "Flux de trésorerie net = SUM(passport.sold_amt WHERE paid=1) + SUM(income.amount WHERE payment_status='received') - SUM(expense.amount WHERE payment_status='paid')"
    },
    "revenue": {
        "tables": ["passport", "income"],
        "formula": "passport sales + other income",
        "context": "Total revenue = SUM(passport.sold_amt WHERE paid=1) + SUM(income.amount WHERE payment_status='received')"
    },
    "revenu": {
        "tables": ["passport", "income"],
        "formula": "ventes passeports + autres revenus",
        "context": "Revenu total = SUM(passport.sold_amt WHERE paid=1) + SUM(income.amount WHERE payment_status='received')"
    },
    "revenus": {
        "tables": ["passport", "income"],
        "formula": "ventes passeports + autres revenus",
        "context": "Revenus totaux = SUM(passport.sold_amt WHERE paid=1) + SUM(income.amount WHERE payment_status='received')"
    },

    # === FRENCH TABLE NAMES ===
    "utilisateurs": "user",
    "utilisateur": "user",
    "clients": "user",
    "client": "user",

    "activités": "activity",
    "activite": "activity",  # Without accent
    "activité": "activity",

    "passeports": "passport",
    "passeport": "passport",

    "inscriptions": "signup",
    "inscription": "signup",

    "sondages": "survey",
    "sondage": "survey",

    # === FRENCH COLUMN NAMES ===
    "nom": "name",
    "courriel": "email",
    "téléphone": "phone",
    "telephone": "phone",  # Without accent
    "adresse": "address",
    "montant": "amount",
    "prix": "price",
    "date": "date",
    "statut": "status",
    "payé": "paid",
    "paye": "paid",  # Without accent

    # === BUSINESS CONCEPTS ===
    "customers": "user",
    "participants": "user",
    "membres": "user",
    "members": "user",

    "sales": "passport WHERE paid = 1",
    "ventes": "passport WHERE paid = 1",

    "unpaid": "paid = 0",
    "non payé": "paid = 0",
    "non paye": "paid = 0",  # Without accent

    # === TIME PERIODS (CRITICAL FOR FRENCH SUPPORT) ===
    "this month": "DATE(created_at) >= DATE('now', 'start of month')",
    "ce mois": "DATE(created_at) >= DATE('now', 'start of month')",

    "last month": "DATE(created_at) >= DATE('now', 'start of month', '-1 month') AND DATE(created_at) < DATE('now', 'start of month')",
    "le mois dernier": "DATE(created_at) >= DATE('now', 'start of month', '-1 month') AND DATE(created_at) < DATE('now', 'start of month')",
    "mois dernier": "DATE(created_at) >= DATE('now', 'start of month', '-1 month') AND DATE(created_at) < DATE('now', 'start of month')",

    "this year": "DATE(created_at) >= DATE('now', 'start of year')",
    "cette année": "DATE(created_at) >= DATE('now', 'start of year')",
    "cette annee": "DATE(created_at) >= DATE('now', 'start of year')",  # Without accent

    "this week": "DATE(created_at) >= DATE('now', 'start of day', '-' || CAST(strftime('%w', 'now') AS INTEGER) || ' days')",
    "cette semaine": "DATE(created_at) >= DATE('now', 'start of day', '-' || CAST(strftime('%w', 'now') AS INTEGER) || ' days')",

    "today": "DATE(created_at) = DATE('now')",
    "aujourd'hui": "DATE(created_at) = DATE('now')",
    "aujourdhui": "DATE(created_at) = DATE('now')",  # Without apostrophe
}


# === COMMON PATTERNS ===
# Pattern detection for better context

COMMON_PATTERNS = {
    "financial_query": [
        r"(cash flow|flux.*tr[eé]sorerie|revenue|revenu|sales|ventes|income|argent|money)",
        "Use passport.sold_amt for actual revenue, not passport_type.price_per_user"
    ],
    "user_lookup": [
        r"(user|utilisateur|customer|client|participant|member|membre)",
        "Join through user table, include name and email"
    ],
    "payment_status": [
        r"(unpaid|non.*pay[eé]|not.*paid|pending|en.*attente)",
        "Check passport.paid = 0 or signup.paid = 0"
    ],
    "time_based": [
        r"(month|mois|year|ann[eé]e|week|semaine|today|aujourd'hui|dernier|last)",
        "Use DATE() functions with 'now' for current periods"
    ],
    "activity_query": [
        r"(activity|activit[eé]|event|[eé]v[eé]nement|populaire|popular|meilleur|best|top)",
        "Query activity table, often with revenue or signup counts"
    ],
}


def detect_language(question: str) -> str:
    """
    Detect if question is in French or English

    Args:
        question: User's question text

    Returns:
        'fr' for French, 'en' for English
    """
    # Strong French indicators - these alone indicate French
    strong_french_patterns = [
        r'\b(quel|quelle|quels|quelles)\b',  # French question words
        r'\b(combien)\b',  # French "how many"
        r'\b(où)\b',  # French "where" with accent
        r'\bmontre-moi\b',  # French "show me"
        r'\b(génèrent|genèrent)\b',  # French "generate" (with or without accent)
    ]

    # Check strong indicators first
    for pattern in strong_french_patterns:
        if re.search(pattern, question, re.IGNORECASE):
            return "fr"

    # Regular French indicators - need 2 or more
    french_indicators = [
        r'\b(comment|quand|pourquoi)\b',
        r'\b(mon|ma|mes|notre|nos|votre|vos|leur|leurs)\b',
        r'\b(est|sont|a|ont|était|etait|étaient|etaient)\b',
        r'\b(de|du|des|le|la|les|un|une)\b',
        r'\b(ce|cette|ces|cet)\b',
        r'\b(montre|montrer|revenus?|activités?|activites?)\b',
        r'\b(utilisateurs?|clients?)\b',
    ]

    # Count French indicators
    french_count = 0
    for pattern in french_indicators:
        if re.search(pattern, question, re.IGNORECASE):
            french_count += 1

    # If 2 or more French indicators, it's French
    return "fr" if french_count >= 2 else "en"


def apply_semantic_aliases(question: str, language: str) -> Tuple[str, List[str]]:
    """
    Apply semantic aliases to user question

    Args:
        question: Original user question
        language: Detected language ('en' or 'fr')

    Returns:
        Tuple of (enhanced_question, context_hints)
    """
    enhanced = question
    hints = []

    # Track what we've replaced to avoid duplicates
    replacements_made = []

    # Apply glossary replacements
    for term, replacement in BUSINESS_GLOSSARY.items():
        # Use word boundary matching to avoid partial word matches
        pattern = r'\b' + re.escape(term) + r'\b'

        if re.search(pattern, question, re.IGNORECASE):
            if isinstance(replacement, dict):
                # It's a complex mapping with context
                # Add context if available
                if 'context' in replacement:
                    hints.append(replacement['context'])
                elif 'note' in replacement:
                    hints.append(replacement['note'])

                if 'column' in replacement:
                    replacements_made.append(f"{term} → {replacement['column']}")

                # Don't replace in the enhanced question - let AI handle it with context
                # The hints provide the guidance needed

            else:
                # Simple string replacement
                replacements_made.append(f"{term} → {replacement}")
                # Don't replace directly - provide as context instead

    # Detect query pattern and add context
    for pattern_name, (regex, hint) in COMMON_PATTERNS.items():
        if re.search(regex, question, re.IGNORECASE):
            if hint not in hints:
                hints.append(hint)

    return enhanced, hints


def get_time_period_hint(question: str) -> str:
    """
    Detect time period references and provide SQL hints

    Args:
        question: User question

    Returns:
        SQL hint for time period filtering
    """
    question_lower = question.lower()

    # Check for specific time periods
    if any(term in question_lower for term in ["ce mois", "this month"]):
        return "Filter by: DATE(created_at) >= DATE('now', 'start of month')"

    if any(term in question_lower for term in ["mois dernier", "le mois dernier", "last month"]):
        return "Filter by: DATE(created_at) >= DATE('now', 'start of month', '-1 month') AND DATE(created_at) < DATE('now', 'start of month')"

    if any(term in question_lower for term in ["cette semaine", "this week"]):
        return "Filter by: DATE(created_at) >= DATE('now', 'start of day', '-' || CAST(strftime('%w', 'now') AS INTEGER) || ' days')"

    if any(term in question_lower for term in ["cette année", "cette annee", "this year"]):
        return "Filter by: DATE(created_at) >= DATE('now', 'start of year')"

    if any(term in question_lower for term in ["aujourd'hui", "aujourdhui", "today"]):
        return "Filter by: DATE(created_at) = DATE('now')"

    return ""


def translate_french_terms(question: str) -> str:
    """
    Translate common French business terms to English for better AI understanding

    Args:
        question: French question

    Returns:
        Question with key terms translated to English
    """
    translations = {
        "montre-moi": "show me",
        "montre moi": "show me",
        "montrez-moi": "show me",
        "combien": "how many",
        "quel est": "what is",
        "quelle est": "what is",
        "quels sont": "what are",
        "quelles sont": "what are",
        "quelles activités": "which activities",
        "quels utilisateurs": "which users",
        "nouveaux utilisateurs": "new users",
        "nouveaux clients": "new customers",
        "génèrent le plus": "generate the most",
        "genèrent le plus": "generate the most",
        "par activité": "per activity",
        "par activite": "per activity",
    }

    result = question
    for french, english in translations.items():
        result = re.sub(r'\b' + re.escape(french) + r'\b', english, result, flags=re.IGNORECASE)

    return result
