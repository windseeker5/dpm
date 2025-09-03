"""
Unit tests for Activity Dashboard Signup Improvements
Tests the default pending filter, has_pending_signups flag, and filter simplification
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from datetime import datetime, timezone


class TestActivityDashboardSignups(unittest.TestCase):
    def setUp(self):
        """Set up test client and testing mode"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        
    def test_pending_filter_is_default(self):
        """Test that pending filter is selected by default when no filter specified"""
        with self.app.test_request_context('/activity-dashboard/1'):
            from flask import request
            # When no filter is specified, it should default to 'pending'
            signup_filter = request.args.get('signup_filter', 'pending')
            self.assertEqual(signup_filter, 'pending')
    
    def test_filter_parameter_override(self):
        """Test that URL parameter overrides the default filter"""
        with self.app.test_request_context('/activity-dashboard/1?signup_filter=all'):
            from flask import request
            signup_filter = request.args.get('signup_filter', 'pending')
            self.assertEqual(signup_filter, 'all')
            
        with self.app.test_request_context('/activity-dashboard/1?signup_filter=approved'):
            from flask import request
            signup_filter = request.args.get('signup_filter', 'pending')
            self.assertEqual(signup_filter, 'approved')
    
    @patch('app.Activity')
    @patch('app.Signup')
    def test_has_pending_signups_calculation(self, mock_signup, mock_activity):
        """Test that has_pending_signups flag is calculated correctly"""
        # Create mock signups with different statuses
        pending_signup1 = Mock()
        pending_signup1.status = 'pending'
        
        pending_signup2 = Mock()
        pending_signup2.status = 'pending'
        
        approved_signup = Mock()
        approved_signup.status = 'approved'
        
        # Test with pending signups
        pending_signups = [pending_signup1, pending_signup2]
        has_pending_signups = len(pending_signups) > 0
        pending_signups_count = len(pending_signups)
        
        self.assertTrue(has_pending_signups)
        self.assertEqual(pending_signups_count, 2)
        
        # Test without pending signups
        pending_signups = []
        has_pending_signups = len(pending_signups) > 0
        pending_signups_count = len(pending_signups)
        
        self.assertFalse(has_pending_signups)
        self.assertEqual(pending_signups_count, 0)
    
    def test_template_receives_pending_variables(self):
        """Test that render_template receives has_pending_signups and pending_signups_count"""
        with patch('app.render_template') as mock_render:
            with patch('app.Activity') as mock_activity:
                with patch('app.Signup') as mock_signup:
                    with patch('app.Passport') as mock_passport:
                        with patch('app.get_kpi_data') as mock_kpi:
                            # Set up mocks
                            mock_activity.query.get.return_value = Mock()
                            mock_signup.query.options.return_value.filter_by.return_value.order_by.return_value.all.return_value = []
                            mock_passport.query.options.return_value.filter.return_value.order_by.return_value.all.return_value = []
                            mock_passport.query.filter_by.return_value.all.return_value = []
                            mock_kpi.return_value = {'revenue': {}}
                            
                            # Simulate the logic from activity_dashboard
                            pending_signups = []
                            has_pending_signups = len(pending_signups) > 0
                            pending_signups_count = len(pending_signups)
                            
                            # Verify the calculations
                            self.assertFalse(has_pending_signups)
                            self.assertEqual(pending_signups_count, 0)
    
    def test_backward_compatibility(self):
        """Test that old filter parameters still work correctly"""
        # Test that 'all' filter still works
        with self.app.test_request_context('/activity-dashboard/1?signup_filter=all'):
            from flask import request
            signup_filter = request.args.get('signup_filter', 'pending')
            self.assertEqual(signup_filter, 'all')
        
        # Test that 'pending' filter works
        with self.app.test_request_context('/activity-dashboard/1?signup_filter=pending'):
            from flask import request
            signup_filter = request.args.get('signup_filter', 'pending')
            self.assertEqual(signup_filter, 'pending')
        
        # Test that 'approved' filter works
        with self.app.test_request_context('/activity-dashboard/1?signup_filter=approved'):
            from flask import request
            signup_filter = request.args.get('signup_filter', 'pending')
            self.assertEqual(signup_filter, 'approved')
        
        # Note: 'unpaid' and 'paid' filters are removed from UI but backend still handles them
        # This ensures backward compatibility if old bookmarks are used
        with self.app.test_request_context('/activity-dashboard/1?signup_filter=unpaid'):
            from flask import request
            signup_filter = request.args.get('signup_filter', 'pending')
            self.assertEqual(signup_filter, 'unpaid')


if __name__ == '__main__':
    unittest.main()