# Email Template Modification Guide

## Overview
This guide explains how to modify and improve the email templates in the Minipass application, including adding hero images and customizing the design.

## Current Email Template System

### Template Structure
The email system uses a two-tier architecture:
1. **Source Templates**: Original HTML templates with embedded images
2. **Compiled Templates**: Processed versions with base64-encoded images for email delivery

### Available Template Types
- `signup` - Registration confirmation emails
- `newPass` - New pass created notifications
- `paymentReceived` - Payment confirmation emails
- `latePayment` - Payment reminder emails
- `redeemPass` - Pass redemption confirmations
- `survey_invitation` - Survey invitation emails
- `email_survey_invitation` - Alternative survey invitation format

### Directory Structure
```
templates/email_templates/
├── compileEmailTemplate.py        # Compilation script
├── signup/                        # Source template
│   ├── index.html
│   ├── good-news.png
│   ├── facebook.png
│   └── instagram.png
├── signup_compiled/               # Compiled version
│   ├── index.html
│   └── inline_images.json
└── [other templates follow same pattern]
```

## Email Template Workflow

### 1. Template Selection Process
```
User triggers email → System checks for compiled version → Falls back to source if needed
                    → Applies custom text from settings → Sends email with embedded images
```

### 2. Image Handling
- Source templates: Images stored as separate files (PNG/JPG)
- Compilation: Images converted to base64 and embedded
- Email delivery: Images attached as CID references

### 3. Customization Points
- **Subject Line**: Configured in settings per event type
- **Title**: Dynamic title from settings
- **Intro Text**: Customizable introduction paragraph
- **Conclusion Text**: Customizable closing paragraph

## How to Modify Templates

### Step 1: Identify Which Files to Modify

**Always modify the SOURCE templates, not the compiled versions:**
- `/templates/email_templates/signup/index.html`
- `/templates/email_templates/newPass/index.html`
- `/templates/email_templates/paymentReceived/index.html`
- `/templates/email_templates/latePayment/index.html`
- `/templates/email_templates/redeemPass/index.html`
- `/templates/email_templates/survey_invitation/index.html`
- `/templates/email_templates/email_survey_invitation/index.html`

### Step 2: Make Your Modifications

#### Adding a Hero Image
1. **Add the image file** to the template folder:
   ```bash
   cp your-hero-image.jpg templates/email_templates/signup/hero.jpg
   ```

2. **Modify the HTML** to include the hero section:
   ```html
   <!-- Add this after the outer container starts (line ~14) -->
   <!-- Hero Image Section -->
   <tr>
     <td style="padding:0;">
       <img src="hero.jpg" alt="Hero Image" width="600" 
            style="display:block; width:100%; height:auto; border-radius: 8px 8px 0 0;">
     </td>
   </tr>
   ```

3. **Adjust existing padding** if needed to accommodate the hero image

#### Modifying Text Styles
Edit the inline CSS in the HTML templates:
```html
<!-- Example: Change title styling -->
<td align="center" style="font-size: 24px; font-weight: bold; color: #1e293b; padding-bottom: 20px;">
  {{ title }}
</td>
```

#### Changing Icons or Graphics
1. Add new image files to the source template folder
2. Update the `<img src="">` references in the HTML
3. Ensure image dimensions are appropriate (typically 48-300px wide)

### Step 3: Compile the Modified Templates

After making changes to source templates, compile them:

```bash
cd templates/email_templates/

# Compile a single template
python compileEmailTemplate.py signup

# Or compile all templates
for template in signup newPass paymentReceived latePayment redeemPass survey_invitation email_survey_invitation; do
    python compileEmailTemplate.py $template
done
```

The compilation script will:
- Read the source HTML and images
- Convert images to base64
- Replace image src with CID references
- Save compiled version in `{template}_compiled/` folder

### Step 4: Test Your Changes

1. **Visual Testing**: Open the compiled HTML in a browser
   ```bash
   firefox templates/email_templates/signup_compiled/index.html
   ```

2. **Send Test Email**: Use the application to trigger the email
   - Create a test signup/payment/etc.
   - Check email rendering in different clients

3. **Verify Images**: Ensure all images display correctly
   - Check CID references are working
   - Verify base64 encoding in `inline_images.json`

## Adding Hero Images to All Templates

### Recommended Approach

1. **Create/Select Hero Images**
   - Dimensions: 600px wide × 200-300px tall
   - Format: JPG for photos, PNG for graphics
   - File size: Keep under 100KB for performance
   - Style: Match your brand identity

2. **Consistent Naming Convention**
   ```
   templates/email_templates/
   ├── signup/hero.jpg
   ├── newPass/hero.jpg
   ├── paymentReceived/hero.jpg
   └── [etc...]
   ```

