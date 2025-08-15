#!/usr/bin/env python3
"""
Test script for the corrected KPI API implementation.
Validates that the fixes work properly.
"""

import sys
import os
sys.path.append('/home/kdresdell/Documents/DEV/minipass_env/app')

from app import app
from kpi_api import get_activity_kpis_implementation
from models import Activity, db
from flask import Flask
from unittest.mock import Mock
import json

def test_corrected_kpi_api():
    """Test the corrected KPI API implementation"""
    with app.app_context():
        print("🧪 TESTING CORRECTED KPI API")
        print("=" * 50)
        
        # Mock the session for admin access
        import flask
        with app.test_request_context('/?period=7'):
            flask.session['admin'] = True
            
            # Test with a real activity
            activities = Activity.query.filter_by(status='active').all()
            if not activities:
                print("❌ No active activities found")
                return
                
            activity = activities[0]
            print(f"\n🎯 Testing with Activity: {activity.name} (ID: {activity.id})")
            
            # Test different periods
            for period in [7, 30, 90]:
                print(f"\n📊 Testing {period}-day period:")
                print("-" * 30)
                
                # Mock the request args
                with app.test_request_context(f'/?period={period}'):
                    flask.session['admin'] = True
                    
                    try:
                        response = get_activity_kpis_implementation(activity.id)
                        
                        if hasattr(response, 'get_json'):
                            data = response.get_json()
                        else:
                            # Handle if response is already a dict
                            data = response.json if hasattr(response, 'json') else response
                            
                        if isinstance(data, str):
                            data = json.loads(data)
                            
                        print(f"✅ API call successful")
                        print(f"   Period: {data.get('period_days', 'unknown')}")
                        
                        kpi_data = data.get('kpi_data', {})
                        
                        # Validate revenue data
                        revenue = kpi_data.get('revenue', {})
                        revenue_trend = revenue.get('trend_data', [])
                        print(f"   Revenue trend data points: {len(revenue_trend)} (expected: {period})")
                        print(f"   Revenue percentage: {revenue.get('percentage', 'N/A')}%")
                        print(f"   Revenue percentage type: {type(revenue.get('percentage', 'N/A'))}")
                        
                        # Validate active users data  
                        active_users = kpi_data.get('active_users', {})
                        users_trend = active_users.get('trend_data', [])
                        print(f"   Active users trend data points: {len(users_trend)} (expected: {period})")
                        print(f"   Active users percentage: {active_users.get('percentage', 'N/A')}%")
                        
                        # Validate unpaid passports data
                        unpaid = kpi_data.get('unpaid_passports', {})
                        unpaid_trend = unpaid.get('trend_data', [])
                        print(f"   Unpaid trend data points: {len(unpaid_trend)} (expected: {period})")
                        
                        # Check debug info
                        debug = data.get('debug', {})
                        print(f"   Debug validation: {debug.get('data_validation', 'N/A')}")
                        
                        # Validate exact data point counts
                        if len(revenue_trend) != period:
                            print(f"   ❌ Revenue trend has {len(revenue_trend)} points, expected {period}")
                        else:
                            print(f"   ✅ Revenue trend has correct number of data points")
                            
                        if len(users_trend) != period:
                            print(f"   ❌ Users trend has {len(users_trend)} points, expected {period}")
                        else:
                            print(f"   ✅ Users trend has correct number of data points")
                            
                        if len(unpaid_trend) != period:
                            print(f"   ❌ Unpaid trend has {len(unpaid_trend)} points, expected {period}")
                        else:
                            print(f"   ✅ Unpaid trend has correct number of data points")
                            
                        # Check for clean numeric data
                        percentage = revenue.get('percentage', 0)
                        if isinstance(percentage, (int, float)) and not isinstance(percentage, bool):
                            print(f"   ✅ Percentage is clean numeric: {percentage}")
                        else:
                            print(f"   ❌ Percentage has encoding issues: {percentage} (type: {type(percentage)})")
                            
                    except Exception as e:
                        print(f"   ❌ Error: {str(e)}")
                        import traceback
                        traceback.print_exc()
        
        print(f"\n" + "=" * 50)
        print("🏁 TEST COMPLETE")

if __name__ == "__main__":
    test_corrected_kpi_api()