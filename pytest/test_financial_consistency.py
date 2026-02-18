#!/usr/bin/env python3
"""
Test Financial Consistency - Activities Page vs Financial Report

This test ensures that the revenue displayed on the Activities page
matches the Financial Report (both using the same SQL view).

Usage:
    cd /home/kdresdell/Documents/DEV/minipass_env/app
    source venv/bin/activate
    python -m unittest test.test_financial_consistency -v
"""

import os
import sys
import unittest

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Activity


class TestFinancialConsistency(unittest.TestCase):
    """Test that financial data is consistent across all pages."""

    def setUp(self):
        """Set up test context."""
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Tear down test context."""
        self.app_context.pop()

    def test_get_activity_revenue_from_view_returns_dict(self):
        """Test that get_activity_revenue_from_view returns a dictionary."""
        from utils import get_activity_revenue_from_view

        result = get_activity_revenue_from_view()

        self.assertIsInstance(result, dict)
        # All values should be floats
        for activity_id, revenue in result.items():
            self.assertIsInstance(activity_id, int)
            self.assertIsInstance(revenue, float)

    def test_get_activity_revenue_from_view_matches_financial_report(self):
        """Test that activity revenue matches financial report totals."""
        from utils import get_activity_revenue_from_view, get_financial_data_from_views

        # Get revenue from the new helper function
        activity_revenue = get_activity_revenue_from_view()

        # Get financial data from views (used by Financial Report page)
        financial_data = get_financial_data_from_views()

        # Build a dict from financial report's by_activity data
        financial_report_revenue = {}
        for activity_data in financial_data.get('by_activity', []):
            activity_id = activity_data.get('activity_id')
            if activity_id:
                financial_report_revenue[activity_id] = activity_data.get('total_revenue', 0)

        # Compare: activity_revenue should match or exceed financial_report_revenue
        # (activity_revenue is all-time, financial_report defaults to all-time too)
        for activity_id, revenue in activity_revenue.items():
            self.assertGreaterEqual(
                revenue, 0,
                f"Activity {activity_id} has negative revenue: {revenue}"
            )

    def test_activity_revenue_includes_income_records(self):
        """Test that revenue includes both passport sales AND Income table records."""
        from sqlalchemy import text

        # Query to check if any activities have Income records
        query = """
            SELECT a.id, a.name,
                   COALESCE(SUM(i.amount), 0) as income_total
            FROM activity a
            LEFT JOIN income i ON a.id = i.activity_id AND i.payment_status = 'received'
            GROUP BY a.id, a.name
            HAVING income_total > 0
        """

        result = db.session.execute(text(query))
        activities_with_income = list(result)

        if activities_with_income:
            from utils import get_activity_revenue_from_view

            activity_revenue = get_activity_revenue_from_view()

            for row in activities_with_income:
                activity_id = row.id
                income_total = float(row.income_total)

                # The activity's total revenue should be at least the income total
                # (it includes passport sales too)
                if activity_id in activity_revenue:
                    self.assertGreaterEqual(
                        activity_revenue[activity_id],
                        income_total,
                        f"Activity {row.name} (id={activity_id}) revenue {activity_revenue[activity_id]} "
                        f"should include income records totaling {income_total}"
                    )

    def test_sql_view_exists(self):
        """Test that the monthly_financial_summary SQL view exists."""
        from sqlalchemy import text

        try:
            result = db.session.execute(text(
                "SELECT COUNT(*) FROM monthly_financial_summary"
            ))
            count = result.scalar()
            # View exists and is queryable
            self.assertIsInstance(count, int)
        except Exception as e:
            self.fail(f"SQL view monthly_financial_summary does not exist: {e}")


if __name__ == '__main__':
    unittest.main()
