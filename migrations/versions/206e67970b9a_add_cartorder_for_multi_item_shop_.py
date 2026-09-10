"""Add CartOrder for multi-item shop checkout

Revision ID: 206e67970b9a
Revises: 9b097cac8701
Create Date: 2026-09-09 09:00:46.660923

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '206e67970b9a'
down_revision = '9b097cac8701'
branch_labels = None
depends_on = None


def upgrade():
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

    with op.batch_alter_table('shop_order', schema=None) as batch_op:
        batch_op.add_column(sa.Column('cart_order_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_shop_order_cart_order_id', 'cart_order', ['cart_order_id'], ['id'], ondelete='SET NULL')

    with op.batch_alter_table('signup', schema=None) as batch_op:
        batch_op.add_column(sa.Column('cart_order_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_signup_cart_order_id', 'cart_order', ['cart_order_id'], ['id'], ondelete='SET NULL')

    with op.batch_alter_table('ebank_payment', schema=None) as batch_op:
        batch_op.add_column(sa.Column('matched_cart_order_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_ebank_payment_matched_cart_order_id', 'cart_order', ['matched_cart_order_id'], ['id'], ondelete='SET NULL')


def downgrade():
    with op.batch_alter_table('ebank_payment', schema=None) as batch_op:
        batch_op.drop_constraint('fk_ebank_payment_matched_cart_order_id', type_='foreignkey')
        batch_op.drop_column('matched_cart_order_id')

    with op.batch_alter_table('signup', schema=None) as batch_op:
        batch_op.drop_constraint('fk_signup_cart_order_id', type_='foreignkey')
        batch_op.drop_column('cart_order_id')

    with op.batch_alter_table('shop_order', schema=None) as batch_op:
        batch_op.drop_constraint('fk_shop_order_cart_order_id', type_='foreignkey')
        batch_op.drop_column('cart_order_id')

    op.drop_table('cart_order')
