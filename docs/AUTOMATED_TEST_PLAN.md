# Complete Automated Test Plan - Minipass Pre-Launch Validation

**Created:** November 21, 2025
**Purpose:** Comprehensive automated testing of ALL Minipass features before production launch
**Execution Method:** Playwright MCP Server with real-time Flask log monitoring
**Test Environment:** Flask server running on `localhost:5000` (already running in debug mode)
**Test Email:** `kdresdell@gmail.com` (to avoid mail server restrictions)

---

## Testing Prerequisites

### Environment Setup
- ✅ Flask server: Already running on `localhost:5000` in debug mode
- ✅ Database: `instance/minipass.db` - clean state preferred
- ✅ Playwright: MCP Server available for browser automation
- ✅ Email: Use `kdresdell@gmail.com` for all test signups/passports

### Flask Log Monitoring
**Critical:** After EVERY action, check Flask logs to verify:
- Success confirmations (✅ markers in logs)
- Email sending confirmations: `✅✅✅ EMAIL SENT SUCCESSFULLY`
- Error messages or stack traces
- Database operations completion
- Payment matching results

**How to Monitor Logs:**
- Flask terminal is already running - watch output after each Playwright action
- Look for specific log markers related to the action performed
- Verify no errors or warnings appear

---

## Test Plan Structure

Each test section follows this pattern:
1. **Action:** Playwright browser automation step
2. **Log Check:** What to verify in Flask terminal logs
3. **Expected Result:** What should appear in browser and logs
4. **Failure Handling:** What to do if test fails

---

## PHASE 1: Admin & Authentication

### Test 1.1: Admin Login
**Goal:** Verify admin can log in successfully

**Playwright Actions:**
1. Navigate to `http://localhost:5000/login`
2. Fill email field with admin credentials
3. Fill password field
4. Click "Login" button
5. Verify redirect to dashboard

**Log Verification:**
```
Look for:
- "Admin logged in: [email]"
- No authentication errors
```

**Expected Result:**
- Browser: Redirect to `/` (dashboard)
- Logs: Successful admin session creation
- UI: Dashboard with "Welcome back" message

---

### Test 1.2: Admin Profile Update
**Goal:** Verify admin can update profile information

**Playwright Actions:**
1. From dashboard, click "Settings" in navigation
2. Navigate to "Profile" section
3. Update admin name/email (if editable)
4. Click "Save Changes"

**Log Verification:**
```
Look for:
- "Admin profile updated: [email]"
- "Database commit successful"
```

**Expected Result:**
- Browser: Success message displayed
- Logs: Profile update confirmation
- Database: Admin record updated

---

## PHASE 2: Activity Management

### Test 2.1: Create New Activity (Full Details)
**Goal:** Create complete activity with all fields populated

**Playwright Actions:**
1. Navigate to `/activities` or click "Activities" in nav
2. Click "Create New Activity" button
3. Fill ALL fields:
   - **Name:** "Test Hockey League - Nov 2025"
   - **Description:** "Monday night hockey league for testing all features"
   - **Start Date:** Today's date
   - **End Date:** 3 months from today
   - **Capacity:** 50
   - **Location:** "Rimouski Arena"
   - **Activity Type:** Select appropriate type
   - **Upload Logo:** Select a test image file (if required)
4. Click "Create Activity"

**Log Verification:**
```
Look for:
- "✅ Activity created: Test Hockey League - Nov 2025"
- "Activity ID: [number]"
- Database insert confirmation
- Logo upload success (if applicable)
```

**Expected Result:**
- Browser: Redirect to activity detail page OR activities list
- Success toast/message displayed
- Activity appears in activities list with all details
- Logs: Activity creation confirmation

**Note Activity ID:** Record the activity ID for use in subsequent tests

---

### Test 2.2: Update Activity Settings
**Goal:** Verify activity can be modified after creation

**Playwright Actions:**
1. Navigate to activity detail page
2. Click "Edit Activity" button
3. Update description field
4. Click "Save Changes"

**Log Verification:**
```
Look for:
- "Activity updated: [activity name]"
- Database update confirmation
```

**Expected Result:**
- Browser: Success message
- Changes reflected immediately in UI
- Logs: Update confirmation

---

## PHASE 3: Passport Types

### Test 3.1: Create Passport Type (Full Details)
**Goal:** Create passport type with all fields filled

