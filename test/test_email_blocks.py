#!/usr/bin/env python3
"""
Test email blocks rendering functionality

This test suite verifies that email blocks (owner_html, history_html) 
render correctly and are properly injected into compiled templates.
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch

# Add the app directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models import Activity, User, Passport, PassportType
from flask import render_template


class TestEmailBlocks(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        
        # Create test data
        self.test_pass_data = Mock()
        self.test_pass_data.id = 1
        self.test_pass_data.uses_remaining = 3
        self.test_pass_data.games_remaining = 3
        self.test_pass_data.sold_amt = 25.00
        self.test_pass_data.user_name = "Test User"
        self.test_pass_data.user_email = "test@example.com"
        self.test_pass_data.phone_number = "555-0123"
        
        # Mock activity
        self.test_pass_data.activity = Mock()
        self.test_pass_data.activity.name = "Test Activity"
        
        # Mock user 
        self.test_pass_data.user = Mock()
        self.test_pass_data.user.name = "Test User"
        self.test_pass_data.user.email = "test@example.com"
        self.test_pass_data.user.phone_number = "555-0123"
        
        # Create test history data
        self.test_history = {
            'created': '2025-01-15 10:30:00',
            'created_by': 'admin@minipass.me',
            'paid': '2025-01-15 10:32:00',
            'paid_by': 'test@example.com',
            'redemptions': [
                {'date': '2025-01-16 14:00:00', 'by': 'coach@example.com'},
                {'date': '2025-01-17 15:30:00', 'by': 'coach@example.com'}
            ],
            'expired': None
        }

    def test_owner_card_block_renders(self):
        """Test that owner_card_inline.html block renders correctly"""
        with self.app.app_context():
            try:
                owner_html = render_template(
                    "email_blocks/owner_card_inline.html", 
                    pass_data=self.test_pass_data
                )
                
                # Verify basic content is present
                self.assertIsNotNone(owner_html)
                self.assertGreater(len(owner_html), 0)
                
                # Check for key elements
                self.assertIn("Test Activity", owner_html)
                self.assertIn("Test User", owner_html)
                self.assertIn("test@example.com", owner_html)
                self.assertIn("555-0123", owner_html)
                self.assertIn("25.00", owner_html)
                self.assertIn("Activités restantes: 3", owner_html)
                
                print("✅ Owner block renders correctly")
                print(f"   Length: {len(owner_html)} characters")
                return True
                
            except Exception as e:
                self.fail(f"Owner block failed to render: {e}")

    def test_history_table_block_renders(self):
        """Test that history_table_inline.html block renders correctly"""
        with self.app.app_context():
            try:
                history_html = render_template(
                    "email_blocks/history_table_inline.html", 
                    history=self.test_history
                )
                
                # Verify basic content is present
                self.assertIsNotNone(history_html)
                self.assertGreater(len(history_html), 0)
                
                # Check for key elements
                self.assertIn("Création", history_html)
                self.assertIn("Paiement", history_html)
                self.assertIn("2025-01-15 10:30:00", history_html)
                self.assertIn("admin", history_html)  # trim_email filter removes @domain
                self.assertIn("Activité #1", history_html)
                self.assertIn("coach", history_html)  # trim_email filter removes @domain
                
                print("✅ History block renders correctly")
                print(f"   Length: {len(history_html)} characters")
                return True
                
            except Exception as e:
                self.fail(f"History block failed to render: {e}")

    def test_compiled_templates_have_block_placeholders(self):
        """Test that all compiled templates contain block placeholders"""
        compiled_templates = [
            "email_templates/newPass_compiled/index.html",
            "email_templates/paymentReceived_compiled/index.html", 
            "email_templates/latePayment_compiled/index.html",
            "email_templates/redeemPass_compiled/index.html"
        ]
        
        with self.app.app_context():
            for template_path in compiled_templates:
                try:
                    # Read template content directly
                    full_path = os.path.join(self.app.template_folder, template_path)
                    with open(full_path, 'r') as f:
                        template_content = f.read()
                    
                    # Check for block placeholders
                    self.assertIn("{{ owner_html | safe }}", template_content, 
                                f"Missing owner_html placeholder in {template_path}")
                    self.assertIn("{{ history_html | safe }}", template_content,
                                f"Missing history_html placeholder in {template_path}")
                    
                    print(f"✅ {template_path} has block placeholders")
                    
                except Exception as e:
                    self.fail(f"Failed to check {template_path}: {e}")

    def test_compiled_template_rendering(self):
        """Test that compiled templates render with blocks injected"""
        with self.app.app_context():
            # Render blocks first
            owner_html = render_template(
                "email_blocks/owner_card_inline.html", 
                pass_data=self.test_pass_data
            )
            history_html = render_template(
                "email_blocks/history_table_inline.html", 
                history=self.test_history
            )
            
            # Test context with blocks
            context = {
                'title': 'Test Email',
                'intro_text': 'This is a test email',
                'conclusion_text': 'Thank you for testing',
                'owner_html': owner_html,
                'history_html': history_html
            }
            
            # Test newPass template
            try:
                rendered_html = render_template(
                    "email_templates/newPass_compiled/index.html",
                    **context
                )
                
                # Verify blocks are injected
                self.assertIn("Test Activity", rendered_html)
                self.assertIn("Test User", rendered_html)
                self.assertIn("Création", rendered_html)
                self.assertIn("Paiement", rendered_html)
                
                print("✅ Compiled template renders with blocks")
                print(f"   Total length: {len(rendered_html)} characters")
                
            except Exception as e:
                self.fail(f"Failed to render compiled template: {e}")

    def test_survey_template_structure(self):
        """Test that survey template has correct variable placeholders"""
        with self.app.app_context():
            template_path = "email_templates/email_survey_invitation_compiled/index.html"
            
            try:
                full_path = os.path.join(self.app.template_folder, template_path)
                with open(full_path, 'r') as f:
                    template_content = f.read()
                
                # Survey-specific variables
                survey_vars = [
                    "{{ title }}",
                    "{{ user_name }}",
                    "{{ intro }}",
                    "{{ activity_name }}",
                    "{{ survey_name }}",
                    "{{ question_count }}",
                    "{{ survey_url }}",
                    "{{ conclusion }}",
                    "{{ organization_name }}",
                    "{{ support_email }}"
                ]
                
                for var in survey_vars:
                    self.assertIn(var, template_content,
                                f"Missing variable {var} in survey template")
                
                print("✅ Survey template has all required variables")
                
            except Exception as e:
                self.fail(f"Failed to check survey template: {e}")

    def test_signup_template_structure(self):
        """Test that signup template has correct variable placeholders"""
        with self.app.app_context():
            template_path = "email_templates/signup_compiled/index.html"
            
            try:
                full_path = os.path.join(self.app.template_folder, template_path)
                with open(full_path, 'r') as f:
                    template_content = f.read()
                
                # Signup template variables - check for patterns, not exact matches
                required_patterns = [
                    "title",
                    "conclusion_text",
                    "intro_text"
                ]
                
                for pattern in required_patterns:
                    self.assertIn(pattern, template_content,
                                f"Missing pattern {pattern} in signup template")
                
                # Signup template should NOT have blocks
                self.assertNotIn("{{ owner_html | safe }}", template_content)
                self.assertNotIn("{{ history_html | safe }}", template_content)
                
                print("✅ Signup template structure is correct")
                
            except Exception as e:
                self.fail(f"Failed to check signup template: {e}")

    def test_block_rendering_performance(self):
        """Test that block rendering is reasonably fast"""
        import time
        
        with self.app.app_context():
            start_time = time.time()
            
            # Render blocks multiple times
            for _ in range(10):
                owner_html = render_template(
                    "email_blocks/owner_card_inline.html", 
                    pass_data=self.test_pass_data
                )
                history_html = render_template(
                    "email_blocks/history_table_inline.html", 
                    history=self.test_history
                )
            
            end_time = time.time()
            avg_time = (end_time - start_time) / 10
            
            # Should render quickly (< 0.1 seconds average)
            self.assertLess(avg_time, 0.1, 
                           f"Block rendering too slow: {avg_time:.3f}s average")
            
            print(f"✅ Block rendering performance: {avg_time:.3f}s average")

    def run_template_readiness_report(self):
        """Generate a comprehensive template readiness report"""
        print("\n" + "="*60)
        print("EMAIL TEMPLATE READINESS REPORT")
        print("="*60)
        
        with self.app.app_context():
            # Check all compiled templates
            compiled_templates = [
                "signup_compiled",
                "newPass_compiled", 
                "paymentReceived_compiled",
                "latePayment_compiled",
                "redeemPass_compiled",
                "email_survey_invitation_compiled"
            ]
            
            for template_name in compiled_templates:
                template_path = f"email_templates/{template_name}/index.html"
                full_path = os.path.join(self.app.template_folder, template_path)
                
                print(f"\n📧 {template_name.upper().replace('_', ' ')}")
                print(f"   Path: {template_path}")
                
                if os.path.exists(full_path):
                    with open(full_path, 'r') as f:
                        content = f.read()
                    
                    print(f"   ✅ Exists ({len(content)} chars)")
                    
                    # Check for blocks
                    has_owner = "{{ owner_html | safe }}" in content
                    has_history = "{{ history_html | safe }}" in content
                    
                    if has_owner:
                        owner_line = None
                        for i, line in enumerate(content.split('\n'), 1):
                            if "{{ owner_html | safe }}" in line:
                                owner_line = i
                                break
                        print(f"   ✅ owner_html block (line {owner_line})")
                    
                    if has_history:
                        history_line = None
                        for i, line in enumerate(content.split('\n'), 1):
                            if "{{ history_html | safe }}" in line:
                                history_line = i
                                break
                        print(f"   ✅ history_html block (line {history_line})")
                    
                    if not has_owner and not has_history:
                        print("   ❌ No email blocks (as expected for some templates)")
                    
                    # Find all Jinja variables
                    import re
                    variables = re.findall(r'{{\s*([^}]+)\s*}}', content)
                    unique_vars = list(set([var.split('|')[0].split('.')[0].strip() 
                                          for var in variables if not var.startswith('set ')]))
                    
                    print(f"   📝 Variables found: {', '.join(sorted(unique_vars))}")
                    
                else:
                    print("   ❌ MISSING")
            
            # Check email blocks exist
            print(f"\n📁 EMAIL BLOCKS")
            block_files = [
                "email_blocks/owner_card_inline.html",
                "email_blocks/history_table_inline.html"
            ]
            
            for block_file in block_files:
                full_path = os.path.join(self.app.template_folder, block_file)
                if os.path.exists(full_path):
                    with open(full_path, 'r') as f:
                        content = f.read()
                    print(f"   ✅ {block_file} ({len(content)} chars)")
                else:
                    print(f"   ❌ {block_file} MISSING")


if __name__ == '__main__':
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add all test methods
    test_methods = [
        'test_owner_card_block_renders',
        'test_history_table_block_renders', 
        'test_compiled_templates_have_block_placeholders',
        'test_compiled_template_rendering',
        'test_survey_template_structure',
        'test_signup_template_structure',
        'test_block_rendering_performance'
    ]
    
    for method in test_methods:
        suite.addTest(TestEmailBlocks(method))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Generate readiness report
    test_instance = TestEmailBlocks()
    test_instance.setUp()
    test_instance.run_template_readiness_report()
    
    # Exit with proper code
    sys.exit(0 if result.wasSuccessful() else 1)