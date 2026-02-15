# Implementation Plan: Cash Flow Accounting & Payment Status Tracking (SIMPLIFIED)

**Date Created**: 2025-11-16
**Last Updated**: 2025-11-16 (Simplified Version)
**Requested By**: Jean-François (LHGI Hockey League)
**Objective**: Align Minipass financial reporting with industry-standard accounting software (QuickBooks, Xero, FreshBooks)
**Approach**: Phase by phase with testing between each phase

---

## Key Clarifications (User Feedback)

✅ **Passport Model**: NO CHANGES - Already has `paid`, `paid_date`, `marked_paid_by`
✅ **NO Bulk Actions**: Skip Phase 6 entirely - use simple per-transaction buttons
✅ **Full Implementation**: Industry-standard accounting with AR/AP terminology
✅ **Phase by Phase**: Test thoroughly between each phase

---

## Problem Statement

Jean-François manages a hockey league and charity foundation with a dedicated bank account. Currently, the Minipass financial report shows:
- **All passport sales as income** (even unpaid ones)
- **No distinction** between cash received vs. accounts receivable
- **KPI totals don't match** the actual bank account balance

### Root Cause
The `get_financial_data()` function in `utils.py` includes ALL passport sales regardless of payment status:
```python
# Line 3666 - CURRENT (WRONG):
passports = passport_query.filter(Passport.activity_id == activity.id).all()

# SHOULD BE (CASH BASIS):
passports = passport_query.filter(
    Passport.activity_id == activity.id,
    Passport.paid == True  # Only count paid passports
).all()
```

---

## Research Findings

### Current Database Schema

**Passport Model** (✅ HAS payment tracking - NO CHANGES NEEDED):
- `paid` (Boolean) - ✅ Already exists
- `paid_date` (DateTime) - ✅ Already exists
- `marked_paid_by` (String) - ✅ Already exists
- **KEEP existing "Mark as Paid" functionality**

**Income Model** (❌ NO payment tracking):
- Missing: `payment_status`, `payment_date`, `payment_method`
- All income entries assumed "received" immediately

**Expense Model** (❌ NO payment tracking):
- Missing: `payment_status`, `payment_date`, `due_date`, `payment_method`
- All expense entries assumed "paid" immediately

---

## Accounting Terminology (Industry Standard)

| Term | Meaning | Example |
|------|---------|---------|
| **Accounts Receivable (AR)** | Money owed TO you (not yet received) | $50 passport sale, customer hasn't paid yet |
| **Cash Received** | Money actually received (in bank) | $50 passport sale, payment received via e-transfer |
| **Accounts Payable (AP)** | Money you owe (not yet paid out) | $200 venue rental bill, not paid yet |
| **Cash Paid** | Money actually paid out (left bank) | $200 venue rental, already paid |
| **Cash Basis** | Only count when cash moves | Bank account balance = Cash Received - Cash Paid |
| **Accrual Basis** | Count when invoice/bill created | Total owed/owing regardless of payment status |

---

## Solution: Dual-View Financial System

### Proposed Financial Report Structure
```
┌─────────────────────────────────────────────────────┐
│ CASH FLOW SUMMARY (Cash Basis)                      │
│ - Cash Received: $5,000 💰                          │
│ - Cash Paid: $2,000                                 │
│ - Net Cash Flow: $3,000 ✅ MATCHES BANK ACCOUNT    │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ ACCOUNTS SUMMARY (Accrual Basis)                    │
│ - Accounts Receivable: $500 (unpaid income)         │
│ - Accounts Payable: $300 (unpaid expenses)          │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ TRANSACTION DETAILS                                  │
│ Date   | Type   | Category | Amount | Status |Action│
│ Nov 16 | Income | Passport | $50    | Paid ✅|  ...  │
│ Nov 15 | Income | Sponsor  | $100   | Unpaid| [Mark]│
│ Nov 14 | Expense| Venue    | $200   | Paid ✅|  ...  │
└─────────────────────────────────────────────────────┘
```

---

## Implementation Phases (With Testing)

### Phase 1: Database Schema Changes
**Goal**: Add payment status tracking to Income and Expense models
**Time**: 1 hour
**Risk**: MEDIUM - Database migration

#### 1.1 Changes to `models.py`

**Add to Income Model** (line ~134):
```python
class Income(db.Model):
    # ... existing fields (keep all) ...

    # NEW FIELDS:
    payment_status = db.Column(db.String(20), default="received")
    # Values: "pending", "received", "cancelled"

    payment_date = db.Column(db.DateTime, nullable=True)
    # Actual date payment was received

    payment_method = db.Column(db.String(50), nullable=True)
    # Values: "e-transfer", "cash", "cheque", "credit_card", "other"
```

**Add to Expense Model** (line ~120):
```python
class Expense(db.Model):
    # ... existing fields (keep all) ...

    # NEW FIELDS:
    payment_status = db.Column(db.String(20), default="paid")
    # Values: "unpaid", "paid", "cancelled"

    payment_date = db.Column(db.DateTime, nullable=True)
    # Actual date payment was made

    due_date = db.Column(db.DateTime, nullable=True)
    # When unpaid bill is due

    payment_method = db.Column(db.String(50), nullable=True)
    # Values: "e-transfer", "cash", "cheque", "credit_card", "other"
```

#### 1.2 Create Migration

```bash
flask db migrate -m "Add payment status to Income and Expense models"
flask db upgrade
```

#### 1.3 Testing Phase 1

