-- View 1: monthly_transactions_detail
-- Transaction Detail Ledger (Accounting Standard - QuickBooks/FreshBooks/Xero Compatible)
--
-- This view provides a detailed transaction ledger with proper accounting terminology:
-- - transaction_type: Income or Expense
-- - category: Accounting category (Passport Sales, Staff, Merchandise Sales, etc.)
-- - customer: Customer name (passport sales only)
-- - vendor: Vendor name (currently not tracked, always NULL)
-- - payment_status: Paid, Unpaid (AR), or Unpaid (AP)

SELECT
    strftime('%Y-%m', COALESCE(p.paid_date, p.created_dt)) as month,
    a.name as project,
    'Income' as transaction_type,
    COALESCE(p.paid_date, p.created_dt) as transaction_date,
    'Passport Sales' as account,
    u.name as customer,
    NULL as vendor,
    p.notes as memo,
    p.sold_amt as amount,
    CASE WHEN p.paid = 1 THEN 'Paid' ELSE 'Unpaid (AR)' END as payment_status,
    'Passport System' as entered_by
FROM passport p
JOIN activity a ON p.activity_id = a.id
LEFT JOIN user u ON p.user_id = u.id

UNION ALL

SELECT
    strftime('%Y-%m', i.date) as month,
    a.name as project,
    'Income' as transaction_type,
    i.date as transaction_date,
    i.category as account,
    NULL as customer,
    NULL as vendor,
    i.note as memo,
    i.amount,
    CASE
        WHEN i.payment_status = 'received' THEN 'Paid'
        WHEN i.payment_status = 'pending' THEN 'Unpaid (AR)'
        ELSE 'Unpaid (AR)'
    END as payment_status,
    COALESCE(i.created_by, 'System') as entered_by
FROM income i
JOIN activity a ON i.activity_id = a.id

UNION ALL

SELECT
    strftime('%Y-%m', e.date) as month,
    a.name as project,
    'Expense' as transaction_type,
    e.date as transaction_date,
    e.category as account,
    NULL as customer,
    NULL as vendor,
    e.description as memo,
    e.amount,
    CASE
        WHEN e.payment_status = 'paid' THEN 'Paid'
        WHEN e.payment_status = 'unpaid' THEN 'Unpaid (AP)'
        ELSE 'Unpaid (AP)'
    END as payment_status,
    COALESCE(e.created_by, 'System') as entered_by
FROM expense e
JOIN activity a ON e.activity_id = a.id

ORDER BY month DESC, transaction_date DESC;
