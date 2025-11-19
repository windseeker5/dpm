"""
Test suite for bilingual chatbot functionality
Tests language detection, semantic aliases, and French query processing
"""

import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from chatbot_v2.query_preprocessor import QueryPreprocessor
from chatbot_v2.semantic_layer import detect_language, apply_semantic_aliases, translate_french_terms


class TestLanguageDetection(unittest.TestCase):
    """Test language detection functionality"""

    def test_detect_french_questions(self):
        """Should detect French questions correctly"""
        french_questions = [
            "Quel est mon flux de trésorerie?",
            "Combien d'utilisateurs?",
            "Montre-moi les activités",
            "Quelles activités génèrent le plus de revenus?",
            "Quel est mon flux de trésorerie par activité",
            "Montre-moi le revenu de ce mois",
        ]
        for q in french_questions:
            with self.subTest(question=q):
                self.assertEqual(detect_language(q), "fr", f"Failed to detect French for: {q}")

    def test_detect_english_questions(self):
        """Should detect English questions correctly"""
        english_questions = [
            "What is my cash flow?",
            "Show me all users",
            "How many activities?",
            "Show me this month's revenue breakdown",
            "What are my top performing activities?",
        ]
        for q in english_questions:
            with self.subTest(question=q):
                self.assertEqual(detect_language(q), "en", f"Failed to detect English for: {q}")


class TestSemanticAliases(unittest.TestCase):
    """Test semantic alias application"""

    def test_cash_flow_french(self):
        """Should map 'flux de trésorerie' to correct column"""
        question = "Quel est mon flux de trésorerie?"
        enhanced, hints = apply_semantic_aliases(question, "fr")

        # Should have hints about passport.sold_amt
        self.assertTrue(len(hints) > 0, "Should generate context hints")
        hints_text = " ".join(hints).lower()
        self.assertTrue("revenue" in hints_text or "sold_amt" in hints_text,
                       "Should provide hints about revenue/sold_amt")

    def test_cash_flow_english(self):
        """Should map 'cash flow' to correct column"""
        question = "What is my cash flow per activity?"
        enhanced, hints = apply_semantic_aliases(question, "en")

        self.assertTrue(len(hints) > 0, "Should generate context hints")
        hints_text = " ".join(hints).lower()
        self.assertTrue("sold_amt" in hints_text or "revenue" in hints_text,
                       "Should provide hints about sold_amt")

    def test_time_period_ce_mois(self):
        """Should detect French time period 'ce mois' (this month)"""
        question = "Montre-moi le revenu de ce mois"
        enhanced, hints = apply_semantic_aliases(question, "fr")

        hints_text = " ".join(hints).lower()
        self.assertTrue("month" in hints_text or "date" in hints_text,
                       "Should provide time period context")

    def test_activity_terms_french(self):
        """Should detect French activity terms"""
        question = "Quelles activités génèrent le plus de revenus?"
        enhanced, hints = apply_semantic_aliases(question, "fr")

        self.assertTrue(len(hints) > 0, "Should generate context hints")
        # Should detect both financial and activity patterns
        hints_text = " ".join(hints).lower()
        self.assertTrue("activity" in hints_text or "sold_amt" in hints_text,
                       "Should detect financial/activity query")


class TestFrenchTranslation(unittest.TestCase):
    """Test French term translation"""

    def test_translate_montre_moi(self):
        """Should translate 'montre-moi' to 'show me'"""
        question = "Montre-moi le revenu de ce mois"
        translated = translate_french_terms(question)

        self.assertIn("show me", translated.lower(),
                     "Should translate 'montre-moi' to 'show me'")

    def test_translate_quelles_activites(self):
        """Should translate 'quelles activités' to 'which activities'"""
        question = "Quelles activités génèrent le plus de revenus?"
        translated = translate_french_terms(question)

        self.assertIn("which activities", translated.lower(),
                     "Should translate 'quelles activités'")

    def test_translate_combien(self):
        """Should translate 'combien' to 'how many'"""
        question = "Combien d'utilisateurs?"
        translated = translate_french_terms(question)

        self.assertIn("how many", translated.lower(),
                     "Should translate 'combien'")


class TestQueryPreprocessor(unittest.TestCase):
    """Test the complete query preprocessor pipeline"""

    def setUp(self):
        self.preprocessor = QueryPreprocessor()

    def test_french_revenue_question(self):
        """Test complete preprocessing for French revenue question"""
        question = "Montre-moi le revenu de ce mois"
        result = self.preprocessor.process(question)

        self.assertEqual(result['language'], 'fr', "Should detect French")
        self.assertEqual(result['detected_intent'], 'financial', "Should detect financial intent")
        self.assertTrue(len(result['context_hints']) > 0, "Should have context hints")
        self.assertIsNotNone(result['enhanced_question'], "Should have enhanced question")

    def test_french_activity_question(self):
        """Test preprocessing for French activity performance question"""
        question = "Quelles activités génèrent le plus de revenus?"
        result = self.preprocessor.process(question)

        self.assertEqual(result['language'], 'fr', "Should detect French")
        # Could be 'activity_performance' or 'financial'
        self.assertIn(result['detected_intent'], ['activity_performance', 'financial'],
                     "Should detect activity or financial intent")
        self.assertTrue(len(result['context_hints']) > 0, "Should have context hints")

    def test_french_cash_flow_question(self):
        """Test preprocessing for French cash flow question"""
        question = "Quel est mon flux de trésorerie par activité"
        result = self.preprocessor.process(question)

        self.assertEqual(result['language'], 'fr', "Should detect French")
        self.assertEqual(result['detected_intent'], 'financial', "Should detect financial intent")

        # Check that we have the critical hint about sold_amt
        hints_text = " ".join(result['context_hints']).lower()
        self.assertTrue("sold_amt" in hints_text, "Should mention sold_amt in hints")

    def test_english_question_still_works(self):
        """Test that English questions still work correctly"""
        question = "Show me this month's revenue breakdown"
        result = self.preprocessor.process(question)

        self.assertEqual(result['language'], 'en', "Should detect English")
        self.assertEqual(result['detected_intent'], 'financial', "Should detect financial intent")
        self.assertTrue(len(result['context_hints']) > 0, "Should have context hints")


