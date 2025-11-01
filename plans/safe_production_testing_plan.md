# Safe Production Testing Plan - Email Payment Bot Testing

**Date:** November 1, 2025
**Purpose:** Test production database upgrade locally without conflicts with live production email monitoring

---

## 🎯 The Problem

**Production and local dev CANNOT run simultaneously** because:
- Both would monitor the same email inbox for incoming payments
- Both would try to process the same e-transfers
- Both would move emails to processed folders
- **RESULT:** Complete chaos, duplicate processing, data corruption

---

## ✅ The Solution: Sequential Testing

Test locally with production database while production is safely stopped, then deploy to production.

---

## 📋 Step-by-Step Testing Plan

### Step 0: Prerequisites (Already Done! ✅)
- ✅ Downloaded production backup from LHGI
- ✅ Restored production database to local dev
- ✅ Ran upgrade script: `python migrations/upgrade_production_database.py`
- ✅ Marked migrations complete: `flask db stamp head`
- ✅ Verified French survey template exists (8 questions)

---

### Step 1: Wait for Safe Shutdown Window ⏰

**TIMING IS CRITICAL:**
- ⚠️ **Wait until AFTER tomorrow's hockey game**
- Choose a low-activity time window (late evening or early morning)
- Notify LHGI customer about brief maintenance window
- Estimated downtime: 2-4 hours for testing

**Communication to Customer:**
```
Hi [Customer],

We're upgrading your Minipass system with new features tonight.
The system will be offline from [TIME] to [TIME] (approximately 2-4 hours).

New features include:
- French survey templates
- Enhanced location tracking
- Performance improvements

We'll notify you when the upgrade is complete.

Thanks for your patience!
```

---

### Step 2: Stop Production Container 🛑

**SSH into production VPS:**
```bash
# Connect to VPS
ssh user@production-vps

# Check running containers
docker ps

# Stop LHGI container
docker stop lhgi_container
# (Replace 'lhgi_container' with actual container name)

# Verify it's stopped
docker ps  # Should NOT show lhgi_container
```

**Important:** Production email payment bot is now inactive - inbox monitoring stopped.

---

### Step 3: Configure Local Email Payment Bot 📧

**On your local dev machine:**

```bash
cd ~/Documents/DEV/minipass_env/app
source venv/bin/activate

# Make sure Flask server is running on localhost:5000
flask run
```

**Configure Email Settings:**
1. Open browser: `http://localhost:5000`
2. Login as admin
3. Go to **Settings** → **Email Configuration**
4. Configure production email credentials:
   - Email address: [production email]
   - Password: [production password]
   - IMAP server: [server address]
   - IMAP port: [usually 993]
5. Enable email payment bot
6. Set monitoring interval (e.g., every 30 minutes)

**Verify Email Bot is Working:**
- Check that bot can connect to email
- Check that bot can read inbox
- Check logs for any connection errors

---

### Step 4: Test Payment Matching 💰

**Test Scenario 1: New Payment (If Possible)**
1. Have someone send a test e-transfer to production email
2. Wait for bot to process (check logs)
3. Verify payment is automatically matched
4. Verify passport is issued
5. Verify email confirmation sent

**Test Scenario 2: Review Existing Payments**
1. Go to **Payments** dashboard
2. Check that all historical payments from production are visible
3. Verify payment statuses are correct
4. Check that payment matching logs are intact

---

### Step 5: Full Feature Testing ✅

**Critical Tests (MUST PASS):**

#### A. Passport Scanning 🏒
- [ ] Open: `http://localhost:5000/scan`
- [ ] Scan QR codes from production passports
- [ ] Verify redemption works correctly
- [ ] Check "uses remaining" decrements properly
- [ ] **THIS IS CRITICAL FOR HOCKEY GAME!**

#### B. Dashboard & KPIs 📊
- [ ] Check: `http://localhost:5000/dashboard`
- [ ] Verify all KPIs display correctly
- [ ] Check production data shows up
- [ ] Verify revenue calculations are accurate
- [ ] Check activity summaries

#### C. Images & Uploads 🖼️
- [ ] View activities - verify activity images display
- [ ] Check email template customization
- [ ] Verify hero images show correctly
- [ ] Verify owner logos display
- [ ] Check that receipts are accessible

#### D. French Survey Template 📋
- [ ] Go to: `http://localhost:5000/survey-templates?show_all=true`
- [ ] Verify "Sondage d'Activité - Simple (questions)" exists
- [ ] Verify it has 8 questions
- [ ] Try creating a new survey using the French template
- [ ] Verify survey invitation email preview works

#### E. New Location Fields 📍
- [ ] Edit an activity
- [ ] Check that location fields appear:
  - Location Address (raw)
  - Location Address (formatted)
  - Location Coordinates
- [ ] Try entering a location address
- [ ] Verify it saves correctly

#### F. Email Templates ✉️
- [ ] Go to activity email template customization
- [ ] Verify Jinja2 variables are present ({{ activity_name }}, {{ question_count }})
- [ ] Preview emails
- [ ] Verify custom hero images load
- [ ] Verify owner logos load

