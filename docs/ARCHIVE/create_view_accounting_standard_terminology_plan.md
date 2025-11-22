# SQLite Views Creation Plan - Accounting-Standard Terminology

**Created:** 2025-01-19
**Status:** Ready for Implementation
**Purpose:** Create SQLite views with professional accounting terminology aligned with QuickBooks, FreshBooks, and Xero

---

## Goal

Create TWO SQLite views that:
1. Show detailed transaction ledger (like QuickBooks Transaction List)
2. Show monthly financial summary with both Cash and Accrual basis accounting
3. Use standard accounting column names
4. Include Accounts Receivable and Accounts Payable

---

## View 1: `monthly_transactions_detail`

**Purpose:** Detailed transaction ledger showing EVERY transaction (paid, unpaid, pending, etc.)

### Column Renaming for Accounting Standards

| Old Name | New Name | Reason |
|----------|----------|--------|
| `month` | `month` | Standard |
| `activity` | `account` | QuickBooks uses "Account" |
| `type` | `transaction_type` | More professional |
| `transaction_date` | `transaction_date` | Standard |
| `user_or_category` | `customer_vendor` | QuickBooks standard |
| `description` | `memo` | QuickBooks standard field |
| `amount` | `amount` | Standard |
| `status` | `payment_status` | More explicit |
| `created_by` | `entered_by` | QuickBooks uses "Entered By" |

### SQL to Create View

```sql
CREATE VIEW monthly_transactions_detail AS
SELECT
    strftime('%Y-%m', COALESCE(p.paid_date, p.created_dt)) as month,
    a.name as account,
    'Passport Sale' as transaction_type,
    COALESCE(p.paid_date, p.created_dt) as transaction_date,
    u.name as customer_vendor,
    p.notes as memo,
    p.sold_amt as amount,
    CASE WHEN p.paid = 1 THEN 'Paid' ELSE 'Unpaid' END as payment_status,
    'Passport System' as entered_by
FROM passport p
JOIN activity a ON p.activity_id = a.id
LEFT JOIN user u ON p.user_id = u.id

UNION ALL

SELECT
    strftime('%Y-%m', i.date) as month,
    a.name as account,
    'Other Income' as transaction_type,
    i.date as transaction_date,
    i.category as customer_vendor,
    i.note as memo,
    i.amount,
    CASE
        WHEN i.payment_status = 'received' THEN 'Received'
        WHEN i.payment_status = 'pending' THEN 'Pending'
        ELSE i.payment_status
    END as payment_status,
    COALESCE(i.created_by, 'System') as entered_by
FROM income i
JOIN activity a ON i.activity_id = a.id

UNION ALL

SELECT
    strftime('%Y-%m', e.date) as month,
    a.name as account,
    'Expense' as transaction_type,
    e.date as transaction_date,
    e.category as customer_vendor,
    e.description as memo,
    e.amount,
    CASE
        WHEN e.payment_status = 'paid' THEN 'Paid'
        WHEN e.payment_status = 'unpaid' THEN 'Unpaid'
        ELSE e.payment_status
    END as payment_status,
    COALESCE(e.created_by, 'System') as entered_by
FROM expense e
JOIN activity a ON e.activity_id = a.id

ORDER BY month DESC, transaction_date DESC;
```

### How to Query This View

```sql
-- See all November 2025 transactions
SELECT * FROM monthly_transactions_detail WHERE month = '2025-11';

-- See only unpaid items
SELECT * FROM monthly_transactions_detail WHERE payment_status IN ('Unpaid', 'Pending');

-- See all expenses
SELECT * FROM monthly_transactions_detail WHERE transaction_type = 'Expense';
```

---

## View 2: `monthly_financial_summary`

**Purpose:** Monthly Profit & Loss + Cash Flow Summary (combines Cash Basis and Accrual Basis)

### Columns (Accounting Standard Terminology)

**CASH BASIS (what actually happened):**
- `passport_sales` - Revenue from paid passport sales
- `other_income` - Revenue from received other income
- `cash_received` - Total cash received (passport_sales + other_income)
- `cash_paid` - Total cash paid out for expenses
- `net_cash_flow` - Net cash position (cash_received - cash_paid)

**ACCRUAL BASIS (includes pending/unpaid):**
- `passport_ar` - Unpaid passport sales
- `other_income_ar` - Pending other income
- `accounts_receivable` - Total AR (passport_ar + other_income_ar)
- `accounts_payable` - Total unpaid expenses
- `total_revenue` - Total revenue including AR (accrual basis)
- `total_expenses` - Total expenses including AP (accrual basis)
- `net_income` - True net income (accrual basis)

### SQL to Create View

