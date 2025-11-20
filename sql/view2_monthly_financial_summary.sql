-- View 2: monthly_financial_summary
-- Monthly Financial Summary with Cash Basis and Accrual Basis Accounting
--
-- This view provides comprehensive monthly financial data including:
-- - Cash Basis: cash_received, cash_paid, net_cash_flow
-- - Accrual Basis: accounts_receivable (AR), accounts_payable (AP), total_revenue, total_expenses, net_income
-- - Separates passport sales from other income
-- - Compatible with QuickBooks, FreshBooks, and Xero terminology

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
