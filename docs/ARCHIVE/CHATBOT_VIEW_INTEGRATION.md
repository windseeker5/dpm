# Chatbot Integration with Accounting-Standard Views

## Overview

Two new SQLite views have been created to simplify chatbot queries about financial data. These views align with QuickBooks, FreshBooks, and Xero accounting standards.

## Available Views

### View 1: `monthly_transactions_detail`
**Purpose:** Transaction Detail Ledger (Accounts Receivable/Payable tracking)

**Columns:**
- `month` - Format: YYYY-MM
- `project` - Activity name (business division/class)
- `transaction_type` - "Income" or "Expense"
- `transaction_date` - Date of transaction
- `account` - Accounting category (Passport Sales, Staff, Merchandise Sales, etc.)
- `customer` - Customer name (passport sales only, NULL otherwise)
- `vendor` - Vendor name (currently always NULL)
- `memo` - Transaction notes/description
- `amount` - Transaction amount
- `payment_status` - "Paid", "Unpaid (AR)", or "Unpaid (AP)"
- `entered_by` - Who entered the transaction

**Use Cases:**
- "Show me all unpaid invoices" → `WHERE payment_status = 'Unpaid (AR)'`
- "What are my accounts receivable?" → `WHERE payment_status = 'Unpaid (AR)'`
- "Show passport sales for January 2025" → `WHERE month = '2025-01' AND account = 'Passport Sales'`
- "List all expenses for Staff" → `WHERE account = 'Staff' AND transaction_type = 'Expense'`

### View 2: `monthly_financial_summary`
**Purpose:** Monthly P&L with Cash Basis and Accrual Basis Accounting

**Columns:**
- `month` - Format: YYYY-MM
- `activity_id` - Activity ID
- `account` - Activity name (project)
- **Cash Basis:**
  - `passport_sales` - Paid passport sales
  - `other_income` - Paid other income
  - `cash_received` - Total cash received (passport_sales + other_income)
  - `cash_paid` - Total cash paid (expenses)
  - `net_cash_flow` - Cash received - Cash paid
- **Accrual Basis:**
  - `passport_ar` - Unpaid passport sales (Accounts Receivable)
  - `other_income_ar` - Unpaid other income (Accounts Receivable)
  - `accounts_receivable` - Total AR (passport_ar + other_income_ar)
  - `accounts_payable` - Total unpaid expenses (AP)
  - `total_revenue` - All revenue (paid + unpaid)
  - `total_expenses` - All expenses (paid + unpaid)
  - `net_income` - Total revenue - Total expenses

**Use Cases:**
- "What is my cash flow this month?" → `WHERE month = '2025-01'` → `net_cash_flow`
- "Show me revenue for Q1" → `WHERE month IN ('2025-01', '2025-02', '2025-03')` → `SUM(total_revenue)`
- "What are my accounts receivable?" → `SUM(accounts_receivable) WHERE month = [current_month]`
- "Show net income year to date" → `SUM(net_income) WHERE month LIKE '2025-%'`

## Chatbot System Prompt Updates

### Location
File: `chatbot_v2/query_engine.py` (line 282+)

### Recommended Addition to System Prompt

Add this section to the chatbot's system prompt:

```
## Accounting-Standard Financial Views

You have access to two pre-built views that simplify financial queries:

### monthly_transactions_detail
Use this view for detailed transaction queries:
- Shows individual transactions with proper accounting terminology
- Includes transaction_type (Income/Expense), account (category), project (activity)
- Tracks payment_status: "Paid", "Unpaid (AR)" for receivables, "Unpaid (AP)" for payables
- Includes customer names for passport sales

Example queries:
- "Quels sont mes comptes à recevoir?" → SELECT * FROM monthly_transactions_detail WHERE payment_status = 'Unpaid (AR)'
- "Show unpaid invoices" → SELECT * FROM monthly_transactions_detail WHERE payment_status LIKE 'Unpaid%'

### monthly_financial_summary
Use this view for monthly P&L and cash flow queries:
- Aggregates data by month and activity
- Provides both Cash Basis (cash_received, cash_paid, net_cash_flow) and Accrual Basis (total_revenue, total_expenses, net_income) accounting
- Includes accounts_receivable and accounts_payable totals

Example queries:
- "What is my cash flow?" → SELECT month, account, net_cash_flow FROM monthly_financial_summary
- "Show revenue this month" → SELECT SUM(total_revenue) FROM monthly_financial_summary WHERE month = strftime('%Y-%m', 'now')
- "Quel est mon revenu net?" → SELECT SUM(net_income) FROM monthly_financial_summary

**IMPORTANT:** Always prefer these views over raw tables for financial queries about:
- Revenue, income, sales
- Expenses, costs
- Cash flow, net cash
- Accounts receivable (AR), accounts payable (AP)
- Net income, profit/loss
```

## Testing the Integration

### Sample Queries to Test

**French (User's Language):**
1. "Quels sont mes revenus ce mois-ci?"
2. "Montre-moi les comptes à recevoir"
3. "Quel est mon flux de trésorerie?"
4. "Combien j'ai dépensé en Staff ce mois-ci?"

**English:**
1. "What is my revenue this month?"
2. "Show me accounts receivable"
3. "What is my cash flow?"
4. "How much did I spend on Staff this month?"

### Expected Behavior

The chatbot should:
1. Recognize financial terminology (revenue, cash flow, AR, AP, net income)
2. Use the appropriate view (detail for transactions, summary for aggregates)
3. Return results with proper accounting terminology
4. Handle both Cash Basis and Accrual Basis queries correctly

## Next Steps

1. **Update chatbot system prompt** in `chatbot_v2/query_engine.py`
2. **Test chatbot** with sample queries above
3. **Document common queries** based on user feedback
4. **Consider caching** view results if performance becomes an issue (currently 93 transactions, 7 summaries)

## Database Statistics

- `monthly_transactions_detail`: 93 transactions
- `monthly_financial_summary`: 7 monthly summaries

## Migration File

Location: `migrations/versions/a9e8d26b87b3_add_accounting_standard_financial_views_.py`

To rollback views:
```bash
flask db downgrade -1
```

To recreate views:
```bash
flask db upgrade
```
