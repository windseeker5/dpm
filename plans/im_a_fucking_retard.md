# Email Footer Fix Plan - I'm a fucking retard

## Root Cause Analysis

### Current Problems:
1. **Organization context is being lost** when emails are sent - the `activity` parameter isn't properly passing organization info to `send_email()`
2. **Templates have hardcoded values** instead of using dynamic variables:
   - Support email: hardcoded `support@minipass.me` 
   - Copyright: hardcoded "© 2025 Minipass"
   - URLs missing subdomain prefix

## The Fix Plan

### 1. Fix Organization Context Detection (utils.py)
- Ensure `send_email()` properly receives and uses the `activity` parameter
- Make organization detection more robust with proper fallback to the correct organization from database
- Pass organization ID explicitly in email context

### 2. Update All 6 Email Templates
Update footer in these templates to use dynamic variables:
- `signup/index.html`
- `newPass/index.html`  
- `paymentReceived/index.html`
- `latePayment/index.html`
- `redeemPass/index.html`
- `email_survey_invitation/index.html`

Changes needed in each template footer:
```html
<!-- FROM -->
<a href="mailto:support@minipass.me">support@minipass.me</a>
<!-- TO -->
<a href="mailto:{{ support_email }}">{{ support_email }}</a>

<!-- FROM -->
© 2025 Minipass. Tous droits réservés.
<!-- TO -->
© 2025 {{ organization_name }}. Tous droits réservés.
```

### 3. Fix URL Generation in utils.py
Ensure these variables are properly set with subdomain:
- `support_email` = `support@{subdomain}.minipass.me`
- `unsubscribe_url` = `https://{subdomain}.minipass.me/unsubscribe?email={email}`
- `privacy_url` = `https://{subdomain}.minipass.me/privacy`

### 4. Update Email Sending Functions
- `send_signup_email()` - ensure organization context passed
- `notify_pass_event()` - ensure organization context passed
- Add `support_email` to context variables

### 5. Recompile All Templates
Run the compiler for all 6 templates to apply changes:
```bash
cd templates/email_templates
python compileEmailTemplate.py signup
python compileEmailTemplate.py newPass
python compileEmailTemplate.py paymentReceived
python compileEmailTemplate.py latePayment
python compileEmailTemplate.py redeemPass
python compileEmailTemplate.py email_survey_invitation
```

### 6. Test Each Template
Verify that each email shows:
- Correct organization name (Foundation LHGI)
- Clickable links with correct subdomain (lhgi.minipass.me)
- Proper support email address

## Expected Results
All 6 email templates should have:
1. Organization name: "Foundation LHGI" (from database)
2. Support email: `support@lhgi.minipass.me`
3. Unsubscribe link: `https://lhgi.minipass.me/unsubscribe?email=xxx`
4. Privacy link: `https://lhgi.minipass.me/privacy`
5. Copyright: "© 2025 Foundation LHGI. Tous droits réservés."