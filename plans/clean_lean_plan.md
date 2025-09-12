# Production Cleanup Plan for Minipass Application

**Created**: 2025-09-12  
**Purpose**: Clean and optimize the application for production deployment  
**Safety**: Create a git commit before executing any cleanup commands

## 🟢 LOW RISK - Safe to Delete (Highly Recommended)

### 1. Python Cache Files
- **Target**: All `__pycache__` directories and `*.pyc`, `*.pyo` files
- **Count**: ~685 __pycache__ directories found
- **Impact**: None - Python automatically regenerates these
- **Space saved**: ~50-100MB
- **Commands**:
```bash
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -o -name "*.pyo" -exec rm -f {} +
```

### 2. Virtual Environment
- **Target**: `venv/` directory
- **Current size**: 1.2GB
- **Impact**: None if deploying via Docker container
- **Space saved**: 1.2GB (biggest savings!)
- **Command**: `rm -rf venv/`
- **Recovery**: `python -m venv venv && source venv/bin/activate && pip install -r requirements.txt`

### 3. Development/Debug Files
- **Files to delete**:
  - `debug_email_templates.py` - Development utility
  - `payment_matching_integration_report.py` - Development report
  - `remove_background.py` - Utility script
  - `test_email_templates_fix.py` - Already marked for deletion in git
- **Impact**: None - these are development tools only
- **Space saved**: ~10KB
- **Command**: 
```bash
rm -f debug_email_templates.py
rm -f payment_matching_integration_report.py
rm -f remove_background.py
rm -f test_email_templates_fix.py
```

### 4. Backup Files
- **Python backups**:
  - `utils_backup_20250912_082649.py`
- **CSS backups**:
  - `static/minipass.css.backup`
- **Template backups** (3 folders):
  - `templates/email_templates_backup_20250911_193454/`
  - `templates/email_templates_backup_20250911_203702/`
  - `templates/email_templates_backup_20250912_080835/`
- **Database backups** in `instance/`:
  - `minipass.db.backup_20250911_193454` (455KB)
  - `minipass.db.backup_20250911_203702` (455KB)
  - `minipass.db.backup_20250912_080835` (475KB)
  - `minipass_bk_ken.db` (455KB)
- **Impact**: None - you have git history
- **Space saved**: ~2-3MB
- **Commands**:
```bash
rm -f utils_backup_*.py
rm -f static/*.backup
rm -rf templates/email_templates_backup_*
rm -f instance/*.backup_*
rm -f instance/minipass_bk_ken.db
```

### 5. Playwright Test Artifacts
- **Target**: `.playwright-mcp/` directory
- **Contents**: Test screenshots and traces
- **Impact**: None - test artifacts only
- **Space saved**: ~5-10MB
- **Command**: `rm -rf .playwright-mcp/`

### 6. Git Deleted Files (Already in staging)
- **Already deleted** (showing in git status):
  - Multiple files in `static/uploads_bk_ken/`
  - Various SVG/PNG assets no longer used
  - `INDIVIDUAL_SAVE_VERIFICATION.md`
- **Action**: These will be removed with next commit

## 🟡 MEDIUM RISK - Review Before Deleting

### 1. Documentation Files
- **Development docs**:
  - `.claude/` folder - Claude AI session data and wireframes
  - `docs/` folder - Various documentation
  - `README.md` - Keep if open source
  - `HOW_TO_UPGRADE_CONTAINER.md` - Deployment guide
- **Impact**: Loss of documentation (have backups)
- **Space saved**: ~200KB
- **Recommendation**: Keep `CLAUDE.md` for maintenance

### 2. Static Uploads
- **Target**: `static/uploads/` directory
- **Current size**: 18MB
- **Impact**: May contain user-uploaded content
- **Recommendation**: Review contents first, migrate important files

### 3. Development Configuration
- **`.git/` directory**
- **Impact**: Removes version control from container
- **Space saved**: Variable (check with `du -sh .git`)
- **Recommendation**: Remove only if deploying via CI/CD

### 4. Plans Folder
- **Target**: `plans/` directory (except this file!)
- **Impact**: Loss of planning documents
- **Recommendation**: Keep for reference or backup elsewhere

## 🔴 HIGH RISK - DO NOT DELETE

