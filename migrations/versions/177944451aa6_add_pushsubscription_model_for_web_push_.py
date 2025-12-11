"""Add PushSubscription model for web push notifications

Revision ID: 177944451aa6
Revises: 90c766ac9eed
Create Date: 2025-12-10 20:56:59.942571

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '177944451aa6'
down_revision = '90c766ac9eed'
branch_labels = None
depends_on = None


def upgrade():
    # Create push_subscription table only
    op.create_table('push_subscription',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('admin_id', sa.Integer(), nullable=False),
        sa.Column('endpoint', sa.Text(), nullable=False),
        sa.Column('p256dh_key', sa.Text(), nullable=False),
        sa.Column('auth_key', sa.Text(), nullable=False),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('created_dt', sa.DateTime(), nullable=True),
        sa.Column('last_used_dt', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['admin_id'], ['admin.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('endpoint')
    )
    with op.batch_alter_table('push_subscription', schema=None) as batch_op:
        batch_op.create_index('ix_push_subscription_admin', ['admin_id'], unique=False)


def downgrade():
    with op.batch_alter_table('push_subscription', schema=None) as batch_op:
        batch_op.drop_index('ix_push_subscription_admin')
    op.drop_table('push_subscription')