class TestCriticalBusinessRules(unittest.TestCase):
    """Test critical business rule mappings"""

    def setUp(self):
        self.preprocessor = QueryPreprocessor()

    def test_cash_flow_uses_complete_financial_model(self):
        """
        CRITICAL: Ensure 'cash flow' queries use complete financial model (passport + income - expense)
        This addresses the reported issue - must use ALL 3 tables
        """
        test_questions = [
            "What is my cash flow?",
            "Quel est mon flux de trésorerie?",
            "Show me revenue",
            "Montre-moi le revenu",
            "Quel est mon flux de trésorerie par activité",
        ]

        for q in test_questions:
            with self.subTest(question=q):
                result = self.preprocessor.process(q)
                hints_text = " ".join(result['context_hints']).lower()

                # Should mention ALL 3 sources: passport, income, expense
                self.assertTrue(
                    ("passport" in hints_text or "sold_amt" in hints_text) and
                    ("income" in hints_text),
                    f"Should mention passport AND income tables for: {q}"
                )

                # For cash flow specifically, should mention expense
                if "cash flow" in q.lower() or "flux" in q.lower():
                    self.assertTrue("expense" in hints_text,
                                  f"Cash flow query should mention expense table for: {q}")

    def test_french_queries_processed_correctly(self):
        """
        Ensure French queries are properly processed
        This addresses the reported issue
        """
        french_questions = [
            "Quel est mon flux de trésorerie?",
            "Montre-moi les utilisateurs non payés",
            "Combien de passeports vendus?",
            "Quelles sont mes activités?",
            "Montre-moi le revenu de ce mois",
            "Quelles activités génèrent le plus de revenus?",
        ]

        for q in french_questions:
            with self.subTest(question=q):
                result = self.preprocessor.process(q)

                self.assertEqual(result['language'], 'fr',
                               f"Should detect French for: {q}")
                self.assertIsNotNone(result['enhanced_question'],
                                   f"Should have enhanced question for: {q}")
                self.assertTrue(len(result['context_hints']) > 0,
                              f"Should have context hints for: {q}")

    def test_time_periods_french(self):
        """Test French time period detection"""
        test_cases = [
            ("ce mois", "month"),
            ("cette semaine", "week"),
            ("cette année", "year"),
            ("mois dernier", "month"),
        ]

        for french_term, expected_period in test_cases:
            with self.subTest(term=french_term):
                question = f"Montre-moi le revenu de {french_term}"
                result = self.preprocessor.process(question)

                hints_text = " ".join(result['context_hints']).lower()
                self.assertTrue("date" in hints_text or "filter" in hints_text,
                              f"Should provide time filtering hint for: {french_term}")


class TestButtonQuestions(unittest.TestCase):
    """Test the three specific button questions"""

    def setUp(self):
        self.preprocessor = QueryPreprocessor()

    def test_button_1_montre_moi_revenu(self):
        """Test button 1: Montre-moi le revenu de ce mois"""
        question = "Montre-moi le revenu de ce mois"
        result = self.preprocessor.process(question)

        self.assertEqual(result['language'], 'fr')
        self.assertEqual(result['detected_intent'], 'financial')
        self.assertTrue(len(result['context_hints']) > 0)

        hints_text = " ".join(result['context_hints']).lower()
        self.assertTrue("sold_amt" in hints_text or "revenue" in hints_text)
        # Should have time period hint
        self.assertTrue("date" in hints_text or "month" in hints_text)

    def test_button_2_activites_revenus(self):
        """Test button 2: Quelles activités génèrent le plus de revenus?"""
        question = "Quelles activités génèrent le plus de revenus?"
        result = self.preprocessor.process(question)

        self.assertEqual(result['language'], 'fr')
        # Should detect as activity_performance or financial
        self.assertIn(result['detected_intent'], ['activity_performance', 'financial'])
        self.assertTrue(len(result['context_hints']) > 0)

    def test_button_3_flux_tresorerie_activite(self):
        """Test button 3: Quel est mon flux de trésorerie par activité"""
        question = "Quel est mon flux de trésorerie par activité"
        result = self.preprocessor.process(question)

        self.assertEqual(result['language'], 'fr')
        self.assertEqual(result['detected_intent'], 'financial')

        hints_text = " ".join(result['context_hints']).lower()
        # Must have complete financial model hints - ALL 3 tables
        self.assertTrue("passport" in hints_text or "sold_amt" in hints_text,
                       "Must mention passport/sold_amt for cash flow query")
        self.assertTrue("income" in hints_text,
                       "Must mention income table for complete revenue")
        self.assertTrue("expense" in hints_text,
                       "Must mention expense table for cash flow calculation")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
