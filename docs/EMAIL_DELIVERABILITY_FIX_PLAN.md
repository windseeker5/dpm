# Minipass Email Deliverability Fix Plan

**Date:** January 8, 2025  
**Priority:** CRITICAL - Implement immediately to restore email delivery  
**Target:** Achieve 95%+ inbox delivery rate  

---

## 📋 Implementation Phases

### **PHASE 1: EMERGENCY FIXES (Day 1 - Immediate)**
*These fixes will provide immediate improvement*

#### 1.1 Configure Email Authentication (2 hours)

**Step 1: Add SPF Record to DNS**
```
Type: TXT
Host: @ (or blank)
Value: v=spf1 include:_spf.google.com include:sendgrid.net ip4:YOUR_SERVER_IP ~all
```

**Step 2: Enable DKIM**
- If using Gmail: Enable in Google Workspace Admin
- If using SendGrid: Generate DKIM records in SendGrid settings
- Add DKIM records to your DNS

**Step 3: Add DMARC Record**
```
Type: TXT
Host: _dmarc
Value: v=DMARC1; p=none; rua=mailto:dmarc@minipass.me; pct=100
```

#### 1.2 Fix Critical Email Headers (1 hour)

**Update `utils.py` send_email function:**
```python
def send_email(subject, to_email, template_name=None, context=None, inline_images=None, html_body=None, timestamp_override=None, email_config=None):
    # ... existing code ...
    
    # ADD THESE HEADERS (after line creating msg object):
    msg["List-Unsubscribe"] = "<mailto:unsubscribe@minipass.me?subject=Unsubscribe>"
    msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
    msg["Reply-To"] = email_config.get('reply_to', 'support@minipass.me') if email_config else 'support@minipass.me'
    msg["X-Priority"] = "3"  # Normal priority
    msg["X-Mailer"] = "Minipass/1.0"
    msg["Precedence"] = "bulk"  # For transactional emails
    
    # ... rest of function ...
```

#### 1.3 Change Sender Address (30 minutes)

**Update default sender in settings:**
```python
# In app.py or settings configuration:
# REPLACE:
MAIL_DEFAULT_SENDER = "noreply@minipass.me"
# WITH:
MAIL_DEFAULT_SENDER = "hockey@minipass.me"  # or "support@minipass.me"
```

#### 1.4 Add Legal Requirements to Footer (1 hour)

**Update all email templates to include:**
```html
<!-- Add to email footer -->
<tr>
  <td style="padding: 20px; background-color: #f8f9fa; font-size: 12px; color: #6c757d;">
    <p><strong>LHGI Hockey League</strong><br>
    123 Main Street, Montreal, QC H1A 1A1<br>
    Tel: (514) 555-0123</p>
    
    <p>Vous recevez ce courriel car vous êtes inscrit à nos activités.<br>
    <a href="https://minipass.me/unsubscribe?token={{unsubscribe_token}}" style="color: #007bff;">Se désabonner</a> | 
    <a href="https://minipass.me/preferences" style="color: #007bff;">Gérer les préférences</a></p>
  </td>
</tr>
```

---

### **PHASE 2: CONTENT OPTIMIZATION (Day 1-2)**
*Improve email content to pass spam filters*

#### 2.1 Create Plain Text Versions (2 hours)

**Add to send_email function:**
```python
def generate_plain_text(html_content):
    """Convert HTML to plain text for email"""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    # Get text
    text = soup.get_text()
    # Break lines and clean up
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = '\n'.join(chunk for chunk in chunks if chunk)
    return text

# In send_email function:
text_content = generate_plain_text(final_html)
msg.attach(MIMEText(text_content, 'plain'))
msg.attach(MIMEText(final_html, 'html'))
```

#### 2.2 Simplify HTML Templates (3 hours)

**New template structure:**
```html
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{activity_name}} - {{email_type}}</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <!-- Simple header -->
        <div style="text-align: center; padding: 20px 0; border-bottom: 2px solid #e0e0e0;">
            <h1 style="color: #2c3e50; margin: 0;">{{activity_name}}</h1>
        </div>
        
        <!-- Content -->
        <div style="padding: 30px 0;">
            <p>Bonjour {{user_name}},</p>
            {{content}}
        </div>
        
        <!-- Footer -->
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e0e0e0; font-size: 12px; color: #666;">
            {{footer_content}}
        </div>
    </div>
</body>
</html>
```

