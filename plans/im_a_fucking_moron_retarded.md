# THE HERO IMAGE CLUSTERFUCK - COMPLETE DIAGNOSIS AND FIX PLAN

## THE CORE ISSUE IN SIMPLE TERMS

You have THREE different sources of truth for hero images, and they're all fighting each other like drunk morons:

1. **THE COMPILED TEMPLATE** (`/templates/email_templates/newPass_compiled/inline_images.json`)
   - This is YOUR SOURCE OF TRUTH - the one you designed and compiled
   - Contains `hero_new_pass` with the person holding certificate image
   - This is what SHOULD be shown as the default

2. **THE ACTIVITY IMAGE** (surfing/wave image from Activity 5)
   - This is being incorrectly used as the "default" hero
   - Stored as `activity.image_filename`
   - This should NEVER be the default hero for email templates

3. **CUSTOM UPLOADED HERO** (`5_newPass_hero.png`)
   - This is what users upload when they want to override the template default
   - This should take priority over everything else when it exists

## WHAT'S HAPPENING NOW (THE FUCKUP)

### In the Edit Modal:
1. You click edit on "New Pass Created" template
2. The modal calls `get_hero_image()` route
3. That route uses `get_activity_hero_image()` function
4. That stupid function has this priority:
   - FIRST: Check if activity has an image → YES (surfing image) → USE IT ❌ WRONG!
   - Never even looks at the compiled template default

**Result**: Modal shows surfing/wave image instead of your compiled template's person with certificate

### In the Preview:
1. Preview loads the compiled template from `newPass_compiled/index.html`
2. It loads `inline_images.json` which has the CORRECT hero image
3. Shows the person with certificate image ✅ CORRECT!

**Result**: Preview shows different image than edit modal = CONFUSION AND RAGE

## THE BROKEN CODE

The main culprit is in `/home/kdresdell/Documents/DEV/minipass_env/app/utils.py` line 58-102:

```python
def get_activity_hero_image(activity, template_type):
    # BROKEN PRIORITY ORDER:
    # Priority 1: Use activity image as hero (DEFAULT) ← THIS IS WRONG!
    if activity and activity.image_filename:
        # This runs FIRST and returns the surfing image
        # NEVER checks the compiled template default
```

## THE FIX PLAN

### Step 1: Fix `get_activity_hero_image()` function in `utils.py`

**CHANGE THE PRIORITY TO:**
1. **FIRST**: Check for custom uploaded hero (`{activity.id}_{template_type}_hero.png`)
2. **SECOND**: Load the compiled template's default from `inline_images.json`
3. **THIRD**: Only use activity image as LAST RESORT if no template exists

### Step 2: Create new function to load template defaults

```python
def get_template_default_hero(template_type):
    """Load the default hero from compiled template"""
    # Map template types to their compiled folders
    template_map = {
        'newPass': 'newPass_compiled',
        'paymentReceived': 'paymentReceived_compiled',
        # etc...
    }
    
    # Load inline_images.json from compiled template
    json_path = f"templates/email_templates/{template_map[template_type]}/inline_images.json"
    
    # Extract the hero image (e.g., 'hero_new_pass')
    # Return the base64 decoded image data
```

### Step 3: Update the complete flow

1. **get_activity_hero_image()** - Fix priority order
2. **get_hero_image() route** - Ensure it uses fixed function
3. **Email preview functions** - Already working correctly

## EXPECTED BEHAVIOR AFTER FIX

### Scenario 1: Fresh template (no custom upload)
- Edit modal: Shows compiled template default (person with certificate) ✅
- Preview: Shows same compiled template default ✅
- **MATCH!**

### Scenario 2: After uploading custom hero (happy face)
- Edit modal: Shows happy face ✅
- Preview: Shows happy face ✅
- **MATCH!**

### Scenario 3: After reset to default
- Custom hero file gets deleted
- Edit modal: Shows compiled template default ✅
- Preview: Shows compiled template default ✅
- **MATCH!**

## WHY THIS IS HAPPENING

Someone (probably you in a past life when you were less tired) decided that the activity image should be the "default" hero for emails. This was a stupid decision because:

1. Activity images are for the activity dashboard
2. Email templates have their own designed hero images
3. Mixing them creates this exact confusion

## FILES THAT NEED FIXING

1. `/home/kdresdell/Documents/DEV/minipass_env/app/utils.py`
   - Function: `get_activity_hero_image()` (lines 58-102)
   - Need to completely rewrite the priority logic

2. `/home/kdresdell/Documents/DEV/minipass_env/app/app.py`
   - The `get_hero_image()` route (around line 7614)
   - Make sure it uses the fixed logic

## THE SIMPLE TEST

After fixing:
1. Go to Activity 5 → Email Templates
2. Click edit on "New Pass Created"
3. Should see person with certificate (NOT surfing image)
4. Click preview → Should see SAME person with certificate
5. Upload happy face → Save
6. Edit again → Should see happy face
7. Preview → Should see happy face
8. Reset to default
9. Edit → Should see person with certificate again
10. Preview → Should see person with certificate again

## IMPORTANT NOTES

- This affects ALL activities, not just Activity 5
- This affects ALL template types (newPass, paymentReceived, etc.)
- The compiled templates are the SOURCE OF TRUTH
- Activity images should NEVER be default heroes for emails
- Only use activity image if no compiled template exists (edge case)

## TL;DR

**Problem**: `get_activity_hero_image()` uses wrong priority - shows activity image instead of compiled template default

**Solution**: Fix the priority order to:
1. Custom upload
2. Compiled template default
3. Activity image (last resort only)

---

END OF DIAGNOSIS - NOW FIX THIS SHIT PROPERLY