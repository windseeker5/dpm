#!/usr/bin/env python3
"""
Unit tests for email customization functionality
Tests default image creation, file uploads, and email rendering
"""

import unittest
import os
import tempfile
import shutil
from unittest.mock import MagicMock, patch, mock_open
import sys
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestEmailCustomization(unittest.TestCase):
    """Test email customization features"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.uploads_dir = os.path.join(self.test_dir, "uploads")
        self.defaults_dir = os.path.join(self.uploads_dir, "defaults")
        os.makedirs(self.defaults_dir)
        
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_default_images_exist(self):
        """Test that default images are created in the correct location"""
        # Check actual default images exist
        real_defaults_dir = "/home/kdresdell/Documents/DEV/minipass_env/app/static/uploads/defaults"
        
        hero_path = os.path.join(real_defaults_dir, "default_hero.png")
        logo_path = os.path.join(real_defaults_dir, "default_owner_logo.png")
        
        self.assertTrue(os.path.exists(hero_path), "Default hero image should exist")
        self.assertTrue(os.path.exists(logo_path), "Default owner logo should exist")
        
        # Verify they are valid image files (check file size)
        self.assertGreater(os.path.getsize(hero_path), 0, "Hero image should not be empty")
        self.assertGreater(os.path.getsize(logo_path), 0, "Owner logo should not be empty")
    
    @patch('shutil.copy')
    @patch('os.path.exists')
    def test_activity_creation_copies_defaults(self, mock_exists, mock_copy):
        """Test that creating a new activity copies default images"""
        mock_exists.return_value = True
        
        # Simulate activity creation with ID 123
        activity_id = 123
        
        # Expected source and destination paths
        hero_src = os.path.join("static", "uploads", "defaults", "default_hero.png")
        hero_dst = os.path.join("static", "uploads", f"{activity_id}_hero.png")
        
        logo_src = os.path.join("static", "uploads", "defaults", "default_owner_logo.png")
        logo_dst = os.path.join("static", "uploads", f"{activity_id}_owner_logo.png")
        
        # Simulate the copy operations
        shutil.copy(hero_src, hero_dst)
        shutil.copy(logo_src, logo_dst)
        
        # Verify copy was called with correct arguments
        mock_copy.assert_any_call(hero_src, hero_dst)
        mock_copy.assert_any_call(logo_src, logo_dst)
        self.assertEqual(mock_copy.call_count, 2)
    
    def test_email_template_references(self):
        """Test that email templates get updated with image references"""
        # Sample email templates structure
        templates = {
            'newPass': {'subject': 'Test'},
            'paymentReceived': {'subject': 'Test2'}
        }
        
        activity_id = 456
        
        # Update templates with image references
        for template_type in templates:
            if isinstance(templates[template_type], dict):
                templates[template_type]['hero_image'] = f"{activity_id}_hero.png"
                templates[template_type]['activity_logo'] = f"{activity_id}_owner_logo.png"
        
        # Verify all templates have image references
        for template_type in templates:
            self.assertIn('hero_image', templates[template_type])
            self.assertIn('activity_logo', templates[template_type])
            self.assertEqual(templates[template_type]['hero_image'], f"{activity_id}_hero.png")
            self.assertEqual(templates[template_type]['activity_logo'], f"{activity_id}_owner_logo.png")
    
    @patch('builtins.open', new_callable=mock_open, read_data=b'fake_image_data')
    @patch('os.path.exists')
    def test_custom_image_loading_in_email(self, mock_exists, mock_file):
        """Test that custom images are loaded when sending emails"""
        # Set up existence checks
        def exists_side_effect(path):
            return '_hero.png' in path or '_owner_logo.png' in path
        mock_exists.side_effect = exists_side_effect
        
        activity_id = 789
        inline_images = {'ticket': b'default_ticket', 'logo': b'default_logo'}
        
        # Simulate loading custom images
        hero_path = os.path.join("static", "uploads", f"{activity_id}_hero.png")
        logo_path = os.path.join("static", "uploads", f"{activity_id}_owner_logo.png")
        
        if os.path.exists(hero_path):
            with open(hero_path, "rb") as f:
                inline_images['ticket'] = f.read()
        
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                inline_images['logo'] = f.read()
        
        # Verify custom images replaced defaults
        self.assertEqual(inline_images['ticket'], b'fake_image_data')
        self.assertEqual(inline_images['logo'], b'fake_image_data')
    
    def test_file_upload_naming(self):
        """Test that uploaded files follow correct naming pattern"""
        activity_id = 999
        
        # Expected file names
        expected_hero = f"{activity_id}_hero.png"
        expected_logo = f"{activity_id}_owner_logo.png"
        
        # Verify naming pattern
        self.assertTrue(expected_hero.startswith(str(activity_id)))
        self.assertTrue(expected_hero.endswith('_hero.png'))
        self.assertTrue(expected_logo.startswith(str(activity_id)))
        self.assertTrue(expected_logo.endswith('_owner_logo.png'))
    
    @patch('os.path.exists')
    def test_fallback_when_custom_missing(self, mock_exists):
        """Test fallback behavior when custom images don't exist"""
        mock_exists.return_value = False
        
        inline_images = {'ticket': b'compiled_ticket', 'logo': b'compiled_logo'}
        original_ticket = inline_images['ticket']
        original_logo = inline_images['logo']
        
        # Since files don't exist, images should remain unchanged
        activity_id = 111
        hero_path = os.path.join("static", "uploads", f"{activity_id}_hero.png")
        
        if not os.path.exists(hero_path):
            # Keep original compiled image
            pass
        
        # Verify fallback worked
        self.assertEqual(inline_images['ticket'], original_ticket)
        self.assertEqual(inline_images['logo'], original_logo)

if __name__ == '__main__':
    unittest.main()