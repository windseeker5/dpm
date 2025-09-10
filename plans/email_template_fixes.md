# Email Template Fixes - Critical Production Issues

## Status: URGENT - Production Down
**Time Constraint:** 20 minutes remaining
**Date:** 2025-01-10

## Current Working State
- ✅ **newPass**: Fully working (no issues)
- ❌ **paymentReceived**: Pink text issue + unwanted activity image
- ❌ **latePayment**: Pink text issue + unwanted activity image  
- ❌ **redeemPass**: Pink text issue (caused by our fix attempt)
- ❌ **signup**: Unknown status
- ❌ **survey_invitation**: Unknown status

## Critical Fixes Required

### 1. Fix Pink Text in redeemPass Template
**File:** `/home/kdresdell/Documents/DEV/minipass_env/app/config/email_defaults.json`
**Lines:** 42 (redeemPass conclusion_text)
**Action:** REVERT to original format without moving `<p>` tags inside conditionals

Original (working):
```json
"conclusion_text": "{% if not pass_data.paid %}<p>Petit rappel amical :</p>\n<p>Votre passe n'a pas encore été payée 🥺</p>\n<p>Merci de faire un virement de <strong>{{ \"%.2f\"|format(pass_data.sold_amt) }}$</strong> afin d'activer votre accès.</p>{% endif %}\n<p>&nbsp;</p>\n<p>💖 Un énorme merci de faire partie de notre belle communauté!</p>\n<p><br>À très bientôt!</p>\n<p><em><strong>— L'équipe</strong></em></p>"
```

### 2. Remove Activity Image Attachments
**File:** `/home/kdresdell/Documents/DEV/minipass_env/app/utils.py`
**Lines:** 157-169 (in get_activity_hero_image function)
**Action:** Comment out or disable the fallback logic that attaches activity images

Code to modify:
```python
# Lines 157-169 - COMMENT OUT THIS BLOCK
if not hero_image_path:
    # Check if there's a cover image
    if activity and activity.cover_image:
        hero_image_path = os.path.join(upload_folder, activity.cover_image)
        if os.path.exists(hero_image_path):
            return hero_image_path
    
    # If no cover image, use the first uploaded image
    if activity and activity.images:
        images = activity.images.split(',')
        if images and images[0]:
            first_image_path = os.path.join(upload_folder, images[0])
            if os.path.exists(first_image_path):
                return first_image_path
```

### 3. Check Other Templates for Pink Text
**Files to check:**
- `config/email_defaults.json` - paymentReceived conclusion_text (line 15)
- `config/email_defaults.json` - latePayment conclusion_text (line 24)

Look for any `{% if %}` blocks with `<p>` tags that might be causing pink text.

## Testing Plan
1. Test with Activity 7 (clean activity with no customizations)
2. User: kdresdell@gmail.com / password: admin123
3. Create passports and trigger each email type
4. Verify:
   - No pink text
   - QR codes display inline (360x360)
   - Logo displays correctly
   - No unwanted activity images attached

## Root Causes Identified
1. **Pink text**: Jinja2 conditionals with unclosed HTML tags
2. **Activity images**: Fallback logic in get_activity_hero_image() attaching images when not needed
3. **CID mismatches**: Fixed by reverting to 'logo' instead of 'logo_image'
4. **QR code sizes**: Fixed by standardizing to 360x360

## Lessons Learned
- Don't move HTML tags inside Jinja2 conditionals - it breaks email rendering
- Test ONE template at a time before moving to next
- The fallback logic for activity images was too aggressive
- CID references must match exactly between template and Python code