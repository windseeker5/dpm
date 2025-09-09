import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock
from email.mime.multipart import MIMEMultipart


class TestEmailDeliverabilityPhase1(unittest.TestCase):
    """Test Phase 1 of email deliverability improvements"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock Flask app context
        self.mock_app = MagicMock()
        self.mock_db = MagicMock()
        
    @patch('utils.get_setting')
    @patch('utils.User')  
    @patch('smtplib.SMTP')
    def test_email_headers_added(self, mock_smtp, mock_user_model, mock_get_setting):
        """Test that deliverability headers are added to emails"""
        from utils import send_email
        
        # Setup mocks
        mock_get_setting.side_effect = lambda key, default=None: {
            'MAIL_DEFAULT_SENDER': 'test@minipass.me',
            'MAIL_SENDER_NAME': 'Minipass Test',
            'MAIL_SERVER': 'smtp.test.com',
            'MAIL_PORT': 587,
            'MAIL_USERNAME': 'testuser',
            'MAIL_PASSWORD': 'testpass',
            'MAIL_USE_TLS': 'true'
        }.get(key, default)
        
        # Mock user lookup (no opt-out)
        mock_user = MagicMock()
        mock_user.email_opt_out = False
        mock_user_model.query.filter_by.return_value.first.return_value = mock_user
        
        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        # Mock render_template
        with patch('utils.render_template', return_value='<html>Test Email</html>'):
            with patch('utils.transform', return_value='<html>Test Email</html>'):
                # Call send_email
                result = send_email(
                    subject="Test Subject",
                    to_email="test@example.com",
                    template_name="test_template",
                    context={'activity_name': 'Test Activity'}
                )
        
        # Verify SMTP was called
        mock_server.sendmail.assert_called_once()
        
        # Get the message that was sent
        call_args = mock_server.sendmail.call_args[0]
        message_str = call_args[2]
        
        # Check that required headers are present
        self.assertIn('Reply-To:', message_str)
        self.assertIn('List-Unsubscribe:', message_str)
        self.assertIn('List-Unsubscribe-Post: List-Unsubscribe=One-Click', message_str)
        self.assertIn('Precedence: bulk', message_str)
        self.assertIn('X-Mailer: Minipass/1.0', message_str)
        self.assertIn('Message-ID:', message_str)
        
    @patch('utils.User')
    def test_opt_out_blocks_email(self, mock_user_model):
        """Test that emails are blocked for opted-out users"""
        from utils import send_email
        
        # Mock user with opt-out enabled
        mock_user = MagicMock()
        mock_user.email_opt_out = True
        mock_user_model.query.filter_by.return_value.first.return_value = mock_user
        
        # Call send_email
        result = send_email(
            subject="Test Subject",
            to_email="opted_out@example.com",
            template_name="test_template",
            context={'activity_name': 'Test Activity'}
        )
        
        # Should return False (blocked)
        self.assertFalse(result)
        
    @patch('utils.User')
    def test_non_existent_user_sends_email(self, mock_user_model):
        """Test that emails send normally for non-existent users"""
        from utils import send_email
        
        # Mock no user found
        mock_user_model.query.filter_by.return_value.first.return_value = None
        
        with patch('utils.get_setting') as mock_get_setting:
            mock_get_setting.side_effect = lambda key, default=None: {
                'MAIL_DEFAULT_SENDER': 'test@minipass.me',
                'MAIL_SENDER_NAME': 'Minipass Test',
                'MAIL_SERVER': 'smtp.test.com',
                'MAIL_PORT': 587,
                'MAIL_USERNAME': 'testuser', 
                'MAIL_PASSWORD': 'testpass',
                'MAIL_USE_TLS': 'true'
            }.get(key, default)
            
            with patch('smtplib.SMTP') as mock_smtp:
                mock_server = MagicMock()
                mock_smtp.return_value = mock_server
                
                with patch('utils.render_template', return_value='<html>Test</html>'):
                    with patch('utils.transform', return_value='<html>Test</html>'):
                        result = send_email(
                            subject="Test Subject",
                            to_email="newuser@example.com",
                            template_name="test_template",
                            context={'activity_name': 'Test Activity'}
                        )
        
        # Should not return False (should send)
        self.assertNotEqual(result, False)


class TestUnsubscribeEndpoint(unittest.TestCase):
    """Test the unsubscribe endpoint functionality"""
    
    def setUp(self):
        """Set up Flask test client"""
        # This would normally set up Flask test client
        # For now, we'll test the logic components
        pass
        
    def test_unsubscribe_form_renders(self):
        """Test that unsubscribe form renders correctly"""
        # Since we're using string templates, test the HTML structure
        from app import unsubscribe
        
        # Mock Flask request
        with patch('app.request') as mock_request:
            mock_request.method = 'GET'
            mock_request.args.get.side_effect = lambda key, default='': {
                'email': 'test@example.com',
                'token': 'testtoken'
            }.get(key, default)
            
            response = unsubscribe()
            
            # Check that form elements are present
            self.assertIn('<title>Unsubscribe - Minipass</title>', response)
            self.assertIn('type="email"', response)
            self.assertIn('name="email"', response)
            self.assertIn('value="test@example.com"', response)
            
    @patch('app.User')
    @patch('app.db')
    def test_unsubscribe_existing_user(self, mock_db, mock_user_model):
        """Test unsubscribing an existing user"""
        from app import unsubscribe
        
        # Mock existing user
        mock_user = MagicMock()
        mock_user.email_opt_out = False
        mock_user_model.query.filter_by.return_value.first.return_value = mock_user
        
        # Mock Flask request for POST
        with patch('app.request') as mock_request:
            mock_request.method = 'POST'
            mock_request.form.get.side_effect = lambda key, default='': {
                'email': 'test@example.com',
                'token': 'testtoken'
            }.get(key, default)
            
            response = unsubscribe()
            
            # Verify user was opted out
            self.assertTrue(mock_user.email_opt_out)
            mock_db.session.commit.assert_called_once()
            
            # Check success message
            self.assertIn('Unsubscribed Successfully', response)
            self.assertIn('test@example.com', response)


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)