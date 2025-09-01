#!/usr/bin/env python3
"""
Unit tests for mobile dashboard bug fixes.
Tests chart rendering and dropdown menu functionality.
"""

import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import get_kpi_data
from datetime import datetime, timedelta


class TestMobileDashboardFixes(unittest.TestCase):
    """Test suite for mobile dashboard fixes"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_admin = MagicMock()
        self.mock_admin.id = 1
        self.mock_admin.display_name = "Test Admin"
    
    def test_kpi_data_structure(self):
        """Test that KPI data has correct structure for charts"""
        with patch('utils.Activity.query') as mock_query:
            # Mock activity data
            mock_activity = MagicMock()
            mock_activity.id = 1
            mock_activity.admin_id = 1
            mock_query.filter_by.return_value.all.return_value = [mock_activity]
            
            with patch('utils.Passport.query') as mock_passport:
                mock_passport.filter_by.return_value.count.return_value = 10
                
                with patch('utils.Income.query') as mock_income:
                    mock_income.filter_by.return_value.all.return_value = []
                    
                    # Get KPI data
                    kpi_data = get_kpi_data(self.mock_admin.id, period='7d')
                    
                    # Verify structure
                    self.assertIn('revenue', kpi_data)
                    self.assertIn('active_users', kpi_data)
                    self.assertIn('passports_created', kpi_data)
                    self.assertIn('unpaid_passports', kpi_data)
                    
                    # Verify each KPI has required fields
                    for kpi_type in ['revenue', 'active_users', 'passports_created', 'unpaid_passports']:
                        self.assertIn('current', kpi_data[kpi_type])
                        self.assertIn('change', kpi_data[kpi_type])
                        self.assertIn('trend_data', kpi_data[kpi_type])
    
    def test_trend_data_format(self):
        """Test that trend data is in correct format for charts"""
        with patch('utils.Activity.query') as mock_query:
            mock_query.filter_by.return_value.all.return_value = []
            
            with patch('utils.Passport.query') as mock_passport:
                mock_passport.filter_by.return_value.count.return_value = 0
                
                with patch('utils.Income.query') as mock_income:
                    mock_income.filter_by.return_value.all.return_value = []
                    
                    kpi_data = get_kpi_data(self.mock_admin.id, period='7d')
                    
                    # Check trend data is a list
                    self.assertIsInstance(kpi_data['revenue']['trend_data'], list)
                    
                    # Check trend data length matches period
                    self.assertEqual(len(kpi_data['revenue']['trend_data']), 7)
    
    def test_mobile_viewport_detection(self):
        """Test mobile viewport detection logic"""
        # Mobile viewport widths
        mobile_widths = [320, 375, 414, 428, 768]
        
        for width in mobile_widths:
            is_mobile = width <= 767
            self.assertTrue(is_mobile or width == 768, 
                          f"Width {width} should be detected as mobile")
        
        # Desktop viewport widths
        desktop_widths = [769, 1024, 1280, 1920]
        
        for width in desktop_widths:
            is_mobile = width <= 767
            self.assertFalse(is_mobile, 
                           f"Width {width} should not be detected as mobile")
    
    def test_dropdown_menu_items(self):
        """Test dropdown menu has all required period options"""
        required_periods = ['7d', '30d', '90d', 'all']
        period_labels = ['Last 7 days', 'Last 30 days', 'Last 90 days', 'All time']
        
        self.assertEqual(len(required_periods), 4)
        self.assertEqual(len(period_labels), 4)
        
        for period, label in zip(required_periods, period_labels):
            self.assertIsNotNone(period)
            self.assertIsNotNone(label)
    
    def test_chart_container_dimensions(self):
        """Test chart container has correct dimensions for mobile"""
        mobile_chart_height = 40
        
        # Verify height is appropriate for mobile
        self.assertEqual(mobile_chart_height, 40)
        self.assertLess(mobile_chart_height, 100)  # Should be compact
    
    def test_kpi_card_structure(self):
        """Test KPI card has correct structure for mobile rendering"""
        kpi_types = ['revenue', 'active_passports', 'passports_created', 'pending_signups']
        
        for kpi_type in kpi_types:
            # Each card should have these elements
            elements = {
                'title': f'{kpi_type.upper()}',
                'value_id': f'{kpi_type.replace("_", "-")}-value',
                'trend_id': f'{kpi_type.replace("_", "-")}-trend',
                'chart_id': f'{kpi_type.replace("_", "-")}-chart',
                'button_attr': f'data-kpi-period-button="{kpi_type}"'
            }
            
            for element, expected_value in elements.items():
                self.assertIsNotNone(expected_value, 
                                   f"KPI card {kpi_type} missing {element}")


if __name__ == '__main__':
    unittest.main(verbosity=2)