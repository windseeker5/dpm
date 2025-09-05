# Fix Payment Matching Logic Plan

## Problem Statement
The `match_gmail_payments_to_passes()` function in `utils.py` has two critical bugs:

1. **Bug 1**: When matching payments, if a person has multiple passports with different amounts, the function stops at the first amount mismatch instead of checking all passports for that person.
2. **Bug 2**: Need to ensure only ONE passport is marked as paid per payment, prioritizing the oldest unpaid passport when multiple matches exist.

## Environment Information (CRITICAL - ALL AGENTS MUST READ)
```
🚨 INFRASTRUCTURE ALREADY RUNNING - DO NOT REINSTALL 🚨
- Flask Server: http://localhost:5000 (ALWAYS RUNNING in debug mode)
- MCP Playwright: ALREADY INSTALLED AND CONFIGURED
- Database: SQLite at instance/minipass.db
- Virtual Environment: venv/ (already activated)
- Test Framework: Python unittest + MCP Playwright for UI tests
```

## Test Credentials (FOR ALL AGENTS)
```
Admin Login:
- URL: http://localhost:5000/admin/login
- Username: admin@app.com
- Password: admin
```

## Implementation Tasks

### Task 1: Code Analysis and Backup
**Assigned to: backend-architect**
**Instructions:**
```bash
# REMEMBER: Flask is already running on port 5000
# REMEMBER: MCP Playwright is already installed

1. Read the current implementation:
   - File: /home/kdresdell/Documents/DEV/minipass_env/app/utils.py
   - Function: match_gmail_payments_to_passes() (lines 932-1109)

2. Create a backup:
   - Save current function to: backup_match_gmail_payments_YYYYMMDD.py

3. Document current logic flow for reference
```

### Task 2: Implement Two-Stage Matching Logic
**Assigned to: backend-architect**
**Instructions:**
```python
# Location: utils.py, function match_gmail_payments_to_passes()
# Lines to modify: approximately 990-1012

NEW LOGIC:
1. Stage 1: Find all name matches
   ```python
   # Find all passports matching the name (above threshold)
   name_matches = []
   for p in unpaid_passports:
       if not p.user:
           continue
       score = fuzz.partial_ratio(name.lower(), p.user.name.lower())
       if score >= threshold:
           name_matches.append((p, score))
   ```

2. Stage 2: Filter by amount from name matches
   ```python
   # From name matches, find amount matches
   amount_matches = []
   for p, score in name_matches:
       if abs(p.sold_amt - amt) < 1:
           amount_matches.append((p, score))
   ```

3. Select best match (oldest if multiple)
   ```python
   if amount_matches:
       # Sort by created_dt (oldest first), then by score
       amount_matches.sort(key=lambda x: (x[0].created_dt, -x[1]))
       best_passport = amount_matches[0][0]
       best_score = amount_matches[0][1]
   ```

IMPORTANT: 
- Preserve all email processing logic
- Keep Gmail folder moving functionality intact
- Maintain EbankPayment logging as-is
```

### Task 3: Enhanced Debug Logging
**Assigned to: backend-architect**
**Instructions:**
```python
# Add detailed logging to understand matching process:

print(f"🔍 Processing payment: Name='{name}', Amount=${amt}")
print(f"📊 Stage 1: Found {len(name_matches)} name matches (threshold={threshold})")
for p, score in name_matches[:3]:  # Show top 3
    print(f"  - {p.user.name}: score={score}, amount=${p.sold_amt}")
    
print(f"💰 Stage 2: Found {len(amount_matches)} amount matches")
if amount_matches:
    print(f"✅ Selected: {best_passport.user.name} (created: {best_passport.created_dt})")
```

