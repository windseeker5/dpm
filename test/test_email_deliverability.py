"""
Unit tests for email deliverability fixes in Phase 1
Tests organization detection, URL generation, and template context
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to sys.path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Flask app to create application context
from app import app


class TestEmailDeliverability(unittest.TestCase):
    """Test the email deliverability improvements"""

    def setUp(self):
        """Set up test fixtures"""
        self.app = app
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        self.test_email = "test@example.com"
        self.test_subject = "Test Email"
        
        # Mock organization
        self.mock_org = Mock()
        self.mock_org.id = 1
        self.mock_org.name = "Test Organization"
        self.mock_org.domain = "testorg"
        
        # Mock user without opt-out
        self.mock_user = Mock()
        self.mock_user.email_opt_out = False

    def tearDown(self):
        """Clean up test fixtures"""
        self.app_context.pop()

    @patch('models.User')
    @patch('models.Organization')
    @patch('flask.session')
    @patch('flask.render_template')
    @patch('premailer.transform')
    @patch('smtplib.SMTP')
    def test_organization_detection_from_context(self, mock_smtp, mock_transform, 
                                                 mock_render, mock_session, 
                                                 mock_org_model, mock_user_model):
        """Test organization detection when organization_id is in context"""
        
        # Setup mocks
        mock_user_model.query.filter_by.return_value.first.return_value = self.mock_user
        mock_org_model.query.get.return_value = self.mock_org
        mock_render.return_value = "<html>Test</html>"
        mock_transform.return_value = "<html>Test</html>"
        
        # Mock SMTP server
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        
        # Test context with organization_id
        context = {'organization_id': 1}
        
        with patch('utils.get_setting') as mock_get_setting:
            mock_get_setting.side_effect = lambda key, default=None: {
                'MAIL_DEFAULT_SENDER': 'noreply@minipass.me',
                'MAIL_SENDER_NAME': 'Minipass',
                'MAIL_SERVER': 'localhost',
                'MAIL_PORT': '587',
                'MAIL_USERNAME': 'test',
                'MAIL_PASSWORD': 'test',
                'MAIL_USE_TLS': 'true'
            }.get(key, default)
            
            result = send_email(
                subject=self.test_subject,
                to_email=self.test_email,
                template_name="test_template.html",
                context=context
            )
        
        # Verify organization was detected
        mock_org_model.query.get.assert_called_with(1)
        
        # Check that template was rendered with enhanced context
        mock_render.assert_called_once()
        render_args, render_kwargs = mock_render.call_args
        
        # Verify context includes organization-specific URLs
        self.assertEqual(render_kwargs['base_url'], 'https://testorg.minipass.me')
        self.assertEqual(render_kwargs['unsubscribe_url'], f'https://testorg.minipass.me/unsubscribe?email={self.test_email}')
        self.assertEqual(render_kwargs['privacy_url'], 'https://testorg.minipass.me/privacy')
        self.assertEqual(render_kwargs['organization_name'], 'Test Organization')

    @patch('utils.User')
    @patch('utils.Organization')
    @patch('utils.session')
    @patch('utils.render_template')
    @patch('utils.transform')
    @patch('utils.smtplib.SMTP')
    def test_organization_detection_from_session(self, mock_smtp, mock_transform, 
                                                 mock_render, mock_session, 
                                                 mock_org_model, mock_user_model):
        """Test organization detection when organization_domain is in session"""
        
        # Setup mocks
        mock_user_model.query.filter_by.return_value.first.return_value = self.mock_user
        mock_org_model.query.filter_by.return_value.first.return_value = self.mock_org
        mock_render.return_value = "<html>Test</html>"
        mock_transform.return_value = "<html>Test</html>"
        mock_session.__contains__ = lambda key: key == 'organization_domain'
        mock_session.__getitem__ = lambda key: 'testorg' if key == 'organization_domain' else None
        
        # Mock SMTP server
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        
        # Test empty context (should use session)
        context = {}
        
        with patch('utils.get_setting') as mock_get_setting:
            mock_get_setting.side_effect = lambda key, default=None: {
                'MAIL_DEFAULT_SENDER': 'noreply@minipass.me',
                'MAIL_SENDER_NAME': 'Minipass',
                'MAIL_SERVER': 'localhost',
                'MAIL_PORT': '587',
                'MAIL_USERNAME': 'test',
                'MAIL_PASSWORD': 'test',
                'MAIL_USE_TLS': 'true'
            }.get(key, default)
            
            result = send_email(
                subject=self.test_subject,
                to_email=self.test_email,
                template_name="test_template.html",
                context=context
            )
        
        # Verify organization was detected from session
        mock_org_model.query.filter_by.assert_called_with(domain='testorg')

    @patch('utils.User')
    @patch('utils.Organization')
    @patch('utils.session')
    @patch('utils.render_template')
    @patch('utils.transform')
    @patch('utils.smtplib.SMTP')
    def test_fallback_to_default_minipass_urls(self, mock_smtp, mock_transform, 
                                               mock_render, mock_session, 
                                               mock_org_model, mock_user_model):
        """Test fallback to default minipass.me URLs when no organization found"""
        
        # Setup mocks
        mock_user_model.query.filter_by.return_value.first.return_value = self.mock_user
        mock_org_model.query.get.return_value = None  # No organization found
        mock_render.return_value = "<html>Test</html>"
        mock_transform.return_value = "<html>Test</html>"
        mock_session.__contains__ = lambda key: False
        
        # Mock SMTP server
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        
        context = {}
        
        with patch('utils.get_setting') as mock_get_setting:
            mock_get_setting.side_effect = lambda key, default=None: {
                'MAIL_DEFAULT_SENDER': 'noreply@minipass.me',
                'MAIL_SENDER_NAME': 'Minipass',
                'MAIL_SERVER': 'localhost',
                'MAIL_PORT': '587',
                'MAIL_USERNAME': 'test',
                'MAIL_PASSWORD': 'test',
                'MAIL_USE_TLS': 'true'
            }.get(key, default)
            
            result = send_email(
                subject=self.test_subject,
                to_email=self.test_email,
                template_name="test_template.html",
                context=context
            )
        
        # Check that template was rendered with default URLs
        mock_render.assert_called_once()
        render_args, render_kwargs = mock_render.call_args
        
        # Verify context includes default URLs
        self.assertEqual(render_kwargs['base_url'], 'https://minipass.me')
        self.assertEqual(render_kwargs['unsubscribe_url'], f'https://minipass.me/unsubscribe?email={self.test_email}')
        self.assertEqual(render_kwargs['privacy_url'], 'https://minipass.me/privacy')
        self.assertEqual(render_kwargs['organization_name'], 'Minipass')

    @patch('utils.User')
    def test_email_opt_out_blocking(self, mock_user_model):
        """Test that emails are blocked for users who have opted out"""
        
        # Mock user with opt-out enabled
        mock_user_opted_out = Mock()
        mock_user_opted_out.email_opt_out = True
        mock_user_model.query.filter_by.return_value.first.return_value = mock_user_opted_out
        
        result = send_email(
            subject=self.test_subject,
            to_email=self.test_email,
            template_name="test_template.html",
            context={}
        )
        
        # Should return False for opted-out users
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()