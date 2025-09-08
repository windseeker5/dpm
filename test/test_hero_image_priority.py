import unittest
import os
import tempfile
import shutil
import json
import base64
from unittest.mock import Mock, patch

# Import the functions we want to test
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_template_default_hero, get_activity_hero_image


class TestHeroImagePriority(unittest.TestCase):
    """Test the fixed hero image priority logic"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create test directory structure
        os.makedirs('templates/email_templates/newPass_compiled', exist_ok=True)
        os.makedirs('static/uploads', exist_ok=True)
        os.makedirs('static/uploads/activity_images', exist_ok=True)
        
        # Create test template with hero image
        test_image_b64 = base64.b64encode(b'fake_template_hero_data').decode()
        template_images = {
            'hero_new_pass': test_image_b64,
            'facebook': 'fake_facebook_data',
            'instagram': 'fake_instagram_data'
        }
        
        with open('templates/email_templates/newPass_compiled/inline_images.json', 'w') as f:
            json.dump(template_images, f)
        
        # Create test activity image
        with open('static/uploads/activity_images/surf.jpg', 'wb') as f:
            f.write(b'fake_activity_image_data')
    
    def tearDown(self):
        """Clean up test fixtures"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_get_template_default_hero_success(self):
        """Test loading template default hero image"""
        hero_data = get_template_default_hero('newPass')
        self.assertIsNotNone(hero_data)
        self.assertEqual(hero_data, b'fake_template_hero_data')
    
    def test_get_template_default_hero_unknown_template(self):
        """Test handling unknown template type"""
        hero_data = get_template_default_hero('unknown')
        self.assertIsNone(hero_data)
    
    def test_get_template_default_hero_missing_file(self):
        """Test handling missing template file"""
        hero_data = get_template_default_hero('paymentReceived')  # No file exists
        self.assertIsNone(hero_data)
    
    def test_priority_1_custom_hero_upload(self):
        """Test Priority 1: Custom uploaded hero takes precedence"""
        # Create mock activity
        activity = Mock()
        activity.id = 5
        activity.image_filename = 'surf.jpg'
        
        # Create custom hero file
        custom_path = 'static/uploads/5_newPass_hero.png'
        with open(custom_path, 'wb') as f:
            f.write(b'custom_hero_data')
        
        # Should return custom hero
        hero_data, is_custom, is_template_default = get_activity_hero_image(activity, 'newPass')
        
        self.assertIsNotNone(hero_data)
        self.assertEqual(hero_data, b'custom_hero_data')
        self.assertTrue(is_custom)
        self.assertFalse(is_template_default)
    
    def test_priority_2_template_default(self):
        """Test Priority 2: Template default when no custom upload"""
        # Create mock activity with no custom hero
        activity = Mock()
        activity.id = 5
        activity.image_filename = 'surf.jpg'  # Has activity image but should use template default
        
        # Should return template default
        hero_data, is_custom, is_template_default = get_activity_hero_image(activity, 'newPass')
        
        self.assertIsNotNone(hero_data)
        self.assertEqual(hero_data, b'fake_template_hero_data')
        self.assertFalse(is_custom)
        self.assertTrue(is_template_default)
    
    def test_priority_3_activity_fallback(self):
        """Test Priority 3: Activity image as last resort"""
        # Create mock activity
        activity = Mock()
        activity.id = 5
        activity.image_filename = 'surf.jpg'
        
        # Remove template file so it falls back to activity image
        os.remove('templates/email_templates/newPass_compiled/inline_images.json')
        
        # Should return activity image
        hero_data, is_custom, is_template_default = get_activity_hero_image(activity, 'newPass')
        
        self.assertIsNotNone(hero_data)
        self.assertEqual(hero_data, b'fake_activity_image_data')
        self.assertFalse(is_custom)
        self.assertFalse(is_template_default)
    
    def test_no_hero_found(self):
        """Test when no hero image is found"""
        # Create mock activity with no image
        activity = Mock()
        activity.id = 5
        activity.image_filename = None
        
        # Remove template file
        os.remove('templates/email_templates/newPass_compiled/inline_images.json')
        
        # Should return None
        hero_data, is_custom, is_template_default = get_activity_hero_image(activity, 'newPass')
        
        self.assertIsNone(hero_data)
        self.assertFalse(is_custom)
        self.assertFalse(is_template_default)
    
    def test_custom_override_beats_template_default(self):
        """Test that custom upload overrides template default"""
        # Create mock activity
        activity = Mock()
        activity.id = 5
        activity.image_filename = None  # No activity image
        
        # Create custom hero file
        custom_path = 'static/uploads/5_newPass_hero.png'
        with open(custom_path, 'wb') as f:
            f.write(b'custom_override_data')
        
        # Should return custom hero, not template default
        hero_data, is_custom, is_template_default = get_activity_hero_image(activity, 'newPass')
        
        self.assertIsNotNone(hero_data)
        self.assertEqual(hero_data, b'custom_override_data')
        self.assertTrue(is_custom)
        self.assertFalse(is_template_default)


if __name__ == '__main__':
    unittest.main()