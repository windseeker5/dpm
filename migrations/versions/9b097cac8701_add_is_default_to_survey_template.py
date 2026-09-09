"""add is_default to survey_template

Revision ID: 9b097cac8701
Revises: d1a7e42b9c03
Create Date: 2026-09-08 19:46:24.726395

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9b097cac8701'
down_revision = 'd1a7e42b9c03'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('survey_template', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade():
    with op.batch_alter_table('survey_template', schema=None) as batch_op:
        batch_op.drop_column('is_default')
