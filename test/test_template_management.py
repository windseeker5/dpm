#!/usr/bin/env python3
"""
Unit tests for email template management system
Tests the new template versioning and hero image priority system
"""

import unittest
import os
import json
import tempfile
import shutil
import sys
from unittest.mock import patch, MagicMock

# Add the app directory to the path so we can import from it
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils import get_template_default_hero, get_activity_hero_image


class TestTemplateManagement(unittest.TestCase):
    """Test template management functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_template_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        
        # Create test template structure
        self.create_test_templates()
    
    def tearDown(self):
        """Clean up test fixtures"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_template_dir, ignore_errors=True)
    
    def create_test_templates(self):
        """Create test template directory structure"""
        # Create original template folder with test data
        original_dir = os.path.join(self.test_template_dir, 'templates', 'email_templates', 'newPass_original')
        os.makedirs(original_dir, exist_ok=True)
        
        # Create test inline_images.json with hero image
        test_images = {
            'hero_new_pass': 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==',  # 1x1 PNG
            'logo': 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=='
        }
        
        with open(os.path.join(original_dir, 'inline_images.json'), 'w') as f:
            json.dump(test_images, f)
        
        with open(os.path.join(original_dir, 'index.html'), 'w') as f:
            f.write('<html><body><img src="cid:hero_new_pass"></body></html>')
        
        # Create compiled template folder (may be modified)
        compiled_dir = os.path.join(self.test_template_dir, 'templates', 'email_templates', 'newPass_compiled')
        os.makedirs(compiled_dir, exist_ok=True)
        
        with open(os.path.join(compiled_dir, 'inline_images.json'), 'w') as f:
            json.dump(test_images, f)
        
        with open(os.path.join(compiled_dir, 'index.html'), 'w') as f:
            f.write('<html><body><img src="cid:hero_new_pass"></body></html>')
    
    @patch('os.getcwd')
    def test_get_template_default_hero_loads_from_original(self, mock_getcwd):
        """Test that get_template_default_hero loads from _original folders"""
        mock_getcwd.return_value = self.test_template_dir
        
        # Change to test directory for relative path resolution
        os.chdir(self.test_template_dir)
        
        # Test loading hero image from original folder
        hero_data = get_template_default_hero('newPass')
        
        # Should return the decoded image data
        self.assertIsNotNone(hero_data)
        self.assertIsInstance(hero_data, bytes)
        
        # Verify it's the expected 1x1 PNG data (allow some variance in PNG encoding)
        self.assertGreater(len(hero_data), 60)  # Should be around 67-70 bytes for 1x1 PNG
        self.assertLess(len(hero_data), 80)
    
    @patch('os.getcwd')
    def test_get_template_default_hero_invalid_template(self, mock_getcwd):
        """Test get_template_default_hero with invalid template type"""
        mock_getcwd.return_value = self.test_template_dir
        os.chdir(self.test_template_dir)
        
        # Test with invalid template type
        hero_data = get_template_default_hero('invalid_template')
        
        # Should return None for invalid template
        self.assertIsNone(hero_data)
    
    @patch('os.getcwd')
    def test_get_activity_hero_image_priority_order(self, mock_getcwd):
        """Test that get_activity_hero_image follows correct priority order"""
        mock_getcwd.return_value = self.test_template_dir
        os.chdir(self.test_template_dir)
        
        # Create mock activity
        mock_activity = MagicMock()
        mock_activity.id = 123
        mock_activity.image_filename = 'test_activity.png'
        
        # Test Priority 2: Template default (no custom hero exists)
        with patch('os.path.exists') as mock_exists:
            # Custom hero doesn't exist, template original exists
            mock_exists.side_effect = lambda path: 'original' in path or 'inline_images.json' in path
            
            hero_data, is_custom, is_template_default = get_activity_hero_image(mock_activity, 'newPass')
            
            # Should use template default
            self.assertIsNotNone(hero_data)
            self.assertFalse(is_custom)
            self.assertTrue(is_template_default)
    
    @patch('os.getcwd')
    def test_get_activity_hero_image_custom_priority(self, mock_getcwd):
        """Test that custom hero has highest priority"""
        mock_getcwd.return_value = self.test_template_dir
        os.chdir(self.test_template_dir)
        
        # Create test custom hero file
        custom_hero_dir = os.path.join(self.test_template_dir, 'static', 'uploads')
        os.makedirs(custom_hero_dir, exist_ok=True)
        custom_hero_path = os.path.join(custom_hero_dir, '123_newPass_hero.png')
        
        # Write test image data
        with open(custom_hero_path, 'wb') as f:
            f.write(b'custom_hero_data')
        
        # Create mock activity
        mock_activity = MagicMock()
        mock_activity.id = 123
        mock_activity.image_filename = 'test_activity.png'
        
        # Test Priority 1: Custom hero (should have highest priority)
        hero_data, is_custom, is_template_default = get_activity_hero_image(mock_activity, 'newPass')
        
        # Should use custom hero
        self.assertEqual(hero_data, b'custom_hero_data')
        self.assertTrue(is_custom)
        self.assertFalse(is_template_default)


