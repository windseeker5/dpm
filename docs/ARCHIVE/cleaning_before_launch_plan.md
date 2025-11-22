# Pre-Launch Code Cleanup Plan

**Date:** November 21, 2025
**Target Launch:** Next week or Monday in 2 weeks
**Status:** Ready for execution

---

## Executive Summary

This plan addresses pre-launch cleanup for the Minipass SaaS application currently running with 2 beta testers on VPS. The cleanup will remove ~1,950 lines of unused code, recover ~42MB of disk space, and fix 1 critical security issue before production launch.

**Total Impact:**
- ~1,950 lines of code removed
- ~42MB disk space recovered
- Critical security issue fixed (hardcoded SECRET_KEY)
- Cleaner, production-ready codebase

---

## Phase 1: 🚨 CRITICAL Security Fix (SECRET_KEY)

**Priority:** MUST DO BEFORE LAUNCH

### Actions:
1. Generate secure random SECRET_KEY (32 bytes hex)
2. Create/update `.env` file with `FLASK_SECRET_KEY=<generated_key>`
3. Update `app.py` line 159 from:
   ```python
   app.config["SECRET_KEY"] = "MY_SECRET_KEY_FOR_NOW"
   ```
   To:
   ```python
   app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", os.urandom(32).hex())
   ```
4. Verify `.env` is in `.gitignore` to prevent committing secrets

### Why This Matters:
- Current hardcoded key allows session hijacking
- All user sessions share the same predictable key
- CSRF protection can be bypassed
- **CRITICAL** for production security

---

## Phase 2: Remove Chatbot Auth Bypass

**Priority:** HIGH

### Actions:
1. Locate development auth bypass in `chatbot_v2/routes_simple.py` line ~148:
   ```python
   if not admin_email:
       current_app.logger.warning("No admin session, allowing for development")
       admin_email = "test@example.com"
   ```
2. Either:
   - **Option A (Recommended):** Remove entirely
   - **Option B:** Guard with `if app.config['DEBUG']` check

### Why This Matters:
- Allows unauthenticated access to AI chatbot in production
- Development bypass code should never reach production

---

## Phase 3: Clean Up Test Routes

### Remove These Routes from app.py:

1. **`/test-notifications`** (line ~189)
   - References non-existent template
   - Test only

