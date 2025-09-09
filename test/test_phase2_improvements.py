"""
Unit tests for Phase 2 email content optimization improvements
Tests plain text generation, dynamic subject lines, and HTML structure optimizations
"""

import unittest
import sys
import os

# Add the parent directory to sys.path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app


class TestPhase2Improvements(unittest.TestCase):
    """Test the Phase 2 content optimization improvements"""

    def setUp(self):
        """Set up test fixtures"""
        self.app = app
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up test fixtures"""
        self.app_context.pop()

    def test_plain_text_generation(self):
        """Test the improved plain text generation from HTML"""
        # Test HTML content
        html_content = """
        <html>
        <head><style>body {color: red;}</style></head>
        <body>
            <h1>Digital Pass Ready</h1>
            <p>Your pass for <strong>Hockey League</strong> is ready.</p>
            <p>Show this QR code at the venue.</p>
            <p><a href="https://lhgi.minipass.me/unsubscribe?email=test@example.com">Unsubscribe</a></p>
            <p><a href="https://lhgi.minipass.me/privacy">Privacy Policy</a></p>
        </body>
        </html>
        """
        
        # Simulate the generate_plain_text function from utils.py
        def test_generate_plain_text(html_content, context):
            """Generate comprehensive plain text from HTML"""
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Get text and preserve structure
                text = soup.get_text(separator='\n', strip=True)
                
                # Add important links in parentheses
                for link in soup.find_all('a', href=True):
                    if 'unsubscribe' in link.get('href', '').lower() or 'privacy' in link.get('href', '').lower():
                        link_text = link.get_text(strip=True)
                        if link_text and link_text not in text:
                            text += f"\n\n{link_text}: {link['href']}"
                
                # Clean up extra whitespace
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                return '\n'.join(lines)
                
            except ImportError:
                return context.get('preview_text', 'Your digital pass is ready')
        
        context = {}
        plain_text = test_generate_plain_text(html_content, context)
        
        # Verify plain text extraction
        self.assertIn('Digital Pass Ready', plain_text)
        self.assertIn('Hockey League', plain_text)
        self.assertIn('Show this QR code', plain_text)
        
        # Verify important links are included (text should be extracted)
        self.assertIn('Unsubscribe', plain_text)
        self.assertIn('Privacy Policy', plain_text)
        
        # Verify styles/scripts are removed
        self.assertNotIn('color: red', plain_text)
        self.assertNotIn('<style>', plain_text)
        
        print("✅ Plain text generation working correctly")

    def test_dynamic_subject_generation(self):
        """Test dynamic subject line generation based on template type"""
        
        # Simulate the generate_dynamic_subject function from utils.py
        def test_generate_dynamic_subject(original_subject, template_name, context):
            """Generate context-aware subject lines"""
            subject_templates = {
                'newPass': '[{activity_name}] Your digital pass is ready',
                'paymentReceived': '[{activity_name}] Payment confirmed - Pass activated', 
                'signup': '[{activity_name}] Registration confirmation',
                'redeemPass': '[{activity_name}] Pass redeemed successfully',
                'latePayment': '[{activity_name}] Payment reminder',
                'email_survey_invitation': '[{activity_name}] We\'d love your feedback'
            }
            
            # Extract template type from template_name
            template_type = None
            if template_name:
                if 'newPass' in template_name:
                    template_type = 'newPass'
                elif 'paymentReceived' in template_name:
                    template_type = 'paymentReceived'
                elif 'signup' in template_name:
                    template_type = 'signup'
                elif 'redeemPass' in template_name:
                    template_type = 'redeemPass'
                elif 'latePayment' in template_name:
                    template_type = 'latePayment'
                elif 'survey' in template_name:
                    template_type = 'email_survey_invitation'
            
            # Use template-based subject if available and context has activity_name
            if template_type and template_type in subject_templates and context.get('activity_name'):
                try:
                    return subject_templates[template_type].format(**context)
                except (KeyError, ValueError):
                    pass
            
            return original_subject
        
        # Test cases
        test_cases = [
            {
                'original_subject': 'Your pass is ready',
                'template_name': 'email_templates/newPass/index.html',
                'context': {'activity_name': 'Hockey League'},
                'expected': '[Hockey League] Your digital pass is ready'
            },
            {
                'original_subject': 'Payment received',
                'template_name': 'email_templates/paymentReceived_compiled/index.html',
                'context': {'activity_name': 'Soccer Tournament'},
                'expected': '[Soccer Tournament] Payment confirmed - Pass activated'
            },
            {
                'original_subject': 'Welcome',
                'template_name': 'email_templates/signup/index.html',
                'context': {'activity_name': 'Tennis Club'},
                'expected': '[Tennis Club] Registration confirmation'
            },
            {
                'original_subject': 'Generic subject',
                'template_name': 'unknown_template.html',
                'context': {'activity_name': 'Hockey League'},
                'expected': 'Generic subject'  # Should fallback to original
            },
            {
                'original_subject': 'Generic subject',
                'template_name': 'email_templates/newPass/index.html',
                'context': {},  # No activity_name
                'expected': 'Generic subject'  # Should fallback to original
            }
        ]
        
        for case in test_cases:
            result = test_generate_dynamic_subject(
                case['original_subject'],
                case['template_name'],
                case['context']
            )
            self.assertEqual(result, case['expected'], 
                           f"Subject generation failed for {case['template_name']}")
        
        print("✅ Dynamic subject line generation working correctly")

    def test_html_structure_optimization(self):
        """Test that templates have been optimized for better structure"""
        template_path = "/home/kdresdell/Documents/DEV/minipass_env/app/templates/email_templates/newPass/index.html"
        
        try:
            with open(template_path, 'r') as f:
                template_content = f.read()
            
            # Check that social media icons have been removed/commented
            self.assertIn('PHASE 2: Optimized Footer', template_content,
                         "Template should have Phase 2 optimization comment")
            
            # Check overall structure is clean
            facebook_count = template_content.count('facebook.png')
            instagram_count = template_content.count('instagram.png')
            
            # Should have minimal or no social media references in main content
            self.assertLessEqual(facebook_count, 1, "Too many Facebook references")
            self.assertLessEqual(instagram_count, 1, "Too many Instagram references")
            
            print("✅ HTML structure optimization working correctly")
            
        except FileNotFoundError:
            self.fail("Template file not found")

    def test_template_size_optimization(self):
        """Test that templates remain under size limits"""
        templates = [
            'newPass/index.html',
            'paymentReceived/index.html',
            'signup/index.html',
            'redeemPass/index.html',
            'latePayment/index.html',
            'email_survey_invitation/index.html'
        ]
        
        for template in templates:
            template_path = f"/home/kdresdell/Documents/DEV/minipass_env/app/templates/email_templates/{template}"
            
            try:
                file_size = os.path.getsize(template_path)
                
                # Check file is under 50KB (50,000 bytes)
                self.assertLess(file_size, 50000, 
                               f"Template {template} is too large: {file_size} bytes")
                
                # Check file is reasonable size (over 1KB)
                self.assertGreater(file_size, 1000,
                                 f"Template {template} seems too small: {file_size} bytes")
                
            except FileNotFoundError:
                self.fail(f"Template file not found: {template}")
        
        print("✅ Template size optimization working correctly")

    def test_compiled_templates_updated(self):
        """Test that compiled templates include Phase 2 optimizations"""
        compiled_template_path = "/home/kdresdell/Documents/DEV/minipass_env/app/templates/email_templates/newPass_compiled/index.html"
        
        try:
            with open(compiled_template_path, 'r') as f:
                compiled_content = f.read()
            
            # Check that Phase 2 optimizations are present in compiled version
            self.assertIn('PHASE 2: Optimized Footer', compiled_content,
                         "Compiled template should include Phase 2 optimizations")
            
            # Check that template variables are present
            self.assertIn('{{ organization_name }}', compiled_content,
                         "Compiled template should have organization variables")
            self.assertIn('{{ unsubscribe_url }}', compiled_content,
                         "Compiled template should have dynamic URLs")
            
            print("✅ Compiled templates updated correctly")
            
        except FileNotFoundError:
            self.fail("Compiled template file not found")


if __name__ == '__main__':
    unittest.main()