#### 2.3 Fix Image Handling (2 hours)

**Step 1: Host images on server**
```python
# Instead of embedding images:
# WRONG: <img src="cid:logo_image">
# RIGHT: <img src="https://minipass.me/static/images/logo.png" alt="Logo">
```

**Step 2: Update QR code handling**
```python
# Generate QR code URL instead of embedding:
def get_qr_code_url(passport_id):
    return f"https://minipass.me/qr/{passport_id}.png"

# In template:
<img src="{{qr_code_url}}" alt="QR Code" style="width: 200px; height: 200px;">
```

---

### **PHASE 3: ACTIVITY-SPECIFIC CUSTOMIZATION (Day 2)**
*Personalize for hockey league*

#### 3.1 Create Organization-Specific Configuration (2 hours)

```python
# Add to Organization model or settings:
HOCKEY_EMAIL_CONFIG = {
    'sender_name': 'LHGI Hockey',
    'sender_email': 'hockey@lhgi.minipass.me',
    'reply_to': 'admin@lhgi.ca',
    'subject_prefix': '[LHGI] ',
    'footer_address': 'LHGI Hockey League\n123 Arena Street\nMontreal, QC H2X 3Y4',
    'footer_phone': '(514) 555-HOCKEY',
    'unsubscribe_url': 'https://lhgi.minipass.me/unsubscribe',
    'logo_url': 'https://lhgi.minipass.me/static/logo.png'
}
```

#### 3.2 Update Email Sending Logic (1 hour)

```python
def send_activity_email(activity, user, email_type, **kwargs):
    """Send activity-specific email"""
    # Get activity-specific config
    if activity.organization:
        email_config = activity.organization.get_email_config()
    else:
        email_config = DEFAULT_EMAIL_CONFIG
    
    # Personalize subject
    subject = f"{email_config['subject_prefix']}{kwargs.get('subject', '')}"
    
    # Add activity context
    context = {
        'user_name': user.name,
        'activity_name': activity.name,
        'organization_name': email_config['sender_name'],
        'footer_address': email_config['footer_address'],
        **kwargs.get('context', {})
    }
    
    send_email(
        subject=subject,
        to_email=user.email,
        template_name=email_type,
        context=context,
        email_config=email_config
    )
```

---

### **PHASE 4: EMAIL WARMING STRATEGY (Week 1-2)**
*Gradually increase sending volume*

#### 4.1 Implement Gradual Sending (1 day)

```python
def get_sending_batch_size(week_number):
    """Calculate batch size based on warming period"""
    if week_number == 1:
        return 0.1  # 10% of users
    elif week_number == 2:
        return 0.25  # 25% of users
    elif week_number == 3:
        return 0.5  # 50% of users
    else:
        return 1.0  # 100% of users

def send_batch_emails(users, email_data, week_number=1):
    """Send emails in batches during warming period"""
    batch_percentage = get_sending_batch_size(week_number)
    batch_size = int(len(users) * batch_percentage)
    
    # Sort users by engagement (most engaged first)
    sorted_users = sorted(users, key=lambda u: u.last_activity_date, reverse=True)
    
    # Send to batch
    for user in sorted_users[:batch_size]:
        send_activity_email(user, **email_data)
        time.sleep(0.5)  # Delay between sends
```

#### 4.2 Ask Users to Whitelist (Immediate)

**Send announcement (via alternative channel):**
```
Chers membres LHGI,

Pour vous assurer de recevoir nos communications importantes 
(confirmations de paiement, passes digitaux), veuillez ajouter 
hockey@minipass.me à vos contacts.

Instructions:
- Gmail: Déplacer un email du spam vers la boîte de réception
- Outlook: Ajouter à la liste des expéditeurs approuvés
- Yahoo: Marquer comme "Pas du spam"

Merci!
L'équipe LHGI
```

---

### **PHASE 5: MONITORING & TESTING (Ongoing)**

#### 5.1 Set Up Monitoring Tools (2 hours)

