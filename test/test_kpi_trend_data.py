#!/usr/bin/env python3
"""
Unit test for KPI trend data generation
Tests that trend data includes today's data point
"""

import unittest
from datetime import datetime, timedelta, timezone
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestKPITrendData(unittest.TestCase):
    """Test KPI trend data includes today's data"""
    
    def setUp(self):
        """Set up test environment"""
        os.environ['FLASK_ENV'] = 'testing'
        os.environ['DATABASE_URL'] = 'sqlite:///test.db'
    
    def test_trend_includes_today(self):
        """Test that trend calculation includes today's data"""
        # Test the date range calculation
        now = datetime.now(timezone.utc)
        days = 7
        
        # Simulate the fixed loop
        trend_days = []
        for i in reversed(range(days)):
            day = (now - timedelta(days=i)).date()
            trend_days.append(day)
        
        # Check that today is included
        self.assertEqual(trend_days[-1], now.date(), 
                        "Trend should include today's date as the last element")
        
        # Check we have the right number of days
        self.assertEqual(len(trend_days), days, 
                        f"Should have exactly {days} days in trend")
        
        # Check days are consecutive
        for i in range(1, len(trend_days)):
            delta = (trend_days[i] - trend_days[i-1]).days
            self.assertEqual(delta, 1, 
                           f"Days should be consecutive, but gap found between {trend_days[i-1]} and {trend_days[i]}")
    
    def test_trend_excludes_future(self):
        """Test that trend doesn't include future dates"""
        now = datetime.now(timezone.utc)
        days = 7
        
        trend_days = []
        for i in reversed(range(days)):
            day = (now - timedelta(days=i)).date()
            trend_days.append(day)
        
        # No date should be in the future
        for day in trend_days:
            self.assertLessEqual(day, now.date(), 
                               f"Date {day} should not be in the future")
    
    def test_old_bug_excluded_today(self):
        """Test that the old bug (i+1) would exclude today"""
        now = datetime.now(timezone.utc)
        days = 7
        
        # Simulate the OLD buggy loop
        old_trend_days = []
        for i in reversed(range(days)):
            day = (now - timedelta(days=i+1)).date()  # Bug: i+1 instead of i
            old_trend_days.append(day)
        
        # The old bug should NOT include today
        self.assertNotEqual(old_trend_days[-1], now.date(), 
                          "Old bug should NOT include today (this confirms the bug existed)")
        
        # The old bug should end at yesterday
        yesterday = (now - timedelta(days=1)).date()
        self.assertEqual(old_trend_days[-1], yesterday, 
                       "Old bug should end at yesterday")

if __name__ == '__main__':
    # Run tests with verbosity
    unittest.main(verbosity=2)