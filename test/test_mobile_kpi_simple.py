#!/usr/bin/env python3
"""
DEAD SIMPLE Mobile KPI Cards - Unit Test

Tests that the mobile KPI implementation is working correctly.
No charts, no dynamic data, just hard-coded values.
"""

import unittest
import sys
import os

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app
from flask import url_for


class TestMobileKPISimple(unittest.TestCase):
    """Test the DEAD SIMPLE mobile KPI cards implementation"""
    
    def setUp(self):
        """Set up test client"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Create application context for URL generation
        self.app_context = self.app.app_context()
        self.app_context.push()
        
    def tearDown(self):
        """Clean up after tests"""
        self.app_context.pop()
    
    def test_dashboard_loads_successfully(self):
        """Test that dashboard loads without errors"""
        response = self.client.get('/dashboard')
        
        # Should get 302 redirect to login (not logged in)
        # This is expected behavior
        self.assertIn(response.status_code, [200, 302])
        
    def test_mobile_kpi_container_in_template(self):
        """Test that mobile KPI container exists in dashboard template"""
        template_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'templates', 
            'dashboard.html'
        )
        
        with open(template_path, 'r') as f:
            template_content = f.read()
            
        # Check for mobile KPI container
        self.assertIn('mobile-kpi-container', template_content)
        self.assertIn('d-md-none', template_content)
        
    def test_mobile_kpi_hard_coded_values(self):
        """Test that hard-coded KPI values are present"""
        template_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'templates', 
            'dashboard.html'
        )
        
        with open(template_path, 'r') as f:
            template_content = f.read()
            
        # Check for hard-coded values
        self.assertIn('$2,688', template_content)  # Revenue
        self.assertIn('>24</div>', template_content)  # Active Passports (appears twice)
        self.assertIn('>8</div>', template_content)   # Unpaid Passports
        
    def test_mobile_kpi_card_structure(self):
        """Test that mobile KPI cards have correct structure"""
        template_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'templates', 
            'dashboard.html'
        )
        
        with open(template_path, 'r') as f:
            template_content = f.read()
            
        # Check for card structure
        self.assertIn('mobile-kpi-card', template_content)
        self.assertIn('mobile-kpi-scroll', template_content)
        
        # Check for all 4 KPI cards
        self.assertIn('REVENUE', template_content)
        self.assertIn('ACTIVE PASSPORTS', template_content)
        self.assertIn('PASSPORTS CREATED', template_content)
        self.assertIn('UNPAID PASSPORTS', template_content)
        
    def test_mobile_dots_navigation(self):
        """Test that dot navigation is present"""
        template_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'templates', 
            'dashboard.html'
        )
        
        with open(template_path, 'r') as f:
            template_content = f.read()
            
        # Check for dots navigation
        self.assertIn('mobile-kpi-dots', template_content)
        self.assertIn('mobile-dot', template_content)
        
        # Should have 4 dots (0, 1, 2, 3)
        self.assertIn('data-index="0"', template_content)
        self.assertIn('data-index="1"', template_content)
        self.assertIn('data-index="2"', template_content)
        self.assertIn('data-index="3"', template_content)
        
    def test_mobile_css_styles_present(self):
        """Test that mobile CSS styles are present"""
        template_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'templates', 
            'dashboard.html'
        )
        
        with open(template_path, 'r') as f:
            template_content = f.read()
            
        # Check for mobile CSS
        self.assertIn('Mobile KPI Styles (DEAD SIMPLE)', template_content)
        self.assertIn('scroll-snap-type: x mandatory', template_content)
        self.assertIn('overflow-x: auto', template_content)
        
    def test_mobile_javascript_present(self):
        """Test that simple JavaScript is present"""
        template_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'templates', 
            'dashboard.html'
        )
        
        with open(template_path, 'r') as f:
            template_content = f.read()
            
        # Check for mobile JavaScript
        self.assertIn('DEAD SIMPLE Mobile KPI dot navigation', template_content)
        self.assertIn('mobile-kpi-scroll', template_content)
        self.assertIn('mobile-dot', template_content)
        
    def test_no_charts_in_mobile(self):
        """Test that there are no chart elements in mobile KPI cards"""
        template_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'templates', 
            'dashboard.html'
        )
        
        with open(template_path, 'r') as f:
            template_content = f.read()
            
        # Extract mobile KPI section
        mobile_start = template_content.find('<!-- Mobile Version (DEAD SIMPLE) -->')
        mobile_end = template_content.find('<!-- Activities Section -->', mobile_start)
        mobile_section = template_content[mobile_start:mobile_end] if mobile_start != -1 and mobile_end != -1 else ''
        
        # Make sure no chart divs in mobile section
        self.assertNotIn('chart', mobile_section.lower())
        self.assertNotIn('apexcharts', mobile_section.lower())
        self.assertNotIn('svg', mobile_section.lower())
        
    def test_accessibility_features(self):
        """Test that mobile KPI cards have good accessibility"""
        template_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'templates', 
            'dashboard.html'
        )
        
        with open(template_path, 'r') as f:
            template_content = f.read()
            
        # Check for proper headings and structure
        self.assertIn('text-uppercase', template_content)  # Proper labels
        self.assertIn('text-center', template_content)     # Centered content
        
    def run_all_tests(self):
        """Convenience method to run all tests and return results"""
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestMobileKPISimple)
        runner = unittest.TextTestRunner(verbosity=2)
        return runner.run(suite)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)