**Tools to implement:**
```python
# Add to email sending function:
def log_email_metrics(to_email, subject, status):
    """Log email sending metrics"""
    EmailLog.create(
        to_email=to_email,
        subject=subject,
        status=status,  # 'sent', 'bounced', 'complained'
        timestamp=datetime.now(),
        spam_score=check_spam_score(email_content)
    )

def check_spam_score(email_content):
    """Check spam score before sending"""
    # Use SpamAssassin API or service
    # Return score 0-10
    pass
```

**External tools to set up:**
1. Google Postmaster Tools (for Gmail delivery)
2. Microsoft SNDS (for Outlook delivery)
3. Return Path Certification (optional)

#### 5.2 Testing Protocol (Before each send)

```python
def test_email_before_sending(email_content, to_email):
    """Test email before sending to production"""
    tests = {
        'spam_score': check_spam_score(email_content) < 5,
        'has_unsubscribe': 'unsubscribe' in email_content.lower(),
        'has_address': check_physical_address(email_content),
        'has_plain_text': check_plain_text_exists(email_content),
        'size_ok': len(email_content) < 102400,  # 100KB
        'auth_configured': check_spf_dkim_dmarc()
    }
    
    if not all(tests.values()):
        failed = [k for k, v in tests.items() if not v]
        raise EmailValidationError(f"Email failed tests: {failed}")
    
    return True
```

---

### **PHASE 6: LONG-TERM IMPROVEMENTS (Month 1-2)**

#### 6.1 Consider Email Service Provider

**Recommended providers for better delivery:**
- SendGrid (excellent for transactional)
- Mailgun (good API, reasonable pricing)
- Amazon SES (cheapest, requires more setup)
- Postmark (best for transactional emails)

#### 6.2 Implement Feedback Loops

```python
# Handle bounce and complaint webhooks
@app.route('/email/webhook', methods=['POST'])
def handle_email_webhook():
    data = request.json
    if data['event'] == 'bounce':
        mark_email_as_bounced(data['email'])
    elif data['event'] == 'complaint':
        unsubscribe_user(data['email'])
    return '', 200
```

#### 6.3 A/B Testing for Optimization

```python
def ab_test_subject_lines(users, subject_a, subject_b):
    """Test which subject line performs better"""
    half = len(users) // 2
    group_a = users[:half]
    group_b = users[half:]
    
    # Send and track metrics
    results_a = send_and_track(group_a, subject_a)
    results_b = send_and_track(group_b, subject_b)
    
    # Analyze and use winner for future
    return compare_results(results_a, results_b)
```

---

## 📊 Success Metrics

### Week 1 Goals:
- Spam score < 5
- 50% inbox delivery rate
- Zero bounce rate on engaged users

### Week 2 Goals:
- Spam score < 3
- 75% inbox delivery rate
- User complaints < 0.1%

### Month 1 Goals:
- Spam score < 2
- 95% inbox delivery rate
- Established sender reputation

---

## 🚀 Quick Start Checklist

### Day 1 - Morning:
- [ ] Configure SPF record
- [ ] Add email headers to send_email function
- [ ] Change from noreply@ to support@ or hockey@
- [ ] Add physical address to footer

### Day 1 - Afternoon:
- [ ] Create plain text version generator
- [ ] Update one template as test
- [ ] Test with mail-tester.com
- [ ] Send test batch to 10 users

### Day 2:
- [ ] Configure DKIM
- [ ] Update all templates
- [ ] Implement organization-specific config
- [ ] Begin gradual sending increase

### Week 1:
- [ ] Monitor delivery metrics
- [ ] Adjust based on feedback
- [ ] Complete DMARC setup
- [ ] Full template migration

---

## 🆘 Emergency Contacts

If you need help:
- **DNS Configuration:** Your domain registrar support
- **Email Authentication:** Your email provider support
- **Deliverability Consulting:** Consider hiring specialist if issues persist

---

## 📝 Notes for Hockey League Specifically

For LHGI Hockey, prioritize:
1. Change sender to hockey@lhgi.minipass.me
2. Add "LHGI Hockey" as sender name
3. Include arena address in footer
4. Use hockey-specific language in templates
5. Test with most engaged members first

---

**End of Fix Plan Document**

*Remember: Email deliverability is an ongoing process. Monitor, adjust, and improve continuously.*