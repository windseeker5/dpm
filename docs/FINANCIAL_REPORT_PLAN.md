# Financial Accounting Report - Implementation Plan

**Feature Request**: Export financial data (income + expenses) for accounting software integration
**Requested by**: Production customer with $300K annual revenue
**Priority**: High - enables scale to enterprise customers
**Status**: Planning Complete - Ready for Implementation

---

## 🎯 Core Features (Simplified)

### 1. **Financial Report Page** (`/reports/financial`)
- **Summary Cards**:
  - Total Revenue (Passport Sales + Other Income)
  - Total Expenses
  - Net Income
  - Period selector: Month, Quarter, Year, Custom Date Range, All-Time

- **Activity Breakdown Table**:
  - Grouped by activity with expandable rows
  - Columns: Date | Type | Category | Description | Amount | Receipt
  - Click activity name → expand to see all transactions
  - Click receipt icon → view PDF/image in modal

### 2. **Filters & Search**:
- Filter by: Activity, Date Range, Type (Income/Expense)
- Search: Description, category, amount
- Sort: By date, amount, activity name

### 3. **Export Formats** (Universal Compatibility):
- **Standard CSV** - Works with ALL accounting software
- **QuickBooks IIF** - QuickBooks Desktop direct import
- **Excel XLSX** - Formatted with formulas and totals

### 4. **Export Configuration** (Simple):
- Basic account code mapping in Settings
- Map categories to account codes (Revenue: 4000, Expenses: 5000-7000)
- Saved in Settings table as JSON

---

## 📊 Data Sources (Already in Database ✅)

```
✅ Passport Sales (Passport table)
   - sold_amt, created_dt, activity_id, passport_type_name

✅ Other Income (Income table)
   - amount, date, category, note, receipt_filename

✅ Expenses (Expense table)
   - amount, date, category, description, receipt_filename
```

**No database changes required!**

---

## 🏗️ Implementation Structure

### New Routes:
```python
/reports/financial          # Main report page
/reports/financial/export   # Export handler (GET with format param)
```

### New Files:
```
templates/financial_report.html           # Main report UI
utils.py: get_financial_data()           # Data aggregation
utils.py: export_financial_csv()         # CSV export
utils.py: export_financial_iif()         # QuickBooks IIF
utils.py: export_financial_xlsx()        # Excel export
```

### Navigation Update:
Add "Financial Report" link under Reports section in `base.html` (line ~492-506)

---

## 🎨 UI Components (Tabler.io)

- **Summary Cards** - 3 metric cards (Revenue, Expenses, Net)
- **Date Range Picker** - Bootstrap daterangepicker
- **Expandable Table** - Activity grouping with collapse/expand
- **Export Dropdown** - Format selector (CSV, IIF, XLSX)
- **Receipt Modal** - View PDF/images inline
- **Search Bar** - Filter transactions

---

## 📤 Standard CSV Export Format

```csv
Date,Activity,Type,Category,Description,Amount,Receipt
2025-09-15,Hockey League,Income,Passport Sales,4-session pass - John Doe,50.00,N/A
2025-09-16,Hockey League,Income,Fundraising,Cupcake sales,120.00,receipt_123.pdf
2025-09-17,Hockey League,Expense,Equipment,Hockey pucks,85.00,invoice_456.pdf
2025-09-18,Yoga Class,Income,Passport Sales,Monthly pass - Jane Smith,100.00,N/A
```

**Why CSV?** Works with: QuickBooks, Xero, Sage, Wave, FreshBooks, and all spreadsheet software.

---

## 📋 QuickBooks IIF Export Format

```
!TRNS	TRNSID	TRNSTYPE	DATE	ACCNT	NAME	CLASS	AMOUNT	DOCNUM	MEMO
!SPL	SPLID	TRNSTYPE	DATE	ACCNT	NAME	CLASS	AMOUNT	DOCNUM	MEMO
!ENDTRNS
TRNS		GENERAL JOURNAL	09/15/2025	Bank Account			50.00		Passport Sales
SPL		GENERAL JOURNAL	09/15/2025	4000 - Sales Revenue			-50.00		Hockey League - 4-session pass
ENDTRNS
```

---

## 🚀 Implementation Steps

### Phase 1: Core Functionality (MVP)
1. **Create data aggregation function** (`get_financial_data()`)
   - Query Passport, Income, Expense tables
   - Group by activity
   - Filter by date range
   - Return structured dict with totals

2. **Build report page** (`/reports/financial`)
   - Summary cards with totals
   - Activity breakdown table (expandable rows)
   - Date range selector
   - Search and filters

3. **Add CSV export** (universal format)
   - Simple format that works everywhere
   - Include receipt filenames
   - Proper escaping for commas/quotes

4. **Add receipt viewing modal**
   - Display PDF/images from uploads folder
   - Handle missing files gracefully

