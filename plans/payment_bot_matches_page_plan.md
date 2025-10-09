# Plan: Payment Bot Matches Page with Badge Notification System

## Overview
Create a new "Payment Bot Matches" page under a Reports section in the navigation menu. This page will show ALL payment bot activity (both matched and unmatched) with actions available for unmatched payments. A badge will show the count of unmatched payments requiring attention.

---

## 1. Navigation Menu Updates

### Add Reports Section (before Settings)
```
Dashboard
Activities
Signups
Passports
Surveys
AI Analytics
→ **Reports** (NEW SECTION)
   └─ Payment Bot Matches (with orange badge showing unmatched count)
Settings
```

### Badge Implementation
- Show orange badge with count of `NO_MATCH` payments (e.g., "3")
- Badge only appears when count > 0
- Similar styling to signup badge (orange color for attention)
- Update badge count dynamically when actions are taken

**Files to modify:**
- `templates/base.html` - Add Reports section to sidebar navigation
- Add badge logic similar to existing signup badge

---

## 2. New Route & Page: Payment Bot Matches

### Create new route in `app.py`
```python
@app.route("/payment-bot-matches")
@login_required
def payment_bot_matches():
    # Get all payments (matched and unmatched)
    # Deduplicate: keep only latest entry per unique payment
    # Return to template with counts
```

### Template: `templates/payment_bot_matches.html`
- Extends base.html
- Uses Tabler.io table styling (consistent with signups/passports)
- Pagination: 50 entries per page, with page navigation
- Search functionality: filter by name, amount, or date

---

## 3. Table Design & Columns

### Table Columns:
1. **Date/Time** - When payment was received
2. **Name** - From payment email (bank_info_name)
3. **Amount** - Payment amount (bank_info_amt)
4. **Status** - Badge showing:
   - 🟢 "MATCHED" (green badge)
   - 🟠 "NO MATCH" (orange badge)
   - 🔵 "MANUAL PROCESSED" (blue badge)
5. **Matched To** - Passport ID or "—" if unmatched
6. **Actions** - Buttons based on status:
   - For NO_MATCH: "Archive Email" button
   - For MATCHED: No action needed
   - For MANUAL_PROCESSED: "Archived" label (no button)

### Deduplication Logic
- Query: Get latest entry per unique (bank_info_name, bank_info_amt, from_email)
- Use SQL with `GROUP BY` and `MAX(id)` to eliminate duplicates
- Show clean list without 100x duplicates of same payment

---

## 4. Actions on the Page

### "Archive Email" Button (for NO_MATCH entries)
**What it does:**
1. Opens confirmation modal: "Move email for [Name] ($[Amount]) to ManualProcessed folder?"
2. On confirm:
   - Calls `/api/move-payment-email` endpoint (already exists!)
   - Moves email from inbox → ManualProcessed folder on mail server
   - Updates database: Changes `result` from `NO_MATCH` to `MANUAL_PROCESSED`
   - Reloads page to show updated status
3. Button becomes "Archived" label (disabled, blue badge)

**API endpoint:** Already implemented at `app.py:1947` - `/api/move-payment-email`

---

## 5. Dashboard Recent Events Updates

### Keep showing events on dashboard
- Continue showing recent payment events in dashboard logs
- Show both MATCHED and NO_MATCH entries
- **Remove** the "Archive Email" button from dashboard logs
- Dashboard is for **viewing** activity, not taking actions
- Link to "Payment Bot Matches" page for actions

---

## 6. Search & Filter Features

### Search bar at top of table
- Search by name (fuzzy search)
- Search by amount
- Search by date range

### Status filter dropdown
- "All" (default)
- "No Match Only" (show only NO_MATCH)
- "Matched Only" (show only MATCHED)
- "Manual Processed" (show only MANUAL_PROCESSED)

---

## 7. Database Query Optimization

### Deduplicated Query Example:
```sql
SELECT * FROM ebank_payment
WHERE id IN (
    SELECT MAX(id)
    FROM ebank_payment
    GROUP BY bank_info_name, bank_info_amt, from_email
)
ORDER BY timestamp DESC
LIMIT 50 OFFSET [page * 50]
```

### Badge Count Query:
```sql
SELECT COUNT(DISTINCT CONCAT(bank_info_name, bank_info_amt, from_email))
FROM ebank_payment
WHERE result = 'NO_MATCH'
```

---

## 8. Implementation Steps

### Step 1: Backend Routes
1. Create `/payment-bot-matches` route in `app.py`
2. Add helper function to get deduplicated payments
3. Add helper function to count unmatched payments (for badge)