3. **HTML Structure for Hero Section**
   ```html
   <table width="600" cellpadding="0" cellspacing="0" border="0" 
          style="background-color:#ffffff; border-radius: 8px; overflow:hidden; margin: 40px auto;">
     
     <!-- NEW: Hero Image Row -->
     <tr>
       <td style="padding:0; line-height:0;">
         <img src="hero.jpg" alt="[Activity Name]" width="600" 
              style="display:block; width:100%; height:auto; max-height:300px; object-fit:cover;">
       </td>
     </tr>
     
     <!-- Existing icon section (adjust top padding) -->
     <tr>
       <td align="center" style="padding:40px 0 16px;"> <!-- Reduced from 80px -->
         <img src="good-news.png" alt="Icon" width="300">
       </td>
     </tr>
     
     <!-- Rest of template continues... -->
   </table>
   ```

4. **Batch Processing Script**
   Create a script to compile all templates at once:
   ```bash
   #!/bin/bash
   # save as: compile_all_templates.sh
   
   cd templates/email_templates/
   
   templates=("signup" "newPass" "paymentReceived" "latePayment" "redeemPass" "survey_invitation" "email_survey_invitation")
   
   for template in "${templates[@]}"; do
       echo "Compiling $template..."
       python compileEmailTemplate.py "$template"
   done
   
   echo "✅ All templates compiled!"
   ```

## Best Practices

### Design Guidelines
- **Mobile Responsive**: Keep width at 600px max
- **Image Optimization**: Compress images before adding
- **Fallback Text**: Always include alt text for images
- **Brand Consistency**: Use consistent colors and fonts
- **Testing**: Test in multiple email clients (Gmail, Outlook, Apple Mail)

### Performance Tips
- Keep total email size under 100KB
- Use JPG for photos, PNG for logos/icons
- Optimize images before adding to templates
- Limit number of images to 3-5 per email

### Maintenance
- Always backup templates before modifying
- Document changes in version control
- Test thoroughly after each modification
- Keep source and compiled versions in sync

## Troubleshooting

### Common Issues

1. **Images not displaying**
   - Check file paths in HTML
   - Verify compilation completed successfully
   - Check `inline_images.json` contains base64 data

2. **Compilation errors**
   - Ensure all image files exist in source folder
   - Check Python dependencies are installed
   - Verify file permissions

3. **Email rendering issues**
   - Test with inline CSS only (no external stylesheets)
   - Use table-based layouts for compatibility
   - Avoid JavaScript entirely

### Debug Commands
```bash
# Check if images exist
ls -la templates/email_templates/signup/*.png

# Verify compilation output
cat templates/email_templates/signup_compiled/inline_images.json | head -20

# Test email sending (from Flask shell)
flask shell
>>> from utils import send_email
>>> send_email("Test", "your@email.com", "signup", {"title": "Test Email"})
```

## Advanced Customization

### Dynamic Hero Images
To make hero images configurable per activity:

1. Add setting in database for hero image URL
2. Pass hero image in email context
3. Use conditional rendering in template:
   ```html
   {% if hero_image %}
   <tr>
     <td style="padding:0;">
       <img src="{{ hero_image }}" alt="Hero" width="600">
     </td>
   </tr>
   {% endif %}
   ```

### Template Variants
Create multiple versions for different use cases:
- `signup_premium/` - Enhanced design for paid tiers
- `signup_minimal/` - Simple text-focused version
- `signup_seasonal/` - Holiday/seasonal themes

### A/B Testing
Implement template selection logic:
```python
# In utils.py
template = "signup_variant_a" if user_id % 2 == 0 else "signup_variant_b"
```

## Summary Checklist

When modifying email templates:

- [ ] Identify correct source template to modify
- [ ] Add/modify images in source folder
- [ ] Update HTML structure as needed
- [ ] Run compilation script
- [ ] Verify compiled output exists
- [ ] Test email rendering locally
- [ ] Send test email through application
- [ ] Verify in multiple email clients
- [ ] Commit changes to version control
- [ ] Document any custom modifications

## Quick Reference

### File Locations
- **Source Templates**: `/templates/email_templates/{name}/index.html`
- **Compiled Templates**: `/templates/email_templates/{name}_compiled/index.html`
- **Compilation Script**: `/templates/email_templates/compileEmailTemplate.py`
- **Email Settings**: Managed through admin panel or `utils.py`

### Compilation Command
```bash
cd templates/email_templates/
python compileEmailTemplate.py [template_name]
```

### Testing URL
```
http://localhost:5000/admin/settings
```

---

*Last updated: January 2025*
*For questions or issues, consult the main application documentation or contact the development team.*