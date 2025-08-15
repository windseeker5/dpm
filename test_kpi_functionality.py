#!/usr/bin/env python3
"""
Test script to analyze KPI percentage calculation issues in the Minipass Flask application.

This script will help identify:
1. Why percentage shows 200% consistently on main dashboard
2. How percentage changes are calculated in get_kpi_stats() function
3. Differences between activity-specific vs global KPI calculations
4. Any encoding issues causing strange characters
"""

import sys
import os
sys.path.append('/home/kdresdell/Documents/DEV/minipass_env/app')

from app import app
from utils import get_kpi_stats
from models import Passport, Signup, Activity, db
from datetime import datetime, timezone, timedelta

def analyze_kpi_calculations():
    """Analyze KPI calculations and identify issues"""
    with app.app_context():
        print("🔍 ANALYZING KPI CALCULATIONS")
        print("=" * 50)
        
        # Test global KPI calculations
        print("\n1. GLOBAL KPI CALCULATIONS")
        print("-" * 30)
        global_kpis = get_kpi_stats()
        
        for period, data in global_kpis.items():
            print(f"\n📊 Period: {period}")
            print(f"   Revenue: ${data.get('revenue', 0):.2f}")
            print(f"   Revenue Previous: ${data.get('revenue_prev', 0):.2f}")
            print(f"   Revenue Change: {data.get('revenue_change', 0)}%")
            print(f"   Active Users: {data.get('active_users', 0)}")
            print(f"   Active Users Previous: {data.get('active_users_prev', 0)}")
            print(f"   Passport Change: {data.get('passport_change', 0)}%")
            print(f"   New Passports Change: {data.get('new_passports_change', 0)}%")
        
        # Test activity-specific KPI calculations
        print("\n2. ACTIVITY-SPECIFIC KPI CALCULATIONS")
        print("-" * 40)
        activities = Activity.query.filter_by(status='active').all()
        
        for activity in activities:
            print(f"\n🎯 Activity: {activity.name} (ID: {activity.id})")
            activity_kpis = get_kpi_stats(activity_id=activity.id)
            
            for period, data in activity_kpis.items():
                print(f"\n   📊 Period: {period}")
                print(f"      Revenue: ${data.get('revenue', 0):.2f}")
                print(f"      Revenue Previous: ${data.get('revenue_prev', 0):.2f}")
                print(f"      Revenue Change: {data.get('revenue_change', 0)}%")
        
        # Analyze raw data to understand percentage calculations
        print("\n3. RAW DATA ANALYSIS")
        print("-" * 25)
        
        now = datetime.now(timezone.utc)
        
        # 7-day periods
        current_7d_start = now - timedelta(days=7)
        previous_7d_start = now - timedelta(days=14)
        previous_7d_end = now - timedelta(days=7)
        
        print(f"\n📅 Current 7d period: {current_7d_start.strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')}")
        print(f"📅 Previous 7d period: {previous_7d_start.strftime('%Y-%m-%d')} to {previous_7d_end.strftime('%Y-%m-%d')}")
        
        # Get paid passports for current period
        current_paid = Passport.query.filter(
            Passport.paid == True,
            db.or_(
                db.and_(Passport.paid_date.isnot(None), Passport.paid_date >= current_7d_start, Passport.paid_date <= now),
                db.and_(Passport.paid_date.is_(None), Passport.created_dt >= current_7d_start, Passport.created_dt <= now)
            )
        ).all()
        
        # Get paid passports for previous period
        previous_paid = Passport.query.filter(
            Passport.paid == True,
            db.or_(
                db.and_(Passport.paid_date.isnot(None), Passport.paid_date >= previous_7d_start, Passport.paid_date <= previous_7d_end),
                db.and_(Passport.paid_date.is_(None), Passport.created_dt >= previous_7d_start, Passport.created_dt <= previous_7d_end)
            )
        ).all()
        
        current_revenue = sum(p.sold_amt for p in current_paid if p.sold_amt)
        previous_revenue = sum(p.sold_amt for p in previous_paid if p.sold_amt)
        
        print(f"\n💰 Current 7d revenue: ${current_revenue:.2f} ({len(current_paid)} passports)")
        print(f"💰 Previous 7d revenue: ${previous_revenue:.2f} ({len(previous_paid)} passports)")
        
        if previous_revenue > 0:
            calculated_change = ((current_revenue - previous_revenue) / previous_revenue) * 100
            print(f"📈 Calculated percentage change: {calculated_change:.1f}%")
        else:
            print(f"📈 Previous revenue is 0, percentage change undefined")
        
        # Check for any unusual characters in the data
        print("\n4. CHARACTER ENCODING CHECK")
        print("-" * 30)
        
        for passport in current_paid[:5]:  # Check first 5 passports
            if passport.user:
                user_name = passport.user.name
                print(f"User name: '{user_name}' (length: {len(user_name)})")
                for i, char in enumerate(user_name):
                    if ord(char) > 127:  # Non-ASCII character
                        print(f"   Non-ASCII character at position {i}: '{char}' (ord: {ord(char)})")
        
        # Check activity names for unusual characters
        for activity in activities:
            activity_name = activity.name
            print(f"Activity name: '{activity_name}' (length: {len(activity_name)})")
            for i, char in enumerate(activity_name):
                if ord(char) > 127:  # Non-ASCII character
                    print(f"   Non-ASCII character at position {i}: '{char}' (ord: {ord(char)})")
        
        print("\n5. POTENTIAL ISSUES IDENTIFIED")
        print("-" * 35)
        
        issues = []
        
        # Check for consistent 200% across periods
        for period, data in global_kpis.items():
            if data.get('revenue_change') == 200.0:
                issues.append(f"🚨 Revenue change shows exactly 200% for {period} period")
        
        # Check for division by zero scenarios
        for period, data in global_kpis.items():
            if data.get('revenue_prev', 0) == 0 and data.get('revenue_change', 0) != 0:
                issues.append(f"🚨 Previous revenue is 0 but change is {data.get('revenue_change')}% for {period}")
        
        # Check for identical values across periods
        revenue_changes = [data.get('revenue_change', 0) for data in global_kpis.values()]
        if len(set(revenue_changes)) == 1 and revenue_changes[0] != 0:
            issues.append(f"🚨 All periods show identical revenue change: {revenue_changes[0]}%")
        
        if issues:
            for issue in issues:
                print(issue)
        else:
            print("✅ No obvious issues detected")
        
        print("\n" + "=" * 50)
        print("🏁 ANALYSIS COMPLETE")

if __name__ == "__main__":
    analyze_kpi_calculations()