**Unit Test Script**: `test/test_phase1_migration.py`
```python
import unittest
from app import app, db
from models import Income, Expense

class TestPhase1Migration(unittest.TestCase):
    """Test that migration adds payment_status fields correctly"""

    def setUp(self):
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        db.session.remove()
        self.app_context.pop()

    def test_income_has_payment_status_field(self):
        """Verify Income model has new payment_status field"""
        income = Income.query.first()
        # Should have payment_status attribute
        self.assertTrue(hasattr(income, 'payment_status'))
        self.assertTrue(hasattr(income, 'payment_date'))
        self.assertTrue(hasattr(income, 'payment_method'))

    def test_expense_has_payment_status_field(self):
        """Verify Expense model has new payment_status field"""
        expense = Expense.query.first()
        # Should have payment_status attribute
        self.assertTrue(hasattr(expense, 'payment_status'))
        self.assertTrue(hasattr(expense, 'payment_date'))
        self.assertTrue(hasattr(expense, 'due_date'))
        self.assertTrue(hasattr(expense, 'payment_method'))

    def test_existing_income_has_default_status(self):
        """Verify existing Income records have default 'received' status"""
        incomes = Income.query.all()
        for income in incomes:
            self.assertEqual(income.payment_status, 'received')

    def test_existing_expense_has_default_status(self):
        """Verify existing Expense records have default 'paid' status"""
        expenses = Expense.query.all()
        for expense in expenses:
            self.assertEqual(expense.payment_status, 'paid')

if __name__ == '__main__':
    unittest.main()
```

**Run Test**:
```bash
python -m unittest test.test_phase1_migration -v
```

**Manual Validation**:
1. Check database schema: `sqlite3 instance/minipass.db ".schema income"`
2. Verify new columns exist: `payment_status`, `payment_date`, `payment_method`
3. Check existing records have defaults: `SELECT id, payment_status FROM income LIMIT 5;`
4. Confirm app still runs: `curl http://localhost:5000/`

---

### Phase 2: Update Backend Logic (get_financial_data)
**Goal**: Calculate cash vs accrual properly
**Time**: 3-4 hours
**Risk**: HIGH - Core business logic

#### 2.1 Changes to `utils.py` function `get_financial_data()` (line ~3592)

**Replace entire function**:

```python
def get_financial_data(start_date, end_date, activity_filter=None, basis='cash'):
    """
    Get financial data for reporting.

    Args:
        start_date: Start of date range
        end_date: End of date range
        activity_filter: Optional activity ID to filter
        basis: 'cash' (default) or 'accrual'

    Returns:
        dict with cash_received, cash_paid, net_cash_flow,
        accounts_receivable, accounts_payable, transactions
    """
    from models import Passport, Income, Expense, Activity, PassportType, User

    # Initialize totals
    cash_received = 0.0
    cash_paid = 0.0
    accounts_receivable = 0.0
    accounts_payable = 0.0
    transactions = []

    # PASSPORT SALES (Income)
    passport_query = Passport.query.join(Activity).join(PassportType).join(User)

    if basis == 'cash':
        # Cash Basis: Only paid passports, use payment_date for filtering
        passport_query = passport_query.filter(
            Passport.paid == True,
            Passport.paid_date >= start_date,
            Passport.paid_date <= end_date
        )
    else:
        # Accrual Basis: All passports, use created_dt for filtering
        passport_query = passport_query.filter(
            Passport.created_dt >= start_date,
            Passport.created_dt <= end_date
        )

    if activity_filter:
        passport_query = passport_query.filter(Passport.activity_id == activity_filter)

    passports = passport_query.all()

    for passport in passports:
        if passport.paid:
            cash_received += passport.sold_amt
        else:
            accounts_receivable += passport.sold_amt

        transactions.append({
            'id': None,
            'date': passport.paid_date.strftime('%Y-%m-%d') if passport.paid_date else passport.created_dt.strftime('%Y-%m-%d'),
            'datetime': passport.paid_date if passport.paid_date else passport.created_dt,
            'type': 'Income',
            'category': 'Passport Sales',
            'description': f"{passport.passport_type.name} - {passport.user.name}",
            'amount': passport.sold_amt,
            'payment_status': 'received' if passport.paid else 'pending',
            'receipt_filename': None,
            'activity_id': passport.activity_id,
            'activity_name': passport.activity.name,
            'activity_image': passport.activity.image_filename,
            'editable': False,  # Passport sales not editable from financial report
            'source_type': 'passport',
            'created_by': passport.marked_paid_by or 'System'
        })

    # MANUAL INCOME ENTRIES
    income_query = Income.query.join(Activity)

    if basis == 'cash':
        # Cash Basis: Only received income, use payment_date
        income_query = income_query.filter(
            Income.payment_status == 'received',
            Income.payment_date >= start_date,
            Income.payment_date <= end_date
        )
    else:
        # Accrual Basis: All income, use invoice date
        income_query = income_query.filter(
            Income.date >= start_date,
            Income.date <= end_date
        )

    if activity_filter:
        income_query = income_query.filter(Income.activity_id == activity_filter)

    incomes = income_query.all()

    for income in incomes:
        if income.payment_status == 'received':
            cash_received += income.amount
        elif income.payment_status == 'pending':
            accounts_receivable += income.amount

        transactions.append({
            'id': income.id,
            'date': income.payment_date.strftime('%Y-%m-%d') if income.payment_date else income.date.strftime('%Y-%m-%d'),
            'datetime': income.payment_date if income.payment_date else income.date,
            'type': 'Income',
            'category': income.category,
            'description': income.note or '',
            'amount': income.amount,
            'payment_status': income.payment_status,
            'receipt_filename': income.receipt_filename,
            'activity_id': income.activity_id,
            'activity_name': income.activity.name,
            'activity_image': income.activity.image_filename,
            'editable': True,
            'source_type': 'income',
            'created_by': income.created_by or 'Unknown'
        })

    # EXPENSES
    expense_query = Expense.query.join(Activity)

    if basis == 'cash':
        # Cash Basis: Only paid expenses, use payment_date
        expense_query = expense_query.filter(
            Expense.payment_status == 'paid',
            Expense.payment_date >= start_date,
            Expense.payment_date <= end_date
        )
    else:
        # Accrual Basis: All expenses, use bill date
        expense_query = expense_query.filter(
            Expense.date >= start_date,
            Expense.date <= end_date
        )

    if activity_filter:
        expense_query = expense_query.filter(Expense.activity_id == activity_filter)

    expenses = expense_query.all()

    for expense in expenses:
        if expense.payment_status == 'paid':
            cash_paid += expense.amount
        elif expense.payment_status == 'unpaid':
            accounts_payable += expense.amount

        transactions.append({
            'id': expense.id,
            'date': expense.payment_date.strftime('%Y-%m-%d') if expense.payment_date else expense.date.strftime('%Y-%m-%d'),
            'datetime': expense.payment_date if expense.payment_date else expense.date,
            'type': 'Expense',
            'category': expense.category,
            'description': expense.description or '',
            'amount': expense.amount,
            'payment_status': expense.payment_status,
            'receipt_filename': expense.receipt_filename,
            'activity_id': expense.activity_id,
            'activity_name': expense.activity.name,
            'activity_image': expense.activity.image_filename,
            'editable': True,
            'source_type': 'expense',
            'created_by': expense.created_by or 'Unknown'
        })

    # Sort transactions by date (newest first)
    transactions.sort(key=lambda x: x['datetime'], reverse=True)

    # Group by activity
    by_activity = []
    if activity_filter:
        # Single activity view
        activity = Activity.query.get(activity_filter)
        if activity:
            activity_transactions = [t for t in transactions if t['activity_id'] == activity.id]
            by_activity.append({
                'activity_id': activity.id,
                'activity_name': activity.name,
                'activity_image': activity.image_filename,
                'total_revenue': sum(t['amount'] for t in activity_transactions if t['type'] == 'Income' and t['payment_status'] == 'received'),
                'total_expenses': sum(t['amount'] for t in activity_transactions if t['type'] == 'Expense' and t['payment_status'] == 'paid'),
                'net_income': sum(t['amount'] for t in activity_transactions if t['type'] == 'Income' and t['payment_status'] == 'received') -
                              sum(t['amount'] for t in activity_transactions if t['type'] == 'Expense' and t['payment_status'] == 'paid'),
                'transactions': activity_transactions
            })
    else:
        # All activities
        activities = Activity.query.all()
        for activity in activities:
            activity_transactions = [t for t in transactions if t['activity_id'] == activity.id]
            if activity_transactions:
                by_activity.append({
                    'activity_id': activity.id,
                    'activity_name': activity.name,
                    'activity_image': activity.image_filename,
                    'total_revenue': sum(t['amount'] for t in activity_transactions if t['type'] == 'Income' and t['payment_status'] == 'received'),
                    'total_expenses': sum(t['amount'] for t in activity_transactions if t['type'] == 'Expense' and t['payment_status'] == 'paid'),
                    'net_income': sum(t['amount'] for t in activity_transactions if t['type'] == 'Income' and t['payment_status'] == 'received') -
                                  sum(t['amount'] for t in activity_transactions if t['type'] == 'Expense' and t['payment_status'] == 'paid'),
                    'transactions': activity_transactions
                })

    return {
        'summary': {
            'cash_received': cash_received,
            'cash_paid': cash_paid,
            'net_cash_flow': cash_received - cash_paid,
            'accounts_receivable': accounts_receivable,
            'accounts_payable': accounts_payable,
            'total_revenue': cash_received + accounts_receivable,  # Accrual total
            'total_expenses': cash_paid + accounts_payable  # Accrual total
        },
        'by_activity': by_activity,
        'transactions': transactions
    }
```

