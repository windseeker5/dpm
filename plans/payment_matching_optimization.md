# Payment Matching Optimization Plan

**Date:** September 13, 2025
**Author:** Claude Code Assistant
**Status:** Ready for Implementation

## Executive Summary
Optimize the payment matching function by filtering by exact amount first, then applying name matching only to those candidates. This simple change will improve performance by 70-90% while maintaining the same accuracy and keeping the threshold configurable.

## Current vs Proposed Approach

### Current Algorithm:
1. Fetches ALL unpaid passports
2. Gets threshold from settings: `threshold = int(get_setting("BANK_EMAIL_NAME_CONFIDANCE", "85"))`
3. Computes fuzzy name match for EVERY passport
4. Filters by amount from name matches
5. Selects best match above threshold

### Proposed Algorithm:
1. Fetches ONLY unpaid passports with exact amount
2. Gets threshold from settings: `threshold = int(get_setting("BANK_EMAIL_NAME_CONFIDANCE", "85"))` **(UNCHANGED)**
3. Computes fuzzy name match for amount matches only (typically 1-3 passports)
4. Selects best match above threshold **(STILL USING SETTINGS VARIABLE)**

## Key Point: Threshold Remains Configurable

**Current code (line 1123):**
```python
threshold = int(get_setting("BANK_EMAIL_NAME_CONFIDANCE", "85"))
```

**This line stays EXACTLY the same!** The threshold is:
- Still read from database settings
- Still configurable by admin
- Still defaults to 85 if not set
- NOT hardcoded

## Performance Impact
- **Current**: ~100 fuzzy match operations per payment (all unpaid passports)
- **Proposed**: ~1-3 fuzzy match operations per payment (only same amount)
- **Expected Improvement**: 70-90% reduction in processing time
- **Real numbers**: If you have 100 unpaid passports and most amounts are unique, you go from 100 operations to 1-2 operations

## Code Changes Required
- **File to modify**: `utils.py`
- **Lines to modify**: ~15-20 lines
- **Lines to add**: ~5 lines (better logging for NO_MATCH cases)
- **Total function size**: Remains roughly the same (~200 lines)
- **Threshold handling**: NO CHANGES - continues using `get_setting()`

## Specific Implementation Changes

### 1. Keep threshold from settings (unchanged)
Line ~1123 stays exactly the same:
```python
threshold = int(get_setting("BANK_EMAIL_NAME_CONFIDANCE", "85"))
```

### 2. Change initial passport query
**Current** (line ~1154):
```python
unpaid_passports = Passport.query.filter_by(paid=False).all()
```

**Change to:**
```python
# Filter by exact amount FIRST for massive performance gain
unpaid_passports = Passport.query.filter_by(paid=False, sold_amt=amt).all()

if not unpaid_passports:
    # No passports with this exact amount
    db.session.add(EbankPayment(
        from_email=from_email,
        subject=subject,
        bank_info_name=name,
        bank_info_amt=amt,
        name_score=0,
        result="NO_MATCH",
        mark_as_paid=False,
        note=f"No unpaid passports for ${amt} - payment may have arrived before passport creation"
    ))
    continue  # Skip to next payment
```

### 3. Simplify matching logic
Remove the amount filtering step (lines ~1244-1255) since we already filtered by amount:
```python
# OLD: Filter by amount from candidates
# NEW: All candidates already have the correct amount, so just find best name match

best_match = None
best_score = 0
all_candidates = []

for p in unpaid_passports:
    if not p.user:
        continue

    normalized_passport_name = normalize_name(p.user.name)
    score = fuzz.ratio(normalized_payment_name, normalized_passport_name)

    # Track all scores for logging
    all_candidates.append((p.user.name, score, p.id))

    # Use the threshold from settings (not hardcoded!)
    if score >= threshold and score > best_score:
        best_score = score
        best_match = p
```

### 4. Improve NO_MATCH logging
When no match is found, provide better context:
```python
if not best_match:
    # Sort candidates by score for helpful logging
    all_candidates.sort(key=lambda x: x[1], reverse=True)
    top_candidates = all_candidates[:3]

    note_parts = [f"No names above {threshold}% threshold for ${amt}."]
    if top_candidates:
        candidate_strs = [f"{name} ({score}%)" for name, score, _ in top_candidates]
        note_parts.append(f"Closest matches: {', '.join(candidate_strs)}")

    db.session.add(EbankPayment(
        from_email=from_email,
        subject=subject,
        bank_info_name=name,
        bank_info_amt=amt,
        name_score=0,
        result="NO_MATCH",
        mark_as_paid=False,
        note=" ".join(note_parts)
    ))
```

## Risk Assessment

### Very Low Risk because:
1. **No logic changes** - Same threshold system, same fuzzy matching algorithm
2. **Settings system untouched** - Threshold still configurable via admin settings
3. **No data changes** - Same database schema, same models
4. **Reversible** - Can revert to old version instantly
5. **Well-tested path** - Amount filtering already exists in the code, just reordering operations

### What could go wrong:
- If there's a bug in the SQL query, some payments might not match (but would show as NO_MATCH for admin review)
- Performance improvement might be less than expected if many passports have the same amount

## Testing Plan

### Before Deployment:
1. Run existing test file: `python test_payment_fixes.py`
2. Verify threshold is still read from settings
3. Test with various threshold values (80, 85, 90) to confirm setting works

### Test Cases:
```python
# Test 1: Exact amount, good name match (should match)
Payment: "John Smith", $50
Passport: "John Smith", $50
Expected: MATCHED

# Test 2: Exact amount, poor name match (should not match)
Payment: "John Smith", $50
Passport: "Robert Jones", $50
Expected: NO_MATCH

# Test 3: No passport with amount (should not match)
Payment: "John Smith", $75
No passports for $75
Expected: NO_MATCH with note about no passports for this amount

# Test 4: Multiple passports same amount (should match best)
Payment: "Jean Francois", $50
Passport 1: "Jean-François Gagné", $50
Passport 2: "Robert Wilson", $50
Expected: MATCHED to Jean-François
```

### After Deployment:
1. Monitor first 10 payment matches
2. Check processing time in logs (should see 70-90% improvement)
3. Verify NO_MATCH cases have helpful notes for admin

## Rollback Plan
1. Keep backup of current `utils.py`: `cp utils.py utils.py.backup`
2. If any issues after deployment: `cp utils.py.backup utils.py`
3. Restart Flask server
4. Total rollback time: <1 minute

## Implementation Checklist
- [ ] Backup current `utils.py`
- [ ] Implement amount-first filtering
- [ ] Remove redundant amount filtering code
- [ ] Improve NO_MATCH logging
- [ ] Run test suite
- [ ] Deploy to development environment
- [ ] Test with real payment examples
- [ ] Monitor first batch of payments
- [ ] Document performance improvement

## Expected Outcomes
- **Performance**: 70-90% faster payment matching
- **Accuracy**: Same or better (no logic changes)
- **Admin experience**: Better NO_MATCH notes for easier manual review
- **Code quality**: Simpler, more maintainable code

## Summary
This is a pure optimization - same business logic, just executed more efficiently. The threshold remains fully configurable through settings, and the risk is minimal since we're only changing the order of operations, not the matching logic itself.

---

**Document Version:** 1.0
**Last Updated:** September 13, 2025