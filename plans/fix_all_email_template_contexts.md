# Fix All Email Template Context Issues

## Problem Identified
ALL email templates using `send_email_async()` have missing footer variables in their context, causing broken footers (missing support email, unclickable links).

## Root Cause
The `send_email()` function properly sets footer variables, but only if the context dictionary contains placeholder keys. When contexts don't include these keys, the template variables remain empty.

## Templates Affected
1. ✅ **signup** - FIXED (lines 2089-2094 in utils.py)
2. ❌ **newPass** (paymentReceived, latePayment, redeemPass) - notify_pass_event context (lines 2250-2259)
3. ❌ **email_survey_invitation** - need to check where this is sent from

## Required Fixes

### 1. Fix notify_pass_event Function (utils.py lines 2250-2259)
Add missing context variables:
```python
context={
    "pass_data": pass_data,
    "title": f"{event_type.title()} Confirmation",
    "intro_text": "Your pass has been updated.",
    "conclusion_text": f"Thank you for using {activity.organization.name if activity and activity.organization else 'Foundation LHGI'}!",
    "owner_html": render_template("email_blocks/owner_card_inline.html", pass_data=pass_data),
    "history_html": render_template("email_blocks/history_table_inline.html", history=get_pass_history_data(pass_data.pass_code, fallback_admin_email=admin_email)),
    "activity_name": activity.name if activity else "",
    "qr_code": generate_qr_code_image(pass_data.pass_code).read(),
    # ADD THESE:
    "support_email": "",
    "organization_name": "",
    "organization_address": "",
    "unsubscribe_url": "",
    "privacy_url": "",
},
```

### 2. Find and Fix email_survey_invitation Sender
- Search for where survey invitation emails are sent
- Add same missing context variables

### 3. Copy Working Footer to All Templates
Once context is fixed, ensure all templates have identical footer:
- paymentReceived/index.html
- latePayment/index.html  
- redeemPass/index.html
- email_survey_invitation/index.html

### 4. Recompile All Templates
After footer updates:
```bash
cd templates/email_templates
python compileEmailTemplate.py paymentReceived
python compileEmailTemplate.py latePayment
python compileEmailTemplate.py redeemPass
python compileEmailTemplate.py email_survey_invitation
```

### 5. Testing Plan
Test each email type:
1. Create activity
2. Sign up (signup email)
3. Create passport (newPass email)
4. Mark payment received (paymentReceived email)
5. Mark payment late (latePayment email)
6. Redeem passport (redeemPass email)
7. Send survey invitation (email_survey_invitation)

Verify in each email:
- Support email shows: lhgi@minipass.me
- Organization shows: Foundation LHGI
- Unsubscribe link works: https://lhgi.minipass.me/unsubscribe
- Privacy link works: https://lhgi.minipass.me/privacy

## Files to Modify
1. `/home/kdresdell/Documents/DEV/minipass_env/app/utils.py` (lines 2250-2259)
2. Template footers (if not identical)
3. Find survey invitation email sender

## Success Criteria
All 6 email templates show:
- Correct support email (lhgi@minipass.me)
- Correct organization (Foundation LHGI)
- Working clickable footer links
- Identical footer structure

## Time Estimate
- 30 minutes to implement context fixes
- 15 minutes to copy footer to remaining templates
- 10 minutes to recompile all templates
- 20 minutes to test all email types
- **Total: ~75 minutes**