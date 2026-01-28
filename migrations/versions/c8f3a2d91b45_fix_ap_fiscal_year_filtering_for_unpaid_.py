"""fix_ap_fiscal_year_filtering_for_unpaid_expenses

Revision ID: c8f3a2d91b45
Revises: 177944451aa6
Create Date: 2026-01-27

This migration fixes a bug where unpaid expenses with a bill date (date) in a previous
fiscal year but a payment_date in the current fiscal year would not appear in the
Accounts Payable for the current fiscal year.

The fix: For unpaid expenses, use COALESCE(payment_date, due_date, date) as the
"effective date" for determining which month/fiscal year the expense belongs to.
This ensures that:
- If payment_date is set, the expense appears in that month
- If only due_date is set, the expense appears in that month
- Falls back to bill date if neither is set (preserves current behavior)

Example scenario this fixes:
- Expense created Dec 15, 2025 (date = 2025-12-15)
- Payment scheduled for Feb 2026 (payment_date = 2026-02-15)
- payment_status = 'unpaid'
- Before: Did NOT show in AP for FY2026 (filtered out because date is in 2025)
- After: Shows in AP for FY2026 in February (based on payment_date)

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c8f3a2d91b45'
down_revision = '177944451aa6'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the existing view
    op.execute("DROP VIEW IF EXISTS monthly_financial_summary")

    # Recreate with fix - use COALESCE(payment_date, due_date, date) for unpaid expenses
    op.execute("""
        CREATE VIEW monthly_financial_summary AS
        WITH
        -- Get ALL distinct month+activity combinations from ALL transaction sources
        all_month_activity AS (
            SELECT DISTINCT
                strftime('%Y-%m', paid_date) as month,
                activity_id
            FROM passport
            WHERE paid = 1 AND paid_date IS NOT NULL

            UNION

            SELECT DISTINCT
                strftime('%Y-%m', COALESCE(paid_date, created_dt)) as month,
                activity_id
            FROM passport
            WHERE paid = 0

            UNION

            SELECT DISTINCT
                strftime('%Y-%m', date) as month,
                activity_id
            FROM income
            WHERE payment_status = 'received'

            UNION

            SELECT DISTINCT
                strftime('%Y-%m', date) as month,
                activity_id
            FROM income
            WHERE payment_status = 'pending'

            UNION

            SELECT DISTINCT
                strftime('%Y-%m', date) as month,
                activity_id
            FROM expense
            WHERE payment_status = 'paid'

            UNION

            -- FIX: For unpaid expenses, use effective date (payment_date > due_date > date)
            SELECT DISTINCT
                strftime('%Y-%m', COALESCE(payment_date, due_date, date)) as month,
                activity_id
            FROM expense
            WHERE payment_status = 'unpaid'
        ),
        monthly_passports_cash AS (
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
        -- FIX: For unpaid expenses, use effective date (payment_date > due_date > date)
        monthly_expenses_ap AS (
            SELECT
                strftime('%Y-%m', COALESCE(payment_date, due_date, date)) as month,
                activity_id,
                SUM(amount) as expenses_ap
            FROM expense
            WHERE payment_status = 'unpaid'
            GROUP BY strftime('%Y-%m', COALESCE(payment_date, due_date, date)), activity_id
        )
        SELECT
            ma.month,
            ma.activity_id,
            a.name as account,

            COALESCE(pc.passport_sales_cash, 0) as passport_sales,
            COALESCE(ic.other_income_cash, 0) as other_income,
            COALESCE(pc.passport_sales_cash, 0) + COALESCE(ic.other_income_cash, 0) as cash_received,
            COALESCE(ec.expenses_cash, 0) as cash_paid,
            (COALESCE(pc.passport_sales_cash, 0) + COALESCE(ic.other_income_cash, 0) - COALESCE(ec.expenses_cash, 0)) as net_cash_flow,

            COALESCE(par.passport_sales_ar, 0) as passport_ar,
            COALESCE(iar.other_income_ar, 0) as other_income_ar,
            COALESCE(par.passport_sales_ar, 0) + COALESCE(iar.other_income_ar, 0) as accounts_receivable,
            COALESCE(eap.expenses_ap, 0) as accounts_payable,

            (COALESCE(pc.passport_sales_cash, 0) + COALESCE(par.passport_sales_ar, 0) +
             COALESCE(ic.other_income_cash, 0) + COALESCE(iar.other_income_ar, 0)) as total_revenue,
            (COALESCE(ec.expenses_cash, 0) + COALESCE(eap.expenses_ap, 0)) as total_expenses,
            ((COALESCE(pc.passport_sales_cash, 0) + COALESCE(par.passport_sales_ar, 0) +
              COALESCE(ic.other_income_cash, 0) + COALESCE(iar.other_income_ar, 0)) -
             (COALESCE(ec.expenses_cash, 0) + COALESCE(eap.expenses_ap, 0))) as net_income

        FROM all_month_activity ma
        JOIN activity a ON ma.activity_id = a.id
        LEFT JOIN monthly_passports_cash pc ON ma.month = pc.month AND ma.activity_id = pc.activity_id
        LEFT JOIN monthly_passports_ar par ON ma.month = par.month AND ma.activity_id = par.activity_id
        LEFT JOIN monthly_income_cash ic ON ma.month = ic.month AND ma.activity_id = ic.activity_id
        LEFT JOIN monthly_income_ar iar ON ma.month = iar.month AND ma.activity_id = iar.activity_id
        LEFT JOIN monthly_expenses_cash ec ON ma.month = ec.month AND ma.activity_id = ec.activity_id
        LEFT JOIN monthly_expenses_ap eap ON ma.month = eap.month AND ma.activity_id = eap.activity_id
        ORDER BY ma.month DESC, a.name
    """)


def downgrade():
    # Revert to the previous version (without the COALESCE fix for unpaid expenses)
    op.execute("DROP VIEW IF EXISTS monthly_financial_summary")

    op.execute("""
        CREATE VIEW monthly_financial_summary AS
        WITH
        -- Get ALL distinct month+activity combinations from ALL transaction sources
        all_month_activity AS (
            SELECT DISTINCT
                strftime('%Y-%m', paid_date) as month,
                activity_id
            FROM passport
            WHERE paid = 1 AND paid_date IS NOT NULL

            UNION

            SELECT DISTINCT
                strftime('%Y-%m', COALESCE(paid_date, created_dt)) as month,
                activity_id
            FROM passport
            WHERE paid = 0

            UNION

            SELECT DISTINCT
                strftime('%Y-%m', date) as month,
                activity_id
            FROM income
            WHERE payment_status = 'received'

            UNION

            SELECT DISTINCT
                strftime('%Y-%m', date) as month,
                activity_id
            FROM income
            WHERE payment_status = 'pending'

            UNION

            SELECT DISTINCT
                strftime('%Y-%m', date) as month,
                activity_id
            FROM expense
            WHERE payment_status = 'paid'

            UNION

            SELECT DISTINCT
                strftime('%Y-%m', date) as month,
                activity_id
            FROM expense
            WHERE payment_status = 'unpaid'
        ),
        monthly_passports_cash AS (
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
            ma.month,
            ma.activity_id,
            a.name as account,

            COALESCE(pc.passport_sales_cash, 0) as passport_sales,
            COALESCE(ic.other_income_cash, 0) as other_income,
            COALESCE(pc.passport_sales_cash, 0) + COALESCE(ic.other_income_cash, 0) as cash_received,
            COALESCE(ec.expenses_cash, 0) as cash_paid,
            (COALESCE(pc.passport_sales_cash, 0) + COALESCE(ic.other_income_cash, 0) - COALESCE(ec.expenses_cash, 0)) as net_cash_flow,

            COALESCE(par.passport_sales_ar, 0) as passport_ar,
            COALESCE(iar.other_income_ar, 0) as other_income_ar,
            COALESCE(par.passport_sales_ar, 0) + COALESCE(iar.other_income_ar, 0) as accounts_receivable,
            COALESCE(eap.expenses_ap, 0) as accounts_payable,

            (COALESCE(pc.passport_sales_cash, 0) + COALESCE(par.passport_sales_ar, 0) +
             COALESCE(ic.other_income_cash, 0) + COALESCE(iar.other_income_ar, 0)) as total_revenue,
            (COALESCE(ec.expenses_cash, 0) + COALESCE(eap.expenses_ap, 0)) as total_expenses,
            ((COALESCE(pc.passport_sales_cash, 0) + COALESCE(par.passport_sales_ar, 0) +
              COALESCE(ic.other_income_cash, 0) + COALESCE(iar.other_income_ar, 0)) -
             (COALESCE(ec.expenses_cash, 0) + COALESCE(eap.expenses_ap, 0))) as net_income

        FROM all_month_activity ma
        JOIN activity a ON ma.activity_id = a.id
        LEFT JOIN monthly_passports_cash pc ON ma.month = pc.month AND ma.activity_id = pc.activity_id
        LEFT JOIN monthly_passports_ar par ON ma.month = par.month AND ma.activity_id = par.activity_id
        LEFT JOIN monthly_income_cash ic ON ma.month = ic.month AND ma.activity_id = ic.activity_id
        LEFT JOIN monthly_income_ar iar ON ma.month = iar.month AND ma.activity_id = iar.activity_id
        LEFT JOIN monthly_expenses_cash ec ON ma.month = ec.month AND ma.activity_id = ec.activity_id
        LEFT JOIN monthly_expenses_ap eap ON ma.month = eap.month AND ma.activity_id = eap.activity_id
        ORDER BY ma.month DESC, a.name
    """)
