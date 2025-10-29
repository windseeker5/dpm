# Minipass Email Template System - Complete Guide

**Version:** 1.0
**Last Updated:** October 28, 2025
**Purpose:** Comprehensive guide for managing and improving Minipass email templates

---

## Table of Contents

1. [System Overview](#system-overview)
2. [The 6 Master Email Templates](#the-6-master-email-templates)
3. [Directory Structure](#directory-structure)
4. [How to Improve/Modify Email Templates](#how-to-improvemodify-email-templates)
5. [Complete Workflow for Template Improvements](#complete-workflow-for-improving-templates)
6. [Important Notes](#important-notes)
7. [Quick Reference Commands](#quick-reference-commands)
8. [Checklist for Template Improvements](#checklist-for-template-improvements)

---

## System Overview

Your Minipass application has **6 beautiful pre-built email templates** that are sent automatically to users. Each template can be customized per activity, and you've already created AI-designed hero images for all of them.

### Architecture Components

1. **Master Templates** - Source templates you edit (in `templateName/` folders)
2. **Compiled Templates** - Production templates with embedded images (in `templateName_compiled/` folders)
3. **Original Backups** - Pristine compiled versions (in `templateName_original/` folders)
4. **Default Text Config** - Default content for all templates (`/config/email_defaults.json`)
5. **Compilation Script** - Python script to compile master templates (`compileEmailTemplate.py`)
6. **AI Hero Images** - Ready-to-use hero images (`email-hero-images/` folder)

---

## The 6 Master Email Templates

1. **`signup`** - Registration confirmation (when user signs up)
2. **`newPass`** - New digital pass created (when pass is issued)
3. **`paymentReceived`** - Payment confirmation (when payment is received)
4. **`redeemPass`** - Pass redemption confirmation (when pass is used)
5. **`latePayment`** - Payment reminder (for unpaid passes)
6. **`survey_invitation`** - Survey invitation (post-activity feedback)

---

## Directory Structure

```
/templates/email_templates/
├── compileEmailTemplate.py          # ⚙️ Compilation script
├── email-hero-images/               # 🎨 AI-designed hero images (ready to use)
│   ├── signup.png
│   ├── New_passport_created.png
│   ├── payment_received.png
│   ├── passport_redeemed.png
│   ├── late_payment_notice.png
│   └── survey.png
│
├── signup/                          # 📝 MASTER (you edit this)
│   ├── index.html
│   └── good-news.png
├── signup_compiled/                 # ✅ COMPILED (app uses this)
│   ├── index.html
│   └── inline_images.json
├── signup_original/                 # 💾 BACKUP (pristine version)
│   ├── index.html
│   └── inline_images.json
│
├── newPass/                         # 📝 MASTER
│   ├── index.html
│   ├── hero_new_pass.png
│   ├── logo.png
│   └── ticket.png
├── newPass_compiled/                # ✅ COMPILED
├── newPass_original/                # 💾 BACKUP
│
├── paymentReceived/                 # 📝 MASTER
├── paymentReceived_compiled/        # ✅ COMPILED
├── paymentReceived_original/        # 💾 BACKUP
│
├── redeemPass/                      # 📝 MASTER
├── redeemPass_compiled/             # ✅ COMPILED
├── redeemPass_original/             # 💾 BACKUP
│
├── latePayment/                     # 📝 MASTER
├── latePayment_compiled/            # ✅ COMPILED
├── latePayment_original/            # 💾 BACKUP
│
├── survey_invitation/               # 📝 MASTER
├── survey_invitation_compiled/      # ✅ COMPILED
└── survey_invitation_original/      # 💾 BACKUP

/config/
└── email_defaults.json              # 📄 Default text for all templates
```

### Folder Naming Convention

- **`templateName/`** - Master template (source you edit)
- **`templateName_compiled/`** - Compiled template (app uses this, images embedded as base64)
- **`templateName_original/`** - Original backup (pristine compiled version, created once, never overwritten)

---

## How to Improve/Modify Email Templates

### Step 1: Update Default Text (Optional)

The default subject, title, intro text, and conclusion text for all templates are stored in:

**File:** `/config/email_defaults.json`

**Current Status:** Defaults are in French

**To update:**

1. Edit `/config/email_defaults.json`
2. Modify the fields you want to change:
   - `subject` - Email subject line
   - `title` - Main heading in the email
   - `intro_text` - Opening paragraph (supports Jinja2 variables and HTML)
   - `conclusion_text` - Closing paragraph (supports Jinja2 variables and HTML)
   - `cta_text` - Call-to-action button text
   - `cta_url` - Call-to-action button URL

**Example:**
```json
{
    "newPass": {
        "subject": "🎟️ Your Digital Pass is Ready!",
        "title": "Welcome!",
        "intro_text": "<p>Hello <strong>{{ pass_data.user.name }}</strong>,</p>\n<p>Great news! Your digital pass has just been created!</p>",
        "conclusion_text": "<p>💖 Thank you for being part of our community!</p>",
        "cta_text": "View My Pass",
        "cta_url": "https://minipass.me/my-passes"
    }
}
```

---

### Step 2: Update Hero Images (Recommended)

You already have **beautiful AI-designed hero images** ready to use in:

**Location:** `/templates/email_templates/email-hero-images/`

**Available Images:**
- `signup.png`
- `New_passport_created.png`
- `payment_received.png`
- `passport_redeemed.png`
- `late_payment_notice.png`
- `survey.png`

**To replace hero images in master templates:**

```bash
cd /home/kdresdell/Documents/DEV/minipass_env/app/templates/email_templates/

# Update newPass hero image
cp email-hero-images/New_passport_created.png newPass/hero_new_pass.png

# Update signup hero image
cp email-hero-images/signup.png signup/good-news.png

# Update paymentReceived hero image
cp email-hero-images/payment_received.png paymentReceived/currency-dollar.png

# Update redeemPass hero image
cp email-hero-images/passport_redeemed.png redeemPass/hand-rock.png

# Update latePayment hero image
cp email-hero-images/late_payment_notice.png latePayment/thumb-down.png

# Update survey_invitation hero image
cp email-hero-images/survey.png survey_invitation/sondage.png
```

**Important:** Make sure the filename matches what's referenced in `index.html`

---

### Step 3: Update HTML Template (Advanced)

If you want to modify the email layout, design, or structure:

1. Navigate to the master template folder (e.g., `/templates/email_templates/newPass/`)
2. Edit `index.html`
3. The HTML uses:
   - **Jinja2 templating** for dynamic content (e.g., `{{ pass_data.user.name }}`)
   - **Responsive email design** (works on mobile and desktop)
   - **Table-based layout** (for email client compatibility)
   - **Inline CSS** (email clients require inline styles)

**Key sections in each template:**
- Hero image section
- Title section
- Intro text section
- Transaction table (showing passport details)
- QR code section
- Conclusion text section
- Footer section

---

### Step 4: Compile Templates

After making any changes to **master templates**, you MUST compile them.

**Run the compilation script:**

```bash
cd /home/kdresdell/Documents/DEV/minipass_env/app/templates/email_templates/

# Compile a single template
python compileEmailTemplate.py signup
python compileEmailTemplate.py newPass
python compileEmailTemplate.py paymentReceived
python compileEmailTemplate.py redeemPass
python compileEmailTemplate.py latePayment
python compileEmailTemplate.py survey_invitation

# Or compile all templates at once (recommended)
python compileEmailTemplate.py signup && \
python compileEmailTemplate.py newPass && \
python compileEmailTemplate.py paymentReceived && \
python compileEmailTemplate.py redeemPass && \
python compileEmailTemplate.py latePayment && \
python compileEmailTemplate.py survey_invitation
```

**What the compilation script does:**
1. Reads `index.html` from master folder
2. Finds all image references (e.g., `<img src="hero_new_pass.png">`)
3. Converts images to **base64 encoded strings**
4. Replaces image paths with **CID references** (e.g., `cid:hero_new_pass`)
5. Writes compiled HTML to `templateName_compiled/index.html`
6. Writes image data to `templateName_compiled/inline_images.json`
7. Creates `templateName_original/` backup (first time only)

**Output example:**
```
🚀 Email Template Compiler v2.0 - Starting compilation...
📧 Starting compilation of 'newPass'
📂 Source path: /path/to/newPass
📂 Target path: /path/to/newPass_compiled
🖼️  Processing 4 images
📎 Embedding image: hero_new_pass.png as cid:hero_new_pass
✅ Successfully embedded 178432 bytes for hero_new_pass
💾 Writing HTML to: /path/to/newPass_compiled/index.html
✅ Verified HTML written: 6842 bytes
💾 Writing images JSON to: /path/to/newPass_compiled/inline_images.json
✅ Verified JSON written: 245632 bytes
🎉 SUCCESS: Compiled 'newPass' → 'newPass_compiled' with 4 embedded images
```

---

### Step 5: Test Your Changes

After compiling, test the templates:

**1. Restart Flask server (if needed):**
```bash
# Flask runs on localhost:5000 (already running in your setup)
# Changes will be picked up automatically if in debug mode
```

**2. Test via the application:**
- Create a test activity
- Customize email templates for that activity (Settings > Email Templates)
- Send a test email or trigger the email in the workflow
- Check your inbox to see the rendered email

**3. Preview in browser:**
- Navigate to `/activity/<activity_id>/email-templates/customize`
- Use the "Preview" or "Send Test Email" functionality

---

## Complete Workflow for Improving Templates

### Scenario: You want to improve all 6 master templates

**Step-by-step process:**

**1. Update hero images (use AI-designed images):**
```bash
cd /home/kdresdell/Documents/DEV/minipass_env/app/templates/email_templates/

cp email-hero-images/signup.png signup/good-news.png
cp email-hero-images/New_passport_created.png newPass/hero_new_pass.png
cp email-hero-images/payment_received.png paymentReceived/currency-dollar.png
cp email-hero-images/passport_redeemed.png redeemPass/hand-rock.png
cp email-hero-images/late_payment_notice.png latePayment/thumb-down.png
cp email-hero-images/survey.png survey_invitation/sondage.png
```

**2. Update default text (optional):**
```bash
nano /home/kdresdell/Documents/DEV/minipass_env/app/config/email_defaults.json
# Edit subject, title, intro_text, conclusion_text for each template
```

**3. Update HTML templates (optional):**
```bash
nano newPass/index.html
# Make design/layout changes
```

**4. Compile all templates:**
```bash
cd /home/kdresdell/Documents/DEV/minipass_env/app/templates/email_templates/

for template in signup newPass paymentReceived redeemPass latePayment survey_invitation; do
    python compileEmailTemplate.py "$template"
done
```

**5. Test the changes:**
- Access Flask app at `localhost:5000`
- Navigate to an activity's email customization page
- Preview or send test emails

---

## Important Notes

### DO NOT Edit `_compiled` or `_original` Folders Directly

- Always edit the **master template** folder (e.g., `newPass/`)
- The `_compiled` folder is **overwritten** every time you run the compilation script
- The `_original` folder is a **backup** created once (never overwritten)

### Image Requirements

- Images must be in the **master template folder**
- Images referenced in HTML must exist as files
- Supported formats: PNG, JPG, GIF
- Keep images optimized (< 500KB for hero images recommended)

### Jinja2 Variables Available

The templates have access to these variables:

**Pass-related templates (newPass, paymentReceived, redeemPass):**
- `{{ pass_data.user.name }}` - User's name
- `{{ pass_data.activity.name }}` - Activity name
- `{{ pass_data.sold_amt }}` - Price paid
- `{{ pass_data.uses_remaining }}` - Sessions remaining
- `{{ pass_data.paid }}` - Payment status (boolean)

**Signup template:**
- `{{ activity_name }}` - Activity name
- `{{ user_name }}` - User name

**Survey invitation template:**
- `{survey_url}` - Dynamic survey URL (placeholder)

### Per-Activity Customization

- Users can customize each template **per activity** via the web interface
- Customizations are stored in the database (`Activity.email_templates` JSON column)
- Master templates serve as **defaults** for new activities
- Users can reset to defaults at any time via the "Reset" button

### How the System Works

1. **Master templates** are the source of truth (what you edit)
2. **Compilation** converts master templates to production-ready versions with embedded images
3. **Default text config** provides fallback values for new activities
4. **Per-activity customization** allows users to override defaults for specific activities
5. **Database storage** preserves customizations (JSON field in Activity model)

---

## Quick Reference Commands

```bash
# Navigate to email templates directory
cd /home/kdresdell/Documents/DEV/minipass_env/app/templates/email_templates/

# Compile a single template
python compileEmailTemplate.py newPass

# Compile all templates (loop)
for t in signup newPass paymentReceived redeemPass latePayment survey_invitation; do
    python compileEmailTemplate.py "$t"
done

# View compiled HTML
cat newPass_compiled/index.html

# Check compilation script help
python compileEmailTemplate.py

# Backup before making changes
cp -r newPass/ newPass_backup_$(date +%Y%m%d)/

# List all template directories
ls -d */

# Check file sizes
du -sh *_compiled/

# View default text config
cat /home/kdresdell/Documents/DEV/minipass_env/app/config/email_defaults.json

# Edit default text config
nano /home/kdresdell/Documents/DEV/minipass_env/app/config/email_defaults.json
```

---

## Checklist for Template Improvements

### Pre-Work

- [ ] Backup current templates before making changes
- [ ] Review current default text in `/config/email_defaults.json`
- [ ] Review AI-designed hero images in `email-hero-images/`
- [ ] Identify which templates need updates

### Making Changes

- [ ] Update hero images from `email-hero-images/` folder
- [ ] Update default text in `/config/email_defaults.json`
- [ ] Modify HTML templates if needed (layout, design)
- [ ] Review Jinja2 variables to ensure compatibility

### Compilation

- [ ] Compile all 6 templates using `compileEmailTemplate.py`
- [ ] Verify no errors in compilation output
- [ ] Check that `_compiled` folders were updated
- [ ] Verify image files were embedded correctly

### Testing

- [ ] Test templates in the running Flask app (`localhost:5000`)
- [ ] Send test emails to verify rendering
- [ ] Check mobile responsiveness (open email on phone)
- [ ] Verify Jinja2 variables render correctly
- [ ] Test all 6 email types (signup, newPass, payment, redeem, late, survey)

### Documentation

- [ ] Update this guide if you made significant architectural changes
- [ ] Document any custom modifications or special considerations
- [ ] Update version number at top of this document

---

## Troubleshooting

### Issue: Compilation fails with "File not found"

**Solution:**
- Verify you're in the correct directory (`/templates/email_templates/`)
- Check that the template folder exists
- Ensure `index.html` exists in the master template folder

### Issue: Images not showing in emails

**Solution:**
- Run the compilation script again
- Verify images are in the master template folder
- Check that image filenames match what's in `index.html`
- Ensure `inline_images.json` was created in `_compiled` folder

### Issue: Changes not reflected in sent emails

**Solution:**
- Verify you compiled the templates after making changes
- Check that Flask is using the `_compiled` folder (not master)
- Restart Flask server if in production mode
- Clear browser cache if testing via web preview

### Issue: Jinja2 variables not rendering

**Solution:**
- Check variable names match what's available in the template context
- Verify syntax is correct: `{{ variable_name }}`
- Review the email sending code to ensure variables are passed correctly

---

## Advanced Topics

### Creating a New Email Template

If you need to add a 7th email template:

1. Create master folder: `/templates/email_templates/newTemplateName/`
2. Add `index.html` and images
3. Add default text to `/config/email_defaults.json`
4. Update `app.py` to include the new template in `template_types` list
5. Compile the new template
6. Update the customization UI to include the new template

### Modifying the Compilation Script

The compilation script (`compileEmailTemplate.py`) can be modified to:
- Change image compression settings
- Add support for new file formats
- Modify the CID naming convention
- Add additional processing steps

---

## Related Documentation

- [Product Requirements Document (PRD)](/docs/PRD.md) - Overall Minipass product vision
- [Development Constraints](/docs/CONSTRAINTS.md) - Technical constraints and guidelines
- [Email Template Customization UI](/templates/email_template_customization.html) - User-facing customization interface

---

**End of Guide**

For questions or issues with the email template system, consult this guide first. If you encounter problems not covered here, document the issue and solution for future reference.