**Playwright Actions:**
1. Navigate to activity detail page OR passport types page
2. Click "Create Passport Type"
3. Fill ALL fields:
   - **Name:** "Full Season Pass"
   - **Description:** "Complete season access with 20 games"
   - **Price:** 500.00
   - **Max Redemptions:** 20
   - **Valid From:** Today
   - **Valid Until:** 3 months from today
   - **Active:** Yes/checked
4. Click "Create Passport Type"

**Log Verification:**
```
Look for:
- "✅ Passport type created: Full Season Pass"
- "Passport Type ID: [number]"
- "Activity ID: [number] linked"
```

**Expected Result:**
- Browser: Success message, passport type appears in list
- Logs: Passport type creation confirmation
- Database: New passport type record

**Note Passport Type ID:** Record for subsequent tests

---

### Test 3.2: Create Second Passport Type (Substitute Pass)
**Goal:** Create alternative passport type to test multiple types

**Playwright Actions:**
1. Click "Create Passport Type" again
2. Fill fields:
   - **Name:** "Substitute Pass"
   - **Description:** "Drop-in games for substitutes"
   - **Price:** 25.00
   - **Max Redemptions:** 1
   - **Valid From:** Today
   - **Valid Until:** 3 months from today
   - **Active:** Yes
3. Click "Create"

**Log Verification:**
```
Look for:
- "✅ Passport type created: Substitute Pass"
- Multiple passport types for activity confirmation
```

**Expected Result:**
- Browser: Both passport types visible in list
- Logs: Creation confirmation

---

## PHASE 4: Signup & Registration

### Test 4.1: Create Signup Using Test Email
**Goal:** Create new signup and verify email notification sent

**Critical:** Use `kdresdell@gmail.com` to avoid mail server errors

**Playwright Actions:**
1. Navigate to signup form (public URL or admin interface)
   - If using admin interface: Click "Signups" → "Create Signup"
   - If using public form: Get activity signup URL
2. Fill signup form:
   - **Name:** "Test User - Automated"
   - **Email:** `kdresdell@gmail.com`
   - **Phone:** "418-555-0199"
   - **Passport Type:** Select "Full Season Pass"
   - **Quantity:** 1
   - **Notes:** "Automated test signup"
3. Submit form

**Log Verification (CRITICAL):**
```
Look for:
- "✅ Signup created: Test User - Automated"
- "Signup ID: [number]"
- "✅✅✅ EMAIL SENT SUCCESSFULLY"
- Email template: "signup"
- Recipient: kdresdell@gmail.com
- No mail server errors
- "Email queued for sending" OR "Email sent immediately"
```

**Expected Result:**
- Browser: Confirmation page with signup details
- Logs: **MUST see email sent confirmation**
- Database: Signup record created with status "pending"
- Email: Signup confirmation sent to kdresdell@gmail.com

**Note Signup ID:** Record for conversion test

**FAILURE HANDLING:**
- If no email log appears: Check Flask terminal for email errors
- If email fails: Check SMTP settings in Settings table
- If signup fails: Verify activity and passport type are active

---

### Test 4.2: View Signup in Admin Dashboard
**Goal:** Verify signup appears in admin interface

**Playwright Actions:**
1. Navigate to `/signups` (admin signups list)
2. Verify "Test User - Automated" appears
3. Click signup to view details

**Log Verification:**
```
Look for:
- Signup query executed
- User data loaded
```

**Expected Result:**
- Signup visible with all details
- Status: "Pending" or "Awaiting Payment"
- Email: kdresdell@gmail.com

---

## PHASE 5: Signup to Passport Conversion

### Test 5.1: Approve Signup and Convert to Passport
**Goal:** Convert signup to active passport and verify email sent

**Playwright Actions:**
1. From signup detail page, click "Approve" OR "Convert to Passport"
2. Confirm conversion (if confirmation modal appears)
3. Verify passport created

**Log Verification (CRITICAL):**
```
Look for:
- "✅ Signup approved: [signup ID]"
- "✅ Passport created from signup"
- "Passport ID: [number]"
- "✅✅✅ EMAIL SENT SUCCESSFULLY"
- Email template: "newPass"
- Recipient: kdresdell@gmail.com
- QR code generation log
- "QR code generated for passport [ID]"
```

**Expected Result:**
- Browser: Redirect to passport detail OR success message
- Logs: **Email sent confirmation with newPass template**
- Database:
  - Signup status updated to "converted"
  - New passport record created
  - Passport status: "active" or "unpaid"