#### 2.2 Testing Phase 2

**Unit Test Script**: `test/test_phase2_calculations.py`
```python
import unittest
from app import app, db
from models import Income, Expense, Passport, Activity, PassportType, User, Admin
from utils import get_financial_data
from datetime import datetime, timezone, timedelta

class TestPhase2Calculations(unittest.TestCase):
    """Test financial data calculations with payment status"""

    def setUp(self):
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

        # Create test data
        self.admin = Admin(email='test@test.com', password_hash='test')
        db.session.add(self.admin)

        self.activity = Activity(name="Test League", admin_id=1)
        db.session.add(self.activity)
        db.session.commit()

        self.user = User(name="Test User", email="user@test.com")
        db.session.add(self.user)

        self.passport_type = PassportType(name="Season Pass", activity_id=self.activity.id, price=50.0)
        db.session.add(self.passport_type)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_cash_basis_only_includes_paid_passports(self):
        """Test that cash basis excludes unpaid passport sales"""
        # Create paid passport
        paid_passport = Passport(
            activity_id=self.activity.id,
            passport_type_id=self.passport_type.id,
            user_id=self.user.id,
            sold_amt=50.0,
            paid=True,
            paid_date=datetime.now(timezone.utc),
            created_dt=datetime.now(timezone.utc)
        )

        # Create unpaid passport
        unpaid_passport = Passport(
            activity_id=self.activity.id,
            passport_type_id=self.passport_type.id,
            user_id=self.user.id,
            sold_amt=100.0,
            paid=False,
            created_dt=datetime.now(timezone.utc)
        )

        db.session.add_all([paid_passport, unpaid_passport])
        db.session.commit()

        # Get financial data (cash basis)
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
        end_date = datetime.now(timezone.utc) + timedelta(days=1)
        data = get_financial_data(start_date, end_date, basis='cash')

        # Cash received should only include paid passport
        self.assertEqual(data['summary']['cash_received'], 50.0)
        self.assertEqual(data['summary']['accounts_receivable'], 0.0)  # Unpaid not in cash basis

    def test_payment_status_filtering_for_income(self):
        """Test that income filtering respects payment status"""
        # Create received income
        received_income = Income(
            activity_id=self.activity.id,
            amount=200.0,
            category="Sponsorship",
            payment_status='received',
            payment_date=datetime.now(timezone.utc),
            date=datetime.now(timezone.utc)
        )

        # Create pending income
        pending_income = Income(
            activity_id=self.activity.id,
            amount=300.0,
            category="Sponsorship",
            payment_status='pending',
            date=datetime.now(timezone.utc)
        )

        db.session.add_all([received_income, pending_income])
        db.session.commit()

        # Get financial data (cash basis)
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
        end_date = datetime.now(timezone.utc) + timedelta(days=1)
        data = get_financial_data(start_date, end_date, basis='cash')

        # Cash received should only include received income
        self.assertEqual(data['summary']['cash_received'], 200.0)
        self.assertEqual(data['summary']['accounts_receivable'], 0.0)  # Pending not in cash basis

    def test_expense_payment_status(self):
        """Test expense filtering by payment status"""
        # Create paid expense
        paid_expense = Expense(
            activity_id=self.activity.id,
            amount=150.0,
            category="Venue",
            payment_status='paid',
            payment_date=datetime.now(timezone.utc),
            date=datetime.now(timezone.utc)
        )

        # Create unpaid expense
        unpaid_expense = Expense(
            activity_id=self.activity.id,
            amount=250.0,
            category="Equipment Rental",
            payment_status='unpaid',
            date=datetime.now(timezone.utc)
        )

        db.session.add_all([paid_expense, unpaid_expense])
        db.session.commit()

        # Get financial data (cash basis)
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
        end_date = datetime.now(timezone.utc) + timedelta(days=1)
        data = get_financial_data(start_date, end_date, basis='cash')

        # Cash paid should only include paid expenses
        self.assertEqual(data['summary']['cash_paid'], 150.0)
        self.assertEqual(data['summary']['accounts_payable'], 0.0)  # Unpaid not in cash basis

    def test_net_cash_flow_calculation(self):
        """Test that net cash flow = cash received - cash paid"""
        # Create some financial data
        income = Income(
            activity_id=self.activity.id,
            amount=1000.0,
            category="Ticket Sales",
            payment_status='received',
            payment_date=datetime.now(timezone.utc),
            date=datetime.now(timezone.utc)
        )

        expense = Expense(
            activity_id=self.activity.id,
            amount=400.0,
            category="Venue",
            payment_status='paid',
            payment_date=datetime.now(timezone.utc),
            date=datetime.now(timezone.utc)
        )

        db.session.add_all([income, expense])
        db.session.commit()

        # Get financial data
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
        end_date = datetime.now(timezone.utc) + timedelta(days=1)
        data = get_financial_data(start_date, end_date, basis='cash')

        # Verify calculations
        self.assertEqual(data['summary']['net_cash_flow'], 600.0)  # 1000 - 400
        self.assertEqual(data['summary']['cash_received'], 1000.0)
        self.assertEqual(data['summary']['cash_paid'], 400.0)

    def test_accrual_basis_includes_unpaid(self):
        """Test that accrual basis includes unpaid transactions"""
        # Create unpaid income
        pending_income = Income(
            activity_id=self.activity.id,
            amount=500.0,
            category="Sponsorship",
            payment_status='pending',
            date=datetime.now(timezone.utc)
        )

        # Create unpaid expense
        unpaid_expense = Expense(
            activity_id=self.activity.id,
            amount=300.0,
            category="Venue",
            payment_status='unpaid',
            date=datetime.now(timezone.utc)
        )

        db.session.add_all([pending_income, unpaid_expense])
        db.session.commit()

        # Get financial data (accrual basis)
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
        end_date = datetime.now(timezone.utc) + timedelta(days=1)
        data = get_financial_data(start_date, end_date, basis='accrual')

        # Should include in AR/AP
        self.assertEqual(data['summary']['accounts_receivable'], 500.0)
        self.assertEqual(data['summary']['accounts_payable'], 300.0)

if __name__ == '__main__':
    unittest.main()
```

