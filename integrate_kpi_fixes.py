#!/usr/bin/env python3
"""
Integration script to apply the KPI API fixes to the main application.
This script shows how to integrate the corrected KPI API.
"""

import sys
import os
sys.path.append('/home/kdresdell/Documents/DEV/minipass_env/app')

def show_integration_instructions():
    """Show how to integrate the corrected KPI API"""
    
    print("🔧 KPI API INTEGRATION INSTRUCTIONS")
    print("=" * 50)
    
    print("\n1. CURRENT SITUATION:")
    print("   - There are two KPI API implementations")
    print("   - app.py has get_activity_kpis_api() function")
    print("   - kpi_api.py has the corrected implementation")
    
    print("\n2. INTEGRATION OPTIONS:")
    print("\n   Option A: Replace the function in app.py")
    print("   - Copy the corrected implementation from kpi_api.py")
    print("   - Replace get_activity_kpis_api() in app.py")
    print("   - Keep the existing route decorator")
    
    print("\n   Option B: Import the corrected module")
    print("   - Add to app.py: from kpi_api import register_kpi_routes")
    print("   - Add after app creation: register_kpi_routes(app)")
    print("   - Comment out the old get_activity_kpis_api() function")
    
    print("\n3. RECOMMENDED APPROACH (Option A):")
    print("\n   Step 1: Backup current implementation")
    print("   Step 2: Replace function body in app.py")
    print("   Step 3: Test with frontend")
    print("   Step 4: Remove backup if working correctly")
    
    print("\n4. TESTING:")
    print("   - Run: python test_corrected_kpi.py")
    print("   - Check frontend charts show correct data points")
    print("   - Verify no strange characters in percentages")
    print("   - Test period switching (7d, 30d, 90d)")
    
    print("\n5. FRONTEND UPDATES (if needed):")
    print("   - Charts should automatically get correct data points")
    print("   - Percentage displays should show clean numbers")
    print("   - Loading states should work properly")
    
    print("\n6. VALIDATION CHECKLIST:")
    print("   ✓ 7-day period shows exactly 7 chart points")
    print("   ✓ 30-day period shows exactly 30 chart points")
    print("   ✓ 90-day period shows exactly 90 chart points")
    print("   ✓ Percentages are clean float numbers")
    print("   ✓ No strange characters in displays")
    print("   ✓ No gray overlay issues")
    print("   ✓ API responses include debug info")
    
    print(f"\n" + "=" * 50)
    print("📁 FILES READY FOR INTEGRATION:")
    print(f"   - kpi_api.py (corrected implementation)")
    print(f"   - test_corrected_kpi.py (validation script)")
    print(f"   - KPI_API_FIXES_SUMMARY.md (documentation)")

if __name__ == "__main__":
    show_integration_instructions()