- Email: newPass email sent with QR code

**Note Passport ID:** Record for redemption test

---

## PHASE 6: Payment Processing

### Test 6.1: Mark Passport as Paid
**Goal:** Mark passport as paid and verify payment email sent

**Playwright Actions:**
1. Navigate to passport detail page OR passports list
2. Find "Test User - Automated" passport
3. Click "Mark as Paid" OR update payment status
4. If payment amount required, enter: 500.00
5. If payment date required, select today
6. Confirm payment

**Log Verification (CRITICAL):**
```
Look for:
- "✅ Passport marked as paid: [passport ID]"
- "Payment amount: 500.00"
- "✅✅✅ EMAIL SENT SUCCESSFULLY"
- Email template: "paymentReceived"
- Recipient: kdresdell@gmail.com
- Database update confirmation
```

**Expected Result:**
- Browser: Passport status updated to "Paid"
- Success message displayed
- Logs: **Payment email sent confirmation**
- Database: Passport `paid` field = 1, `paid_date` = today
- Email: paymentReceived email sent to kdresdell@gmail.com

---

### Test 6.2: Verify Payment in Payment Inbox (if applicable)
**Goal:** Check payment appears in payment inbox dashboard

**Playwright Actions:**
1. Navigate to `/payment-inbox` OR "Reports" → "Payments"
2. Verify payment entry appears
3. Check payment status (MATCHED, etc.)

**Log Verification:**
```
Look for:
- Payment inbox query executed
- Payment record loaded
```

**Expected Result:**
- Payment visible in inbox
- Status: MATCHED or MANUAL_PROCESSED
- Amount: 500.00
- Linked to correct passport

---

## PHASE 7: Passport Redemption

### Test 7.1: Redeem Passport
**Goal:** Redeem passport and verify redemption email sent

**Playwright Actions:**
1. Navigate to passport redemption interface
   - Option A: QR code scanning page (manual entry)
   - Option B: Passport detail page → "Redeem" button
2. Redeem 1 session/use from the passport
3. Add redemption note (optional): "Test redemption - automated"

**Log Verification (CRITICAL):**
```
Look for:
- "✅ Passport redeemed: [passport ID]"
- "Redemptions remaining: [number]"
- "✅✅✅ EMAIL SENT SUCCESSFULLY"
- Email template: "redeemPass"
- Recipient: kdresdell@gmail.com
- Redemption history updated
```

**Expected Result:**
- Browser: Success message, redemption counter updated
- Logs: **Redemption email sent confirmation**
- Database:
  - Redemption record created
  - Passport `redeemed_count` incremented
  - Remaining redemptions = 19 (if max was 20)
- Email: redeemPass email sent showing updated balance

---

### Test 7.2: Redeem Multiple Times
**Goal:** Verify multiple redemptions work correctly

**Playwright Actions:**
1. Redeem the same passport 2 more times
2. Verify counter updates each time

**Log Verification:**
```
Look for:
- Multiple redemption confirmations
- Email sent for each redemption (3 emails total)
- Redemption count accurate
```

**Expected Result:**
- 3 total redemptions recorded
- Remaining redemptions = 17
- 3 redemption emails sent

---

## PHASE 8: Financial Management

### Test 8.1: Add Income Entry with Receipt
**Goal:** Create custom income entry with receipt upload

**Playwright Actions:**
1. Navigate to Financial Report page (`/financial-report`)
2. Click "Add Income" button (desktop drawer or mobile modal)
3. Fill income form:
   - **Date:** Today
   - **Category:** "Sponsorship"
   - **Amount:** 1000.00
   - **Activity:** Select "Test Hockey League"
   - **Notes:** "Test sponsorship income"
   - **Payment Status:** "received"
   - **Receipt Upload:** Upload a test PDF or image file
4. Click "Save Income"

**Log Verification:**
```
Look for:
- "✅ Income entry created"
- "Income ID: [number]"
- "Receipt uploaded: [filename]"
- "File size: [size]"
- Activity linkage confirmation
```

**Expected Result:**
- Browser: Success message, income appears in financial dashboard
- Logs: Income creation + receipt upload confirmation
- Database: Income record with receipt file path
- File: Receipt saved to `instance/receipts/` directory

---

### Test 8.2: Add Expense Entry with Receipt
**Goal:** Create expense entry with receipt upload