5. **Update navigation**
   - Add "Financial Report" under Reports section in base.html

### Phase 2: Enhanced Exports (Optional)
6. **Add QuickBooks IIF export**
   - For QuickBooks Desktop users
   - Proper IIF format with TRNS/SPL/ENDTRNS

7. **Add Excel export**
   - Formatted with subtotals and formulas
   - Multiple sheets: Summary, Transactions, By Activity

8. **Write tests**
   - Test data aggregation
   - Test export formats
   - Test date filtering

---

## 🔄 User Flow

1. Navigate to **Reports → Financial Report**
2. Select period (e.g., "Q3 2025" or "Last Month")
3. View summary: $9,500 revenue, $1,200 expenses, $8,300 net
4. See activity breakdown table
5. Click "Hockey League" → Expand to see 45 transactions
6. Click receipt icon → View invoice in modal
7. Click **Export → CSV** → Download `financial_report_2025-Q3.csv`
8. Import into QuickBooks/Xero/Sage

---

## 💾 Example Data Structure

### `get_financial_data(start_date, end_date, activity_id=None)` returns:

```python
{
    'summary': {
        'total_revenue': 9500.00,
        'total_expenses': 1200.00,
        'net_income': 8300.00,
        'period_label': 'Q3 2025'
    },
    'by_activity': [
        {
            'activity_id': 1,
            'activity_name': 'Hockey League',
            'total_revenue': 5500.00,
            'total_expenses': 800.00,
            'net_income': 4700.00,
            'transactions': [
                {
                    'date': '2025-09-15',
                    'type': 'Income',
                    'category': 'Passport Sales',
                    'description': '4-session pass - John Doe',
                    'amount': 50.00,
                    'receipt_filename': None
                },
                # ... more transactions
            ]
        },
        # ... more activities
    ],
    'all_transactions': [
        # Flat list of all transactions for export
    ]
}
```

---

## ✅ Benefits

- ✅ Works with ALL accounting software (not vendor-locked)
- ✅ Single source of truth - no manual data entry
- ✅ Scales to enterprise customers ($300K+ revenue)
- ✅ Professional reporting for serious customers
- ✅ Audit trail with receipt attachments
- ✅ Fast to implement (1-2 days)
- ✅ No new database tables needed
- ✅ Supports drill-down for detailed analysis

---

## ❌ Features Removed (Keep It Simple)

- ~~Email report to accountant~~ - User can download and email manually
- ~~Scheduled reports~~ - User can export when needed
- ~~Compare periods~~ - Let accounting software handle this
- ~~Complex chart of accounts wizard~~ - Simple mapping is enough
- ~~Transaction notes/audit log~~ - Phase 2 if needed

---

## 📅 Estimated Effort

- **Backend (Data + Export)**: 4-6 hours
- **Frontend (UI + Table)**: 4-6 hours
- **Testing**: 2-3 hours
- **Total**: 1-2 days for MVP

---

## 🔧 Technical Notes

### Date Handling
- All dates stored as timezone-aware datetime in UTC
- Display dates in user's timezone (or admin's local time)
- Filter queries should use UTC boundaries

### Performance Considerations
- For $300K revenue org: ~3,000-5,000 transactions/year
- No pagination needed for report view
- Consider caching summary data for dashboard

### Security
- Admin authentication required
- Validate date ranges
- Sanitize filenames for receipt downloads
- Proper CSV escaping to prevent formula injection

### File Downloads
- CSV: `text/csv` with UTF-8 BOM for Excel compatibility
- IIF: `text/plain`
- XLSX: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

---

## 📝 Implementation Checklist

### Backend
- [ ] Create `get_financial_data()` in utils.py
- [ ] Create route `/reports/financial` in app.py
- [ ] Create route `/reports/financial/export` in app.py
- [ ] Implement CSV export function
- [ ] Implement QuickBooks IIF export (Phase 2)
- [ ] Implement Excel export (Phase 2)
- [ ] Add error handling for missing data

### Frontend
- [ ] Create `templates/financial_report.html`
- [ ] Add summary cards (3 metrics)
- [ ] Add date range selector
- [ ] Add activity breakdown table with expandable rows
- [ ] Add search/filter functionality
- [ ] Add export format dropdown
- [ ] Add receipt viewing modal
- [ ] Update `base.html` navigation (add Financial Report link)

### Testing
- [ ] Test data aggregation with real data
- [ ] Test CSV export format
- [ ] Test date filtering
- [ ] Test activity filtering
- [ ] Test receipt viewing
- [ ] Verify accounting software import (QuickBooks, Xero)

### Documentation
- [ ] Add user guide for exporting reports
- [ ] Document CSV format for support team
- [ ] Add accounting software import instructions

---

**This simplified version focuses on the core need: "Export my financial data to my accounting software."**

---

*Last Updated: 2025-10-10*
*Author: Planning session with production customer feedback*
