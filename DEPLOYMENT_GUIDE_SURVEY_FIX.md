# Deployment Guide: Survey Email Template Fix + French Survey

## What This Deployment Includes

1. **French 8-Question Survey Template** - Ready-to-use survey for client feedback
2. **Email Template Preview Fix** - Fixes broken hero images in preview
3. **Jinja2 Variable Support** - Proper dynamic variable rendering in survey emails

## Affected Clients

- **LinkDocking** (VPS Docker container)
- **DukeBeck** (VPS Docker container)

## Pre-Deployment Checklist

- [ ] Test in dev environment (localhost)
- [ ] Commit code changes to git
- [ ] Push to main branch
- [ ] Backup client databases before deployment

## Deployment Steps

### Step 1: Update Code on Client Containers

SSH into each client's VPS and update the code:

```bash
# SSH into client VPS
ssh user@linkdocking-server  # or dukebeck-server

# Navigate to app directory
cd /path/to/minipass/app

# Pull latest code from git
git pull origin main

# Check files updated
git log -1 --stat
```

**Expected files changed:**
- `utils.py` (Jinja2 rendering in get_email_context)
- `app.py` (Preview merge fix + hero_cid_map)
- `migrations/add_french_survey_and_fix_email_templates.py` (NEW)
- Email templates (if any changes)

### Step 2: Run Database Migration

Still on the client server:

```bash
# Activate virtual environment
source venv/bin/activate

# Run migration script
python3 migrations/add_french_survey_and_fix_email_templates.py
```

**Expected output:**
```
============================================================
🚀 MIGRATION: Survey Email Template Fixes + French Survey
============================================================

📋 Task 1: Adding French Survey Template
------------------------------------------------------------
✅ Successfully created French survey template
   - 8 questions (4 required, 4 optional)
   - 2 open-ended, 5 multiple choice, 1 rating scale
   - Status: Active

🖼️  Task 2: Cleaning up stale hero_image references
------------------------------------------------------------
✅ Cleaned X stale hero_image reference(s)
   (or "No stale hero_image references found")

🔧 Task 3: Ensuring Jinja2 variables in email templates
------------------------------------------------------------
✅ All email templates already use Jinja2 variables
   (or "Updated X email template(s)")

============================================================
✅ MIGRATION COMPLETED SUCCESSFULLY
============================================================
```

### Step 3: Restart Flask Application

```bash
# If using systemd
sudo systemctl restart minipass

# Or if using Docker
docker restart minipass-container

# Or if running directly
pkill -f "python app.py"
python app.py  # in screen/tmux session
```

### Step 4: Verify Deployment

1. **Check Survey Template Exists:**
   - Login to admin panel
   - Navigate to Surveys → Templates
   - Verify "Sondage d'Activité - Simple (questions)" exists
   - Should have 8 questions in French

2. **Test Email Preview:**
   - Go to any Activity → Email Templates
   - Click "Edit" on Survey Invitation
   - Click "Preview Changes"
   - **Verify:** Hero image appears (not broken)
   - **Verify:** Variables rendered (not showing {{ activity_name }})

3. **Test Sending Survey:**
   - Create a test survey for an activity
   - Send invitation to your email
   - **Verify:** Email has correct hero image
   - **Verify:** Email shows actual activity name, not {{ activity_name }}

## Rollback Procedure (If Needed)

If migration causes issues:

```bash
# Revert code
git reset --hard HEAD~1

# Manually remove French survey from database
sqlite3 instance/minipass.db
DELETE FROM survey_template WHERE name = "Sondage d'Activité - Simple (questions)";
.quit

# Restart Flask
sudo systemctl restart minipass
```

## What Changed Technically

### 1. Code Changes

**File:** `utils.py` (line ~3195-3208)
- Added Jinja2 template rendering to `get_email_context()`
- Now renders `{{ activity_name }}` and `{{ question_count }}` variables

**File:** `app.py` (line ~8223-8227)
- Fixed preview to merge customizations instead of replacing
- Added `survey_invitation: 'sondage'` to hero_cid_map (line ~8271)

### 2. Database Changes

**Table:** `survey_template`
- Adds 1 new row: French 8-question survey

**Table:** `activity.email_templates` (JSON column)
- Removes stale `hero_image` entries if files don't exist
- Ensures `intro_text` uses Jinja2 variables

## Testing Checklist

After deployment on each client:

- [ ] French survey template appears in survey templates list
- [ ] Can create new survey using French template
- [ ] Email template preview shows hero image (not broken)
- [ ] Email template preview renders variables (shows activity name, not {{ activity_name }})
- [ ] Sending survey invitation works
- [ ] Received email has correct hero image
- [ ] Received email has actual activity name (not variable literal)

## Support

If issues occur:
1. Check Flask logs: `tail -f /var/log/minipass.log` (or wherever logs are)
2. Check migration output for errors
3. Verify database changes: `sqlite3 instance/minipass.db "SELECT name FROM survey_template;"`
4. Contact dev team if needed

## Notes

- Migration is **idempotent** - safe to run multiple times
- Won't duplicate survey templates (checks if exists first)
- Won't break existing activities or surveys
- Cleans up stale data automatically
