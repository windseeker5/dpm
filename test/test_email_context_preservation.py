"""
Test email context preservation functionality

This test suite verifies that email blocks (owner_html, history_html) 
are properly preserved when merging customizations with get_email_context.
"""

import unittest
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from utils import get_email_context
from models import Activity
from flask import render_template


class TestEmailContextPreservation(unittest.TestCase):
    """Test that email blocks are preserved when applying customizations"""
    
    def setUp(self):
        """Set up test app context"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create mock activity with email templates
        self.mock_activity = type('MockActivity', (), {})()
        self.mock_activity.name = "Test Activity"
        self.mock_activity.id = 1
        self.mock_activity.email_templates = {
            'newPass': {
                'title': 'Custom Title',
                'intro_text': 'Custom intro text',
                'owner_html': 'SHOULD BE IGNORED',  # This should be ignored
                'history_html': 'SHOULD BE IGNORED',  # This should be ignored
                'custom_message': 'Custom message'
            }
        }
    
    def tearDown(self):
        """Clean up app context"""
        self.app_context.pop()
    
    def test_email_blocks_preserved_from_base_context(self):
        """Test that email blocks from base_context are never overridden"""
        print("\n🔍 Testing email blocks preservation...")
        
        # Set up base context with email blocks
        base_context = {
            'owner_html': '<div class="owner-card">PRESERVED OWNER BLOCK</div>',
            'history_html': '<table class="history">PRESERVED HISTORY BLOCK</table>',
            'title': 'Original Title',
            'intro_text': 'Original intro'
        }
        
        # Get merged context
        context = get_email_context(self.mock_activity, 'newPass', base_context)
        
        # Verify email blocks are preserved
        self.assertEqual(
            context['owner_html'], 
            '<div class="owner-card">PRESERVED OWNER BLOCK</div>',
            "owner_html should be preserved from base_context"
        )
        self.assertEqual(
            context['history_html'], 
            '<table class="history">PRESERVED HISTORY BLOCK</table>',
            "history_html should be preserved from base_context"
        )
        
        # Verify other customizations are applied
        self.assertEqual(context['title'], 'Custom Title')
        self.assertEqual(context['intro_text'], 'Custom intro text')
        self.assertEqual(context['custom_message'], 'Custom message')
        
        print("✅ Email blocks preserved correctly!")
        print(f"   owner_html: {context['owner_html'][:30]}...")
        print(f"   history_html: {context['history_html'][:30]}...")
        print(f"   Custom title: {context['title']}")
    
    def test_no_base_context_blocks_not_added(self):
        """Test that when no base_context is provided, no blocks are added"""
        print("\n🔍 Testing without base context...")
        
        # Get merged context without base_context
        context = get_email_context(self.mock_activity, 'newPass', None)
        
        # Verify no email blocks are present
        self.assertNotIn('owner_html', context, "owner_html should not be added without base_context")
        self.assertNotIn('history_html', context, "history_html should not be added without base_context")
        
        # Verify customizations are still applied
        self.assertEqual(context['title'], 'Custom Title')
        self.assertEqual(context['intro_text'], 'Custom intro text')
        
        print("✅ No blocks added when no base_context provided!")
        print(f"   Context keys: {list(context.keys())}")
    
    def test_partial_blocks_in_base_context(self):
        """Test that only blocks present in base_context are preserved"""
        print("\n🔍 Testing partial blocks preservation...")
        
        # Base context with only owner_html
        base_context = {
            'owner_html': '<div>OWNER ONLY</div>',
            'title': 'Original Title'
        }
        
        # Get merged context
        context = get_email_context(self.mock_activity, 'newPass', base_context)
        
        # Verify only owner_html is preserved
        self.assertEqual(context['owner_html'], '<div>OWNER ONLY</div>')
        self.assertNotIn('history_html', context, "history_html should not be present")
        
        # Verify customizations are applied
        self.assertEqual(context['title'], 'Custom Title')
        
        print("✅ Partial blocks preserved correctly!")
        print(f"   Has owner_html: {'owner_html' in context}")
        print(f"   Has history_html: {'history_html' in context}")
    
    def test_empty_customizations_preserve_blocks(self):
        """Test that blocks are preserved even when activity has no customizations"""
        print("\n🔍 Testing with no customizations...")
        
        # Activity with no email templates
        empty_activity = type('MockActivity', (), {})()
        empty_activity.name = "Empty Activity"
        empty_activity.email_templates = None
        
        # Base context with blocks
        base_context = {
            'owner_html': '<div>PRESERVED</div>',
            'history_html': '<table>PRESERVED</table>'
        }
        
        # Get merged context
        context = get_email_context(empty_activity, 'newPass', base_context)
        
        # Verify blocks are preserved
        self.assertEqual(context['owner_html'], '<div>PRESERVED</div>')
        self.assertEqual(context['history_html'], '<table>PRESERVED</table>')
        
        # Verify defaults are applied
        self.assertEqual(context['subject'], 'Minipass Notification')
        self.assertEqual(context['title'], 'Welcome to Minipass')
        
        print("✅ Blocks preserved with no customizations!")
        print(f"   owner_html: {context['owner_html']}")
        print(f"   Default title: {context['title']}")
    
    def test_blocks_never_overridden_by_customizations(self):
        """Test that customizations cannot override email blocks"""
        print("\n🔍 Testing blocks cannot be overridden...")
        
        # Activity with customizations trying to override blocks
        override_activity = type('MockActivity', (), {})()
        override_activity.name = "Override Test"
        override_activity.email_templates = {
            'newPass': {
                'owner_html': 'MALICIOUS OVERRIDE ATTEMPT',
                'history_html': 'ANOTHER OVERRIDE ATTEMPT',
                'title': 'Custom Title'
            }
        }
        
        # Base context with protected blocks
        base_context = {
            'owner_html': '<div>PROTECTED OWNER</div>',
            'history_html': '<table>PROTECTED HISTORY</table>'
        }
        
        # Get merged context
        context = get_email_context(override_activity, 'newPass', base_context)
        
        # Verify blocks are NOT overridden
        self.assertEqual(context['owner_html'], '<div>PROTECTED OWNER</div>')
        self.assertEqual(context['history_html'], '<table>PROTECTED HISTORY</table>')
        
        # Verify other customizations still work
        self.assertEqual(context['title'], 'Custom Title')
        
        print("✅ Blocks successfully protected from override!")
        print(f"   owner_html: {context['owner_html']}")
        print(f"   history_html: {context['history_html']}")
        print(f"   Custom title: {context['title']}")


def run_test_suite():
    """Run the complete test suite"""
    print("🚀 RUNNING EMAIL CONTEXT PRESERVATION TESTS")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestEmailContextPreservation)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED - Email blocks properly preserved!")
    else:
        print("❌ SOME TESTS FAILED - Check email block preservation logic")
        for failure in result.failures:
            print(f"   FAILURE: {failure[0]}")
        for error in result.errors:
            print(f"   ERROR: {error[0]}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_test_suite()
    sys.exit(0 if success else 1)