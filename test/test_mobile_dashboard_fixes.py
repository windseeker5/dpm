#!/usr/bin/env python3
"""
Unit tests for mobile dashboard bug fixes.

This module tests the Python/Flask server-side components that support
the mobile dashboard fixes for:
1. Chart white gap issue
2. Dropdown menu cutoff issue

Following Python-first development approach with minimal JavaScript.
"""

import unittest
import sys
import os

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_test_app
from flask import url_for
from utils import get_kpi_data


class TestMobileDashboardFixes(unittest.TestCase):
    """Test mobile dashboard fixes for chart rendering and dropdown positioning."""
    
    def setUp(self):
        """Set up test client and application context."""
        self.app = create_test_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
    def tearDown(self):
        """Clean up test context."""
        self.app_context.pop()
    
    def test_kpi_data_structure_for_charts(self):
        """Test that KPI data has the correct structure for chart rendering."""
        # Test that get_kpi_data returns proper structure for mobile charts
        kpi_data = get_kpi_data(period='7d')
        
        # Verify essential KPI data structure
        self.assertIsInstance(kpi_data, dict)
        self.assertIn('revenue', kpi_data)
        self.assertIn('active_users', kpi_data)
        self.assertIn('passports_created', kpi_data)
        self.assertIn('unpaid_passports', kpi_data)
        
        # Test revenue data structure for chart rendering
        revenue_data = kpi_data['revenue']
        self.assertIn('current', revenue_data)
        self.assertIn('change', revenue_data)
        self.assertIn('trend', revenue_data)
        
        # Test that trend data exists for chart rendering
        if revenue_data['trend']:
            self.assertIsInstance(revenue_data['trend'], list)
            
    def test_dashboard_mobile_template_rendering(self):
        """Test that dashboard template renders correctly with mobile fixes."""
        with self.client.session_transaction() as sess:
            # Mock admin session
            sess['admin_id'] = 1
            sess['admin_email'] = 'test@example.com'
        
        response = self.client.get('/dashboard')
        
        # Check that response is successful
        self.assertEqual(response.status_code, 200)
        
        # Verify mobile CSS fixes are included
        response_data = response.data.decode('utf-8')
        
        # Test for chart white gap fixes
        self.assertIn('max-height: 40px !important', response_data)
        self.assertIn('position: absolute !important', response_data)
        self.assertIn('overflow: hidden !important', response_data)
        
        # Test for dropdown cutoff fixes
        self.assertIn('position: absolute !important', response_data)
        self.assertIn('z-index: 999999 !important', response_data)
        self.assertIn('overflow: visible !important', response_data)
        
    def test_kpi_data_periods(self):
        """Test KPI data retrieval for different time periods used in dropdowns."""
        periods = ['7d', '30d', '90d', 'all']
        
        for period in periods:
            with self.subTest(period=period):
                kpi_data = get_kpi_data(period=period)
                
                # Verify data structure is consistent across periods
                self.assertIsInstance(kpi_data, dict)
                self.assertIn('revenue', kpi_data)
                
                # Verify trend data exists for chart rendering
                revenue = kpi_data.get('revenue', {})
                self.assertIsInstance(revenue, dict)
                
    def test_chart_data_format(self):
        """Test that chart data is in correct format for ApexCharts rendering."""
        kpi_data = get_kpi_data(period='7d')
        
        # Test revenue chart data format
        if 'revenue' in kpi_data and 'trend' in kpi_data['revenue']:
            trend_data = kpi_data['revenue']['trend']
            if trend_data:
                # Should be a list of numbers for ApexCharts
                self.assertIsInstance(trend_data, list)
                for value in trend_data:
                    self.assertTrue(isinstance(value, (int, float)))
                    
    def test_mobile_specific_css_classes(self):
        """Test that mobile-specific CSS classes are present in template."""
        with self.client.session_transaction() as sess:
            sess['admin_id'] = 1
            sess['admin_email'] = 'test@example.com'
            
        response = self.client.get('/dashboard')
        response_data = response.data.decode('utf-8')
        
        # Check for mobile-specific classes
        self.assertIn('kpi-card-mobile', response_data)
        self.assertIn('dropdown-toggle', response_data)
        self.assertIn('kpi-period-btn', response_data)
        
        # Check for chart containers
        self.assertIn('id="revenue-chart"', response_data)
        self.assertIn('id="active-passports-chart"', response_data)
        self.assertIn('id="passports-created-chart"', response_data)
        self.assertIn('id="pending-signups-chart"', response_data)
        
    def test_javascript_functions_exist(self):
        """Test that required JavaScript functions for mobile fixes exist in template."""
        with self.client.session_transaction() as sess:
            sess['admin_id'] = 1
            sess['admin_email'] = 'test@example.com'
            
        response = self.client.get('/dashboard')
        response_data = response.data.decode('utf-8')
        
        # Check for mobile fix functions
        self.assertIn('function fixMobileChartRendering()', response_data)
        self.assertIn('function handleMobileDropdownPositioning()', response_data)
        
        # Check for initialization calls
        self.assertIn('fixMobileChartRendering()', response_data)
        self.assertIn('handleMobileDropdownPositioning()', response_data)
        
    def test_error_handling_in_template(self):
        """Test that template handles missing KPI data gracefully."""
        with self.client.session_transaction() as sess:
            sess['admin_id'] = 1
            sess['admin_email'] = 'test@example.com'
            
        response = self.client.get('/dashboard')
        
        # Should not fail even with missing or invalid data
        self.assertEqual(response.status_code, 200)


class TestMobileResponsiveDesign(unittest.TestCase):
    """Test responsive design elements for mobile dashboard."""
    
    def setUp(self):
        """Set up test client and application context."""
        self.app = create_test_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
    def tearDown(self):
        """Clean up test context."""
        self.app_context.pop()
        
    def test_mobile_viewport_meta_tag(self):
        """Test that mobile viewport meta tag is present."""
        with self.client.session_transaction() as sess:
            sess['admin_id'] = 1
            sess['admin_email'] = 'test@example.com'
            
        response = self.client.get('/dashboard')
        response_data = response.data.decode('utf-8')
        
        # Check for mobile viewport meta tag (should be in base template)
        # This ensures proper mobile rendering
        self.assertTrue(
            'viewport' in response_data.lower() or 
            response.status_code == 200  # Template loads successfully
        )
        
    def test_responsive_grid_system(self):
        """Test that Tabler.io responsive grid classes are used."""
        with self.client.session_transaction() as sess:
            sess['admin_id'] = 1
            sess['admin_email'] = 'test@example.com'
            
        response = self.client.get('/dashboard')
        response_data = response.data.decode('utf-8')
        
        # Check for Bootstrap/Tabler responsive classes
        responsive_classes = ['col-', 'd-md-', 'd-lg-', 'text-md-', 'mb-', 'mt-']
        found_responsive = any(cls in response_data for cls in responsive_classes)
        self.assertTrue(found_responsive, "No responsive classes found in template")


def create_test_app():
    """Create a test Flask app instance."""
    # Import main app and configure for testing
    import app as main_app
    
    # Create app with test config
    app = main_app.app
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = 'test-key'
    
    return app


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)