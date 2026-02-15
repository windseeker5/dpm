# Payment Bot - Create Passport from Payment Fix Plan

**Date:** 2026-01-28 (Updated: 2026-01-29)
**Status:** FIXES APPLIED - READY FOR TESTING

## Overview

Fixing the "Create Passport from Payment" feature in the payment bot matches page (`/payment-bot-matches`).

## Issues Identified

### Issue 1: Cosmetic (FIXED)
- **Problem:** Example used real name "Rusty Ouellet"
- **Fix:** Changed to "Roger Ouellet" and "Gestion Roger Inc"
- **File:** `templates/payment_bot_matches.html` line ~364
- **Status:** DONE

### Issue 2: Ugly JavaScript Alert (FIXED)
- **Problem:** Native `alert()` popup after creating passport
- **Fix:** Replaced with flash messages (green=success, yellow=warning, red=error)
- **File:** `templates/payment_bot_matches.html` - JavaScript section
- **File:** `app.py` - API endpoint added flash() calls
- **Status:** DONE

### Issue 3: Email Not Moving to PaymentProcessed Folder (FIXED 2026-01-29)
- **Problem:** After creating passport, the email stays in inbox instead of moving to PaymentProcessed folder
- **Root Cause 1:** Code was searching `FROM "{payment.from_email}"` but from_email is the PAYER's email, not the INTERAC sender
- **Root Cause 2:** Amount format mismatch - searching "60.00" but email contains "60,00 $" (French Canadian)
- **Root Cause 3:** The for loop was accidentally placed in `else` block instead of `if` block
- **Root Cause 4:** Folder not being created/selected before COPY operation
- **Root Cause 5:** Non-breaking spaces (\xa0) in French Canadian emails not being normalized
- **Fix Applied (2026-01-29):**
  - Changed to search ALL emails in inbox
  - Filter by name + amount in body
  - Added multiple amount formats: "60.00", "60,00", "60", etc.
  - Fixed the for loop placement
  - **NEW:** Added folder creation before COPY (like working payment bot does)
  - **NEW:** Added non-breaking space normalization for amount matching
  - **NEW:** Added better debug output when no match found
- **File:** `app.py` lines ~2656-2760
- **Status:** FIXED - NEEDS TESTING

### Issue 4: No "Payment Confirmed" Email (FIXED 2026-01-29)
- **Problem:** Only sending "passport created" email, not "payment confirmed" email
- **Root Cause:** The `event_type_mapping` in `notify_pass_event()` had NO mapping for `pass_paid`!
  When `event_type="pass_paid"` was passed, it defaulted to `'newPass'` template.
  User was receiving TWO "passport created" emails instead of "created" + "paid".
- **Fix Applied (2026-01-29):**
  - Added second `notify_pass_event()` call with `event_type="pass_paid"` (was already done)
  - **ROOT FIX:** Added `'pass_paid': 'paymentReceived'` mapping to THREE places in `utils.py`:
    - Line ~2996: `event_type_mapping` dict
    - Line ~3020: First `template_mapping` dict
    - Line ~3098: Second `template_mapping` dict
- **File:** `utils.py` lines ~2994-3000, ~3018-3025, ~3096-3103
- **Status:** FIXED - NEEDS TESTING

### Issue 5: Variable Name Bug Causing Crash (FIXED)
- **Problem:** `UnboundLocalError: cannot access local variable 'success_msg'`
- **Root Cause:** Used `success_msg` in if branch, `warning_msg` in else branch, but return statement used `success_msg`
- **Fix:** Changed to use `result_msg` consistently in both branches
- **File:** `app.py` lines ~2768-2790
- **Status:** DONE

### Issue 6: Flash Message Color Logic (FIXED)
- **Problem:** Green flash even when email move failed
- **Fix:** Green if fully successful, Yellow/Warning if email move failed
- **File:** `app.py` lines ~2768-2781
- **Status:** DONE

## Files Modified

1. **`templates/payment_bot_matches.html`**
   - Line ~364: Changed example name from Rusty to Roger
   - Line ~359: Made caution icon explicitly red
   - JavaScript: Replaced alert() with page reload (flash message shown by server)
   - Removed unused Result Notification Modal HTML

2. **`app.py`** - `api_create_passport_from_payment()` function (~line 2511-2800)
   - Added flash() calls for success/warning/error
   - Added "pass_paid" notification email
   - Fixed email search logic (ALL instead of FROM)
   - Added multiple amount formats for French Canadian
   - Fixed for loop placement bug
   - Fixed variable name bug (success_msg -> result_msg)
   - Added debug print statements

## Code Changes Summary

### Email Move Logic (app.py ~line 2659-2730)
```python
# OLD (broken):
status, data = mail.search(None, f'FROM "{payment.from_email}"')

# NEW (fixed):
status, data = mail.search(None, "ALL")
# Then filter by name + amount in body with multiple formats
amt_formats = [
    f"{amt_float:.2f}",           # 60.00
    f"{amt_float:.2f}".replace(".", ","),  # 60,00 (French)
    f"{int(amt_float)}",          # 60
    f"{int(amt_float)},00",       # 60,00
    f"{int(amt_float)}.00",       # 60.00
]
```

### Flash Message Logic (app.py ~line 2768-2781)
```python
result_msg = f"Passport created for {user_name}"
if email_sent:
    result_msg += f" - confirmation email sent to {user_email}"

if email_moved:
    flash(result_msg, "success")  # Green
else:
    result_msg += ". Warning: payment email could not be moved from inbox (manual cleanup needed)"
    flash(result_msg, "warning")  # Yellow
```

### Dual Email Notifications (app.py ~line 2746-2763)
```python
# Send "passport created" email
notify_pass_event(..., event_type="pass_created", ...)

# Also send "payment confirmed" email since passport is already paid
notify_pass_event(..., event_type="pass_paid", ...)
```

## Debug Output Added

Look for these in Flask logs:
```
📧 EMAIL MOVE: Starting... mail_user=xxx, processed_folder=xxx
📧 EMAIL MOVE: Looking for payment: name='xxx', amount=xxx
🔍 Searching X emails for name='xxx' and amount formats: [...]
📧 Found matching email (UID: xxx)
✅ Payment email moved to xxx folder
```

## Testing Steps

1. Send an e-transfer payment
2. Wait for payment bot to process (should show as "No Match" if no unpaid passport exists)
3. Click "Actions" > "Create Passport"
4. Fill form and click "Create Passport"
5. **Expected Results:**
   - Yellow warning OR green success flash message (no crash)
   - Receive "passport created" email
   - Receive "payment confirmed" email
   - Email moved from inbox to PaymentProcessed folder
   - No ugly JavaScript alert

## Next Steps if Still Failing

1. Check Flask logs for debug output about email move
2. If no debug output, check if MAIL_USERNAME/MAIL_PASSWORD are set
3. If searching but not finding, check email body format vs search criteria
4. May need to add more amount format variations

## Related Files

- `utils.py` - Contains the main payment bot logic that works correctly
- `templates/base.html` - Contains flash message CSS/JS
- `docs/DESIGN_SYSTEM.md` - Color codes for flash messages