**Playwright Actions:**
1. Click "Add Expense" button
2. Fill expense form:
   - **Date:** Today
   - **Category:** "Venue"
   - **Amount:** 300.00
   - **Activity:** Select "Test Hockey League"
   - **Description:** "Arena rental for testing"
   - **Payment Status:** "paid"
   - **Receipt Upload:** Upload a test PDF or image file
3. Click "Save Expense"

**Log Verification:**
```
Look for:
- "✅ Expense entry created"
- "Expense ID: [number]"
- "Receipt uploaded: [filename]"
- Activity linkage
```

**Expected Result:**
- Browser: Expense appears in financial list
- Logs: Expense creation + receipt upload
- Database: Expense record with receipt
- Financial KPIs updated (Total Expenses increased)

---

### Test 8.3: View Receipt (Modal)
**Goal:** Verify receipt viewing works for both income and expense

**Playwright Actions:**
1. In financial report, find income entry with receipt
2. Click "View Receipt" link/button
3. Verify modal opens showing receipt (PDF or image)
4. Close modal
5. Repeat for expense receipt

**Log Verification:**
```
Look for:
- Receipt file access log
- "Serving receipt: [filename]"
```

**Expected Result:**
- Modal displays receipt correctly (PDF or image preview)
- Download option available
- No errors loading receipt files

---

### Test 8.4: Export Financial Data (CSV)
**Goal:** Export financial report to CSV for accounting

**Playwright Actions:**
1. On financial report page, select period filter (e.g., "All Time")
2. Click "Export CSV" button
3. Verify download initiated

**Log Verification:**
```
Look for:
- "CSV export requested"
- "Financial report generated"
- "Rows exported: [number]"
```

**Expected Result:**
- Browser: CSV file downloads
- Filename: `financial_report_YYYYMMDD.csv` or similar
- CSV Contents: All income and expense entries with proper formatting
- Columns: Date, Type (Income/Expense), Category, Amount, Activity, Notes, etc.
- Compatible with QuickBooks/Xero format

---

## PHASE 9: User Contact Management

### Test 9.1: View User Contacts List
**Goal:** Verify user contact directory loads correctly

**Playwright Actions:**
1. Navigate to "Reports" → "User Contacts" OR `/user-contacts`
2. Verify user list displays with:
   - User name
   - Email
   - Phone
   - Passport count
   - Revenue generated
   - Last activity date
   - Email opt-out status

**Log Verification:**
```
Look for:
- "User contacts query executed"
- "Users loaded: [count]"
- Engagement metrics calculated
```

**Expected Result:**
- Browser: Table/list showing all users
- Test user "Test User - Automated" visible
- Metrics accurate (1 passport, $500 revenue)
- Gravatar images loaded

---

### Test 9.2: Search User Contacts
**Goal:** Test search functionality

**Playwright Actions:**
1. Use search box (Ctrl+K shortcut)
2. Search for "Test User"
3. Verify filtered results

**Log Verification:**
```
Look for:
- Search query executed
- Filtered results count
```

**Expected Result:**
- Only matching users displayed
- Search is case-insensitive
- Real-time filtering works

---

### Test 9.3: Export User Contacts (CSV)
**Goal:** Export user contact list for CRM/marketing

**Playwright Actions:**
1. Click "Export CSV" button
2. Verify download

**Log Verification:**
```
Look for:
- "User contacts CSV export"
- "Rows exported: [number]"
```

**Expected Result:**
- CSV file downloads: `user_contacts_all_YYYYMMDD.csv`
- Contents: All user data with engagement metrics
- Format compatible with CRM tools (HubSpot, Mailchimp, etc.)

---

## PHASE 10: Payment Inbox

### Test 10.1: View Payment Inbox
**Goal:** Verify payment inbox dashboard displays correctly

**Playwright Actions:**
1. Navigate to "Reports" → "Payments" OR `/payment-inbox`
2. View all payment entries
3. Check status indicators (MATCHED, NO_MATCH, etc.)

**Log Verification:**
```
Look for:
- "Payment inbox loaded"
- "Payments count: [number]"
```

**Expected Result:**
- All payments visible
- Status badges color-coded
- Search and filter options available
- Pagination works (if > 50 payments)

---

### Test 10.2: Filter Payments by Status
**Goal:** Test filter functionality

