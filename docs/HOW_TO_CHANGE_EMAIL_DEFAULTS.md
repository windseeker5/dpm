# How to Change Default Email Templates

## Quick Guide

To change the default email templates for all new activities:

1. **Edit the configuration file:**
   ```
   config/email_defaults.json
   ```

2. **Available email types to customize:**
   - `newPass` - Sent when a new digital pass is created
   - `paymentReceived` - Sent when payment is confirmed
   - `latePayment` - Payment reminder
   - `signup` - Registration confirmation
   - `redeemPass` - Pass redemption confirmation
   - `survey_invitation` - Survey request

3. **Fields you can modify for each email type:**
   - `subject` - Email subject line
   - `title` - Main title in the email body
   - `intro_text` - Opening text (supports HTML)
   - `conclusion_text` - Closing text (supports HTML)
   - `custom_message` - Additional custom content
   - `cta_text` - Call-to-action button text (if applicable)
   - `cta_url` - Call-to-action button URL (if applicable)

## Example

To change the subject of the "newPass" email:

1. Open `config/email_defaults.json`
2. Find the `"newPass"` section
3. Change the `"subject"` field:
   ```json
   "subject": "🎉 Votre nouveau passe est prêt!"
   ```
4. Save the file
5. All new activities created after this change will use the new default

## Important Notes

- Changes only affect **new activities** created after modification
- Existing activities keep their current templates
- You can use HTML in `intro_text` and `conclusion_text`
- Support Jinja2 variables like `{{ pass_data.user.name }}`
- Keep the JSON format valid (use quotes, commas correctly)

## Testing Changes

After modifying the defaults, create a test activity to verify the new templates are applied correctly.