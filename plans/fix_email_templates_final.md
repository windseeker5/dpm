# Final Email Template Fix Plan

## Current Critical Issues (From Testing)

### newPass Template Problems:
1. **Missing hero image** - not displaying at all
2. **Wrong text color** - showing pink/red text instead of grey (#6b7280)
3. **Footer completely broken:**
   - Organization name shows "Minipass" instead of "Fondation LHGI"
   - Support email shows support@minipass.me instead of support@lhgi.minipass.me
   - Unsubscribe link: https://minipass.me/unsubscribe instead of https://lhgi.minipass.me/unsubscribe
   - Privacy link: https://minipass.me/privacy instead of https://lhgi.minipass.me/privacy
   - Random "..." (three dots) appearing in footer
   - Text color is pink/red instead of grey

### signup Template Problems:
1. **Wrong text color** - showing pink/red text instead of grey
2. **Footer has same issues as newPass**

## The Fix Strategy

### Step 1: Fix newPass Template COMPLETELY
Fix in `/home/kdresdell/Documents/DEV/minipass_env/app/templates/email_templates/newPass/index.html`:

1. **Fix hero image issue**
   - Check why hero image is not loading
   - Ensure proper image reference

2. **Fix all text colors**
   - Replace all pink/red colors with proper grey (#6b7280)
   - Ensure inline styles use correct color values

3. **Fix footer completely:**
   ```html
   <!-- Correct footer colors and structure -->
   <p style="color:#6b7280;">Pour toute question, contactez-nous à 
     <a href="mailto:{{ support_email }}" style="color:#3b82f6;">{{ support_email }}</a>
   </p>
   <p style="color:#6b7280;">
     {{ organization_name }} • {{ organization_address }}
   </p>
   <p style="color:#6b7280;">
     <a href="{{ unsubscribe_url }}" style="color:#3b82f6;">Se désabonner</a> | 
     <a href="{{ privacy_url }}" style="color:#3b82f6;">Politique de confidentialité</a>
   </p>
   <p style="color:#94a3b8;">
     Vous recevez ce courriel car vous êtes inscrit à {{ activity_name }}
   </p>
   <p style="color:#94a3b8;">
     © 2025 {{ organization_name }}. Tous droits réservés.
   </p>
   ```

4. **Remove the "..." dots issue**
   - Find and remove any stray ellipsis in the template

### Step 2: Manual Compilation
- User will manually run: `python compileEmailTemplate.py newPass`

### Step 3: Test with New Activity
- Create new activity
- Create new passport
- Verify email shows:
  - Correct grey colors
  - "Fondation LHGI" as organization
  - support@lhgi.minipass.me
  - Correct subdomain links
  - No random dots

### Step 4: Copy Fixed Footer to ALL Templates
Once newPass is confirmed working, copy the exact footer HTML to:
- `signup/index.html`
- `paymentReceived/index.html`
- `latePayment/index.html`
- `redeemPass/index.html`
- `email_survey_invitation/index.html`

### Step 5: Fix Text Colors in All Templates
Ensure all templates use grey (#6b7280) not pink/red for body text

### Step 6: Compile All Templates
```bash
cd /home/kdresdell/Documents/DEV/minipass_env/app/templates/email_templates
python compileEmailTemplate.py signup
python compileEmailTemplate.py newPass
python compileEmailTemplate.py paymentReceived
python compileEmailTemplate.py latePayment
python compileEmailTemplate.py redeemPass
python compileEmailTemplate.py email_survey_invitation
```

## Expected Final Result
All 6 email templates will have:
1. **Correct grey text colors** (#6b7280 for body, #94a3b8 for light text)
2. **Organization name:** "Fondation LHGI"
3. **Support email:** support@lhgi.minipass.me
4. **Correct subdomain links:** https://lhgi.minipass.me/...
5. **No random dots or broken formatting**
6. **Identical, working footers across all templates**

## Why Previous Attempts Failed
1. Organization context not being passed correctly to email sending functions
2. Hardcoded values in templates instead of using variables
3. Color styles being overridden somewhere in the email rendering
4. Inconsistent footer HTML across templates

## This Time Will Work Because:
1. We fix ONE template completely (newPass)
2. Test it thoroughly before proceeding
3. Copy the working footer exactly to all other templates
4. Ensure consistent color styling throughout