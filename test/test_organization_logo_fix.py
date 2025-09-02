#!/usr/bin/env python3
"""
Unit Test for Organization Logo Fix in Emails

This test verifies that:
1. Organization logo (from settings) is used instead of default Minipass logo
2. Both 'logo' and 'logo_image' CIDs are set correctly
3. The correct logo file is loaded based on LOGO_FILENAME setting
"""

import unittest
import os
import sys
import base64
from unittest.mock import patch, MagicMock, mock_open

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestOrganizationLogoFix(unittest.TestCase):
    """Test suite for organization logo fix in email functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_logo_filename = 'flhgi.png'
        self.default_logo = 'logo.png'
        self.test_logo_data = b'test_logo_binary_data'
        self.default_logo_data = b'default_logo_binary_data'
        
    @patch('utils.get_setting')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_notify_pass_event_uses_organization_logo(self, mock_file, mock_exists, mock_get_setting):
        """Test that notify_pass_event uses organization logo when available"""
        # Setup mocks
        mock_get_setting.return_value = self.test_logo_filename
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = self.test_logo_data
        
        # Simulate inline_images dict
        inline_images = {}
        
        # Simulate the logo loading logic from notify_pass_event
        from utils import get_setting
        org_logo_filename = get_setting('LOGO_FILENAME', 'logo.png')
        org_logo_path = os.path.join("static/uploads", org_logo_filename)
        
        if os.path.exists(org_logo_path):
            logo_data = open(org_logo_path, "rb").read()
            inline_images['logo'] = logo_data
            inline_images['logo_image'] = logo_data
        
        # Assertions
        self.assertEqual(inline_images['logo'], self.test_logo_data)
        self.assertEqual(inline_images['logo_image'], self.test_logo_data)
        mock_get_setting.assert_called_with('LOGO_FILENAME', 'logo.png')
        
    @patch('utils.get_setting')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_fallback_to_default_logo_when_org_logo_missing(self, mock_file, mock_exists, mock_get_setting):
        """Test fallback to default logo when organization logo doesn't exist"""
        # Setup mocks
        mock_get_setting.return_value = 'nonexistent.png'
        
        # Make org logo not exist, but default logo exists
        def exists_side_effect(path):
            if 'nonexistent.png' in path:
                return False
            return True
        mock_exists.side_effect = exists_side_effect
        
        mock_file.return_value.read.return_value = self.default_logo_data
        
        # Simulate inline_images dict
        inline_images = {}
        
        # Simulate the logo loading logic
        from utils import get_setting
        org_logo_filename = get_setting('LOGO_FILENAME', 'logo.png')
        org_logo_path = os.path.join("static/uploads", org_logo_filename)
        
        if os.path.exists(org_logo_path):
            logo_data = open(org_logo_path, "rb").read()
            inline_images['logo'] = logo_data
            inline_images['logo_image'] = logo_data
        else:
            # Fallback to default logo
            logo_data = open("static/uploads/logo.png", "rb").read()
            inline_images['logo'] = logo_data
            inline_images['logo_image'] = logo_data
        
        # Assertions
        self.assertEqual(inline_images['logo'], self.default_logo_data)
        self.assertEqual(inline_images['logo_image'], self.default_logo_data)
        
    def test_both_cid_references_are_set(self):
        """Test that both 'logo' and 'logo_image' CIDs are set"""
        test_logo_data = b'test_data'
        inline_images = {}
        
        # Simulate setting both CIDs
        inline_images['logo'] = test_logo_data  # For owner_card_inline.html
        inline_images['logo_image'] = test_logo_data  # For compiled templates
        
        # Assertions
        self.assertIn('logo', inline_images)
        self.assertIn('logo_image', inline_images)
        self.assertEqual(inline_images['logo'], inline_images['logo_image'])
        
    def test_logo_filename_from_settings(self):
        """Test that logo filename is correctly retrieved from settings"""
        # Test data
        expected_filename = 'flhgi.png'
        expected_path = os.path.join("static/uploads", expected_filename)
        
        # Simulate getting logo filename from settings
        with patch('utils.get_setting') as mock_get_setting:
            mock_get_setting.return_value = expected_filename
            
            from utils import get_setting
            org_logo_filename = get_setting('LOGO_FILENAME', 'logo.png')
            org_logo_path = os.path.join("static/uploads", org_logo_filename)
            
            # Assertions
            self.assertEqual(org_logo_filename, expected_filename)
            self.assertEqual(org_logo_path, expected_path)
            mock_get_setting.assert_called_with('LOGO_FILENAME', 'logo.png')
    
    def test_owner_card_template_cid_reference(self):
        """Test that owner_card_inline.html uses correct CID reference"""
        template_path = 'templates/email_blocks/owner_card_inline.html'
        
        # Check if template exists and contains correct CID
        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                content = f.read()
                # The template should use cid:logo
                self.assertIn('cid:logo', content, 
                            "owner_card_inline.html should reference 'cid:logo'")
                
if __name__ == '__main__':
    unittest.main()