### Critical Application Files
- ✅ `app.py` - Main application (66k lines)
- ✅ `models.py` - Database models
- ✅ `utils.py` - Business logic
- ✅ `config.py` - Configuration
- ✅ `decorators.py` - Authentication decorators
- ✅ `kpi_renderer.py` - KPI functionality
- ✅ `utils_email_defaults.py` - Email templates
- ✅ `init_db.py` - Database initialization
- ✅ `requirements.txt` or `Pipfile` - Dependencies

### Essential Directories
- ✅ `templates/` - Jinja2 templates (except backups)
- ✅ `templates/email_templates/` - Active email templates
- ✅ `templates/email_blocks/` - Email components
- ✅ `templates/partials/` - Template partials
- ✅ `static/` - Production assets (review uploads)
- ✅ `static/css/`, `static/js/` - Frontend assets
- ✅ `static/tabler/`, `static/tinymce/` - Third-party libraries
- ✅ `api/` - API blueprints
- ✅ `chatbot_v2/` - Chatbot functionality
- ✅ `migrations/` - Database migrations
- ✅ `instance/minipass.db` - Main database (549KB)
- ✅ `models/` - Model definitions
- ✅ `components/` - Application components
- ✅ `config/` - Configuration files
- ✅ `prompts/` - AI prompts if used

### Required Configuration
- ✅ `CLAUDE.md` - AI assistant context
- ✅ `.env` or environment configuration files
- ✅ Any `*.ini` or `*.conf` files

## 📋 Execution Steps

### Step 1: Create Safety Backup
```bash
# Create git commit
git add -A
git commit -m "Pre-cleanup backup - before production optimization"

# Optional: Create tar backup
tar -czf ../minipass_backup_$(date +%Y%m%d_%H%M%S).tar.gz .
```

### Step 2: Execute Low-Risk Cleanup
```bash
# Remove Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -o -name "*.pyo" -exec rm -f {} +

# Remove venv (if using Docker)
rm -rf venv/

# Remove backup files
rm -f utils_backup_*.py
rm -f static/*.backup
rm -rf templates/email_templates_backup_*
rm -f instance/*.backup_*
rm -f instance/minipass_bk_ken.db

# Remove test/debug files
rm -f debug_email_templates.py
rm -f payment_matching_integration_report.py
rm -f remove_background.py

# Remove playwright artifacts
rm -rf .playwright-mcp/
```

### Step 3: Review and Execute Medium-Risk Cleanup
```bash
# After review, optionally remove:
rm -rf .claude/
rm -rf docs/  # Keep important docs
# Review static/uploads/ before deleting
```

### Step 4: Verify Application
```bash
# Test the application
curl http://localhost:5000/

# Check critical endpoints
curl http://localhost:5000/login
curl http://localhost:5000/api/health  # if exists
```

## 📊 Expected Results

### Space Savings Summary
- **Python cache**: ~50-100MB
- **Virtual environment**: 1.2GB
- **Backups and test files**: ~10MB
- **Documentation (optional)**: ~1MB
- **Total potential savings**: ~1.3GB

### File Count Reduction
- **Before**: ~1000+ files including cache
- **After**: ~200-300 essential files
- **Reduction**: ~70-80% fewer files

## ⚠️ Important Notes

1. **Database Safety**: Keep at least one recent database backup
2. **Docker Consideration**: If using Docker, venv is not needed
3. **Requirements File**: Ensure `requirements.txt` is up to date
4. **Environment Variables**: Document all required env vars
5. **Testing**: Run full test suite after cleanup
6. **Monitoring**: Watch application logs after deployment

## ✅ Post-Cleanup Checklist

- [ ] Git commit created before cleanup
- [ ] Python cache files removed
- [ ] Virtual environment removed (if using Docker)
- [ ] Backup files cleaned
- [ ] Test files removed
- [ ] Application tested and working
- [ ] Docker image builds successfully
- [ ] All endpoints responding correctly
- [ ] Database connections working
- [ ] Static assets loading properly

## 🚀 Final Production Steps

1. Run cleanup commands
2. Test application thoroughly
3. Build Docker image: `docker build -t minipass:prod .`
4. Run container: `docker run -p 5000:5000 minipass:prod`
5. Verify all functionality
6. Deploy to production environment

---

**Note**: This plan prioritizes safety. Start with LOW RISK items and test after each step. The virtual environment (venv) removal provides the biggest space savings at 1.2GB.