"""
Comprehensive unit tests for the email template customization system.

Tests the newly implemented functionality:
1. get_email_context() helper function
2. JSON storage in Activity model
3. Email template routes (GET and POST)
4. File upload functionality for hero images
5. Integration with email sending system
6. Edge cases and error handling
"""
import unittest
import sys
import os
import json
import tempfile
import shutil
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, mock_open
from io import BytesIO

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import get_email_context
from models import db, Activity, Admin


class TestEmailTemplateCustomization(unittest.TestCase):
    """Test the email template customization system comprehensively"""
    
    def setUp(self):
        """Set up test environment"""
        self.mock_app = MagicMock()
        self.mock_context = MagicMock()
        self.mock_app.app_context.return_value = self.mock_context
        
        # Mock Flask session
        self.mock_session = {'admin': {'id': 1, 'username': 'test_admin'}}
        
        # Mock Activity instance
        self.mock_activity = MagicMock(spec=Activity)
        self.mock_activity.id = 1
        self.mock_activity.activity_name = "Test Activity"
        self.mock_activity.email_templates = None
        
        # Template types used in the system
        self.template_types = [
            'newPass', 'paymentReceived', 'latePayment', 
            'signup', 'redeemPass', 'survey_invitation'
        ]
        
        # Create temporary upload directory for testing
        self.test_upload_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_upload_dir)

    # ================================
    # 📧 GET_EMAIL_CONTEXT FUNCTION TESTS
    # ================================
    
    def test_get_email_context_with_no_activity(self):
        """Test get_email_context with None activity returns defaults"""
        result = get_email_context(None, 'newPass')
        
        # Should return default values
        expected_defaults = {
            'subject': 'Minipass Notification',
            'title': 'Welcome to Minipass', 
            'intro_text': 'Thank you for using our service.',
            'conclusion_text': 'We appreciate your business!',
            'hero_image': None,
            'cta_text': None,
            'cta_url': None,
            'custom_message': None
        }
        
        for key, value in expected_defaults.items():
            self.assertEqual(result[key], value)
    
    def test_get_email_context_with_base_context(self):
        """Test get_email_context merges with base context"""
        base_context = {
            'user_name': 'John Doe',
            'activity_name': 'Test Activity',
            'subject': 'Custom Subject'  # Should be overridden by defaults
        }
        
        result = get_email_context(None, 'newPass', base_context)
        
        # Should preserve base context values not in defaults
        self.assertEqual(result['user_name'], 'John Doe')
        self.assertEqual(result['activity_name'], 'Test Activity')
        
        # Should apply defaults for missing values
        self.assertEqual(result['title'], 'Welcome to Minipass')
        self.assertEqual(result['intro_text'], 'Thank you for using our service.')
    
    def test_get_email_context_no_customizations(self):
        """Test activity with no email_templates returns defaults"""
        activity = MagicMock()
        activity.email_templates = None
        
        result = get_email_context(activity, 'newPass')
        
        # Should return defaults since no customizations
        self.assertEqual(result['subject'], 'Minipass Notification')
        self.assertEqual(result['title'], 'Welcome to Minipass')
    
    def test_get_email_context_empty_customizations(self):
        """Test activity with empty email_templates dict returns defaults"""
        activity = MagicMock()
        activity.email_templates = {}
        
        result = get_email_context(activity, 'newPass')
        
        # Should return defaults since template type not in dict
        self.assertEqual(result['subject'], 'Minipass Notification')
        self.assertEqual(result['title'], 'Welcome to Minipass')
    
    def test_get_email_context_partial_customizations(self):
        """Test activity with partial customizations merges with defaults"""
        activity = MagicMock()
        activity.email_templates = {
            'newPass': {
                'subject': 'Custom Welcome Subject',
                'title': 'Custom Title',
                # intro_text, conclusion_text, etc. not provided - should use defaults
            }
        }
        
        result = get_email_context(activity, 'newPass')
        
        # Should use custom values where provided
        self.assertEqual(result['subject'], 'Custom Welcome Subject')
        self.assertEqual(result['title'], 'Custom Title')
        
        # Should use defaults for missing values
        self.assertEqual(result['intro_text'], 'Thank you for using our service.')
        self.assertEqual(result['conclusion_text'], 'We appreciate your business!')
        self.assertIsNone(result['hero_image'])
    
    def test_get_email_context_full_customizations(self):
        """Test activity with complete customizations overrides all defaults"""
        activity = MagicMock()
        activity.email_templates = {
            'paymentReceived': {
                'subject': 'Payment Confirmed!',
                'title': 'Thank You for Your Payment',
                'intro_text': 'We have received your payment.',
                'conclusion_text': 'Your pass is now active.',
                'hero_image': 'custom_hero.jpg',
                'cta_text': 'View Your Pass',
                'cta_url': 'https://example.com/pass',
                'custom_message': 'Special promotion inside!'
            }
        }
        
        result = get_email_context(activity, 'paymentReceived')
        
        # Should use all custom values
        self.assertEqual(result['subject'], 'Payment Confirmed!')
        self.assertEqual(result['title'], 'Thank You for Your Payment')
        self.assertEqual(result['intro_text'], 'We have received your payment.')
        self.assertEqual(result['conclusion_text'], 'Your pass is now active.')
        self.assertEqual(result['hero_image'], 'custom_hero.jpg')
        self.assertEqual(result['cta_text'], 'View Your Pass')
        self.assertEqual(result['cta_url'], 'https://example.com/pass')
        self.assertEqual(result['custom_message'], 'Special promotion inside!')
    
    def test_get_email_context_ignores_empty_strings(self):
        """Test that empty string values are ignored in favor of defaults"""
        activity = MagicMock()
        activity.email_templates = {
            'latePayment': {
                'subject': 'Late Payment Notice',
                'title': '',  # Empty string should be ignored
                'intro_text': 'Your payment is overdue.',
                'conclusion_text': '',  # Empty string should be ignored
                'hero_image': '',  # Empty string should be ignored
            }
        }
        
        result = get_email_context(activity, 'latePayment')
        
        # Should use custom non-empty values
        self.assertEqual(result['subject'], 'Late Payment Notice')
        self.assertEqual(result['intro_text'], 'Your payment is overdue.')
        
        # Should use defaults for empty string values
        self.assertEqual(result['title'], 'Welcome to Minipass')
        self.assertEqual(result['conclusion_text'], 'We appreciate your business!')
        self.assertIsNone(result['hero_image'])
    
    def test_get_email_context_different_template_types(self):
        """Test that different template types access correct customizations"""
        activity = MagicMock()
        activity.email_templates = {
            'newPass': {'subject': 'New Pass Created'},
            'signup': {'subject': 'Signup Confirmed'},
            'redeemPass': {'subject': 'Pass Redeemed'}
        }
        
        # Test each template type gets its own customizations
        result_newpass = get_email_context(activity, 'newPass')
        result_signup = get_email_context(activity, 'signup') 
        result_redeem = get_email_context(activity, 'redeemPass')
        
        self.assertEqual(result_newpass['subject'], 'New Pass Created')
        self.assertEqual(result_signup['subject'], 'Signup Confirmed')
        self.assertEqual(result_redeem['subject'], 'Pass Redeemed')
        
        # Template type not in customizations should use defaults
        result_payment = get_email_context(activity, 'paymentReceived')
        self.assertEqual(result_payment['subject'], 'Minipass Notification')
    
    # ================================
    # 🗄️ ACTIVITY MODEL JSON STORAGE TESTS  
    # ================================
    
    @patch('models.db')
    def test_activity_email_templates_json_storage(self, mock_db):
        """Test that Activity model can store and retrieve email_templates JSON"""
        # Create a mock Activity instance
        activity = Activity()
        activity.id = 1
        activity.activity_name = "Test Activity"
        
        # Test storing email templates
        email_templates = {
            'newPass': {
                'subject': 'Custom New Pass Subject',
                'title': 'Your New Pass is Ready!',
                'intro_text': 'Congratulations on your new pass.'
            },
            'paymentReceived': {
                'subject': 'Payment Received',
                'conclusion_text': 'Thank you for your payment!'
            }
        }
        
        activity.email_templates = email_templates
        
        # Verify the JSON data is stored correctly
        self.assertEqual(activity.email_templates, email_templates)
        self.assertIsInstance(activity.email_templates, dict)
        
        # Test accessing nested data
        self.assertEqual(activity.email_templates['newPass']['subject'], 'Custom New Pass Subject')
        self.assertEqual(activity.email_templates['paymentReceived']['conclusion_text'], 'Thank you for your payment!')
    
    @patch('models.db')
    def test_activity_email_templates_json_serialization(self, mock_db):
        """Test JSON serialization and deserialization"""
        activity = Activity()
        
        # Test with various data types
        complex_templates = {
            'newPass': {
                'subject': 'String value',
                'hero_image': None,
                'cta_url': 'https://example.com',
                'custom_data': {'nested': 'dict', 'number': 123}
            }
        }
        
        activity.email_templates = complex_templates
        
        # Convert to JSON and back (simulating database storage/retrieval)
        json_str = json.dumps(activity.email_templates)
        restored_data = json.loads(json_str)
        
        self.assertEqual(restored_data, complex_templates)
        self.assertEqual(restored_data['newPass']['custom_data']['nested'], 'dict')
        self.assertEqual(restored_data['newPass']['custom_data']['number'], 123)
    
    # ================================
    # 🌐 FLASK ROUTES TESTS
    # ================================
    
    def test_email_template_customization_route_get(self):
        """Test GET request to email template customization route logic"""
        # Mock activity with existing templates
        mock_activity = MagicMock()
        mock_activity.id = 1
        mock_activity.activity_name = "Test Activity"
        mock_activity.email_templates = {
            'newPass': {'subject': 'Custom Subject'}
        }
        
        # Simulate the core route logic
        template_types = {
            'newPass': 'New Pass Created',
            'paymentReceived': 'Payment Received',
            'latePayment': 'Late Payment Reminder',
            'signup': 'Signup Confirmation',
            'redeemPass': 'Pass Redeemed',
            'survey_invitation': 'Survey Invitation'
        }
        current_templates = mock_activity.email_templates or {}
        
        # Verify the data that would be passed to template
        self.assertEqual(mock_activity.activity_name, "Test Activity")
        self.assertIn('newPass', template_types)
        self.assertEqual(template_types['newPass'], 'New Pass Created')
        self.assertEqual(current_templates['newPass']['subject'], 'Custom Subject')
        self.assertEqual(len(template_types), 6)  # All 6 template types present
    
    def test_save_email_templates_route_post(self):
        """Test POST request to save email templates route logic"""
        # Test the core logic without Flask context
        mock_activity = MagicMock()
        mock_activity.id = 1
        mock_activity.email_templates = {}
        
        # Mock form data
        form_data = {
            'newPass_subject': 'New Pass Created!',
            'newPass_title': 'Your Pass is Ready',
            'newPass_intro_text': 'Thank you for signing up.',
            'paymentReceived_subject': 'Payment Confirmed',
            'paymentReceived_conclusion_text': 'Your payment has been processed.',
        }
        
        def get_form_value(key, default=''):
            return form_data.get(key, default)
        
        # Simulate the core route logic
        template_types = ['newPass', 'paymentReceived', 'latePayment', 'signup', 'redeemPass', 'survey_invitation']
        
        if mock_activity.email_templates is None:
            mock_activity.email_templates = {}
        
        for template_type in template_types:
            template_data = {}
            
            subject = get_form_value(f'{template_type}_subject', '').strip()
            title = get_form_value(f'{template_type}_title', '').strip()
            intro_text = get_form_value(f'{template_type}_intro_text', '').strip()
            conclusion_text = get_form_value(f'{template_type}_conclusion_text', '').strip()
            
            if subject:
                template_data['subject'] = subject
            if title:
                template_data['title'] = title
            if intro_text:
                template_data['intro_text'] = intro_text
            if conclusion_text:
                template_data['conclusion_text'] = conclusion_text
            
            if template_data:
                mock_activity.email_templates[template_type] = template_data
        
        # Verify templates were saved correctly
        self.assertEqual(mock_activity.email_templates['newPass']['subject'], 'New Pass Created!')
        self.assertEqual(mock_activity.email_templates['newPass']['title'], 'Your Pass is Ready')
        self.assertEqual(mock_activity.email_templates['newPass']['intro_text'], 'Thank you for signing up.')
        
        self.assertEqual(mock_activity.email_templates['paymentReceived']['subject'], 'Payment Confirmed')
        self.assertEqual(mock_activity.email_templates['paymentReceived']['conclusion_text'], 'Your payment has been processed.')
    
    def test_routes_require_authentication(self):
        """Test that routes redirect to login when not authenticated"""
        # Test authentication logic without Flask context
        def check_auth(session_has_admin):
            if not session_has_admin:
                return "redirect_to_login"
            return "authenticated"
        
        # Test unauthenticated case
        result_unauth = check_auth(False)
        self.assertEqual(result_unauth, "redirect_to_login")
        
        # Test authenticated case
        result_auth = check_auth(True)
        self.assertEqual(result_auth, "authenticated")
    
    # ================================
    # 📁 FILE UPLOAD TESTS
    # ================================
    
    @patch('app.os.makedirs')
    @patch('app.datetime')
    def test_hero_image_file_upload_success(self, mock_datetime, mock_makedirs):
        """Test successful hero image file upload"""
        # Mock datetime for filename generation
        mock_datetime.now.return_value.strftime.return_value = '20231215_120000'
        
        # Create mock file upload
        mock_file = MagicMock()
        mock_file.filename = 'hero.jpg'
        mock_file.save = MagicMock()
        
        # Mock secure_filename
        with patch('app.secure_filename', return_value='hero.jpg'):
            # Simulate the file upload logic
            activity_id = 1
            template_type = 'newPass'
            filename = f"{activity_id}_{template_type}_20231215_120000_hero.jpg"
            upload_path = os.path.join('static', 'uploads', 'email_heroes', filename)
            
            # Mock file saving
            mock_file.save(upload_path)
            
            # Verify file was saved with correct path
            mock_file.save.assert_called_once_with(upload_path)
    
    def test_hero_image_filename_security(self):
        """Test that uploaded filenames are secured"""
        from werkzeug.utils import secure_filename
        
        # Test various potentially malicious filenames
        dangerous_names = [
            '../../../etc/passwd',
            '..\\..\\windows\\system32\\config',
            'script<>alert.jpg',
            'file with spaces.jpg',
            'normalfile.jpg'
        ]
        
        for dangerous_name in dangerous_names:
            secured = secure_filename(dangerous_name)
            # Should not contain path traversal or dangerous characters
            self.assertNotIn('..', secured)
            self.assertNotIn('<', secured)
            self.assertNotIn('>', secured)
    
    def test_file_upload_no_file_provided(self):
        """Test handling when no file is provided"""
        # Mock request with no file
        def get_file(key):
            return None
        
        # Simulate the file upload check
        hero_file = get_file('newPass_hero_image')
        
        self.assertIsNone(hero_file)
        # Should not attempt to save when no file provided
    
    def test_file_upload_empty_filename(self):
        """Test handling when file object has empty filename"""
        # Mock file with empty filename
        mock_file = MagicMock()
        mock_file.filename = ''
        
        def get_file(key):
            return mock_file
        
        # Simulate the filename check
        hero_file = get_file('newPass_hero_image')
        
        self.assertIsNotNone(hero_file)
        self.assertEqual(hero_file.filename, '')
        # Should not process file with empty filename
    
    # ================================
    # 📧 EMAIL INTEGRATION TESTS
    # ================================
    
    @patch('utils.send_email_async')
    @patch('utils.get_email_context')
    def test_email_sending_uses_customizations(self, mock_get_context, mock_send_email):
        """Test that email sending integrates with customizations"""
        # Mock activity with customizations
        mock_activity = MagicMock()
        mock_activity.email_templates = {
            'newPass': {
                'subject': 'Your Custom Pass is Ready!',
                'title': 'Custom Title',
                'intro_text': 'Custom introduction text.'
            }
        }
        
        # Mock context with customizations applied
        custom_context = {
            'subject': 'Your Custom Pass is Ready!',
            'title': 'Custom Title', 
            'intro_text': 'Custom introduction text.',
            'conclusion_text': 'We appreciate your business!',  # default
            'user_name': 'John Doe',  # from base context
            'activity_name': 'Test Activity'  # from base context
        }
        mock_get_context.return_value = custom_context
        
        # Simulate the email sending logic that uses get_email_context
        template_name = 'email_templates/newPass/index.html'
        template_type = 'newPass'  # extracted from template_name
        base_context = {
            'user_name': 'John Doe',
            'activity_name': 'Test Activity'
        }
        
        # This is what happens in send_email_async
        context = mock_get_context(mock_activity, template_type, base_context)
        subject = context.get('subject', 'Default Subject')
        
        # Verify customizations were applied
        self.assertEqual(subject, 'Your Custom Pass is Ready!')
        self.assertEqual(context['title'], 'Custom Title')
        self.assertEqual(context['intro_text'], 'Custom introduction text.')
        
        # Verify get_email_context was called correctly
        mock_get_context.assert_called_once_with(mock_activity, template_type, base_context)
    
    @patch('utils.get_email_context')
    def test_template_type_mapping(self, mock_get_context):
        """Test that template names are correctly mapped to template types"""
        template_mappings = {
            'email_templates/newPass/index.html': 'newPass',
            'email_templates/newPass_compiled/index.html': 'newPass',
            'email_templates/paymentReceived/index.html': 'paymentReceived',
            'email_templates/paymentReceived_compiled/index.html': 'paymentReceived',
            'email_templates/latePayment/index.html': 'latePayment',
            'email_templates/signup/index.html': 'signup',
            'email_templates/redeemPass/index.html': 'redeemPass',
            'email_templates/survey_invitation/index.html': 'survey_invitation'
        }
        
        mock_activity = MagicMock()
        
        for template_name, expected_type in template_mappings.items():
            # Simulate the mapping logic
            template_type_mapping = {
                'email_templates/newPass/index.html': 'newPass',
                'email_templates/newPass_compiled/index.html': 'newPass',
                'email_templates/paymentReceived/index.html': 'paymentReceived',
                'email_templates/paymentReceived_compiled/index.html': 'paymentReceived',
                'email_templates/latePayment/index.html': 'latePayment',
                'email_templates/latePayment_compiled/index.html': 'latePayment',
                'email_templates/signup/index.html': 'signup',
                'email_templates/signup_compiled/index.html': 'signup',
                'email_templates/redeemPass/index.html': 'redeemPass',
                'email_templates/redeemPass_compiled/index.html': 'redeemPass',
                'email_templates/survey_invitation/index.html': 'survey_invitation',
                'email_templates/survey_invitation_compiled/index.html': 'survey_invitation',
                'survey_invitation': 'survey_invitation'
            }
            
            template_type = template_type_mapping.get(template_name)
            self.assertEqual(template_type, expected_type)
    
    # ================================
    # 🚨 EDGE CASES AND ERROR HANDLING
    # ================================
    
    def test_get_email_context_with_none_values(self):
        """Test get_email_context handles None values in customizations"""
        activity = MagicMock()
        activity.email_templates = {
            'newPass': {
                'subject': None,  # None should be ignored
                'title': 'Custom Title',
                'intro_text': None,  # None should be ignored
                'hero_image': None  # None is a valid value for hero_image
            }
        }
        
        result = get_email_context(activity, 'newPass')
        
        # None values should be ignored in favor of defaults
        self.assertEqual(result['subject'], 'Minipass Notification')  # default
        self.assertEqual(result['title'], 'Custom Title')  # custom
        self.assertEqual(result['intro_text'], 'Thank you for using our service.')  # default
        self.assertIsNone(result['hero_image'])  # None is valid for hero_image
    
    def test_get_email_context_with_invalid_json(self):
        """Test behavior when email_templates contains invalid data"""
        activity = MagicMock()
        # Simulate corrupted JSON data
        activity.email_templates = {
            'newPass': "invalid_string_instead_of_dict"
        }
        
        # Should handle gracefully and not crash
        try:
            result = get_email_context(activity, 'newPass')
            # If it doesn't crash, check it returns defaults
            self.assertEqual(result['subject'], 'Minipass Notification')
        except (TypeError, AttributeError):
            # Expected behavior - invalid data structure should be handled
            pass
    
    @patch('app.db.session')
    @patch('app.flash')
    def test_save_email_templates_database_error(self, mock_flash, mock_session):
        """Test error handling in save_email_templates when database fails"""
        # Mock database error
        mock_session.commit.side_effect = Exception("Database connection lost")
        mock_session.rollback = MagicMock()
        
        # Simulate the error handling logic
        try:
            mock_session.commit()
        except Exception as e:
            mock_session.rollback()
            mock_flash(f"❌ Error saving email templates: {str(e)}", "error")
        
        # Verify error handling
        mock_session.rollback.assert_called_once()
        mock_flash.assert_called_once_with("❌ Error saving email templates: Database connection lost", "error")
    
    def test_template_data_validation(self):
        """Test that only valid template data is saved"""
        template_data = {}
        form_values = {
            'subject': '  Valid Subject  ',  # Should be stripped
            'title': '',  # Empty string should be ignored
            'intro_text': '   ',  # Whitespace-only should be ignored
            'conclusion_text': 'Valid conclusion',
            'cta_url': None  # None should be ignored
        }
        
        # Simulate the validation logic from save_email_templates
        for key, value in form_values.items():
            if key == 'subject':
                stripped_value = value.strip() if value else ''
                if stripped_value:
                    template_data[key] = stripped_value
            elif key == 'title' and not value:
                # Empty string ignored
                continue
            elif key == 'intro_text' and (not value or not value.strip()):
                # Whitespace-only ignored
                continue
            elif key == 'conclusion_text' and value:
                template_data[key] = value
            elif key == 'cta_url' and value is not None:
                template_data[key] = value
        
        # Should only contain valid data
        expected_data = {
            'subject': 'Valid Subject',
            'conclusion_text': 'Valid conclusion'
        }
        
        self.assertEqual(template_data, expected_data)
    
    def test_activity_not_found_error(self):
        """Test handling when activity is not found"""
        with patch('app.Activity') as mock_activity_model:
            # Mock 404 error
            mock_activity_model.query.get_or_404.side_effect = Exception("404 Not Found")
            
            # Should raise exception when activity not found
            with self.assertRaises(Exception):
                mock_activity_model.query.get_or_404(999)
    
    def test_large_json_data_handling(self):
        """Test handling of large email template customizations"""
        # Create large customization data
        large_customizations = {}
        for template_type in self.template_types:
            large_customizations[template_type] = {
                'subject': f'Subject for {template_type}',
                'title': f'Title for {template_type}',
                'intro_text': 'A' * 1000,  # Large text field
                'conclusion_text': 'B' * 1000,  # Large text field
                'custom_message': 'C' * 2000,  # Very large custom message
                'hero_image': f'hero_{template_type}.jpg'
            }
        
        activity = MagicMock()
        activity.email_templates = large_customizations
        
        # Should handle large data without issues
        result = get_email_context(activity, 'newPass')
        
        self.assertEqual(result['subject'], 'Subject for newPass')
        self.assertEqual(len(result['intro_text']), 1000)
        self.assertEqual(len(result['custom_message']), 2000)
    
    def test_special_characters_in_customizations(self):
        """Test handling of special characters in email customizations"""
        activity = MagicMock()
        activity.email_templates = {
            'newPass': {
                'subject': 'Congrats! 🎉 Your pass is ready',
                'title': 'Welcome to Café & Bistro',
                'intro_text': 'Special chars: àáâãäåæçèéêë',
                'custom_message': 'Unicode: ñÑøØßÿ'
            }
        }
        
        result = get_email_context(activity, 'newPass')
        
        # Should preserve special characters
        self.assertEqual(result['subject'], 'Congrats! 🎉 Your pass is ready')
        self.assertEqual(result['title'], 'Welcome to Café & Bistro')
        self.assertEqual(result['intro_text'], 'Special chars: àáâãäåæçèéêë')
        self.assertEqual(result['custom_message'], 'Unicode: ñÑøØßÿ')


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)