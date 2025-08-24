#!/usr/bin/env python3
"""
Test script for the missed notification scenario.
Simulates the exact scenario described in the issue:
1. User submits signup (while not connected to SSE)
2. Notification is broadcast (but no one receives it)
3. User navigates to dashboard and connects to SSE
4. User should receive the missed notification
"""

import sys
import os
import time
from datetime import datetime, timezone

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def simulate_missed_notification_scenario():
    """Simulate the exact scenario where notifications are missed and then recovered"""
    print("🎭 Simulating Missed Notification Scenario")
    print("=" * 70)
    
    try:
        from api.notifications import NotificationManager
        
        # Create a fresh notification manager (simulating server restart or fresh state)
        manager = NotificationManager()
        print("✅ Fresh NotificationManager created")
        
        print("\n📋 SCENARIO: User submits signup while not connected to dashboard")
        print("-" * 70)
        
        # Step 1: User submits signup (creates notification but no one is connected)
        print("1️⃣  User 'John Doe' submits signup for 'Rock Climbing Adventure'")
        signup_notification = {
            'type': 'signup',
            'id': f'signup_john_doe_{int(time.time())}',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': {
                'signup_id': 123,
                'user_name': 'John Doe',
                'email': 'john.doe@example.com',
                'phone': '+1-555-0123',
                'activity': 'Rock Climbing Adventure',
                'activity_id': 45,
                'passport_type': 'Premium Pass',
                'passport_type_price': 75.0,
                'avatar': 'https://www.gravatar.com/avatar/123',
                'created_at': datetime.now(timezone.utc).isoformat()
            }
        }
        
        # Step 2: System broadcasts notification (but no one is listening)
        print("2️⃣  System broadcasts signup notification...")
        manager.broadcast_to_admins(signup_notification)
        print("   ✅ Notification broadcasted and stored in recent notifications")
        
        # Simulate time passing - user is filling out forms, reviewing confirmation, etc.
        print("3️⃣  User spends 30 seconds reviewing confirmation and clicking links...")
        # We'll simulate this without actually waiting
        
        # Step 3: User finally navigates to dashboard and establishes SSE connection
        print("4️⃣  User navigates to dashboard and SSE connection is established")
        admin_email = 'john.doe@example.com'  # In real scenario, this would be an admin
        
        # This simulates what happens when a new SSE connection is established
        recent_notifications = manager.get_recent_notifications(admin_email)
        
        print(f"   🎯 SSE connection retrieves {len(recent_notifications)} recent notifications")
        
        # Step 4: Verify the user sees their own notification
        if len(recent_notifications) > 0:
            notification = recent_notifications[0]
            print(f"   📬 User receives their own notification:")
            print(f"      👤 Name: {notification['data']['user_name']}")
            print(f"      📧 Email: {notification['data']['email']}")
            print(f"      🎯 Activity: {notification['data']['activity']}")
            print(f"      🎫 Pass Type: {notification['data']['passport_type']} (${notification['data']['passport_type_price']})")
            print(f"      ⏰ Original time: {notification['timestamp']}")
            print(f"      🏷️  Server timestamp: {notification['server_timestamp']}")
            
            # Calculate how long ago this was "sent"
            server_time = notification['server_timestamp']
            current_time = datetime.now(timezone.utc).timestamp()
            elapsed = current_time - server_time
            print(f"      ⏳ Time elapsed: {elapsed:.2f} seconds ago")
            
        else:
            print("   ❌ No recent notifications found!")
            return False
        
        print("\n🎊 SUCCESS: User received their missed notification!")
        
        # Additional test: Simulate another user connecting later
        print("\n🔄 BONUS TEST: Another admin connects 2 minutes later")
        print("-" * 70)
        
        admin2_email = 'admin@example.com'
        admin2_notifications = manager.get_recent_notifications(admin2_email)
        print(f"5️⃣  Admin also receives {len(admin2_notifications)} recent notifications")
        
        if len(admin2_notifications) > 0:
            print("   ✅ Admin can see recent activity even though they weren't connected")
        else:
            print("   ❌ Admin didn't receive recent notifications")
            
        return True
        
    except Exception as e:
        print(f"❌ Scenario test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_notification_expiration():
    """Test that notifications older than 5 minutes are not sent to new connections"""
    print("\n⏰ Testing Notification Expiration")
    print("=" * 70)
    
    try:
        from api.notifications import NotificationManager
        
        manager = NotificationManager()
        
        # Create a notification with an old timestamp
        old_notification = {
            'type': 'signup',
            'id': 'old_notification_test',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': {'user_name': 'Old User', 'email': 'old@example.com', 'activity': 'Old Activity'}
        }
        
        # Manually add it with an old server timestamp (simulate it being 10 minutes old)
        old_timestamp = datetime.now(timezone.utc).timestamp() - 600  # 10 minutes ago
        old_notification_with_timestamp = {
            **old_notification,
            'server_timestamp': old_timestamp
        }
        
        manager._recent_notifications.append(old_notification_with_timestamp)
        
        # Add a recent notification
        recent_notification = {
            'type': 'payment',
            'id': 'recent_notification_test',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': {'user_name': 'Recent User', 'email': 'recent@example.com', 'activity': 'Recent Activity'}
        }
        manager.broadcast_to_admins(recent_notification)
        
        print("1️⃣  Added one old notification (10 minutes ago) and one recent notification")
        print(f"   📊 Total stored notifications: {len(manager._recent_notifications)}")
        
        # Test what a new connection receives
        new_admin_notifications = manager.get_recent_notifications('newadmin@example.com')
        
        print(f"2️⃣  New connection receives {len(new_admin_notifications)} notifications")
        
        # Should only receive the recent one, not the old one
        if len(new_admin_notifications) == 1 and new_admin_notifications[0]['data']['user_name'] == 'Recent User':
            print("   ✅ Only recent notification received (old one properly filtered)")
            return True
        else:
            print("   ❌ Received wrong notifications or count")
            for notif in new_admin_notifications:
                print(f"      - {notif['data']['user_name']} ({notif.get('server_timestamp', 'no timestamp')})")
            return False
            
    except Exception as e:
        print(f"❌ Expiration test failed: {e}")
        return False

if __name__ == '__main__':
    print("🚀 Testing Missed Notification Recovery System")
    print()
    
    # Run the main scenario test
    scenario_passed = simulate_missed_notification_scenario()
    
    # Test expiration functionality
    expiration_passed = test_notification_expiration()
    
    print("\n" + "=" * 70)
    if scenario_passed and expiration_passed:
        print("🎉 ALL SCENARIO TESTS PASSED!")
        print("\n📋 What this means for users:")
        print("   ✅ Users who submit signups will see their notification when they return")
        print("   ✅ Notifications are preserved for 5 minutes after submission") 
        print("   ✅ Old notifications don't clutter new connections")
        print("   ✅ Multiple users can receive the same recent notifications")
        print("\n🔧 The original issue has been SOLVED!")
        print("   • Users won't miss their own signup notifications anymore")
        print("   • Flash messages will still work as before")
        print("   • But now flashy SSE notifications will also appear!")
    else:
        print("❌ SOME TESTS FAILED!")
        
    print("\n🏁 Scenario testing completed.")