**Playwright Actions:**
1. Click "Matched" filter button
2. Verify only matched payments shown
3. Click "No Match" filter
4. Verify only unmatched payments shown

**Log Verification:**
```
Look for:
- Filter query executed
- Results count for each filter
```

**Expected Result:**
- Filters work correctly
- GitHub-style filter buttons toggle
- Result count updates

---

## PHASE 11: Email Template Customization

### Test 11.1: Customize Email Template (newPass)
**Goal:** Customize newPass email template for activity

**Playwright Actions:**
1. Navigate to activity detail page
2. Click "Email Templates" tab OR "Customize Emails"
3. Select "newPass" template
4. Customize fields:
   - **Subject:** "Welcome to Test Hockey League!"
   - **Title:** "Your Season Pass is Ready!"
   - **Intro Text:** "We're excited to have you join our league."
   - **Body Content:** "Your digital pass includes 20 games..."
   - **Conclusion:** "See you on the ice!"
   - **CTA Text:** "View My Pass"
   - **CTA URL:** "https://minipass.me"
   - **Hero Image:** Upload test image (PNG, auto-resized)
5. Click "Save Template"

**Log Verification:**
```
Look for:
- "✅ Email template updated: newPass"
- "Hero image uploaded and resized"
- "Template compiled successfully"
- File saved to compiled directory
```

**Expected Result:**
- Browser: Success message
- Template preview updates
- Logs: Template compilation confirmation
- Files: Template saved to `_compiled/` directory

---

### Test 11.2: Send Test Email
**Goal:** Verify test email functionality

**Playwright Actions:**
1. On email template customization page
2. Click "Send Test Email" button
3. Verify email sent to admin email

**Log Verification (CRITICAL):**
```
Look for:
- "✅ Test email sent"
- "Template: newPass"
- "Recipient: [admin email]"
- "✅✅✅ EMAIL SENT SUCCESSFULLY"
```

**Expected Result:**
- Browser: Success toast/message
- Logs: Test email sent confirmation
- Email: Receive test email with customized template

---

### Test 11.3: Reset Template to Default
**Goal:** Test reset functionality

**Playwright Actions:**
1. Click "Reset to Default" button for newPass template
2. Confirm reset

**Log Verification:**
```
Look for:
- "Email template reset to default: newPass"
- Original template restored
```

**Expected Result:**
- Template reverts to original content
- Customizations cleared
- Template still functional

---

## PHASE 12: KPI Dashboard

### Test 12.1: View Activity KPIs
**Goal:** Verify KPI dashboard displays accurate metrics

**Playwright Actions:**
1. Navigate to main dashboard (`/`)
2. View KPI cards for "Test Hockey League" activity:
   - Total Revenue
   - Passports Created
   - Active Passports
   - Pending Signups
   - Payment Status (Paid vs Unpaid)

**Log Verification:**
```
Look for:
- "KPI data calculated for activity: [activity_id]"
- Revenue sum query
- Passport count query
```

**Expected Result:**
- KPI cards display correct numbers:
  - Total Revenue: $1500 ($500 passport + $1000 sponsorship - $300 expense)
  - Passports Created: 1
  - Active Passports: 1
  - Pending Signups: 0 (converted to passport)
  - Paid Passports: 1

---

### Test 12.2: View Financial Summary KPIs
**Goal:** Verify overall financial KPIs

**Playwright Actions:**
1. On dashboard or financial report page
2. View summary KPI cards:
   - Total Revenue
   - Total Expenses
   - Net Income

**Log Verification:**
```
Look for:
- Financial summary calculation
- All income sources aggregated
- All expenses aggregated
```

**Expected Result:**
- Total Revenue: $1500
- Total Expenses: $300
- Net Income: $1200
- Mobile carousel view works (if on mobile)

---

## PHASE 13: Settings Management

### Test 13.1: Update Organization Settings
**Goal:** Update organization name and address in Settings

**Playwright Actions:**
1. Navigate to "Settings" page
2. Find organization settings section
3. Update fields:
   - **ORG_NAME:** "Test Organization - Automated"
   - **ORG_ADDRESS:** "123 Test Street, Test City, QC A1A 1A1"
   - **MAIL_USERNAME:** Keep existing or update
4. Click "Save Settings"

**Log Verification:**
```
Look for:
- "✅ Setting updated: ORG_NAME"
- "✅ Setting updated: ORG_ADDRESS"
- Database update confirmation
```

