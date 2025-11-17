"""Add payment status to Income and Expense models

Revision ID: 0307966a5581
Revises: f4c10e5088aa
Create Date: 2025-11-16 17:37:18.371808

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0307966a5581'
down_revision = 'f4c10e5088aa'
branch_labels = None
depends_on = None


def upgrade():
    # Add payment tracking fields to Expense table
    with op.batch_alter_table('expense', schema=None) as batch_op:
        batch_op.add_column(sa.Column('payment_status', sa.String(length=20), server_default='paid', nullable=False))
        batch_op.add_column(sa.Column('payment_date', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('due_date', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('payment_method', sa.String(length=50), nullable=True))

    # Add payment tracking fields to Income table
    with op.batch_alter_table('income', schema=None) as batch_op:
        batch_op.add_column(sa.Column('payment_status', sa.String(length=20), server_default='received', nullable=False))
        batch_op.add_column(sa.Column('payment_date', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('payment_method', sa.String(length=50), nullable=True))


def downgrade():
    # Remove payment tracking fields from Income table
    with op.batch_alter_table('income', schema=None) as batch_op:
        batch_op.drop_column('payment_method')
        batch_op.drop_column('payment_date')
        batch_op.drop_column('payment_status')

    # Remove payment tracking fields from Expense table
    with op.batch_alter_table('expense', schema=None) as batch_op:
        batch_op.drop_column('payment_method')
        batch_op.drop_column('due_date')
        batch_op.drop_column('payment_date')
        batch_op.drop_column('payment_status')
