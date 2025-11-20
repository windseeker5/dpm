"""Remove unused organizations table and foreign keys

Revision ID: cb97872b8def
Revises: adf18285427e
Create Date: 2025-11-20 14:06:01.476324

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cb97872b8def'
down_revision = 'adf18285427e'
branch_labels = None
depends_on = None


def upgrade():
    """
    Remove unused organizations table and foreign keys.
    This was built for multi-tenant feature that was never activated.
    Table has 0 records, no activities or users reference it.

    Note: We need to drop/recreate views because SQLite doesn't allow
    table alterations when views reference those tables.
    """
    # Step 1: Drop views that depend on user/activity tables
    op.execute('DROP VIEW IF EXISTS monthly_transactions_detail')
    op.execute('DROP VIEW IF EXISTS monthly_financial_summary')

    # Step 2: Drop organization_id from user table
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('organization_id')

    # Step 3: Drop organization_id from activity table
    with op.batch_alter_table('activity', schema=None) as batch_op:
        batch_op.drop_column('organization_id')

    # Step 4: Drop organizations table
    op.drop_table('organizations')

    # Step 5: Recreate the views (without organization dependencies)
    op.execute('''
        CREATE VIEW monthly_transactions_detail AS
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

        ORDER BY month DESC, transaction_date DESC
    ''')

    op.execute('''
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
    ''')


def downgrade():
    """
    Downgrade not supported - this was an unused feature.
    If needed, recreate from migration f4c10e5088aa (initial schema).
    """
    pass
