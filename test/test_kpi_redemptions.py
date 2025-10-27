"""
Unit tests for Passports Redeemed KPI
Tests the new passports_redeemed functionality in get_kpi_data()
"""
import unittest
import sys
import os
from datetime import datetime, timedelta, timezone

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models import db, Activity, Passport, User, Redemption, PassportType
from utils import get_kpi_data


class TestKPIRedemptions(unittest.TestCase):
    """Test cases for Passports Redeemed KPI"""

    def setUp(self):
        """Set up test database before each test"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

        with app.app_context():
            db.create_all()

            # Create test data
            self.now = datetime.now(timezone.utc)

            # Create test user
            user = User(name="Test User", email="test@example.com")
            db.session.add(user)

            # Create test activity
            activity = Activity(
                name="Test Activity",
                type="test",
                created_dt=self.now
            )
            db.session.add(activity)
            db.session.commit()

            self.user_id = user.id
            self.activity_id = activity.id

    def tearDown(self):
        """Clean up after each test"""
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_kpi_structure_includes_passports_redeemed(self):
        """Test that get_kpi_data returns passports_redeemed key"""
        with app.app_context():
            result = get_kpi_data(period='7d')

            # Verify passports_redeemed key exists
            self.assertIn('passports_redeemed', result)

            # Verify structure
            redeemed = result['passports_redeemed']
            self.assertIn('current', redeemed)
            self.assertIn('previous', redeemed)
            self.assertIn('change', redeemed)
            self.assertIn('trend_data', redeemed)

    def test_empty_redemptions_returns_zero(self):
        """Test that empty redemption table returns 0, not None"""
        with app.app_context():
            result = get_kpi_data(period='7d')

            # Should return 0, not None
            self.assertEqual(result['passports_redeemed']['current'], 0)
            self.assertIsInstance(result['passports_redeemed']['trend_data'], list)

    def test_count_redemptions_7d_period(self):
        """Test redemption counting for 7-day period"""
        with app.app_context():
            # Create passport
            passport = Passport(
                pass_code="TEST001",
                user_id=self.user_id,
                activity_id=self.activity_id,
                uses_remaining=5,
                created_dt=self.now - timedelta(days=10)
            )
            db.session.add(passport)
            db.session.commit()

            # Create redemptions in last 7 days
            for i in range(3):
                redemption = Redemption(
                    passport_id=passport.id,
                    date_used=self.now - timedelta(days=i)
                )
                db.session.add(redemption)

            # Create redemption outside 7-day window (should not be counted)
            old_redemption = Redemption(
                passport_id=passport.id,
                date_used=self.now - timedelta(days=10)
            )
            db.session.add(old_redemption)
            db.session.commit()

            result = get_kpi_data(period='7d')

            # Should count only 3 redemptions in last 7 days
            self.assertEqual(result['passports_redeemed']['current'], 3)

    def test_count_redemptions_30d_period(self):
        """Test redemption counting for 30-day period"""
        with app.app_context():
            passport = Passport(
                pass_code="TEST002",
                user_id=self.user_id,
                activity_id=self.activity_id,
                uses_remaining=10,
                created_dt=self.now - timedelta(days=40)
            )
            db.session.add(passport)
            db.session.commit()

            # Create 5 redemptions in last 30 days
            for i in range(5):
                redemption = Redemption(
                    passport_id=passport.id,
                    date_used=self.now - timedelta(days=i*5)
                )
                db.session.add(redemption)

            db.session.commit()

            result = get_kpi_data(period='30d')

            # Should count 5 redemptions
            self.assertEqual(result['passports_redeemed']['current'], 5)

    def test_activity_filtering_works(self):
        """Test that activity_id filtering works correctly"""
        with app.app_context():
            # Create second activity
            activity2 = Activity(
                name="Activity 2",
                type="test",
                created_dt=self.now
            )
            db.session.add(activity2)
            db.session.commit()

            # Create passports for both activities
            passport1 = Passport(
                pass_code="ACTIVITY1",
                user_id=self.user_id,
                activity_id=self.activity_id,
                uses_remaining=5,
                created_dt=self.now - timedelta(days=5)
            )
            passport2 = Passport(
                pass_code="ACTIVITY2",
                user_id=self.user_id,
                activity_id=activity2.id,
                uses_remaining=5,
                created_dt=self.now - timedelta(days=5)
            )
            db.session.add_all([passport1, passport2])
            db.session.commit()

            # Create redemptions for both
            for i in range(3):
                r1 = Redemption(passport_id=passport1.id, date_used=self.now - timedelta(days=i))
                r2 = Redemption(passport_id=passport2.id, date_used=self.now - timedelta(days=i))
                db.session.add_all([r1, r2])
            db.session.commit()

            # Test global count
            result_global = get_kpi_data(period='7d')
            self.assertEqual(result_global['passports_redeemed']['current'], 6)

            # Test activity-specific counts
            result_activity1 = get_kpi_data(activity_id=self.activity_id, period='7d')
            self.assertEqual(result_activity1['passports_redeemed']['current'], 3)

            result_activity2 = get_kpi_data(activity_id=activity2.id, period='7d')
            self.assertEqual(result_activity2['passports_redeemed']['current'], 3)

    def test_percentage_change_calculation(self):
        """Test that percentage change is calculated correctly"""
        with app.app_context():
            passport = Passport(
                pass_code="TEST003",
                user_id=self.user_id,
                activity_id=self.activity_id,
                uses_remaining=20,
                created_dt=self.now - timedelta(days=20)
            )
            db.session.add(passport)
            db.session.commit()

            # Create 2 redemptions in previous period (days 8-14)
            for i in range(2):
                r = Redemption(
                    passport_id=passport.id,
                    date_used=self.now - timedelta(days=10+i)
                )
                db.session.add(r)

            # Create 4 redemptions in current period (last 7 days)
            for i in range(4):
                r = Redemption(
                    passport_id=passport.id,
                    date_used=self.now - timedelta(days=i)
                )
                db.session.add(r)

            db.session.commit()

            result = get_kpi_data(period='7d')

            # Current: 4, Previous: 2, Change should be 100% increase
            self.assertEqual(result['passports_redeemed']['current'], 4)
            self.assertEqual(result['passports_redeemed']['previous'], 2)
            self.assertEqual(result['passports_redeemed']['change'], 100.0)

    def test_trend_data_generation(self):
        """Test that trend data is generated correctly"""
        with app.app_context():
            passport = Passport(
                pass_code="TEST004",
                user_id=self.user_id,
                activity_id=self.activity_id,
                uses_remaining=10,
                created_dt=self.now - timedelta(days=10)
            )
            db.session.add(passport)
            db.session.commit()

            # Create one redemption per day for last 7 days
            for i in range(7):
                r = Redemption(
                    passport_id=passport.id,
                    date_used=self.now - timedelta(days=i)
                )
                db.session.add(r)

            db.session.commit()

            result = get_kpi_data(period='7d')

            # Trend data should be a list of 7 elements
            trend = result['passports_redeemed']['trend_data']
            self.assertIsInstance(trend, list)
            self.assertEqual(len(trend), 7)

            # Each day should have 1 redemption
            self.assertEqual(sum(trend), 7)

    def test_all_period_returns_all_redemptions(self):
        """Test that 'all' period returns all redemptions"""
        with app.app_context():
            passport = Passport(
                pass_code="TEST005",
                user_id=self.user_id,
                activity_id=self.activity_id,
                uses_remaining=100,
                created_dt=self.now - timedelta(days=100)
            )
            db.session.add(passport)
            db.session.commit()

            # Create redemptions across wide time range
            for days_ago in [1, 10, 30, 60, 90]:
                r = Redemption(
                    passport_id=passport.id,
                    date_used=self.now - timedelta(days=days_ago)
                )
                db.session.add(r)

            db.session.commit()

            result = get_kpi_data(period='all')

            # Should count all 5 redemptions
            self.assertEqual(result['passports_redeemed']['current'], 5)
            # For 'all' period, previous and change should be None
            self.assertIsNone(result['passports_redeemed']['previous'])
            self.assertIsNone(result['passports_redeemed']['change'])

    def test_existing_kpis_still_work(self):
        """Regression test: ensure existing KPIs are not broken"""
        with app.app_context():
            result = get_kpi_data(period='7d')

            # All original KPIs should still exist
            self.assertIn('revenue', result)
            self.assertIn('active_users', result)
            self.assertIn('passports_created', result)
            self.assertIn('unpaid_passports', result)

            # And the new one
            self.assertIn('passports_redeemed', result)


if __name__ == '__main__':
    unittest.main(verbosity=2)
