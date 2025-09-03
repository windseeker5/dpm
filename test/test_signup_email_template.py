"""
Unit tests for signup email template functionality
Tests the hero image replacement logic in notify_signup_event
"""

import unittest
import os
import sys
import json
import base64
from unittest.mock import Mock, patch, MagicMock, mock_open, ANY
from pathlib import Path

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the function we're testing
from utils import notify_signup_event


class TestSignupEmailTemplate(unittest.TestCase):
    """Test signup email template with hero image replacement"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_app = Mock()
        
        self.mock_activity = Mock()
        self.mock_activity.id = 4
        self.mock_activity.activity_name = "Test Activity"
        self.mock_activity.organization = Mock()
        self.mock_activity.organization.name = "Test Organization"
        self.mock_activity.organization.email = "org@test.com"
        self.mock_activity.organization.phone_number = "514-555-9999"
        
        self.mock_signup = Mock()
        self.mock_signup.user_first_name = "John"
        self.mock_signup.user_last_name = "Doe"
        self.mock_signup.user_email = "john.doe@test.com"
        self.mock_signup.user_phone = "514-555-0123"
        self.mock_signup.payment_received_status = "Not Received"
        
        self.mock_passport_type = Mock()
        self.mock_passport_type.price_per_user = 50.00
        self.mock_passport_type.sessions_included = 10
        self.mock_passport_type.payment_instructions = "E-transfer to org@test.com"
        
    @patch('utils.send_email')
    @patch('utils.get_passport_type_by_signup')
    @patch('utils.get_setting')
    @patch('utils.render_template_string')
    @patch('builtins.open', new_callable=mock_open)
    @patch('utils.os.path.exists')
    def test_signup_with_activity_hero_image(self, mock_exists, mock_file_open, mock_render, mock_get_setting, mock_get_passport, mock_send):
        """Test that activity-specific hero image replaces 'good-news' CID"""
        
        # Setup path existence checks
        def path_exists_check(path):
            if 'signup_compiled' in path:  # Compiled template folders
                return True
            if '4_hero.png' in path:  # Activity hero image
                return True
            if 'logo.png' in path:  # Organization logo
                return False
            return False
        
        mock_exists.side_effect = path_exists_check
        mock_get_setting.return_value = 'logo.png'
        
        # Setup file reads
        template_html = '<html>Template with cid:good-news</html>'
        inline_images_json = json.dumps({'good-news': base64.b64encode(b'default_image').decode()})
        hero_image_data = b'activity_hero_image_data'
        
        def read_file_content(*args, **kwargs):
            file_path = args[0]
            mock = MagicMock()
            if 'index.html' in file_path:
                mock.read.return_value = template_html
                mock.__enter__.return_value = mock
            elif 'inline_images.json' in file_path:
                mock.read.return_value = inline_images_json
                mock.__enter__.return_value = mock
            elif '4_hero.png' in file_path:
                mock.read.return_value = hero_image_data
                mock.__enter__.return_value = mock
            else:
                mock.read.return_value = b''
                mock.__enter__.return_value = mock
            return mock
        
        mock_file_open.side_effect = read_file_content
        mock_render.return_value = '<html>Rendered Template</html>'
        
        # Call the function
        result = notify_signup_event(
            self.mock_app,
            signup=self.mock_signup,
            activity=self.mock_activity
        )
        
        # Verify send_email was called with replaced hero image
        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        
        # Check that inline_images contains the replaced hero
        self.assertIn('inline_images', call_args)
        self.assertIn('good-news', call_args['inline_images'])
        self.assertEqual(call_args['inline_images']['good-news'], hero_image_data)
        
    @patch('utils.send_email')
    @patch('utils.get_setting')
    @patch('utils.render_template_string')
    @patch('builtins.open', new_callable=mock_open)
    @patch('utils.os.path.exists')
    def test_signup_without_activity_hero_image(self, mock_exists, mock_file_open, mock_render, mock_get_setting, mock_send):
        """Test fallback to default 'good-news' image when no activity hero exists"""
        
        # Setup path existence - no hero image
        def path_exists_check(path):
            if 'signup_compiled' in path:  # Compiled template folders exist
                return True
            if '4_hero.png' in path:  # Activity hero image does NOT exist
                return False
            return False
        
        mock_exists.side_effect = path_exists_check
        mock_get_setting.return_value = 'logo.png'
        
        # Setup file reads
        template_html = '<html>Template with cid:good-news</html>'
        default_image_data = b'default_good_news_image'
        inline_images_json = json.dumps({'good-news': base64.b64encode(default_image_data).decode()})
        
        def read_file_content(*args, **kwargs):
            file_path = args[0]
            mock = MagicMock()
            if 'index.html' in file_path:
                mock.read.return_value = template_html
                mock.__enter__.return_value = mock
            elif 'inline_images.json' in file_path:
                mock.read.return_value = inline_images_json
                mock.__enter__.return_value = mock
            else:
                mock.read.return_value = b''
                mock.__enter__.return_value = mock
            return mock
        
        mock_file_open.side_effect = read_file_content
        mock_render.return_value = '<html>Rendered Template</html>'
        
        # Call the function
        result = notify_signup_event(
            self.mock_app,
            signup=self.mock_signup,
            activity=self.mock_activity
        )
        
        # Verify send_email was called with default image
        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        
        # Check that inline_images contains the default image (not replaced)
        self.assertIn('inline_images', call_args)
        self.assertIn('good-news', call_args['inline_images'])
        self.assertEqual(call_args['inline_images']['good-news'], default_image_data)
        
    @patch('utils.send_email')
    @patch('utils.get_setting')
    @patch('utils.render_template_string')
    @patch('builtins.open', new_callable=mock_open)
    @patch('utils.os.path.exists')
    @patch('builtins.print')
    def test_debug_messages(self, mock_print, mock_exists, mock_file_open, mock_render, mock_get_setting, mock_send):
        """Test that appropriate debug messages are printed"""
        
        # Test when hero image exists
        def path_exists_with_hero(path):
            if 'signup_compiled' in path:
                return True
            if '4_hero.png' in path:
                return True
            return False
        
        mock_exists.side_effect = path_exists_with_hero
        mock_get_setting.return_value = 'logo.png'
        
        # Setup file reads
        template_html = '<html>Template</html>'
        inline_images_json = json.dumps({'good-news': base64.b64encode(b'default').decode()})
        
        def read_file_content(*args, **kwargs):
            file_path = args[0]
            mock = MagicMock()
            if 'index.html' in file_path:
                mock.read.return_value = template_html
            elif 'inline_images.json' in file_path:
                mock.read.return_value = inline_images_json
            elif '4_hero.png' in file_path:
                mock.read.return_value = b'hero_data'
            else:
                mock.read.return_value = b''
            mock.__enter__.return_value = mock
            return mock
        
        mock_file_open.side_effect = read_file_content
        mock_render.return_value = '<html>Rendered</html>'
        
        # Call with hero image present
        notify_signup_event(
            self.mock_app,
            signup=self.mock_signup,
            activity=self.mock_activity
        )
        
        # Check for success debug message
        mock_print.assert_any_call("Using activity-specific hero image: 4_hero.png")
        
        # Reset for test without hero
        mock_print.reset_mock()
        mock_exists.side_effect = lambda path: 'signup_compiled' in path  # Only template exists
        
        # Call without hero image
        notify_signup_event(
            self.mock_app,
            signup=self.mock_signup,
            activity=self.mock_activity
        )
        
        # Check for not found debug message
        expected_path = os.path.join("static/uploads", "4_hero.png")
        mock_print.assert_any_call(f"Activity hero image not found: {expected_path}")


if __name__ == '__main__':
    unittest.main(verbosity=2)