**Run Test**:
```bash
python -m unittest test.test_phase2_calculations -v
```

**Manual Validation**:
1. Check financial report still loads: `curl http://localhost:5000/reports/financial`
2. Verify KPI values are calculated correctly
3. Check logs for any errors

---

### Phase 3: Update Financial Report UI
**Goal**: Display industry-standard accounting view
**Time**: 2 hours
**Risk**: LOW - UI only

#### 3.1 Changes to `templates/financial_report.html`

**Replace KPI Cards** (lines 52-209 for desktop, similar for mobile):

```html
<!-- Desktop: Row 1 - Cash Basis (Primary) -->
<div class="row mb-3">
  <div class="col-md-4">
    <div class="card" style="border-radius: 12px; min-height: 130px;">
      <div class="card-body text-center" style="display: flex; flex-direction: column; justify-content: center;">
        <div class="text-muted small text-uppercase mb-2">CASH RECEIVED</div>
        <div class="h1 mb-2" style="font-size: 2.5rem; font-weight: 700; color: #0f172a;">
          ${{ "{:,.0f}".format(financial_data.summary.cash_received) }}
        </div>
        <div class="text-muted small">Actual deposits</div>
      </div>
    </div>
  </div>

  <div class="col-md-4">
    <div class="card" style="border-radius: 12px; min-height: 130px;">
      <div class="card-body text-center" style="display: flex; flex-direction: column; justify-content: center;">
        <div class="text-muted small text-uppercase mb-2">CASH PAID</div>
        <div class="h1 mb-2" style="font-size: 2.5rem; font-weight: 700; color: #0f172a;">
          ${{ "{:,.0f}".format(financial_data.summary.cash_paid) }}
        </div>
        <div class="text-muted small">Actual payments</div>
      </div>
    </div>
  </div>

  <div class="col-md-4">
    <div class="card" style="border-radius: 12px; min-height: 130px;">
      <div class="card-body text-center" style="display: flex; flex-direction: column; justify-content: center;">
        <div class="text-muted small text-uppercase mb-2">NET CASH FLOW</div>
        <div class="h1 mb-2 text-success" style="font-size: 2.5rem; font-weight: 700;">
          ${{ "{:,.0f}".format(financial_data.summary.net_cash_flow) }}
        </div>
        <div class="text-success small">✅ Matches bank account</div>
      </div>
    </div>
  </div>
</div>

<!-- Desktop: Row 2 - Accrual Basis (Secondary) -->
<div class="row mb-4">
  <div class="col-md-6">
    <div class="card" style="border-radius: 12px; min-height: 110px;">
      <div class="card-body text-center" style="display: flex; flex-direction: column; justify-content: center;">
        <div class="text-muted small text-uppercase mb-2">ACCOUNTS RECEIVABLE</div>
        <div class="h2 mb-2" style="font-weight: 600; color: #0f172a;">
          ${{ "{:,.0f}".format(financial_data.summary.accounts_receivable) }}
        </div>
        <div class="text-muted small">Unpaid invoices</div>
      </div>
    </div>
  </div>

  <div class="col-md-6">
    <div class="card" style="border-radius: 12px; min-height: 110px;">
      <div class="card-body text-center" style="display: flex; flex-direction: column; justify-content: center;">
        <div class="text-muted small text-uppercase mb-2">ACCOUNTS PAYABLE</div>
        <div class="h2 mb-2" style="font-weight: 600; color: #0f172a;">
          ${{ "{:,.0f}".format(financial_data.summary.accounts_payable) }}
        </div>
        <div class="text-muted small">Unpaid bills</div>
      </div>
    </div>
  </div>
</div>
```

