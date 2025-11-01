# PAYMENT BOT BUG - FINAL FIX PLAN
## Created: 2025-11-01 - Context save before auto-compact

## THE PROBLEM (CONFIRMED)

**Bot WAS running in October, NOT broken for 35 days**

Bot successfully:
- ✅ Found payment emails
- ✅ Matched to passports
- ✅ Set `passport.paid = True`
- ✅ Set `passport.paid_date`

Bot FAILED:
- ❌ `passport.marked_paid_by = "gmail-bot@system"` → Field is NULL in DB (doesn't persist)
- ❌ `EbankPayment` MATCHED records not created
- ❌ Emails not moved to processed folder

**Evidence**: 32 out of 74 paid passports have NULL `marked_paid_by` (43.2%)
**Zero passports** have "gmail-bot@system" value

## ROOT CAUSE (HYPOTHESIS)

SQLAlchemy session issue causing partial commit:
- Some fields persist (paid, paid_date)
- Other fields don't persist (marked_paid_by)
- Entire EbankPayment object creation fails

**Possible causes**:
1. Exception between setting field and commit
2. Autoflush at wrong time
3. Session tracking issue
4. Database constraint violation on EbankPayment causing partial rollback

## FIXES ALREADY IMPLEMENTED

### File: `/home/kdresdell/Documents/DEV/minipass_env/app/utils.py`

**Lines 1515-1603: Added comprehensive logging + exception handling**
```python
try:
    # Set all fields
    best_passport.paid = True
    best_passport.paid_date = now_utc
    best_passport.marked_paid_by = "gmail-bot@system"

    # Log pre-commit state
    print(f"🔍 PRE-COMMIT STATE:")
    print(f"   marked_paid_by = {repr(best_passport.marked_paid_by)}")

    # Create EbankPayment
    db.session.add(EbankPayment(...))

    # EXPLICIT FLUSH before commit
    db.session.flush()

    # Commit
    db.session.commit()

    # VERIFY what persisted
    db.session.refresh(best_passport)
    print(f"🔍 POST-COMMIT VERIFICATION:")
    print(f"   marked_paid_by = {repr(best_passport.marked_paid_by)}")

    if best_passport.marked_paid_by != "gmail-bot@system":
        print(f"❌ BUG DETECTED!")

except Exception as e:
    traceback.print_exc()
    db.session.rollback()
    continue
```

**Lines 617-628: Fixed display bug**
```python
# Now shows actual marked_paid_by from DB instead of session admin fallback
marked_by = getattr(hockey_pass, "marked_paid_by", None)
if marked_by:
    history["paid_by"] = marked_by
elif fallback_admin_email:
    history["paid_by"] = fallback_admin_email
else:
    history["paid_by"] = "system (no audit trail)"
```

## NEXT STEPS TO FIND BUG

### Step 1: Wait for new payment email to arrive
Current inbox only has already-paid passports, can't test with those

### Step 2: When new email arrives, run:
```bash
cd /home/kdresdell/Documents/DEV/minipass_env/app
venv/bin/python test_payment_bot.py
```

### Step 3: Look for in logs:
```
🎯 MATCH FOUND - STARTING PAYMENT PROCESSING
🔍 PRE-COMMIT STATE:
   marked_paid_by = 'gmail-bot@system'
✅ COMMITTED to database
🔍 POST-COMMIT VERIFICATION (refreshed from DB):
   marked_paid_by = None    ← IF THIS HAPPENS, BUG STILL EXISTS
❌ BUG DETECTED: marked_paid_by didn't persist!
```

### Step 4A: IF BUG DETECTED
The explicit flush didn't fix it. Next fixes to try:

1. **Check if there's a model hook interfering**:
```bash
grep -n "__setattr__\|before_update\|after_update" models.py
```

2. **Try raw SQL instead of ORM**:
```python
# After setting fields, use raw SQL
db.session.execute(
    "UPDATE passport SET marked_paid_by = :val WHERE id = :id",
    {"val": "gmail-bot@system", "id": best_passport.id}
)
db.session.commit()
```

3. **Check for competing commits**:
```python
# Add logging to see if something else commits between our changes
import threading
print(f"Thread: {threading.current_thread().name}")
```

### Step 4B: IF BUG NOT DETECTED
The explicit flush() fixed it! The bug was SQLAlchemy not flushing changes before commit.

## ADDITIONAL FIX NEEDED (Regardless of bug status)

### Move email BEFORE database commit (transaction safety)

**Current flow (BROKEN)**:
1. Match payment
2. Mark passport paid
3. Commit to DB
4. Try to move email → **IF THIS FAILS, email stays in inbox**
5. Next run: reprocess same email as NO_MATCH

**Fixed flow**:
```python
if best_passport:
    # 1. Try to move email FIRST
    email_moved = False
    if uid:
        try:
            copy_result = mail.uid("COPY", uid, processed_folder)
            if copy_result[0] == 'OK':
                mail.uid("STORE", uid, "+FLAGS", "(\\Deleted)")
                email_moved = True
        except Exception as e:
            print(f"Email move failed: {e}")

    # 2. Only proceed if email moved OR no uid
    if email_moved or not uid:
        # Mark passport paid and commit
        best_passport.paid = True
        best_passport.paid_date = now_utc
        best_passport.marked_paid_by = "gmail-bot@system"
        db.session.add(EbankPayment(...))
        db.session.flush()
        db.session.commit()
    else:
        print(f"Skipping payment - email move failed")
        continue
```

## FILES CREATED

1. `test_payment_bot.py` - Manual test script
2. `diagnose_payment_records.py` - Diagnostic analysis
3. `PAYMENT_BOT_FIX_SUMMARY.md` - Investigation summary
4. `FINAL_FIX_PLAN.md` - This file

## SCHEMA ISSUE (Non-critical)

`EbankPayment.matched_pass_id` has foreign key to "pass" table, should be "passport" table.
Not causing failures (SQLite foreign keys disabled), but data integrity issue.

## COMMANDS REFERENCE

```bash
# Run payment bot manually
venv/bin/python test_payment_bot.py

# Check current state
venv/bin/python diagnose_payment_records.py

# Check database schema
sqlite3 instance/minipass.db ".schema passport"
sqlite3 instance/minipass.db ".schema ebank_payment"

# Count passports with/without marked_paid_by
sqlite3 instance/minipass.db "SELECT COUNT(*) FROM passport WHERE paid=1 AND marked_paid_by IS NULL;"
sqlite3 instance/minipass.db "SELECT COUNT(*) FROM passport WHERE paid=1 AND marked_paid_by IS NOT NULL;"
```

## SUCCESS CRITERIA

✅ All new payments have `marked_paid_by = "gmail-bot@system"`
✅ EbankPayment MATCHED records created successfully
✅ Emails moved to processed folder before DB commit
✅ No more "NO_MATCH" records for payments that were actually matched
✅ Display shows correct "paid by" information

## IF CONTEXT IS LOST

1. Read this file
2. Read `PAYMENT_BOT_FIX_SUMMARY.md`
3. Run `diagnose_payment_records.py` to see current state
4. When new payment arrives, run `test_payment_bot.py`
5. Look for "❌ BUG DETECTED" in logs
6. If detected, try raw SQL fix (see Step 4A above)
