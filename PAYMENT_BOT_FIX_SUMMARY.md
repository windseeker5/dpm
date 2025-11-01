# Payment Bot Bug - Investigation Summary

## Problem Confirmed

**User was RIGHT**: The bot WAS running in October, NOT stopped for 35 days. The bot successfully marked passports as paid, but had a bug preventing proper audit trail.

## Evidence

### Database Analysis
- **74 paid passports total**
- **42 have `marked_paid_by` set** (all marked by "jf@jfgoulet.com" - manual admin action)
- **32 have `marked_paid_by = NULL`** (43.2%) - these were marked by buggy bot
- **ZERO passports have `marked_paid_by = "gmail-bot@system"`** - confirms bot field not persisting

### Specific Cases (Oct 27, 2025)
1. **Jean Bélanger** - Passport #90
   - Paid date: 2025-10-27 18:23:07
   - marked_paid_by: NULL
   - Bot found it already paid on Nov 1, created NO_MATCH

2. **Samuel Turbide** - Passport #78
   - Paid date: 2025-10-27 12:23:07
   - marked_paid_by: NULL
   - Bot found it already paid on Nov 1, created NO_MATCH

3. **Patrick Beland** - No matching passport found (different issue)

## Root Cause

**The bot in October was PARTIALLY working:**
1. ✅ Found payment emails
2. ✅ Matched to correct passports
3. ✅ Set `passport.paid = True`
4. ✅ Set `passport.paid_date = timestamp`
5. ❌ Set `passport.marked_paid_by = "gmail-bot@system"` BUT IT DIDN'T PERSIST
6. ❌ Created `EbankPayment` MATCHED record BUT IT FAILED (no records created)
7. ❌ Moved emails to processed folder BUT IT FAILED (emails stayed in inbox)

**Why marked_paid_by didn't persist**: UNKNOWN - needs live testing with new logging

**Why emails weren't moved**: Likely IMAP failure, but not critical since it's after DB commit

## Fixes Implemented

### 1. Comprehensive Logging ✅
Added detailed pre/post-commit logging to `utils.py`:
- Shows exact state before commit
- Flushes session explicitly
- Refreshes object after commit
- Detects if `marked_paid_by` didn't persist
- Shows "❌ BUG DETECTED" if field is NULL after commit

### 2. Exception Handling ✅
Wrapped payment processing in try/except:
- Catches any exceptions during processing
- Rolls back transaction on failure
- Continues to next payment instead of crashing
- Prints full stack trace for debugging

### 3. Display Bug Fixed ✅
Fixed `get_pass_history_data()` in `utils.py`:
- Now shows actual `marked_paid_by` value from database
- Falls back to session admin only if field is NULL
- Shows "system (no audit trail)" if no data available
- No longer misleads user by showing their email for bot-marked passports

### 4. Database Schema Checked ✅
- Foreign key constraint exists but is NOT enforced (SQLite pragma = 0)
- `EbankPayment.matched_pass_id` references old "pass" table, not "passport" table
- Not causing failures, but is a data integrity issue

## Testing Scripts Created

### 1. `test_payment_bot.py`
Manually trigger payment bot with detailed logging output

### 2. `diagnose_payment_records.py`
Analyze current state of payment records, identify issues

## Next Steps

### Immediate (User to do)

1. **Run bot manually** to see if the bug still occurs:
   ```bash
   cd /home/kdresdell/Documents/DEV/minipass_env/app
   venv/bin/python test_payment_bot.py
   ```

2. **Watch for these log messages**:
   - `🎯 MATCH FOUND` - bot found a match
   - `🔍 PRE-COMMIT STATE` - shows marked_paid_by = 'gmail-bot@system'
   - `✅ COMMITTED to database` - transaction completed
   - `🔍 POST-COMMIT VERIFICATION` - shows what actually persisted
   - `❌ BUG DETECTED: marked_paid_by didn't persist!` - THE SMOKING GUN

3. **If bug is detected**: We'll know exactly where the field is being lost

4. **If bug is NOT detected**: The fixes we made (explicit flush, better session handling) may have resolved it

### Follow-up Fixes (if needed)

**If marked_paid_by still doesn't persist:**
- Check for SQLAlchemy session auto-flush settings
- Add database-level trigger to log changes
- Consider using raw SQL UPDATE to bypass ORM
- Check if there's a model __setattr__ override interfering

**Additional improvements:**
- Move email BEFORE committing (transaction safety)
- Fix foreign key reference (pass → passport)
- Add retry logic for IMAP failures
- Create cleanup script to backfill missing marked_paid_by values

## Files Modified

1. `/home/kdresdell/Documents/DEV/minipass_env/app/utils.py`
   - Lines 1514-1603: Added logging, exception handling, explicit flush
   - Lines 617-628: Fixed display bug in get_pass_history_data()

2. `/home/kdresdell/Documents/DEV/minipass_env/app/test_payment_bot.py` (NEW)
   - Manual test script

3. `/home/kdresdell/Documents/DEV/minipass_env/app/diagnose_payment_records.py` (NEW)
   - Diagnostic analysis script

## Success Criteria

✅ Confirmed bot was running (not stopped for 35 days)
✅ Identified exact fields that aren't persisting
✅ Added comprehensive debugging
✅ Fixed misleading display
✅ Ready for live testing to identify persistence bug

❓ **NEXT**: Run test_payment_bot.py and watch logs for "BUG DETECTED" message