**Add Status Column to Transaction Table** (line ~274):
```html
<th class="text-end">Amount</th>
<th class="text-center">Status</th> <!-- NEW COLUMN -->
<th class="text-center">Actions</th>

<!-- In tbody: -->
<td class="text-center">
  {% if transaction.payment_status in ['paid', 'received'] %}
    <span class="badge bg-success">Paid</span>
  {% elif transaction.payment_status in ['pending', 'unpaid'] %}
    <span class="badge bg-warning">Unpaid</span>
  {% else %}
    <span class="badge bg-secondary">{{ transaction.payment_status|title }}</span>
  {% endif %}
</td>
```

#### 3.2 Testing Phase 3

**MCP Playwright Test**: `test/test_phase3_ui.py`
```python
# Test financial report UI displays correctly

def test_kpi_cards_display(page):
    """Test that 5 KPI cards display with correct labels"""
    page.goto('http://localhost:5000/reports/financial')

    # Cash Basis Cards
    assert page.locator('text=CASH RECEIVED').is_visible()
    assert page.locator('text=CASH PAID').is_visible()
    assert page.locator('text=NET CASH FLOW').is_visible()

    # Accrual Basis Cards
    assert page.locator('text=ACCOUNTS RECEIVABLE').is_visible()
    assert page.locator('text=ACCOUNTS PAYABLE').is_visible()

def test_status_badges_display(page):
    """Test that status badges appear in transaction table"""
    page.goto('http://localhost:5000/reports/financial')

    # Should see status badges
    assert page.locator('.badge.bg-success').count() > 0  # Paid badges
    # If unpaid transactions exist, should see warning badges
    # assert page.locator('.badge.bg-warning').count() > 0

def test_mobile_responsive(page):
    """Test mobile view displays correctly"""
    page.set_viewport_size({"width": 375, "height": 667})
    page.goto('http://localhost:5000/reports/financial')

    # Mobile carousel should be visible
    assert page.locator('.mobile-kpi-scroll').is_visible()
    assert page.locator('.mobile-dot').count() == 5  # 5 KPI cards
```

**Run with MCP Playwright**:
```python
# Using MCP Playwright tools directly in Claude Code
# Navigate to financial report and verify visual elements
```

**Manual Validation**:
1. Open `http://localhost:5000/reports/financial` in browser
2. Verify 5 KPI cards display correctly
3. Check status badges appear in transaction table
4. Test mobile responsive view (resize browser window)
5. Verify no layout issues or overlapping text

---

### Phase 4: Update Income/Expense Entry Forms
**Goal**: Allow entering unpaid invoices/bills
**Time**: 2 hours
**Risk**: MEDIUM - Form changes

#### 4.1 Update Income Form

**Find income form in drawer** (`templates/financial_report.html` line ~426-464):

Add after Category field:
```html
<!-- Payment Status Field -->
<div class="mb-3">
  <label class="form-label">Payment Status</label>
  <select class="form-select" name="payment_status" id="txPaymentStatus">
    <option value="received" selected>Received (Paid)</option>
    <option value="pending">Pending (Not Yet Received)</option>
  </select>
</div>

<!-- Payment Date Field -->
<div class="mb-3" id="txPaymentDateField">
  <label class="form-label">Payment Date</label>
  <input type="date" class="form-control" name="payment_date" id="txPaymentDate" value="">
</div>

<!-- Payment Method Field -->
<div class="mb-3">
  <label class="form-label">Payment Method</label>
  <select class="form-select" name="payment_method" id="txPaymentMethod">
    <option value="">Select method...</option>
    <option value="e-transfer">E-Transfer</option>
    <option value="cash">Cash</option>
    <option value="cheque">Cheque</option>
    <option value="credit_card">Credit Card</option>
    <option value="other">Other</option>
  </select>
</div>
```

Add JavaScript (in scripts section):
```javascript
// Show/hide payment date based on status (Income)
document.getElementById('txPaymentStatus').addEventListener('change', function() {
  const paymentDateField = document.getElementById('txPaymentDateField');
  if (this.value === 'received') {
    paymentDateField.style.display = 'block';
    document.getElementById('txPaymentDate').required = true;
  } else {
    paymentDateField.style.display = 'none';
    document.getElementById('txPaymentDate').required = false;
  }
});

// Set default date to today when status is "received"
document.addEventListener('DOMContentLoaded', function() {
  const today = new Date().toISOString().split('T')[0];
  document.getElementById('txPaymentDate').value = today;
});
```

#### 4.2 Update Expense Form

