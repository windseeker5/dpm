# Quick Preview Test - Survey Email Template Fix ✅

**Status**: READY TO TEST
**Date**: 2025-10-16 20:20

---

## 🎯 WHAT TO DO (Takes 30 seconds)

### Step 1: Go to Email Templates
1. Open browser
2. Navigate to: **http://localhost:5000/activity/1/email-templates**
3. Login if needed (admin account)

### Step 2: Open Survey Invitation Template
1. Find the **"Survey Invitation"** card (purple button icon 📝)
2. Click the **"Customize"** button (pencil icon)
3. Modal opens with your saved customizations

### Step 3: Click Preview
1. In the modal, click **"Preview Changes"** button (👁️ eye icon)
2. A new tab opens with the email preview

---

## ✅ WHAT YOU SHOULD SEE

### In the Preview (New Tab):

**✅ Title**: "Partagez votre expérience" (YOUR French title - NOT "We'd Love Your Feedback!")

**✅ Intro Text**:
```
Bonjour,

Nous aimerions connaître votre expérience récente avec nous!
Cela ne prendra que quelques minutes et nous aidera à améliorer nos services.
```

**✅ Survey Info Card**:
- Activity: Hockey du midi LHGI - 2025 / 2026
- Survey: Post-Activity Feedback Survey
- "⏱️ Seulement 5 questions rapides"

**✅ Button**: Purple gradient "📝 Répondre au sondage"

**✅ Conclusion Text**:
```
Merci de prendre le temps de partager vos commentaires.
Votre opinion compte beaucoup pour nous!
```

**✅ Footer**: French legal text with organization name

**✅ Design**: Professional Tabler.io layout (clean white card, proper spacing)

---

## ❌ WHAT YOU SHOULD **NOT** SEE

If you see any of these, the fix didn't work:

- ❌ "We'd Love Your Feedback!" (English title)
- ❌ "Thank you for participating in our activity..." (English intro)
- ❌ Blue gradient header
- ❌ "Thank you for helping us create better experiences!" (English conclusion)
- ❌ Any hardcoded English text

---

## 🐛 IF IT DOESN'T WORK

### Problem 1: Preview Shows Old Blue Template

**Cause**: Preview route not working or template not found

**Check**:
1. Open browser console (F12)
2. Look for errors when clicking "Preview Changes"
3. Check if request went to `/activity/1/email-preview-live`

**Fix**:
- Flask server might need restart (Ctrl+C, then restart)
- Check Flask console for error messages

### Problem 2: Preview Shows English Text

**Cause**: Database doesn't have your customizations

**Check**:
```bash
sqlite3 instance/minipass.db "SELECT email_templates FROM activity WHERE id=1;" | python -m json.tool | grep -A 20 survey_invitation
```

**Expected**: Should show your French text

**Fix**:
- Re-save your customizations through the UI
- Make sure "Save Changes" button was clicked

### Problem 3: Preview Opens But Looks Broken

**Cause**: Template rendering error

**Check**:
- Preview tab should show error message with details
- Check Flask console logs

**Fix**:
- Check template path: `templates/email_templates/survey_invitation_compiled/index.html`
- Verify file exists and has Jinja variables

---

## 🎉 IF IT WORKS

**Next Steps**:

1. **Test actual email send**:
   - Go to http://localhost:5000/surveys
   - Send a survey invitation
   - Check inbox for French customized email

2. **Test editing**:
   - Change title to "TEST TITLE"
   - Click "Preview Changes"
   - Should see "TEST TITLE" immediately (without saving)

3. **Test saving**:
   - Change something
   - Click "Save Changes"
   - Click "Preview Changes" again
   - Should see saved changes

---

## 📋 VERIFICATION CHECKLIST

After viewing preview, check these items:

- [ ] Preview opened in new tab (not error page)
- [ ] Title is in French ("Partagez votre expérience")
- [ ] Intro text is in French (mentions "expérience récente")
- [ ] Conclusion text is in French (mentions "Merci de prendre")
- [ ] Survey info card shows activity name correctly
- [ ] Button text is French ("Répondre au sondage")
- [ ] Footer is in French
- [ ] Design looks professional (Tabler.io style)
- [ ] NO English text appears anywhere
- [ ] NO blue gradient header (old template)

**If all items checked**: ✅ **THE FIX WORKS!**

---

## 🔧 TECHNICAL DETAILS

### What Happens When You Click Preview:

1. JavaScript collects form data (title, intro_text, conclusion_text)
2. Sends POST request to `/activity/1/email-preview-live`
3. Backend creates context with your form values:
   ```python
   context = {
       'title': 'Partagez votre expérience',
       'intro_text': '<p>Nous aimerions connaître...</p>',
       'conclusion_text': '<p>Merci de prendre...</p>',
       'survey_url': 'https://minipass.me/survey/preview',
       'activity_name': 'Hockey du midi LHGI - 2025 / 2026',
       'question_count': 5,
       ...
   }
   ```
4. Renders `survey_invitation_compiled/index.html` with context
5. Jinja replaces variables: `{{ title }}` → "Partagez votre expérience"
6. Returns HTML to browser
7. Browser opens in new tab

### Key Files Involved:

- **Frontend**: `templates/email_template_customization.html` (line 613)
- **Backend**: `app.py` (line 7698 - new route added!)
- **Template**: `templates/email_templates/survey_invitation_compiled/index.html`
- **Database**: `activity.email_templates['survey_invitation']`

---

## 📝 ADDED IN THIS FINAL UPDATE

**New Route**: `/activity/<id>/email-preview-live` (app.py lines 7698-7758)

This route was missing, which is why preview wasn't working before. Now it:
- Takes form data from the modal
- Renders the compiled template with your customizations
- Returns HTML for preview in new tab
- Works WITHOUT saving (live preview)

---

**Ready to test?** Go to http://localhost:5000/activity/1/email-templates and click Preview! 🚀
