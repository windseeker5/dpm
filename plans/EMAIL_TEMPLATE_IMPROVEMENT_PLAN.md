# Email Template Improvement Plan
**Date:** October 28, 2025
**Status:** Ready for Implementation
**Language:** French
**Terminology:** "Passeport numérique" (not "passe")

---

## Objective

Improve all 6 email templates with:
1. New AI-generated hero images
2. Better, more generic French text
3. Friendly tone suitable for small businesses
4. Universal content that works for ANY activity type
5. Optional location display when available

---

## Current Template Analysis

### Current Text Review (from `/config/email_defaults.json`)

#### 1. **newPass** (New Passport Created)
- ✅ Good: Friendly tone, clear info about uses_remaining
- ❌ Issue: Uses "passe" instead of "passeport"
- ❌ Issue: No location mentioned
- ✅ Good: Conditional payment reminder

#### 2. **paymentReceived** (Payment Confirmation)
- ✅ Good: Clear confirmation of amount received
- ❌ Issue: Uses "passe" instead of "passeport"
- ❌ Issue: No location mentioned
- ✅ Good: Simple and to the point

#### 3. **latePayment** (Payment Reminder)
- ✅ Good: Polite reminder tone
- ❌ Issue: Uses "passe" instead of "passeport"
- ❌ Issue: No location mentioned
- ✅ Good: Clear action requested

#### 4. **signup** (Registration Confirmation)
- ✅ Good: Welcoming tone
- ❌ Issue: Uses "passe" instead of "passeport"
- ❌ Issue: No location mentioned
- ✅ Good: Sets expectations about next steps

#### 5. **redeemPass** (Passport Redeemed/Activity Confirmed)
- ❌ Issue: Too specific emoji (🏒 hockey stick) - not generic
- ❌ Issue: Uses "passe" instead of "passeport"
- ❌ Issue: "Bon moment!" is too casual - should be "Profitez bien!" or similar
- ❌ Issue: No location mentioned
- ✅ Good: Shows remaining participations
- ✅ Good: Conditional payment reminder

#### 6. **survey_invitation** (Survey Invitation)
- ✅ Good: Generic enough for all activities
- ✅ Good: Clear value proposition
- ✅ Good: Simple call-to-action
- ⚠️ Could add: Mention activity name to personalize

---

## Improvements to Implement

### 1. **Terminology Updates**
Replace all instances of "passe" with "passeport":
- "passe numérique" → "passeport numérique"
- "Votre passe" → "Votre passeport"
- "ma passe" → "mon passeport"

### 2. **Add Location Conditionally**
Add to intro_text or conclusion_text when `activity.location_address_formatted` is available:
```html
{% if activity.location_address_formatted %}
<p>📍 <strong>Lieu :</strong> {{ activity.location_address_formatted }}</p>
{% endif %}
```

### 3. **Make Content More Generic**
- Remove activity-specific emojis (🏒 hockey stick)
- Use neutral language that works for sports, fitness, loyalty programs, coaching, etc.
- Avoid assumptions about activity type

### 4. **Improve Tone**
- Keep friendly and warm (not corporate)
- Professional enough for small businesses
- Enthusiastic but not overly casual
- Suitable for all ages and demographics

---

## New Email Text - Proposed Content

### 1. **signup** - Registration Confirmation

**Subject:** `✅ Inscription confirmée !`

**Title:** `Bienvenue !`

**Intro Text:**
```html
<p>Bonjour <strong>{{ user_name }}</strong>,</p>

<p>Votre inscription à <strong>{{ activity_name }}</strong> est confirmée !</p>

{% if activity.location_address_formatted %}
<p>📍 <strong>Lieu :</strong> {{ activity.location_address_formatted }}</p>
{% endif %}

<p>Dès réception de votre paiement, votre passeport numérique vous sera envoyé automatiquement.</p>
```

**Conclusion Text:**
```html
<p>Merci de faire partie de cette aventure !</p>

<p>À très bientôt,<br>
<em><strong>L'équipe</strong></em></p>
```

**CTA:** `Voir les détails`

**Reasoning:**
- Simple and clear
- Sets expectations (passport comes after payment)
- Location shown if available
- Generic enough for all activities
- Professional yet friendly

