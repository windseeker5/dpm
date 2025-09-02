# Email Template Modification Workflow Guide

## 📋 Overview
This guide explains how to modify the core email templates and email blocks in the Minipass system.

## 🗂️ Directory Structure
```
templates/email_templates/
├── newPass/                 # Source template
│   ├── index.html          # Edit this HTML
│   └── *.png/jpg           # Images to embed
├── newPass_compiled/        # Auto-generated (don't edit)
│   ├── index.html          # Has cid: references
│   └── inline_images.json  # Base64 encoded images
└── compileEmailTemplate.py  # Compilation tool

templates/email_blocks/
├── owner_card_inline.html  # Owner/activity card block
└── history_table_inline.html # History table block
```

## 📝 Workflow A: Modifying Main Email Templates

### Step 1: Edit the Source Template
1. Navigate to: `templates/email_templates/[template_name]/`
   - Example: `templates/email_templates/newPass/`
2. Edit `index.html` with your changes:
   - Background styles
   - Layout changes
   - Color schemes
   - Any HTML/CSS modifications

### Step 2: Add/Replace Images
1. Place new images in the same folder as `index.html`
2. Reference them in HTML as: `<img src="filename.png">`
3. The compiler will convert these to `cid:` references

### Step 3: Compile the Template
```bash
cd templates/email_templates/
python compileEmailTemplate.py newPass
```
This will:
- Create/update `newPass_compiled/` folder
- Convert image references to `cid:image_name`
- Generate `inline_images.json` with base64 encoded images

### Step 4: Test Your Changes
1. Go to Activities → Email Customization
2. Click "Test Email" to see preview
3. Send test email to verify images render correctly

## 📝 Workflow B: Modifying Email Blocks

### Step 1: Edit the Block Template
1. Navigate to: `templates/email_blocks/`
2. Edit the block file:
   - `owner_card_inline.html` - For owner/activity card
   - `history_table_inline.html` - For history table

### Step 2: Important Notes for Blocks
- These are Jinja2 templates that receive data
- Use variables like `{{ pass_data.user.name }}`
- Inline all CSS (no external stylesheets)
- Images must use `cid:` references (e.g., `cid:logo`)

### Step 3: No Compilation Needed
- Email blocks don't need compilation
- Changes take effect immediately
- They're rendered server-side and injected into emails

### Step 4: Test Block Changes
1. Send a test email through the system
2. Check that blocks render correctly
3. Verify data is populating properly

## 🎨 Available Templates to Modify

1. **newPass** - New pass purchase confirmation
2. **redeemPass** - Pass redemption confirmation
3. **latePayment** - Payment reminder
4. **welcomeBack** - Return customer greeting
5. **cancelSignup** - Cancellation confirmation
6. **passTypeChange** - Pass type modification

## 🔑 Key Variables in Templates

### Main Templates Can Use:
- `{{ title }}` - Email title
- `{{ intro_text }}` - Introduction paragraph
- `{{ owner_html | safe }}` - Owner card block (never override!)
- `{{ history_html | safe }}` - History block (never override!)
- `{{ footer_text }}` - Footer content
- `cid:qr_code` - QR code image
- `cid:logo` - Activity logo

### Email Blocks Receive:
- `pass_data` - Pass object with user, activity, etc.
- `history` - List of pass events
- Other context variables passed from Python

## ⚠️ Important Rules

1. **Never edit *_compiled folders** - They're auto-generated
2. **Always compile after changes** to main templates
3. **Email blocks don't need compilation** - Direct edits work
4. **Use cid: for images** in final emails (not http://)
5. **Preserve {{ owner_html }} and {{ history_html }}** placeholders

## 🔧 Quick Commands

```bash
# Compile a specific template
cd templates/email_templates/
python compileEmailTemplate.py newPass

# Compile all templates (if needed)
for dir in */; do
    if [[ ! "$dir" == *"_compiled"* ]]; then
        python compileEmailTemplate.py "${dir%/}"
    fi
done
```

## 📌 Example: Changing newPass Background

1. Edit: `templates/email_templates/newPass/index.html`
2. Find: `<body style="background-color:#f5f6fa;"`
3. Change to: `<body style="background: linear-gradient(to bottom, #e3f2fd, #ffffff);"`
4. Run: `python compileEmailTemplate.py newPass`
5. Test in Email Customization tool

## 📌 Example: Improving Owner Card

1. Edit: `templates/email_blocks/owner_card_inline.html`
2. Modify the table styles, colors, layout
3. No compilation needed
4. Test by sending an email

## 🚀 Complete Example Workflow

### Scenario: Update newPass template with new background and logo

```bash
# 1. Navigate to the source template
cd /home/kdresdell/Documents/DEV/minipass_env/app/templates/email_templates/newPass/

# 2. Edit index.html (use your favorite editor)
nano index.html
# Make your changes to styles, layout, etc.

# 3. Add new logo if needed
cp /path/to/new/logo.png ./logo.png

# 4. Go back to parent directory
cd ..

# 5. Compile the template
python compileEmailTemplate.py newPass

# 6. You should see:
# ✅ Compiled 'newPass' → 'newPass_compiled' with X embedded image(s).

# 7. Test in browser
# Go to http://localhost:5000/activities
# Click on an activity → Email Customization → Test Email
```

## 💡 Tips & Tricks

1. **Keep a backup** before major changes:
   ```bash
   cp -r newPass newPass_backup_$(date +%Y%m%d)
   ```

2. **Test with different email clients** - Gmail, Outlook, Apple Mail render differently

3. **Use inline CSS** - Many email clients strip `<style>` tags

4. **Image optimization** - Keep images under 100KB for faster loading

5. **Mobile responsiveness** - Use media queries but have fallbacks

## 🔍 Troubleshooting

### Images not showing in email?
- Check compilation output for warnings
- Verify image files exist in source folder
- Ensure `cid:` references match image names

### Styles not applying?
- Use inline styles instead of classes
- Some CSS properties aren't supported in email
- Test in multiple email clients

### Block not updating?
- Email blocks update immediately (no compilation)
- Clear any caching if using one
- Check Jinja2 syntax for errors

## 📚 Related Documentation
- `/docs/PRD.md` - Product requirements
- `/docs/CONSTRAINTS.md` - Technical constraints
- `/plans/finalization_of_email_customization.md` - Implementation details

---
*Last updated: January 2025*
*This workflow ensures your beautiful templates remain the foundation while allowing customization through the tool we built.*