Similar changes for expense form in drawer. Add after Category field:
```html
<!-- Payment Status Field -->
<div class="mb-3">
  <label class="form-label">Payment Status</label>
  <select class="form-select" name="payment_status" id="expensePaymentStatus">
    <option value="paid" selected>Paid</option>
    <option value="unpaid">Unpaid (Bill Not Yet Paid)</option>
  </select>
</div>

<!-- Payment Date Field (shown when paid) -->
<div class="mb-3" id="expensePaymentDateField">
  <label class="form-label">Payment Date</label>
  <input type="date" class="form-control" name="payment_date" id="expensePaymentDate" value="">
</div>

<!-- Due Date Field (shown when unpaid) -->
<div class="mb-3" id="expenseDueDateField" style="display: none;">
  <label class="form-label">Due Date</label>
  <input type="date" class="form-control" name="due_date" id="expenseDueDate">
</div>

<!-- Payment Method Field -->
<div class="mb-3">
  <label class="form-label">Payment Method</label>
  <select class="form-select" name="payment_method" id="expensePaymentMethod">
    <option value="">Select method...</option>
    <option value="e-transfer">E-Transfer</option>
    <option value="cash">Cash</option>
    <option value="cheque">Cheque</option>
    <option value="credit_card">Credit Card</option>
    <option value="other">Other</option>
  </select>
</div>
```

Add JavaScript:
```javascript
// Toggle payment date vs due date based on status (Expense)
document.getElementById('expensePaymentStatus').addEventListener('change', function() {
  const isPaid = this.value === 'paid';
  document.getElementById('expensePaymentDateField').style.display = isPaid ? 'block' : 'none';
  document.getElementById('expenseDueDateField').style.display = isPaid ? 'none' : 'block';

  if (isPaid) {
    document.getElementById('expensePaymentDate').required = true;
    document.getElementById('expenseDueDate').required = false;
  } else {
    document.getElementById('expensePaymentDate').required = false;
    document.getElementById('expenseDueDate').required = true;
  }
});

// Set default date to today when status is "paid"
document.addEventListener('DOMContentLoaded', function() {
  const today = new Date().toISOString().split('T')[0];
  document.getElementById('expensePaymentDate').value = today;
});
```

#### 4.3 Update Route Handlers in `app.py`

**Update Income route** (find `@app.route('/admin/activity-income/<int:activity_id>', methods=['POST'])`):
```python
# Add to Income creation:
income = Income(
    activity_id=activity_id,
    date=date,
    category=category,
    amount=amount,
    note=note,
    created_by=session.get('admin_email'),
    receipt_filename=receipt_filename,
    # NEW FIELDS:
    payment_status=request.form.get('payment_status', 'received'),
    payment_date=datetime.fromisoformat(request.form.get('payment_date')) if request.form.get('payment_date') and request.form.get('payment_status') == 'received' else None,
    payment_method=request.form.get('payment_method')
)
```

**Update Expense route** (find `@app.route('/admin/activity-expenses/<int:activity_id>', methods=['POST'])`):
```python
# Add to Expense creation:
expense = Expense(
    activity_id=activity_id,
    date=date,
    category=category,
    amount=amount,
    description=description,
    created_by=session.get('admin_email'),
    receipt_filename=receipt_filename,
    # NEW FIELDS:
    payment_status=request.form.get('payment_status', 'paid'),
    payment_date=datetime.fromisoformat(request.form.get('payment_date')) if request.form.get('payment_date') and request.form.get('payment_status') == 'paid' else None,
    due_date=datetime.fromisoformat(request.form.get('due_date')) if request.form.get('due_date') and request.form.get('payment_status') == 'unpaid' else None,
    payment_method=request.form.get('payment_method')
)
```

#### 4.4 Testing Phase 4

**MCP Playwright Test**: `test/test_phase4_forms.py`
```python
def test_add_unpaid_income(page):
    """Test adding unpaid invoice"""
    page.goto('http://localhost:5000/reports/financial')

    # Open income drawer
    page.click('button:has-text("Income")')

    # Fill form with unpaid status
    page.fill('input[name="date"]', '2025-11-16')
    page.select_option('select[name="activity_id"]', index=1)  # Select first activity
    page.select_option('select[name="category"]', 'Sponsorship')
    page.fill('input[name="amount"]', '500')
    page.fill('textarea[name="note"]', 'Test unpaid sponsorship')
    page.select_option('select[name="payment_status"]', 'pending')

    # Submit
    page.click('button[type="submit"]')

    # Verify redirect to financial report
    page.wait_for_url('**/reports/financial')

    # Should see unpaid badge
    assert page.locator('.badge.bg-warning:has-text("Unpaid")').count() > 0

def test_add_paid_expense(page):
    """Test adding paid expense (default behavior)"""
    page.goto('http://localhost:5000/reports/financial')

    # Open expense drawer
    page.click('button:has-text("Expense")')

    # Fill form with paid status (default)
    page.fill('input[name="date"]', '2025-11-16')
    page.select_option('select[name="activity_id"]', index=1)
    page.select_option('select[name="category"]', 'Venue')
    page.fill('input[name="amount"]', '300')
    page.fill('textarea[name="description"]', 'Test venue rental')
    # payment_status should default to "paid"
    page.fill('input[name="payment_date"]', '2025-11-16')

    # Submit
    page.click('button[type="submit"]')

    # Verify redirect
    page.wait_for_url('**/reports/financial')

    # Should see paid badge
    assert page.locator('.badge.bg-success:has-text("Paid")').count() > 0

def test_add_unpaid_expense_with_due_date(page):
    """Test adding unpaid expense with due date"""
    page.goto('http://localhost:5000/reports/financial')

    # Open expense drawer
    page.click('button:has-text("Expense")')

    # Fill form with unpaid status
    page.fill('input[name="date"]', '2025-11-16')
    page.select_option('select[name="activity_id"]', index=1)
    page.select_option('select[name="category"]', 'Equipment Rental')
    page.fill('input[name="amount"]', '450')
    page.select_option('select[name="payment_status"]', 'unpaid')
    page.fill('input[name="due_date"]', '2025-11-30')

    # Submit
    page.click('button[type="submit"]')

    # Verify
    page.wait_for_url('**/reports/financial')
    assert page.locator('.badge.bg-warning:has-text("Unpaid")').count() > 0
```

