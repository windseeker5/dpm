# migrations/migrate_to_enhanced_settings.py
"""
Migration script to upgrade from simple Settings table to enhanced settings architecture
"""
from sqlalchemy import text
from models import db, Setting
from models.settings import SettingSchema, SettingValue, SettingChangeLog, initialize_setting_schemas, SettingsManager
from datetime import datetime, timezone

def migrate_settings():
    """Migrate existing settings to new enhanced system"""
    
    print("Starting migration to enhanced settings system...")
    
    # Step 1: Create new tables
    print("Creating new settings tables...")
    db.create_all()
    
    # Step 2: Initialize setting schemas
    print("Initializing setting schemas...")
    initialize_setting_schemas()
    
    # Step 3: Migrate existing settings
    print("Migrating existing settings...")
    migrated_count = 0
    
    existing_settings = Setting.query.all()
    for setting in existing_settings:
        # Check if schema exists for this setting
        schema = SettingSchema.query.filter_by(key=setting.key).first()
        if not schema:
            print(f"Warning: No schema found for setting '{setting.key}', skipping...")
            continue
        
        # Create new setting value
        setting_value = SettingValue(
            key=setting.key,
            created_by='migration_script',
            updated_by='migration_script'
        )
        
        # Set value (will handle encryption for sensitive settings)
        try:
            setting_value.decrypted_value = setting.value
            db.session.add(setting_value)
            migrated_count += 1
            print(f"Migrated setting: {setting.key}")
        except Exception as e:
            print(f"Error migrating setting '{setting.key}': {e}")
    
    # Step 4: Add initial change log entry
    change_log = SettingChangeLog(
        setting_key='SYSTEM_MIGRATION',
        old_value=None,
        new_value='Enhanced settings system initialized',
        changed_by='migration_script',
        change_reason='System migration to enhanced settings architecture'
    )
    db.session.add(change_log)
    
    # Commit all changes
    db.session.commit()
    print(f"Migration completed! Migrated {migrated_count} settings.")
    
    # Step 5: Validate all settings
    print("Validating migrated settings...")
    errors = SettingsManager.validate_all()
    if errors:
        print("Validation errors found:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("All settings validated successfully!")
    
    return migrated_count, errors

def rollback_migration():
    """Rollback to simple settings system (emergency use only)"""
    print("WARNING: Rolling back to simple settings system...")
    
    # Step 1: Copy data back to simple Setting table
    setting_values = SettingValue.query.all()
    for setting_value in setting_values:
        existing = Setting.query.filter_by(key=setting_value.key).first()
        if existing:
            existing.value = setting_value.decrypted_value
        else:
            db.session.add(Setting(key=setting_value.key, value=setting_value.decrypted_value))
    
    # Step 2: Drop enhanced tables (careful!)
    db.session.execute(text('DROP TABLE IF EXISTS setting_change_logs'))
    db.session.execute(text('DROP TABLE IF EXISTS setting_values'))
    db.session.execute(text('DROP TABLE IF EXISTS setting_schemas'))
    
    db.session.commit()
    print("Rollback completed!")

def verify_migration():
    """Verify that migration was successful"""
    print("Verifying migration...")
    
    # Check that new tables exist and have data
    schema_count = SettingSchema.query.count()
    value_count = SettingValue.query.count()
    
    print(f"Setting schemas: {schema_count}")
    print(f"Setting values: {value_count}")
    
    # Test getting/setting values
    try:
        test_value = SettingsManager.get('ORG_NAME', 'Test Org')
        print(f"Test get setting: {test_value}")
        
        SettingsManager.set('TEST_SETTING', 'test_value', 'verification_script')
        retrieved_value = SettingsManager.get('TEST_SETTING')
        assert retrieved_value == 'test_value'
        
        # Clean up test setting
        test_setting = SettingValue.query.filter_by(key='TEST_SETTING').first()
        if test_setting:
            db.session.delete(test_setting)
            db.session.commit()
        
        print("Migration verification passed!")
        return True
    except Exception as e:
        print(f"Migration verification failed: {e}")
        return False

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python migrate_to_enhanced_settings.py [migrate|rollback|verify]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'migrate':
        migrate_settings()
    elif command == 'rollback':
        rollback_migration()
    elif command == 'verify':
        verify_migration()
    else:
        print("Invalid command. Use: migrate, rollback, or verify")