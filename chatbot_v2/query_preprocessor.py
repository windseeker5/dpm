"""
Query Preprocessor for Bilingual Chatbot
Handles language detection, semantic aliases, and context enrichment
"""

from typing import Dict, List, Any
from .semantic_layer import (
    detect_language,
    apply_semantic_aliases,
    get_time_period_hint,
    translate_french_terms,
    BUSINESS_GLOSSARY
)


class QueryPreprocessor:
    """
    Pre-processes user questions before sending to AI for SQL generation.
    Handles language detection, semantic aliases, and context enrichment.
    """

    def __init__(self):
        self.supported_languages = ['en', 'fr']

    def process(self, user_question: str) -> Dict[str, Any]:
        """
        Main processing pipeline

        Args:
            user_question: Raw question from user

        Returns:
            {
                'original_question': str,
                'enhanced_question': str,
                'language': 'en' | 'fr',
                'context_hints': List[str],
                'detected_intent': str,
                'confidence': float
            }
        """
        # 1. Detect language
        language = detect_language(user_question)

        # 2. Apply semantic aliases
        enhanced_question, context_hints = apply_semantic_aliases(user_question, language)

        # 3. If French, also translate key terms for better AI understanding
        if language == 'fr':
            enhanced_question = translate_french_terms(user_question)
            context_hints.append("Question is in French - respond with French column aliases in results")

        # 4. Detect time period and add SQL hint
        time_hint = get_time_period_hint(user_question)
        if time_hint:
            context_hints.append(time_hint)

        # 5. Detect query intent
        intent = self._detect_intent(user_question)

        # 6. Add intent-specific hints
        if intent == 'financial':
            context_hints.append("CRITICAL: Use ALL 3 revenue sources - passport.sold_amt + income.amount - expense.amount")
            context_hints.append("CRITICAL: Total Revenue = SUM(passport.sold_amt WHERE paid=1) + SUM(income.amount WHERE payment_status='received')")
            context_hints.append("CRITICAL: Cash Flow = Revenue - SUM(expense.amount WHERE payment_status='paid')")
            context_hints.append("CRITICAL: Must LEFT JOIN with passport, income, AND expense tables for complete financial data")
        elif intent == 'user_lookup':
            context_hints.append("Include user.name and user.email in results")
        elif intent == 'payment_status':
            context_hints.append("Check passport.paid or signup.paid (1=paid, 0=unpaid)")
        elif intent == 'activity_performance':
            context_hints.append("Join activity with passport, income, and expense tables")
            context_hints.append("Calculate revenue from both passport sales and other income")

        return {
            'original_question': user_question,
            'enhanced_question': enhanced_question,
            'language': language,
            'context_hints': context_hints,
            'detected_intent': intent,
            'confidence': self._calculate_confidence(user_question, enhanced_question, context_hints)
        }

    def _detect_intent(self, question: str) -> str:
        """
        Classify query intent

        Args:
            question: User question

        Returns:
            Intent classification string
        """
        question_lower = question.lower()

        # Financial queries
        if any(term in question_lower for term in
               ['cash flow', 'flux', 'revenue', 'revenu', 'revenus', 'sales', 'ventes', 'income', 'argent', 'money', 'trésorerie', 'tresorerie']):
            return 'financial'

        # Activity performance queries
        if any(term in question_lower for term in
               ['top', 'best', 'meilleur', 'populaire', 'popular', 'performing', 'génèrent', 'genèrent', 'generate']):
            return 'activity_performance'

        # User lookup queries
        if any(term in question_lower for term in
               ['user', 'utilisateur', 'customer', 'client', 'participant', 'member', 'membres']):
            return 'user_lookup'

        # Payment status queries
        if any(term in question_lower for term in
               ['unpaid', 'non payé', 'non paye', 'pending', 'attente', 'not paid', 'paid']):
            return 'payment_status'

        # Activity queries
        if any(term in question_lower for term in
               ['activity', 'activité', 'activite', 'event', 'événement', 'evenement']):
            return 'activity_query'

        # Signup/registration queries
        if any(term in question_lower for term in
               ['signup', 'signed up', 'inscription', 'inscrit', 'registered', 'enregistré']):
            return 'signup_query'

        return 'general'

    def _calculate_confidence(self, original: str, enhanced: str, hints: List[str]) -> float:
        """
        Calculate confidence that we understood the query correctly

        Args:
            original: Original question
            enhanced: Enhanced question
            hints: Context hints generated

        Returns:
            Confidence score between 0.0 and 1.0
        """
        base_confidence = 0.5

        # Higher confidence if we have context hints
        if len(hints) > 0:
            base_confidence += 0.1 * min(len(hints), 3)

        # Higher confidence if we applied transformations
        if original != enhanced:
            base_confidence += 0.2

        # Cap at 1.0
        return min(base_confidence, 1.0)
