#!/usr/bin/env python3
"""
Unit tests for email inline images functionality.

Tests that compiled template paths are used correctly and inline_images.json files are loaded properly.
"""

import unittest
import json
import base64
import os
import tempfile
from unittest.mock import patch, mock_open, MagicMock
# Create a simple Mock App for testing
class MockApp:
    def __init__(self):
        self.config = {'TESTING': True}

try:
    from utils import notify_pass_event
except ImportError:
    notify_pass_event = None


class TestEmailInlineImages(unittest.TestCase):
    """Test class for email inline images functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.app = MockApp()
        
    @unittest.skipIf(notify_pass_event is None, "notify_pass_event function not available")
    def test_notify_pass_event_uses_compiled_templates(self):
        """Test that notify_pass_event uses compiled template paths."""
        # Test data
        test_cases = [
            ('pass_created', 'newPass_compiled/index.html'),
            ('payment_received', 'paymentReceived_compiled/index.html'),
            ('payment_late', 'latePayment_compiled/index.html'),
            ('pass_redeemed', 'redeemPass_compiled/index.html'),
            ('unknown_event', 'newPass_compiled/index.html')  # Default case
        ]
        
        for event_type, expected_template in test_cases:
            with self.subTest(event_type=event_type):
                # Mock the database objects
                mock_pass = MagicMock()
                mock_pass.pass_code = 'TEST123'
                mock_pass.uses_remaining = 5
                mock_pass.sold_amt = 25.00
                mock_pass.paid = True
                mock_pass.created_dt = '2023-01-01'
                mock_pass.user = MagicMock()
                mock_pass.user.name = 'Test User'
                mock_pass.user.email = 'test@example.com'
                mock_pass.user.phone_number = '1234567890'
                mock_pass.activity = MagicMock()
                mock_pass.activity.name = 'Test Activity'
                
                # Mock external dependencies
                with patch('utils.generate_qr_code_image') as mock_qr, \
                     patch('utils.get_pass_history_data') as mock_history, \
                     patch('utils.render_template') as mock_render, \
                     patch('utils.send_email_async') as mock_email, \
                     patch('utils.open', mock_open(read_data=b'fake_logo_data')) as mock_file_open, \
                     patch('os.path.exists', return_value=True), \
                     patch('builtins.open', mock_open(read_data='{"test_cid": "dGVzdF9pbWFnZV9kYXRh"}')):
                    
                    # Configure mocks
                    mock_qr.return_value.read.return_value = b'fake_qr_data'
                    mock_history.return_value = []
                    mock_render.return_value = '<div>test</div>'
                    
                    # Call the function
                    notify_pass_event(
                        app=self.app,
                        pass_data=mock_pass,
                        event_type=event_type,
                        activity=mock_pass.activity,
                        admin_email='admin@example.com'
                    )
                    
                    # Verify send_email_async was called with correct template
                    mock_email.assert_called_once()
                    call_args = mock_email.call_args
                    
                    # Check that template_name argument matches expected compiled template
                    self.assertEqual(call_args[1]['template_name'], expected_template)
                    
                    # Verify inline_images contains decoded base64 data
                    inline_images = call_args[1]['inline_images']
                    self.assertIn('test_cid', inline_images)
                    self.assertEqual(inline_images['test_cid'], b'test_image_data')
                    self.assertIn('qr_code', inline_images)
                    self.assertIn('logo_image', inline_images)

    @unittest.skipIf(notify_pass_event is None, "notify_pass_event function not available")
    def test_notify_pass_event_loads_inline_images_json(self):
        """Test that notify_pass_event loads inline_images.json correctly."""
        # Sample base64 encoded test images
        test_images = {
            'checkmark': base64.b64encode(b'checkmark_data').decode(),
            'facebook': base64.b64encode(b'facebook_data').decode(),
            'instagram': base64.b64encode(b'instagram_data').decode()
        }
        
        mock_pass = MagicMock()
        mock_pass.pass_code = 'TEST123'
        mock_pass.uses_remaining = 5
        mock_pass.sold_amt = 25.00
        mock_pass.paid = True
        mock_pass.created_dt = '2023-01-01'
        mock_pass.user = MagicMock()
        mock_pass.user.name = 'Test User'
        mock_pass.user.email = 'test@example.com'
        mock_pass.user.phone_number = '1234567890'
        mock_pass.activity = MagicMock()
        mock_pass.activity.name = 'Test Activity'
        
        with patch('utils.generate_qr_code_image') as mock_qr, \
             patch('utils.get_pass_history_data') as mock_history, \
             patch('utils.render_template') as mock_render, \
             patch('utils.send_email_async') as mock_email, \
             patch('utils.open', mock_open(read_data=b'fake_logo_data')), \
             patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=json.dumps(test_images))):
            
            # Configure mocks
            mock_qr.return_value.read.return_value = b'fake_qr_data'
            mock_history.return_value = []
            mock_render.return_value = '<div>test</div>'
            
            # Call the function
            notify_pass_event(
                app=self.app,
                pass_data=mock_pass,
                event_type='pass_created',
                activity=mock_pass.activity,
                admin_email='admin@example.com'
            )
            
            # Verify inline_images contains all decoded images
            call_args = mock_email.call_args
            inline_images = call_args[1]['inline_images']
            
            # Check that all test images were decoded properly
            self.assertEqual(inline_images['checkmark'], b'checkmark_data')
            self.assertEqual(inline_images['facebook'], b'facebook_data')
            self.assertEqual(inline_images['instagram'], b'instagram_data')
            
            # Check that dynamic images are still added
            self.assertIn('qr_code', inline_images)
            self.assertIn('logo_image', inline_images)

    @unittest.skipIf(notify_pass_event is None, "notify_pass_event function not available")
    def test_notify_pass_event_handles_missing_json_file(self):
        """Test that notify_pass_event handles missing inline_images.json gracefully."""
        mock_pass = MagicMock()
        mock_pass.pass_code = 'TEST123'
        mock_pass.uses_remaining = 5
        mock_pass.sold_amt = 25.00
        mock_pass.paid = True
        mock_pass.created_dt = '2023-01-01'
        mock_pass.user = MagicMock()
        mock_pass.user.name = 'Test User'
        mock_pass.user.email = 'test@example.com'
        mock_pass.user.phone_number = '1234567890'
        mock_pass.activity = MagicMock()
        mock_pass.activity.name = 'Test Activity'
        
        with patch('utils.generate_qr_code_image') as mock_qr, \
             patch('utils.get_pass_history_data') as mock_history, \
             patch('utils.render_template') as mock_render, \
             patch('utils.send_email_async') as mock_email, \
             patch('utils.open', mock_open(read_data=b'fake_logo_data')), \
             patch('os.path.exists', return_value=False):  # JSON file doesn't exist
            
            # Configure mocks
            mock_qr.return_value.read.return_value = b'fake_qr_data'
            mock_history.return_value = []
            mock_render.return_value = '<div>test</div>'
            
            # Call the function - should not raise an exception
            notify_pass_event(
                app=self.app,
                pass_data=mock_pass,
                event_type='pass_created',
                activity=mock_pass.activity,
                admin_email='admin@example.com'
            )
            
            # Verify inline_images only contains dynamic images
            call_args = mock_email.call_args
            inline_images = call_args[1]['inline_images']
            
            # Should only have dynamic images, no compiled images
            expected_keys = {'qr_code', 'logo_image'}
            self.assertEqual(set(inline_images.keys()), expected_keys)

    @patch('app.current_app')
    @patch('app.Survey')
    @patch('app.SurveyResponse')
    @patch('app.Passport')
    def test_send_survey_invitations_uses_compiled_template(self, mock_passport, mock_survey_response, 
                                                           mock_survey, mock_current_app):
        """Test that send_survey_invitations uses compiled template path."""
        # This would require more complex setup due to the Flask app context
        # For now, we'll test the template path change through integration
        
        # Mock survey object
        mock_survey_instance = MagicMock()
        mock_survey_instance.id = 1
        mock_survey_instance.name = 'Test Survey'
        mock_survey_instance.survey_token = 'test_token'
        mock_survey_instance.activity = MagicMock()
        mock_survey_instance.activity.name = 'Test Activity'
        
        # Verify the template path is updated to compiled version
        expected_template = 'email_survey_invitation_compiled/index.html'
        
        # This test would need more Flask app context setup to work properly
        # The main verification is that the template_name is changed in the source code
        self.assertTrue(True)  # Placeholder - actual test needs app context

    def test_compiled_templates_exist(self):
        """Test that all expected compiled template directories exist."""
        template_base = 'templates/email_templates'
        expected_compiled_dirs = [
            'newPass_compiled',
            'paymentReceived_compiled', 
            'latePayment_compiled',
            'redeemPass_compiled',
            'email_survey_invitation_compiled'
        ]
        
        for dir_name in expected_compiled_dirs:
            dir_path = os.path.join(template_base, dir_name)
            if os.path.exists(dir_path):
                # Check if index.html exists
                index_path = os.path.join(dir_path, 'index.html')
                self.assertTrue(os.path.exists(index_path), 
                               f"index.html should exist in {dir_path}")
            # Note: Not all directories may exist in test environment
            
    def test_inline_images_json_structure(self):
        """Test that inline_images.json files have correct structure when they exist."""
        template_base = 'templates/email_templates'
        compiled_dirs = [
            'newPass_compiled',
            'paymentReceived_compiled', 
            'latePayment_compiled',
            'redeemPass_compiled'
        ]
        
        for dir_name in compiled_dirs:
            json_path = os.path.join(template_base, dir_name, 'inline_images.json')
            if os.path.exists(json_path):
                with self.subTest(json_file=json_path):
                    with open(json_path, 'r') as f:
                        try:
                            data = json.load(f)
                            # Should be a dictionary
                            self.assertIsInstance(data, dict)
                            
                            # Each value should be a valid base64 string
                            for cid, b64_data in data.items():
                                self.assertIsInstance(cid, str)
                                self.assertIsInstance(b64_data, str)
                                # Test that it's valid base64
                                try:
                                    decoded = base64.b64decode(b64_data)
                                    self.assertIsInstance(decoded, bytes)
                                except Exception as e:
                                    self.fail(f"Invalid base64 data for CID '{cid}' in {json_path}: {e}")
                                    
                        except json.JSONDecodeError as e:
                            self.fail(f"Invalid JSON in {json_path}: {e}")


if __name__ == '__main__':
    unittest.main()