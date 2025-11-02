# Security Checklist for Production Deployment

## 🚨 CRITICAL ISSUES TO FIX BEFORE PRODUCTION

### 1. Hardcoded SECRET_KEY (CRITICAL)

**Location:** `app.py` line 189

**Current Code:**
```python
app.config["SECRET_KEY"] = "MY_SECRET_KEY_FOR_NOW"
```

**Required Fix:**
```python
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
if not app.config["SECRET_KEY"]:
    raise ValueError("SECRET_KEY environment variable must be set for production")
```

**Why This Matters:**
- Flask's SECRET_KEY is used for session signing, CSRF tokens, and other security features
- A hardcoded key means anyone with access to the code can forge sessions
- This is a **CRITICAL** vulnerability that MUST be fixed before production deployment

**Action Required:**
1. Generate a strong random secret key: `python -c "import secrets; print(secrets.token_hex(32))"`
2. Add `SECRET_KEY=<generated_key>` to your `.env` file
3. Update app.py to read from environment variable
4. Never commit the `.env` file to git (already in .gitignore)

---

## ✅ Security Best Practices Already Implemented

1. **Environment Variables:** Using `.env` file for sensitive configuration
2. **Password Hashing:** Using bcrypt for admin password hashing
3. **CSRF Protection:** Flask-WTF CSRFProtect enabled
4. **Rate Limiting:** Custom rate limiting decorators implemented
5. **SQL Injection Protection:** Using SQLAlchemy ORM parameterized queries
6. **Secure File Uploads:** Using `secure_filename()` for uploaded files
7. **Email Configuration:** Mail passwords stored in database settings (encrypted)

---

## 🔍 Additional Security Considerations for Production

### Database Security
- [ ] Ensure production database has proper file permissions (600)
- [ ] Regularly backup database files
- [ ] Consider database encryption at rest for sensitive customer data

### Web Server Configuration
- [ ] Use HTTPS/TLS certificates (Let's Encrypt recommended)
- [ ] Configure proper CORS headers
- [ ] Set secure session cookie flags (`SESSION_COOKIE_SECURE=True`)
- [ ] Enable `SESSION_COOKIE_HTTPONLY=True`
- [ ] Set `SESSION_COOKIE_SAMESITE='Lax'`

### API Keys & Credentials
- [ ] Rotate all API keys before production
- [ ] Use different Stripe keys for production vs development
- [ ] Ensure all email service credentials are in environment variables
- [ ] Verify Google AI API keys are production-ready

### Container Security
- [ ] Run containers as non-root user
- [ ] Limit container resource usage (memory, CPU)
- [ ] Regularly update base images and dependencies
- [ ] Implement container health checks

### Monitoring & Logging
- [ ] Set up error logging to external service
- [ ] Monitor failed login attempts
- [ ] Track API rate limit violations
- [ ] Log all payment processing events

---

## 📋 Pre-Deployment Checklist

- [ ] **Fix SECRET_KEY hardcode** (CRITICAL - do this first!)
- [ ] Run security audit: `pip install bandit && bandit -r app.py`
- [ ] Update all dependencies: `pip list --outdated`
- [ ] Review all TODO/FIXME comments in code
- [ ] Test backup and restore procedures
- [ ] Verify email delivery works in production
- [ ] Test payment processing with Stripe test mode
- [ ] Ensure all sensitive data is in .env (not in code)
- [ ] Review .gitignore to ensure no secrets are committed
- [ ] Document all environment variables needed for deployment

---

## 🔐 Environment Variables Required for Production

```bash
# Flask Configuration
SECRET_KEY=<generate-with-secrets.token_hex(32)>
FLASK_ENV=production

# Database
DATABASE_URL=sqlite:///instance/minipass.db

# Email Service (SendGrid/AWS SES)
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USERNAME=<your-username>
MAIL_PASSWORD=<your-password>

# Payment Processing
STRIPE_PUBLISHABLE_KEY=<production-key>
STRIPE_SECRET_KEY=<production-key>

# AI Services
GOOGLE_AI_API_KEY=<production-key>
GROQ_API_KEY=<production-key>

# Optional
SENTRY_DSN=<for-error-tracking>
```

---

## 📚 Resources

- [Flask Security Best Practices](https://flask.palletsprojects.com/en/2.3.x/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://snyk.io/blog/python-security-best-practices/)

---

**Last Updated:** 2025-11-02
**Next Review:** Before production deployment