```sql
CREATE VIEW monthly_financial_summary AS
WITH monthly_passports_cash AS (
    SELECT
        strftime('%Y-%m', paid_date) as month,
        activity_id,
        SUM(sold_amt) as passport_sales_cash
    FROM passport
    WHERE paid = 1 AND paid_date IS NOT NULL
    GROUP BY month, activity_id
),
monthly_passports_ar AS (
    SELECT
        strftime('%Y-%m', COALESCE(paid_date, created_dt)) as month,
        activity_id,
        SUM(sold_amt) as passport_sales_ar
    FROM passport
    WHERE paid = 0
    GROUP BY month, activity_id
),
monthly_income_cash AS (
    SELECT
        strftime('%Y-%m', date) as month,
        activity_id,
        SUM(amount) as other_income_cash
    FROM income
    WHERE payment_status = 'received'
    GROUP BY month, activity_id
),
monthly_income_ar AS (
    SELECT
        strftime('%Y-%m', date) as month,
        activity_id,
        SUM(amount) as other_income_ar
    FROM income
    WHERE payment_status = 'pending'
    GROUP BY month, activity_id
),
monthly_expenses_cash AS (
    SELECT
        strftime('%Y-%m', date) as month,
        activity_id,
        SUM(amount) as expenses_cash
    FROM expense
    WHERE payment_status = 'paid'
    GROUP BY month, activity_id
),
monthly_expenses_ap AS (
    SELECT
        strftime('%Y-%m', date) as month,
        activity_id,
        SUM(amount) as expenses_ap
    FROM expense
    WHERE payment_status = 'unpaid'
    GROUP BY month, activity_id
)
SELECT
    COALESCE(pc.month, ic.month, ec.month, par.month, iar.month, eap.month) as month,
    a.id as activity_id,
    a.name as account,

    -- CASH BASIS (what actually happened)
    COALESCE(pc.passport_sales_cash, 0) as passport_sales,
    COALESCE(ic.other_income_cash, 0) as other_income,
    COALESCE(pc.passport_sales_cash, 0) + COALESCE(ic.other_income_cash, 0) as cash_received,
    COALESCE(ec.expenses_cash, 0) as cash_paid,
    (COALESCE(pc.passport_sales_cash, 0) + COALESCE(ic.other_income_cash, 0) - COALESCE(ec.expenses_cash, 0)) as net_cash_flow,

    -- ACCRUAL BASIS (includes pending/unpaid)
    COALESCE(par.passport_sales_ar, 0) as passport_ar,
    COALESCE(iar.other_income_ar, 0) as other_income_ar,
    COALESCE(par.passport_sales_ar, 0) + COALESCE(iar.other_income_ar, 0) as accounts_receivable,
    COALESCE(eap.expenses_ap, 0) as accounts_payable,

    -- TOTAL ACCRUAL REVENUE & NET INCOME
    (COALESCE(pc.passport_sales_cash, 0) + COALESCE(par.passport_sales_ar, 0) +
     COALESCE(ic.other_income_cash, 0) + COALESCE(iar.other_income_ar, 0)) as total_revenue,
    (COALESCE(ec.expenses_cash, 0) + COALESCE(eap.expenses_ap, 0)) as total_expenses,
    ((COALESCE(pc.passport_sales_cash, 0) + COALESCE(par.passport_sales_ar, 0) +
      COALESCE(ic.other_income_cash, 0) + COALESCE(iar.other_income_ar, 0)) -
     (COALESCE(ec.expenses_cash, 0) + COALESCE(eap.expenses_ap, 0))) as net_income

FROM activity a
LEFT JOIN monthly_passports_cash pc ON a.id = pc.activity_id
LEFT JOIN monthly_passports_ar par ON a.id = par.activity_id AND COALESCE(pc.month, par.month) = par.month
LEFT JOIN monthly_income_cash ic ON a.id = ic.activity_id AND COALESCE(pc.month, par.month, ic.month) = ic.month
LEFT JOIN monthly_income_ar iar ON a.id = iar.activity_id AND COALESCE(pc.month, par.month, ic.month, iar.month) = iar.month
LEFT JOIN monthly_expenses_cash ec ON a.id = ec.activity_id AND COALESCE(pc.month, par.month, ic.month, iar.month, ec.month) = ec.month
LEFT JOIN monthly_expenses_ap eap ON a.id = eap.activity_id AND COALESCE(pc.month, par.month, ic.month, iar.month, ec.month, eap.month) = eap.month
WHERE COALESCE(pc.month, par.month, ic.month, iar.month, ec.month, eap.month) IS NOT NULL
ORDER BY month DESC, a.name;
```

### How to Query This View

```sql
-- Get November 2025 financial summary
SELECT * FROM monthly_financial_summary WHERE month = '2025-11';

-- Get cash flow for all months
SELECT month, account, cash_received, cash_paid, net_cash_flow
FROM monthly_financial_summary
ORDER BY month DESC;

-- Get accounts receivable summary
SELECT month, account, accounts_receivable, accounts_payable
FROM monthly_financial_summary
WHERE accounts_receivable > 0 OR accounts_payable > 0
ORDER BY month DESC;
```

