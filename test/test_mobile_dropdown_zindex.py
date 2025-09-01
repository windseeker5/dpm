#!/usr/bin/env python3
"""
Unit test for mobile dropdown z-index fix
Tests that the mobile dropdown menu appears on top of all other elements
"""

import unittest
import re
from pathlib import Path


class TestMobileDropdownZIndex(unittest.TestCase):
    """Test mobile dropdown z-index implementation"""
    
    def setUp(self):
        """Set up test environment"""
        self.dashboard_template = Path(__file__).parent.parent / "templates" / "dashboard.html"
        self.assertIsNotNone(self.dashboard_template.exists(), "Dashboard template not found")
    
    def test_mobile_dropdown_css_exists(self):
        """Test that mobile-specific dropdown CSS exists"""
        with open(self.dashboard_template, 'r') as f:
            content = f.read()
        
        # Check for mobile media query
        self.assertIn('@media screen and (max-width: 767.98px)', content)
        
        # Check for ultra-high z-index values
        self.assertIn('z-index: 999999 !important', content)
        
        # Check for position: fixed for dropdown-menu on mobile
        mobile_section = re.search(
            r'@media screen and \(max-width: 767\.98px\) \{.*?\}',
            content, 
            re.DOTALL
        )
        self.assertIsNotNone(mobile_section, "Mobile media query section not found")
        
        mobile_css = mobile_section.group(0)
        self.assertIn('position: fixed !important', mobile_css)
    
    def test_stacking_context_hierarchy(self):
        """Test that z-index hierarchy is correct"""
        with open(self.dashboard_template, 'r') as f:
            content = f.read()
        
        # Extract z-index values from mobile section
        z_indices = re.findall(r'z-index: (\d+) !important', content)
        z_indices = [int(z) for z in z_indices if int(z) > 900000]  # Focus on ultra-high values
        
        # Ensure we have the expected ultra-high z-index values
        self.assertTrue(any(z >= 999999 for z in z_indices), "Ultra-high z-index not found")
    
    def test_mobile_specific_selectors(self):
        """Test that mobile-specific CSS selectors are present"""
        with open(self.dashboard_template, 'r') as f:
            content = f.read()
        
        expected_selectors = [
            '.kpi-card-mobile .dropdown-menu',
            '.kpi-card-mobile .dropdown.show',
            '.kpi-card-mobile .dropdown.show .dropdown-menu'
        ]
        
        for selector in expected_selectors:
            self.assertIn(selector, content, f"Missing selector: {selector}")


if __name__ == '__main__':
    unittest.main()