#!/usr/bin/env python3

"""
Check database to see what activities exist and if they have passports/signups
"""

import sqlite3
import os

def check_database():
    db_path = "instance/minipass.db"
    
    if not os.path.exists(db_path):
        print("❌ Database file not found at", db_path)
        return
        
    print("=== Database Analysis ===")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check activities
        print("1. Activities:")
        cursor.execute("SELECT id, name, status FROM activity ORDER BY id")
        activities = cursor.fetchall()
        
        if not activities:
            print("   No activities found")
        else:
            for act_id, name, status in activities:
                print(f"   ID {act_id}: {name} (status: {status})")
                
                # Check passports for this activity
                cursor.execute("SELECT COUNT(*) FROM passport WHERE activity_id = ?", (act_id,))
                passport_count = cursor.fetchone()[0]
                
                # Check signups for this activity  
                cursor.execute("SELECT COUNT(*) FROM signup WHERE activity_id = ?", (act_id,))
                signup_count = cursor.fetchone()[0]
                
                print(f"      Passports: {passport_count}, Signups: {signup_count}")
                
                if passport_count > 0 or signup_count > 0:
                    print(f"      ✅ Activity {act_id} has data - good for testing!")
        
        print("\n2. Overall Data Summary:")
        
        # Total counts
        cursor.execute("SELECT COUNT(*) FROM activity WHERE status != 'cancelled'")
        active_activities = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM passport")
        total_passports = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM signup") 
        total_signups = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM user")
        total_users = cursor.fetchone()[0]
        
        print(f"   Active Activities: {active_activities}")
        print(f"   Total Passports: {total_passports}")
        print(f"   Total Signups: {total_signups}")
        print(f"   Total Users: {total_users}")
        
        # If we have no test data, suggest creating some
        if total_passports == 0 and total_signups == 0:
            print("\n⚠️  No test data found!")
            print("To test the AJAX filtering:")
            print("1. Create an activity via the web interface")
            print("2. Create some passports or signups for that activity")
            print("3. Then test the filter buttons")
        else:
            print("\n✅ Test data exists - AJAX filtering should work!")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")

if __name__ == "__main__":
    check_database()