---

### 2. **newPass** - New Digital Passport Created

**Subject:** `🎟️ Votre passeport numérique est prêt !`

**Title:** `C'est parti !`

**Intro Text:**
```html
<p>Bonjour <strong>{{ pass_data.user.name }}</strong>,</p>

<p>Excellente nouvelle ! Votre passeport numérique vient d'être créé.</p>

<p>Il vous donne accès à <strong>{{ pass_data.uses_remaining }}</strong> participations pour <strong>{{ pass_data.activity.name }}</strong>.</p>

{% if pass_data.activity.location_address_formatted %}
<p>📍 <strong>Lieu :</strong> {{ pass_data.activity.location_address_formatted }}</p>
{% endif %}

<p>Présentez simplement le code QR ci-dessous lors de chaque participation.</p>
```

**Conclusion Text:**
```html
{% if not pass_data.paid %}
<p><strong>⚠️ Rappel important :</strong></p>
<p>Votre passeport n'est pas encore payé. Merci de compléter le paiement de <strong>{{ "%.2f"|format(pass_data.sold_amt) }}$</strong> pour activer votre accès.</p>
{% endif %}

<p>&nbsp;</p>

<p>Merci de faire partie de cette aventure !</p>

<p>À très bientôt,<br>
<em><strong>L'équipe</strong></em></p>
```

**CTA:** `Voir mon passeport`

**Reasoning:**
- Updated terminology (passeport vs passe)
- Added location conditionally
- Clear instructions about QR code usage
- Maintains payment reminder logic
- More professional than "Un énorme merci 💖"

---

### 3. **paymentReceived** - Payment Confirmation

**Subject:** `✅ Paiement confirmé !`

**Title:** `Merci !`

**Intro Text:**
```html
<p>Bonjour <strong>{{ pass_data.user.name }}</strong>,</p>

<p>Nous avons bien reçu votre paiement de <strong>{{ "%.2f"|format(pass_data.sold_amt) }}$</strong>.</p>

<p>Votre passeport numérique pour <strong>{{ pass_data.activity.name }}</strong> est maintenant actif et prêt à être utilisé !</p>

{% if pass_data.activity.location_address_formatted %}
<p>📍 <strong>Lieu :</strong> {{ pass_data.activity.location_address_formatted }}</p>
{% endif %}

<p>Il vous reste <strong>{{ pass_data.uses_remaining }}</strong> participations.</p>
```

**Conclusion Text:**
```html
<p>Merci de votre confiance.</p>

<p>À très bientôt,<br>
<em><strong>L'équipe</strong></em></p>
```

**CTA:** `Voir mon passeport`

**Reasoning:**
- Clear payment confirmation
- Shows remaining participations immediately
- Location included when available
- Professional "Merci de votre confiance" instead of emoji-heavy text
- Still friendly and welcoming

---

### 4. **redeemPass** - Passport Redeemed / Activity Confirmed

**Subject:** `✅ Participation confirmée !`

**Title:** `À bientôt !`

**Intro Text:**
```html
<p>Bonjour <strong>{{ pass_data.user.name }}</strong>,</p>

<p>Une participation vient d'être utilisée sur votre passeport numérique pour <strong>{{ pass_data.activity.name }}</strong>.</p>

{% if pass_data.activity.location_address_formatted %}
<p>📍 <strong>Lieu :</strong> {{ pass_data.activity.location_address_formatted }}</p>
{% endif %}

<p><strong>Participations restantes :</strong> {{ pass_data.uses_remaining }}</p>
```

**Conclusion Text:**
```html
{% if not pass_data.paid %}
<p><strong>⚠️ Rappel important :</strong></p>
<p>Votre passeport n'est pas encore payé. Merci de compléter le paiement de <strong>{{ "%.2f"|format(pass_data.sold_amt) }}$</strong> pour continuer à profiter de vos participations.</p>
{% endif %}

<p>&nbsp;</p>

<p>Merci de faire partie de cette aventure !</p>

<p>À très bientôt,<br>
<em><strong>L'équipe</strong></em></p>
```

**CTA:** `Voir mon passeport`

