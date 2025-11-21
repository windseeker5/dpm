"""fix_monthly_financial_summary_view_to_include_all_transactions

Revision ID: 90c766ac9eed
Revises: cb97872b8def
Create Date: 2025-11-21 15:18:07.014170

This migration fixes a critical bug in the monthly_financial_summary view where transactions
were being excluded if an activity had income/expenses in a month but no passport sales.

The problem: The view used activity as the base table and only created rows when passport
transactions existed. If an activity had income or expenses but no passports in a given month,
those transactions were silently dropped.

The fix: Create a base table of ALL distinct (month, activity_id) combinations from ALL
transaction sources (passports, income, expenses), then LEFT JOIN the aggregated data.

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '90c766ac9eed'
down_revision = 'cb97872b8def'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the existing view
    op.execute("DROP VIEW IF EXISTS monthly_financial_summary")

    # Recreate with fix - use UNION of all month+activity combinations as base
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


def downgrade():
    # Revert to the old buggy version
    op.execute("DROP VIEW IF EXISTS monthly_financial_summary")

    op.execute("""
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

        FROM activity a
        LEFT JOIN monthly_passports_cash pc ON a.id = pc.activity_id
        LEFT JOIN monthly_passports_ar par ON a.id = par.activity_id AND COALESCE(pc.month, par.month) = par.month
        LEFT JOIN monthly_income_cash ic ON a.id = ic.activity_id AND COALESCE(pc.month, par.month, ic.month) = ic.month
        LEFT JOIN monthly_income_ar iar ON a.id = iar.activity_id AND COALESCE(pc.month, par.month, ic.month, iar.month) = iar.month
        LEFT JOIN monthly_expenses_cash ec ON a.id = ec.activity_id AND COALESCE(pc.month, par.month, ic.month, iar.month, ec.month) = ec.month
        LEFT JOIN monthly_expenses_ap eap ON a.id = eap.activity_id AND COALESCE(pc.month, par.month, ic.month, iar.month, ec.month, eap.month) = eap.month
        WHERE COALESCE(pc.month, par.month, ic.month, iar.month, ec.month, eap.month) IS NOT NULL
        ORDER BY month DESC, a.name
    """)
