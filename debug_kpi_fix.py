#!/usr/bin/env python3
"""
Debug script to verify KPI data structure fixes
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
import json

app = create_app()

with app.app_context():
    try:
        from utils import get_kpi_data
        
        # Test the data structure
        result = get_kpi_data(period='7d')
        print("✅ KPI Data Structure Test:")
        print(json.dumps(result, indent=2))
        
        # Verify the keys exist
        expected_keys = ['revenue', 'active_users', 'passports_created', 'unpaid_passports']
        missing_keys = [key for key in expected_keys if key not in result]
        
        if missing_keys:
            print(f"❌ Missing keys: {missing_keys}")
        else:
            print("✅ All expected keys present")
        
        # Verify each KPI has trend_data
        for key, kpi in result.items():
            if 'trend_data' in kpi:
                print(f"✅ {key}: has trend_data with {len(kpi['trend_data'])} points")
            else:
                print(f"❌ {key}: missing trend_data")
                
        print("\n" + "="*50)
        print("Frontend Chart Debugging:")
        print("The JavaScript code expects:")
        print("- kpiData.revenue.trend_data")
        print("- kpiData.active_users.trend_data") 
        print("- kpiData.passports_created.trend_data")
        print("- kpiData.unpaid_passports.trend_data")
        print("\nBackend is now providing:")
        for key in result.keys():
            if 'trend_data' in result[key]:
                print(f"- kpiData.{key}.trend_data ✅")
            else:
                print(f"- kpiData.{key}.trend_data ❌")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()