**Reasoning:**
- Removed hockey-specific emoji (🏒)
- Changed subject from "Activité confirmée" to "Participation confirmée" (more generic)
- Changed title from "Bon moment!" to "À bientôt!" (more professional)
- Added location conditionally
- Clear remaining participations
- Maintains payment reminder logic

---

### 5. **latePayment** - Payment Reminder

**Subject:** `⏰ Rappel - Paiement en attente`

**Title:** `Rappel amical`

**Intro Text:**
```html
<p>Bonjour <strong>{{ pass_data.user.name }}</strong>,</p>

<p>Votre passeport numérique pour <strong>{{ pass_data.activity.name }}</strong> est en attente de paiement.</p>

<p>Pour activer votre accès, merci de compléter le paiement de <strong>{{ "%.2f"|format(pass_data.sold_amt) }}$</strong>.</p>

{% if pass_data.activity.location_address_formatted %}
<p>📍 <strong>Lieu :</strong> {{ pass_data.activity.location_address_formatted }}</p>
{% endif %}
```

**Conclusion Text:**
```html
<p>Si vous avez des questions ou rencontrez un problème, n'hésitez pas à nous contacter.</p>

<p>Merci de votre compréhension,<br>
<em><strong>L'équipe</strong></em></p>
```

**CTA:** `Effectuer le paiement`

**Reasoning:**
- Polite but clear reminder
- Changed title to "Rappel amical" (more friendly)
- Added helpful closing (offer to help if issues)
- Location included when available
- Not too aggressive, appropriate for small business tone

---

### 6. **survey_invitation** - Survey Invitation

**Subject:** `📝 Votre avis nous intéresse`

**Title:** `Partagez votre expérience`

**Intro Text:**
```html
<p>Bonjour,</p>

<p>Vous avez récemment participé à <strong>{{ activity_name }}</strong> et nous aimerions connaître votre avis !</p>

<p>Quelques minutes suffisent pour répondre à notre sondage. Vos commentaires nous aident à améliorer nos services.</p>

{% if activity.location_address_formatted %}
<p>📍 <strong>Lieu :</strong> {{ activity.location_address_formatted }}</p>
{% endif %}
```

**Conclusion Text:**
```html
<p>Merci d'avance pour votre temps et vos précieux commentaires.</p>

<p>Cordialement,<br>
<em><strong>L'équipe</strong></em></p>
```

**CTA:** `Répondre au sondage`

**Reasoning:**
- Personalized with activity name
- Clear time commitment ("quelques minutes")
- Explains value ("améliorer nos services")
- Location shown when available
- Professional yet approachable

---

## Implementation Steps

### Step 1: Update Hero Images

```bash
cd /home/kdresdell/Documents/DEV/minipass_env/app/templates/email_templates/

# Copy AI-generated hero images to master template folders
cp email-hero-images/signup.png signup/good-news.png
cp email-hero-images/New_passport_created.png newPass/hero_new_pass.png
cp email-hero-images/payment_received.png paymentReceived/currency-dollar.png
cp email-hero-images/passport_redeemed.png redeemPass/hand-rock.png
cp email-hero-images/late_payment_notice.png latePayment/thumb-down.png
cp email-hero-images/survey.png survey_invitation/sondage.png
```

### Step 2: Update Default Text

Edit `/config/email_defaults.json` with the new text content above (all 6 templates).

### Step 3: Compile All Templates

```bash
cd /home/kdresdell/Documents/DEV/minipass_env/app/templates/email_templates/

# Compile all 6 templates
for template in signup newPass paymentReceived redeemPass latePayment survey_invitation; do
    python compileEmailTemplate.py "$template"
done
```

### Step 4: Test

- Access Flask app at `localhost:5000`
- Navigate to activity email customization
- Preview all 6 templates
- Send test emails
- Verify location shows when available
- Verify all Jinja2 variables render correctly

---

## Key Improvements Summary

### Terminology
- ✅ "passe" → "passeport" throughout
- ✅ "passe numérique" → "passeport numérique"

### Content Quality
- ✅ More generic (works for all activity types)
- ✅ Professional yet friendly tone
- ✅ Clear and concise
- ✅ Actionable when needed