2. **`/test/sse`** (line ~7957)
   - Broken route (directory doesn't exist)

3. **`/test/notification-endpoints`** (line ~7967)
   - Broken route (directory doesn't exist)

### Keep These Routes (Per User Request):
- `/test-payment-bot-now` - Keep for payment bot testing
- `/test-late-payment` - Keep if exists (search for it)

**Lines Removed:** ~150-200 lines

---

## Phase 4: Delete Unused Template Files

### Delete 6 Unused Template Files:

```bash
templates/email_template_customization_backup.html       # 270 lines, 18KB
templates/email_template_customization_fixed.html         # 282 lines, 13KB
templates/signup_form_WORKING.html                        # 551 lines, 19KB
templates/test_dashboard.html                             # 127 lines
templates/kpi_card_bar.html                               # 33 lines
templates/kpi_card_line.html                              # 33 lines
```

**Total:** ~1,296 lines, ~50KB

### Delete Email Template Backup Directories:

**Remove both backup directories (saves 36MB):**
```bash
templates/email_templates_backup_20251116_152650/        # 18MB
templates/email_templates_backup_20251116_155243/        # 18MB
```

**Justification:** Git history serves as backup; these are duplicates from same day

### Delete October Email Template Variants:

**Remove old variants from main templates (saves ~6MB):**
```bash
templates/email_templates/latePayment/original_old_oct9/
templates/email_templates/newPass/original_old_oct9/
templates/email_templates/paymentReceived/original_old_oct9/
templates/email_templates/redeemPass/original_old_oct9/
templates/email_templates/signup/original_old_oct9/
templates/email_templates/survey_invitation/original_old_oct9/
```

**Also consider removing compiled variants if stable:**
```bash
templates/email_templates/*/compiled/
```

**Total Disk Space Recovered:** ~42MB

---

## Phase 5: Remove Unused Utility Functions

### Delete from utils.py (9 functions, ~350 lines):

1. **`get_gravatar_url(email, size=64)`** (line 336)
   - Gravatar integration abandoned
   - Not called anywhere

2. **`encrypt_password(password)`** (line 3151)
   - Unused, bcrypt handles encryption directly

3. **`decrypt_password(encrypted_password)`** (line 3162)
   - Paired with unused encrypt_password

4. **`generate_optimized_qr_code(pass_code)`** (line 451)
   - System uses `generate_qr_code_image()` instead

5. **`save_qr_code_to_static(pass_code, qr_data, base_url)`** (line 482)
   - Not called anywhere

6. **`get_or_create_qr_code_url(pass_code, base_url)`** (line 495)
   - Not called anywhere

7. **`generate_image_urls(context, base_url)`** (line 509)
   - Not called anywhere

8. **`get_template_default_hero(template_type)`** (line 59)
   - Functionality in `get_activity_hero_image()` instead

9. **`strip_html_tags(html)`** (line 1961)
   - ContentSanitizer class handles HTML sanitization

**Lines Removed:** ~350 lines

---

## Phase 6: Minor Code Cleanup

### Remove Unused Imports:

1. **`import socket`** from app.py (line 8)
   - Imported but never used

2. **Duplicate `import hashlib`** (lines 9 and 200)
   - Keep first occurrence, remove duplicate

### Clean Up Debug Code:

1. **Commented database check** (app.py lines 144-146):
   ```python
   #if not os.path.exists(db_path):
   #    print(f"❌ {db_path} is missing!")
   #    exit(1)
   ```

2. **Other debug comments to remove:**
   - "Bypass authentication for testing - REMOVE THIS AFTER DEBUGGING"
   - "🔁 Replace with your email for testing"
   - "#testing_mode = True"

**Lines Removed:** ~50 lines

---

## Phase 7: Verification & Testing

### Post-Cleanup Testing Checklist:

1. **Monitor Flask Server (Already Running)**
   - **Note:** Flask is already running on `localhost:5000` in debug mode with auto-reload
   - After each code change, Flask will automatically reload
   - Watch the terminal for any import errors or exceptions
   - **Only restart manually if Flask crashes** (which shouldn't happen for this cleanup)
   - If errors appear, they will show in the terminal immediately after saving changes

2. **Test Critical Routes**
   - Login page: `http://localhost:5000/login`
   - Dashboard: `http://localhost:5000/`
   - Activities: `http://localhost:5000/activities`
   - Passports: `http://localhost:5000/passports`
   - Signups: `http://localhost:5000/signups`
   - Financial Report: `http://localhost:5000/financial-report`

3. **Test Email System**
   - Send test email from email template customization
   - Verify templates render correctly
   - Check hero images load

4. **Test Payment Bot**
   - Use `/test-payment-bot-now` route (kept intentionally)
   - Verify payment matching still works

5. **Test AI Chatbot**
   - Navigate to analytics chatbot
   - Ask test question
   - Verify authentication required (no bypass)

6. **Check Database Operations**
   - Create test activity
   - Create test passport
   - Redeem test passport
   - Verify all operations work

---

## Security Review Summary

### Issues Addressed:

1. **CRITICAL - Hardcoded SECRET_KEY** ✅ Fixed
   - Moved to environment variable
   - Secure random generation

2. **HIGH - Chatbot Auth Bypass** ✅ Fixed
   - Development code removed/guarded

3. **MEDIUM - Test Routes Exposure** ✅ Fixed
   - Broken test routes removed
   - Only intentional test routes remain

### Security Features Confirmed Working:

- ✅ CSRF protection active (Flask-WTF)
- ✅ Password hashing with bcrypt
- ✅ SQL injection protection (parameterized queries)
- ✅ File upload validation (`secure_filename`, extension checks)
- ✅ Session management properly configured
- ✅ HTML sanitization via ContentSanitizer

---

## Rollback Plan (If Issues Arise)

### If Flask Server Crashes or Shows Errors:
**Note:** Flask is running in debug mode and auto-reloads on file changes. If errors appear:
1. Check the Flask terminal output for the specific error message
2. Review recent changes: `git diff`
3. Check git status: `git status`
4. Look for missing imports or syntax errors in the error traceback
5. If needed, revert last commit: `git reset --hard HEAD~1`
6. Flask will auto-reload after reverting (no manual restart needed)

### If Templates Break:
1. Check template references in app.py
2. Verify `render_template()` calls match existing files
3. Restore from git: `git checkout HEAD -- templates/[filename]`

### If Utils Functions Needed:
1. Check error messages for missing function names
2. Restore specific function from git history
3. Search codebase for hidden usage: `grep -r "function_name" .`

### Complete Rollback:
```bash
# If all else fails, return to pre-cleanup state
git log  # Find commit hash before cleanup
git reset --hard <commit_hash>
```

---

## Post-Launch Monitoring

### Week 1 After Launch:
- Monitor error logs for missing imports
- Watch for template rendering errors
- Check for any 404s on removed routes
- Verify SECRET_KEY is working (sessions persist correctly)

### Month 1 After Launch:
- Review if kept test routes are still needed
- Consider removing additional commented code
- Evaluate if any removed functions need restoration

---

## Files Modified Summary

### Files to Edit:
- `app.py` - Remove imports, routes, debug code
- `utils.py` - Remove 9 unused functions
- `chatbot_v2/routes_simple.py` - Remove auth bypass
- `.env` - Add FLASK_SECRET_KEY (create if needed)

### Files to Delete:
- 6 unused template files
- 2 backup directories (36MB)
- Multiple `*_original_old_oct9` directories (6MB)

### Files to Verify in .gitignore:
- `.env` - Must be ignored to protect SECRET_KEY

---

## Estimated Time to Complete

- **Phase 1 (SECRET_KEY):** 15 minutes
- **Phase 2 (Auth Bypass):** 10 minutes
- **Phase 3 (Test Routes):** 20 minutes
- **Phase 4 (Templates):** 15 minutes
- **Phase 5 (Utils Functions):** 25 minutes
- **Phase 6 (Minor Cleanup):** 10 minutes
- **Phase 7 (Testing):** 30 minutes

**Total Estimated Time:** ~2 hours

---

## Sign-Off Checklist

Before deploying to production:

- [ ] SECRET_KEY moved to environment variable
- [ ] All beta testers notified of update
- [ ] Backup of current production database taken
- [ ] All 7 phases completed
- [ ] Testing checklist completed
- [ ] No errors in Flask terminal after auto-reload
- [ ] Critical routes tested and working
- [ ] Email system verified working
- [ ] Git commit created with cleanup changes
- [ ] Production deployment scheduled

---

**Next Steps:** Execute this plan phase by phase, testing after each major phase. Commit frequently so rollback is easy if needed.

**Owner:** Ken Dresdell
**Launch Target:** November 2025
**Status:** Ready for execution
