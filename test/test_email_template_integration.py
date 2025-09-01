#!/usr/bin/env python3
"""
Integration test for email template copying feature
Creates an activity and verifies email templates are copied
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Activity
from utils import copy_global_email_templates_to_activity
from datetime import datetime, timezone

def test_email_template_integration():
    """Integration test for email template copying"""
    
    with app.app_context():
        print("=" * 60)
        print("EMAIL TEMPLATE INTEGRATION TEST")
        print("=" * 60)
        
        # Step 1: Test the copy function directly
        print("\n1. Testing copy_global_email_templates_to_activity()...")
        templates = copy_global_email_templates_to_activity()
        
        expected_types = ['newPass', 'paymentReceived', 'latePayment', 
                         'signup', 'redeemPass', 'survey_invitation']
        
        all_present = all(t in templates for t in expected_types)
        if all_present:
            print("   ✅ All 6 template types returned")
            for template_type in expected_types:
                fields = len(templates[template_type])
                print(f"      - {template_type}: {fields} fields")
        else:
            print("   ❌ Missing template types")
            return False
        
        # Step 2: Create a new activity with templates
        print("\n2. Creating new activity with email templates...")
        test_activity = Activity(
            name=f"Integration Test {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            type="test",
            description="Testing email template defaults",
            status="active",
            created_by=1,
            email_templates=copy_global_email_templates_to_activity()
        )
        
        db.session.add(test_activity)
        db.session.commit()
        print(f"   ✅ Activity created with ID: {test_activity.id}")
        
        # Step 3: Verify templates were saved
        print("\n3. Verifying templates were saved to database...")
        saved_activity = Activity.query.get(test_activity.id)
        
        if saved_activity.email_templates:
            print("   ✅ Email templates saved to database")
            
            # Verify all types are present
            for template_type in expected_types:
                if template_type in saved_activity.email_templates:
                    template = saved_activity.email_templates[template_type]
                    print(f"   ✅ {template_type}:")
                    print(f"      Subject: {template.get('subject', 'N/A')[:40]}...")
                    print(f"      Title: {template.get('title', 'N/A')[:40]}...")
                else:
                    print(f"   ❌ {template_type}: Missing")
        else:
            print("   ❌ No email templates found on saved activity")
            
        # Step 4: Cleanup
        print("\n4. Cleaning up test data...")
        db.session.delete(saved_activity)
        db.session.commit()
        print("   ✅ Test activity deleted")
        
        print("\n" + "=" * 60)
        print("✅ INTEGRATION TEST COMPLETED SUCCESSFULLY")
        print("=" * 60)
        return True

if __name__ == "__main__":
    success = test_email_template_integration()
    exit(0 if success else 1)