### Step 2: Template Creation
1. Create `templates/payment_bot_matches.html`
2. Design table using Tabler.io components
3. Add pagination controls (using existing patterns)
4. Add search bar and filter dropdown

### Step 3: Navigation Menu
1. Add "Reports" section to `templates/base.html` sidebar
2. Add "Payment Bot Matches" link with badge
3. Badge shows count of NO_MATCH entries

### Step 4: JavaScript Functionality
1. Add `movePaymentEmail()` function (similar to dashboard)
2. Add confirmation modal HTML
3. Wire up Archive Email buttons
4. Add search functionality (client-side or server-side)

### Step 5: Dashboard Cleanup
1. Remove "Archive Email" button from dashboard logs
2. Keep showing events for visibility
3. Maybe add link: "View all in Payment Bot Matches →"

### Step 6: Testing
1. Test with production backup data (4889 entries)
2. Verify deduplication works (only latest entry shown)
3. Test Archive Email button functionality
4. Verify badge count updates after archiving
5. Test pagination with 50+ entries
6. Test search and filter features

---

## 9. Files to Create/Modify

### New Files:
- `templates/payment_bot_matches.html` - Main page template

### Files to Modify:
- `app.py` - Add `/payment-bot-matches` route
- `templates/base.html` - Add Reports section to navigation
- `templates/dashboard.html` - Remove Archive Email buttons from logs (keep events visible)
- `utils.py` - Add deduplication query helper function (if needed)

---

## 10. Success Criteria

✅ New "Reports" section appears in sidebar navigation before Settings
✅ Badge shows count of NO_MATCH payments (e.g., orange "3")
✅ Payment Bot Matches page displays beautiful table (like signups/passports)
✅ Table shows deduplicated entries (no 100x duplicates)
✅ Table shows MATCHED, NO_MATCH, and MANUAL_PROCESSED statuses
✅ Archive Email button works for NO_MATCH entries
✅ Email moves to ManualProcessed folder on mail server
✅ Database updates to MANUAL_PROCESSED after archiving
✅ Badge count decreases when payments are archived
✅ Pagination works (50 per page)
✅ Search filters by name/amount
✅ Dashboard still shows recent events (without action buttons)
✅ Field user can handle unmatched payments in under 30 seconds

---

## 11. User Workflow (Field User Experience)

1. Admin sees orange badge "3" on Reports → Payment Bot Matches
2. Clicks to open Payment Bot Matches page
3. Sees clean table with 3 NO_MATCH entries:
   - Christian Tremblay - $160.00 - 🟠 NO MATCH - [Archive Email]
   - Jean-Martin Morin - $80.00 - 🟠 NO MATCH - [Archive Email]
   - Yannick Drapeau - $50.00 - 🟠 NO MATCH - [Archive Email]
4. Clicks "Archive Email" for each → Confirms → Email moved
5. Status changes to 🔵 MANUAL PROCESSED
6. Badge updates to "0" (all handled)
7. Done in ~30 seconds! ✅

---

## Notes

- Reuses existing `/api/move-payment-email` endpoint - no new API needed
- Badge provides visibility into pending issues
- Centralized page = simple, clear workflow for field users
- Deduplication handled at query level = clean display
- Dashboard remains informational (no clutter with action buttons)
- Consistent UI/UX with existing signups/passports pages

---

## Current State Analysis

### What's Already Working:
1. **"Archive Email" button** already exists in dashboard for "Payment No Match" entries
2. **API endpoint** `/api/move-payment-email` is implemented in `app.py:1947`
3. **Move function** `move_payment_email_by_criteria()` exists in `utils.py:1476`
4. **Email archiving** moves emails to `ManualProcessed` folder on mail server
5. **Database tracking** marks archived payments as `MANUAL_PROCESSED` to prevent duplicate archiving
6. **Duplicate cleanup tool** already exists in Settings → Your Data (recently moved there)

### Current Issues to Address:
1. **Mass duplicates in logs** - 4889 entries with many duplicated 10-100 times
2. **Three specific unmatched payments:**
   - Christian Tremblay: $160.00
   - Jean-Martin Morin: $80.00
   - Yannick Drapeau: $50.00
3. **UI/UX issue** - Archive Email buttons on dashboard logs are not intuitive for field users

### Root Cause Investigation Needed:
1. Why are duplicates being created?
2. Why did these 3 payments not match despite passports potentially existing?
3. Are there timing issues (email arrives before passport created)?
4. Are there name normalization issues (accents, hyphens, case sensitivity)?
