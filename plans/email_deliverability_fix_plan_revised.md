# Email Deliverability Fix Implementation Plan (REVISED)

**Created:** January 9, 2025  
**Revised:** January 9, 2025  
**Purpose:** Fix email deliverability issues with subdomain-aware architecture  
**Current Status:** Phase 1 partially implemented but needs fixes  
**Architecture:** One container per customer with subdomain (e.g., lhgi.minipass.me)

---

## 🔴 Critical Issues Found in Initial Implementation

1. **Hardcoded URLs:** Templates use `https://minipass.me` instead of customer subdomains
2. **Uncompiled Templates:** Changes only in source files, not compiled versions
3. **Missing Context:** No organization/subdomain context passed to templates
4. **Architecture Mismatch:** Unsubscribe endpoint needs to work per-container

---

## 🚀 Phase 1: Critical Headers & Compliance (REVISED)
**Impact: 50% spam reduction**
**Status: Needs completion**

### 1.1 ✅ Add Missing Email Headers (COMPLETED)
Location: `utils.py` lines 1522-1536

Headers successfully added:
- Reply-To
- List-Unsubscribe 
- List-Unsubscribe-Post
- Precedence: bulk
- X-Mailer: Minipass/1.0
- Message-ID with timestamp
- X-Entity-Ref-ID for tracking

### 1.2 ⚠️ Fix Organization Context & URLs (NEEDS WORK)

#### Add Organization Detection to send_email()
```python
# Detect organization from context or session
if context and 'organization_id' in context:
    org = Organization.query.get(context['organization_id'])
elif 'organization_domain' in session:
    org = Organization.query.filter_by(domain=session['organization_domain']).first()
else:
    org = None

# Generate base URL
if org and org.domain:
    base_url = f"https://{org.domain}.minipass.me"
else:
    base_url = "https://minipass.me"  # Fallback

# Add to context
context['base_url'] = base_url
context['unsubscribe_url'] = f"{base_url}/unsubscribe?email={to_email}"
context['privacy_url'] = f"{base_url}/privacy"
context['organization_name'] = org.name if org else "Minipass"
context['organization_address'] = org.address if org else "123 Main Street, Montreal, QC H1A 1A1"

# Fix List-Unsubscribe header to use subdomain
msg["List-Unsubscribe"] = f"<{context['unsubscribe_url']}>"
```

### 1.3 ⚠️ Update All Email Templates (NEEDS RECOMPILATION)

Replace hardcoded URLs with template variables in ALL templates:

**OLD (Wrong):**
```html
<a href="https://minipass.me/unsubscribe?email={{ user_email }}">Unsubscribe</a>
<a href="https://minipass.me/privacy">Privacy Policy</a>
<p>Minipass - 123 Main Street, Montreal, QC H1A 1A1, Canada</p>
```

**NEW (Correct):**
```html
<a href="{{ unsubscribe_url }}">Unsubscribe</a>
<a href="{{ privacy_url }}">Privacy Policy</a>
<p>{{ organization_name }} - {{ organization_address }}</p>
```

Templates to update:
- [ ] newPass/index.html
- [ ] paymentReceived/index.html
- [ ] signup/index.html
- [ ] redeemPass/index.html
- [ ] latePayment/index.html
- [ ] email_survey_invitation/index.html

### 1.4 ⚠️ Compile All Templates (CRITICAL)

After updating templates, MUST compile them:
```bash
cd templates/email_templates
python compileEmailTemplate.py newPass
python compileEmailTemplate.py paymentReceived
python compileEmailTemplate.py signup
python compileEmailTemplate.py redeemPass
python compileEmailTemplate.py latePayment
python compileEmailTemplate.py email_survey_invitation
```

### 1.5 ✅ Unsubscribe Mechanism (COMPLETED but needs subdomain fix)
- Added `email_opt_out` column to User model
- Created `/unsubscribe` endpoint with CSRF exemption
- Added opt-out checking in send_email()
- Works at container level (each subdomain handles its own)

---

## 🔧 Phase 2: Content Optimization
**Impact: 30% spam reduction**
**Status: Not started**

### 2.1 Improve Plain Text Generation
Location: `utils.py` lines 1524-1527

Current implementation is minimal. Need full text extraction:
```python
def generate_plain_text(html_content, context):
    """Generate comprehensive plain text from HTML"""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Get text and preserve structure
    text = soup.get_text(separator='\n', strip=True)
    
    # Add links in parentheses
    for link in soup.find_all('a', href=True):
        text = text.replace(link.text, f"{link.text} ({link['href']})")
    
    return text
```

### 2.2 Fix Subject Lines
Implement dynamic, context-aware subjects:

