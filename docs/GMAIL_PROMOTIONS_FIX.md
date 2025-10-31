# Gmail Promotions Folder Fix

**Date**: October 30, 2025
**Issue**: Payment and redemption confirmation emails going to Gmail Promotions folder instead of Primary inbox

## Problem Summary

Users reported that transactional emails (payment confirmations, passport redemptions) were being filtered into Gmail's Promotions folder, which reduced visibility and engagement.

## Root Causes Identified

1. **Emojis in Subject Lines** - Strong promotion signal (✅, 🎟️, 👏, 💚)
2. **Casual Marketing Language** - Subjects like "Youpi !", "C'est parti !", "Excellente participation !"
3. **Large Hero Images** - 200px decorative images increased image-to-text ratio
4. **Low Text Content** - Short conclusion text made emails look promotional

## Solution Implemented

### 1. Reduced Hero Image Size ✅
**Changed**: 200px → 90px in all templates

**Files Modified**:
- `templates/email_templates/paymentReceived_original/index.html`
- `templates/email_templates/newPass_original/index.html`
- `templates/email_templates/redeemPass_original/index.html`
- `templates/email_templates/signup_original/index.html`
- `templates/email_templates/latePayment_original/index.html`
- `templates/email_templates/survey_invitation_original/index.html`

**Impact**: Lower image-to-text ratio signals transactional email

### 2. Removed ALL Emojis from Subject Lines ✅

**Before** → **After**:
- `✅ Paiement confirmé !` → `Confirmation de paiement`
- `🎟️ Votre passeport numérique est prêt !` → `Votre passeport numérique`
- `✅ Participation confirmée !` → `Confirmation de participation`
- `✅ Inscription confirmée !` → `Confirmation d'inscription`
- `⏰ Rappel - Paiement en attente` → `Rappel de paiement en attente`
- `📝 Votre avis nous intéresse` → `Votre avis nous intéresse`

**Impact**: Subjects look professional and transactional

### 3. Simplified Email Titles ✅

**Before** → **After**:
- `Youpi ! Votre passeport est prêt ! 🎟️` → `Votre passeport numérique est disponible`
- `C'est confirmé, merci ! 💚` → `Paiement confirmé`
- `Excellente participation, merci ! 👏` → `Participation enregistrée`
- `C'est parti, bienvenue à bord ! 🎉` → `Inscription confirmée`

**Impact**: Professional tone matches transactional nature

### 4. Enhanced Conclusion Text ✅

Added 2-3 more sentences with helpful information and support contact details.

**Example - Payment Received**:

**Before**:
```
Merci de votre confiance.
À très bientôt,
L'équipe
```

**After**:
```
Merci de votre confiance. Votre passeport est maintenant actif
et vous pouvez commencer à l'utiliser dès aujourd'hui.

Si vous avez des questions ou besoin d'assistance, n'hésitez
pas à nous contacter directement. Nous sommes là pour vous aider.

À très bientôt,
L'équipe
```

**Impact**: Better text-to-image ratio, more helpful for users

### 5. Kept Functional Emojis ✅

**Removed**: 👏, 💚, 🎉 (decorative)
**Kept**: 📍 (location indicator - functional information)

## Technical Implementation

### Step 1: Updated Source Templates
Modified all 6 `_original/index.html` files to reduce hero image width from 200px to 90px.

### Step 2: Recompiled Templates
Ran compilation script for all 6 templates:
```bash
cd templates/email_templates
python compileEmailTemplate.py signup
python compileEmailTemplate.py newPass
python compileEmailTemplate.py paymentReceived
python compileEmailTemplate.py latePayment
python compileEmailTemplate.py redeemPass
python compileEmailTemplate.py survey_invitation
```

All compiled successfully with new 90px hero images embedded.

### Step 3: Updated Database
Updated `activity.email_templates` JSON for activity #4 with:
- New subject lines (no emojis)
- Simplified titles
- Enhanced conclusion text

Script: `update_email_templates.py`

## Expected Results

**Primary Inbox** (Desired):
- ✅ Payment confirmations
- ✅ Passport created notifications
- ✅ Redemption confirmations
- ✅ Signup confirmations

**Promotions Folder** (Acceptable):
- Survey invitations (promotional by nature)

## Testing Instructions

1. Create new signup for activity #4
2. Convert signup to passport
3. Mark passport as paid
4. Redeem passport
5. Check Gmail inbox placement for each email

## Best Practices Going Forward

### DO:
✅ Use plain, professional subject lines
✅ Keep titles transactional and factual
✅ Add helpful information in email body
✅ Keep hero images small (80-100px max)
✅ Use functional emojis sparingly (📍 for location)

### DON'T:
❌ Add emojis to subject lines
❌ Use exclamation marks excessively
❌ Use casual/excited language ("Youpi!", "C'est parti!")
❌ Use large decorative images (200px+)
❌ Use decorative emojis (👏, 💚, 🎉)

## Files Modified

**Original Templates** (6 files):
- All `_original/index.html` files (hero image width: 200px → 90px)

**Compiled Templates** (6 files - auto-generated):
- All `_compiled/index.html` files (via compilation script)

**Database**:
- Activity #4: `email_templates` JSON field

**Scripts**:
- `update_email_templates.py` (created for one-time database update)

## Gmail Filtering Algorithm Signals

**Promotion Signals** (AVOID):
- Emojis in subject lines
- Multiple exclamation marks
- Marketing language ("Amazing!", "Don't miss!")
- Large images
- Low text-to-image ratio
- Promotional CTAs

**Transactional Signals** (USE):
- Plain subject lines
- Professional language
- Order/payment references
- Small/minimal images
- High text-to-image ratio
- Functional content

## Notes

- Hero images are still present (just smaller) to maintain visual appeal
- Text-to-image ratio significantly improved
- Professional tone maintained while keeping friendly voice
- Location emoji (📍) retained as it provides functional information
- All new Minipass activities will get these improved templates via `_original` folders

---

**Status**: ✅ Completed
**Next**: Test with real signup/payment flow and monitor inbox placement
