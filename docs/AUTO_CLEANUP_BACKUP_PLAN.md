# Auto-Cleanup Backup Implementation Plan

## Objective
Modify `api/backup.py` to automatically delete old backup files, keeping only the 3 most recent backups to prevent unlimited disk space growth.

## Problem Statement
Currently, each restore operation creates permanent safety backups that never get deleted:
- `instance/*.backup_*` (database backups, ~6-10MB each)
- `static/uploads_backup_*/` folders (~5-8MB each)
- `templates/email_templates_backup_*/` folders (~5-10MB each)
- Restore points in `instance/restore_points/` (~21MB each)

**Impact**: 10 restores = 200-500MB wasted space. Without cleanup, this grows indefinitely.

## Solution: Option 2 - Auto-Cleanup with Keep Count = 3

Automatically delete old backups when new ones are created, keeping only the 3 most recent backups.

### Risk Assessment: **LOW (2/10)**

**Why Low Risk:**
- No changes to core backup/restore logic
- Only adding cleanup functions that delete old files
- Cleanup happens AFTER new backup is successfully created
- Original backup/restore functionality remains unchanged
- Uses glob patterns to safely identify backup files by timestamp pattern

**Potential Risks:**
1. Pattern matching could theoretically match unintended files (mitigated by specific timestamp patterns)
2. Race condition if multiple restores happen simultaneously (unlikely in single-user scenario)

**Mitigation:**
- Test thoroughly before deploying to production
- Keep backup of current working code
- Pattern matching is very specific (`*.backup_YYYYMMDD_HHMMSS`)

## Implementation Steps

### 1. Add Cleanup Functions

Add two new functions to `api/backup.py`:

```python
def cleanup_old_restore_points(keep_count=3):
    """
    Delete old restore point ZIP files, keeping only the most recent ones.

    Args:
        keep_count (int): Number of most recent restore points to keep
    """
    restore_dir = os.path.join('instance', 'restore_points')
    if not os.path.exists(restore_dir):
        return

    # Get all restore point ZIP files with timestamp pattern
    pattern = os.path.join(restore_dir, 'restore_point_*.zip')
    restore_files = glob.glob(pattern)

    # Sort by modification time (newest first)
    restore_files.sort(key=os.path.getmtime, reverse=True)

    # Delete old files beyond keep_count
    for old_file in restore_files[keep_count:]:
        try:
            os.remove(old_file)
            print(f"Deleted old restore point: {old_file}")
        except Exception as e:
            print(f"Error deleting {old_file}: {e}")


def cleanup_old_safety_backups(keep_count=3):
    """
    Delete old safety backups created before restore operations.
    Cleans up:
    - instance/*.backup_* (database backups)
    - static/uploads_backup_*/ (upload folder backups)
    - templates/email_templates_backup_*/ (template folder backups)

    Args:
        keep_count (int): Number of most recent backups to keep for each type
    """
    # Cleanup database backups
    db_backup_pattern = 'instance/*.backup_*'
    db_backups = glob.glob(db_backup_pattern)
    db_backups.sort(key=os.path.getmtime, reverse=True)
    for old_backup in db_backups[keep_count:]:
        try:
            os.remove(old_backup)
            print(f"Deleted old database backup: {old_backup}")
        except Exception as e:
            print(f"Error deleting {old_backup}: {e}")

    # Cleanup uploads backups
    uploads_backup_pattern = 'static/uploads_backup_*'
    uploads_backups = glob.glob(uploads_backup_pattern)
    uploads_backups.sort(key=os.path.getmtime, reverse=True)
    for old_backup in uploads_backups[keep_count:]:
        try:
            shutil.rmtree(old_backup)
            print(f"Deleted old uploads backup: {old_backup}")
        except Exception as e:
            print(f"Error deleting {old_backup}: {e}")

    # Cleanup template backups
    templates_backup_pattern = 'templates/email_templates_backup_*'
    template_backups = glob.glob(templates_backup_pattern)
    template_backups.sort(key=os.path.getmtime, reverse=True)
    for old_backup in template_backups[keep_count:]:
        try:
            shutil.rmtree(old_backup)
            print(f"Deleted old template backup: {old_backup}")
        except Exception as e:
            print(f"Error deleting {old_backup}: {e}")
```

### 2. Add Import Statement

At the top of `api/backup.py`, add:

```python
import glob
```

### 3. Modify `create_restore_point()` Function

After successfully creating a restore point, add cleanup call:

```python
def create_restore_point():
    """Create a restore point before proceeding with backup restoration."""
    try:
        # ... existing code to create restore point ...

        # NEW: Cleanup old restore points after successful creation
        cleanup_old_restore_points(keep_count=3)

        return {
            'success': True,
            'message': f'Restore point created: {restore_filename}',
            'restore_point': restore_filename
        }
    except Exception as e:
        # ... existing error handling ...
```

### 4. Modify `restore_backup()` Function

After successfully restoring all components, add cleanup call:

```python
def restore_backup(backup_file):
    """
    Restore a backup from the uploaded file.
    """
    try:
        # ... existing code for restore operations ...

        # NEW: Cleanup old safety backups after successful restore
        cleanup_old_safety_backups(keep_count=3)

        return {
            'success': True,
            'message': 'Backup restored successfully',
            'details': result
        }
    except Exception as e:
        # ... existing error handling ...
```

## Files to Modify

1. **api/backup.py**
   - Add `import glob` at top
   - Add `cleanup_old_restore_points(keep_count=3)` function
   - Add `cleanup_old_safety_backups(keep_count=3)` function
   - Modify `create_restore_point()` to call cleanup
   - Modify `restore_backup()` to call cleanup after restore

## Expected Results

### Space Savings
- **Maximum storage per backup type:**
  - Restore points: 3 × 21MB = 63MB maximum
  - Database backups: 3 × 10MB = 30MB maximum
  - Upload backups: 3 × 8MB = 24MB maximum
  - Template backups: 3 × 13MB = 39MB maximum
- **Total maximum**: ~156MB (vs unlimited growth)

### Behavior After Implementation
- After 4th restore: Oldest backup automatically deleted
- After 5th restore: Second oldest deleted
- System maintains rolling window of 3 most recent backups
- No manual cleanup required

## Testing Plan

### Test 1: Verify Cleanup After Restore
1. Perform 5 consecutive backup/restore cycles
2. Verify only 3 most recent backups exist in each location
3. Confirm oldest backups were deleted

### Test 2: Verify No Data Loss
1. Create backup with unique test data
2. Perform restore
3. Verify all data restored correctly
4. Confirm cleanup happened without affecting restore

### Test 3: Edge Case - First Restore
1. Clear all existing backups manually
2. Perform first restore
3. Verify no errors when cleanup runs with 0 existing backups

### Test 4: Edge Case - Exactly 3 Backups
1. Ensure exactly 3 backups exist
2. Perform restore (creating 4th backup)
3. Verify oldest deleted, 3 remain

## Rollback Plan

If issues arise:
1. Revert changes to `api/backup.py`
2. Restore from git commit before changes
3. Manually delete excess backup files if needed

## Timeline

- **Implementation**: 15-20 minutes
- **Testing**: 10-15 minutes
- **Total**: 25-35 minutes

## Success Criteria

✅ Auto-cleanup runs without errors
✅ Only 3 most recent backups retained
✅ No impact on backup/restore functionality
✅ Space growth capped at ~156MB maximum
✅ All tests pass successfully

---

**Status**: Approved and ready for implementation
**Date**: 2025-11-06
**Risk Level**: LOW (2/10)