```python
# In send_email() or calling code
subject_templates = {
    'newPass': '[{activity_name}] Your digital pass is ready',
    'paymentReceived': '[{activity_name}] Payment confirmed - Pass activated',
    'signup': '[{activity_name}] Registration confirmation',
    'redeemPass': '[{activity_name}] Pass redeemed successfully',
    'latePayment': '[{activity_name}] Payment reminder',
    'email_survey_invitation': '[{activity_name}] We'd love your feedback'
}

# Use template type to generate subject
if template_type in subject_templates and context.get('activity_name'):
    subject = subject_templates[template_type].format(**context)
```

### 2.3 Optimize HTML Structure
- Remove excessive inline CSS
- Use single table layout
- Reduce nested tables
- Keep total email size < 50KB

---

## 🖼️ Phase 3: Image Handling
**Impact: 20% spam reduction**
**Status: Not started**

### 3.1 Convert Inline Images to Hosted URLs

Instead of embedding images as base64:
```python
# Save images to static directory
image_urls = {
    'qr_code': f"{base_url}/static/uploads/qr/{pass_id}.png",
    'hero_image': f"{base_url}/static/uploads/heroes/{activity_id}.jpg",
    'logo': f"{base_url}/static/uploads/logos/{org.logo_filename}"
}

# Pass URLs to template instead of inline data
context['image_urls'] = image_urls
```

### 3.2 Optimize QR Codes
- Reduce to 200x200px
- Use PNG compression
- Cache generated codes
- Serve from subdomain URL

### 3.3 Remove Social Media Icons
- Remove Facebook/Instagram embedded icons
- Use text links only
- Reduces spam signals

---

## 📊 Phase 4: Monitoring & DNS
**Impact: Final optimizations**
**Status: Not started**

### 4.1 Update DMARC Policy
Each subdomain needs proper DNS records:
```
_dmarc.lhgi.minipass.me IN TXT "v=DMARC1; p=quarantine; pct=100; rua=mailto:admin@lhgi.minipass.me"
```

### 4.2 Monitoring Per Container
- Track bounce rates per organization
- Monitor spam complaints
- Set up per-container alerts

---

## 🧪 Testing Protocol

### After Each Phase:
1. **Test with specific subdomain:**
   ```bash
   curl https://lhgi.minipass.me/test-email
   ```

2. **Verify headers and URLs:**
   - Check List-Unsubscribe points to subdomain
   - Verify all links use correct subdomain
   - Confirm images load from subdomain

3. **Spam Score Testing:**
   - Use mail-tester.com
   - Test from actual subdomain
   - Verify score improvement

### Success Metrics:
| Phase | Expected Score | Current | Target |
|-------|---------------|---------|--------|
| Initial | ~11.0 | 11.0 | - |
| Phase 1 Fixed | ~6.0 | Pending | <7.0 |
| Phase 2 | ~4.0 | - | <5.0 |
| Phase 3 | ~2.0 | - | <3.0 |
| Phase 4 | <2.0 | - | <2.0 |

---

## 📋 Implementation Checklist

### Phase 1 Fixes (PRIORITY):
- [ ] Add organization detection to send_email()
- [ ] Update context with base_url and dynamic URLs
- [ ] Fix all 6 templates to use template variables
- [ ] Compile all templates
- [ ] Test unsubscribe at subdomain URL
- [ ] Verify headers use subdomain URLs
- [ ] Run database migration for email_opt_out

### Phase 2 Tasks:
- [ ] Implement full plain text generation
- [ ] Add dynamic subject lines
- [ ] Simplify HTML structure
- [ ] Remove nested tables
- [ ] Test spam score improvement

### Phase 3 Tasks:
- [ ] Move images to static hosting
- [ ] Update templates for URL-based images
- [ ] Optimize QR code generation
- [ ] Remove social media icons
- [ ] Verify email size <50KB

### Phase 4 Tasks:
- [ ] Configure DMARC per subdomain
- [ ] Set up monitoring dashboard
- [ ] Create alert system
- [ ] Document DNS requirements

---

## 🎯 Critical Success Factors

1. **Subdomain Awareness:** Every URL must respect the customer's subdomain
2. **Template Compilation:** Changes must be compiled to take effect
3. **Organization Context:** Every email must know which organization it's from
4. **Container Isolation:** Each container handles its own unsubscribes
5. **Testing:** Must test from actual subdomain, not localhost

---

## 📝 Notes

- **Current Issue:** Phase 1 partially implemented but not working due to hardcoded URLs and uncompiled templates
- **Priority:** Fix Phase 1 completely before moving to Phase 2
- **Architecture:** Remember each customer has their own container at subdomain.minipass.me
- **Rollback:** Keep original templates in `_original` folders

---

**End of Revised Plan**