class TestTemplateCompilation(unittest.TestCase):
    """Test template compilation with original preservation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        
        # Create test source template
        source_dir = os.path.join(self.test_dir, 'test_template')
        os.makedirs(source_dir)
        
        # Create test HTML with image reference
        with open(os.path.join(source_dir, 'index.html'), 'w') as f:
            f.write('<html><body><img src="hero_image.png"></body></html>')
        
        # Create test image file
        with open(os.path.join(source_dir, 'hero_image.png'), 'wb') as f:
            f.write(b'test_image_data')
        
        os.chdir(self.test_dir)
    
    def tearDown(self):
        """Clean up test fixtures"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_compilation_creates_both_folders(self):
        """Test that compilation creates both _compiled and _original folders"""
        # Import here to avoid issues with path setup
        compile_script_path = os.path.join(self.original_cwd, 'templates', 'email_templates')
        if compile_script_path not in sys.path:
            sys.path.insert(0, compile_script_path)
        
        try:
            from compileEmailTemplate import compile_email_template_to_folder
        except ImportError:
            self.skipTest("compileEmailTemplate module not found - skipping compilation test")
        
        # Run compilation
        compile_email_template_to_folder('test_template')
        
        # Check both folders were created
        self.assertTrue(os.path.exists('test_template_compiled'))
        self.assertTrue(os.path.exists('test_template_original'))
        
        # Check both have the required files
        for folder in ['test_template_compiled', 'test_template_original']:
            self.assertTrue(os.path.exists(os.path.join(folder, 'index.html')))
            self.assertTrue(os.path.exists(os.path.join(folder, 'inline_images.json')))
    
    def test_recompilation_preserves_original(self):
        """Test that recompilation preserves the original folder"""
        # Import here to avoid issues with path setup
        compile_script_path = os.path.join(self.original_cwd, 'templates', 'email_templates')
        if compile_script_path not in sys.path:
            sys.path.insert(0, compile_script_path)
        
        try:
            from compileEmailTemplate import compile_email_template_to_folder
        except ImportError:
            self.skipTest("compileEmailTemplate module not found - skipping compilation test")
        
        # First compilation
        compile_email_template_to_folder('test_template')
        
        # Modify the original folder to simulate it being pristine
        original_html_path = os.path.join('test_template_original', 'index.html')
        with open(original_html_path, 'w') as f:
            f.write('<html><body>ORIGINAL VERSION</body></html>')
        
        # Modify source and recompile
        source_html_path = os.path.join('test_template', 'index.html')
        with open(source_html_path, 'w') as f:
            f.write('<html><body>MODIFIED VERSION</body></html>')
        
        # Second compilation
        compile_email_template_to_folder('test_template')
        
        # Original should be preserved, compiled should be updated
        with open(original_html_path, 'r') as f:
            original_content = f.read()
        
        with open(os.path.join('test_template_compiled', 'index.html'), 'r') as f:
            compiled_content = f.read()
        
        # Original should still contain the preserved version
        self.assertIn('ORIGINAL VERSION', original_content)
        
        # Compiled should contain the new version
        self.assertIn('MODIFIED VERSION', compiled_content)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)