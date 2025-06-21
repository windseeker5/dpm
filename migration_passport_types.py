#!/usr/bin/env python3
"""
Database Migration Script: Passport Type Management Enhancement
================================================================

This script backfills missing passport_type_name data for existing passports
and ensures database consistency after adding the new fields.

Run this script after updating the models.py file with the new fields.

Author: Claude Code Assistant
Date: 2025-06-21
"""

import os
import sys
from datetime import datetime, timezone

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_migration():
    """Run the passport type migration"""
    
    try:
        # Import after adding path
        from app import app, db
        from models import Passport, PassportType
        
        print("🔧 Starting Passport Type Migration...")
        print("=" * 50)
        
        with app.app_context():
            # Get all passports that have a passport_type_id but no passport_type_name
            passports_to_update = Passport.query.filter(
                Passport.passport_type_id.isnot(None),
                Passport.passport_type_name.is_(None)
            ).all()
            
            print(f"📊 Found {len(passports_to_update)} passports needing type name backfill")
            
            updated_count = 0
            missing_types = []
            
            for passport in passports_to_update:
                passport_type = PassportType.query.get(passport.passport_type_id)
                
                if passport_type:
                    passport.passport_type_name = passport_type.name
                    updated_count += 1
                    print(f"✅ Updated passport {passport.pass_code} with type name '{passport_type.name}'")
                else:
                    # Passport type was deleted, we can't recover the name
                    missing_types.append({
                        'passport_id': passport.id,
                        'passport_code': passport.pass_code,
                        'missing_type_id': passport.passport_type_id
                    })
                    print(f"⚠️  Passport {passport.pass_code} has missing passport type ID {passport.passport_type_id}")
            
            # Commit the updates
            if updated_count > 0:
                db.session.commit()
                print(f"\n✅ Successfully updated {updated_count} passport records")
            
            # Handle missing passport types
            if missing_types:
                print(f"\n⚠️  Warning: {len(missing_types)} passports reference deleted passport types:")
                for missing in missing_types:
                    print(f"   - Passport {missing['passport_code']} (ID: {missing['passport_id']}) -> Missing Type ID: {missing['missing_type_id']}")
                
                print("\n🔧 Setting passport_type_name to 'Deleted Type' for orphaned passports...")
                for missing in missing_types:
                    passport = Passport.query.get(missing['passport_id'])
                    passport.passport_type_name = "Deleted Type"
                    passport.passport_type_id = None  # Clear the invalid foreign key
                
                db.session.commit()
                print(f"✅ Updated {len(missing_types)} orphaned passport records")
            
            # Check for passport types that should be marked as archived
            print("\n🔍 Checking for passport types that should be archived...")
            
            # Get all passport types with active status
            active_passport_types = PassportType.query.filter_by(status='active').all()
            archived_count = 0
            
            for pt in active_passport_types:
                # Check if this passport type has any passports
                passport_count = Passport.query.filter_by(passport_type_id=pt.id).count()
                
                if passport_count == 0:
                    print(f"ℹ️  Passport type '{pt.name}' has no associated passports")
                else:
                    print(f"ℹ️  Passport type '{pt.name}' has {passport_count} associated passports")
            
            # Summary
            print("\n" + "=" * 50)
            print("📈 Migration Summary:")
            print(f"   • {updated_count} passport type names backfilled")
            print(f"   • {len(missing_types)} orphaned passports fixed")
            print(f"   • {len(active_passport_types)} active passport types found")
            print("✅ Migration completed successfully!")
            
            return True
            
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

def verify_migration():
    """Verify the migration was successful"""
    
    try:
        from app import app, db
        from models import Passport, PassportType
        
        print("\n🔍 Verifying migration results...")
        
        with app.app_context():
            # Check for passports without type names but with type IDs
            problematic_passports = Passport.query.filter(
                Passport.passport_type_id.isnot(None),
                Passport.passport_type_name.is_(None)
            ).count()
            
            if problematic_passports > 0:
                print(f"⚠️  Warning: {problematic_passports} passports still missing type names")
                return False
            
            # Check for orphaned passport type references
            orphaned_passports = Passport.query.filter(
                Passport.passport_type_id.isnot(None)
            ).join(PassportType, Passport.passport_type_id == PassportType.id, isouter=True).filter(
                PassportType.id.is_(None)
            ).count()
            
            if orphaned_passports > 0:
                print(f"⚠️  Warning: {orphaned_passports} passports reference non-existent passport types")
                return False
            
            # Count totals
            total_passports = Passport.query.count()
            passports_with_names = Passport.query.filter(
                Passport.passport_type_name.isnot(None)
            ).count()
            
            print(f"✅ Total passports: {total_passports}")
            print(f"✅ Passports with type names: {passports_with_names}")
            print("✅ Migration verification passed!")
            
            return True
            
    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Passport Type Enhancement Migration")
    print("=====================================")
    
    # Run migration
    success = run_migration()
    
    if success:
        # Verify migration
        verify_migration()
        print("\n🎉 All done! Your passport type management system has been enhanced.")
        print("\nNext steps:")
        print("1. Test the passport type deletion prevention in your admin interface")
        print("2. Verify that archived passport types work correctly")
        print("3. Check that passport displays show preserved type names")
    else:
        print("\n❌ Migration failed. Please check the errors above and try again.")
        sys.exit(1)