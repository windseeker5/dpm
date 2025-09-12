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
