# Email Payment Bot Enhancement Plan

## User's Original Request
Create a redesigned, user-friendly, mobile-friendly email parser payment section with the following requirements:

## Key Requirements

### 1. Core Functionality to Preserve
- **Existing bot runs every 30 minutes** via BackgroundScheduler (NOT 15 minutes as initially misunderstood)
- **Keep all existing functionality intact** - the bot already works, just needs better UI
- **All business logic in Flask/Python** (app.py) - minimal JavaScript only for UI interactions
- **Maintain consistent styling** with existing Tabler.io design - no fancy animations or custom colors

### 2. UI/UX Requirements

#### Main Configuration Card
- **Toggle switch** for auto-validation with clear explanation
- **Display payment email address prominently**: lhgi@minipass.me (or configurable)
- **Configurable fields**:
  - Sender email pattern (e.g., notify@interac.ca)
  - Subject line pattern
  - Fuzzy match threshold with slider (default 85%)
  - Gmail label for processed emails
  
#### Test Payment Feature
- **REAL email sending** - not just triggering validation
- User can craft the email with:
  - From address field
  - Subject field
  - Recipient name field
  - Amount field
- Sends actual test email to lhgi@minipass.me
- Button: "Send Test Payment Email"

#### Recent Payment Logs
- Display last 5-10 payment entries
- Show:
  - Timestamp
  - Sender name
  - Amount
  - Match result (matched/unmatched)
  - Confidence score
  
#### Flash Messages
- **5 seconds maximum** display time (not 10)
- For demo/promotional videos
- Shows when new payments are detected
- Clean, non-intrusive design

### 3. Technical Implementation

#### Flask Routes (app.py)
1. `/payment-bot-settings` - Main settings page (GET/POST)
2. `/api/send-test-payment` - Send test email endpoint (POST)
3. `/api/run-payment-bot` - Manually trigger bot (POST)
4. `/api/payment-logs` - Get recent logs (GET)
5. `/api/check-new-payments` - Check for new payments for flash messages (GET)

#### Database Models (already exist)
- `EbankPayment` - Payment logs
- `Passport` - Digital passes
- `Setting` - Configuration values
- `AdminActionLog` - Audit trail

#### Template Structure
- Create/modify `templates/partials/settings_payment_bot.html`
- Integrate with existing `setup.html` page
- Use Tabler.io components exclusively

### 4. Implementation Steps

1. **Review existing code**:
   - Check `utils.py` for `match_gmail_payments_to_passes()` function
   - Understand current bot scheduling in `app.py`
   - Review `EbankPayment` model structure

2. **Create enhanced UI**:
   - Design card-based layout using Tabler.io
   - Add configuration fields with proper form controls
   - Implement test email modal
   - Add payment logs table

3. **Implement Flask endpoints**:
   - All logic in Python
   - Proper error handling
   - Session authentication checks
   - Input validation

4. **Testing requirements**:
   - Unit tests for all endpoints
   - Test email sending functionality
   - Verify payment matching logic
   - Check flash message timing

5. **Security considerations**:
   - Validate all inputs
   - Sanitize email content
   - Rate limiting on test emails
   - Proper authentication checks

## What Went Wrong in Previous Attempt

1. **Didn't use specialized agents** (flask-ui-developer, backend-architect, code-security-reviewer)
2. **Created route that rendered partial template directly** instead of full page
3. **Didn't test properly** before claiming it worked
4. **Started Flask server without permission**
5. **Broke the existing setup page** by not understanding template structure

## Correct Approach

1. **Use flask-ui-developer agent** for UI implementation
2. **Use backend-architect agent** for Flask route design
3. **Use code-security-reviewer agent** for security review
4. **Test everything properly** with Playwright MCP
5. **Never start/restart Flask server** without explicit permission
6. **Integrate with existing setup page** rather than creating separate page

## Files to Modify/Create

- `/templates/partials/settings_payment_bot.html` - Enhanced UI
- `/app.py` - Add API endpoints (lines ~4159-4363)
- `/test/test_payment_bot_endpoints.py` - Unit tests
- Keep existing `/utils.py` functionality unchanged

## Success Criteria

- [ ] Payment bot settings accessible from Settings menu
- [ ] Can send real test emails to payment address
- [ ] Shows recent payment logs
- [ ] Flash messages appear for 5 seconds max
- [ ] Mobile-friendly responsive design
- [ ] All existing bot functionality preserved
- [ ] Runs every 30 minutes as before
- [ ] No custom CSS or animations
- [ ] All logic in Flask/Python