**Expected Result:**
- Settings saved successfully
- Organization name appears in emails and footer
- All future emails use updated settings

---

### Test 13.2: Database Backup
**Goal:** Create and download database backup

**Playwright Actions:**
1. On Settings page, find "Backup & Restore" section
2. Click "Create Backup" button
3. Wait for backup generation
4. Click "Download Backup" button

**Log Verification:**
```
Look for:
- "✅ Backup created: minipass_backup_YYYYMMDD_HHMMSS.db"
- "Backup file size: [size]"
- File saved to instance/backups/
```

**Expected Result:**
- Browser: Backup download initiated
- File: SQLite database file downloads
- Logs: Backup creation confirmation
- Backup file size > 0 bytes

---

## PHASE 14: Survey System (Professional Tier Feature)

**Note:** Skip this section if testing Starter tier. For Professional/Enterprise tiers, proceed.

### Test 14.1: Create Survey Template
**Goal:** Create reusable survey template

**Playwright Actions:**
1. Navigate to "Surveys" → "Templates"
2. Click "Create Template"
3. Fill template details:
   - **Name:** "Post-Game Feedback"
   - **Description:** "Automated test survey template"
   - **Questions:** Add 3-5 test questions (JSON format)
4. Click "Save Template"

**Log Verification:**
```
Look for:
- "✅ Survey template created: Post-Game Feedback"
- Template ID assigned
```

**Expected Result:**
- Template appears in library
- Template is reusable

---

### Test 14.2: Deploy Survey (3-Click Deployment)
**Goal:** Deploy survey to activity participants

**Playwright Actions:**
1. Navigate to activity detail page
2. Click "Create Survey" OR "Surveys" tab
3. **Click 1:** Select template "Post-Game Feedback"
4. **Click 2:** Customize name/description (optional)
5. **Click 3:** Click "Send Invitations" (select "All participants" or specific passport type)

**Log Verification:**
```
Look for:
- "✅ Survey created from template"
- "Survey ID: [number]"
- "Invitations sent: [count]"
- "✅✅✅ EMAIL SENT SUCCESSFULLY" (for each invitation)
- Email template: "survey_invitation"
```

**Expected Result:**
- Survey created and linked to activity
- Invitation emails sent to participants
- Survey status: "Active"

---

### Test 14.3: Complete Survey Response
**Goal:** Submit survey response as participant

**Playwright Actions:**
1. Get survey link from email or survey detail page
2. Navigate to survey response page (public URL)
3. Fill out survey form
4. Submit response

**Log Verification:**
```
Look for:
- "✅ Survey response recorded"
- Response token created
- IP and user agent captured
```

**Expected Result:**
- Response saved to database
- Survey completion timestamp recorded
- Response appears in survey results dashboard

---

### Test 14.4: Export Survey Results
**Goal:** Download survey responses as CSV

**Playwright Actions:**
1. Navigate to survey detail page
2. Click "Export Results" button

**Log Verification:**
```
Look for:
- "Survey results CSV export"
- "Responses exported: [count]"
```

**Expected Result:**
- CSV downloads: `survey_Post-Game-Feedback_YYYYMMDD.csv`
- Contains all responses with timestamps

---

## PHASE 15: AI Analytics Chatbot (Professional Tier Feature)

**Note:** Skip for Starter tier. For Professional/Enterprise, proceed.

### Test 15.1: AI Chatbot - Basic Query
**Goal:** Ask natural language question and verify response

**Playwright Actions:**
1. Navigate to "AI Analytics" OR `/chatbot`
2. Verify chatbot interface loads (Claude.ai-inspired design)
3. Check AI provider status LED (should be green)
4. Type question: "How many passports have been created?"
5. Submit query

**Log Verification:**
```
Look for:
- "AI chatbot query received"
- "Provider: gemini" (or groq if failover)
- "SQL generated: SELECT COUNT(*) FROM passport..."
- "Query executed successfully"
- "Response sent to user"
- Token usage logged
```

**Expected Result:**
- Browser: Response appears in chat with answer
- SQL query shown (for transparency)
- Answer: "1 passport has been created"
- Response time displayed
- No errors

---

### Test 15.2: AI Chatbot - Complex Query
**Goal:** Test complex natural language to SQL conversion

**Playwright Actions:**
1. Ask: "Show me total revenue by activity this month"
2. Submit query