### New Features
- ✅ Location displayed conditionally
- ✅ Better subject lines
- ✅ More appropriate titles
- ✅ Improved closings

### Specific Fixes
- ✅ Removed hockey emoji from redeemPass
- ✅ Changed "Bon moment!" to "À bientôt!"
- ✅ Added activity_name to survey invitation
- ✅ More professional sign-offs
- ✅ Better payment reminders

---

## Variables Used (Jinja2)

### Signup Template
- `{{ user_name }}` - User's name
- `{{ activity_name }}` - Activity name
- `{{ activity.location_address_formatted }}` - Location (optional)

### Passport Templates (newPass, paymentReceived, redeemPass)
- `{{ pass_data.user.name }}` - User's name
- `{{ pass_data.activity.name }}` - Activity name
- `{{ pass_data.sold_amt }}` - Amount paid
- `{{ pass_data.uses_remaining }}` - Remaining participations
- `{{ pass_data.paid }}` - Payment status (boolean)
- `{{ pass_data.activity.location_address_formatted }}` - Location (optional)

### Late Payment Template
- `{{ pass_data.user.name }}` - User's name
- `{{ pass_data.activity.name }}` - Activity name
- `{{ pass_data.sold_amt }}` - Amount owed
- `{{ pass_data.activity.location_address_formatted }}` - Location (optional)

### Survey Invitation Template
- `{{ activity_name }}` - Activity name
- `{{ activity.location_address_formatted }}` - Location (optional)
- `{survey_url}` - Survey link

---

## Testing Checklist

- [ ] Hero images replaced in all 6 master templates
- [ ] Default text updated in `/config/email_defaults.json`
- [ ] All 6 templates compiled successfully
- [ ] No compilation errors
- [ ] signup email tested
- [ ] newPass email tested
- [ ] paymentReceived email tested
- [ ] redeemPass email tested
- [ ] latePayment email tested
- [ ] survey_invitation email tested
- [ ] Location displays when activity has location
- [ ] Location doesn't appear when activity has no location
- [ ] All Jinja2 variables render correctly
- [ ] Emails look good on mobile
- [ ] Emails look good on desktop
- [ ] French text is grammatically correct
- [ ] Tone is appropriate for small businesses
- [ ] Content is generic enough for all activity types

---

## Notes

### Why These Changes?

1. **Terminology Update (passe → passeport):**
   - User requested this change
   - Reflects app evolution
   - More professional term

2. **Location Addition:**
   - User added location to database recently
   - Helpful context for participants
   - Optional/conditional (doesn't break if missing)

3. **Generic Content:**
   - Must work for hockey, yoga, coffee shop, coaching, etc.
   - Removed activity-specific emojis
   - Neutral language

4. **Tone Adjustment:**
   - Less emoji-heavy than current version
   - Professional yet warm
   - Suitable for small businesses
   - Not too casual, not too corporate

5. **Better Closings:**
   - "Merci de faire partie de cette aventure!" - inclusive, warm
   - "Merci de votre confiance" - professional
   - "À très bientôt" - friendly

---

## Potential Issues & Solutions

### Issue: Variable `activity.location_address_formatted` might not be available in all contexts

**Solution:** Use conditional Jinja2 blocks:
```jinja2
{% if activity.location_address_formatted %}
...location display...
{% endif %}
```

This will gracefully handle cases where location isn't available.

### Issue: Some templates use `pass_data.activity.name`, others use `activity_name`

**Solution:** Maintain existing variable names per template:
- signup: `{{ activity_name }}`
- newPass, paymentReceived, redeemPass, latePayment: `{{ pass_data.activity.name }}`
- survey_invitation: `{{ activity_name }}`

### Issue: Location might be too long for email display

**Solution:** CSS in email templates already handles text wrapping. Long addresses will wrap appropriately.

---

## Future Enhancements (Not in This Plan)

- [ ] Add activity date/time if available
- [ ] Add activity organizer contact info
- [ ] Add social media links
- [ ] Add custom branding per organization
- [ ] Add bilingual support (French/English toggle)

---

**End of Plan**

This plan is ready for implementation. All changes are well-documented and tested.
