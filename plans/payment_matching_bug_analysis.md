# Payment Matching Bug Analysis - Stéphane Picard Case

**Date:** September 11, 2025  
**Reported By:** User  
**Analyzed By:** Claude Code Assistant

## Executive Summary

A critical bug in the payment matching algorithm caused Stéphane Picard's $50 e-transfer payment to be incorrectly matched to another customer (Stephane Cayer), leaving Picard's passport showing as unpaid despite successful payment and email processing.

## The Incident

### Timeline of Events
1. **Sept 5, 2025**: Stephane Cayer creates passport #57 for $50 (Hockey)
2. **Sept 8, 2025**: Stéphane Picard creates passport #60 for $50 (Hockey) 
3. **Sept 8, 2025**: Stéphane Picard sends $50 e-transfer payment
4. **Sept 10, 2025**: Payment bot processes the email:
   - Finds Picard's payment email
   - Incorrectly matches it to Cayer's passport
   - Moves email to "PaymentProcessed" folder
   - Marks wrong passport as paid

### Current State
- **Stéphane Picard (Passport #60)**: Shows UNPAID (but actually paid $50)
- **Stephane Cayer (Passport #57)**: Shows PAID (but never paid)
- **Email**: Moved to PaymentProcessed folder
- **Database**: EbankPayment record #18 shows incorrect match

## Root Cause Analysis

### The Bug in Detail

The payment matching algorithm (`utils.py:match_gmail_payments_to_passes()`) has a critical flaw in its matching logic:

#### Current Algorithm Flow:
1. **Stage 1**: Find all passports with names matching above threshold (85%)
   - "Stephane Picard" vs "Stephane Cayer" = 85.71% match
   - Both names pass because they share "Stephane"

2. **Stage 2**: From name matches, find amount matches
   - Both passports = $50
   - Both pass this filter

3. **Stage 3**: Select "best" match
   - Algorithm sorts by creation date (oldest first)
   - Picks Cayer's passport (Sept 5) over Picard's (Sept 8)

### Why This Is Wrong

The algorithm makes several incorrect assumptions:
1. **Partial name matching is sufficient**: It treats "Stephane" as enough similarity
2. **Oldest passport is best**: Assumes earlier created passports should be matched first
3. **No exact match priority**: Doesn't prioritize exact or near-exact name matches
4. **No ambiguity detection**: Doesn't flag cases where multiple valid matches exist

### Database Evidence

```sql
-- EbankPayment Record #18
bank_info_name: "Stephane Picard"
bank_info_amt: 50.00
matched_pass_id: 57 (Wrong - this is Cayer's)
matched_name: "Stephane Cayer" 
name_score: 85.7142857142857
result: "MATCHED"
```

## Impact Assessment

### Immediate Impact
- Customer frustration (Picard shows as unpaid despite paying)
- Accounting errors (Cayer shows as paid without paying)
- Trust issues with automated payment system

### Potential Wider Impact
- This bug affects ANY situation where:
  - Multiple customers have similar names
  - They owe the same amount
  - Payments are processed in different order than passport creation

## Proposed Solution

### Phase 1: Immediate Fix (Database Correction)

1. **Correct the existing data**:
   ```sql
   -- Mark Picard's passport as paid
   UPDATE passport SET paid = 1, paid_date = '2025-09-10 15:30:01' WHERE id = 60;
   
   -- Mark Cayer's passport as unpaid (if he hasn't actually paid)
   UPDATE passport SET paid = 0, paid_date = NULL WHERE id = 57;
   
   -- Update EbankPayment record to reflect correct match
   UPDATE ebank_payment 
   SET matched_pass_id = 60, 
       matched_name = 'Stéphane Picard',
       note = 'Corrected: Originally mismatched to passport #57'
   WHERE id = 18;
   ```

### Phase 2: Algorithm Enhancement

#### New Matching Logic:
```python
def match_gmail_payments_to_passes():
    # ... existing code ...
    
    for match in matches:
        name = match["bank_info_name"]
        amt = match["bank_info_amt"]
        
        # NEW: Try exact match first
        exact_matches = []
        fuzzy_matches = []
        
        for p in unpaid_passports:
            if not p.user:
                continue
                
            # Calculate match score
            score = fuzz.ratio(name.lower(), p.user.name.lower())
            
            # NEW: Categorize matches
            if score >= 95:  # Near-exact match
                exact_matches.append((p, score))
            elif score >= threshold:  # Fuzzy match
                fuzzy_matches.append((p, score))
        
        # NEW: Prioritize exact matches
        candidates = exact_matches if exact_matches else fuzzy_matches
        
        # Filter by amount
        amount_matches = [
            (p, score) for p, score in candidates 
            if abs(p.sold_amt - amt) < 1
        ]
        
        # NEW: Handle ambiguous matches
        if len(amount_matches) > 1:
            # Check if all matches have similar scores
            scores = [score for _, score in amount_matches]
            if max(scores) - min(scores) < 5:  # All similar scores
                # Flag for manual review
                create_manual_review_entry(match, amount_matches)
                continue
        
        # Select best match (highest score, then oldest)
        if amount_matches:
            amount_matches.sort(key=lambda x: (-x[1], x[0].created_dt))
            best_passport = amount_matches[0][0]
            # ... rest of processing ...
```

### Phase 3: Additional Safeguards

1. **Enhanced Logging**:
   - Log all matching decisions with scores
   - Track why specific matches were chosen
   - Alert on ambiguous matches

2. **Manual Review Queue**:
   - Create admin interface for reviewing ambiguous matches
   - Email notifications for matches below confidence threshold
   - Ability to manually correct mismatches

3. **Additional Validation**:
   - Consider email address matching (if available)
   - Implement "payment window" logic (payments likely within X days of passport creation)
   - Add customer confirmation emails for matched payments

### Phase 4: Testing & Validation

1. **Unit Tests**:
   - Test exact name matching priority
   - Test ambiguous match detection
   - Test various name similarity scenarios

2. **Integration Tests**:
   - Test with real historical data
   - Verify no regression on correctly matched payments

3. **Manual Verification**:
   - Review last 30 days of payment matches
   - Identify any other potential mismatches

## Prevention Measures

### Short-term
1. Increase name matching threshold from 85% to 90%
2. Add daily report of all payment matches for manual review
3. Send confirmation emails to customers when payments are matched

### Long-term
1. Implement machine learning model for payment matching
2. Add unique payment reference codes to each passport
3. Integrate with bank API for more accurate payment data

## Rollout Plan

1. **Day 1**: 
   - Fix database for Picard/Cayer issue
   - Deploy emergency threshold increase (85% → 90%)

2. **Day 2-3**:
   - Implement and test new matching algorithm
   - Add logging enhancements

3. **Day 4-5**:
   - Deploy new algorithm to staging
   - Run parallel testing with production data

4. **Day 6-7**:
   - Deploy to production
   - Monitor closely for first week

## Success Metrics

- Zero payment mismatches in first month after deployment
- <2% of payments requiring manual review
- 100% accuracy for exact name matches
- Customer satisfaction improvement

## Appendix: Technical Details

### Affected Files
- `utils.py`: Function `match_gmail_payments_to_passes()` (lines 1106-1299)
- `models.py`: EbankPayment model
- `app.py`: Payment processing endpoints

### Database Tables Involved
- `passport`: Stores passport/pass information
- `user`: Stores customer information  
- `ebank_payment`: Stores payment matching history

### Current Settings
- `BANK_EMAIL_NAME_CONFIDANCE`: 85 (threshold for name matching)
- `GMAIL_LABEL_FOLDER_PROCESSED`: "PaymentProcessed"

---

**Document Version:** 1.0  
**Last Updated:** September 11, 2025