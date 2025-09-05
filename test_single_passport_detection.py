#!/usr/bin/env python3
"""
Test script to verify single passport type detection logic
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import PassportType, Activity, db

def test_single_passport_detection():
    """Test the single passport type detection logic"""
    with app.app_context():
        # Test with different activities to check passport type counts
        activities = Activity.query.limit(10).all()
        
        for activity in activities:
            passport_types = PassportType.query.filter_by(
                activity_id=activity.id, 
                status='active'
            ).all()
            
            # Apply the same logic as in create_passport()
            single_passport_type_id = None
            if len(passport_types) == 1:
                single_passport_type_id = passport_types[0].id
            
            print(f"Activity ID {activity.id} ({activity.name}): {len(passport_types)} passport types")
            if single_passport_type_id:
                print(f"  -> Auto-select passport type ID: {single_passport_type_id}")
            else:
                print(f"  -> No auto-selection (multiple or no passport types)")
            print()

if __name__ == "__main__":
    test_single_passport_detection()