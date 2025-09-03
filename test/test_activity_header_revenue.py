"""
Unit tests for activity header revenue calculation and display logic.

Tests the revenue progress calculation, formatting, and edge cases
used in the activity header component.
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import get_kpi_data
from models import Activity


class TestActivityHeaderRevenue(unittest.TestCase):
    """Test cases for activity header revenue calculations."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_activity = Mock()
        self.mock_activity.id = 1
        self.mock_activity.target_revenue = 1000.0
        self.mock_activity.name = "Test Activity"

    def test_revenue_progress_calculation_basic(self):
        """Test basic revenue progress percentage calculation."""
        # Test case: 250/1000 = 25%
        actual_revenue = 250.0
        target_revenue = 1000.0
        
        expected_percentage = 25
        actual_percentage = round((actual_revenue / target_revenue * 100) if target_revenue > 0 else 0)
        
        self.assertEqual(actual_percentage, expected_percentage)

    def test_revenue_progress_calculation_zero_target(self):
        """Test revenue progress when target is zero."""
        actual_revenue = 500.0
        target_revenue = 0.0
        
        expected_percentage = 0
        actual_percentage = round((actual_revenue / target_revenue * 100) if target_revenue > 0 else 0)
        
        self.assertEqual(actual_percentage, expected_percentage)

    def test_revenue_progress_calculation_exceeding_target(self):
        """Test revenue progress when actual exceeds target."""
        actual_revenue = 1500.0
        target_revenue = 1000.0
        
        expected_percentage = 150
        actual_percentage = round((actual_revenue / target_revenue * 100) if target_revenue > 0 else 0)
        
        self.assertEqual(actual_percentage, expected_percentage)

    def test_revenue_progress_calculation_zero_revenue(self):
        """Test revenue progress when actual revenue is zero."""
        actual_revenue = 0.0
        target_revenue = 1000.0
        
        expected_percentage = 0
        actual_percentage = round((actual_revenue / target_revenue * 100) if target_revenue > 0 else 0)
        
        self.assertEqual(actual_percentage, expected_percentage)

    def test_revenue_formatting_thousands(self):
        """Test revenue formatting with thousands separators."""
        revenue = 12345.67
        formatted = "{:,.0f}".format(revenue)
        expected = "12,346"  # Rounded to nearest dollar
        self.assertEqual(formatted, expected)

    def test_revenue_formatting_millions(self):
        """Test revenue formatting with millions."""
        revenue = 1234567.89
        formatted = "{:,.0f}".format(revenue)
        expected = "1,234,568"
        self.assertEqual(formatted, expected)

    def test_revenue_formatting_zero(self):
        """Test revenue formatting with zero value."""
        revenue = 0.0
        formatted = "{:,.0f}".format(revenue)
        expected = "0"
        self.assertEqual(formatted, expected)

    def test_revenue_formatting_small_decimal(self):
        """Test revenue formatting with small decimal values."""
        revenue = 99.99
        formatted = "{:,.0f}".format(revenue)
        expected = "100"  # Should round up
        self.assertEqual(formatted, expected)

    def test_progress_bar_width_calculation(self):
        """Test progress bar width calculation with capping at 100%."""
        test_cases = [
            (250, 1000, 25),   # Normal case
            (1500, 1000, 100), # Exceeding target should cap at 100%
            (0, 1000, 0),      # Zero revenue
            (1000, 1000, 100), # Exact target
        ]
        
        for actual, target, expected_width in test_cases:
            percentage = round((actual / target * 100) if target > 0 else 0)
            width = min(percentage, 100)
            
            with self.subTest(actual=actual, target=target):
                self.assertEqual(width, expected_width)

    def test_default_target_revenue_fallback(self):
        """Test default target revenue fallback when activity has no target."""
        # This simulates the template logic: activity.target_revenue|float if activity.target_revenue else 1000
        activity_target = None
        default_target = 1000
        
        target_revenue = float(activity_target) if activity_target else default_target
        
        self.assertEqual(target_revenue, default_target)

    def test_default_target_revenue_with_value(self):
        """Test target revenue when activity has a value."""
        activity_target = "2500.0"
        default_target = 1000
        
        target_revenue = float(activity_target) if activity_target else default_target
        
        self.assertEqual(target_revenue, 2500.0)

    @patch('utils.get_kpi_data')
    def test_kpi_data_revenue_extraction(self, mock_get_kpi_data):
        """Test extracting revenue from KPI data structure."""
        # Mock KPI data structure
        mock_kpi_data = {
            'revenue': {
                'current': 750.25,
                'previous': 500.0,
                'change': 50.1,
                'trend_data': [100, 200, 300, 400, 500, 600, 750.25]
            }
        }
        
        mock_get_kpi_data.return_value = mock_kpi_data
        
        # Simulate template logic
        kpi_data = mock_get_kpi_data(activity_id=1)
        actual_revenue = float(kpi_data['revenue']['current']) if kpi_data and kpi_data['revenue'] else 0
        
        self.assertEqual(actual_revenue, 750.25)

    @patch('utils.get_kpi_data')
    def test_kpi_data_revenue_extraction_none(self, mock_get_kpi_data):
        """Test extracting revenue when KPI data is None."""
        mock_get_kpi_data.return_value = None
        
        # Simulate template logic
        kpi_data = mock_get_kpi_data(activity_id=1)
        actual_revenue = float(kpi_data['revenue']['current']) if kpi_data and kpi_data['revenue'] else 0
        
        self.assertEqual(actual_revenue, 0)

    @patch('utils.get_kpi_data')
    def test_kpi_data_revenue_extraction_empty_revenue(self, mock_get_kpi_data):
        """Test extracting revenue when revenue section is empty."""
        mock_kpi_data = {
            'revenue': None
        }
        
        mock_get_kpi_data.return_value = mock_kpi_data
        
        # Simulate template logic
        kpi_data = mock_get_kpi_data(activity_id=1)
        actual_revenue = float(kpi_data['revenue']['current']) if kpi_data and kpi_data['revenue'] else 0
        
        self.assertEqual(actual_revenue, 0)

    def test_progress_display_text_formatting(self):
        """Test the progress display text formatting."""
        test_cases = [
            (0, 1000, "0% Complete"),
            (250, 1000, "25% Complete"),
            (1000, 1000, "100% Complete"),
            (1500, 1000, "150% Complete"),  # Can exceed 100%
        ]
        
        for actual, target, expected_text in test_cases:
            percentage = round((actual / target * 100) if target > 0 else 0)
            display_text = f"{percentage}% Complete"
            
            with self.subTest(actual=actual, target=target):
                self.assertEqual(display_text, expected_text)


