# Chatbot Failed Queries - Improvement Tracker

**Created:** 2025-01-19
**Purpose:** Track actual user questions that fail, then add targeted improvements to the system prompt.

---

## How to Use This Document

1. **When a query fails:** Add it to the "Failed Query Log" below
2. **Analyze the failure:** Understand why it failed (wrong table? Missing join? French term?)
3. **Fix iteratively:** Add few-shot examples to the system prompt in `query_engine.py` ONLY for patterns that actually fail
4. **Track improvements:** Document what was added and whether it resolved the issue

---

## Failed Query Log

### Template for New Entries

```markdown
### [YYYY-MM-DD] - Query Type: [Financial/User/Activity/Payment/Other]

**User Question (Original):**
[Exact question from user - French or English]

**Language:** [French/English]

**What Happened:**
[Error message, wrong results, or SQL that was generated]

**Expected Result:**
[What should have happened]

**Root Cause:**
[Why it failed - e.g., "AI didn't understand 'flux de trésorerie' maps to revenue calculation"]

**Fix Applied:**
[What was added to the system prompt - e.g., "Added French example for cash flow query"]

**Result After Fix:**
[Did it work? Yes/No - test with same query]
```

---

## Example Entries

### [2025-01-19] - Query Type: Financial

**User Question (Original):**
"Quel est mon flux de trésorerie ce mois?"

**Language:** French

**What Happened:**
Generated SQL only queried passport table, ignored income and expense tables.

**Expected Result:**
Should calculate: SUM(passport.sold_amt WHERE paid=1) + SUM(income.amount) - SUM(expense.amount)

**Root Cause:**
AI doesn't know that "flux de trésorerie" (cash flow) requires all 3 tables.

**Fix Applied:**
Added few-shot example to system prompt:
```python
Question: "Quel est mon flux de trésorerie ce mois?"
Answer: SELECT (SELECT COALESCE(SUM(sold_amt), 0) FROM passport WHERE paid = 1 AND DATE(paid_date) >= DATE('now', 'start of month')) + (SELECT COALESCE(SUM(amount), 0) FROM income WHERE DATE(date) >= DATE('now', 'start of month')) - (SELECT COALESCE(SUM(amount), 0) FROM expense WHERE DATE(date) >= DATE('now', 'start of month')) as flux_tresorerie
```

**Result After Fix:**
✅ Works correctly

---

## Actual Failed Queries (Add Below)

### [Date] - Query Type: [Type]

*No failed queries logged yet. This section will be populated as beta users test the chatbot.*

---

## Improvement History

Track all prompt improvements made based on real failures:

| Date | Improvement | Reason | Impact |
|------|------------|--------|--------|
| 2025-01-19 | Simplified system prompt, removed preprocessing | Over-engineering caused issues | Baseline established |
| | | | |

---

## Notes for Future Improvements

- Focus on **real user queries that fail**, not predicted failures
- Add few-shot examples **only when patterns emerge** (2-3 similar failures)
- Keep system prompt **as simple as possible**
- Trust Gemini 2.0's multilingual capabilities
- Monitor QueryLog table for patterns of failed queries

---

## Query Success Metrics

Track success rate over time:

- **Week 1 (Baseline):** [Calculate from QueryLog after first week]
- **Week 2:** [Update after improvements]
- **Week 3:** [Continue tracking]

**Target:** 85%+ success rate for both French and English queries

---

**Last Updated:** 2025-01-19
