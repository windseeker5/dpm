"""
Integration test for email system with compiled templates and blocks

This test verifies that the complete email system works with:
1. Compiled templates using safe_template()
2. Email blocks rendering and preservation
3. Template customizations merged properly
"""

import unittest
import sys
import os
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from utils import get_email_context, safe_template, send_email
from models import Activity
from flask import render_template


class TestEmailIntegration(unittest.TestCase):
    """Integration tests for email system"""
    
    def setUp(self):
        """Set up test app context"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create mock activity
        self.mock_activity = type('MockActivity', (), {})()
        self.mock_activity.name = "Test Activity"
        self.mock_activity.id = 3
        self.mock_activity.email_templates = {
            'newPass': {
                'title': 'Your Test Pass is Ready!',
                'intro_text': 'Welcome to the test activity.',
                'conclusion_text': 'Thank you for testing with us.'
            }
        }
    
    def tearDown(self):
        """Clean up app context"""
        self.app_context.pop()
    
    def test_safe_template_returns_compiled_version(self):
        """Test that safe_template returns compiled template paths"""
        print("\n🔍 Testing safe_template function...")
        
        # Test various template types
        templates = ['newPass', 'paymentReceived', 'redeemPass', 'latePayment']
        
        for template_type in templates:
            compiled_path = safe_template(template_type)
            print(f"   {template_type} -> {compiled_path}")
            
            # Should return compiled version
            self.assertIn('_compiled', compiled_path)
            self.assertIn('index.html', compiled_path)
            
            # Verify the file exists
            full_path = os.path.join('templates', compiled_path)
            self.assertTrue(os.path.exists(full_path), f"Template should exist: {full_path}")
        
        print("✅ All templates have compiled versions!")
    
    def test_email_blocks_render_correctly(self):
        """Test that email blocks render without errors"""
        print("\n🔍 Testing email block rendering...")
        
        # Mock pass data for owner block
        pass_data_mock = {
            'activity': {'name': 'Test Activity', 'id': 3},
            'user': {'name': 'Test User', 'email': 'test@example.com', 'phone_number': '555-0123'},
            'pass_type': {'name': 'Test Pass', 'price': 25.00},
            'created_dt': datetime.now(),
            'sold_amt': 25.00,
            'paid': True,
            'pass_code': 'TEST123',
            'remaining_activities': 5
        }
        
        class MockObject:
            def __init__(self, data):
                for key, value in data.items():
                    if isinstance(value, dict):
                        setattr(self, key, MockObject(value))
                    else:
                        setattr(self, key, value)
        
        pass_data = MockObject(pass_data_mock)
        
        # Test owner block rendering
        owner_html = render_template("email_blocks/owner_card_inline.html", pass_data=pass_data)
        self.assertIsNotNone(owner_html)
        self.assertGreater(len(owner_html), 0)
        self.assertIn("Test Activity", owner_html)
        self.assertIn("Test User", owner_html)
        print(f"   Owner block rendered: {len(owner_html)} chars")
        
        # Test history block rendering
        history = [
            {'date': '2025-01-09', 'action': 'Création'},
            {'date': '2025-01-10', 'action': 'Paiement'}
        ]
        history_html = render_template("email_blocks/history_table_inline.html", history=history)
        self.assertIsNotNone(history_html)
        self.assertGreater(len(history_html), 0)
        self.assertIn("Création", history_html)  # French for "Creation"
        print(f"   History block rendered: {len(history_html)} chars")
        
        print("✅ Email blocks render correctly!")
    
    def test_compiled_template_renders_with_blocks(self):
        """Test that compiled templates render correctly with email blocks"""
        print("\n🔍 Testing compiled template rendering with blocks...")
        
        # Create complete context with blocks
        pass_data_mock = {
            'activity': {'name': 'Test Activity', 'id': 3},
            'user': {'name': 'Test User', 'email': 'test@example.com', 'phone_number': '555-0123'},
            'pass_type': {'name': 'Test Pass', 'price': 25.00},
            'created_dt': datetime.now(),
            'sold_amt': 25.00,
            'paid': True,
            'pass_code': 'TEST123',
            'remaining_activities': 5
        }
        
        class MockObject:
            def __init__(self, data):
                for key, value in data.items():
                    if isinstance(value, dict):
                        setattr(self, key, MockObject(value))
                    else:
                        setattr(self, key, value)
        
        pass_data = MockObject(pass_data_mock)
        
        # Create base context with blocks
        base_context = {
            'user_name': 'Test User',
            'user_email': 'test@example.com',
            'activity_name': 'Test Activity',
            'pass_code': 'TEST123',
            'owner_html': render_template("email_blocks/owner_card_inline.html", pass_data=pass_data),
            'history_html': render_template("email_blocks/history_table_inline.html", 
                                          history=[{'date': '2025-01-09', 'action': 'Création'}])
        }
        
        # Get merged context (should preserve blocks)
        context = get_email_context(self.mock_activity, 'newPass', base_context)
        
        # Get compiled template
        template_path = safe_template('newPass')
        
        # Try to render the template
        try:
            rendered_html = render_template(template_path, **context)
            self.assertIsNotNone(rendered_html)
            self.assertGreater(len(rendered_html), 100)  # Should be substantial HTML
            
            # Check that blocks are included
            self.assertIn("Test Activity", rendered_html)
            self.assertIn("Test User", rendered_html)
            self.assertIn("Création", rendered_html)  # French for "Creation"
            
            # Check customizations are applied
            self.assertIn("Your Test Pass is Ready!", rendered_html)  # Custom title
            self.assertIn("Welcome to the test activity", rendered_html)  # Custom intro
            
            print(f"   Template rendered: {len(rendered_html)} chars")
            print("   ✅ Contains email blocks")
            print("   ✅ Contains customizations")
            
        except Exception as e:
            self.fail(f"Template rendering failed: {str(e)}")
        
        print("✅ Compiled template renders with blocks!")
    
    def test_full_context_building_flow(self):
        """Test the complete context building flow as used in the app"""
        print("\n🔍 Testing complete context building flow...")
        
        template_type = 'newPass'
        
        # Step 1: Create base context like test_email_template does
        base_context = {
            'user_name': 'Kevin Dresdell',
            'user_email': 'kdresdell@gmail.com',
            'activity_name': self.mock_activity.name,
            'pass_code': 'TEST123',
            'amount': '$25.00',
            'test_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Step 2: Add email blocks for templates that need them
        pass_data_mock = {
            'activity': {'name': self.mock_activity.name, 'id': self.mock_activity.id},
            'user': {'name': 'Kevin Dresdell', 'email': 'kdresdell@gmail.com', 'phone_number': '555-0123'},
            'pass_type': {'name': 'Test Pass', 'price': 25.00},
            'created_dt': datetime.now(),
            'sold_amt': 25.00,
            'paid': True,
            'pass_code': 'TEST123',
            'remaining_activities': 3
        }
        
        class MockObject:
            def __init__(self, data):
                for key, value in data.items():
                    if isinstance(value, dict):
                        setattr(self, key, MockObject(value))
                    else:
                        setattr(self, key, value)
        
        pass_data = MockObject(pass_data_mock)
        
        base_context['owner_html'] = render_template(
            "email_blocks/owner_card_inline.html", 
            pass_data=pass_data
        )
        
        print(f"   Added owner_html: {len(base_context['owner_html'])} chars")
        
        # Step 3: Get merged context (should preserve blocks and apply customizations)
        context = get_email_context(self.mock_activity, template_type, base_context)
        
        # Verify blocks are preserved
        self.assertIn('owner_html', context)
        self.assertEqual(context['owner_html'], base_context['owner_html'])
        
        # Verify customizations are applied
        self.assertEqual(context['title'], 'Your Test Pass is Ready!')
        self.assertEqual(context['intro_text'], 'Welcome to the test activity.')
        
        # Verify base context is preserved
        self.assertEqual(context['user_name'], 'Kevin Dresdell')
        self.assertEqual(context['pass_code'], 'TEST123')
        
        print("   ✅ Blocks preserved")
        print("   ✅ Customizations applied")
        print("   ✅ Base context preserved")
        
        # Step 4: Verify template can be rendered
        template_path = safe_template(template_type)
        rendered_html = render_template(template_path, **context)
        
        self.assertGreater(len(rendered_html), 1000)  # Should be substantial
        self.assertIn("Kevin Dresdell", rendered_html)
        self.assertIn("Your Test Pass is Ready!", rendered_html)
        
        print(f"   Template renders: {len(rendered_html)} chars")
        print("✅ Complete flow works correctly!")


def run_integration_tests():
    """Run the complete integration test suite"""
    print("🚀 RUNNING EMAIL INTEGRATION TESTS")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestEmailIntegration)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ ALL INTEGRATION TESTS PASSED!")
        print("   - Compiled templates work correctly")
        print("   - Email blocks render and are preserved")
        print("   - Customizations apply without breaking blocks")
        print("   - Complete email flow functions properly")
    else:
        print("❌ SOME INTEGRATION TESTS FAILED")
        for failure in result.failures:
            print(f"   FAILURE: {failure[0]}")
        for error in result.errors:
            print(f"   ERROR: {error[0]}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)