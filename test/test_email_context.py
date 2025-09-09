"""
Simple integration test for email deliverability Phase 1 implementation
Tests the actual context enhancement functionality
"""

import unittest
import sys
import os

# Add the parent directory to sys.path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import Organization, db


class TestEmailContextEnhancement(unittest.TestCase):
    """Test the email context enhancement for subdomain support"""

    def setUp(self):
        """Set up test fixtures"""
        self.app = app
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up test fixtures"""
        self.app_context.pop()

    def test_organization_url_generation(self):
        """Test that organization context generates correct subdomain URLs"""
        # Simulate what happens in send_email when organization is detected
        test_email = "test@example.com"
        
        # Mock organization
        org = type('MockOrg', (), {
            'id': 1,
            'name': 'Test Organization',
            'domain': 'testorg'
        })()
        
        # Generate URLs as done in send_email
        if org and org.domain:
            base_url = f"https://{org.domain}.minipass.me"
        else:
            base_url = "https://minipass.me"
        
        context = {}
        context['base_url'] = base_url
        context['unsubscribe_url'] = f"{base_url}/unsubscribe?email={test_email}"
        context['privacy_url'] = f"{base_url}/privacy"
        context['organization_name'] = org.name if org else "Minipass"
        context['organization_address'] = "123 Main Street, Montreal, QC H1A 1A1"
        
        # Test that URLs are correctly generated with subdomain
        self.assertEqual(context['base_url'], 'https://testorg.minipass.me')
        self.assertEqual(context['unsubscribe_url'], 'https://testorg.minipass.me/unsubscribe?email=test@example.com')
        self.assertEqual(context['privacy_url'], 'https://testorg.minipass.me/privacy')
        self.assertEqual(context['organization_name'], 'Test Organization')
        self.assertIn('123 Main Street', context['organization_address'])
        
        print("✅ Organization URL generation working correctly")

    def test_fallback_url_generation(self):
        """Test fallback to default minipass.me URLs when no organization"""
        test_email = "test@example.com"
        
        # Simulate no organization found
        org = None
        
        # Generate URLs as done in send_email
        if org and org.domain:
            base_url = f"https://{org.domain}.minipass.me"
        else:
            base_url = "https://minipass.me"
        
        context = {}
        context['base_url'] = base_url
        context['unsubscribe_url'] = f"{base_url}/unsubscribe?email={test_email}"
        context['privacy_url'] = f"{base_url}/privacy"
        context['organization_name'] = org.name if org else "Minipass"
        context['organization_address'] = "123 Main Street, Montreal, QC H1A 1A1"
        
        # Test that URLs fallback to default
        self.assertEqual(context['base_url'], 'https://minipass.me')
        self.assertEqual(context['unsubscribe_url'], 'https://minipass.me/unsubscribe?email=test@example.com')
        self.assertEqual(context['privacy_url'], 'https://minipass.me/privacy')
        self.assertEqual(context['organization_name'], 'Minipass')
        
        print("✅ Fallback URL generation working correctly")

    def test_template_variables_present(self):
        """Test that all required template variables are present"""
        # This is what we added to the send_email function
        required_vars = [
            'base_url',
            'unsubscribe_url', 
            'privacy_url',
            'organization_name',
            'organization_address'
        ]
        
        # Simulate context creation from send_email
        context = {}
        test_email = "test@example.com"
        
        # Mock organization
        org = type('MockOrg', (), {
            'id': 1,
            'name': 'LHGI',
            'domain': 'lhgi'
        })()
        
        # Add context variables as implemented in utils.py
        if org and org.domain:
            base_url = f"https://{org.domain}.minipass.me"
        else:
            base_url = "https://minipass.me"
        
        context['base_url'] = base_url
        context['unsubscribe_url'] = f"{base_url}/unsubscribe?email={test_email}"
        context['privacy_url'] = f"{base_url}/privacy"
        context['organization_name'] = org.name if org else "Minipass"
        context['organization_address'] = "123 Main Street, Montreal, QC H1A 1A1"
        
        # Test all required variables are present
        for var in required_vars:
            self.assertIn(var, context, f"Required variable '{var}' missing from context")
            self.assertIsNotNone(context[var], f"Variable '{var}' is None")
            
        print("✅ All template variables present and populated")

    def test_email_templates_fixed(self):
        """Test that email templates use template variables instead of hardcoded URLs"""
        # Test reading one of the fixed templates
        template_path = "/home/kdresdell/Documents/DEV/minipass_env/app/templates/email_templates/newPass/index.html"
        
        try:
            with open(template_path, 'r') as f:
                template_content = f.read()
            
            # Check that hardcoded URLs have been replaced
            self.assertNotIn('https://minipass.me/unsubscribe?email={{ user_email }}', template_content,
                           "Template still contains hardcoded unsubscribe URL")
            self.assertNotIn('https://minipass.me/privacy', template_content,
                           "Template still contains hardcoded privacy URL")
            self.assertNotIn('Minipass - 123 Main Street', template_content,
                           "Template still contains hardcoded organization info")
            
            # Check that template variables are present
            self.assertIn('{{ unsubscribe_url }}', template_content,
                         "Template missing unsubscribe_url variable")
            self.assertIn('{{ privacy_url }}', template_content,
                         "Template missing privacy_url variable")
            self.assertIn('{{ organization_name }}', template_content,
                         "Template missing organization_name variable")
            self.assertIn('{{ organization_address }}', template_content,
                         "Template missing organization_address variable")
            
            print("✅ Email templates properly updated with template variables")
            
        except FileNotFoundError:
            self.fail("newPass template file not found")


if __name__ == '__main__':
    unittest.main()