**Log Verification:**
```
Look for:
- SQL query with GROUP BY and date filtering
- Intent: "aggregation"
- Entity extraction: date range
- Query execution
```

**Expected Result:**
- Structured response with revenue breakdown
- SQL displayed
- Data accurate

---

### Test 15.3: AI Provider Failover
**Goal:** Verify automatic failover from Gemini to Groq

**Playwright Actions:**
1. In chatbot, select "Groq" from provider dropdown
2. Ask same question: "How many passports have been created?"
3. Verify response with different provider

**Log Verification:**
```
Look for:
- "Provider switched to: groq"
- Different model name in logs
- Query still executes successfully
```

**Expected Result:**
- Response received from Groq
- Functionality identical
- Status LED remains green

---

## PHASE 16: Late Payment Email Test

### Test 16.1: Send Late Payment Email
**Goal:** Trigger late payment email for unpaid signup

**Setup:**
1. Create another signup (without converting to passport yet)
2. Leave payment status as "unpaid"

**Playwright Actions:**
1. Navigate to signup detail page (unpaid signup)
2. Click "Send Payment Reminder" OR trigger late payment email
3. Verify email sent

**Log Verification (CRITICAL):**
```
Look for:
- "✅ Late payment email triggered"
- "✅✅✅ EMAIL SENT SUCCESSFULLY"
- Email template: "latePayment"
- Recipient: kdresdell@gmail.com
```

**Expected Result:**
- Browser: Confirmation message
- Logs: Email sent with latePayment template
- Email: Received with payment instructions and amount due

---

## PHASE 17: Multiple Activities & Passport Types

### Test 17.1: Create Second Activity
**Goal:** Test multi-activity functionality

**Playwright Actions:**
1. Create another activity: "Test Yoga Class - Nov 2025"
2. Create passport type for this activity: "Monthly Membership - $100"
3. Verify both activities appear in dashboard

**Log Verification:**
```
Look for:
- Second activity creation
- Activity count: 2
- KPI dashboard includes both activities
```

**Expected Result:**
- Dashboard shows KPIs for both activities
- Activities list displays both
- Financial report can filter by activity

---

## PHASE 18: Edge Cases & Error Handling

### Test 18.1: Duplicate Email Signup
**Goal:** Test duplicate email handling

**Playwright Actions:**
1. Try to create signup with same email (kdresdell@gmail.com) for same activity
2. Verify error handling

**Log Verification:**
```
Look for:
- Duplicate detection logic
- Appropriate error message
```

**Expected Result:**
- User-friendly error message
- Signup prevented OR warning shown

---

### Test 18.2: Invalid Data Entry
**Goal:** Test validation

**Playwright Actions:**
1. Try to create income with negative amount
2. Try to create expense without required fields
3. Verify validation messages

**Log Verification:**
```
Look for:
- Validation errors logged
- No database corruption
```

**Expected Result:**
- Form validation prevents submission
- Clear error messages displayed

---

## PHASE 19: Email Delivery Verification Summary

**Goal:** Verify ALL emails were sent successfully during test run

### Email Count Expected:
1. ✅ Signup email (Test User signup)
2. ✅ newPass email (Signup to passport conversion)
3. ✅ paymentReceived email (Passport marked as paid)
4. ✅ redeemPass email (First redemption)
5. ✅ redeemPass email (Second redemption)
6. ✅ redeemPass email (Third redemption)
7. ✅ Test email (Email template test)
8. ✅ latePayment email (Payment reminder)
9. ✅ survey_invitation email (If Professional tier tested)

**Total Expected:** 8-9 emails sent to `kdresdell@gmail.com`

### Verification Method:
**Check Flask logs for all:**
```
✅✅✅ EMAIL SENT SUCCESSFULLY
```

**Count instances and verify total matches expected count.**

---

## PHASE 20: Data Integrity Checks

### Test 20.1: Database Consistency
**Goal:** Verify database relationships are intact

**Actions:**
1. Query database directly (if needed) OR
2. Check related records through UI:
   - Activity → Passport Types → Signups → Passports
   - Income/Expense → Activity linkage
   - Payment → Passport linkage

**Log Verification:**
```
Look for:
- No foreign key errors
- All relationships valid
```

**Expected Result:**
- All records properly linked
- No orphaned records
- Referential integrity maintained

---

### Test 20.2: File Storage Verification
**Goal:** Verify uploaded files are stored correctly

