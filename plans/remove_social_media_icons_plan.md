# Plan to Remove Social Media Icons from Email Templates

**Created:** January 9, 2025  
**Purpose:** Complete removal of social media icons to improve email deliverability  
**Status:** Ready for implementation  

---

## Current Situation

- Social media icons (Facebook & Instagram) are still present in 3 main templates:
  - `signup/index.html`
  - `latePayment/index.html`  
  - `redeemPass/index.html`
- The `newPass` and `paymentReceived` templates were partially cleaned in Phase 2
- Icon image files exist in 5 templates (72KB of unnecessary images total)
- These icons link to generic Minipass social pages, not customer-specific ones

## Implementation Plan

### 1. Remove Social Media HTML Sections from remaining templates

Remove the entire "Footer Icons with Facebook and Instagram" table section from:
- `signup/index.html` (lines 64-80)
- `latePayment/index.html` (similar section)
- `redeemPass/index.html` (similar section)

Example of section to remove:
```html
<!-- ✅ Footer Icons with Facebook and Instagram only -->
<table width="600" cellpadding="0" cellspacing="0" border="0" style="margin: 0 auto 7px;">
  <tr>
    <td align="center" style="padding: 7px 0; font-size:0;">
      <a href="https://www.facebook.com/profile.php?id=61554658763800">
        <img src="facebook.png" alt="Facebook" width="30" style="margin: 0 8px;">
      </a>
      <a href="#">
        <img src="instagram.png" alt="Instagram" width="30" style="margin: 0 8px;">
      </a>
    </td>
  </tr>
</table>
```

### 2. Delete Social Media Image Files

Remove the following files:
- `newPass/facebook.png` (12KB)
- `newPass/instagram.png` (60KB)
- `paymentReceived/facebook.png` (12KB)
- `paymentReceived/instagram.png` (60KB)
- `signup/facebook.png` (12KB)
- `signup/instagram.png` (60KB)
- `redeemPass/facebook.png` (12KB)
- `redeemPass/instagram.png` (60KB)
- `latePayment/facebook.png` (12KB)
- `latePayment/instagram.png` (60KB)

Total space saved: 360KB of unnecessary images

### 3. Recompile All Templates

```bash
cd templates/email_templates
python compileEmailTemplate.py newPass
python compileEmailTemplate.py paymentReceived
python compileEmailTemplate.py signup
python compileEmailTemplate.py redeemPass
python compileEmailTemplate.py latePayment
python compileEmailTemplate.py email_survey_invitation
```

### 4. Test the Changes

- Verify templates still render correctly
- Check that compiled versions don't reference missing images
- Run existing unit tests to ensure no breakage
- Test email sending with one template to verify no broken images

## Benefits

- **Reduced spam signals**: Social media icons are known spam indicators
- **Better deliverability**: Cleaner, more professional emails
- **Smaller email size**: 360KB less in image attachments per email
- **Multi-tenant appropriate**: No hardcoded Minipass social links in customer emails
- **Better image-to-text ratio**: Fewer images means better spam scores
- **Faster email loading**: Less data to download

## Impact

This will complete the social media icon removal that was started in Phase 2, ensuring all templates are clean and optimized for deliverability.

## Expected Improvement

- **Spam score reduction**: ~5-10% improvement
- **Email size reduction**: ~360KB per email
- **Professional appearance**: Cleaner footer without irrelevant social links

## Notes

- This is a follow-up to Phase 2 optimizations
- Part of the larger email deliverability improvement initiative
- Aligns with multi-tenant architecture where each organization would want their own social links (if any)