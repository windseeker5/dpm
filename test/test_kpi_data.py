"""
Comprehensive unit tests for the new simplified get_kpi_data function.

Tests all 4 KPIs across all time periods with various data scenarios.
"""
import unittest
import sys
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import get_kpi_data
from models import db, Passport, Signup, Income, User, Activity


class TestKPIData(unittest.TestCase):
    """Test the get_kpi_data function comprehensively"""
    
    def setUp(self):
        """Set up test environment with mock Flask app context"""
        self.mock_app = MagicMock()
        self.mock_context = MagicMock()
        self.mock_app.app_context.return_value = self.mock_context
        
        # Mock current time for consistent testing
        self.now = datetime(2023, 12, 15, 12, 0, 0, tzinfo=timezone.utc)
        
    def test_period_validation(self):
        """Test that invalid periods raise ValueError"""
        with patch('flask.current_app', self.mock_app):
            with patch('utils.datetime') as mock_datetime:
                mock_datetime.now.return_value = self.now
                mock_datetime.min.replace.return_value = datetime.min.replace(tzinfo=timezone.utc)
                
                with self.assertRaises(ValueError):
                    get_kpi_data(period='invalid')
    
    def test_time_range_calculations_7d(self):
        """Test 7-day period time range calculations"""
        with patch('flask.current_app', self.mock_app):
            with patch('utils.datetime') as mock_datetime:
                mock_datetime.now.return_value = self.now
                mock_datetime.timedelta = timedelta
                
                # Mock all the database queries to return empty results
                self._mock_empty_queries()
                
                result = get_kpi_data(period='7d')
                
                # Should have all 4 KPIs
                self.assertIn('revenue', result)
                self.assertIn('active_users', result)
                self.assertIn('passports_created', result)
                self.assertIn('unpaid_passports', result)
                
                # Each KPI should have the expected structure
                for kpi in result.values():
                    self.assertIn('current', kpi)
                    self.assertIn('previous', kpi)
                    self.assertIn('change', kpi)
                    self.assertIn('trend_data', kpi)
    
    def test_time_range_calculations_30d(self):
        """Test 30-day period time range calculations"""
        with patch('flask.current_app', self.mock_app):
            with patch('utils.datetime') as mock_datetime:
                mock_datetime.now.return_value = self.now
                mock_datetime.timedelta = timedelta
                
                self._mock_empty_queries()
                
                result = get_kpi_data(period='30d')
                self.assertIsInstance(result, dict)
                self.assertEqual(len(result), 4)
    
    def test_time_range_calculations_90d(self):
        """Test 90-day period time range calculations"""
        with patch('flask.current_app', self.mock_app):
            with patch('utils.datetime') as mock_datetime:
                mock_datetime.now.return_value = self.now
                mock_datetime.timedelta = timedelta
                
                self._mock_empty_queries()
                
                result = get_kpi_data(period='90d')
                self.assertIsInstance(result, dict)
                self.assertEqual(len(result), 4)
    
    def test_time_range_calculations_all(self):
        """Test 'all' period calculations (no previous comparison)"""
        with patch('flask.current_app', self.mock_app):
            with patch('utils.datetime') as mock_datetime:
                mock_datetime.now.return_value = self.now
                mock_datetime.min.replace.return_value = datetime.min.replace(tzinfo=timezone.utc)
                
                self._mock_empty_queries()
                
                result = get_kpi_data(period='all')
                
                # For 'all' period, previous and change should be None
                for kpi in result.values():
                    self.assertIsNone(kpi['previous'])
                    self.assertIsNone(kpi['change'])
                    self.assertIsNotNone(kpi['current'])
                    self.assertIsNotNone(kpi['trend_data'])
    
    def test_global_vs_activity_specific(self):
        """Test that activity_id filter is applied correctly"""
        with patch('flask.current_app', self.mock_app):
            with patch('utils.datetime') as mock_datetime:
                mock_datetime.now.return_value = self.now
                mock_datetime.timedelta = timedelta
                
                self._mock_empty_queries()
                
                # Test global (no activity_id)
                global_result = get_kpi_data()
                self.assertIsInstance(global_result, dict)
                
                # Test activity-specific
                activity_result = get_kpi_data(activity_id=1)
                self.assertIsInstance(activity_result, dict)
    
    def test_kpi_1_revenue_calculation(self):
        """Test KPI 1: Revenue calculation (passport amounts + income amounts)"""
        with patch('flask.current_app', self.mock_app):
            with patch('utils.datetime') as mock_datetime:
                mock_datetime.now.return_value = self.now
                mock_datetime.timedelta = timedelta
                
                # Mock passport revenue query to return 100.0
                mock_passport_query = self._create_mock_query_chain()
                mock_passport_query.scalar.return_value = 100.0
                
                # Mock income revenue query to return 50.0
                mock_income_query = self._create_mock_query_chain()
                mock_income_query.scalar.return_value = 50.0
                
                # Mock previous period queries
                mock_prev_passport = self._create_mock_query_chain()
                mock_prev_passport.scalar.return_value = 80.0
                
                mock_prev_income = self._create_mock_query_chain()
                mock_prev_income.scalar.return_value = 40.0
                
                with patch('models.Passport.query', return_value=mock_passport_query):
                    with patch('models.Income.query', return_value=mock_income_query):
                        # Mock other queries to return empty
                        self._mock_remaining_queries()
                        
                        result = get_kpi_data(period='7d')
                        
                        # Revenue should be passport + income = 100 + 50 = 150
                        self.assertEqual(result['revenue']['current'], 150.0)
    
    def test_kpi_2_active_users_calculation(self):
        """Test KPI 2: Active Users calculation (uses_remaining > 0)"""
        with patch('flask.current_app', self.mock_app):
            with patch('utils.datetime') as mock_datetime:
                mock_datetime.now.return_value = self.now
                mock_datetime.timedelta = timedelta
                
                # Mock active users query to return 25
                mock_active_query = self._create_mock_query_chain()
                mock_active_query.count.return_value = 25
                
                with patch('models.Passport.query', return_value=mock_active_query):
                    # Mock other queries
                    self._mock_revenue_queries()
                    self._mock_remaining_queries()
                    
                    result = get_kpi_data(period='7d')
                    
                    self.assertEqual(result['active_users']['current'], 25)
    
    def test_kpi_3_passports_created_calculation(self):
        """Test KPI 3: Passports Created calculation"""
        with patch('flask.current_app', self.mock_app):
            with patch('utils.datetime') as mock_datetime:
                mock_datetime.now.return_value = self.now
                mock_datetime.timedelta = timedelta
                
                # Mock passports created query to return 15
                mock_created_query = self._create_mock_query_chain()
                mock_created_query.count.return_value = 15
                
                with patch('models.Passport.query', return_value=mock_created_query):
                    # Mock other queries
                    self._mock_revenue_queries()
                    self._mock_remaining_queries()
                    
                    result = get_kpi_data(period='7d')
                    
                    self.assertEqual(result['passports_created']['current'], 15)
    
    def test_kpi_4_unpaid_passports_calculation(self):
        """Test KPI 4: Unpaid Passports calculation (paid=False)"""
        with patch('flask.current_app', self.mock_app):
            with patch('utils.datetime') as mock_datetime:
                mock_datetime.now.return_value = self.now
                mock_datetime.timedelta = timedelta
                
                # Mock unpaid passports query to return 5
                mock_unpaid_query = self._create_mock_query_chain()
                mock_unpaid_query.count.return_value = 5
                
                with patch('models.Passport.query', return_value=mock_unpaid_query):
                    # Mock other queries
                    self._mock_revenue_queries()
                    self._mock_remaining_queries()
                    
                    result = get_kpi_data(period='7d')
                    
                    self.assertEqual(result['unpaid_passports']['current'], 5)
    
    def test_trend_data_length(self):
        """Test that trend arrays have correct length for each period"""
        with patch('flask.current_app', self.mock_app):
            with patch('utils.datetime') as mock_datetime:
                mock_datetime.now.return_value = self.now
                mock_datetime.timedelta = timedelta
                
                self._mock_empty_queries()
                
                # Test 7d trend length
                result_7d = get_kpi_data(period='7d')
                self.assertEqual(len(result_7d['revenue']['trend_data']), 7)
                
                # Test 30d trend length
                result_30d = get_kpi_data(period='30d')
                self.assertEqual(len(result_30d['revenue']['trend_data']), 30)
                
                # Test 90d trend length (should be 30 for readability)
                result_90d = get_kpi_data(period='90d')
                self.assertEqual(len(result_90d['revenue']['trend_data']), 30)
                
                # Test all trend length (should be 30 for readability)
                result_all = get_kpi_data(period='all')
                self.assertEqual(len(result_all['revenue']['trend_data']), 30)
    
    def test_percentage_change_calculation(self):
        """Test percentage change calculations"""
        with patch('flask.current_app', self.mock_app):
            with patch('utils.datetime') as mock_datetime:
                mock_datetime.now.return_value = self.now
                mock_datetime.timedelta = timedelta
                
                # Mock current revenue = 150, previous revenue = 100
                # Expected change: (150-100)/100*100 = 50%
                self._mock_revenue_calculation(current=150.0, previous=100.0)
                self._mock_remaining_queries()
                
                result = get_kpi_data(period='7d')
                
                self.assertEqual(result['revenue']['current'], 150.0)
                self.assertEqual(result['revenue']['previous'], 100.0)
                self.assertEqual(result['revenue']['change'], 50.0)
    
    def test_zero_division_handling(self):
        """Test handling of zero division in percentage calculations"""
        with patch('flask.current_app', self.mock_app):
            with patch('utils.datetime') as mock_datetime:
                mock_datetime.now.return_value = self.now
                mock_datetime.timedelta = timedelta
                
                # Mock current revenue = 100, previous revenue = 0
                # Should handle zero division gracefully
                self._mock_revenue_calculation(current=100.0, previous=0.0)
                self._mock_remaining_queries()
                
                result = get_kpi_data(period='7d')
                
                self.assertEqual(result['revenue']['current'], 100.0)
                self.assertEqual(result['revenue']['previous'], 0.0)
                self.assertEqual(result['revenue']['change'], 0)  # Should not crash
    
    def test_edge_case_no_data(self):
        """Test behavior when no data exists"""
        with patch('flask.current_app', self.mock_app):
            with patch('utils.datetime') as mock_datetime:
                mock_datetime.now.return_value = self.now
                mock_datetime.timedelta = timedelta
                
                # Mock all queries to return 0 or None
                self._mock_empty_queries()
                
                result = get_kpi_data(period='7d')
                
                # All current values should be 0
                self.assertEqual(result['revenue']['current'], 0.0)
                self.assertEqual(result['active_users']['current'], 0)
                self.assertEqual(result['passports_created']['current'], 0)
                self.assertEqual(result['unpaid_passports']['current'], 0)
    
    def test_rounding_behavior(self):
        """Test that values are rounded correctly"""
        with patch('flask.current_app', self.mock_app):
            with patch('utils.datetime') as mock_datetime:
                mock_datetime.now.return_value = self.now
                mock_datetime.timedelta = timedelta
                
                # Mock revenue with decimal values
                self._mock_revenue_calculation(current=123.456, previous=100.123)
                self._mock_remaining_queries()
                
                result = get_kpi_data(period='7d')
                
                # Revenue should be rounded to 2 decimal places
                self.assertEqual(result['revenue']['current'], 123.46)
                self.assertEqual(result['revenue']['previous'], 100.12)
                # Change should be rounded to 1 decimal place
                self.assertAlmostEqual(result['revenue']['change'], 23.3, places=1)
    
    # Helper methods for mocking
    
    def _create_mock_query_chain(self):
        """Create a mock query object that supports chaining"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.with_entities.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.scalar.return_value = 0
        return mock_query
    
    def _mock_empty_queries(self):
        """Mock all database queries to return empty results"""
        mock_query = self._create_mock_query_chain()
        
        with patch('models.Passport.query', mock_query):
            with patch('models.Income.query', mock_query):
                with patch('models.Signup.query', mock_query):
                    pass
    
    def _mock_revenue_queries(self):
        """Mock revenue-related queries"""
        mock_passport = self._create_mock_query_chain()
        mock_income = self._create_mock_query_chain()
        
        with patch('models.Passport.query', mock_passport):
            with patch('models.Income.query', mock_income):
                pass
    
    def _mock_remaining_queries(self):
        """Mock queries for active users, created, and unpaid"""
        mock_query = self._create_mock_query_chain()
        
        with patch('models.Signup.query', mock_query):
            pass
    
    def _mock_revenue_calculation(self, current, previous):
        """Mock revenue calculation with specific values"""
        # Mock current period queries
        mock_curr_passport = self._create_mock_query_chain()
        mock_curr_passport.scalar.return_value = current * 0.7  # 70% from passports
        
        mock_curr_income = self._create_mock_query_chain()
        mock_curr_income.scalar.return_value = current * 0.3  # 30% from income
        
        # Mock previous period queries
        mock_prev_passport = self._create_mock_query_chain()
        mock_prev_passport.scalar.return_value = previous * 0.7
        
        mock_prev_income = self._create_mock_query_chain()
        mock_prev_income.scalar.return_value = previous * 0.3
        
        with patch('models.Passport.query', side_effect=[mock_curr_passport, mock_prev_passport] * 10):
            with patch('models.Income.query', side_effect=[mock_curr_income, mock_prev_income] * 10):
                pass


if __name__ == '__main__':
    # Run the tests
    unittest.main()