**Actions:**
1. Check `instance/receipts/` directory
2. Verify receipt files exist and are accessible
3. Check logo/hero image storage

**Expected Result:**
- All uploaded files present
- File permissions correct
- No corrupted files

---

## PHASE 21: Performance & Load

### Test 21.1: Dashboard Load Time
**Goal:** Verify dashboard loads within performance targets

**Playwright Actions:**
1. Navigate to dashboard
2. Measure page load time

**Log Verification:**
```
Look for:
- Database query times < 100ms
- Total page load < 500ms
```

**Expected Result:**
- Dashboard loads in < 2 seconds
- All KPIs render correctly
- No timeout errors

---

### Test 21.2: Large Data Export
**Goal:** Test CSV export with multiple records

**Actions:**
1. Export financial report (all records)
2. Measure export time

**Expected Result:**
- Export completes successfully
- File size appropriate
- No memory errors

---

## TEST EXECUTION CHECKLIST

### Before Starting Tests:
- [ ] Flask server running on localhost:5000 (debug mode)
- [ ] Database in clean state (or backed up)
- [ ] Playwright MCP server available
- [ ] Terminal visible for log monitoring
- [ ] Test email kdresdell@gmail.com ready

### During Tests:
- [ ] Monitor Flask logs AFTER EVERY ACTION
- [ ] Record all Activity IDs, Passport IDs, Signup IDs
- [ ] Screenshot failures for debugging
- [ ] Note any warnings in logs
- [ ] Track email count (should match expected)

### After Tests:
- [ ] Verify total email count (8-9 expected)
- [ ] Check database consistency
- [ ] Review all log files for errors
- [ ] Confirm all test records created
- [ ] Validate CSV exports downloaded
- [ ] Test backup/restore if needed

---

## SUCCESS CRITERIA

**All tests MUST pass with:**
1. ✅ All emails sent successfully (verified in logs)
2. ✅ No errors in Flask terminal
3. ✅ All database records created correctly
4. ✅ All CSV exports download and contain correct data
5. ✅ All uploads (receipts, images) stored properly
6. ✅ All KPIs display accurate numbers
7. ✅ All UI elements render correctly (responsive)
8. ✅ All redirects work as expected
9. ✅ All forms validate properly
10. ✅ All integrations function (payment, email, AI)

---

## FAILURE RECOVERY PROCEDURES

### If Email Fails to Send:
1. Check SMTP settings in Settings table
2. Verify email template exists and is compiled
3. Check mail server logs
4. Verify recipient email format
5. Test with different email address

### If Database Error Occurs:
1. Check migration status: `flask db current`
2. Verify table schema matches models
3. Check foreign key relationships
4. Restore from backup if needed

### If Playwright Test Fails:
1. Check element selectors (may have changed)
2. Verify page loaded completely
3. Check for JavaScript errors in browser console
4. Retry action after short wait

### If Flask Server Crashes:
1. Check terminal for traceback
2. Identify error line and function
3. Fix bug and restart server
4. Resume tests from last successful step

---

## NOTES FOR EXECUTION

- **Do not restart Flask server** unless absolutely necessary (already running in debug mode)
- **Use kdresdell@gmail.com** for ALL signups/emails
- **Check logs after EVERY action** - this is critical
- **Record all IDs** (activity, passport, signup) for cross-referencing
- **Screenshot any errors** for debugging
- **Verify email count** at end matches expected (8-9 emails)
- **Test systematically** - complete each phase before moving to next
- **Document failures** with logs, screenshots, and steps to reproduce

---

## ESTIMATED EXECUTION TIME

- **Phase 1-7 (Core Flow):** 30-45 minutes
- **Phase 8-10 (Financial & Reports):** 20-30 minutes
- **Phase 11-13 (Settings & Templates):** 15-20 minutes
- **Phase 14-15 (Professional Features):** 15-20 minutes (if applicable)
- **Phase 16-21 (Edge Cases & Validation):** 20-30 minutes

**Total:** 100-145 minutes (1.5 - 2.5 hours) for complete test suite

---

## END OF TEST PLAN

This comprehensive test plan covers **every feature** mentioned in the PRD, from basic admin functions to advanced AI analytics. Execute systematically, monitor logs after each action, and document all results.

**Remember:** The goal is not just to test features, but to verify that emails are sent, logs confirm success, and the entire user experience works seamlessly from signup to redemption to financial reporting.

Good luck with the testing! 🚀
