"""Add CartOrder for multi-item shop checkout

Revision ID: 206e67970b9a
Revises: 9b097cac8701
Create Date: 2026-09-09 09:00:46.660923

Every operation here is guarded by an existence check, because this revision runs
against two very different starting states:

  * An existing tenant DB, where shop_order/signup/ebank_payment are all present.
  * A brand new deployment, where 'flask db upgrade' runs BEFORE
    migrations/upgrade_production_database.py — and shop_order does not exist yet,
    since it is created by that script (task51), not by Alembic.

Without the guards the fresh-deploy case died with NoSuchTableError: shop_order and
took the whole customer deployment with it. Anything skipped here is applied right
afterwards by task53_add_cart_order_table, which is idempotent and covers the same
ground.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '206e67970b9a'
down_revision = '9b097cac8701'
branch_labels = None
depends_on = None


# (table, column, foreign key name) — each one links a row back to its parent cart.
_CART_LINKS = (
    ('shop_order', 'cart_order_id', 'fk_shop_order_cart_order_id'),
    ('signup', 'cart_order_id', 'fk_signup_cart_order_id'),
    ('ebank_payment', 'matched_cart_order_id', 'fk_ebank_payment_matched_cart_order_id'),
)


def _has_column(insp, table, column):
    return column in {c['name'] for c in insp.get_columns(table)}


def upgrade():
    insp = sa.inspect(op.get_bind())

    if not insp.has_table('cart_order'):
        op.create_table('cart_order',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('cart_code', sa.String(length=20), nullable=True),
            sa.Column('buyer_name', sa.String(length=150), nullable=False),
            sa.Column('buyer_email', sa.String(length=150), nullable=True),
            sa.Column('buyer_phone', sa.String(length=20), nullable=True),
            sa.Column('payment_method', sa.String(length=20), nullable=True),
            sa.Column('stripe_checkout_session_id', sa.String(length=255), nullable=True),
            sa.Column('total_amount', sa.Float(), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('created_dt', sa.DateTime(), nullable=True),
            sa.Column('paid_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('cart_code'),
        )

    for table, column, fk_name in _CART_LINKS:
        if not insp.has_table(table) or _has_column(insp, table, column):
            continue
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.add_column(sa.Column(column, sa.Integer(), nullable=True))
            batch_op.create_foreign_key(fk_name, 'cart_order', [column], ['id'], ondelete='SET NULL')


def downgrade():
    insp = sa.inspect(op.get_bind())

    for table, column, fk_name in reversed(_CART_LINKS):
        if not insp.has_table(table) or not _has_column(insp, table, column):
            continue
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.drop_constraint(fk_name, type_='foreignkey')
            batch_op.drop_column(column)

    if insp.has_table('cart_order'):
        op.drop_table('cart_order')