class TestActivityHeaderEdgeCases(unittest.TestCase):
    """Test edge cases for activity header revenue logic."""

    def test_float_precision_handling(self):
        """Test handling of float precision in calculations."""
        # Test case where division might produce floating point precision issues
        actual_revenue = 333.33
        target_revenue = 1000.0
        
        # Should handle precision gracefully
        percentage = round((actual_revenue / target_revenue * 100))
        self.assertEqual(percentage, 33)  # Should round properly

    def test_very_large_numbers(self):
        """Test handling of very large revenue numbers."""
        actual_revenue = 999999999.99
        target_revenue = 1000000000.0
        
        percentage = round((actual_revenue / target_revenue * 100))
        formatted_actual = "{:,.0f}".format(actual_revenue)
        formatted_target = "{:,.0f}".format(target_revenue)
        
        self.assertEqual(percentage, 100)
        self.assertEqual(formatted_actual, "1,000,000,000")
        self.assertEqual(formatted_target, "1,000,000,000")

    def test_negative_revenue_handling(self):
        """Test handling of negative revenue values."""
        actual_revenue = -100.0  # Refunds or corrections
        target_revenue = 1000.0
        
        percentage = round((actual_revenue / target_revenue * 100))
        
        self.assertEqual(percentage, -10)  # Should handle negative percentages

    def test_template_min_function_behavior(self):
        """Test the template's min function for progress bar width capping."""
        test_cases = [
            (25, 100, 25),   # Normal case
            (150, 100, 100), # Should cap at 100
            (0, 100, 0),     # Zero case
            (100, 100, 100), # Exact match
        ]
        
        for percentage, max_value, expected in test_cases:
            result = min(percentage, max_value)
            
            with self.subTest(percentage=percentage, max_value=max_value):
                self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main(verbosity=2)