#### G. Financial Reports 💵
- [ ] Check income/expense reports
- [ ] Verify receipts are accessible
- [ ] Try exporting to CSV
- [ ] Verify data is intact

#### H. Data Integrity 🔍
- [ ] Check all passports from production are visible
- [ ] Check all signups from production are visible
- [ ] Check all users from production are visible
- [ ] Verify no data was lost during migration

---

### Step 6: Monitor Email Bot Performance 📈

**While testing, monitor:**
- Email connection stability
- Payment matching accuracy
- Email processing speed
- Any error messages in logs

**Check Logs:**
```bash
# View Flask logs for email bot activity
# Look for patterns like:
# - "Email payment bot is ENABLED"
# - "Checking for new payments..."
# - "Found payment: $XX from user@email.com"
# - "Matched payment to signup ID: XX"
```

---

### Step 7: Decision Point - Ready for Production? 🚀

**If ALL tests pass:**
- ✅ Payment matching works
- ✅ Passport scanning works
- ✅ All images display
- ✅ French survey exists
- ✅ No data corruption
- ✅ Email bot is stable

**→ PROCEED TO PRODUCTION DEPLOYMENT**

**If ANY test fails:**
- ❌ Fix issues locally first
- ❌ DO NOT deploy to production
- ❌ Restore production from backup if needed
- ❌ Contact user for guidance

---

### Step 8: Deploy to Production 🎉

**When confident everything works:**

```bash
# SSH into production VPS
ssh user@production-vps
cd /path/to/lhgi_app

# Create backup FIRST (critical!)
docker exec lhgi_container cp instance/minipass.db instance/minipass.db.backup_before_upgrade_$(date +%Y%m%d_%H%M%S)

# Pull latest code
docker exec lhgi_container git pull origin main

# Run upgrade commands
docker exec lhgi_container bash -c "source venv/bin/activate && python migrations/upgrade_production_database.py"
docker exec lhgi_container bash -c "source venv/bin/activate && flask db stamp head"

# Restart container
docker restart lhgi_container

# Verify container started
docker ps  # Should show lhgi_container running

# Check logs for errors
docker logs lhgi_container --tail 50
```

**Immediately After Deployment:**
1. Test app loads: `https://lhgi.yourdomain.com`
2. Test passport scanning
3. Check dashboard loads
4. Verify email bot resumes monitoring
5. Monitor logs for 30 minutes

---

### Step 9: Notify Customer ✅

**Success Message:**
```
Hi [Customer],

Your Minipass upgrade is complete!

New features now available:
✅ French survey templates (8 questions)
✅ Enhanced location tracking for activities
✅ Performance improvements
✅ Bug fixes

Everything is running smoothly. Let us know if you have any questions!
```

---

## 🔄 Rollback Plan (If Something Goes Wrong)

**If production deployment fails:**

```bash
# SSH into production VPS
ssh user@production-vps

# Stop container
docker stop lhgi_container

# Restore database from backup
docker exec lhgi_container cp instance/minipass.db.backup_before_upgrade_YYYYMMDD instance/minipass.db

# Revert code (if needed)
docker exec lhgi_container git reset --hard HEAD~1

# Restart container
docker restart lhgi_container

# Verify old version is running
docker logs lhgi_container --tail 50
```

---

## 📊 Testing Checklist Summary

**Before Starting:**
- [ ] Hockey game is over
- [ ] Customer notified about maintenance window
- [ ] Production container stopped
- [ ] Local dev is running with production database

**During Testing:**
- [ ] Email payment bot configured and monitoring
- [ ] All critical features tested (passport scanning, dashboard, images)
- [ ] French survey verified (8 questions)
- [ ] Location fields present
- [ ] Data integrity confirmed
- [ ] No errors in logs

**Before Production Deployment:**
- [ ] All tests passed successfully
- [ ] Confident in upgrade process
- [ ] Backup plan understood
- [ ] Rollback commands ready

**After Production Deployment:**
- [ ] Container running
- [ ] App accessible
- [ ] Passport scanning works
- [ ] Email bot resumed monitoring
- [ ] Customer notified

---

## ⚠️ Critical Reminders

1. **NEVER run production and local dev simultaneously with email bot enabled**
2. **Always backup before deploying to production**
3. **Test passport scanning first** (critical for hockey)
4. **Monitor logs** after production deployment for 30+ minutes
5. **Have rollback plan ready** in case something breaks

---

## 📝 Notes

**Production Container Details:**
- VPS: [fill in]
- Container name: [fill in]
- App path inside container: [fill in]
- Domain: [fill in]

**Email Configuration:**
- Email address: [fill in]
- IMAP server: [fill in]
- IMAP port: [fill in]

**Customer Contact:**
- Name: [fill in]
- Email: [fill in]
- Phone: [fill in]

---

**This plan ensures safe testing without conflicts and a smooth production deployment!** 🚀