**Manual Validation**:
1. Test adding income with "Received" status → Should appear as Paid
2. Test adding income with "Pending" status → Should appear as Unpaid, in AR
3. Test adding expense with "Paid" status → Should appear as Paid
4. Test adding expense with "Unpaid" status → Should appear as Unpaid, in AP
5. Verify financial report KPIs update correctly

---

### Phase 5: Add "Mark as Paid" Individual Buttons
**Goal**: Allow marking unpaid transactions as paid (like passport already does)
**Time**: 1 hour
**Risk**: LOW - Simple feature, isolated

#### 5.1 Add "Mark as Paid" to Transaction Dropdown

**Update transaction actions dropdown** in `templates/financial_report.html` (line ~302):

```html
<div class="dropdown-menu dropdown-menu-end">
  {% if transaction.receipt_filename %}
    <a class="dropdown-item" href="#" onclick="viewReceipt('{{ transaction.receipt_filename }}'); return false;">
      <i class="ti ti-file me-2"></i>View Receipt
    </a>
  {% endif %}

  <!-- NEW: Mark as Paid button for unpaid transactions -->
  {% if transaction.payment_status in ['pending', 'unpaid'] and transaction.source_type in ['income', 'expense'] %}
    <a class="dropdown-item text-success" href="#"
       onclick="markAsPaid('{{ transaction.source_type }}', {{ transaction.id }}); return false;">
      <i class="ti ti-check me-2"></i>Mark as Paid
    </a>
    <div class="dropdown-divider"></div>
  {% endif %}

  <a class="dropdown-item" href="#"
     onclick="openDrawerWithData('{{ transaction.source_type }}', {{ transaction.id }}, ...); return false;">
    <i class="ti ti-edit me-2"></i>Edit Entry
  </a>

  {% if transaction.editable %}
    <div class="dropdown-divider"></div>
    <a class="dropdown-item text-danger" href="#"
       onclick="confirmDelete('{{ transaction.source_type }}', {{ transaction.id }}, '{{ transaction.description|replace("'", "\\'") }}'); return false;">
      <i class="ti ti-trash me-2"></i>Delete Entry
    </a>
  {% endif %}
</div>
```

#### 5.2 Add JavaScript Function

Add in scripts section of `templates/financial_report.html`:

```javascript
// Mark individual transaction as paid
async function markAsPaid(sourceType, id) {
  if (!confirm('Mark this transaction as paid/received?')) return;

  const url = sourceType === 'income'
    ? `/admin/mark-income-paid/${id}`
    : `/admin/mark-expense-paid/${id}`;

  try {
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': csrfToken
      }
    });

    const data = await response.json();

    if (data.success) {
      // Reload page to show updated status
      window.location.reload();
    } else {
      alert('Error: ' + (data.message || 'Failed to mark as paid'));
    }
  } catch (error) {
    console.error('Error:', error);
    alert('Network error. Please try again.');
  }
}
```

#### 5.3 Add Routes in `app.py`

Add two new routes:

```python
@app.route('/admin/mark-income-paid/<int:income_id>', methods=['POST'])
def mark_income_paid(income_id):
    """Mark an income transaction as received"""
    if 'admin_logged_in' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        income = Income.query.get_or_404(income_id)

        # Update payment status
        income.payment_status = 'received'
        income.payment_date = datetime.now(timezone.utc)

        db.session.commit()

        flash(f'Income of ${income.amount:.2f} marked as received', 'success')
        return jsonify({'success': True, 'message': 'Income marked as received'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/admin/mark-expense-paid/<int:expense_id>', methods=['POST'])
def mark_expense_paid(expense_id):
    """Mark an expense transaction as paid"""
    if 'admin_logged_in' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        expense = Expense.query.get_or_404(expense_id)

        # Update payment status
        expense.payment_status = 'paid'
        expense.payment_date = datetime.now(timezone.utc)

        db.session.commit()

        flash(f'Expense of ${expense.amount:.2f} marked as paid', 'success')
        return jsonify({'success': True, 'message': 'Expense marked as paid'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
```

#### 5.4 Testing Phase 5

**MCP Playwright Test**: `test/test_phase5_mark_paid.py`
```python
def test_mark_income_as_received(page):
    """Test marking unpaid income as received"""
    # First create unpaid income
    page.goto('http://localhost:5000/reports/financial')
    page.click('button:has-text("Income")')
    page.fill('input[name="amount"]', '250')
    page.select_option('select[name="payment_status"]', 'pending')
    page.click('button[type="submit"]')

    # Find and expand the transaction details
    page.click('text=Details')

    # Click Mark as Paid
    page.click('text=Mark as Paid')

    # Confirm dialog
    page.on('dialog', lambda dialog: dialog.accept())

    # Wait for reload
    page.wait_for_load_state('networkidle')

    # Should now show as Paid
    assert page.locator('.badge.bg-success:has-text("Paid")').count() > 0

    # Cash Received KPI should increase
    # (verify the number increased)

def test_mark_expense_as_paid(page):
    """Test marking unpaid expense as paid"""
    # First create unpaid expense
    page.goto('http://localhost:5000/reports/financial')
    page.click('button:has-text("Expense")')
    page.fill('input[name="amount"]', '350')
    page.select_option('select[name="payment_status"]', 'unpaid')
    page.fill('input[name="due_date"]', '2025-12-01')
    page.click('button[type="submit"]')

    # Find and mark as paid
    page.click('text=Details')
    page.click('text=Mark as Paid')
    page.on('dialog', lambda dialog: dialog.accept())

    # Wait for reload
    page.wait_for_load_state('networkidle')

    # Should show as Paid
    assert page.locator('.badge.bg-success:has-text("Paid")').count() > 0
```

**Manual Validation**:
1. Create unpaid income transaction
2. Find it in financial report, expand details
3. Click "Mark as Paid" in dropdown
4. Verify confirmation dialog appears
5. After confirmation, verify badge changes to "Paid"
6. Verify KPI cards update (AR decreases, Cash Received increases)
7. Repeat for unpaid expense

