# Email Deliverability Fix Implementation Plan

**Created:** January 9, 2025  
**Purpose:** Fix email deliverability issues causing spam folder placement  
**Current Status:** Emails scoring ~11/5 on SpamAssassin (threshold is 5)  

---

## 🚀 Phase 1: Critical Headers & Compliance (1-2 hours)
**Impact: 50% spam reduction**

### 1.1 Add Missing Email Headers in send_email()
Location: `utils.py` lines 1514-1529

Required headers to add:
```python
msg["Reply-To"] = reply_to_email or from_email
msg["List-Unsubscribe"] = f"<mailto:unsubscribe@minipass.me?subject=Unsubscribe&body=email:{to_email}>"
msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
msg["Precedence"] = "bulk"
msg["X-Mailer"] = "Minipass/1.0"
msg["Message-ID"] = f"<{timestamp}@minipass.me>"
msg["X-Entity-Ref-ID"] = organization_id  # For tracking
```

### 1.2 Implement Unsubscribe Mechanism
- Add unsubscribe link to all email templates
- Create `/unsubscribe` endpoint in app.py
- Add `email_opt_out` column to User model
- Check opt-out status before sending

### 1.3 Add Legal Compliance to Templates
Add to all templates in `/templates/email_templates/*/index.html`:
```html
<div class="footer-legal">
  <p>Minipass - 123 Main Street, Montreal, QC H1A 1A1, Canada</p>
  <p><a href="{unsubscribe_url}">Unsubscribe</a> | <a href="https://minipass.me/privacy">Privacy Policy</a></p>
  <p>You received this email because you signed up for {activity_name}</p>
</div>
```

---

## 🔧 Phase 2: Content Optimization (2-3 hours)
**Impact: 30% spam reduction**

### 2.1 Improve Plain Text Generation
Location: `utils.py` lines 1524-1527

Replace minimal plain text with full content extraction:
```python
def generate_plain_text(html_content, context):
    """Generate comprehensive plain text from HTML"""
    # Extract all text content
    # Include all links with full URLs
    # Format for readability
    # Match HTML information structure
```

### 2.2 Fix Subject Lines
Current: "Minipass Notification"

Implement dynamic subjects:
- New Pass: `[{activity_name}] Your digital pass is ready`
- Payment Received: `[{activity_name}] Payment confirmed - Pass activated`
- Reminder: `[{activity_name}] Reminder: Your session is tomorrow`
- Survey: `[{activity_name}] We'd love your feedback`

### 2.3 Optimize HTML Structure
- Remove inline CSS blocks (lines 20-85 in templates)
- Use single table layout instead of nested tables
- Implement responsive design with media queries
- Use semantic HTML5 where possible

---

## 🖼️ Phase 3: Image Handling (2-3 hours)
**Impact: 20% spam reduction**

### 3.1 Convert Inline Images to Hosted URLs

Current implementation:
```python
inline_images = {
    'qr_code': qr_img_data,
    'hero_image': hero_data
}
```

New implementation:
```python
# Save images to static/uploads/email_assets/
# Reference via URLs
image_urls = {
    'qr_code': f"https://minipass.me/static/uploads/qr/{pass_id}.png",
    'hero_image': f"https://minipass.me/static/uploads/heroes/{activity_id}.jpg"
}
```

### 3.2 Optimize QR Codes
- Reduce QR code size to 200x200px
- Use PNG compression
- Cache generated QR codes
- Serve from CDN or static hosting

### 3.3 Remove Social Media Icons
- Remove Facebook/Instagram embedded icons
- Replace with text links if needed
- Reduces spam indicators

---

## 📊 Phase 4: Monitoring & DNS (30 minutes)
**Quick wins outside code**

### 4.1 Update DMARC Policy
Update DNS TXT record for `_dmarc.minipass.me`:

**Current:**
```
v=DMARC1; p=none; rua=mailto:admin@minipass.me
```

**New:**
```
v=DMARC1; p=quarantine; pct=100; rua=mailto:admin@minipass.me; ruf=mailto:admin@minipass.me; fo=1
```

### 4.2 Set Up Monitoring
- Create DMARC report parser
- Track bounce rates in EmailLog table
- Monitor spam complaints
- Set up alerts for delivery issues

---

## 🧪 Testing Protocol

### After Each Phase:
1. **Authentication Test:**
   ```bash
   # Send test email to Port25 verifier
   curl -X POST http://localhost:5000/admin/test-email \
     -d "to=check-auth@verifier.port25.com"
   ```

2. **Spam Score Test:**
   - Generate unique test address at https://www.mail-tester.com
   - Send test email to provided address
   - Review detailed spam report

3. **Provider Testing:**
   - Gmail: Check if lands in Primary, Promotions, or Spam
   - Outlook: Test Focused Inbox placement
   - Yahoo: Verify inbox delivery

### Success Metrics:
| Phase | Expected SpamAssassin Score | Target |
|-------|----------------------------|--------|
| Current | ~11.0 | Failing |
| After Phase 1 | ~6.0 | Borderline |
| After Phase 2 | ~4.0 | Passing |
| After Phase 3 | ~2.0 | Excellent |
| After Phase 4 | <2.0 | Optimal |

---

## 📋 Implementation Checklist

### Phase 1 Tasks:
- [ ] Add email headers to send_email()
- [ ] Create unsubscribe endpoint
- [ ] Add unsubscribe link to templates
- [ ] Add physical address to footers
- [ ] Test with mail-tester.com

### Phase 2 Tasks:
- [ ] Implement full plain text generation
- [ ] Update all email subjects
- [ ] Simplify HTML structure
- [ ] Remove nested tables
- [ ] Test spam score improvement

### Phase 3 Tasks:
- [ ] Move images to static hosting
- [ ] Update templates to use image URLs
- [ ] Optimize QR code generation
- [ ] Remove social media icons
- [ ] Verify email size <50KB

### Phase 4 Tasks:
- [ ] Update DMARC record in DNS
- [ ] Set up DMARC report parsing
- [ ] Create monitoring dashboard
- [ ] Document monitoring process

---

## 🎯 Expected Outcomes

### Immediate Benefits (Phase 1):
- Legal compliance achieved
- 50% reduction in spam scoring
- Some emails reaching inbox

### Short-term Benefits (Phase 2-3):
- 80% inbox delivery rate
- Professional email appearance
- Improved user trust

### Long-term Benefits (Phase 4):
- 95%+ inbox delivery rate
- Full visibility into delivery issues
- Proactive issue detection
- Maintained sender reputation

---

## 📝 Notes

- Authentication (SPF/DKIM) is already working perfectly
- Main issues are missing headers and content structure
- Each phase can be tested independently
- Rollback plan: Keep original send_email() as send_email_legacy()

---

**End of Plan**