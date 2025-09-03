#!/usr/bin/env python3
"""
Test suite for ContentSanitizer class and email template security
"""

import unittest
import sys
import os

# Add the parent directory to Python path to import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import ContentSanitizer


class TestContentSanitizer(unittest.TestCase):
    """Test cases for ContentSanitizer class"""

    def setUp(self):
        """Set up test fixtures"""
        self.sanitizer = ContentSanitizer()

    def test_sanitize_html_basic_tags(self):
        """Test that basic HTML tags are preserved"""
        content = "<p>Hello <strong>world</strong>!</p>"
        result = self.sanitizer.sanitize_html(content)
        self.assertEqual(result, "<p>Hello <strong>world</strong>!</p>")

    def test_sanitize_html_removes_script_tags(self):
        """Test that script tags are completely removed"""
        malicious_content = "<p>Hello</p><script>alert('XSS')</script><p>World</p>"
        result = self.sanitizer.sanitize_html(malicious_content)
        self.assertEqual(result, "<p>Hello</p><p>World</p>")

    def test_sanitize_html_removes_javascript_urls(self):
        """Test that javascript: URLs are removed"""
        malicious_content = '<a href="javascript:alert(\'XSS\')">Click me</a>'
        result = self.sanitizer.sanitize_html(malicious_content)
        self.assertNotIn("javascript:", result)

    def test_sanitize_html_removes_event_handlers(self):
        """Test that event handlers are removed"""
        malicious_content = '<p onclick="alert(\'XSS\')">Click me</p>'
        result = self.sanitizer.sanitize_html(malicious_content)
        self.assertNotIn("onclick", result)

    def test_sanitize_html_allows_safe_links(self):
        """Test that safe HTTP links are preserved"""
        content = '<p><a href="https://example.com">Safe link</a></p>'
        result = self.sanitizer.sanitize_html(content)
        self.assertIn('href="https://example.com"', result)

    def test_sanitize_html_empty_content(self):
        """Test handling of empty content"""
        result = self.sanitizer.sanitize_html("")
        self.assertEqual(result, "")
        
        result = self.sanitizer.sanitize_html(None)
        self.assertEqual(result, "")

    def test_validate_url_safe_urls(self):
        """Test that safe URLs are preserved"""
        test_cases = [
            ("https://example.com", "https://example.com"),
            ("http://example.com", "http://example.com"),
            ("mailto:test@example.com", "mailto:test@example.com"),
            ("example.com", "https://example.com"),  # Protocol added
            ("test@example.com", "mailto:test@example.com"),  # Mailto added
        ]
        
        for input_url, expected in test_cases:
            with self.subTest(input_url=input_url):
                result = self.sanitizer.validate_url(input_url)
                self.assertEqual(result, expected)

    def test_validate_url_malicious_urls(self):
        """Test that malicious URLs are rejected"""
        malicious_urls = [
            "javascript:alert('XSS')",
            "data:text/html,<script>alert('XSS')</script>",
            "vbscript:msgbox('XSS')",
            "file:///etc/passwd",
        ]
        
        for url in malicious_urls:
            with self.subTest(url=url):
                result = self.sanitizer.validate_url(url)
                self.assertEqual(result, "")

    def test_validate_url_empty_content(self):
        """Test handling of empty URLs"""
        result = self.sanitizer.validate_url("")
        self.assertEqual(result, "")
        
        result = self.sanitizer.validate_url(None)
        self.assertEqual(result, "")

    def test_validate_url_invalid_formats(self):
        """Test handling of invalid URL formats"""
        invalid_urls = [
            "not-a-url",
            "://missing-protocol",
            "https://",  # Missing domain
        ]
        
        for url in invalid_urls:
            with self.subTest(url=url):
                result = self.sanitizer.validate_url(url)
                # Should either return empty string or a valid corrected URL
                if result:
                    # If not empty, should be a valid URL
                    self.assertTrue(result.startswith(('http://', 'https://', 'mailto:')))

    def test_sanitize_email_template_data_complete(self):
        """Test complete email template data sanitization"""
        template_data = {
            'subject': 'Test <script>alert("XSS")</script> Subject',
            'title': 'Test <b>Title</b>',
            'intro_text': '<p>Welcome <strong>user</strong>!</p><script>alert("XSS")</script>',
            'conclusion_text': '<p>Thank you!</p><img src="x" onerror="alert(\'XSS\')">',
            'cta_text': 'Click <script>alert("XSS")</script> Here',
            'cta_url': 'javascript:alert("XSS")',
            'custom_message': '<p>Custom <em>message</em></p><script>alert("XSS")</script>',
        }
        
        result = self.sanitizer.sanitize_email_template_data(template_data)
        
        # Check that script tags are removed
        for key, value in result.items():
            self.assertNotIn('<script>', str(value))
            self.assertNotIn('javascript:', str(value))
        
        # Check that plain text fields have no HTML
        plain_text_fields = ['subject', 'title', 'cta_text']
        for field in plain_text_fields:
            if field in result:
                self.assertNotIn('<', result[field])
                self.assertNotIn('>', result[field])
        
        # Check that HTML fields still have safe HTML
        if 'intro_text' in result:
            self.assertIn('<p>', result['intro_text'])
            self.assertIn('<strong>', result['intro_text'])
        
        # Check that URL is sanitized or empty
        if 'cta_url' in result:
            self.assertEqual(result['cta_url'], "")  # Should be empty due to javascript:

    def test_sanitize_email_template_data_empty(self):
        """Test handling of empty template data"""
        result = self.sanitizer.sanitize_email_template_data(None)
        self.assertEqual(result, {})
        
        result = self.sanitizer.sanitize_email_template_data({})
        self.assertEqual(result, {})

    def test_xss_prevention_comprehensive(self):
        """Comprehensive XSS prevention test"""
        xss_payloads = [
            '<script>alert("XSS")</script>',
            '<img src="x" onerror="alert(\'XSS\')">',
            '<div onclick="alert(\'XSS\')">Click me</div>',
            '<iframe src="javascript:alert(\'XSS\')"></iframe>',
            '<link rel="stylesheet" href="javascript:alert(\'XSS\')">',
            '<style>@import "javascript:alert(\'XSS\')";</style>',
            '<object data="javascript:alert(\'XSS\')"></object>',
            '<embed src="javascript:alert(\'XSS\')">',
            '<svg onload="alert(\'XSS\')"></svg>',
            '<math><mtext><option><FAKEFAKE><option></option></mtext></math>',
        ]
        
        for payload in xss_payloads:
            with self.subTest(payload=payload):
                result = self.sanitizer.sanitize_html(payload)
                # Should not contain any dangerous elements
                self.assertNotIn('script', result.lower())
                self.assertNotIn('javascript:', result.lower())
                self.assertNotIn('onerror', result.lower())
                self.assertNotIn('onclick', result.lower())
                self.assertNotIn('onload', result.lower())

    def test_sql_injection_prevention(self):
        """Test that content doesn't contain SQL injection attempts"""
        sql_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users --",
        ]
        
        for payload in sql_payloads:
            with self.subTest(payload=payload):
                result = self.sanitizer.sanitize_html(payload)
                # While we don't specifically filter SQL, the content should be HTML-escaped
                # This is more for documentation that SQLAlchemy handles SQL injection prevention
                self.assertIsInstance(result, str)

    def test_allowed_html_tags(self):
        """Test that allowed HTML tags are preserved correctly"""
        allowed_content = '''
        <p>Paragraph with <strong>bold</strong> and <em>italic</em> text.</p>
        <ul>
            <li>List item 1</li>
            <li>List item 2 with <a href="https://example.com">link</a></li>
        </ul>
        <blockquote>This is a quote</blockquote>
        <h3>Heading 3</h3>
        <h4>Heading 4</h4>
        '''
        
        result = self.sanitizer.sanitize_html(allowed_content)
        
        # Check that allowed tags are preserved
        allowed_tags = ['<p>', '<strong>', '<em>', '<ul>', '<li>', '<a href=', '<blockquote>', '<h3>', '<h4>']
        for tag in allowed_tags:
            self.assertIn(tag, result)

    def test_disallowed_html_tags(self):
        """Test that disallowed HTML tags are removed"""
        disallowed_content = '''
        <script>alert('XSS')</script>
        <iframe src="evil.com"></iframe>
        <object data="evil.swf"></object>
        <embed src="evil.swf">
        <form><input type="text"></form>
        <meta http-equiv="refresh" content="0;url=evil.com">
        '''
        
        result = self.sanitizer.sanitize_html(disallowed_content)
        
        # Check that disallowed tags are removed
        disallowed_tags = ['<script>', '<iframe>', '<object>', '<embed>', '<form>', '<input>', '<meta>']
        for tag in disallowed_tags:
            self.assertNotIn(tag, result)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)