---

## Summary of Changes

| Phase | Changes | Risk | Time | Testing |
|-------|---------|------|------|---------|
| 1 | Add payment_status to Income/Expense models | MEDIUM | 1h | Unit tests + manual validation |
| 2 | Update get_financial_data() logic | HIGH | 3-4h | Unit tests (5 test cases) |
| 3 | Redesign financial report UI (5 KPI cards + Status column) | LOW | 2h | MCP Playwright + manual |
| 4 | Update Income/Expense forms | MEDIUM | 2h | MCP Playwright (3 scenarios) |
| 5 | Add "Mark as Paid" individual buttons | LOW | 1h | MCP Playwright (2 scenarios) |
| **Total** | | | **9-10 hours** | **10+ automated tests** |

---

## What's NOT Changing (Simplified)

✅ **Passport model**: NO changes - already has payment tracking
✅ **Passport "Mark as Paid"**: Keep existing functionality
✅ **NO bulk actions**: Skipped entirely (Phase 6 removed)
✅ **NO complex frontend**: Simple per-transaction buttons

---

## Files to Modify

| File | Location | Changes |
|------|----------|---------|
| `models.py` | Line ~120, ~134 | Add payment_status fields to Income/Expense |
| `migrations/` | New file | Migration for schema changes |
| `utils.py` | Line ~3592 | Replace `get_financial_data()` function |
| `templates/financial_report.html` | Lines 52-209, 274, 302, 426-464 | KPI cards, Status column, Forms, Mark as Paid |
| `app.py` | Income/Expense routes | Update route handlers, add mark-paid routes |
| `test/test_phase1_migration.py` | New file | Phase 1 unit tests |
| `test/test_phase2_calculations.py` | New file | Phase 2 unit tests |
| `test/test_phase3_ui.py` | New file | Phase 3 Playwright tests |
| `test/test_phase4_forms.py` | New file | Phase 4 Playwright tests |
| `test/test_phase5_mark_paid.py` | New file | Phase 5 Playwright tests |

---

## Testing Strategy (Comprehensive)

### Phase 1 Testing
- **Unit Tests**: 4 test cases (field existence, defaults)
- **Manual**: Database schema verification
- **Time**: 15 minutes

### Phase 2 Testing
- **Unit Tests**: 5 test cases (cash/accrual filtering, calculations)
- **Manual**: Financial report still loads
- **Time**: 30 minutes

### Phase 3 Testing
- **Playwright**: 3 test cases (KPI display, badges, mobile)
- **Manual**: Visual check, responsive design
- **Time**: 20 minutes

### Phase 4 Testing
- **Playwright**: 3 test cases (add unpaid income, paid expense, unpaid expense)
- **Manual**: Form submission validation
- **Time**: 25 minutes

### Phase 5 Testing
- **Playwright**: 2 test cases (mark income paid, mark expense paid)
- **Manual**: End-to-end workflow
- **Time**: 15 minutes

### Final Validation
- Export Jean-François's financial report
- Compare "Net Cash Flow" with bank statement
- Should match exactly ✅

**Total Testing Time**: ~2 hours
**Total Automated Tests**: 10+ test cases

---

## Benefits (Industry Alignment)

✅ **Matches QuickBooks/Xero/FreshBooks**: Dual-view (cash + accrual) is universal standard
✅ **Bank Reconciliation**: Net Cash Flow KPI = Actual Bank Balance
✅ **Invoice Tracking**: Can enter unpaid invoices (AR) and bills (AP)
✅ **Cash Flow Visibility**: See actual cash position vs. amounts owed
✅ **Flexible Usage**: Simple users enter everything as paid, advanced users track unpaid
✅ **Standard Terminology**: AR, AP, Cash Received, Cash Paid (universally recognized)
✅ **Professional Credibility**: Aligns with accounting best practices (GAAP/IFRS)

---

## Backward Compatibility

**Preserved**:
- ✅ Existing Income/Expense records automatically marked as "received"/"paid"
- ✅ Default form values maintain simple behavior (immediate paid/received)
- ✅ No breaking changes to existing workflows
- ✅ Users who don't need unpaid tracking can ignore new fields
- ✅ Advanced users (like Jean-François) can leverage full accrual accounting

**Rollback Plan**:
- Database: `flask db downgrade` to revert migration
- Code: `git revert` to undo changes
- Each phase can be reverted independently

---

## Success Metrics

1. ✅ **Bank Account Match**: Net Cash Flow KPI = Bank Statement Balance (within $1)
2. ✅ **User Adoption**: Jean-François successfully uses unpaid invoice tracking
3. ✅ **No Regressions**: Existing financial reports still work for all customers
4. ✅ **Performance**: Financial report loads in <2 seconds with 500+ transactions
5. ✅ **Data Integrity**: All existing financial data preserved, no data loss
6. ✅ **Test Coverage**: 10+ automated tests passing

---

## Risk Mitigation

### Pre-Implementation Checklist
- [ ] Backup database: `cp instance/minipass.db instance/minipass.db.backup-$(date +%Y%m%d)`
- [ ] Test migration on copy of database
- [ ] Review all changes to `get_financial_data()`
- [ ] Ensure Flask server running on localhost:5000

### During Implementation
- [ ] Commit after each phase
- [ ] Run tests after each phase
- [ ] Manual validation after each phase
- [ ] Monitor Flask debug output for errors

### Post-Implementation
- [ ] Verify Jean-François's bank reconciliation
- [ ] Check other customers' financial reports
- [ ] Monitor for 48 hours
- [ ] Collect user feedback

---

**End of Implementation Plan (Simplified)**

**Document Version**: 2.0 (Simplified)
**Last Updated**: 2025-11-16
**Author**: Claude Code Assistant
**Status**: Ready for Phase-by-Phase Implementation
**Estimated Total Time**: 9-10 hours + 2 hours testing = 11-12 hours