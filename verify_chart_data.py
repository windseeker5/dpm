#!/usr/bin/env python3
"""
Verify that the corrected KPI API generates the exact number of chart data points.
"""

import sys
import os
sys.path.append('/home/kdresdell/Documents/DEV/minipass_env/app')

from app import app
from kpi_api import get_activity_kpis_implementation
from models import Activity
import flask
import json

def verify_chart_data():
    """Verify chart data point generation"""
    with app.app_context():
        print("📊 CHART DATA VERIFICATION")
        print("=" * 40)
        
        # Get an activity to test with
        activity = Activity.query.filter_by(status='active').first()
        if not activity:
            print("❌ No active activities found")
            return
            
        print(f"🎯 Testing with: {activity.name}")
        
        for period in [7, 30, 90]:
            print(f"\n📅 {period}-day period:")
            print("-" * 25)
            
            with app.test_request_context(f'/?period={period}'):
                flask.session['admin'] = True
                
                try:
                    response = get_activity_kpis_implementation(activity.id)
                    data = response.get_json() if hasattr(response, 'get_json') else response
                    
                    kpi_data = data.get('kpi_data', {})
                    
                    # Check each KPI type
                    for kpi_type in ['revenue', 'active_users', 'unpaid_passports', 'profit']:
                        kpi_info = kpi_data.get(kpi_type, {})
                        trend_data = kpi_info.get('trend_data', [])
                        
                        print(f"   {kpi_type:15}: {len(trend_data):2} points {'' if len(trend_data) == period else '❌'}")
                        
                        # Show actual data points for verification
                        if len(trend_data) <= 10:  # Only show if reasonable number
                            print(f"                     Data: {trend_data}")
                        else:
                            print(f"                     Sample: {trend_data[:5]}...{trend_data[-2:]}")
                    
                    # Verify all trend data has same length as period
                    all_lengths = [
                        len(kpi_data.get('revenue', {}).get('trend_data', [])),
                        len(kpi_data.get('active_users', {}).get('trend_data', [])),
                        len(kpi_data.get('unpaid_passports', {}).get('trend_data', [])),
                        len(kpi_data.get('profit', {}).get('trend_data', []))
                    ]
                    
                    if all(length == period for length in all_lengths):
                        print(f"   ✅ All KPIs have exactly {period} data points")
                    else:
                        print(f"   ❌ Inconsistent data point counts: {all_lengths}")
                        
                except Exception as e:
                    print(f"   ❌ Error: {e}")
        
        print(f"\n" + "=" * 40)
        print("✅ VERIFICATION COMPLETE")

if __name__ == "__main__":
    verify_chart_data()