---

## Implementation Steps

### Step 1: Test SQL in DBeaver (BEFORE creating views)

1. Copy the SELECT portion of each view (everything after `CREATE VIEW ... AS`)
2. Test in DBeaver to verify results are correct
3. Check column names and values make sense
4. Verify numbers match your expectations

### Step 2: Create Flask Migration

Once SQL is tested and working:

```bash
cd /home/kdresdell/Documents/DEV/minipass_env/app
flask db migrate -m "Add accounting-standard financial views"
```

Edit the migration file to add:

```python
def upgrade():
    # Create detailed transactions view
    op.execute("""
        CREATE VIEW monthly_transactions_detail AS
        [paste full SQL here]
    """)

    # Create financial summary view
    op.execute("""
        CREATE VIEW monthly_financial_summary AS
        [paste full SQL here]
    """)

def downgrade():
    op.execute("DROP VIEW IF EXISTS monthly_transactions_detail")
    op.execute("DROP VIEW IF EXISTS monthly_financial_summary")
```

Then run:

```bash
flask db upgrade
```

### Step 3: Update Chatbot System Prompt

Modify `chatbot_v2/query_engine.py` to tell AI about the views:

```python
CRITICAL BUSINESS RULES:
- Use the 'monthly_transactions_detail' VIEW for detailed transaction queries
- Use the 'monthly_financial_summary' VIEW for revenue, cash flow, and financial queries

CASH BASIS vs ACCRUAL BASIS:
- cash_received = money you actually received
- cash_paid = money you actually paid out
- net_cash_flow = cash_received - cash_paid
- accounts_receivable = money customers owe you (unpaid)
- accounts_payable = money you owe vendors (unpaid)
- total_revenue = cash_received + accounts_receivable
- total_expenses = cash_paid + accounts_payable
- net_income = total_revenue - total_expenses

EXAMPLE QUERIES:
- "Quels sont mes revenus ce mois?" → SELECT cash_received FROM monthly_financial_summary WHERE month = strftime('%Y-%m', 'now')
- "Show me unpaid invoices" → SELECT * FROM monthly_transactions_detail WHERE payment_status = 'Unpaid'
- "What's my cash flow?" → SELECT month, account, net_cash_flow FROM monthly_financial_summary ORDER BY month DESC
```

### Step 4: Test Chatbot Queries

Test with the questions that failed before:

- "Quels sont mes revenus ce mois-ci?" (What is my revenue this month?)
- "Quels sont mes revenus pour le dernier mois?" (What is my revenue last month?)
- "Show me my accounts receivable"
- "What is my cash flow by activity?"

---

## Benefits of This Approach

✅ **Professional Accounting Terms** - Matches QuickBooks, FreshBooks, Xero
✅ **Dual Accounting Basis** - Shows both Cash and Accrual data in one view
✅ **Complete Financial Picture** - AR, AP, Cash Flow, Net Income all in one place
✅ **Simpler AI Queries** - Chatbot just queries the views instead of complex JOINs
✅ **Export-Ready** - Views can be exported directly to accounting software
✅ **No Cartesian Product Bug** - Views use CTEs to avoid multiplication errors
✅ **Debugging Friendly** - Detailed view shows every transaction for verification

---

## Column Mapping Reference

### For Chatbot Translation (French ↔ English)

| User Term (French) | User Term (English) | Database Column |
|-------------------|---------------------|-----------------|
| Revenus / Revenu | Revenue | `cash_received` |
| Flux de trésorerie | Cash flow | `net_cash_flow` |
| Comptes clients | Accounts receivable | `accounts_receivable` |
| Comptes fournisseurs | Accounts payable | `accounts_payable` |
| Bénéfice net | Net income | `net_income` |
| Dépenses | Expenses | `cash_paid` or `total_expenses` |
| Non payé | Unpaid | `payment_status = 'Unpaid'` |
| En attente | Pending | `payment_status = 'Pending'` |

---

## Testing Checklist

- [ ] Test View 1 SQL in DBeaver - verify all transactions show up
- [ ] Test View 2 SQL in DBeaver - verify totals are correct
- [ ] Check November 2025: $688 revenue, $120 expenses, $568 net cash flow
- [ ] Verify unpaid expense shows up in detailed view
- [ ] Create Flask migration
- [ ] Run migration: `flask db upgrade`
- [ ] Verify views exist: `SELECT * FROM monthly_financial_summary LIMIT 5;`
- [ ] Update chatbot system prompt
- [ ] Test French query: "Quels sont mes revenus ce mois?"
- [ ] Test English query: "What is my revenue this month?"
- [ ] Compare chatbot results with DBeaver query results

---

**Next Steps:** Test both SQL queries in DBeaver, verify results, then proceed with migration creation.

**Last Updated:** 2025-01-19
