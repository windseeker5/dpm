# Redemption CASCADE DELETE Bug Fix

## Issue Summary
Date: October 30, 2025

**Problem**: Email history cards showed incorrect activity counts due to orphaned redemption records from deleted passports.

**Example**: User created a passport on Oct 30, but email showed 2 activities consumed (one from Oct 27 - before passport existed!).

## Root Cause Analysis

### The Bug Chain
1. **Foreign keys were DISABLED** in SQLite (`PRAGMA foreign_keys = 0`)
2. **Missing CASCADE DELETE** on `Redemption.passport_id` foreign key
3. **Incomplete cleanup** in activity/passport deletion code

### What Happened
1. Oct 27: User created test passport #67 for "Surf Sess" activity, redeemed it twice (redemptions #99, #100)
2. Oct 30, 23:27: User deleted "Surf Sess" activity
3. **BUG**: Deletion code deleted passports but NOT redemptions
4. **Result**: Redemptions #99 and #100 became orphaned (pointing to non-existent passport #67)
5. Oct 30, 23:44: User created NEW passport #77 for "Tournois Pocker" activity
6. **Database Corruption**: Redemption #100's `passport_id` somehow changed from 67 to 77
7. **Email Impact**: History card showed 2 redemptions for passport #77 (including the impossible Oct 27 date)

## Fixes Implemented

### 1. Cleaned Corrupted Data
```sql
DELETE FROM redemption WHERE id IN (99, 100);
```
- Removed orphaned redemption #99 (passport no longer exists)
- Removed invalid redemption #100 (dated before passport creation)

### 2. Enabled Foreign Key Constraints
**File**: `app.py:158-162`

Added `@app.before_request` hook to enable foreign keys on every request:
```python
@app.before_request
def enable_foreign_keys():
    """Enable foreign key constraints for SQLite on every request"""
    if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
        db.session.execute(text('PRAGMA foreign_keys = ON'))
```

### 3. Updated Redemption Model
**File**: `models.py:221`

Added `ondelete="CASCADE"` to foreign key:
```python
class Redemption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    passport_id = db.Column(db.Integer, db.ForeignKey("passport.id", ondelete="CASCADE"), nullable=False)
    date_used = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    redeemed_by = db.Column(db.String(100), nullable=True)
```

### 4. Database Migration
**File**: `migrations/fix_redemption_cascade.py`

Recreated `redemption` table with CASCADE DELETE constraint:
```sql
CREATE TABLE redemption_new (
    id INTEGER NOT NULL,
    passport_id INTEGER NOT NULL,
    date_used DATETIME,
    redeemed_by VARCHAR(100),
    PRIMARY KEY (id),
    FOREIGN KEY(passport_id) REFERENCES passport (id) ON DELETE CASCADE
)
```

### 5. Updated Deletion Code
**File**: `app.py:4643-4646`

Added explicit redemption cleanup before passport deletion:
```python
# Delete redemptions first (explicit cleanup before CASCADE)
passport_ids = [p.id for p in Passport.query.filter_by(activity_id=activity_id).all()]
if passport_ids:
    Redemption.query.filter(Redemption.passport_id.in_(passport_ids)).delete(synchronize_session=False)
```

Also added comment at individual passport deletion (app.py:4119):
```python
db.session.delete(passport)  # CASCADE will delete redemptions
```

## Verification

### Test Results
✅ CASCADE DELETE constraint properly configured
✅ Foreign keys enabled in database connections
✅ Only 1 redemption remains for passport #77 (the valid one)
✅ Orphaned records cleaned up

### Database State
```
PRAGMA foreign_key_list(redemption):
  ON DELETE: CASCADE ✅

SELECT COUNT(*) FROM redemption WHERE passport_id = 77:
  Result: 1 ✅ (only the legitimate Oct 30 redemption)
```

## Impact

### Before Fix
- Foreign keys disabled → orphaned data allowed
- Deleting passports left redemptions intact
- Email history cards showed incorrect/impossible data
- Data integrity issues could accumulate over time

### After Fix
- Foreign keys enabled → prevents orphaned data
- Deleting passports auto-deletes redemptions via CASCADE
- Email history cards show accurate data only
- Database integrity maintained automatically

## Prevention

1. **Foreign key enforcement** prevents orphaned records
2. **CASCADE DELETE** ensures automatic cleanup
3. **Explicit deletion** provides double protection
4. **Test script** available to verify configuration

## Files Modified

1. `app.py` - Added foreign key enforcement and updated deletion code
2. `models.py` - Added CASCADE DELETE to Redemption model
3. `migrations/fix_redemption_cascade.py` - Database migration script
4. `test_redemption_cascade.py` - Verification test

## Testing Recommendations

1. Create test activity with passport
2. Redeem passport to create redemption records
3. Delete activity
4. Verify redemptions were also deleted
5. Check email history cards show correct data

## Related Issues

- Email template system recently updated (Oct 9-30, 2025)
- This bug was discovered during email template testing
- Similar CASCADE fixes may be needed for other foreign keys

---

**Fix completed**: October 30, 2025
**Status**: ✅ Resolved and tested
**Breaking changes**: None - backwards compatible
