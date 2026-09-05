"""Focused tests for Wayne's local-first routing and OpenRouter safeguards.

Run: python -m unittest test.test_wayne -v
"""

import json
import unittest
from unittest.mock import patch

from flask import Flask
from sqlalchemy import text

from models import db
from wayne.client import _RetryableResponseError, _parse_response
from wayne.router import clear_decision_cache, route_question
from wayne.skills.finances import activity_revenue, highest_revenue_activity, most_profitable_activity


class WayneRouterTests(unittest.TestCase):
    def setUp(self):
        clear_decision_cache()

    @patch("wayne.router.select_skill")
    def test_common_question_does_not_call_openrouter(self, select_skill):
        decision = route_question("How many participants?")
        self.assertEqual("count_participants", decision.skill)
        self.assertEqual("local", decision.source)
        select_skill.assert_not_called()

    def test_greeting_does_not_hide_question(self):
        decision = route_question("Hey Wayne, how many passports do I have?")
        self.assertEqual("count_passports", decision.skill)

    def test_greeting_only_is_a_greeting(self):
        decision = route_question("Bonjour Wayne!")
        self.assertEqual("greeting", decision.status)
        self.assertEqual("fr", decision.language)

    def test_french_activity_is_extracted(self):
        decision = route_question("Combien de personnes sont inscrites au yoga?")
        self.assertEqual("count_participants", decision.skill)
        self.assertEqual({"activity": "yoga"}, decision.arguments)

    def test_french_active_passports(self):
        decision = route_question("Combien de passeports actifs ai-je?")
        self.assertEqual("list_active_passports", decision.skill)
        self.assertEqual("fr", decision.language)

    def test_french_help_with_curly_apostrophe(self):
        decision = route_question("Bonjour Wayne, comment peux-tu m’aider aujourd’hui?")
        self.assertEqual("help", decision.status)
        self.assertEqual("fr", decision.language)

    def test_french_unpaid_wording_is_not_mistaken_for_paid(self):
        decision = route_question("Donne-moi la liste des clients qui n'ont pas payé.")
        self.assertEqual("list_unpaid_participants", decision.skill)
        self.assertEqual("fr", decision.language)

    def test_english_revenue_year_routes_locally(self):
        decision = route_question("What was my revenue in 2026?")
        self.assertEqual("activity_revenue", decision.skill)
        self.assertEqual({"year": 2026}, decision.arguments)
        self.assertEqual("local", decision.source)

    def test_exact_french_revenue_year_question_routes_locally(self):
        decision = route_question("Hey Wayne, peux-tu me donner mes revenus total pour l'année 2026?")
        self.assertEqual("activity_revenue", decision.skill)
        self.assertEqual({"year": 2026}, decision.arguments)
        self.assertEqual("fr", decision.language)
        self.assertEqual("local", decision.source)

    def test_highest_collected_revenue_routes_locally_in_french(self):
        questions = (
            "Et Wayne, peux-tu me dire quelle activité a été la plus payante?",
            "Quelle est mon activité la plus... avec le plus de revenus?",
            "Mais non, donne-moi juste l'activité qui a le plus de revenus. Pas la liste, j'en veux juste la. Donne-moi l'activité.",
        )
        for question in questions:
            with self.subTest(question=question):
                decision = route_question(question)
                self.assertEqual("highest_revenue_activity", decision.skill)
                self.assertEqual({}, decision.arguments)
                self.assertEqual("fr", decision.language)
                self.assertEqual("local", decision.source)

    def test_exact_french_unpaid_passports_question(self):
        decision = route_question("Est-ce qu'il y a des passeports qui n'ont pas été payés encore?")
        self.assertEqual("list_unpaid_passports", decision.skill)
        self.assertEqual({}, decision.arguments)
        self.assertEqual("fr", decision.language)
        self.assertEqual("local", decision.source)

    def test_french_unpaid_passport_variations(self):
        questions = (
            "Quels passeports restent à payer?",
            "Quels passeports n’ont toujours pas été payés?",
            "Quels passeports ont un paiement en attente?",
            "Pour quels passeports le paiement n’a pas été reçu?",
            "Quels passeports sont impayés?",
            "Quels passeports sont non réglés?",
            "Quels passeports sont non acquittés?",
            "Qui doit encore payer son passeport?",
        )
        for question in questions:
            with self.subTest(question=question):
                decision = route_question(question)
                self.assertEqual("list_unpaid_passports", decision.skill)
                self.assertEqual("fr", decision.language)
                self.assertEqual("local", decision.source)

    def test_french_highest_revenue_and_profit_variations(self):
        revenue_questions = (
            "Quelle activité rapporte le plus?",
            "Laquelle a généré le plus d’argent?",
            "Quelle activité a le meilleur chiffre d’affaires?",
        )
        for question in revenue_questions:
            with self.subTest(question=question):
                self.assertEqual("highest_revenue_activity", route_question(question).skill)
        self.assertEqual("most_profitable_activity", route_question("Quelle activité est la plus lucrative?").skill)

    def test_most_profitable_routes_locally_with_year(self):
        decision = route_question("What was my most profitable activity in 2026?")
        self.assertEqual("most_profitable_activity", decision.skill)
        self.assertEqual({"year": 2026}, decision.arguments)
        self.assertEqual("local", decision.source)

    def test_operations_questions_route_locally_in_both_languages(self):
        cases = (
            ("What needs my attention today?", "operational_overview"),
            ("How much do customers owe me?", "outstanding_balances"),
            ("How much do I still owe in expenses?", "outstanding_expenses"),
            ("Did anyone pay today?", "payment_summary"),
            ("Compare my activities in 2026", "activity_performance"),
            ("Which passports have never been used?", "unused_passports"),
            ("Who has one credit left?", "low_credit_passports"),
            ("How many passports did I sell this month?", "passport_sales_summary"),
            ("Who did not show up?", "session_no_shows"),
            ("Are any activities almost full?", "available_session_seats"),
            ("How many emails did I send this year?", "email_delivery_summary"),
            ("Who received a payment reminder?", "reminder_summary"),
            ("Who has not answered the survey?", "pending_survey_responses"),
            ("Which activity has the most registrations?", "activity_registration_summary"),
            ("Who registered this week?", "list_signups"),
            ("How many credits were redeemed this week?", "redemption_summary"),
            ("Qu’est-ce qui nécessite mon attention aujourd’hui?", "operational_overview"),
            ("Combien ai-je reçu ce mois-ci?", "payment_summary"),
            ("Quels passeports n’ont jamais été utilisés?", "unused_passports"),
            ("Qui ne s’est pas présenté?", "session_no_shows"),
            ("Combien de courriels ai-je envoyés cette année?", "email_delivery_summary"),
            ("Qui n’a pas encore répondu au sondage?", "pending_survey_responses"),
        )
        for question, expected_skill in cases:
            with self.subTest(question=question):
                decision = route_question(question)
                self.assertEqual(expected_skill, decision.skill)
                self.assertEqual("local", decision.source)

    def test_overlapping_wording_uses_the_specific_skill(self):
        cases = (
            ("Who still hasn’t paid?", "list_unpaid_participants"),
            ("Who registered but didn’t show up?", "session_no_shows"),
            ("How many people attended hockey this month?", "session_attendance"),
            ("How many people completed the survey?", "survey_summary"),
            ("Which participants haven’t answered yet?", "pending_survey_responses"),
        )
        for question, expected_skill in cases:
            with self.subTest(question=question):
                self.assertEqual(expected_skill, route_question(question).skill)

    def test_unsupported_comparison_does_not_return_wrong_revenue(self):
        decision = route_question("Did revenue increase compared with last year?")
        self.assertEqual("unsupported", decision.status)
        self.assertIsNone(decision.skill)

    def test_period_is_passed_to_local_skill(self):
        decision = route_question("How many signups did I get this month?")
        self.assertEqual("count_signups", decision.skill)
        self.assertEqual({"period": "this_month"}, decision.arguments)

    def test_customer_history_extracts_customer_name(self):
        decision = route_question("Show me everything about Steven Belanger")
        self.assertEqual("customer_summary", decision.skill)
        self.assertEqual({"customer": "steven belanger"}, decision.arguments)

    def test_customer_spending_question_extracts_name(self):
        decision = route_question("How much has Steven Belanger spent?")
        self.assertEqual("customer_summary", decision.skill)
        self.assertEqual({"customer": "steven belanger"}, decision.arguments)

    def test_french_customer_visit_question_extracts_name(self):
        decision = route_question("Quelle est la dernière visite de Steven Belanger?")
        self.assertEqual("customer_summary", decision.skill)
        self.assertEqual({"customer": "steven belanger"}, decision.arguments)
        self.assertEqual("fr", decision.language)

    def test_help_is_local(self):
        decision = route_question("What data can you help me with?")
        self.assertEqual("help", decision.status)
        self.assertEqual("local", decision.source)

    @patch("wayne.router.select_skill")
    def test_invalid_model_skill_is_safely_discarded(self, select_skill):
        select_skill.return_value = {
            "content": json.dumps({
                "status": "unsupported", "language": "en", "skill": "name|null", "arguments": {}
            }),
            "model": "cheap-router",
            "tokens_used": 20,
        }
        decision = route_question("Please make sense of everything")
        self.assertEqual("unsupported", decision.status)
        self.assertIsNone(decision.skill)

    @patch("wayne.router.select_skill")
    def test_unusual_question_is_cached(self, select_skill):
        select_skill.return_value = {
            "content": json.dumps({
                "status": "unsupported", "language": "en", "skill": None, "arguments": {}
            }),
            "model": "cheap-router",
            "tokens_used": 20,
        }
        first = route_question("Give me a quick overview")
        second = route_question("Give me a quick overview")
        self.assertEqual("unsupported", first.status)
        self.assertEqual("openrouter", first.source)
        self.assertEqual("cache", second.source)
        self.assertEqual(0, second.tokens_used)
        select_skill.assert_called_once()


class WayneFinanceSkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Flask(__name__)
        cls.app.config.update(
            SQLALCHEMY_DATABASE_URI="sqlite://",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
        db.init_app(cls.app)
        cls.context = cls.app.app_context()
        cls.context.push()
        db.session.execute(text("""
            CREATE TABLE monthly_financial_summary (
                month TEXT,
                account TEXT,
                cash_received REAL,
                total_revenue REAL,
                total_expenses REAL,
                net_income REAL
            )
        """))
        db.session.execute(text("""
            INSERT INTO monthly_financial_summary
                (month, account, cash_received, total_revenue, total_expenses, net_income)
            VALUES
                ('2025-12', 'Yoga', 100.00, 120.00, 20.00, 100.00),
                ('2026-01', 'Yoga', 250.00, 300.00, 50.00, 250.00),
                ('2026-02', 'Hockey', 400.00, 420.00, 300.00, 120.00)
        """))
        db.session.commit()

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        cls.context.pop()

    def test_revenue_is_filtered_to_requested_year(self):
        result = activity_revenue({"year": 2026}, "fr")
        self.assertEqual("Les revenus encaissés en 2026 totalisent $650.00 pour 2 activité(s).", result.answer)
        self.assertEqual([["Hockey", "$400.00"], ["Yoga", "$250.00"]], result.rows)

    def test_highest_revenue_uses_collected_cash(self):
        result = highest_revenue_activity({"year": 2026}, "fr")
        self.assertIn("Hockey", result.answer)
        self.assertIn("$400.00", result.answer)
        self.assertEqual([["Hockey", "$400.00"]], result.rows)

    def test_most_profitable_uses_net_income_after_expenses(self):
        result = most_profitable_activity({"year": 2026}, "en")
        self.assertIn("Yoga", result.answer)
        self.assertIn("$250.00", result.answer)
        self.assertEqual([["Yoga", "$250.00"]], result.rows)


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload


class WayneClientTests(unittest.TestCase):
    def test_empty_model_content_is_rejected_cleanly(self):
        response = FakeResponse({
            "choices": [{"message": {"content": None}, "finish_reason": "length"}],
            "usage": {"total_tokens": 300},
        })
        with self.assertRaisesRegex(_RetryableResponseError, "empty response"):
            _parse_response(response, "test-model")

    def test_truncated_model_content_is_rejected_cleanly(self):
        response = FakeResponse({
            "choices": [{"message": {"content": '{"status":'}, "finish_reason": "length"}],
            "usage": {"total_tokens": 300},
        })
        with self.assertRaisesRegex(_RetryableResponseError, "truncated response"):
            _parse_response(response, "test-model")


if __name__ == "__main__":
    unittest.main()