### Task 4: Create Unit Tests
**Assigned to: code-security-reviewer**
**Instructions:**
```python
# File: /home/kdresdell/Documents/DEV/minipass_env/app/test/test_payment_matching.py
# REMEMBER: Use existing test infrastructure, DO NOT install new packages

import unittest
from unittest.mock import Mock, patch
from utils import match_gmail_payments_to_passes

class TestPaymentMatching(unittest.TestCase):
    
    def test_multiple_passports_different_amounts(self):
        """Test: Person has 3 passports ($20, $30, $40), receives $30 payment"""
        # Should match only the $30 passport
        pass
    
    def test_multiple_passports_same_amount(self):
        """Test: Person has 3 passports all $25, receives one $25 payment"""
        # Should match only the oldest passport
        pass
    
    def test_no_amount_match(self):
        """Test: Person found but no passport matches the amount"""
        # Should create NO_MATCH entry
        pass
    
    def test_fuzzy_name_matching(self):
        """Test: Payment from 'John Smith' matches 'Jon Smyth' passport"""
        # Should match if score >= threshold
        pass

# Run with:
# cd /home/kdresdell/Documents/DEV/minipass_env/app
# python -m unittest test.test_payment_matching -v
```

### Task 5: Integration Testing with MCP Playwright
**Assigned to: flask-ui-developer**
**Instructions:**
```python
# File: /home/kdresdell/Documents/DEV/minipass_env/app/test/test_payment_ui.py
# REMEMBER: MCP Playwright is ALREADY INSTALLED - use it directly

# Test flow:
1. Navigate to http://localhost:5000/admin/login
2. Login with: admin@app.com / admin
3. Create test passports:
   - 3 for "John Doe" with different amounts ($20, $30, $40)
   - 2 for "Jane Smith" with same amount ($25)
4. Navigate to payment matching section
5. Trigger payment processing
6. Verify only correct passports are marked as paid

# Use MCP Playwright browser commands:
- mcp__playwright__browser_navigate
- mcp__playwright__browser_type
- mcp__playwright__browser_click
- mcp__playwright__browser_snapshot
```

### Task 6: Manual Testing Checklist
**Assigned to: ui-designer** (for visual verification)
**Instructions:**
```
REMEMBER: Everything is already running!
- Flask: http://localhost:5000
- Login: admin@app.com / admin

Test Scenarios:
□ Create 5 passports for "Test User" with amounts: $10, $20, $20, $30, $40
□ Process payment for "Test User" $20
  - Verify: Only ONE $20 passport marked as paid (the older one)
□ Process payment for "Test User" $30  
  - Verify: The $30 passport marked as paid
□ Process payment for "Test User" $50
  - Verify: No match found, payment logged as NO_MATCH
□ Check email logs show correct matching decisions
```

## Rollback Plan
If issues occur:
1. Restore from backup: `backup_match_gmail_payments_YYYYMMDD.py`
2. Restart Flask (it auto-reloads in debug mode)
3. Clear test data from database if needed

## Success Criteria
- [x] Multiple passports for same person are all checked
- [x] Only ONE passport marked as paid per payment
- [x] When multiple matches exist, oldest is selected
- [x] All existing functionality preserved
- [x] Debug logs clearly show matching logic
- [x] All unit tests pass
- [x] UI tests confirm correct behavior

## Critical Reminders for ALL Agents
```
⚠️ DO NOT:
- Install Flask (already running on port 5000)
- Install Playwright (MCP Playwright already configured)
- Create new virtual environments
- Change database configuration
- Modify email server settings

✅ DO:
- Use existing Flask at http://localhost:5000
- Use MCP Playwright browser tools directly
- Run tests in existing venv
- Use admin@app.com / admin for testing
- Save all tests in /test folder
```

## Execution Order
1. Task 1: Backup current code
2. Task 2: Implement new matching logic
3. Task 3: Add debug logging
4. Task 4: Create unit tests
5. Task 5: Run integration tests
6. Task 6: Manual verification

## Notes
- The fix is approximately 30-40 lines of code changes
- Most changes are in lines 990-1012 of utils.py
- Preserve all peripheral functionality (email parsing, folder moving, logging)